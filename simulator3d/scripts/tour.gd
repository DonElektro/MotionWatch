extends CanvasLayer
## 3D-4.2x «Mehr» → Rundgang mit Blinki (Wunsch Daniel 30.10.2026), wie die Rundgänge von MoveEye (516 / 586 / 589):
## das Fenster wird abgedunkelt, nur das erklärte Teil bleibt hell (blauer Rahmen); daneben die Sprechblase mit Blinki
## (der kleinen Figur aus dem MoveEye-Logo), Punkte für die Schritte, «Später», «Überspringen», «Weiter ›» / «Fertig».
## Beim ersten Start einmal von selbst (nicht bei automatischen Läufen: --no-update / --no-tour, Kinder-Modus, Spiel,
## Testlauf), danach unter Mehr → «Rundgang mit Blinki». «Später» merkt sich den Schritt (weiter beim nächsten Start oder
## unter Mehr), «Überspringen» beendet ihn. Tasten: → / Enter weiter, ← zurück, Esc später.

var main
var mehr
var i := 0
var active := false
var _steps: Array = []
var _ov: Control                      # dims everything except the spot
var _bub: PanelContainer
var _bk: Control                      # Blinki
var _title: Label
var _text: Label
var _dots: Control
var _next: Button
var _back: Button
var _rect := Rect2()
var _btns: Array = []

const UI = preload("res://scripts/ui_style.gd")
const Icons = preload("res://scripts/mehr_icons.gd")


func _ready() -> void:
	layer = 63                                      # above the windows (60) and the look filter (62)
	_ov = Control.new()
	_ov.set_anchors_preset(Control.PRESET_FULL_RECT)
	_ov.mouse_filter = Control.MOUSE_FILTER_STOP
	_ov.draw.connect(_draw_ov)
	_ov.gui_input.connect(func(e):
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			go(1))
	add_child(_ov)
	_bub = PanelContainer.new()
	_bub.theme = UI.theme()
	add_child(_bub)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	_bub.add_child(v)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	v.add_child(row)
	_bk = BlinkiView.new()
	_bk.custom_minimum_size = Vector2(56, 64)
	_bk.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	row.add_child(_bk)
	var say := PanelContainer.new()
	say.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	say.set_meta("say", true)
	row.add_child(say)
	var sv := VBoxContainer.new()
	sv.add_theme_constant_override("separation", 4)
	say.add_child(sv)
	_title = Label.new()
	_title.add_theme_font_override("font", UI.heading_font())
	_title.add_theme_font_size_override("font_size", 15)
	_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_title.custom_minimum_size = Vector2(270, 0)
	sv.add_child(_title)
	_text = Label.new()
	_text.add_theme_font_size_override("font_size", 13)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.custom_minimum_size = Vector2(270, 0)
	sv.add_child(_text)
	var gb := HBoxContainer.new()
	gb.add_theme_constant_override("separation", 6)
	v.add_child(gb)
	_dots = Control.new()
	_dots.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_dots.custom_minimum_size = Vector2(60, 24)
	_dots.draw.connect(_draw_dots)
	gb.add_child(_dots)
	_back = _btn("‹", "Zurück (←)", func(): go(-1))
	gb.add_child(_back)
	gb.add_child(_btn("Später", "Den Rundgang später fortsetzen (Esc) – Mehr → Rundgang mit Blinki", func(): stop("later")))
	gb.add_child(_btn("Überspringen", "Den Rundgang beenden – er kommt nicht mehr von selbst", func(): stop("skipped")))
	_next = _btn("Weiter ›", "Weiter (→ / Enter)", func(): go(1))
	gb.add_child(_next)
	visible = false


func _btn(t: String, tip: String, f: Callable) -> Button:
	var b := Button.new()
	b.text = t
	b.tooltip_text = tip
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", 13)
	b.custom_minimum_size = Vector2(0, 30)
	b.pressed.connect(f)
	_btns.append(b)
	return b


# ---- the steps: what is explained and where it is ----------------------------------------------------------------------------
func _card(title: String) -> Control:
	for b in main.fold_bodies:
		if is_instance_valid(b) and str(b.get_meta("title", "")) == title:
			return b.get_meta("card", null)
	return null


func _quick_part(head: String) -> Array:
	"""the heading of the quick tiles (WELT, TESTEN …) and its tiles"""
	var q = main.quick
	if q == null or not is_instance_valid(q):
		return []
	var kids: Array = q.get_children()
	for k in range(kids.size()):
		var c = kids[k]
		if c is Label and str(c.text).strip_edges().to_upper() == head.to_upper():
			var out := [c]
			if k + 1 < kids.size() and kids[k + 1] is Control:
				out.append(kids[k + 1])
			return out
	return [q]


func _make_steps() -> Array:
	var tb: Control = main.toolbar if main.toolbar != null and main.toolbar.visible else null
	return [
		[[], "Hallo, ich bin Blinki!", "Ich bin das Auge von MoveEye. Ich zeige dir das Bedienfeld des Simulators Schritt für Schritt – und wenn ich blinzle, ist alles gut.", "normal"],
		[[tb] if tb != null else [], "Die Leiste unten", "Bewegen und Ansicht: Erkunden mit dem Rover, Rover-Route, Folgen, Kopf drehen, Versetzen, Stange, Mitspieler, Ansicht, Bedienfeld ein / aus, Hell / Rotlicht / Dunkel und «?». Mit der Maus über ein Symbol: sein Name.", "point"],
		[_quick_part("Welt"), "Welt", "Die Kacheln oben: Szene, Tageszeit, Wetter, Besuch, Gegenstände, echter Ort und Aufstellen – ein Klick, oder ein kleines Menü direkt an der Kachel.", "point"],
		[_quick_part("Testen"), "Testen", "Testlauf und Prüfstand messen mit festen Abläufen, wie gut MoveEye Personen und Tiere erkennt – auch nachts und bei Regen.", "point"],
		[_quick_part("Lernen"), "Lernen", "Trainingsbilder sammeln: damit lernt MoveEye ein eigenes KI-Modell – ohne echte Nächte.", "point"],
		[_quick_part("Spielen"), "Spielen und Spiel-Assistent", "Der Spiel-Assistent führt durch ein Spiel: «Team gegen MoveEye», «Entkomme der Kamera» … – mit Handys als Controller (QR-Code).", "point"],
		[[main.simple_seg] if main.simple_seg != null else [], "Einfach oder Experte", "«Einfach» zeigt nur das Wichtigste, «Experte» alle Einstellungen – wie in MoveEye. Daneben: Kinder / Erwachsene.", "point"],
		[[_card("Verbindung")] if _card("Verbindung") != null else [], "Verbindung zu MoveEye", "Hier schickt der Simulator seine Bilder an MoveEye. Das Symbol wird grün, sobald MoveEye verbunden ist; im anderen Netz hilft der Tunnel.", "point"],
		[[mehr.card] if mehr.card != null else [], "Mehr", "Hilfe, dieser Rundgang, Selbstdiagnose, Protokoll, Updates, Hell / Rotlicht / Dunkel, Rückmeldung an den Entwickler und «Über». Das «?» in der Leiste führt auch hierher. Viel Spass!", "happy"]]


# ---- start, steps, end -------------------------------------------------------------------------------------------------------
func start(from := 0) -> void:
	if main.kids_on:
		mehr.toast("Der Rundgang erklärt das Bedienfeld der Erwachsenen – zuerst oben «Erwachsene» wählen.")
		return
	main.show_panel(true)
	_steps = _make_steps()
	i = clampi(from, 0, _steps.size() - 1)
	active = true
	visible = true
	mehr.tour_state = "running"
	_paint(0)


func stop(how: String) -> void:
	"""how: done / skipped / later"""
	if not active:
		return
	active = false
	visible = false
	mehr.tour_state = how
	mehr.tour_step = i if how == "later" else 0
	main._settings_dirty = true
	if how == "later":
		mehr.toast("Rundgang pausiert – weiter unter Mehr → Rundgang mit Blinki (Schritt %d von %d)." % [i + 1, _steps.size()])
	elif how == "done":
		mehr.toast("Rundgang fertig – jederzeit wieder unter Mehr.")


func go(d: int) -> void:
	if not active:
		return
	var n := i + d
	if n >= _steps.size():
		stop("done")
		return
	if n < 0:
		return
	i = n
	_paint(d)


func _paint(d: int) -> void:
	var s: Array = _steps[i]
	_title.text = s[1]
	_text.text = s[2]
	_bk.mood = s[3]
	_bk.talk()
	if d > 0 and i > 0:
		_bk.hop()
	_next.text = "Fertig" if i == _steps.size() - 1 else "Weiter ›"
	_back.disabled = i == 0
	_style()
	for c in s[0]:                                    # into view (the panel scrolls)
		if c != null and is_instance_valid(c) and c.is_visible_in_tree():
			var sc := _scroll_of(c)
			if sc != null:
				sc.ensure_control_visible(c)
			break
	_dots.queue_redraw()


func _scroll_of(c: Node) -> ScrollContainer:
	var p := c.get_parent()
	while p != null:
		if p is ScrollContainer:
			return p
		p = p.get_parent()
	return null


func _target_rect() -> Rect2:
	var r := Rect2()
	for c in _steps[i][0]:
		if c != null and is_instance_valid(c) and c.is_visible_in_tree():
			var g: Rect2 = c.get_global_rect()
			r = g if r.size == Vector2.ZERO else r.merge(g)
	if r.size != Vector2.ZERO and main.ui_root != null and main.ui_root.visible and main.ui_root.get_global_rect().encloses(r.grow(-2)):
		var pr: Rect2 = main.ui_root.get_global_rect()          # not over the edge of the panel (scrolled parts)
		r = r.intersection(pr)
	return r


func _process(_dt: float) -> void:
	if not active:
		return
	var r := _target_rect()
	if r != _rect:
		_rect = r
		_ov.queue_redraw()
	_bub.reset_size()
	var vs: Vector2 = _ov.get_viewport_rect().size
	var bs := _bub.size
	var p: Vector2
	if _rect.size == Vector2.ZERO:
		p = (vs - bs) / 2.0
	else:
		var sp := _rect.grow(6)
		p = Vector2(sp.position.x + sp.size.x / 2.0 - bs.x / 2.0, sp.end.y + 10.0)
		if p.y + bs.y > vs.y - 8.0:
			p.y = sp.position.y - bs.y - 10.0
		if p.y < 8.0:                                 # tall parts (the panel): next to it, on the left
			p = Vector2(sp.position.x - bs.x - 14.0, clampf(sp.position.y + 20.0, 8.0, vs.y - bs.y - 8.0))
	p.x = clampf(p.x, 12.0, vs.x - bs.x - 12.0)
	p.y = clampf(p.y, 8.0, vs.y - bs.y - 8.0)
	_bub.position = p


func _draw_ov() -> void:
	var vs: Vector2 = _ov.size
	var dim := Color(0, 0, 0, 0.64)
	if _rect.size == Vector2.ZERO:
		_ov.draw_rect(Rect2(Vector2.ZERO, vs), dim)
		return
	var r := _rect.grow(6)
	_ov.draw_rect(Rect2(0, 0, vs.x, r.position.y), dim)
	_ov.draw_rect(Rect2(0, r.end.y, vs.x, vs.y - r.end.y), dim)
	_ov.draw_rect(Rect2(0, r.position.y, r.position.x, r.size.y), dim)
	_ov.draw_rect(Rect2(r.end.x, r.position.y, vs.x - r.end.x, r.size.y), dim)
	var acc: Color = UI.palette(UI.theme_now)["acc"] if UI.theme_now != "red" else Color("#a52a20")
	_ov.draw_rect(r.grow(2), acc, false, 3.0)


func _draw_dots() -> void:
	var n := _steps.size()
	var pal: Dictionary = UI.palette(UI.theme_now)
	for k in range(n):
		_dots.draw_circle(Vector2(4 + k * 11, 12), 3.5, pal["acc"] if k == i else pal["line"].lerp(pal["mut"], 0.35))


func _style() -> void:
	"""the bubble in the colours of the chosen look (it lies above the look filter, like the bubble of MoveEye)"""
	var pal: Dictionary = UI.palette(UI.theme_now)
	var sb := UI.box(pal["panel"], pal["line"], 14, 14, 1)
	sb.shadow_color = Color(0, 0, 0, 0.55)
	sb.shadow_size = 18
	_bub.add_theme_stylebox_override("panel", sb)
	var say: PanelContainer = _title.get_parent().get_parent() as PanelContainer
	say.add_theme_stylebox_override("panel", UI.box(pal["bg"], pal["line"], 14, 10, 1))
	_title.add_theme_color_override("font_color", pal["txt"])
	_text.add_theme_color_override("font_color", pal["mut"] if UI.theme_now != "dark" else Color("#9fb0c3"))
	for b in _btns:
		var main_b: bool = b == _next
		var bg: Color = pal["acc"] if main_b else pal["panel"].lerp(pal["line"], 0.6)
		for st in ["normal", "hover", "pressed", "focus"]:
			var x := UI.box(bg.lightened(0.08) if st == "hover" else bg, pal["acc"] if main_b else pal["line"], 10, 8, 1)
			b.add_theme_stylebox_override(st, x)
		b.add_theme_stylebox_override("disabled", UI.box(bg.darkened(0.2), pal["line"], 10, 8, 1))
		var fc: Color = Color.WHITE if main_b and UI.theme_now != "red" else pal["txt"]
		for k in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
			b.add_theme_color_override(k, fc)
		b.add_theme_color_override("font_disabled_color", pal["mut"])
	_bk.line = pal["txt"]
	_bk.red = UI.theme_now == "red"


func _unhandled_key_input(e: InputEvent) -> void:
	if not active or not (e is InputEventKey) or not e.pressed:
		return
	match (e as InputEventKey).keycode:
		KEY_ESCAPE:
			stop("later")
		KEY_RIGHT, KEY_ENTER, KEY_KP_ENTER:
			go(1)
		KEY_LEFT:
			go(-1)
		_:
			return
	get_viewport().set_input_as_handled()


func state() -> Dictionary:
	return {"active": active, "step": i, "steps": _steps.size(), "title": _title.text if active else "", "rect": [_rect.position.x, _rect.position.y, _rect.size.x, _rect.size.y],
			"state": mehr.tour_state, "saved_step": mehr.tour_step}


# ---- Blinki: blinks, looks around, hops, «talks» (like the CSS animations of 589) ------------------------------------------
class BlinkiView extends Control:
	var mood := "normal"
	var line := Color("#e8eef5")
	var red := false
	var t := 0.0
	var _hop := 9.0
	var _talk := 9.0

	func hop() -> void:
		_hop = 0.0

	func talk() -> void:
		_talk = 0.0

	func _process(dt: float) -> void:
		t += dt
		_hop += dt
		_talk += dt
		queue_redraw()

	func _draw() -> void:
		var cyc := fmod(t, 4.8) / 4.8                    # blink: 93 % … 94.5 % of 4.8 s
		var lid := 0.0
		if cyc > 0.9 and cyc < 0.975:
			lid = 1.0 - absf(cyc - 0.9375) / 0.0375
		var lk := fmod(t, 7.0) / 7.0                     # look left / right
		var look := 0.0
		if lk > 0.08 and lk < 0.84:
			look = -1.0 if lk < 0.44 else 1.0
		var hp := 0.0
		if _hop < 0.75:
			var u := _hop / 0.75
			hp = 13.0 * sin(PI * clampf((u - 0.15) / 0.47, 0.0, 1.0))
		var tk := 0.0
		if _talk < 1.28:
			tk = 0.5 - 0.5 * cos(TAU * _talk / 0.32)
		var h := size.y
		Icons.blinki(self, Vector2((size.x - h * 100.0 / 112.0) / 2.0, 0), h, mood, look, clampf(lid, 0.0, 1.0), line, hp, tk, red)
