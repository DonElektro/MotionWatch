extends Control
## 3D-3.87: der Schriftzug W6 von MoveEye (wie in der Kopfzeile der Webseite): «Move» hell, «Eye» orange, das «o» ist das
## Auge mit Sichtfächer und erkannter Person. Buchstaben als Pfade (Liberation Sans Bold, SIL OFL).
## 3D-4.23 (Daniel): bewegt wie im Web (MoveEye 2.98.52, quelle/144_logo_schriftzug.py): die rote Person geht hin und her
## (7 s, mit Schritten 0.7 s), der Sichtfächer schwenkt mit, die Pupille schaut zur Person, das Auge blinzelt ab und zu
## (23 s, nach 9.2 s und 22.1 s). Die Ebenen unten sind aus WORDMARK_W6 geschnitten (gleiche Masse wie im Web): sie werden
## einmal als kleine Bilder gezeichnet, pro Bild nur verschoben / gedreht; höchstens 30 Bilder/s, still wenn nicht sichtbar.

const VB := Vector2(0, 31)                 # origin and size of the viewBox
const VS := Vector2(320, 135)
const EYE := Vector2(86.00, 130.60)                  # eye centre (the cone turns around it)
const CONE_A := 14.1                            # degrees the cone swings to each side
const WALK_X := 13.8                            # the person walks this far to each side
const PUPIL_X := Vector2(-2.96, 4.60)              # pupil x when the person is left / right
const PUPIL_Y := -2.0
const STEP_A := 18.0                                # legs / arms swing
const PIVOT := {"leg1": Vector2(86.25, 78.60), "leg2": Vector2(91.00, 78.60), "arm1": Vector2(89.50, 69.60), "arm2": Vector2(95.00, 69.60)}
const OVER := 2.0                                   # layers drawn twice as fine (smooth when they move by parts of a pixel)
const LAYERS := {
	"cone": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"135\" viewBox=\"0 31 320 135\"><defs><linearGradient id=\"mwfw6\" x1=\"0\" y1=\"1\" x2=\"0\" y2=\"0\"><stop offset=\"0\" stop-color=\"#ff9f43\" stop-opacity=\".95\"/><stop offset=\"1\" stop-color=\"#ff9f43\" stop-opacity=\".12\"/></linearGradient></defs><path d=\"M86.0 130.6 L32.8 51.8 A95 95 0 0 1 139.1 51.8 Z\" fill=\"url(#mwfw6)\"/></svg>",
	"body": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"135\" viewBox=\"0 31 320 135\"><g transform=\"translate(89.0 75.6) scale(1.00)\" fill=\"#e0242b\" stroke=\"#e0242b\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"1\" cy=\"-15.5\" r=\"5.2\" stroke=\"none\"/><path d=\"M0.5 -9 L-0.5 3\" stroke-width=\"8\"/></g><g fill=\"none\" stroke=\"#e8eef5\" stroke-width=\"2.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M72.0 56.6 V50.6 H78.0 M99.0 50.6 H105.0 V56.6 M105.0 90.6 V96.6 H99.0 M78.0 96.6 H72.0 V90.6\"/></g></svg>",
	"leg1": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"135\" viewBox=\"0 31 320 135\"><g transform=\"translate(89.0 75.6) scale(1.00)\" fill=\"#e0242b\" stroke=\"#e0242b\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M-0.5 3 L-5 13.5\" stroke-width=\"4.6\" fill=\"none\"/></g></svg>",
	"leg2": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"135\" viewBox=\"0 31 320 135\"><g transform=\"translate(89.0 75.6) scale(1.00)\" fill=\"#e0242b\" stroke=\"#e0242b\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M-0.5 3 L4.5 13\" stroke-width=\"4.6\" fill=\"none\"/></g></svg>",
	"arm1": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"135\" viewBox=\"0 31 320 135\"><g transform=\"translate(89.0 75.6) scale(1.00)\" fill=\"#e0242b\" stroke=\"#e0242b\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M0.5 -6 L-5.5 0.5\" stroke-width=\"3.6\" fill=\"none\"/></g></svg>",
	"arm2": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"135\" viewBox=\"0 31 320 135\"><g transform=\"translate(89.0 75.6) scale(1.00)\" fill=\"#e0242b\" stroke=\"#e0242b\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M0.5 -6 L6 -0.5\" stroke-width=\"3.6\" fill=\"none\"/></g></svg>",
	"letters": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"135\" viewBox=\"0 31 320 135\"><path d=\"M49.94921875 150.0V119.9765625Q49.94921875 118.95703125 49.966796875 117.9375Q49.984375 116.91796875 50.30078125 109.18359375Q47.8046875 118.640625 46.609375 122.3671875L37.6796875 150.0H30.296875L21.3671875 122.3671875L17.60546875 109.18359375Q18.02734375 117.33984375 18.02734375 119.9765625V150.0H8.81640625V100.46484375H22.703125L31.5625 128.16796875L32.3359375 130.83984375L34.0234375 137.484375L36.23828125 129.5390625L45.34375 100.46484375H59.16015625V150.0Z M133.65625 150.0H121.84375L108.23828125 111.9609375H118.6796875L125.32421875 133.23046875Q125.8515625 134.98828125 127.8203125 142.01953125Q128.171875 140.578125 129.26171875 136.95703125Q130.3515625 133.3359375 137.34765625 111.9609375H147.68359375Z M168.6015625 150.703125Q160.0234375 150.703125 155.41796875 145.623046875Q150.8125 140.54296875 150.8125 130.8046875Q150.8125 121.3828125 155.48828125 116.3203125Q160.1640625 111.2578125 168.7421875 111.2578125Q176.93359375 111.2578125 181.2578125 116.689453125Q185.58203125 122.12109375 185.58203125 132.59765625V132.87890625H161.18359375Q161.18359375 138.43359375 163.240234375 141.263671875Q165.296875 144.09375 169.09375 144.09375Q174.33203125 144.09375 175.703125 139.55859375L185.01953125 140.3671875Q180.9765625 150.703125 168.6015625 150.703125ZM168.6015625 117.48046875Q165.12109375 117.48046875 163.240234375 119.90625Q161.359375 122.33203125 161.25390625 126.69140625H176.01953125Q175.73828125 122.0859375 173.8046875 119.783203125Q171.87109375 117.48046875 168.6015625 117.48046875Z\" fill=\"#e8eef5\"/><path d=\"M192.859375 150.0V100.46484375H231.8125V108.48046875H203.23046875V120.92578125H229.66796875V128.94140625H203.23046875V141.984375H233.25390625V150.0Z M246.015625 164.94140625Q242.46484375 164.94140625 239.79296875 164.484375V157.453125Q241.65625 157.734375 243.203125 157.734375Q245.3125 157.734375 246.701171875 157.06640625Q248.08984375 156.3984375 249.197265625 154.8515625Q250.3046875 153.3046875 251.67578125 149.61328125L236.62890625 111.9609375H247.0703125L253.046875 129.78515625Q254.453125 133.6171875 256.59765625 141.52734375L257.4765625 138.1875L259.76171875 129.92578125L265.38671875 111.9609375H275.72265625L260.67578125 152.00390625Q257.65234375 159.31640625 254.400390625 162.12890625Q251.1484375 164.94140625 246.015625 164.94140625Z M296.7109375 150.703125Q288.1328125 150.703125 283.52734375 145.623046875Q278.921875 140.54296875 278.921875 130.8046875Q278.921875 121.3828125 283.59765625 116.3203125Q288.2734375 111.2578125 296.8515625 111.2578125Q305.04296875 111.2578125 309.3671875 116.689453125Q313.69140625 122.12109375 313.69140625 132.59765625V132.87890625H289.29296875Q289.29296875 138.43359375 291.349609375 141.263671875Q293.40625 144.09375 297.203125 144.09375Q302.44140625 144.09375 303.8125 139.55859375L313.12890625 140.3671875Q309.0859375 150.703125 296.7109375 150.703125ZM296.7109375 117.48046875Q293.23046875 117.48046875 291.349609375 119.90625Q289.46875 122.33203125 289.36328125 126.69140625H304.12890625Q303.84765625 122.0859375 301.9140625 119.783203125Q299.98046875 117.48046875 296.7109375 117.48046875Z\" fill=\"#ff9f43\"/></svg>",
	"ring": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"135\" viewBox=\"0 31 320 135\"><circle cx=\"86.0\" cy=\"130.6\" r=\"18.4\" fill=\"none\" stroke=\"#ff9f43\" stroke-width=\"9.4\"/></svg>",
	"pupil": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"135\" viewBox=\"0 31 320 135\"><circle cx=\"86.0\" cy=\"130.6\" r=\"7.7\" fill=\"#e8eef5\"/></svg>",
}
const SVG := "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"135\" viewBox=\"0 31 320 135\"><defs><linearGradient id=\"mwfw6\" x1=\"0\" y1=\"1\" x2=\"0\" y2=\"0\"><stop offset=\"0\" stop-color=\"#ff9f43\" stop-opacity=\".95\"/><stop offset=\"1\" stop-color=\"#ff9f43\" stop-opacity=\".12\"/></linearGradient></defs><path d=\"M86.0 130.6 L32.8 51.8 A95 95 0 0 1 139.1 51.8 Z\" fill=\"url(#mwfw6)\"/><g><g transform=\"translate(89.0 75.6) scale(1.00)\" fill=\"#e0242b\" stroke=\"#e0242b\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"1\" cy=\"-15.5\" r=\"5.2\" stroke=\"none\"/><path d=\"M0.5 -9 L-0.5 3\" stroke-width=\"8\"/><g><path d=\"M-0.5 3 L-5 13.5\" stroke-width=\"4.6\" fill=\"none\"/></g><g><path d=\"M-0.5 3 L4.5 13\" stroke-width=\"4.6\" fill=\"none\"/></g><g><path d=\"M0.5 -6 L-5.5 0.5\" stroke-width=\"3.6\" fill=\"none\"/></g><g><path d=\"M0.5 -6 L6 -0.5\" stroke-width=\"3.6\" fill=\"none\"/></g></g><g fill=\"none\" stroke=\"#e8eef5\" stroke-width=\"2.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M72.0 56.6 V50.6 H78.0 M99.0 50.6 H105.0 V56.6 M105.0 90.6 V96.6 H99.0 M78.0 96.6 H72.0 V90.6\"/></g></g><path d=\"M49.94921875 150.0V119.9765625Q49.94921875 118.95703125 49.966796875 117.9375Q49.984375 116.91796875 50.30078125 109.18359375Q47.8046875 118.640625 46.609375 122.3671875L37.6796875 150.0H30.296875L21.3671875 122.3671875L17.60546875 109.18359375Q18.02734375 117.33984375 18.02734375 119.9765625V150.0H8.81640625V100.46484375H22.703125L31.5625 128.16796875L32.3359375 130.83984375L34.0234375 137.484375L36.23828125 129.5390625L45.34375 100.46484375H59.16015625V150.0Z M133.65625 150.0H121.84375L108.23828125 111.9609375H118.6796875L125.32421875 133.23046875Q125.8515625 134.98828125 127.8203125 142.01953125Q128.171875 140.578125 129.26171875 136.95703125Q130.3515625 133.3359375 137.34765625 111.9609375H147.68359375Z M168.6015625 150.703125Q160.0234375 150.703125 155.41796875 145.623046875Q150.8125 140.54296875 150.8125 130.8046875Q150.8125 121.3828125 155.48828125 116.3203125Q160.1640625 111.2578125 168.7421875 111.2578125Q176.93359375 111.2578125 181.2578125 116.689453125Q185.58203125 122.12109375 185.58203125 132.59765625V132.87890625H161.18359375Q161.18359375 138.43359375 163.240234375 141.263671875Q165.296875 144.09375 169.09375 144.09375Q174.33203125 144.09375 175.703125 139.55859375L185.01953125 140.3671875Q180.9765625 150.703125 168.6015625 150.703125ZM168.6015625 117.48046875Q165.12109375 117.48046875 163.240234375 119.90625Q161.359375 122.33203125 161.25390625 126.69140625H176.01953125Q175.73828125 122.0859375 173.8046875 119.783203125Q171.87109375 117.48046875 168.6015625 117.48046875Z\" fill=\"#e8eef5\"/><g><circle cx=\"86.0\" cy=\"130.6\" r=\"18.4\" fill=\"none\" stroke=\"#ff9f43\" stroke-width=\"9.4\"/><circle cx=\"86.0\" cy=\"130.6\" r=\"7.7\" fill=\"#e8eef5\"/></g><path d=\"M192.859375 150.0V100.46484375H231.8125V108.48046875H203.23046875V120.92578125H229.66796875V128.94140625H203.23046875V141.984375H233.25390625V150.0Z M246.015625 164.94140625Q242.46484375 164.94140625 239.79296875 164.484375V157.453125Q241.65625 157.734375 243.203125 157.734375Q245.3125 157.734375 246.701171875 157.06640625Q248.08984375 156.3984375 249.197265625 154.8515625Q250.3046875 153.3046875 251.67578125 149.61328125L236.62890625 111.9609375H247.0703125L253.046875 129.78515625Q254.453125 133.6171875 256.59765625 141.52734375L257.4765625 138.1875L259.76171875 129.92578125L265.38671875 111.9609375H275.72265625L260.67578125 152.00390625Q257.65234375 159.31640625 254.400390625 162.12890625Q251.1484375 164.94140625 246.015625 164.94140625Z M296.7109375 150.703125Q288.1328125 150.703125 283.52734375 145.623046875Q278.921875 140.54296875 278.921875 130.8046875Q278.921875 121.3828125 283.59765625 116.3203125Q288.2734375 111.2578125 296.8515625 111.2578125Q305.04296875 111.2578125 309.3671875 116.689453125Q313.69140625 122.12109375 313.69140625 132.59765625V132.87890625H289.29296875Q289.29296875 138.43359375 291.349609375 141.263671875Q293.40625 144.09375 297.203125 144.09375Q302.44140625 144.09375 303.8125 139.55859375L313.12890625 140.3671875Q309.0859375 150.703125 296.7109375 150.703125ZM296.7109375 117.48046875Q293.23046875 117.48046875 291.349609375 119.90625Q289.46875 122.33203125 289.36328125 126.69140625H304.12890625Q303.84765625 122.0859375 301.9140625 119.783203125Q299.98046875 117.48046875 296.7109375 117.48046875Z\" fill=\"#ff9f43\"/></svg>"

var tex := {}
var off := {}
var k := 1.0
var _acc := 0.0
var t0 := 0.0


static func texture(height: float) -> ImageTexture:
	"""the still wordmark as one picture (fallback / other places)"""
	var img := Image.new()
	if img.load_svg_from_string(SVG, height / VS.y) != OK:
		return null
	return ImageTexture.create_from_image(img)


func build(height: float) -> bool:
	"""draws the layers once; false when the SVG cannot be read (then the caller shows the still logo)"""
	k = height / VS.y
	for n in LAYERS:
		var img := Image.new()
		if img.load_svg_from_string(LAYERS[n], k * OVER) != OK:
			return false
		var r: Rect2i = img.get_used_rect()
		if r.size.x <= 0 or r.size.y <= 0:
			return false
		tex[n] = ImageTexture.create_from_image(img.get_region(r))
		off[n] = Vector2(r.position) / OVER
	custom_minimum_size = VS * k
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	tooltip_text = "MoveEye"
	t0 = Time.get_ticks_msec() / 1000.0
	return true


func _process(dt: float) -> void:
	_acc += dt
	if _acc < 1.0 / 30.0 or not is_visible_in_tree() or DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_MINIMIZED:
		return
	_acc = 0.0
	queue_redraw()


static func ease_io(x: float) -> float:
	"""CSS ease-in-out = cubic-bezier(.42, 0, .58, 1): y for the time x (Newton on the x curve)"""
	var u := x
	for i in range(6):
		var bx: float = 3.0 * u * (1.0 - u) * (1.0 - u) * 0.42 + 3.0 * u * u * (1.0 - u) * 0.58 + u * u * u
		var d: float = 3.0 * (1.0 - u) * (1.0 - u) * 0.42 + 6.0 * u * (1.0 - u) * (0.58 - 0.42) + 3.0 * u * u * (1.0 - 0.58)
		if absf(d) < 0.000001:
			break
		u = clampf(u - (bx - x) / d, 0.0, 1.0)
	return 3.0 * u * u * (1.0 - u) + u * u * u


static func swing(t: float, period: float) -> float:
	"""-1 -> 1 -> -1 within the period, ease-in-out on each half (like the keyframes 0%, 50%, 100%)"""
	var p: float = fposmod(t, period) / period
	if p < 0.5:
		return -1.0 + 2.0 * ease_io(p * 2.0)
	return 1.0 - 2.0 * ease_io(p * 2.0 - 1.0)


static func blink(t: float) -> float:
	"""1 = open, 0.1 = closed: twice in 23 s (keyframes wmb of the web page), linear"""
	var p: float = fposmod(t, 23.0) / 23.0 * 100.0
	for c in [39.6, 95.6]:
		if p >= c and p < c + 0.9:
			var q: float = p - c
			if q < 0.25:
				return lerpf(1.0, 0.1, q / 0.25)
			if q < 0.55:
				return 0.1
			return lerpf(0.1, 1.0, (q - 0.55) / 0.35)
	return 1.0


func _px(p: Vector2) -> Vector2:
	return (p - VB) * k


func _layer(n: String, m: Transform2D) -> void:
	if not tex.has(n):
		return
	draw_set_transform_matrix(m)
	var tx: Texture2D = tex[n]
	draw_texture_rect(tx, Rect2(off[n], Vector2(tx.get_size()) / OVER), false)


func _turn(pivot_svg: Vector2, deg: float) -> Transform2D:
	var p := _px(pivot_svg)
	return Transform2D(0.0, p) * Transform2D(deg_to_rad(deg), Vector2.ZERO) * Transform2D(0.0, -p)


func _draw() -> void:
	if tex.is_empty():
		return
	var t: float = Time.get_ticks_msec() / 1000.0 - t0
	var s: float = swing(t, 7.0)                    # the walk: person, cone and pupil on the same curve
	# steps (wms: 18 deg at 0 %, -18 at 50 %). On the web half the limbs run «reverse» - with these mirror-like keyframes
	# that gives the same angle, so all four limbs swing together there; the same here (same look)
	var st: float = -STEP_A * swing(t, 0.7)
	var st2: float = st
	_layer("cone", _turn(EYE, CONE_A * s))
	var walk := Transform2D(0.0, Vector2(WALK_X * s * k, 0.0))
	_layer("body", walk)
	_layer("leg1", walk * _turn(PIVOT["leg1"], st))
	_layer("leg2", walk * _turn(PIVOT["leg2"], st2))
	_layer("arm1", walk * _turn(PIVOT["arm1"], st2))
	_layer("arm2", walk * _turn(PIVOT["arm2"], st))
	_layer("letters", Transform2D())
	var e := _px(EYE)
	var b: float = blink(t)
	var lid := Transform2D(0.0, e) * Transform2D(Vector2(1.0, 0.0), Vector2(0.0, b), Vector2.ZERO) * Transform2D(0.0, -e)
	_layer("ring", lid)
	var px: float = lerpf(PUPIL_X.x, PUPIL_X.y, 0.5 + 0.5 * s)
	_layer("pupil", lid * Transform2D(0.0, Vector2(px, PUPIL_Y) * k))
	draw_set_transform_matrix(Transform2D())
