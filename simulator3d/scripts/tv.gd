extends Control
## TV mode (3D-3.44): the simulator as a big screen for the games evening - on a television at the PC or at the HDMI of the Pi.
## The whole window shows the 3D world (the director of the spectators chooses the shots during a round, otherwise the camera
## glides slowly round the camp); on the right a panel with the game: the wizard while it is set up, the QR code to join, the
## countdown / time left, the players with their state, what happened and the ranking. All other buttons are hidden.
## Switched with the key T, from the panel (System), or from MoveEye (CONTROL action "tv").

const UI = preload("res://scripts/ui_style.gd")
const Qr = preload("res://scripts/qr.gd")
const Pics = preload("res://scripts/wizpics.gd")

var main
var on := false
var info_url := ""            # the product page of MoveEye (/info/) - shown when nothing is going on
var _was_full := false
var _t := 0.0
var _qr_for := ""
var _orbit := 0.0
var _key := ""

var side: PanelContainer
var title: Label
var clock: Label
var state_l: Label
var big: Label
var sub: Label
var qr: TextureRect
var qr_l: Label
var plist: VBoxContainer
var feed: Label
var shot: Label
var pics: HBoxContainer


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false
	# top left: name and clock on a dark strip
	var topbar := PanelContainer.new()
	topbar.add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.78), Color(UI.BG, 0.0), 14, 14, 0))
	topbar.position = Vector2(24, 20)
	add_child(topbar)
	var th := HBoxContainer.new()
	th.add_theme_constant_override("separation", 22)
	topbar.add_child(th)
	title = Label.new()
	title.text = "MoveEye"
	title.add_theme_font_override("font", UI.heading_font())
	title.add_theme_font_size_override("font_size", 30)
	th.add_child(title)
	clock = Label.new()
	clock.add_theme_font_size_override("font_size", 30)
	clock.add_theme_color_override("font_color", UI.MUT)
	th.add_child(clock)
	# bottom left: what the camera shows
	shot = Label.new()
	shot.add_theme_font_size_override("font_size", 24)
	shot.add_theme_color_override("font_color", Color.WHITE)
	shot.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	shot.add_theme_constant_override("outline_size", 8)
	shot.anchor_top = 1.0
	shot.anchor_bottom = 1.0
	shot.offset_left = 28
	shot.offset_top = -64
	shot.offset_bottom = -24
	add_child(shot)
	# right: the game
	side = PanelContainer.new()
	side.add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.86), UI.LINE, 0, 26, 0))
	side.anchor_left = 0.66
	side.anchor_right = 1.0
	side.anchor_bottom = 1.0
	add_child(side)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	side.add_child(v)
	state_l = Label.new()
	state_l.add_theme_font_size_override("font_size", 22)
	state_l.add_theme_color_override("font_color", UI.MUT)
	state_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(state_l)
	big = Label.new()
	big.add_theme_font_override("font", UI.heading_font())
	big.add_theme_font_size_override("font_size", 54)
	big.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(big)
	sub = Label.new()
	sub.add_theme_font_size_override("font_size", 24)
	sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(sub)
	pics = HBoxContainer.new()
	pics.add_theme_constant_override("separation", 10)
	v.add_child(pics)
	var qrow := HBoxContainer.new()
	qrow.add_theme_constant_override("separation", 18)
	v.add_child(qrow)
	var qbg := PanelContainer.new()
	qbg.add_theme_stylebox_override("panel", UI.box(Color.WHITE, Color.WHITE, 12, 10, 0))
	qrow.add_child(qbg)
	qr = TextureRect.new()
	qr.custom_minimum_size = Vector2(200, 200)
	qr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	qr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	qr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	qbg.add_child(qr)
	qr_l = Label.new()
	qr_l.add_theme_font_size_override("font_size", 20)
	qr_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	qr_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	qr_l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	qrow.add_child(qr_l)
	plist = VBoxContainer.new()
	plist.add_theme_constant_override("separation", 6)
	v.add_child(plist)
	feed = Label.new()
	feed.add_theme_font_size_override("font_size", 18)
	feed.add_theme_color_override("font_color", UI.MUT)
	feed.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(feed)


func set_on(v: bool, fullscreen := true) -> void:
	if v == on:
		return
	on = v
	visible = v
	position = Vector2.ZERO
	size = get_viewport_rect().size
	if main.ui_layer != null:
		main.ui_layer.visible = not v                    # all other buttons and pictures away
	if v:
		_was_full = DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
		if fullscreen and not _was_full:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
		main.set_view(0)
		main.follow = false
		_key = ""
	else:
		if not _was_full and DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		if main.spectate and not main.game_spectate:
			main.spectate_stop()


func state() -> Dictionary:
	return {"on": on, "info_url": info_url}


func idle_cam(dt: float) -> void:
	"""nothing is going on: the camera glides slowly round the camp"""
	var c: Vector3 = main.head.global_position if main.head != null else Vector3.ZERO
	_orbit += dt * 0.05
	var pos := c + Vector3(sin(_orbit) * 16.0, 0, cos(_orbit) * 16.0)
	pos.y = main.ground_y(pos.x, pos.z) + 7.0
	var want := Transform3D(Basis(), pos).looking_at(c + Vector3(0, 1.0, 0), Vector3.UP)
	main.view_cam.fov = 58.0
	main.view_cam.global_transform = main.view_cam.global_transform.interpolate_with(want, 1.0 - exp(-dt * 1.2))


func _process(dt: float) -> void:
	if not on:
		return
	_t += dt
	if _t < 0.5:
		return
	_t = 0.0
	if size != get_viewport_rect().size:
		size = get_viewport_rect().size
	var tm := Time.get_datetime_dict_from_system()
	clock.text = "%02d:%02d" % [tm.hour, tm.minute]
	var g = main.game
	var w = main.gamewiz
	# during a round the director of the spectators chooses the shots
	if g != null and g.open and g.round_state in ["countdown", "play", "end"] and not main.spectate:
		main.spectate_start()
	shot.text = _plain(main.spec_label) if main.spectate else ""
	if w != null and w.shown:
		_paint_wizard(w.model(), g)
	elif g != null and g.open:
		var gl = main.smalltv.game_live() if main.smalltv != null else null   # Aufräumen 2: one source with MoveEye's displays
		_paint_game(gl if gl != null else {}, g)
	else:
		_paint_idle()


func _set_qr(text: String, label: String) -> void:
	qr.get_parent().visible = text != ""
	qr_l.visible = text != ""
	if text != "" and text != _qr_for:
		_qr_for = text
		qr.texture = Qr.texture(text, 6)
	qr_l.text = label


func _players(list: Array) -> void:
	var key := JSON.stringify(list)
	if key == _key:
		return
	_key = key
	for c in plist.get_children():
		c.queue_free()
	for p in list:
		var row := PanelContainer.new()
		row.add_theme_stylebox_override("panel", UI.box(UI.PANEL, UI.LINE, 10, 10, 1))
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 12)
		row.add_child(h)
		var dot := ColorRect.new()
		dot.custom_minimum_size = Vector2(18, 18)
		dot.color = Color(str(p.get("c", "#3b8cff")))
		dot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(dot)
		var n := Label.new()
		n.text = str(p.get("n", ""))
		n.add_theme_font_size_override("font_size", 26)
		n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(n)
		var s := Label.new()
		s.text = str(p.get("s", ""))
		s.add_theme_font_size_override("font_size", 22)
		s.add_theme_color_override("font_color", UI.MUT)
		h.add_child(s)
		plist.add_child(row)


func _clear_pics() -> void:
	for c in pics.get_children():
		c.queue_free()


func _paint_wizard(m: Dictionary, g) -> void:
	state_l.text = "Das Spiel wird eingerichtet · Schritt %d von 4" % (int(m.get("step", 0)) + 1)
	big.text = str(m.get("title", ""))
	var chosen := []
	for c in m.get("cards", []):
		if bool(c.get("on", false)):
			chosen.append(str(c.get("title", "")))
	sub.text = ("Gewählt: " + ", ".join(chosen)) if not chosen.is_empty() else "Gleich geht es los."
	var want := []
	for c in m.get("cards", []):
		if bool(c.get("on", false)):
			want.append(str(c.get("v", "")))
	var pk := ",".join(want)
	if pics.get_meta("k", "") != pk:
		pics.set_meta("k", pk)
		_clear_pics()
		for k in want:
			var tx = Pics.texture(k, 1.0)
			if tx != null:
				var tr := TextureRect.new()
				tr.texture = tx
				tr.custom_minimum_size = Vector2(320, 180)
				tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
				tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
				pics.add_child(tr)
	pics.visible = not want.is_empty()
	if g != null and g.open:
		_set_qr(g.address(), "Mitspielen: QR-Code mit dem Handy scannen\n(gleiches WLAN)\n" + g.address())
	else:
		_set_qr("", "")
	_players([])
	feed.text = ""


func _paint_game(d: Dictionary, g) -> void:
	"""d = «game_live» (smalltv.gd): the same numbers and words as the TV page of MoveEye (150) and the SmallTV (552)"""
	pics.visible = false
	var r := str(d.get("round", "lobby"))
	var names := {"lobby": "Warte auf Spieler", "countdown": "Macht euch bereit", "play": "Runde läuft", "end": "Runde vorbei"}
	state_l.text = str(names.get(r, r)) + (" · " + str(d.get("goal", "")) if str(d.get("goal", "")) != "" else "")
	if r == "countdown":
		big.text = str(d.get("cd", ""))
	elif r == "play":
		var left := int(d.get("left", 0))
		big.text = "%d:%02d" % [left / 60, left % 60] + ("  letzte Minute!" if bool(d.get("lm", false)) else "")
	elif r == "end":
		big.text = "Ende"
	else:
		big.text = "%d Spieler" % d.get("players", []).size()
	sub.text = _plain(str(d.get("task", "")))
	var RW: Dictionary = d.get("win", {})             # the winner screen (gamerules.gd)
	if r == "end" and not RW.is_empty():
		big.text = _plain(str(RW.get("title", ""))) + ("  %d" % int(RW.get("score", -1)) if int(RW.get("score", -1)) >= 0 else "")
		sub.text = _plain(str(RW.get("hl", "")))
	var RN: String = str(d.get("next", ""))
	if r in ["lobby", "end"] and RN != "":
		sub.text = (sub.text + "\n" if sub.text != "" else "") + _plain(RN)
	if int(d.get("mw", 0)) > 0:
		sub.text = (sub.text + "\n" if sub.text != "" else "") + "MoveEye hat %d erwischt" % int(d.get("mw", 0))
	if r in ["lobby", "end"]:
		_set_qr(str(d.get("url", g.address())), "Mitspielen: QR-Code scannen\n(gleiches WLAN)\n" + str(d.get("url", g.address())))
	else:
		_set_qr("", "")
	var st := {"goal": "im Ziel", "out": "erwischt", "jail": "gefangen", "play": "unterwegs", "lobby": "bereit"}
	var list := []
	if r == "end" and not d.get("board", []).is_empty():
		var i := 0
		for b in d.get("board", []):
			i += 1
			list.append({"n": "%d. " % i + str(b.get("n", "")), "c": b.get("c", "#3b8cff"), "s": str(b.get("score", ""))})
	else:
		for p in d.get("players", []):
			var k := int(p.get("k", 0))
			list.append({"n": p.get("n", ""), "c": p.get("c", ""), "s": str(st.get(str(p.get("s", "")), str(p.get("s", "")))) + (" · %d×" % k if k > 0 else "") + " · %d Punkte" % int(p.get("pt", 0))})
	_players(list)
	var lines := []
	for e in d.get("feed", []):
		lines.append("• " + _plain(str(e)))
	feed.text = "\n".join(lines.slice(0, 4))


func _paint_idle() -> void:
	pics.visible = false
	state_l.text = main.status_text() if main.has_method("status_text") else ""
	big.text = "Gerade ist nichts los"
	sub.text = "MoveEye hält Wache. Ein Spiel startet man im Spiel-Assistenten – auf der Seite von MoveEye oder im Simulator."
	if info_url != "":
		_set_qr(info_url, "Mehr über MoveEye:\nQR-Code scannen\n" + info_url)
	else:
		_set_qr("", "")
	_players([])
	feed.text = ""


func _plain(t: String) -> String:
	"""without emoji (the font of a television PC may not have them)"""
	var o := ""
	for i in t.length():
		var c := t.unicode_at(i)
		if c < 0x2190 or (c >= 0x2500 and c < 0x2600 and false):
			o += t[i]
	return o.strip_edges()
