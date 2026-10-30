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
			blinki(d, c + Vector2(-8.9, -10), 20.0, "normal", 0.0, 0.0, col)
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


# ---- Blinki (quelle/589_blinki.py, viewBox 100 × 112): the fan = body, the eye at the bottom = face, the corners = mood ----
const BK_O := Color("#ff9f43")
const BK_O2 := Color("#e8590c")
const BK_W := Color("#ffffff")
const BK_D := Color("#0a0e14")


static func blinki(d: CanvasItem, pos: Vector2, height: float, mood := "normal", look := 0.0, lid := 0.0, line := Color("#e8eef5"),
		hop := 0.0, talk := 0.0, red := false) -> void:
	"""draws Blinki with its top-left corner at pos. look -1 … 1 (pupil left / right), lid 0 … 1 (blink), hop = jump in
	px of the viewBox, talk = fan pulse 0 … 1; red: the dim colours of the red light view (like html.sxnight .bk)"""
	var o: Color = Color("#7a160e") if red else BK_O
	var o2: Color = Color("#5a0f0a") if red else BK_O2
	var wh: Color = Color("#2a0606") if red else BK_W
	var dk: Color = Color("#000000") if red else BK_D
	if red:
		line = Color("#7d1f1a")
	var k := height / 112.0
	var tilt: float = deg_to_rad({"point": 7.0, "think": -5.0}.get(mood, 0.0))
	var P := func(x: float, y: float) -> Vector2:
		return pos + Vector2(x, y - hop) * k
	var R := func(x: float, y: float) -> Vector2:          # rotated around the eye (50, 80)
		var v := Vector2(x - 50.0, y - 80.0).rotated(tilt)
		return pos + (Vector2(50, 80 - hop) + v) * k
	for fx in [39.0, 61.0]:                                # feet
		var fp := PackedVector2Array()
		for i in range(16):
			var a := TAU * i / 16.0
			fp.append(pos + Vector2(fx + cos(a) * 7.5, 105.5 + sin(a) * 3.8) * k)
		d.draw_colored_polygon(fp, o2)
	# the fan: opaque at the eye, lighter at the top; «talk» = a little pulse
	var sc := 1.0 + 0.045 * talk
	var pts := PackedVector2Array([R.call(50.0, 80.0)])
	var cols := PackedColorArray([Color(o, 1.0)])
	for i in range(25):
		var g := deg_to_rad(-128.0 + 76.0 * i / 24.0)
		var y := 80.0 + 64.0 * sin(g) * sc
		pts.append(R.call(50.0 + 64.0 * cos(g) * sc, y))
		cols.append(Color(o, clampf(0.4 + 0.6 * (y - 16.0) / 64.0, 0.4, 1.0)))
	d.draw_polygon(pts, cols)
	var lw: float = max(1.0, 3.0 * k)
	var dx := 3.0 if mood == "point" else 0.0
	for seg in [[37, 33, 37, 27, 43, 27], [57, 27, 63, 27, 63, 33], [63, 45, 63, 51, 57, 51], [43, 51, 37, 51, 37, 45]]:
		d.draw_polyline(PackedVector2Array([R.call(seg[0] + dx, seg[1]), R.call(seg[2] + dx, seg[3]), R.call(seg[4] + dx, seg[5])]), line, lw, true)
	if mood == "point":
		d.draw_polyline(PackedVector2Array([R.call(46 + dx, 33.5), R.call(54.5 + dx, 39), R.call(46 + dx, 44.5)]), line, lw, true)
	elif mood == "think":
		for cx in [43.5, 50.0, 56.5]:
			d.draw_circle(R.call(cx, 39.0), 2.4 * k, line)
	elif mood == "happy":                                 # a heart in the frame
		d.draw_circle(R.call(46.6, 37.6), 3.9 * k, o2)
		d.draw_circle(R.call(53.4, 37.6), 3.9 * k, o2)
		d.draw_colored_polygon(PackedVector2Array([R.call(43, 39.5), R.call(57, 39.5), R.call(50, 46.5)]), o2)
	# the eye
	var ec: Vector2 = P.call(50.0, 80.0)
	d.draw_circle(ec, 17.0 * k, wh)
	if mood == "happy":
		var q := PackedVector2Array()
		for i in range(17):
			var t := i / 16.0
			q.append(P.call(40.5 + 19.0 * t, 83.5 - 25.0 * t * (1.0 - t)))
		d.draw_polyline(q, dk, max(1.0, 3.6 * k), true)
	else:
		var off: Vector2 = {"point": Vector2(5, -1), "think": Vector2(-4, -5)}.get(mood, Vector2(5.0 * clampf(look, -1.0, 1.0), 0.0))
		d.draw_circle(ec + off * k, 10.5 * k, o)
		d.draw_circle(ec + off * k, 5.2 * k, dk)
		if not red:
			d.draw_circle(ec + (off + Vector2(3.2, -3.4)) * k, 2.0 * k, BK_W)
		if lid > 0.02:                                     # the lid comes down from the top: the part of the eye above «cut»
			var sn := clampf(-1.0 + 2.0 * clampf(lid, 0.0, 1.0), -1.0, 1.0)
			var a0 := PI - asin(sn)
			var a1 := TAU + asin(sn)
			var lp := PackedVector2Array()
			for i in range(21):
				var a := a0 + (a1 - a0) * i / 20.0
				lp.append(ec + Vector2(cos(a), sin(a)) * 17.0 * k)
			if a1 - a0 > 0.05:
				d.draw_colored_polygon(lp, o2)
	d.draw_arc(ec, 17.0 * k, 0.0, TAU, 32, o2, max(1.0, 2.6 * k), true)
