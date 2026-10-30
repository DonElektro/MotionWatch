extends PanelContainer
## «Rückmeldung an den Entwickler» im Simulator – dasselbe Fenster wie in MoveEye (584: Art Fehler / Wunsch / Lob / Frage,
## «Wie zufrieden?» 1–5 Sterne, Nachricht, Kontakt freiwillig, Bildschirmfoto, technische Angaben, «Immer dabei», wartende
## Nachrichten mit «Jetzt senden»).
##   * MoveEye verbunden (MoveEye 2.98.33): die Nachricht geht als Anfrage (mw_cmd «feedback») an MoveEye, das sie wie alle
##     Rückmeldungen anonym weiterschickt (Teil 350 / 370; das Bildschirmfoto holt MoveEye selbst über /view.jpg).
##   * 3D-4.2x (Wunsch Daniel 30.10.2026): ohne MoveEye schickt der Simulator selbst – genau wie MoveEye (370 feedback_send /
##     feedback_flush): Text als ntfy-Nachricht an denselben öffentlichen Entwickler-Kanal auf beiden Servern (ntfy-me.com und
##     ntfy.sh, eine Annahme genügt), das Bild als zweite Nachricht mit Anhang (PUT), höchstens 350 KB, 5 Nachrichten pro
##     Stunde, ohne Internet wartet sie (user://feedback_outbox.json) und geht alle 10 Minuten wieder auf den Weg.
##     Anonym: kein Name, keine Adresse, ausser man schreibt sie hinein; Bild = das Fenster des Simulators (verkleinert).
##   * Tests: «fb_test» über /control lenkt die Nachrichten an eine Adresse auf diesem PC um (nur 127.0.0.1 / localhost);
##     «Was wird gesendet?» im Fenster zeigt den Text, wie er abgeht.

var main
var mehr
var _kind := "idea"
var _kind_btns := {}
var _text: TextEdit
var _contact: LineEdit
var _shot: CheckBox
var _diag: CheckBox
var _prev: TextureRect
var _stars := 0
var _star_ics := []
var _status: Label
var _route: Label
var _wait_box: HBoxContainer
var _wait_l: Label
var _peek: Label
var _send_b: Button
var _sent_id := 0
var _img: Image = null                 # the window as it was when the dialog opened (preview = what is sent)
var page := "Mehr"                     # where it was written (like «Seite» in MoveEye)

# the public developer channel of MoveEye (quelle/370_rueckmeldung_teilen_abschreckung.py _FB_DEST / _FB_DEST2), unchanged
const _FB_DEST := "aHR0cHM6Ly9udGZ5LW1lLmNvbS9tdy1mYi0xYzE3ZTFkMWViNWZhMmFhZTQ5Nw=="
const _FB_DEST2 := "aHR0cHM6Ly9udGZ5LnNoL213LWZiLTFjMTdlMWQxZWI1ZmEyYWFlNDk3"
const FB_SHOT_MAX := 350 * 1024
const OUTBOX := "user://feedback_outbox.json"
const SHOTS := "user://feedback_shots"
const KINDS := [["bug", "Fehler", "bug"], ["idea", "Wunsch", "bulb"], ["praise", "Lob", "star"], ["question", "Frage", "question"]]
const FB_KINDS := {"bug": "Fehler", "idea": "Wunsch", "praise": "Lob", "question": "Frage", "other": "Feedback"}
const UI = preload("res://scripts/ui_style.gd")
const Icons = preload("res://scripts/mehr_icons.gd")
const YEL := Color("#f5c542")

var test_url := ""                     # tests: a local address instead of the developer channel
var sent_log: Array = []               # times of the last messages (5 per hour)
var errs := {}                         # host -> {"why", "t"}
var ok_t := 0.0
var _busy := false
var _flush_t := 20.0                   # the first try a little after the start, then every 10 minutes
var last: Dictionary = {}              # the last message (for tests): body, title, route, shot size


func _ready() -> void:
	visible = false
	var a := OS.get_cmdline_args() + OS.get_cmdline_user_args()      # tests: --fb-test-url http://127.0.0.1:PORT/topic
	var ai := a.find("--fb-test-url")
	if ai >= 0 and ai + 1 < a.size() and (a[ai + 1].begins_with("http://127.0.0.1") or a[ai + 1].begins_with("http://localhost")):
		test_url = a[ai + 1]
	add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.99), UI.LINE, 16, 16, 1))
	custom_minimum_size = Vector2(520, 0)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 8)
	add_child(box)
	var hd := HBoxContainer.new()
	hd.add_theme_constant_override("separation", 8)
	box.add_child(hd)
	hd.add_child(Icons.icon("chat", UI.TXT, 22.0))
	var tl := Label.new()
	tl.text = "Rückmeldung an den Entwickler"
	tl.add_theme_font_override("font", UI.heading_font())
	tl.add_theme_font_size_override("font_size", 17)
	tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(tl)
	var x := Button.new()
	x.flat = true
	x.custom_minimum_size = Vector2(30, 30)
	x.tooltip_text = "Schliessen (Esc)"
	var xi := Icons.icon("x", UI.MUT, 16.0)
	xi.position = Vector2(7, 7)
	x.add_child(xi)
	x.pressed.connect(func(): visible = false)
	hd.add_child(x)
	box.add_child(_wrap(UI.small("Fehler, Wünsche, Lob, Fragen – alles hilft. Die Nachricht geht anonym weg: kein Name, keine Adresse, ausser du schreibst sie hinein.")))
	var seg := HBoxContainer.new()
	seg.add_theme_constant_override("separation", 6)
	box.add_child(seg)
	for k in KINDS:
		var b := Button.new()
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size = Vector2(0, 34)
		b.focus_mode = Control.FOCUS_NONE
		var h := HBoxContainer.new()
		h.set_anchors_preset(Control.PRESET_FULL_RECT)
		h.alignment = BoxContainer.ALIGNMENT_CENTER
		h.mouse_filter = Control.MOUSE_FILTER_IGNORE
		h.add_theme_constant_override("separation", 5)
		var ki := Icons.icon(k[2], YEL if k[0] == "praise" else UI.TXT, 16.0)
		ki.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(ki)
		var l := Label.new()
		l.text = k[1]
		l.add_theme_font_size_override("font_size", 13)
		h.add_child(l)
		b.add_child(h)
		b.pressed.connect(func(): _kind = k[0]; _paint_kind(); _peek_update())
		seg.add_child(b)
		_kind_btns[k[0]] = b
	var sr := HBoxContainer.new()
	sr.add_theme_constant_override("separation", 2)
	box.add_child(sr)
	var sl := UI.small("Wie zufrieden? (freiwillig)")
	sl.autowrap_mode = TextServer.AUTOWRAP_OFF
	sl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	sr.add_child(sl)
	var sp := Control.new()
	sp.custom_minimum_size = Vector2(8, 0)
	sr.add_child(sp)
	for i in range(1, 6):
		var b := Button.new()
		b.flat = true
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(30, 30)
		b.tooltip_text = "%d / 5" % i
		var ic := Control.new()
		ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
		ic.position = Vector2(4, 4)
		ic.size = Vector2(22, 22)
		ic.set_meta("on", false)
		ic.draw.connect(func():
			ic.draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.1, 1.1))
			Icons.draw(ic, "star_on" if ic.get_meta("on") else "star", Vector2(10, 10), YEL)
			ic.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE))
		b.add_child(ic)
		b.pressed.connect(func(): _set_stars(0 if _stars == i else i); _peek_update())
		_star_ics.append(ic)
		sr.add_child(b)
	_text = TextEdit.new()
	_text.placeholder_text = "Deine Nachricht …"
	_text.custom_minimum_size = Vector2(480, 110)
	_text.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	_text.text_changed.connect(_peek_update)
	box.add_child(_text)
	_contact = LineEdit.new()
	_contact.placeholder_text = "Kontakt für eine Antwort (freiwillig)"
	_contact.max_length = 120
	_contact.text_changed.connect(func(_t): _peek_update())
	box.add_child(_contact)
	_shot = CheckBox.new()
	_shot.text = "Bildschirmfoto mitschicken – das Bild des Simulator-Fensters (verkleinert)"
	_shot.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_shot.custom_minimum_size = Vector2(480, 0)
	_shot.toggled.connect(func(_on): _paint_prev(); _peek_update())
	box.add_child(_shot)
	_prev = TextureRect.new()
	_prev.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_prev.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	_prev.custom_minimum_size = Vector2(0, 150)
	_prev.visible = false
	box.add_child(_prev)
	_diag = CheckBox.new()
	_diag.text = "Technische Angaben mitsenden (Version, Gerät, letzte wichtige Ereignisse – keine Bilder, keine Passwörter)"
	_diag.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_diag.custom_minimum_size = Vector2(480, 0)
	_diag.button_pressed = true
	_diag.toggled.connect(func(_on): _peek_update())
	box.add_child(_diag)
	_route = _wrap(UI.small(""))
	box.add_child(_route)
	var pk := UI.sub_fold(box, "Was wird gesendet?", false)
	_peek = _wrap(UI.small("", UI.TXT))
	_peek.custom_minimum_size = Vector2(460, 0)
	pk.add_child(_peek)
	_wait_box = HBoxContainer.new()
	_wait_box.add_theme_constant_override("separation", 6)
	box.add_child(_wait_box)
	var wi := UI.group_icon("clock")
	wi.set_meta("col", UI.ORG)
	_wait_box.add_child(wi)
	_wait_l = UI.small("")
	_wait_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_wait_l.custom_minimum_size = Vector2(340, 0)
	_wait_box.add_child(_wait_l)
	var now_b := Button.new()
	now_b.text = "Jetzt senden"
	now_b.add_theme_font_size_override("font_size", 12)
	now_b.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	now_b.pressed.connect(func(): await flush(); _paint_wait())
	_wait_box.add_child(now_b)
	_status = _wrap(UI.small("", UI.RED))
	box.add_child(_status)
	var bt := HBoxContainer.new()
	bt.alignment = BoxContainer.ALIGNMENT_END
	bt.add_theme_constant_override("separation", 8)
	var cancel := Button.new()
	cancel.text = "Abbrechen"
	cancel.pressed.connect(func(): visible = false)
	bt.add_child(cancel)
	_send_b = Button.new()
	_send_b.text = "Senden"
	_send_b.custom_minimum_size = Vector2(96, 0)
	UI.primary(_send_b)
	_send_b.pressed.connect(_send)
	bt.add_child(_send_b)
	box.add_child(bt)
	_paint_kind()
	_set_stars(0)


func _wrap(l: Label) -> Label:
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(480, 0)
	return l


func _paint_kind() -> void:
	for k in _kind_btns:
		var b: Button = _kind_btns[k]
		var on: bool = k == _kind
		var st := UI.box(UI.ORG.darkened(0.72) if on else UI.BTN2, UI.ORG if on else UI.LINE, 10, 8, 1)
		for s in ["normal", "hover", "pressed", "focus"]:
			b.add_theme_stylebox_override(s, st)


func _set_stars(i: int) -> void:
	_stars = i
	for j in range(_star_ics.size()):
		var ic: Control = _star_ics[j]
		ic.set_meta("on", j < _stars)
		ic.queue_redraw()


func connected() -> bool:
	return main.mw_addr != "" and main.now() - main.mw_t <= 10.0


func open(where := "") -> void:
	"""the dialog (with MoveEye connected the message goes over MoveEye, else straight from here)"""
	if where != "":
		page = where
	_status.text = ""
	if visible:
		get_parent().move_child(self, -1)
		return
	_img = get_viewport().get_texture().get_image()          # the window as it is now (before the dialog covers it)
	_prev.texture = null
	visible = true
	get_parent().move_child(self, -1)
	_paint_prev()
	_paint_route()
	_paint_wait()
	_peek_update()
	_place()
	_text.grab_focus()


func _paint_route() -> void:
	if connected():
		_route.text = "Immer dabei: 3D-Simulator %s · Seite «%s». Weg: über MoveEye «%s» (verbunden) – MoveEye schickt sie anonym weiter." % [main.VERSION, page, str(main.mw.get("device", "MoveEye"))]
	else:
		_route.text = "Immer dabei: 3D-Simulator %s · Seite «%s». Weg: direkt vom Simulator (kein MoveEye verbunden) – ohne Internet wartet sie und geht später." % [main.VERSION, page]
	if test_url != "":
		_route.text += " · TESTMODUS: geht nur an " + test_url


func _paint_prev() -> void:
	_prev.visible = _shot.button_pressed and _img != null and not connected()
	if _prev.visible and _prev.texture == null:
		var sm: Image = _img.duplicate()
		sm.resize(480, int(480.0 * sm.get_height() / max(1, sm.get_width())), Image.INTERPOLATE_BILINEAR)
		_prev.texture = ImageTexture.create_from_image(sm)


func _paint_wait() -> void:
	var box := _load()
	_wait_box.visible = not box.is_empty()
	var t := "%d Feedbacks warten noch auf das Senden" % box.size()
	for h in errs:
		t += "\nLetzter Fehler · %s: %s" % [h, str(errs[h]["why"])]
	_wait_l.text = t


func _place() -> void:
	"""in the middle of the window, as small as the content allows"""
	await get_tree().process_frame
	reset_size()
	await get_tree().process_frame
	reset_size()
	position = ((get_viewport_rect().size - size) / 2.0).max(Vector2(8, 8))


func fill_and_send(d: Dictionary) -> void:
	"""for tests over /control: fill the fields and press «Senden» (press = false: only fill)"""
	_text.text = str(d.get("text", ""))
	_kind = str(d.get("kind", "idea"))
	_paint_kind()
	_set_stars(clampi(int(d.get("stars", 0)), 0, 5))
	_contact.text = str(d.get("contact", ""))
	_shot.button_pressed = bool(d.get("shot", false))
	_diag.button_pressed = bool(d.get("diag", true))
	if bool(d.get("press", true)):
		_send()
	else:
		_peek_update()


# ---- the message (like feedback_send of MoveEye) ---------------------------------------------------------------------------
func _body(text: String) -> String:
	var b := text
	var ct := _contact.text.strip_edges().substr(0, 120)
	if ct != "":
		b += "\n\nKontakt: " + ct
	if _stars > 0:
		b += "\n\nZufriedenheit: " + "★".repeat(_stars) + "☆".repeat(5 - _stars) + " (%d/5)" % _stars
	b += "\n\n— 3D-Simulator %s · ohne MoveEye · Seite: %s" % [main.VERSION, page]
	if _diag.button_pressed:
		var v: Dictionary = Engine.get_version_info()
		b += "\n\n--- Technik ---\nSimulator %s · Godot %s · %s · %s · Grafik %s · Laufzeit %d h" % [main.VERSION, str(v.get("string", "")), OS.get_name(),
				RenderingServer.get_video_adapter_name(), str(main.quality), int(main.now() / 3600.0)]
		var pr = mehr.protokoll if mehr != null else null
		if pr != null:
			var imp: Array = pr.items.filter(func(e): return str(e["k"]) in ["fehler", "warnung", "verbindung", "update", "start"])
			for e in imp.slice(max(0, imp.size() - 8)):
				b += "\n" + pr._hms(float(e["t"])) + " " + str(e["x"]).substr(0, 140)
	return b


func _title(kind: String, stars: int) -> String:
	return "MoveEye – " + FB_KINDS.get(kind, "Feedback") + ((" " + "★".repeat(stars)) if stars > 0 else "")


func _peek_update() -> void:
	if _peek == null:
		return
	var t := _text.text.strip_edges()
	if connected():
		_peek.text = "Geht an MoveEye «%s», das sie wie alle Rückmeldungen anonym weiterschickt (Art %s, %d Sterne%s)." % [
				str(main.mw.get("device", "MoveEye")), FB_KINDS.get(_kind, ""), _stars, ", mit Bild von /view.jpg" if _shot.button_pressed else ""]
		return
	_peek.text = "Titel: %s\n\n%s%s" % [_title(_kind, _stars), _body(t if t != "" else "(deine Nachricht)"),
			"\n\n+ ein Bild als zweite Nachricht (JPEG, höchstens 350 KB)" if _shot.button_pressed else ""]


func _send() -> void:
	var t := _text.text.strip_edges()
	_status.add_theme_color_override("font_color", UI.RED)
	if t.length() < 3:
		_status.text = "Bitte ein paar Worte schreiben."
		return
	if connected():
		_send_mw(t)
		return
	var now_ := Time.get_unix_time_from_system()
	sent_log = sent_log.filter(func(x): return now_ - float(x) < 3600.0)
	if sent_log.size() >= 5:
		_status.text = "Höchstens 5 Nachrichten pro Stunde – bitte später nochmals."
		return
	var msg := {"kind": _kind, "body": _body(t.substr(0, 3000)), "t": Time.get_datetime_string_from_system(false, true), "stars": _stars}
	if _shot.button_pressed and _img != null:
		var jpg := shot_jpg(_img)
		if not jpg.is_empty():
			DirAccess.make_dir_recursive_absolute(SHOTS)
			msg["img"] = "%08x%04x" % [randi(), randi() % 65536]
			var f := FileAccess.open(SHOTS.path_join(str(msg["img"]) + ".jpg"), FileAccess.WRITE)
			if f != null:
				f.store_buffer(jpg)
				f.close()
				msg["img_kb"] = jpg.size() / 1024
			else:
				msg.erase("img")
	sent_log.append(now_)
	var box := _load()
	box.append(msg)
	_save(box.slice(max(0, box.size() - 20)))
	last = {"route": "direct", "title": _title(_kind, _stars), "body": msg["body"], "shot_kb": int(msg.get("img_kb", 0)), "test_url": test_url}
	if mehr != null and mehr.protokoll != null:
		mehr.protokoll.add("rueckmeldung", "Rückmeldung geschrieben (%s) – geht direkt an den Entwickler%s" % [FB_KINDS.get(_kind, ""), " (Testmodus)" if test_url != "" else ""])
	_text.text = ""
	_contact.text = ""
	_set_stars(0)
	visible = false
	if mehr != null:
		mehr.toast("Danke! Die Nachricht ist unterwegs.")
	flush()


func _send_mw(t: String) -> void:
	"""MoveEye is connected: it takes the message (mw_cmd «feedback», 350) and sends it like all feedback"""
	var id: int = max(int(Time.get_unix_time_from_system() * 1000.0), int(main.mw_cmd.get("id", 0)) + 1)
	main.mw_cmd = {"id": id, "op": "feedback", "kind": _kind, "stars": _stars, "text": t.substr(0, 3000),
				   "contact": _contact.text.strip_edges(), "shot": _shot.button_pressed, "sim": main.VERSION}
	_sent_id = id
	last = {"route": "moveeye", "id": id, "kind": _kind, "stars": _stars, "text": t.substr(0, 3000)}
	_status.add_theme_color_override("font_color", UI.MUT)
	_status.text = "Übergeben an MoveEye …"
	_send_b.disabled = true
	for i in range(30):
		await get_tree().create_timer(0.5).timeout
		var r = main.mw.get("refscan", null)
		if typeof(r) == TYPE_DICTIONARY and int(r.get("cmd_seen", 0)) >= id:
			_send_b.disabled = false
			last["seen"] = true
			if mehr != null and mehr.protokoll != null:
				mehr.protokoll.add("rueckmeldung", "Rückmeldung an MoveEye übergeben – MoveEye schickt sie weiter")
			_text.text = ""
			_set_stars(0)
			visible = false
			if mehr != null:
				mehr.toast("Danke! MoveEye hat die Nachricht übernommen und schickt sie weiter.")
			return
	_send_b.disabled = false
	_status.text = "MoveEye hat noch nicht geantwortet – die Nachricht bleibt bereit, solange MoveEye verbunden ist."


static func shot_jpg(img: Image) -> PackedByteArray:
	"""the window as a small JPEG: at most 1024 px wide and FB_SHOT_MAX (like _fbx_jpg of MoveEye)"""
	var im: Image = img.duplicate()
	if im.get_format() != Image.FORMAT_RGB8:
		im.convert(Image.FORMAT_RGB8)
	if im.get_width() > 1024:
		im.resize(1024, max(1, int(im.get_height() * 1024.0 / im.get_width())), Image.INTERPOLATE_BILINEAR)
	for q in [0.75, 0.6, 0.45, 0.35]:
		var b := im.save_jpg_to_buffer(q)
		if not b.is_empty() and b.size() <= FB_SHOT_MAX:
			return b
		if q == 0.45:
			im.resize(im.get_width() / 2, im.get_height() / 2, Image.INTERPOLATE_BILINEAR)
	return PackedByteArray()


# ---- the outbox and the sending (like feedback_flush of MoveEye) -----------------------------------------------------------
func _load() -> Array:
	if not FileAccess.file_exists(OUTBOX):
		return []
	var d = JSON.parse_string(FileAccess.get_file_as_string(OUTBOX))
	return (d as Array).filter(func(x): return typeof(x) == TYPE_DICTIONARY) if typeof(d) == TYPE_ARRAY else []


func _save(box: Array) -> void:
	var f := FileAccess.open(OUTBOX, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(box))
		f.close()
	var keep := {}
	for m in box:
		if m.has("img"):
			keep[str(m["img"])] = true
	var da := DirAccess.open(SHOTS)
	if da != null:
		for fn in da.get_files():
			if not keep.has(fn.get_basename()):
				da.remove(fn)


func urls() -> Array:
	if test_url != "":
		return [test_url]
	return [Marshalls.base64_to_utf8(_FB_DEST), Marshalls.base64_to_utf8(_FB_DEST2)]


static func _host(u: String) -> String:
	var p := u.split("/")
	return p[2] if p.size() > 2 else u


static func _hdr(v: String) -> String:
	"""HTTP headers are latin-1: umlauts / ★ go as RFC 2047 (ntfy understands that) - like _hdr of MoveEye"""
	v = " ".join(v.split(" ", false))
	for i in range(v.length()):
		if v.unicode_at(i) > 127:
			return "=?UTF-8?B?" + Marshalls.utf8_to_base64(v) + "?="
	return v


func _req(url: String, data: PackedByteArray, headers: PackedStringArray, method: int) -> bool:
	var h := HTTPRequest.new()
	h.timeout = 30.0 if method == HTTPClient.METHOD_PUT else 15.0
	add_child(h)
	var err := h.request_raw(url, headers, method, data)
	var host := _host(url)
	var why := ""
	if err != OK:
		why = "Anfrage nicht möglich (%d)" % err
	else:
		var r: Array = await h.request_completed
		if int(r[0]) == HTTPRequest.RESULT_SUCCESS and int(r[1]) < 300:
			h.queue_free()
			errs.erase(host)
			ok_t = Time.get_unix_time_from_system()
			return true
		var reasons := ["", "Antwort unvollständig", "keine Antwort", "keine Verbindung", "kein Netz / Adresse unbekannt", "Verbindung fehlgeschlagen",
				"TLS-Fehler", "keine Antwort", "Antwort zu gross", "zu viele Umleitungen", "Fehler beim Speichern", "Fehler beim Schreiben", "Zeit abgelaufen"]
		why = ("HTTP %d" % int(r[1])) if int(r[0]) == HTTPRequest.RESULT_SUCCESS else str(reasons[clampi(int(r[0]), 0, reasons.size() - 1)])
	h.queue_free()
	if not errs.has(host) and mehr != null and mehr.protokoll != null:
		mehr.protokoll.add("warnung", "Rückmeldung: %s hat abgelehnt (%s) – später nochmals" % [host, why])
	errs[host] = {"why": why, "t": Time.get_unix_time_from_system()}
	return false


func flush() -> void:
	"""send what is waiting: to both servers; a message counts as sent when one server took it; the picture goes to the
	same server(s)"""
	if _busy:
		return
	_busy = true
	var box := _load()
	var us := urls()
	var left := []
	var sent := 0
	for m in box:
		var title := _title(str(m.get("kind", "")), int(m.get("stars", 0)))
		var tags: String = {"bug": "bug", "idea": "bulb", "praise": "star", "question": "question"}.get(str(m.get("kind", "")), "speech_balloon")
		if not bool(m.get("text_sent", false)):
			var oks := []
			for i in range(us.size()):
				if await _req(us[i], str(m["body"]).to_utf8_buffer(), PackedStringArray(["Title: " + _hdr(title), "Tags: " + tags]), HTTPClient.METHOD_POST):
					oks.append(i)
			if oks.is_empty():
				left.append(m)
				continue
			m["text_sent"] = true
			m["dests"] = oks
		if m.has("img"):
			var p := SHOTS.path_join(str(m["img"]) + ".jpg")
			var jpg := FileAccess.get_file_as_bytes(p) if FileAccess.file_exists(p) else PackedByteArray()
			if not jpg.is_empty():
				var h := PackedStringArray(["Title: " + _hdr(title + " · Bildschirmfoto"), "Tags: camera", "Filename: moveeye_rueckmeldung.jpg",
						"Message: " + _hdr("Bildschirmfoto zur Rückmeldung von " + str(m.get("t", "")).substr(0, 16).replace("T", " ")), "Content-Type: image/jpeg"])
				var any := false
				for i in m.get("dests", [0, 1]):
					if int(i) < us.size() and await _req(us[int(i)], jpg, h, HTTPClient.METHOD_PUT):
						any = true
				if not any:
					left.append(m)
					continue
		sent += 1
	# keep what was written meanwhile
	for m in _load():
		if not box.any(func(o): return str(o.get("t", "")) == str(m.get("t", "")) and str(o.get("body", "")) == str(m.get("body", ""))):
			left.append(m)
	_save(left)
	if sent > 0 and mehr != null and mehr.protokoll != null:
		mehr.protokoll.add("rueckmeldung", "Rückmeldung gesendet (%d)%s" % [sent, " – Testmodus: " + test_url if test_url != "" else ""])
	_busy = false
	if visible:
		_paint_wait()


func _process(dt: float) -> void:
	_flush_t -= dt
	if _flush_t <= 0.0:
		_flush_t = 600.0
		if not _load().is_empty():
			flush()


func _unhandled_key_input(e: InputEvent) -> void:
	if visible and e is InputEventKey and e.pressed and (e as InputEventKey).keycode == KEY_ESCAPE:
		visible = false
		get_viewport().set_input_as_handled()


func status() -> Dictionary:
	return {"open": visible, "connected": connected(), "waiting": _load().size(), "errors": errs, "ok_t": ok_t, "test_url": test_url, "last": last,
			"kind": _kind, "stars": _stars, "busy": _busy, "peek": _peek.text if _peek != null else ""}
