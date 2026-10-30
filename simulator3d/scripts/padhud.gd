extends Control
## 3D-4.13: what the game controller shows on the screen (padmap.gd), drawn the same in the window and in the game at the PC:
##   · a chip per controller: number + role in its colour (orange Wächter, green Schleicher, blue Rover, grey alles)
##   · the mini-map (north up, the head in the middle, its field of view yellow, the rover green, me white) with the
##     direction on the rim: yellow = where the head looks, green = where the rover drives (MoveEye 538 draws the same)
##   · a clear focus ring while the controller moves through a menu
## «local» = inside the game at the PC (localplay.gd): the mini-map of the player; else the window: only while a controller
## was used in the last 20 s (the big map of the window shows the rest).

var main
var pm
var local := false
var _t := 0.0

const UI = preload("res://scripts/ui_style.gd")


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(dt: float) -> void:
	var vs := get_viewport_rect().size
	if size != vs:
		position = Vector2.ZERO
		size = vs
	_t -= dt
	var lp = main.localplay
	if not local and lp != null and lp.active:
		visible = false                                       # the game at the PC has its own (local) one
		return
	visible = pm.any() or pm.menu
	if visible and (_t <= 0.0 or pm.menu):
		_t = 0.1
		queue_redraw()


func map_data() -> Dictionary:
	"""head position, its yaw and field of view, the rover; for the player in the game also «me»"""
	var cam: Camera3D = main.cams[0] if not main.cams.is_empty() else null
	var d := {}
	if cam != null:
		d = {"hx": cam.global_position.x, "hz": cam.global_position.z, "hy": rad_to_deg(cam.global_rotation.y), "fov": float(main.CAM_FOV[0])}
	var g = main.game
	var lp = main.localplay
	if local and lp != null and lp.active and lp.p != null and g != null:
		if str(lp.role) == "guard":
			var gc: int = g.guard_cam(lp.p)
			if gc < main.cams.size():
				var c2: Camera3D = main.cams[gc]
				d = {"hx": c2.global_position.x, "hz": c2.global_position.z, "hy": rad_to_deg(c2.global_rotation.y), "fov": float(main.CAM_FOV[mini(gc, 1)])}
		else:
			var a = lp.p["actor"]
			d["me"] = [a.position.x, a.position.z]
	if main.mover_on or main.rig.position.length() > 0.5:
		d["rx"] = main.rig.position.x
		d["rz"] = main.rig.position.z
		d["ry"] = rad_to_deg(main.rig.rotation.y)
	return d


func _draw() -> void:
	var vs := size
	var font := get_theme_default_font()
	# the chips of the controllers
	var ds: Array = pm.devices()
	var x := 14.0
	var y := vs.y - (110.0 if local else 96.0)
	if local:
		y = 128.0
		x = vs.x - 14.0
	var chips := []
	for d in ds:
		var r: String = pm.role_of(d)
		if r == "":
			continue
		chips.append([pm.number(d), pm.role_name(r), pm.role_color(r), d == pm.last_dev and main.now() - pm.last_use < 1.0])
	for ch in chips:
		var txt := "%d  %s" % [int(ch[0]), str(ch[1])]
		var w := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x + 34.0
		var rx := x - w if local else x
		var rr := Rect2(Vector2(rx, y), Vector2(w, 24))
		draw_rect(rr, Color(0.03, 0.05, 0.08, 0.8))
		draw_rect(rr, ch[2], false, 3.0 if ch[3] else 1.5)
		_pad_icon(Vector2(rx + 13, y + 12), ch[2])
		draw_string(font, Vector2(rx + 26, y + 17), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.WHITE)
		if local:
			y += 28.0
		else:
			x += w + 6.0
	# the mini-map / direction
	var show_map: bool = local or main.now() - pm.last_use < 20.0
	if show_map and not pm.menu:
		var R := 62.0 if local else 44.0
		var c := Vector2(vs.x - R - 16.0, vs.y - R - 70.0) if local else Vector2(14.0 + R, vs.y - 112.0 - R)
		if not local and main.ui_root != null and main.ui_root.visible:
			c.x = 14.0 + R
		draw_map(self, c, R, map_data(), 40.0 if local else 30.0)
	# the focus ring (menu with the controller)
	var f := get_viewport().gui_get_focus_owner()
	if f != null and (pm.menu or (local and main.localplay != null and main.localplay.pad_on())):
		var gr := f.get_global_rect().grow(4.0)
		var a := 0.65 + 0.35 * sin(Time.get_ticks_msec() / 160.0)
		draw_rect(gr, Color(1.0, 0.83, 0.3, a), false, 3.0)
		draw_rect(gr.grow(2.0), Color(0, 0, 0, 0.5), false, 1.0)


func _pad_icon(c: Vector2, col: Color) -> void:
	draw_rect(Rect2(c + Vector2(-8, -4), Vector2(16, 9)), col, false, 1.5)
	draw_circle(c + Vector2(-7, 3), 3.0, col)
	draw_circle(c + Vector2(7, 3), 3.0, col)


static func draw_map(ci: CanvasItem, c: Vector2, R: float, d: Dictionary, span: float) -> void:
	"""the same picture as MWPad.drawMap of the web pages"""
	if d.is_empty():
		return
	var sc := R / (span / 2.0)
	var dir := func(deg: float) -> Vector2: return Vector2(-sin(deg_to_rad(deg)), -cos(deg_to_rad(deg)))
	var at := func(px: float, pz: float) -> Vector2: return c + (Vector2(px, pz) - Vector2(float(d.get("hx", 0.0)), float(d.get("hz", 0.0)))) * sc
	ci.draw_circle(c, R, Color(0.03, 0.05, 0.08, 0.72))
	var half := float(d.get("fov", 66.0)) / 2.0
	var poly := PackedVector2Array([c])
	for i in range(13):
		poly.append(c + dir.call(float(d.get("hy", 0.0)) - half + 2.0 * half * i / 12.0) * R * 0.95)
	ci.draw_colored_polygon(poly, Color(1.0, 0.82, 0.24, 0.28))
	if d.has("rx"):
		var p: Vector2 = at.call(float(d["rx"]), float(d["rz"]))
		if p.distance_to(c) < R - 4.0:
			var v: Vector2 = dir.call(float(d["ry"]))
			var n := Vector2(-v.y, v.x)
			ci.draw_colored_polygon(PackedVector2Array([p + v * 7.0, p - v * 5.0 + n * 5.0, p - v * 5.0 - n * 5.0]), Color(0.35, 0.9, 0.45))
	if d.has("me"):
		var q: Vector2 = at.call(float(d["me"][0]), float(d["me"][1]))
		if q.distance_to(c) < R - 3.0:
			ci.draw_circle(q, 4.0, Color.WHITE)
	ci.draw_circle(c, 4.0, Color(1.0, 0.6, 0.2))
	ci.draw_arc(c, R, 0.0, TAU, 48, Color(1, 1, 1, 0.35), 2.0, true)
	for m in [[float(d.get("hy", 0.0)), Color(1.0, 0.83, 0.3)], [float(d.get("ry", 0.0)), Color(0.35, 0.9, 0.45)]]:
		if m[1] == Color(0.35, 0.9, 0.45) and not d.has("ry"):
			continue
		var v2: Vector2 = dir.call(float(m[0]))
		var n2 := Vector2(-v2.y, v2.x)
		var tip := c + v2 * (R + 1.0)
		ci.draw_colored_polygon(PackedVector2Array([tip, tip - v2 * 10.0 + n2 * 6.0, tip - v2 * 10.0 - n2 * 6.0]), m[1])
	ci.draw_string(ThemeDB.fallback_font, c + Vector2(-4, -R + 13), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1, 1, 1, 0.8))


static func draw_crosshair(ci: CanvasItem, c: Vector2, rad: float, lw: float) -> void:
	"""ONE crosshair (MWPad.XH_CSS of the web pages): a red ring with a cross through it, a dark edge"""
	var col := Color(1.0, 0.23, 0.19, 0.95)
	var dk := Color(0, 0, 0, 0.5)
	var arm := rad + 14.0
	ci.draw_arc(c, rad, 0.0, TAU, 72, dk, lw + 2.0, true)
	for v in [Vector2.RIGHT, Vector2.DOWN]:
		ci.draw_line(c - v * arm, c + v * arm, dk, lw + 2.0, true)
	ci.draw_arc(c, rad, 0.0, TAU, 72, col, lw, true)
	for v in [Vector2.RIGHT, Vector2.DOWN]:
		ci.draw_line(c - v * arm, c + v * arm, col, lw, true)
