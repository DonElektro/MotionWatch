extends SceneTree
## Test «Karten der Geschichten» (Daniel 02.11.2026) ohne Bild, mit der echten Welt (main.tscn):
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/story_karten_test.gd" -- --no-update --no-tour
## Prüft an «Maggie und der Bergkristall»: die Startkarte «Ein Abendspaziergang» hat oben rechts «× Beenden»; Esc öffnet
## die Pause (die Karte bleibt darunter), Esc / «Weiter» bringt die Karte zurück; «× Beenden» beendet die Geschichte;
## eine Karte ohne laufende Geschichte schliesst Esc; «Das Hospiz» hat «× Beenden» auf seinen Karten; der Stream für
## MoveEye (padview.overlay_rects, dock=1) nimmt die Karte mit; Esc kommt über /view_input (MoveEye) an.
## Ende: «Story-Karten-Test OK» oder «SCRIPT ERROR: Story-Karten-Test: …» (Exit-Code 0 / 1).

var errs := []
var m = null


func _init() -> void:
	_start.call_deferred()


func _warte(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func _f(t: String) -> void:
	errs.append(t)


func _esc() -> void:
	var k := InputEventKey.new()
	k.keycode = KEY_ESCAPE
	k.physical_keycode = KEY_ESCAPE
	k.pressed = true
	Input.parse_input_event(k)
	await process_frame
	await process_frame
	var u := InputEventKey.new()
	u.keycode = KEY_ESCAPE
	u.physical_keycode = KEY_ESCAPE
	u.pressed = false
	Input.parse_input_event(u)
	await process_frame


func _xbtn(card: Control) -> Button:
	return card.find_child("Beenden", true, false) as Button if card != null and is_instance_valid(card) else null


func _start() -> void:
	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in range(60):
		await process_frame
	await _warte(1.0)
	var st = m.maggie
	if st == null:
		_f("main.maggie fehlt")
		_ende()
		return
	# 1. the start card «Ein Abendspaziergang»
	st.control({"do": "start", "name": "Test"})
	var t0 := Time.get_ticks_msec()
	while str(st.phase) != "intro" and Time.get_ticks_msec() - t0 < 120000:
		await _warte(0.25)
	if str(st.phase) != "intro" or st._card == null:
		_f("Startkarte kommt nicht (phase %s)" % st.phase)
		_ende()
		return
	await process_frame
	var card: Control = st._card
	var x := _xbtn(card)
	if x == null or not x.visible:
		_f("Startkarte ohne «× Beenden»")
	elif x.get_global_rect().end.x < card.get_global_rect().end.x - 60.0 or x.get_global_rect().position.y > card.get_global_rect().position.y + 60.0:
		_f("«× Beenden» nicht oben rechts: %s in %s" % [x.get_global_rect(), card.get_global_rect()])
	if card.size.y > 500.0:                              # (the title wrapped letter by letter once: the card got taller than the window)
		_f("Startkarte zu hoch: %s" % card.size)
	# the stream (MoveEye's simulator page, dock=1) takes the card along
	if m.padview != null:
		var cr: Rect2 = card.get_global_transform_with_canvas() * Rect2(Vector2.ZERO, card.size)
		var hit := false
		for r in m.padview.overlay_rects():
			if (r as Rect2).encloses(cr):
				hit = true
		if not hit:
			_f("Stream (dock=1): die Startkarte fehlt in overlay_rects")
		for r in m.padview.overlay_rects():
			if m.ui_root != null and m.ui_root.is_visible_in_tree() and (r as Rect2).encloses(m.ui_root.get_global_rect()):
				_f("Stream (dock=1): das Bedienfeld wäre im Bild")
	# 2. Esc: the pause over the start card, Esc again: the card is back
	if m.news != null and m.news.visible:
		m.news.close(false)                             # «Neu in dieser Version» (fresh test HOME) would take the first Esc
	await process_frame
	await _esc()
	if str(st.phase) != "pause":
		_f("Esc auf der Startkarte: phase %s statt pause" % st.phase)
	elif is_instance_valid(card) and card.visible:
		_f("Esc: die Startkarte liegt noch sichtbar unter der Pause")
	if st._card == null or _xbtn(st._card) == null:
		_f("Pause ohne «× Beenden»")
	await _esc()
	if str(st.phase) != "intro" or st._card != card or not card.visible:
		_f("Esc in der Pause: nicht zurück zur Startkarte (phase %s)" % st.phase)
	# the same with Esc from MoveEye (view_input, key «Escape»)
	if not m.VIEW_KEYS.has("Escape"):
		_f("VIEW_KEYS ohne Escape")
	else:
		m.view_input([{"t": "key", "k": "Escape", "down": true}])
		await process_frame
		await process_frame
		m.view_input([{"t": "key", "k": "Escape", "down": false}])
		await process_frame
		if str(st.phase) != "pause":
			_f("Esc von MoveEye: phase %s statt pause" % st.phase)
		st._unpause()
	# 3. «× Beenden» ends the story
	x = _xbtn(st._card)
	if x != null:
		x.pressed.emit()
		await process_frame
		if bool(st.running) or st._card != null:
			_f("«× Beenden»: die Geschichte läuft noch (phase %s)" % st.phase)
	# 4. a card without the story running: Esc closes it
	st._ensure_ui()
	st._continue_card()
	await process_frame
	if st._card == null or _xbtn(st._card) == null:
		_f("Karte «Weiter spielen?» ohne «× Beenden»")
	await _esc()
	if st._card != null:
		_f("Esc schliesst die Karte ohne laufende Geschichte nicht")
	# 5. «Das Hospiz»: «× Beenden» on its cards too
	var h = m.get("horror")
	if h != null:
		if h.has_method("_ensure_ui"):
			h._ensure_ui()
		if h.get("_ui") != null:
			h._new_card("Test", Color.RED, 500)
			if _xbtn(h._card) == null:
				_f("Hospiz-Karte ohne «× Beenden»")
			h.card_quit()
			await process_frame
			if h._card != null:
				_f("Hospiz: «× Beenden» schliesst die Karte nicht")
	_ende()


func _ende() -> void:
	if errs.is_empty():
		print("Story-Karten-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Story-Karten-Test: " + str(e))
		quit(1)
