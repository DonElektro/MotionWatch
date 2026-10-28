extends Control
## 3D-3.62: the orange MoveEye symbol (like «Classic» in MoveEye) at the top left of the panel.
## The pupil in the eye looks around: slowly to the left, short stop, to the right, short stop.

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
	# 3D-3.79: MoveEye - the field of view, the eye at the bottom, a walking person inside detection corners (walks to and fro)
	var P := func(x: float, y: float) -> Vector2: return o + Vector2(x, y) * k
	var fan := PackedVector2Array([P.call(50, 78)])
	var fcol := PackedColorArray([Color(1, 1, 1, 1)])
	for i in range(17):
		var ang: float = deg_to_rad(-140.0 + 100.0 * i / 16.0)
		var q := Vector2(50 + cos(ang) * 62.0, 78 + sin(ang) * 62.0)
		fan.append(P.call(q.x, q.y))
		fcol.append(Color(1, 1, 1, lerpf(0.35, 1.0, clampf((q.y - 16.0) / 62.0, 0.0, 1.0))))
	draw_polygon(fan, fcol)
	var dx: float = look() * 3.0
	var ph: float = t * 4.0                                # the legs and arms swing
	var hx := 60.0 + dx
	var Wc := BOT
	var lw: float = max(1.0, 3.5 * k * 1.1)
	draw_circle(P.call(hx + 1.1, 40 - 16.5), 5.5 * k, Wc)                      # head
	draw_line(P.call(hx, 40 - 9.9), P.call(hx - 1.1, 40 + 3.3), Wc, max(1.5, 7.7 * k), true)   # body
	var sw := sin(ph) * 4.5
	draw_line(P.call(hx - 1.1, 43.3), P.call(hx - 1.1 - 5.0 - sw * 0.6, 54.3), Wc, lw, true)    # legs
	draw_line(P.call(hx - 1.1, 43.3), P.call(hx - 1.1 + 5.0 + sw * 0.6, 53.2), Wc, lw, true)
	draw_line(P.call(hx, 33.4), P.call(hx - 6.6 + sw * 0.4, 40), Wc, max(1.0, 3.3 * k), true)   # arms
	draw_line(P.call(hx, 33.4), P.call(hx + 6.6 - sw * 0.4, 38.9), Wc, max(1.0, 3.3 * k), true)
	var cw: float = max(1.0, 2.5 * k)                      # the detection corners move with the person
	var x0 := 48.0 + dx
	var x1 := 72.0 + dx
	for c in [[x0, 21, x0, 16, x0 + 5, 16], [x1 - 5, 16, x1, 16, x1, 21], [x1, 49, x1, 54, x1 - 5, 54], [x0 + 5, 54, x0, 54, x0, 49]]:
		draw_polyline(PackedVector2Array([P.call(c[0], c[1]), P.call(c[2], c[3]), P.call(c[4], c[5])]), DARK, cw, true)
	draw_circle(P.call(50, 78), 10.0 * k, Color.WHITE)    # the eye
	draw_circle(P.call(50, 78), 5.0 * k, DARK)
