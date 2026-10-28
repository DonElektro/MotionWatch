extends Control
## 3D-3.62: the orange Motion Watch symbol (like «Classic» in Motion Watch) at the top left of the panel.
## The eye in the middle looks around: slowly to the left, short stop, to the right, short stop.

var t := 0.0
const TOP := Color(1.0, 0.624, 0.263)      # #ff9f43
const BOT := Color(0.910, 0.349, 0.047)    # #e8590c
const DARK := Color(0.039, 0.055, 0.078)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(dt: float) -> void:
	if is_visible_in_tree():
		t += dt
		queue_redraw()


func look() -> float:
	"""-1 .. 1: 6 s cycle middle -> left (stop) -> right (stop) -> middle, eased"""
	var p: float = fmod(t, 6.0) / 6.0
	var keys := [[0.0, 0.0], [0.12, -1.0], [0.38, -1.0], [0.62, 1.0], [0.88, 1.0], [1.0, 0.0]]
	for i in range(keys.size() - 1):
		var a: Array = keys[i]
		var b: Array = keys[i + 1]
		if p <= b[0]:
			var f: float = (p - a[0]) / max(0.0001, b[0] - a[0])
			f = f * f * (3.0 - 2.0 * f)
			return lerp(float(a[1]), float(b[1]), f)
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
	var P := func(x: float, y: float) -> Vector2: return o + Vector2(50.0 + x, 46.0 + y) * k
	var w: float = max(1.5, 6.0 * k)
	# fork, stand
	var fork := PackedVector2Array([P.call(-26, -6), P.call(-26, 10)])
	for i in range(1, 9):
		var a: float = PI - i * (PI / 2.0) / 8.0
		fork.append(P.call(-16 + cos(a) * 10.0, 10 + sin(a) * 10.0))
	for i in range(0, 9):
		var a: float = PI / 2.0 - i * (PI / 2.0) / 8.0
		fork.append(P.call(16 + cos(a) * 10.0, 10 + sin(a) * 10.0))
	fork.append(P.call(26, -6))
	draw_polyline(fork, Color.WHITE, w, true)
	draw_line(P.call(0, 20), P.call(0, 30), Color.WHITE, w, true)
	draw_line(P.call(-14, 32), P.call(14, 32), Color.WHITE, w, true)
	for q in [P.call(-26, -6), P.call(26, -6), P.call(-14, 32), P.call(14, 32)]:
		draw_circle(q, w / 2.0, Color.WHITE)
	# camera head with the moving eye
	draw_circle(P.call(0, 0), 19.0 * k, Color.WHITE)
	var dx: float = look() * 6.0
	draw_circle(P.call(dx, 0), 11.0 * k, DARK)
	draw_circle(P.call(dx * 1.1, 0), 6.0 * k, BOT)
	draw_circle(P.call(dx - 3.5, -3.5), 2.6 * k, Color.WHITE)
