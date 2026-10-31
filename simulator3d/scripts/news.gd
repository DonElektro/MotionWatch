extends PanelContainer
## 3D-3.82 (Wunsch Daniel, während dem grossen Makeover): nach jedem Update erscheint einmal eine kurze Info «Neu in dieser
## Version» - alle Versionen seit der zuletzt gesehenen (aus neu_data.gd, erzeugt aus «Lies mich.txt») und «Als Nächstes im
## Makeover» (NEXT_ALL ohne DONE, bei jeder Makeover-Version nachführen). main.news_seen / main.news_popup sind in KEEP.

var main
var _box: VBoxContainer

const UI = preload("res://scripts/ui_style.gd")
const Data = preload("res://scripts/neu_data.gd")

const NEXT_ALL := [
	[1, "Ein gemeinsames Erscheinungsbild (Web, Fenster, Simulator)"], [2, "Simulations-Modus sichtbar (oranger Streifen «SIMULATION»)"],
	[3, "Startseite mit Simulator-Kachel"], [4, "Kachel-Steuerung des Simulators auf dem Handy"], [5, "Kino-Modus (Vollbild für TV / Beamer)"],
	[6, "Einheitliche Ereignis-Symbole"], [7, "Simulator-Zentrale in MoveEye"], [8, "«Was wäre wenn …?» bei echten Alarmen"],
	[9, "Dein Platz (Ort, Winkel, Zonen, Patrouille)"], [10, "Zonen im Simulator sehen"], [11, "Erkennung live in der 3D-Ansicht"],
	[12, "Automatische Trainings-Nacht"], [13, "Einstellungs-Vergleich A/B"], [14, "Benachrichtigungen testen (Test-Kanal)"],
	[15, "Akku-, Wetter- und WLAN-Ausfall üben"], [16, "Mehrere MoveEye-Geräte im Simulator"], [17, "Rover voll integriert"],
	[18, "Tagebuch-Statistik aus dem Simulator"], [19, "Versionen vergleichen (Kurve)"], [20, "Ein-Klick-Demo"],
	[21, "Fehlalarm-Lernen"], [22, "Karte der blinden Flecken"], [23, "Nacht-Generalprobe vor dem Scharfschalten"],
	[24, "Schwellen automatisch einstellen"], [25, "Erkennungs-Check jede Woche"]]
const DONE := [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]                       # numbers already delivered (nachführen)


static func _vt(v: String) -> Array:
	var out := []
	for x in v.trim_prefix("3D-").split("."):
		out.append(int(x))
	return out


static func _newer(a: String, b: String) -> bool:
	"""a > b"""
	var x := _vt(a)
	var y := _vt(b)
	for i in range(maxi(x.size(), y.size())):
		var p: int = x[i] if i < x.size() else 0
		var q: int = y[i] if i < y.size() else 0
		if p != q:
			return p > q
	return false


func entries(seen: String) -> Array:
	var out := []
	for e in Data.LOG:
		var v: String = e[0]
		if (seen == "" and v == main.VERSION) or (seen != "" and _newer(v, seen) and not _newer(v, main.VERSION)):
			out.append(e)
	return out.slice(0, 6)


func next_list(n := 5) -> Array:
	var out := []
	for x in NEXT_ALL:
		if not (x[0] in DONE):
			out.append(x)
	return out.slice(0, n)


var _scroll: ScrollContainer = null
var _list: VBoxContainer = null


func _ready() -> void:
	visible = false
	add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.97), UI.ORG, 16, 14, 2))
	_box = VBoxContainer.new()
	_box.add_theme_constant_override("separation", 6)
	add_child(_box)


func check() -> void:
	"""at the start: show once per version"""
	if main.news_seen == main.VERSION or not main.news_popup:
		return
	var es := entries(main.news_seen)
	if es.is_empty():
		main.news_seen = main.VERSION
		main._settings_dirty = true
		return
	show_news(es)


func show_news(es := []) -> void:
	if es.is_empty():
		es = entries(main.news_seen) if main.news_seen != main.VERSION else []
	if es.is_empty():
		es = [Data.LOG[0]] if not Data.LOG.is_empty() else []
	for c in _box.get_children():
		c.queue_free()
	var tag := UI.small("MOVEEYE SIM · " + main.VERSION, UI.ORG)
	_box.add_child(tag)
	_box.add_child(UI.heading("✨ Neu in dieser Version"))
	# 3D-4.x: the list scrolls - the window is never higher than the screen, OK always reachable (Daniel 31.10.)
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 6)
	_scroll.add_child(_list)
	_box.add_child(_scroll)
	for e in es:
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 10)
		var v := Label.new()
		v.text = e[0]
		v.add_theme_color_override("font_color", UI.ACC)
		v.custom_minimum_size = Vector2(64, 0)
		v.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		h.add_child(v)
		var t := Label.new()
		t.text = e[1]
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		t.custom_minimum_size = Vector2(500, 0)
		t.add_theme_font_size_override("font_size", 13)
		h.add_child(t)
		_list.add_child(h)
	var nx := next_list()
	if not nx.is_empty():
		var hd := Label.new()
		hd.text = "→ Als Nächstes im Makeover (%d/%d erledigt)" % [DONE.size(), NEXT_ALL.size()]
		hd.add_theme_font_size_override("font_size", 14)
		_list.add_child(hd)
		for x in nx:
			_list.add_child(UI.small("   %d. %s" % [x[0], x[1]]))
	var b := HBoxContainer.new()
	b.alignment = BoxContainer.ALIGNMENT_END
	b.add_theme_constant_override("separation", 8)
	_box.add_child(b)
	var off := Button.new()
	off.text = "Nicht mehr anzeigen"
	off.pressed.connect(func(): close(true))
	b.add_child(off)
	var ok := Button.new()
	ok.text = "OK"
	ok.custom_minimum_size = Vector2(90, 0)
	UI.primary(ok)
	ok.pressed.connect(func(): close(false))
	b.add_child(ok)
	visible = true
	get_parent().move_child(self, -1)


func _unhandled_input(ev: InputEvent) -> void:
	if visible and ev is InputEventKey and ev.pressed and not ev.echo and ev.keycode == KEY_ESCAPE:
		close(false)
		get_viewport().set_input_as_handled()


func close(off: bool) -> void:
	visible = false
	main.news_seen = main.VERSION
	if off:
		main.news_popup = false
	main._settings_dirty = true


func _process(_dt: float) -> void:
	if visible:
		var vs := get_viewport_rect().size
		if _scroll != null and is_instance_valid(_scroll):
			var room := maxf(120.0, vs.y - 48.0 - (_box.get_combined_minimum_size().y - _scroll.get_combined_minimum_size().y) - 40.0)
			_scroll.custom_minimum_size = Vector2(_list.get_combined_minimum_size().x + 14.0, minf(_list.get_combined_minimum_size().y, room))
		size = get_combined_minimum_size()
		position = ((vs - size) / 2.0).floor()


func info() -> Dictionary:
	return {"visible": visible, "seen": main.news_seen, "popup": main.news_popup, "entries": entries(main.news_seen).map(func(e): return e[0]), "next": next_list().size()}
