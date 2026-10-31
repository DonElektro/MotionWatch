extends Control
## Overview map in the corner of the view (from 3D-3.12): north up, MoveEye in the middle, what the cameras see (cones),
## houses and obstacles, visitors, players of the game, the goal, where you look from. Wheel = zoom, drag the corner = size,
## click = fly there. M or the button «Karte» shows / hides it. At a real place the aerial picture lies below.

var main
var size_px := 220.0
var span := 80.0                 # metres from the left to the right edge
var resizing := false
var res_from := Vector2.ZERO
var res_size := 0.0
var t_draw := 0.0
const MIN_PX := 130.0
const MAX_PX := 520.0
const PERSON := ["person", "child", "jogger"]


func _ready() -> void:
	position = Vector2(14, 92)
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	tooltip_text = "Übersichtskarte · Rad: zoomen · Ecke unten rechts ziehen: Grösse · Klick: dorthin fliegen · M: aus / ein"
	_apply_size()


func _apply_size() -> void:
	size = Vector2(size_px, size_px)
	custom_minimum_size = size


func _process(dt: float) -> void:
	if not visible:
		return
	t_draw -= dt
	if t_draw <= 0.0:
		t_draw = 0.15
		queue_redraw()


func center() -> Vector3:
	return main.rig.global_position if main.rig != null else Vector3.ZERO


func w2m(p: Vector3) -> Vector2:
	var c := center()
	var k := size_px / span
	return Vector2(size_px / 2.0 + (p.x - c.x) * k, size_px / 2.0 + (p.z - c.z) * k)


func m2w(q: Vector2) -> Vector3:
	var c := center()
	var k := span / size_px
	return Vector3(c.x + (q.x - size_px / 2.0) * k, 0.0, c.z + (q.y - size_px / 2.0) * k)


func _draw() -> void:
	var s := size_px
	var rect := Rect2(Vector2.ZERO, Vector2(s, s))
	draw_rect(rect, Color(0.16, 0.24, 0.14, 0.88))
	var k := s / span
	var c := center()
	# real place: the aerial picture below
	if main.terrain and main.scene == "ort" and main.geo.photo_near != null:
		var rn: Rect2 = main.geo.rect_near
		var a := w2m(Vector3(rn.position.x, 0, rn.position.y))
		var tex: Texture2D = main.geo.photo_near
		draw_texture_rect(tex, Rect2(a, rn.size * k), false, Color(1, 1, 1, 0.85))
	# 3D-4.x: the map of a scene in the style of the Landeskarte (bergtal.gd), turned with the scene; orientation «schwer»: none
	var md0: Dictionary = main.scenes.data
	var orient := str(md0.get("orientation", "leicht"))
	if md0.has("map_img") and orient != "schwer":
		var mi: Array = md0["map_img"]
		var o2 := w2m(mi[1])
		var ax := (w2m(mi[2]) - o2) / float(mi[4])
		var ay := (w2m(mi[3]) - o2) / float(mi[4])
		draw_set_transform_matrix(Transform2D(ax, ay, o2))
		draw_texture(mi[0], Vector2.ZERO, Color(1, 1, 1, 0.92))
		draw_set_transform_matrix(Transform2D.IDENTITY)
		if md0.has("map_fog"):                             # Bergtal: still covered parts of the map (bergtal_aussicht.gd)
			var mf: Array = md0["map_fog"]
			var of := w2m(mf[1])
			draw_set_transform_matrix(Transform2D((w2m(mf[2]) - of) / float(mf[4]), (w2m(mf[3]) - of) / float(mf[4]), of))
			draw_texture(mf[0], Vector2.ZERO)
			draw_set_transform_matrix(Transform2D.IDENTITY)
	# roads of the drawn scenes
	if not main.terrain and main.scenes.data.has("road_z"):
		var rz: float = float(main.scenes.data["road_z"]) - 1.2
		var y0 := w2m(Vector3(0, 0, rz)).y
		draw_rect(Rect2(0, y0 - 2.5 * k, s, 5.0 * k), Color(0.45, 0.44, 0.42, 0.9))
	# obstacles: houses, caravans, fences (boxes), trees and posts (circles)
	var lo := m2w(Vector2(-10, -10))
	var hi := m2w(Vector2(s + 10, s + 10))
	for o in main.obstacles:
		var oc: Vector2 = o["c"]
		if oc.x < lo.x - 20 or oc.x > hi.x + 20 or oc.y < lo.z - 20 or oc.y > hi.z + 20:
			continue
		var mp := w2m(Vector3(oc.x, 0, oc.y))
		if o.has("r"):
			var rr: float = max(1.5, float(o["r"]) * k)
			var tree: bool = float(o["r"]) < 0.8
			draw_circle(mp, rr if not tree else max(rr, 2.2), Color(0.1, 0.32, 0.12, 0.95) if tree else Color(0.55, 0.5, 0.45, 0.95))
		else:
			var h: Vector2 = o["h"]
			var b: Basis = o["b"]
			var pts := PackedVector2Array()
			for corner in [Vector2(-h.x, -h.y), Vector2(h.x, -h.y), Vector2(h.x, h.y), Vector2(-h.x, h.y)]:
				var w3: Vector3 = b * Vector3(corner.x, 0, corner.y)
				pts.append(mp + Vector2(w3.x, w3.z) * k)
			var col := Color(0.62, 0.6, 0.58, 0.95) if not o["po"] else Color(0.3, 0.42, 0.22, 0.95)
			draw_colored_polygon(pts, col)
			pts.append(pts[0])
			draw_polyline(pts, Color(0.1, 0.1, 0.1, 0.6), 1.0)
	# 3D-4.x: a scene with its own map (bergtal.gd): road, trails, lakes, and marks (sleeping spots, viewpoints, places)
	var md: Dictionary = main.scenes.data
	if md.has("map_lines") and orient != "schwer":
		for ln in md["map_lines"]:
			var pl := PackedVector2Array()
			for q in ln[0]:
				pl.append(w2m(Vector3(q.x, 0, q.y)))
			if pl.size() > 1:
				draw_polyline(pl, ln[1], float(ln[2]))
	if md.has("map_marks") and orient == "leicht":
		for mk in md["map_marks"]:
			var mp2 := w2m(mk[0])
			if not rect.grow(4).has_point(mp2):
				continue
			draw_circle(mp2, 4.5 if mk[3] else 3.0, mk[2])
			if mk[3] or span < 450.0:
				draw_string(ThemeDB.fallback_font, mp2 + Vector2(5, 4), str(mk[1]), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(1, 1, 1, 0.85))
	# what the cameras see
	for i in [1, 0]:
		var cam: Camera3D = main.cams[i]
		var p := w2m(cam.global_position)
		var f: Vector3 = -cam.global_transform.basis.z
		var ang := atan2(f.z, f.x)
		var half: float = deg_to_rad(float(main.CAM_FOV[i]) / 2.0)
		var reach := (30.0 if i == 0 else 20.0) * k
		var col := Color(1.0, 0.62, 0.2, 0.28) if i == 0 else Color(0.5, 0.75, 1.0, 0.22)
		var fan := PackedVector2Array([p])
		for j in range(13):
			var a2: float = ang - half + 2.0 * half * j / 12.0
			fan.append(p + Vector2(cos(a2), sin(a2)) * reach)
		draw_colored_polygon(fan, col)
	# the game: goal, players
	var g = main.game
	if g != null and g.open:
		var gp := w2m(g.goal)
		draw_arc(gp, 6, 0, TAU, 16, Color(1, 0.85, 0.2), 2.0)
		draw_line(gp + Vector2(-4, -4), gp + Vector2(4, 4), Color(1, 0.85, 0.2), 2.0)
		for pl in g.players:
			if pl == null or not is_instance_valid(pl["actor"]):
				continue
			var col2: Color = g.TEAM_COLORS[int(pl.get("team", 0))] if main.game_teams else g.COLORS[int(pl["slot"])]
			var pp := w2m(pl["actor"].global_position)
			draw_circle(pp, 4.5, col2)
			draw_arc(pp, 5.5, 0, TAU, 12, Color(1, 1, 1), 1.0)
	# visitors
	for v in main.visitors.get_children():
		if v.done:
			continue
		var vp := w2m(v.global_position)
		if not rect.grow(4).has_point(vp):
			continue
		var vc := Color(0.35, 0.65, 1.0) if v.kind in PERSON else (Color(0.8, 0.8, 0.85) if v.kind == "car" else Color(0.85, 0.55, 0.25))
		draw_circle(vp, 3.0 if v.kind != "car" else 4.0, vc)
		if v == main.selected:
			draw_arc(vp, 6.0, 0, TAU, 16, Color(1, 0.8, 0.2), 2.0)
	# MoveEye
	var mp0 := w2m(main.head.global_position)
	draw_circle(mp0, 5.0, Color(0.95, 0.45, 0.1))
	draw_arc(mp0, 5.0, 0, TAU, 16, Color(1, 1, 1), 1.2)
	# where you look from (the free view)
	if main.view_mode == 0:
		var vp2 := w2m(main.view_cam.global_position)
		var fw: Vector3 = -main.view_cam.global_transform.basis.z
		var dv := Vector2(fw.x, fw.z).normalized() if Vector2(fw.x, fw.z).length() > 0.01 else Vector2(0, -1)
		if rect.has_point(vp2):
			draw_colored_polygon(PackedVector2Array([vp2 + dv * 8, vp2 + dv.orthogonal() * 4 - dv * 4, vp2 - dv.orthogonal() * 4 - dv * 4]), Color(1, 1, 1, 0.95))
	# frame, north, scale, resize corner
	draw_rect(rect, Color(1, 1, 1, 0.35), false, 1.5)
	draw_string(ThemeDB.fallback_font, Vector2(s / 2.0 - 4, 13), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.9))
	var bar := 10.0
	for cand in [5.0, 10.0, 20.0, 50.0, 100.0, 200.0]:
		if cand * k > 30.0:
			bar = cand
			break
	draw_line(Vector2(8, s - 10), Vector2(8 + bar * k, s - 10), Color(1, 1, 1, 0.9), 2.0)
	draw_string(ThemeDB.fallback_font, Vector2(8, s - 14), "%d m" % int(bar), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1, 1, 1, 0.9))
	for j in range(3):
		var o2 := 4.0 + j * 4.0
		draw_line(Vector2(s - o2, s - 2), Vector2(s - 2, s - o2), Color(1, 1, 1, 0.7), 1.0)


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton:
		if ev.button_index == MOUSE_BUTTON_LEFT:
			if ev.pressed:
				if ev.position.x > size_px - 18 and ev.position.y > size_px - 18:
					resizing = true
					res_from = ev.global_position
					res_size = size_px
				else:
					var g: Vector3 = m2w(ev.position)
					g.y = main.ground_y(g.x, g.z)
					main.fly_to(g, 14.0)
				accept_event()
			else:
				if resizing:
					resizing = false
					main.map_size = size_px
					main._settings_dirty = true
		elif ev.pressed and ev.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			span = clampf(span * (0.8 if ev.button_index == MOUSE_BUTTON_WHEEL_UP else 1.25), 30.0, 900.0)
			main.map_span = span
			main._settings_dirty = true
			queue_redraw()
			accept_event()
	elif ev is InputEventMouseMotion and resizing:
		var d: Vector2 = ev.global_position - res_from
		size_px = clampf(res_size + max(d.x, d.y), MIN_PX, MAX_PX)
		_apply_size()
		queue_redraw()
		accept_event()
