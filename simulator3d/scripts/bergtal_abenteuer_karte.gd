extends Control
## Bergtal-Abenteuer: die alte Schatzkarte (vergilbte Landeskarte, 5 Stücke, Symbole, Weg, Sonne, Kompass) und die
## Treffer-Karte des Testgeländes (was MoveEye in der Nacht gesehen / verpasst hat, als Punkte um das Lager).
## Gezeichnet mit _draw (kein Bild pro Schritt) - billig, auch im Lite-Modus.

const Bt = preload("res://scripts/bergtal.gd")
const T = preload("res://scripts/i18n.gd")

var mode := "schatz"                 # schatz | treffer
var pieces: Array = []               # revealed piece numbers 0 … 4
var symbols: Array = []              # [[symbol, Vector2 valley]] of the revealed pieces
var route: PackedVector2Array = PackedVector2Array()        # walked so far (valley)
var plan: PackedVector2Array = PackedVector2Array()         # still to walk (valley)
var me := Vector2.INF                # GPS point (only «leicht»)
var compass := true
var sun_az := -1.0                   # degrees from north, < 0 = night
var sun_el := 0.0
var marks: Array = []                # own marks [[name, x, z]] (after the finale they are on the map)
# hit map: [{"x", "z", "path": [[t, x, z]], "st": seen | missed | hidden, "label"}] in world metres around MoveEye
var hits: Array = []
var cam_yaw := 0.0                   # where MoveEye looks (radians, world)
var hit_r := 60.0

# the 5 pieces (valley rectangles x0, z0, x1, z1) - each chapter reveals one
const PIECES := [[-50.0, -760.0, 420.0, 60.0], [-280.0, -420.0, 120.0, 60.0], [-900.0, -420.0, -100.0, -100.0],
		[-900.0, -200.0, -450.0, 620.0], [-960.0, 340.0, -480.0, 620.0]]
const AREA := [-960.0, -780.0, 460.0, 640.0]      # what the map shows (valley)
const PAPER := Color(0.86, 0.78, 0.6)
const INK := Color(0.33, 0.2, 0.1)
const RED := Color(0.72, 0.12, 0.08)


func _ready() -> void:
	custom_minimum_size = Vector2(300, 300)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _sq() -> Rect2:
	var s := minf(size.x, size.y)
	return Rect2((size.x - s) / 2.0, (size.y - s) / 2.0, s, s)


func to_px(q: Vector2) -> Vector2:
	var r := _sq()
	return r.position + Vector2((q.x - AREA[0]) / (AREA[2] - AREA[0]), (q.y - AREA[1]) / (AREA[3] - AREA[1])) * r.size


func _draw() -> void:
	if mode == "treffer":
		_draw_hits()
		return
	var r := _sq()
	draw_rect(r, PAPER)
	var tex := Bt.map_texture() if not Bt._hm.is_empty() else null
	for i in range(PIECES.size()):
		var p: Array = PIECES[i]
		var a := to_px(Vector2(p[0], p[1]))
		var b := to_px(Vector2(p[2], p[3]))
		var pr := Rect2(a, b - a)
		if i in pieces and tex != null:
			# the national map, old and yellowed (512 px = 2048 m, 4 m per pixel)
			var src := Rect2((p[0] - Bt.LO) / 4.0, (p[1] - Bt.LO) / 4.0, (p[2] - p[0]) / 4.0, (p[3] - p[1]) / 4.0)
			draw_texture_rect_region(tex, pr, src, Color(1.0, 0.86, 0.62))
			draw_rect(pr, Color(INK, 0.55), false, 1.5)
		elif not i in pieces:
			draw_rect(pr, Color(INK, 0.06))
			draw_rect(pr, Color(INK, 0.25), false, 1.0)
			var font := get_theme_default_font()
			draw_string(font, pr.get_center() + Vector2(-6, 8), "?", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(INK, 0.35))
	# folds of the old paper
	for k in range(1, 4):
		var x := r.position.x + r.size.x * k / 4.0
		draw_line(Vector2(x, r.position.y), Vector2(x, r.end.y), Color(INK, 0.12), 1.0)
		var y := r.position.y + r.size.y * k / 4.0
		draw_line(Vector2(r.position.x, y), Vector2(r.end.x, y), Color(INK, 0.12), 1.0)
	draw_rect(r, INK, false, 2.0)
	for sy in symbols:
		_symbol(str(sy[0]), to_px(sy[1]))
	if plan.size() >= 2:
		for i in range(plan.size() - 1):
			_dashed(to_px(plan[i]), to_px(plan[i + 1]), Color(RED, 0.55))
	if route.size() >= 2:
		var pts := PackedVector2Array()
		for q in route:
			pts.append(to_px(q))
		draw_polyline(pts, RED, 2.5, true)
	for mk in marks:
		var mp := to_px(Vector2(float(mk[1]), float(mk[2])))
		draw_circle(mp, 4.0, Color(0.5, 0.2, 0.7))
		draw_string(get_theme_default_font(), mp + Vector2(6, 4), str(mk[0]), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.4, 0.15, 0.55))
	if me != Vector2.INF:
		var mp2 := to_px(me)
		draw_circle(mp2, 7.0, Color(0.23, 0.55, 1.0, 0.35))
		draw_circle(mp2, 4.0, Color(0.23, 0.55, 1.0))
	if compass:
		_compass(r.position + Vector2(r.size.x - 34, 36))
	if sun_az >= 0.0:
		# the sun at the edge, in its direction (seen from the middle of the map)
		var d := Vector2(sin(deg_to_rad(sun_az)), -cos(deg_to_rad(sun_az)))
		var c := r.get_center()
		var t := 0.46 * r.size.x / maxf(absf(d.x), absf(d.y))
		var sp := c + d * minf(t, r.size.x * 0.46)
		var col := Color(0.95, 0.65, 0.1) if sun_el > 0.0 else Color(0.85, 0.4, 0.2)
		draw_circle(sp, 8.0, col)
		for k in range(8):
			var a2 := TAU * k / 8.0
			draw_line(sp + Vector2(cos(a2), sin(a2)) * 10.0, sp + Vector2(cos(a2), sin(a2)) * 14.0, col, 2.0)
		_dashed(c, sp - d * 16.0, Color(col, 0.6))


func _dashed(a: Vector2, b: Vector2, col: Color) -> void:
	var L := a.distance_to(b)
	var n := int(L / 6.0)
	for i in range(0, n, 2):
		draw_line(a.lerp(b, float(i) / maxf(1, n)), a.lerp(b, float(i + 1) / maxf(1, n)), col, 2.0)


func _compass(c: Vector2) -> void:
	draw_circle(c, 20.0, Color(PAPER, 0.9))
	draw_arc(c, 20.0, 0.0, TAU, 32, INK, 1.5)
	draw_colored_polygon(PackedVector2Array([c + Vector2(0, -17), c + Vector2(5, 0), c + Vector2(-5, 0)]), RED)
	draw_colored_polygon(PackedVector2Array([c + Vector2(0, 17), c + Vector2(5, 0), c + Vector2(-5, 0)]), INK)
	draw_string(get_theme_default_font(), c + Vector2(-4, -22), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, INK)


func _symbol(kind: String, p: Vector2) -> void:
	"""the symbols of the old map, drawn like ink"""
	match kind:
		"glocke":
			draw_arc(p + Vector2(0, -2), 7.0, PI, TAU, 12, INK, 2.0)
			draw_line(p + Vector2(-7, -2), p + Vector2(-9, 6), INK, 2.0)
			draw_line(p + Vector2(7, -2), p + Vector2(9, 6), INK, 2.0)
			draw_line(p + Vector2(-9, 6), p + Vector2(9, 6), INK, 2.0)
			draw_circle(p + Vector2(0, 9), 2.0, INK)
			draw_rect(Rect2(p + Vector2(-8, 13), Vector2(16, 5)), INK, false, 1.5)    # the well below
		"wellen":
			for k in range(2):
				var y := -5.0 + k * 8.0
				var pts := PackedVector2Array()
				for i in range(9):
					pts.append(p + Vector2(-10 + i * 2.5, y + sin(i * 1.2) * 2.5))
				draw_polyline(pts, Color(0.15, 0.3, 0.6), 2.0)
			draw_line(p + Vector2(-10, 10), p + Vector2(10, 10), INK, 2.0)
		"sonne":
			draw_circle(p + Vector2(0, -6), 5.0, Color(0.9, 0.55, 0.1))
			draw_polyline(PackedVector2Array([p + Vector2(-12, 2), p + Vector2(-5, -4), p + Vector2(0, 1), p + Vector2(5, -5), p + Vector2(12, 2)]), INK, 1.5)
			draw_rect(Rect2(p + Vector2(-3, 4), Vector2(6, 5)), INK)
			draw_line(p + Vector2(-3, 9), p + Vector2(-14, 9), Color(INK, 0.6), 2.0)
		"steinmann":
			for k in range(3):
				draw_circle(p + Vector2(0, 6 - k * 6), 4.5 - k, INK)
			draw_circle(p + Vector2(-1.5, -6), 0.9, PAPER)
			draw_circle(p + Vector2(1.5, -6), 0.9, PAPER)
		"see":
			draw_arc(p, 9.0, 0.0, TAU, 20, Color(0.15, 0.3, 0.6), 2.0)
			draw_line(p + Vector2(-3, -18), p + Vector2(3, -18), INK, 2.0)
			draw_line(p + Vector2(0, -21), p + Vector2(0, -12), INK, 2.0)
		"kapelle", "kapelle_kerze":                    # Roter Faden (geschichten_faden.gd): Maggies Bergkapelle
			preload("res://scripts/geschichten_faden.gd").zeichne_kapelle(self, p, kind == "kapelle_kerze")
		"kreuz":
			draw_line(p + Vector2(-6, -6), p + Vector2(6, 6), RED, 3.0)
			draw_line(p + Vector2(6, -6), p + Vector2(-6, 6), RED, 3.0)
		_:
			draw_circle(p, 4.0, INK)


func _draw_hits() -> void:
	"""MoveEye in the middle, rings 10 / 25 / 50 m, the view of the head camera, every night event as a dot + its path:
	green = MoveEye has reported it, red = visible but not reported (missed), grey = not in the picture"""
	var r := _sq()
	draw_rect(r, Color(0.07, 0.09, 0.12))
	var c := r.get_center()
	var k := r.size.x * 0.48 / hit_r
	var font := get_theme_default_font()
	for rr in [10.0, 25.0, 50.0]:
		if rr <= hit_r:
			draw_arc(c, rr * k, 0.0, TAU, 48, Color(0.3, 0.36, 0.44), 1.0)
			draw_string(font, c + Vector2(rr * k + 2, -2), "%d m" % int(rr), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.5, 0.56, 0.64))
	# the view of the head camera (≈ 66° horizontal - Camera Module 3: 66° (Raspberry Pi datasheet))
	var fwd := Vector2(-sin(cam_yaw), -cos(cam_yaw))
	var half := deg_to_rad(33.0)
	var fan := PackedVector2Array([c])
	for i in range(13):
		var a := -half + 2.0 * half * i / 12.0
		fan.append(c + fwd.rotated(a) * hit_r * k)
	draw_colored_polygon(fan, Color(0.23, 0.55, 1.0, 0.12))
	for h in hits:
		var col: Color = {"seen": Color(0.3, 0.85, 0.45), "missed": Color(1.0, 0.35, 0.3), "hidden": Color(0.55, 0.58, 0.62)}.get(str(h.get("st", "hidden")), Color.GRAY)
		var path: Array = h.get("path", [])
		if path.size() >= 2:
			var pts := PackedVector2Array()
			for q in path:
				var v := Vector2(float(q[1]), float(q[2]))
				if v.length() <= hit_r * 1.2:
					pts.append(c + v.limit_length(hit_r) * k)
			if pts.size() >= 2:
				draw_polyline(pts, Color(col, 0.55), 1.5)
		var p := Vector2(float(h.get("x", 0.0)), float(h.get("z", 0.0)))
		var pp := c + p.limit_length(hit_r) * k
		draw_circle(pp, 5.0, col)
		draw_string(font, pp + Vector2(7, 4), str(h.get("label", "")), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.85, 0.88, 0.92))
	draw_circle(c, 5.0, Color(0.23, 0.55, 1.0))
	draw_string(font, c + Vector2(-22, 18), "MoveEye", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.6, 0.75, 1.0))
	draw_rect(r, Color(0.2, 0.25, 0.32), false, 1.0)
