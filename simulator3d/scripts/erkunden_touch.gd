extends CanvasLayer
## «Frei erkunden mit eigener Figur» (Besitzer 21.11.2026): die Knöpfe für Handy / iPad am linken Bildrand, solange man als
## Figur erkundet (der grüne Stick zum Gehen bleibt unten rechts, rover_pad.gd):
##   * Haltung (gross): stehen → geduckt → kriechen → stehen - das Symbol zeigt die Haltung JETZT (wie Taste C)
##   * Sitzen (X), Hinlegen (Z), Springen / Hochklettern (Leertaste) - nochmals Sitzen / Hinlegen = aufstehen
##   * Ansicht (V): hinter der Figur → aus den Augen → von oben
## Die Symbole sind gezeichnet (keine Emoji-Schrift nötig). Gross genug für Daumen (≥ 60 px, auf dem Handy grösser).

const T = preload("res://scripts/i18n.gd")

var person                           # explore_person.gd
var root: Control
var knoepfe := {}                    # id -> Knopf
var forced := -1                     # tests / screenshots: 1 = always shown, 0 = never, -1 = touch screen


class Knopf extends Control:
	var id := ""
	var symbol := ""
	var aktiv := false
	var gross := false
	var tap: Callable
	var _down := false

	func _gui_input(ev: InputEvent) -> void:
		if (ev is InputEventScreenTouch or (ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT)):
			if ev.pressed and not _down:
				_down = true
				if tap.is_valid():
					tap.call()
			elif not ev.pressed:
				_down = false
			queue_redraw()
			accept_event()

	func _draw() -> void:
		var r := minf(size.x, size.y) * 0.5
		var c := size * 0.5
		var col := Color(0.35, 0.75, 1.0) if aktiv else Color(0.9, 0.93, 0.96)
		draw_circle(c, r, Color(0.05, 0.07, 0.09, 0.62 if not _down else 0.85))
		draw_arc(c, r - 1.5, 0.0, TAU, 40, Color(col.r, col.g, col.b, 0.95), 3.0, true)
		Knopf.figur(self, symbol, c, r * 0.62, col)

	static func figur(ci: CanvasItem, s: String, c: Vector2, k: float, col: Color) -> void:
		"""a small person: stand | geduckt | kriechen | sitzen | liegen | sprung | schwimmen | ansicht"""
		var w := maxf(2.5, k * 0.16)
		var L := func(a: Vector2, b: Vector2): ci.draw_line(c + a * k, c + b * k, col, w, true)
		var H := func(p: Vector2): ci.draw_circle(c + p * k, k * 0.17, col)
		match s:
			"geduckt":
				H.call(Vector2(0.15, -0.45))
				L.call(Vector2(0.05, -0.28), Vector2(-0.25, 0.15))            # back, bent forward
				L.call(Vector2(-0.25, 0.15), Vector2(0.15, 0.35))             # thigh
				L.call(Vector2(0.15, 0.35), Vector2(-0.05, 0.8))              # shin
				L.call(Vector2(0.0, -0.15), Vector2(0.45, 0.1))               # arm
			"kriechen", "liegen":
				H.call(Vector2(-0.72, 0.38))
				L.call(Vector2(-0.52, 0.48), Vector2(0.75, 0.55))             # body on the ground
				if s == "kriechen":
					L.call(Vector2(-0.45, 0.5), Vector2(-0.85, 0.75))         # arm reaching forward
					L.call(Vector2(0.35, 0.53), Vector2(0.5, 0.3))            # knee drawn up
					L.call(Vector2(0.5, 0.3), Vector2(0.75, 0.55))
				else:
					ci.draw_line(c + Vector2(-0.95, 0.75) * k, c + Vector2(0.95, 0.75) * k, col, w * 0.6, true)   # the ground
			"sitzen":
				H.call(Vector2(-0.1, -0.6))
				L.call(Vector2(-0.1, -0.42), Vector2(-0.1, 0.15))             # upright back
				L.call(Vector2(-0.1, 0.15), Vector2(0.45, 0.15))              # thigh level
				L.call(Vector2(0.45, 0.15), Vector2(0.45, 0.75))              # shin down
				ci.draw_line(c + Vector2(-0.55, 0.22) * k, c + Vector2(0.2, 0.22) * k, col, w * 0.7, true)   # the seat
			"sprung":
				H.call(Vector2(0.0, -0.75))
				L.call(Vector2(0.0, -0.57), Vector2(0.0, 0.05))
				L.call(Vector2(0.0, -0.4), Vector2(-0.4, -0.75))              # arms up
				L.call(Vector2(0.0, -0.4), Vector2(0.4, -0.75))
				L.call(Vector2(0.0, 0.05), Vector2(-0.3, 0.35))
				L.call(Vector2(-0.3, 0.35), Vector2(-0.1, 0.55))
				L.call(Vector2(0.0, 0.05), Vector2(0.3, 0.4))
				ci.draw_line(c + Vector2(-0.5, 0.85) * k, c + Vector2(0.5, 0.85) * k, col, w * 0.6, true)
			"schwimmen":
				H.call(Vector2(-0.55, 0.05))
				L.call(Vector2(-0.38, 0.15), Vector2(0.6, 0.25))
				L.call(Vector2(-0.3, 0.12), Vector2(-0.75, -0.25))
				for i in range(3):                                          # waves
					var x0 := -0.9 + 0.62 * i
					ci.draw_arc(c + Vector2(x0 + 0.15, 0.55) * k, k * 0.16, PI, TAU, 8, col, w * 0.6, true)
			"ansicht":
				ci.draw_arc(c, k * 0.55, 0.0, TAU, 24, col, w, true)           # an eye
				ci.draw_circle(c, k * 0.22, col)
			_:                                                              # standing
				H.call(Vector2(0.0, -0.72))
				L.call(Vector2(0.0, -0.54), Vector2(0.0, 0.2))
				L.call(Vector2(0.0, -0.35), Vector2(-0.35, 0.05))
				L.call(Vector2(0.0, -0.35), Vector2(0.35, 0.05))
				L.call(Vector2(0.0, 0.2), Vector2(-0.25, 0.85))
				L.call(Vector2(0.0, 0.2), Vector2(0.25, 0.85))


func _ready() -> void:
	layer = 6
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	for e in [["haltung", "Haltung wechseln (C): stehen → geduckt → kriechen"], ["sitzen", "Hinsetzen / aufstehen (X)"],
			["liegen", "Hinlegen und still liegen / aufstehen (Z)"], ["sprung", "Springen, an einer Kante hochklettern (Leertaste)"],
			["ansicht", "Ansicht (V): hinter der Figur, aus den Augen, von oben"]]:
		var b := Knopf.new()
		b.id = str(e[0])
		b.symbol = "sprung" if b.id == "sprung" else ("ansicht" if b.id == "ansicht" else b.id)
		b.tooltip_text = T.t(str(e[1]))
		b.mouse_filter = Control.MOUSE_FILTER_STOP
		var bid := b.id
		b.tap = func(): person.touch_tipp(bid)
		root.add_child(b)
		knoepfe[b.id] = b
	get_viewport().size_changed.connect(_layout)
	_layout()
	visible = false


func _layout() -> void:
	var s: Vector2 = get_viewport().get_visible_rect().size if is_inside_tree() else Vector2(1280, 720)
	var k := clampf(minf(s.x, s.y) / 720.0, 0.62, 1.35)
	var hoch := s.y > s.x
	var gr := clampf(minf(s.x, s.y) * (0.2 if hoch else 0.13), 72.0, 112.0)    # the posture button: the biggest
	var kl := gr * 0.78
	var pad := 14.0 * k + 6.0
	var y := s.y - pad - gr - (s.y * 0.06 if hoch else 0.0)
	var hb: Knopf = knoepfe["haltung"]
	hb.size = Vector2(gr, gr)
	hb.position = Vector2(pad, y)
	var order := ["sprung", "sitzen", "liegen", "ansicht"]
	for i in range(order.size()):
		var b: Knopf = knoepfe[order[i]]
		b.size = Vector2(kl, kl)
		b.position = Vector2(pad + (gr - kl) * 0.5, y - (kl + pad * 0.6) * float(i + 1))
	for b in knoepfe.values():
		b.queue_redraw()


func zeigen() -> bool:
	if forced >= 0:
		return forced == 1
	return DisplayServer.is_touchscreen_available() or (person != null and person.ex != null and str(person.ex.device) == "touch")


func tick() -> void:
	var on: bool = person != null and person.ok() and bool(person.active) and zeigen() and not bool(person.ex.fly) \
			and not (person.gestalten != null and person.gestalten.offen)
	if visible != on:
		visible = on
		if on:
			_layout()
	if not on:
		return
	var h := str(person.haltung)
	var hb: Knopf = knoepfe["haltung"]
	var sym := h if h in ["geduckt", "kriechen"] else "stehen"
	if str(person.wasser) == "schwimmen":
		sym = "schwimmen"
	if hb.symbol != sym:
		hb.symbol = sym
		hb.queue_redraw()
	for id in ["sitzen", "liegen"]:
		var b: Knopf = knoepfe[id]
		var a: bool = h == id
		if b.aktiv != a:
			b.aktiv = a
			b.queue_redraw()


func info() -> Dictionary:
	var o := {"visible": visible}
	for id in knoepfe:
		var b: Knopf = knoepfe[id]
		o[id] = {"symbol": b.symbol, "aktiv": b.aktiv, "rect": [int(b.position.x), int(b.position.y), int(b.size.x), int(b.size.y)]}
	return o
