extends Control
## 3D-3.62: the orange MoveEye symbol (like the app icon «MoveEye» in MoveEye, 490) at the top left of the panel - ONE script for
## every place in the simulator (Mehr, Spiel-Assistent, Grossvater-Karte, Mini-Leiste, Menü).
## Besitzer 22.11.2026 («Symbol-Animation», same as MW_SYMBOL_HTML of MoveEye part 144): the red person walks inside the
## detection corners, corners + person go ±9 to and fro in 7 s (ease-in-out), the field of view swings ±12° around the eye
## with it, the pupil looks up at the person, the eye blinks twice in 23 s, steps 0.7 s (leg / arm half a step apart).
## «Bewegung reduzieren» (UI.motion_still): still.

const UI = preload("res://scripts/ui_style.gd")
var t := 0.0
const TOP := Color(1.0, 0.624, 0.263)      # #ff9f43
const BOT := Color(0.910, 0.349, 0.047)    # #e8590c
const DARK := Color(0.039, 0.055, 0.078)
const RED := Color("#e0242b")              # LOGO_RED (MoveEye part 144)
const WALK := 9.0                          # units of the 100 × 100 tile
const SWING := 12.0                        # degrees
const PUPIL := Vector2(2.2, -3.0)          # ±3.8 / −5.2 of the big eye (r 17), here r 10 (pupil r 5 stays inside)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(dt: float) -> void:
	if is_visible_in_tree():
		t += dt
		queue_redraw()


static func eio(u: float) -> float:
	"""like the CSS ease-in-out between two keyframes"""
	u = clampf(u, 0.0, 1.0)
	return u * u * (3.0 - 2.0 * u)


static func walk(tt: float) -> float:
	"""-1 .. 1: the 7 s walk (0 s left, 3.5 s right, eased); 0 when the motion is reduced"""
	if UI.motion_still:
		return 0.0
	var p: float = fmod(tt, 7.0) / 7.0
	return -1.0 + 2.0 * eio(p * 2.0) if p < 0.5 else 1.0 - 2.0 * eio((p - 0.5) * 2.0)


static func step(tt: float) -> float:
	"""-1 .. 1: the 0.7 s step (leg 1 and arm 2; leg 2 and arm 1 half a step later = the opposite)"""
	if UI.motion_still:
		return 0.0
	var p: float = fmod(tt, 0.7) / 0.7
	return 1.0 - 2.0 * eio(p * 2.0) if p < 0.5 else -1.0 + 2.0 * eio((p - 0.5) * 2.0)


static func lid(tt: float) -> float:
	"""0 .. 1: the eye blinks twice in 23 s (at 39.85 … 40.15 % and 95.85 … 96.15 %, like @keyframes mws-b)"""
	if UI.motion_still:
		return 0.0
	var p: float = fmod(tt, 23.0) / 23.0 * 100.0
	for k in [[39.6, 39.85, 40.15, 40.5], [95.6, 95.85, 96.15, 96.5]]:
		if p >= k[0] and p <= k[3]:
			if p < k[1]:
				return (p - k[0]) / (k[1] - k[0])
			if p <= k[2]:
				return 1.0
			return (k[3] - p) / (k[3] - k[2])
	return 0.0


func _draw() -> void:
	var s: float = min(size.x, size.y)
	var k: float = s / 100.0
	var o := Vector2((size.x - s) / 2.0, (size.y - s) / 2.0)
	# tile with rounded corners and the orange gradient
	var pts := PackedVector2Array()
	var cols := PackedColorArray()
	var r := 22.0
	for c in [[100.0 - r, r, -90.0], [100.0 - r, 100.0 - r, 0.0], [r, 100.0 - r, 90.0], [r, r, 180.0]]:
		for i in range(7):
			var ang: float = deg_to_rad(c[2] + i * 15.0)
			var q := Vector2(c[0] + cos(ang) * r, c[1] + sin(ang) * r)
			pts.append(o + q * k)
			cols.append(TOP.lerp(BOT, q.y / 100.0))
	draw_polygon(pts, cols)
	# 3D-3.79: MoveEye - the field of view, the eye at the bottom, a walking person inside detection corners (walks to and fro)
	var P := func(x: float, y: float) -> Vector2: return o + Vector2(x, y) * k
	var w: float = walk(t)
	var rot: float = deg_to_rad(SWING * w)
	var fan := PackedVector2Array([P.call(50, 78)])
	var fcol := PackedColorArray([Color(1, 1, 1, 1)])
	for i in range(17):
		var ang: float = deg_to_rad(-140.0 + 100.0 * i / 16.0) + rot
		var q := Vector2(50 + cos(ang) * 62.0, 78 + sin(ang) * 62.0)
		fan.append(P.call(q.x, q.y))
		fcol.append(Color(1, 1, 1, lerpf(0.35, 1.0, clampf((q.y - 16.0) / 62.0, 0.0, 1.0))))
	draw_polygon(fan, fcol)
	# the red person (geometry of MoveEye _wm_walk, scale 1.1, at 60 / 40 like the app icon) walks with the corners
	var dx: float = WALK * w
	var sc := 1.1
	var hp := Vector2(60.0 + dx, 40.0)
	var Q := func(x: float, y: float) -> Vector2: return P.call(hp.x + x * sc, hp.y + y * sc)
	var st: float = step(t)
	var limb := func(a: Vector2, b: Vector2, deg: float, wd: float) -> void:
		var e: Vector2 = a + (b - a).rotated(deg_to_rad(deg))
		draw_line(Q.call(a.x, a.y), Q.call(e.x, e.y), RED, max(1.0, wd * sc * k), true)
	draw_circle(Q.call(1.0, -15.5), 5.2 * sc * k, RED)                          # head
	draw_line(Q.call(0.5, -9.0), Q.call(-0.5, 3.0), RED, max(1.5, 8.0 * sc * k), true)   # body
	limb.call(Vector2(-0.5, 3), Vector2(-5, 13.5), 18.0 * st, 4.6)            # leg 1
	limb.call(Vector2(-0.5, 3), Vector2(4.5, 13), -18.0 * st, 4.6)            # leg 2 (half a step later)
	limb.call(Vector2(0.5, -6), Vector2(-5.5, 0.5), -18.0 * st, 3.6)          # arm 1 (with leg 2)
	limb.call(Vector2(0.5, -6), Vector2(6, -0.5), 18.0 * st, 3.6)             # arm 2 (with leg 1)
	var cw: float = max(1.0, 2.5 * k)                      # the detection corners move with the person
	var x0 := 48.0 + dx
	var x1 := 72.0 + dx
	for c in [[x0, 21, x0, 16, x0 + 5, 16], [x1 - 5, 16, x1, 16, x1, 21], [x1, 49, x1, 54, x1 - 5, 54], [x0 + 5, 54, x0, 54, x0, 49]]:
		draw_polyline(PackedVector2Array([P.call(c[0], c[1]), P.call(c[2], c[3]), P.call(c[4], c[5])]), DARK, cw, true)
	draw_circle(P.call(50, 78), 10.0 * k, Color.WHITE)    # the eye; the pupil looks up at the person
	draw_circle(P.call(50 + PUPIL.x * w, 78 + (0.0 if UI.motion_still else PUPIL.y)), 5.0 * k, DARK)
	var ld: float = lid(t)
	if ld > 0.02:                                          # the lid (colour of the tile) comes down from the top
		var sn := clampf(-1.0 + 2.0 * ld, -1.0, 1.0)
		var a0 := PI - asin(sn)
		var a1 := TAU + asin(sn)
		var lp := PackedVector2Array()
		for i in range(21):
			var an := a0 + (a1 - a0) * i / 20.0
			lp.append(P.call(50 + cos(an) * 10.0, 78 + sin(an) * 10.0))
		if a1 - a0 > 0.05:
			draw_colored_polygon(lp, TOP.lerp(BOT, 0.78))
