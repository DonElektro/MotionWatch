extends Control
## Ruhebild (MoveEye 639y): a calm background - dark gradient, two mountain ridges, a few faint stars - for the update window
## (update.gd) of the simulator. The same look as the calm picture of MoveEye (quelle/639y_ruhebild.py) and the start picture
## (ruhebild_start.png, project.godot boot_splash, made by werkzeuge/ruhebild_start_bauen.py). Still: nothing moves
## («Bewegung reduzieren» needs nothing here).

const TOP := Color(0.043, 0.071, 0.125)          # #0b1220
const BOT := Color(0.078, 0.118, 0.173)          # #141e2c
const RIDGES := [[0.70, 0.10, Color(0.114, 0.157, 0.212), 0.0], [0.80, 0.07, Color(0.086, 0.125, 0.173), 1.7]]


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(queue_redraw)


func _draw() -> void:
	var w := size.x
	var h := size.y
	if w < 2.0 or h < 2.0:
		return
	draw_polygon(PackedVector2Array([Vector2(0, 0), Vector2(w, 0), Vector2(w, h), Vector2(0, h)]),
		PackedColorArray([TOP, TOP, BOT, BOT]))
	for i in range(40):                                # a soft glow behind the window (like the picture of MoveEye), fine steps
		var r := minf(w, h) * (0.46 - i * 0.0105)
		draw_circle(Vector2(w * 0.5, h * 0.38), r, Color(0.16, 0.25, 0.38, 0.009))
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in range(int(w * h / 9000.0)):
		draw_circle(Vector2(rng.randf() * w, rng.randf() * h * 0.55), 1.0, Color(0.55, 0.58, 0.62, 0.55))
	for rd in RIDGES:
		var pts := PackedVector2Array()
		var n := 96
		for k in range(n + 1):
			var xs := float(k) / n
			var ph: float = rd[3]
			var y: float = h * (rd[0] - rd[1] * (0.55 * sin(xs * 6.1 + ph) + 0.30 * sin(xs * 13.7 + ph * 2.0) + 0.15 * sin(xs * 29.0 + ph)))
			pts.append(Vector2(xs * w, y))
		pts.append(Vector2(w, h))
		pts.append(Vector2(0, h))
		draw_colored_polygon(pts, rd[2])
