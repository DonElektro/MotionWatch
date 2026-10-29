extends PanelContainer
## MoveEye 2.98.33 (Wunsch Daniel): «Rückmeldung an den Entwickler» aus dem Simulator. Kein eigener Versand: die Nachricht
## geht als Anfrage (mw_cmd «feedback») an das verbundene MoveEye, das sie wie alle Rückmeldungen anonym weiterschickt
## (Teil 370 / 584; das Bildschirmfoto holt MoveEye selbst über /view.jpg). Ist kein MoveEye verbunden, öffnet der Knopf
## die Seite «Mehr» von MoveEye (falls die Adresse bekannt ist), sonst steht dort, wo es die Rückmeldung gibt.

var main
var _kind: OptionButton
var _text: TextEdit
var _contact: LineEdit
var _shot: CheckBox
var _stars := 0
var _star_btns := []
var _status: Label
var _sent_id := 0

const UI = preload("res://scripts/ui_style.gd")
const KINDS := [["bug", "Fehler"], ["idea", "Wunsch"], ["praise", "Lob"], ["question", "Frage"]]


func _ready() -> void:
	visible = false
	add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.98), UI.ORG, 16, 14, 2))
	custom_minimum_size = Vector2(460, 0)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 7)
	add_child(box)
	box.add_child(UI.heading("Rückmeldung an den Entwickler"))
	var hint := UI.small("Fehler, Wünsche, Lob, Fragen – alles hilft. MoveEye schickt die Nachricht anonym weiter: kein Name, keine Adresse, ausser du schreibst sie hinein.")
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint.custom_minimum_size = Vector2(410, 0)
	box.add_child(hint)
	_kind = OptionButton.new()
	for k in KINDS:
		_kind.add_item(k[1])
	_kind.select(1)
	box.add_child(_kind)
	var sr := HBoxContainer.new()
	sr.add_theme_constant_override("separation", 4)
	var sl := UI.small("Wie zufrieden? (freiwillig)")
	sl.autowrap_mode = TextServer.AUTOWRAP_OFF
	sl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sr.add_child(sl)
	for i in range(1, 6):
		var b := Button.new()
		b.text = str(i)
		b.toggle_mode = true
		b.custom_minimum_size = Vector2(34, 0)
		b.tooltip_text = "%d von 5" % i
		b.pressed.connect(func(): _set_stars(i))
		_star_btns.append(b)
		sr.add_child(b)
	box.add_child(sr)
	_text = TextEdit.new()
	_text.placeholder_text = "Deine Nachricht …"
	_text.custom_minimum_size = Vector2(410, 110)
	_text.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	box.add_child(_text)
	_contact = LineEdit.new()
	_contact.placeholder_text = "Kontakt für eine Antwort (freiwillig)"
	_contact.max_length = 120
	box.add_child(_contact)
	_shot = CheckBox.new()
	_shot.text = "Bildschirmfoto mitschicken (Bild des Simulators)"
	box.add_child(_shot)
	box.add_child(UI.small("Immer dabei: Version von MoveEye und Simulator %s." % str(main.VERSION if main != null else "")))
	_status = UI.small("")
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status.custom_minimum_size = Vector2(410, 0)
	box.add_child(_status)
	var bt := HBoxContainer.new()
	bt.alignment = BoxContainer.ALIGNMENT_END
	bt.add_theme_constant_override("separation", 8)
	var cancel := Button.new()
	cancel.text = "Schliessen"
	cancel.pressed.connect(func(): visible = false)
	bt.add_child(cancel)
	var send := Button.new()
	send.text = "Senden"
	send.custom_minimum_size = Vector2(90, 0)
	UI.primary(send)
	send.pressed.connect(_send)
	bt.add_child(send)
	box.add_child(bt)


func _set_stars(i: int) -> void:
	_stars = 0 if _stars == i else i
	for j in range(_star_btns.size()):
		_star_btns[j].button_pressed = j < _stars


func connected() -> bool:
	return main.mw_addr != "" and main.now() - main.mw_t <= 10.0


func open() -> void:
	"""the button in the panel: the dialog when MoveEye is connected, else the page of MoveEye"""
	if not connected():
		if main.mw_addr != "":
			OS.shell_open("%s://%s:%d/more#feedback" % [str(main.mw.get("mw_scheme", "http")), main.mw_addr, int(main.mw.get("mw_port", 5000))])
			main.status_label.text = "MoveEye antwortet gerade nicht – die Seite «Mehr» von MoveEye ist geöffnet (Rückmeldung an den Entwickler)."
		else:
			main.status_label.text = "MoveEye ist nicht verbunden. Rückmeldung auf der Webseite von MoveEye: Mehr → Rückmeldung an den Entwickler (oder 💬 oben)."
		return
	_status.text = ""
	visible = true
	get_parent().move_child(self, -1)
	_place()
	_text.grab_focus()


func _place() -> void:
	"""in the middle of the window, as small as the content allows"""
	await get_tree().process_frame
	reset_size()
	await get_tree().process_frame
	reset_size()
	position = ((get_viewport_rect().size - size) / 2.0).max(Vector2(8, 8))


func fill_and_send(d: Dictionary) -> void:
	"""for tests over /control: fill the fields and press «Senden»"""
	_text.text = str(d.get("text", ""))
	for i in range(KINDS.size()):
		if KINDS[i][0] == str(d.get("kind", "idea")):
			_kind.select(i)
	_stars = 0
	_set_stars(int(d.get("stars", 0)))
	_shot.button_pressed = bool(d.get("shot", false))
	_send()


func _send() -> void:
	var t := _text.text.strip_edges()
	if t.length() < 3:
		_status.text = "Bitte ein paar Worte schreiben."
		return
	if not connected():
		_status.text = "MoveEye ist nicht mehr verbunden – bitte später nochmals."
		return
	var id: int = max(int(Time.get_unix_time_from_system() * 1000.0), int(main.mw_cmd.get("id", 0)) + 1)
	main.mw_cmd = {"id": id, "op": "feedback", "kind": KINDS[_kind.selected][0], "stars": _stars, "text": t.substr(0, 3000),
				   "contact": _contact.text.strip_edges(), "shot": _shot.button_pressed, "sim": main.VERSION}
	_sent_id = id
	_status.text = "Übergeben an MoveEye …"
	for i in range(30):
		await get_tree().create_timer(0.5).timeout
		var r = main.mw.get("refscan", null)
		if typeof(r) == TYPE_DICTIONARY and int(r.get("cmd_seen", 0)) >= id:
			_status.text = "Danke! MoveEye hat die Nachricht übernommen und schickt sie weiter (ohne Internet später)."
			_text.text = ""
			_set_stars(_stars)
			return
	_status.text = "MoveEye hat noch nicht geantwortet – die Nachricht bleibt bereit, solange MoveEye verbunden ist."
