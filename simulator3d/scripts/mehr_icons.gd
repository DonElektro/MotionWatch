extends RefCounted
## 3D-4.2x «Mehr» (Wunsch Daniel 30.10.2026): gezeichnete Symbole für «Mehr», Rückmeldung, Selbstdiagnose, Protokoll,
## Ansicht – keine Emoji (die Schrift von Godot kann die meisten nicht). Gezeichnet in einem Feld 20 × 20 um c (wie
## ui_style.gd _draw_group_icon, das unbekannte Symbole hierher weitergibt). Keine Abhängigkeit zu ui_style.gd (kein
## Kreis beim Laden). Dazu Blinki, die kleine Figur aus dem MoveEye-Logo (wie quelle/589_blinki.py).

const KINDS := ["more", "help", "chat", "info", "steth", "log", "update", "theme", "tour", "bug", "bulb", "star", "star_on",
		"question", "copy", "x", "sun", "moon", "trash", "play"]


static func draw(d: CanvasItem, kind: String, c: Vector2, col: Color, w := 1.8) -> bool:
	"""draws the symbol, false = unknown"""
	match kind:
		"more":                                       # ⋯
			for x in [-6.0, 0.0, 6.0]:
				d.draw_circle(c + Vector2(x, 0), 1.9, col)
		"help":                                       # ? in a circle
			d.draw_arc(c, 8.0, 0.0, TAU, 28, col, w, true)
			d.draw_arc(c + Vector2(0, -2.6), 3.0, PI * 1.05, PI * 2.35, 12, col, w, true)
			d.draw_line(c + Vector2(0.6, 0.2), c + Vector2(0, 2.4), col, w, true)
			d.draw_circle(c + Vector2(0, 5.0), 1.2, col)
		"chat":                                       # speech bubble
			d.draw_polyline(PackedVector2Array([c + Vector2(-8, -6), c + Vector2(8, -6), c + Vector2(8, 4), c + Vector2(-1, 4),
					c + Vector2(-5, 8), c + Vector2(-4, 4), c + Vector2(-8, 4), c + Vector2(-8, -6)]), col, w, true)
			for x in [-4.0, 0.0, 4.0]:
				d.draw_circle(c + Vector2(x, -1), 1.1, col)
		"info":
			d.draw_arc(c, 8.0, 0.0, TAU, 28, col, w, true)
			d.draw_circle(c + Vector2(0, -4), 1.3, col)
			d.draw_line(c + Vector2(0, -1), c + Vector2(0, 5), col, 2.0, true)
		"steth":                                      # stethoscope (Selbstdiagnose)
			d.draw_arc(c + Vector2(-2, -4), 4.5, 0.0, PI, 12, col, w, true)
			d.draw_line(c + Vector2(-6.5, -4), c + Vector2(-6.5, -8), col, w, true)
			d.draw_line(c + Vector2(2.5, -4), c + Vector2(2.5, -8), col, w, true)
			d.draw_polyline(PackedVector2Array([c + Vector2(-2, 0.5), c + Vector2(-2, 4), c + Vector2(1, 7.5), c + Vector2(5, 6), c + Vector2(6, 1.5)]), col, w, true)
			d.draw_arc(c + Vector2(6, -1), 2.4, 0.0, TAU, 12, col, w, true)
		"log":                                        # a page with lines
			d.draw_rect(Rect2(c + Vector2(-6.5, -8), Vector2(13, 16)), col, false, w)
			for y in [-4.0, -0.5, 3.0]:
				d.draw_line(c + Vector2(-3.5, y), c + Vector2(3.5, y), col, 1.4, true)
		"update":                                     # circular arrow
			d.draw_arc(c, 7.0, -PI * 0.15, PI * 1.55, 22, col, w, true)
			var tip := c + Vector2(cos(-PI * 0.15), sin(-PI * 0.15)) * 7.0
			d.draw_colored_polygon(PackedVector2Array([tip + Vector2(-3.5, -3.5), tip + Vector2(3.0, -1.0), tip + Vector2(-1.0, 3.2)]), col)
		"theme":                                      # ◐ like the button of the MoveEye window
			d.draw_arc(c, 7.5, 0.0, TAU, 28, col, w, true)
			var pts := PackedVector2Array()
			for i in range(15):
				var a := -PI * 0.5 + PI * i / 14.0
				pts.append(c + Vector2(-cos(a), sin(a)) * 7.5)
			d.draw_colored_polygon(pts, col)
		"sun":
			d.draw_circle(c, 3.6, col)
			for i in range(8):
				var a := TAU * i / 8.0
				d.draw_line(c + Vector2(cos(a), sin(a)) * 5.6, c + Vector2(cos(a), sin(a)) * 8.4, col, 1.6, true)
		"moon":
			d.draw_arc(c, 7.0, PI * 0.35, PI * 1.65, 20, col, w, true)
			d.draw_arc(c + Vector2(3.5, 0), 5.2, PI * 0.62, PI * 1.38, 14, col, w, true)
		"tour":                                       # a small Blinki
			blinki(d, c + Vector2(-blinki_width(20.0) / 2.0, -10), 20.0, "normal", 0.0, 0.0, col)
		"bug":
			d.draw_arc(c + Vector2(0, 1.5), 5.5, 0.0, TAU, 20, col, w, true)
			d.draw_line(c + Vector2(0, -4), c + Vector2(0, 7), col, 1.4, true)
			d.draw_arc(c + Vector2(0, -5), 2.6, PI, TAU, 8, col, w, true)
			for s in [-1.0, 1.0]:
				d.draw_line(c + Vector2(5 * s, -1), c + Vector2(8.5 * s, -3), col, 1.4, true)
				d.draw_line(c + Vector2(5.5 * s, 2.5), c + Vector2(9 * s, 2.5), col, 1.4, true)
				d.draw_line(c + Vector2(5 * s, 5.5), c + Vector2(8 * s, 8), col, 1.4, true)
		"bulb":
			d.draw_arc(c + Vector2(0, -2.5), 5.5, PI * 0.8, PI * 2.2, 18, col, w, true)
			d.draw_line(c + Vector2(-3, 2.2), c + Vector2(-2.5, 5), col, w, true)
			d.draw_line(c + Vector2(3, 2.2), c + Vector2(2.5, 5), col, w, true)
			d.draw_line(c + Vector2(-2.5, 6), c + Vector2(2.5, 6), col, w, true)
			d.draw_line(c + Vector2(-1.5, 8.2), c + Vector2(1.5, 8.2), col, w, true)
		"star", "star_on":
			var sp := PackedVector2Array()
			for i in range(11):
				var a := -PI * 0.5 + PI * i / 5.0
				var r := 8.5 if i % 2 == 0 else 3.6
				sp.append(c + Vector2(cos(a), sin(a)) * r)
			if kind == "star_on":
				sp.remove_at(sp.size() - 1)
				d.draw_colored_polygon(sp, col)
			else:
				d.draw_polyline(sp, col, 1.5, true)
		"question":
			d.draw_arc(c + Vector2(0, -3.5), 4.2, PI * 1.0, PI * 2.4, 14, col, 2.0, true)
			d.draw_line(c + Vector2(0.8, -0.2), c + Vector2(0, 3.0), col, 2.0, true)
			d.draw_circle(c + Vector2(0, 6.6), 1.4, col)
		"copy":
			d.draw_rect(Rect2(c + Vector2(-7, -4), Vector2(10, 12)), col, false, w)
			d.draw_polyline(PackedVector2Array([c + Vector2(-3, -4), c + Vector2(-3, -8), c + Vector2(7, -8), c + Vector2(7, 4), c + Vector2(3, 4)]), col, w, true)
		"x":
			d.draw_line(c + Vector2(-6, -6), c + Vector2(6, 6), col, 2.0, true)
			d.draw_line(c + Vector2(6, -6), c + Vector2(-6, 6), col, 2.0, true)
		"trash":
			d.draw_line(c + Vector2(-7, -5), c + Vector2(7, -5), col, w, true)
			d.draw_polyline(PackedVector2Array([c + Vector2(-5, -5), c + Vector2(-4, 8), c + Vector2(4, 8), c + Vector2(5, -5)]), col, w, true)
			d.draw_line(c + Vector2(-2, -8), c + Vector2(2, -8), col, w, true)
		"play":
			d.draw_colored_polygon(PackedVector2Array([c + Vector2(-4, -7), c + Vector2(7, 0), c + Vector2(-4, 7)]), col)
		_:
			return false
	return true


static func icon(kind: String, col: Color, size := 20.0) -> Control:
	"""a small Control with the symbol (colour can change later: set_meta("col", …) + queue_redraw())"""
	var d := Control.new()
	d.custom_minimum_size = Vector2(size, size)
	d.mouse_filter = Control.MOUSE_FILTER_IGNORE
	d.set_meta("col", col)
	d.draw.connect(func():
		var k := size / 20.0
		d.draw_set_transform(Vector2.ZERO, 0.0, Vector2(k, k))
		draw(d, kind, Vector2(10, 10), d.get_meta("col", col))
		d.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE))
	return d


# ---- Blinki (quelle/589_blinki.py): eye = face, feet; since Daniel 31.10.2026 WITHOUT the orange fan (the logo keeps it,
# mw_logo.gd). Coordinates of the old 100 × 112 figure, cut out: x 26 … 74, y 59 … 111 (48 × 52). The mood signs (corners,
# arrow, heart, dots) are drawn by blinki_bubble in a small speech bubble (like BLINKI_BUB of 589).
const BK_O := Color("#ff9f43")
const BK_O2 := Color("#e8590c")
const BK_W := Color("#ffffff")
const BK_D := Color("#0a0e14")
const BK_X0 := 26.0
const BK_Y0 := 59.0
const BK_VW := 48.0
const BK_VH := 52.0


static func blinki_width(height: float) -> float:
	return height * BK_VW / BK_VH


static func blinki_fit(box: Vector2) -> Rect2:
	"""the biggest Blinki that fits in box, centred (position = top-left corner, size.y = the height for blinki())"""
	var h: float = minf(box.y, box.x * BK_VH / BK_VW)
	var w := blinki_width(h)
	return Rect2(Vector2((box.x - w) / 2.0, (box.y - h) / 2.0), Vector2(w, h))


static func blinki(d: CanvasItem, pos: Vector2, height: float, mood := "normal", look := 0.0, lid := 0.0, line := Color("#e8eef5"),
		hop := 0.0, talk := 0.0, red := false) -> void:
	"""draws Blinki with its top-left corner at pos. look -1 … 1 (pupil left / right), lid 0 … 1 (blink), hop = jump in
	units of the viewBox, talk = eye pulse 0 … 1; red: the dim colours of the red light view (like html.sxnight .bk).
	line is not used any more (the corners are in blinki_bubble now)"""
	var o: Color = Color("#7a160e") if red else BK_O
	var o2: Color = Color("#5a0f0a") if red else BK_O2
	var wh: Color = Color("#2a0606") if red else BK_W
	var dk: Color = Color("#000000") if red else BK_D
	var k := height / BK_VH
	var P := func(x: float, y: float) -> Vector2:
		return pos + Vector2(x - BK_X0, y - hop - BK_Y0) * k
	for fx in [39.0, 61.0]:                                # feet
		var fp := PackedVector2Array()
		for i in range(16):
			var a := TAU * i / 16.0
			fp.append(pos + Vector2(fx + cos(a) * 7.5 - BK_X0, 105.5 + sin(a) * 3.8 - BK_Y0) * k)
		d.draw_colored_polygon(fp, o2)
	# the eye («talk» = a little pulse of the eye, like .bk.talk .bk-eye)
	var ec: Vector2 = P.call(50.0, 80.0)
	var ke := k * (1.0 + 0.05 * talk)
	d.draw_circle(ec, 17.0 * ke, wh)
	if mood == "happy":
		var q := PackedVector2Array()
		for i in range(17):
			var t := i / 16.0
			q.append(ec + Vector2(-9.5 + 19.0 * t, 3.5 - 25.0 * t * (1.0 - t)) * ke)
		d.draw_polyline(q, dk, max(1.0, 3.6 * ke), true)
	else:
		var off: Vector2 = {"point": Vector2(5, -1), "think": Vector2(-4, -5)}.get(mood, Vector2(5.0 * clampf(look, -1.0, 1.0), 0.0))
		d.draw_circle(ec + off * ke, 10.5 * ke, o)
		d.draw_circle(ec + off * ke, 5.2 * ke, dk)
		if not red:
			d.draw_circle(ec + (off + Vector2(3.2, -3.4)) * ke, 2.0 * ke, BK_W)
		if lid > 0.02:                                     # the lid comes down from the top: the part of the eye above «cut»
			var sn := clampf(-1.0 + 2.0 * clampf(lid, 0.0, 1.0), -1.0, 1.0)
			var a0 := PI - asin(sn)
			var a1 := TAU + asin(sn)
			var lp := PackedVector2Array()
			for i in range(21):
				var a := a0 + (a1 - a0) * i / 20.0
				lp.append(ec + Vector2(cos(a), sin(a)) * 17.0 * ke)
			if a1 - a0 > 0.05:
				d.draw_colored_polygon(lp, o2)
	d.draw_arc(ec, 17.0 * ke, 0.0, TAU, 32, o2, max(1.0, 2.6 * ke), true)


static func _bk_round(pts: PackedVector2Array, c: Vector2, r: float, a0: float) -> void:
	for i in range(7):
		var a := a0 + PI * 0.5 * i / 6.0
		pts.append(c + Vector2(cos(a), sin(a)) * r)


static func blinki_bubble(d: CanvasItem, pos: Vector2, height: float, mood: String, alpha: float, line := Color("#e8eef5"),
		bg := Color("#0b1016"), edge := Color("#2a3646"), red := false) -> void:
	"""the mood bubble of Blinki (pos / height like blinki()): above right of the eye, tail to the eye; alpha 0 … 1 (also
	a small pop). Same place and shape as BLINKI_BUB / .bk-bub in 589 (bubble viewBox 28 19 44 47, scale 0.75)"""
	if alpha <= 0.01:
		return
	if red:
		line = Color("#7d1f1a")
		bg = Color("#120202")
		edge = Color("#5a0f0a")
	var k := height / BK_VH
	var s := 0.75 * (0.8 + 0.2 * clampf(alpha, 0.0, 1.0))
	var B := func(x: float, y: float) -> Vector2:          # bubble coordinates -> screen (tail tip (30, 64) at (58, 63))
		return pos + Vector2(58.0 + (x - 30.0) * s - BK_X0, 63.0 + (y - 64.0) * s - BK_Y0) * k
	var a := clampf(alpha, 0.0, 1.0)
	var lc := Color(line, line.a * a)
	var o2: Color = Color("#5a0f0a") if red else BK_O2
	# the outline: M39 21 H61 A8 69 29 V49 A8 61 57 H47 L30 64 L39 57 A8 31 49 V29 A8 39 21 Z
	var pl := PackedVector2Array()
	_bk_round(pl, Vector2(61, 29), 8.0, -PI * 0.5)
	_bk_round(pl, Vector2(61, 49), 8.0, 0.0)
	pl.append(Vector2(47, 57))
	pl.append(Vector2(30, 64))
	_bk_round(pl, Vector2(39, 49), 8.0, PI * 0.5)
	_bk_round(pl, Vector2(39, 29), 8.0, PI)
	var sp := PackedVector2Array()
	for p in pl:
		sp.append(B.call(p.x, p.y))
	d.draw_colored_polygon(sp, Color(bg, bg.a * a))
	sp.append(sp[0])
	d.draw_polyline(sp, Color(edge, edge.a * a), max(1.0, 1.4 * s * k), true)
	var lw: float = max(1.0, 3.0 * s * k)
	for seg in [[37, 33, 37, 27, 43, 27], [57, 27, 63, 27, 63, 33], [63, 45, 63, 51, 57, 51], [43, 51, 37, 51, 37, 45]]:
		d.draw_polyline(PackedVector2Array([B.call(seg[0], seg[1]), B.call(seg[2], seg[3]), B.call(seg[4], seg[5])]), lc, lw, true)
	if mood == "point":
		d.draw_polyline(PackedVector2Array([B.call(46, 33.5), B.call(54.5, 39), B.call(46, 44.5)]), lc, max(1.0, 3.2 * s * k), true)
	elif mood == "think":
		for cx in [43.5, 50.0, 56.5]:
			d.draw_circle(B.call(cx, 39.0), 2.4 * s * k, lc)
	elif mood == "happy":                                 # a heart
		var hc := Color(o2, a)
		d.draw_circle(B.call(46.6, 37.6), 3.9 * s * k, hc)
		d.draw_circle(B.call(53.4, 37.6), 3.9 * s * k, hc)
		d.draw_colored_polygon(PackedVector2Array([B.call(43, 39.5), B.call(57, 39.5), B.call(50, 46.5)]), hc)
