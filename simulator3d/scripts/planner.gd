extends PanelContainer
## Aufstell-Planer (3D-3.44): where should MoveEye stand? A map from above of the place: what the head camera can see
## (with its turning range), what the fixed camera sees, and the blind spots behind caravan, hedges, houses and hills - for
## the area that matters (tent / caravan). «Besten Platz suchen» tries many spots and directions; «Hierhin stellen» puts
## MoveEye there in the simulator; MoveEye takes over the patrol (3 waypoints across the area) with one button on
## its page (Simulator → Aufstell-Planer) - CONTROL action "planner".

const UI = preload("res://scripts/ui_style.gd")

var main
var map: Control
var info: Label
var best_b: Button
var put_b: Button
var night_cb: CheckButton
var zone_r := 12.0              # radius of the area that matters (m)
var span := 56.0                # the map shows this many metres
var cand_pos := Vector3.ZERO    # the spot being looked at
var cand_yaw := 0.0             # where «straight ahead» of the head points (rotation.y)
var cells := []                 # [Vector2 xz, kind] kind: 0 unseen 1 head 2 fixed 3 both, +10 = in the area
var stats := {}
var best := {}                  # {"pos", "yaw", "pct"}
var busy := false
var night := false
var _drag := false


func _ready() -> void:
	visible = false
	add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.97), UI.LINE, 14, 14, 1))
	anchor_left = 0.0
	anchor_top = 0.0
	anchor_right = 1.0
	anchor_bottom = 1.0
	offset_left = 16
	offset_top = 16
	offset_right = -410                 # next to the panel on the right
	offset_bottom = -16
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	add_child(v)
	var hd := HBoxContainer.new()
	v.add_child(hd)
	var t := UI.heading("Aufstell-Planer: Wo soll MoveEye hin?")
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(t)
	var x := Button.new()
	x.text = "Schliessen"
	x.pressed.connect(func(): open(false))
	hd.add_child(x)
	var lead := UI.small("Grün: sieht die Kopfkamera (mit Drehen) · Blau: die Weitwinkel-Kamera · Rot: tote Winkel im wichtigen Bereich (Kreis um Zelt und Wohnwagen). Den Punkt von MoveEye auf der Karte ziehen, um andere Plätze auszuprobieren; Rechtsklick dreht die Blickrichtung.")
	lead.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(lead)
	map = Control.new()
	map.custom_minimum_size = Vector2(300, 300)
	map.size_flags_vertical = Control.SIZE_EXPAND_FILL
	map.mouse_filter = Control.MOUSE_FILTER_STOP
	map.draw.connect(_draw_map)
	map.gui_input.connect(_map_input)
	map.clip_contents = true
	v.add_child(map)
	info = UI.small("", UI.TXT)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_theme_font_size_override("font_size", 14)
	v.add_child(info)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	v.add_child(row)
	best_b = Button.new()
	best_b.text = "Besten Platz suchen"
	best_b.pressed.connect(search_best)
	UI.primary(best_b)
	row.add_child(best_b)
	put_b = Button.new()
	put_b.text = "MoveEye hierhin stellen"
	put_b.pressed.connect(place_here)
	row.add_child(put_b)
	var put_rs := Button.new()                       # 3D-3.72: place it and let MoveEye take the reference scan there
	put_rs.text = "Hierhin stellen + Referenz-Scan"
	put_rs.tooltip_text = "MoveEye an diesen Platz stellen und gleich die Referenz-Fotos aufnehmen lassen"
	put_rs.pressed.connect(func():
		place_here()
		main.mw_request("refscan"))
	row.add_child(put_rs)
	var back := Button.new()
	back.text = "Zurück an den Anfang"
	back.pressed.connect(func():
		main.set_home(Vector3.ZERO, 0.0)
		cand_pos = Vector3.ZERO
		cand_yaw = 0.0
		compute())
	row.add_child(back)
	night_cb = CheckButton.new()
	night_cb.text = "Nacht (Infrarot-Reichweite)"
	night_cb.toggled.connect(func(on):
		night = on
		compute())
	row.add_child(night_cb)


func open(on: bool) -> void:
	visible = on
	if on:
		cand_pos = main.rig.global_position
		cand_yaw = main.rig.rotation.y
		night = main.is_dark()
		night_cb.set_pressed_no_signal(night)
		best = {}
		compute()


func area_center() -> Vector3:
	var a: Vector3 = main.obj.get("pir", Vector3.ZERO)
	var b: Vector3 = main.obj.get("door", Vector3.ZERO)
	return (a + b) / 2.0


func _pan_half() -> float:
	var s: Dictionary = main.mw.get("servo", {})
	var hp := float(s.get("pan_range", 180.0)) / 2.0
	if s.has("pan_limit"):
		hp = min(hp, float(s.get("pan_limit", hp)))
	return clampf(hp, 5.0, 180.0)


func _yaw_to(from: Vector3, to: Vector3) -> float:
	var d := to - from
	return atan2(-d.x, -d.z)


func _sees_head(p: Vector3, yaw: float, q: Vector3) -> bool:
	var reach: float = main.ir_range + 4.0 if night else 32.0
	var d := Vector2(q.x - p.x, q.z - p.z).length()
	if d > reach or d < 0.5:
		return d < 0.5
	var rel := wrapf(_yaw_to(p, q) - yaw, -PI, PI)
	if abs(rad_to_deg(rel)) > _pan_half() + main.CAM_FOV[0] / 2.0:
		return false
	return main.line_free(p + Vector3(0, main.HEAD_H, 0), q)


func _sees_fixed(q: Vector3) -> bool:
	var c1: Transform3D = main.cams[1].global_transform
	var p := c1.origin
	var d := Vector2(q.x - p.x, q.z - p.z).length()
	if d > (12.0 if night else 25.0):
		return false
	var fw := -c1.basis.z
	var to := (q - p)
	to.y = 0
	fw.y = 0
	if fw.length() < 0.01 or to.length() < 0.01:
		return true
	if rad_to_deg(fw.normalized().angle_to(to.normalized())) > main.CAM_FOV[1] / 2.0:
		return false
	return main.line_free(p, q)


func _cover(p: Vector3, yaw: float, step: float, only_area: bool) -> Dictionary:
	var c := area_center()
	var out := []
	var n_area := 0
	only_area = only_area                              # the grid always lies round the important area
	var seen_area := 0
	var head_area := 0
	var half := span / 2.0
	var x := -half
	while x < half:
		var z := -half
		while z < half:
			var q := Vector3(c.x + x, 0, c.z + z)
			var in_area := Vector2(q.x - c.x, q.z - c.z).length() <= zone_r
			if only_area and not in_area:
				z += step
				continue
			q.y = main.ground_y(q.x, q.z) + 1.0
			var h := _sees_head(p, yaw, q)
			var f := _sees_fixed(q)
			var k := (1 if h else 0) + (2 if f else 0)
			if in_area:
				n_area += 1
				if k > 0:
					seen_area += 1
				if h:
					head_area += 1
			if not only_area:
				out.append([Vector2(q.x, q.z), k + (10 if in_area else 0)])
			z += step
		x += step
	return {"cells": out, "pct": 100.0 * seen_area / max(1, n_area), "head_pct": 100.0 * head_area / max(1, n_area), "n": n_area}


func compute() -> void:
	var r := _cover(cand_pos, cand_yaw, 1.4, false)
	cells = r["cells"]
	stats = r
	var lines := ["Wichtiger Bereich (%d m um Zelt und Wohnwagen): %d %% im Blick, davon %d %% mit der Kopfkamera." % [int(zone_r), int(r["pct"]), int(r["head_pct"])]]
	lines.append("Drehbereich des Kopfes: ±%d° · Kamera-Blickwinkel %d° · %s" % [int(_pan_half()), int(main.CAM_FOV[0]),
			("nachts reicht das Infrarot-Licht etwa %d m" % int(main.ir_range)) if night else "tagsüber etwa 30 m"])
	if not best.is_empty():
		lines.append("Bester gefundener Platz: %d %% im Blick (gelber Ring auf der Karte)." % int(best["pct"]))
	var wp := waypoints()
	lines.append("Für MoveEye: Patrouille über 3 Punkte (Schwenk %d / %d / %d %%) – auf der Seite von MoveEye unter Simulator → «Vom Aufstell-Planer übernehmen»." % [int(wp[0][0]), int(wp[1][0]), int(wp[2][0])])
	info.text = "\n".join(lines)
	map.queue_redraw()


func waypoints() -> Array:
	"""3 patrol points (pan %, tilt %) across the important area, as seen from the current spot of MoveEye"""
	var p: Vector3 = main.rig.global_position
	var yaw: float = main.rig.rotation.y
	var c := area_center()
	var mid := rad_to_deg(wrapf(_yaw_to(p, c) - yaw, -PI, PI))
	var d := Vector2(c.x - p.x, c.z - p.z).length()
	var spread := rad_to_deg(atan2(zone_r * 0.7, max(1.0, d)))
	var hp := _pan_half()
	var out := []
	for k in [-1.0, 0.0, 1.0]:
		var rel: float = clampf(mid + k * spread, -hp, hp)
		var pan_deg := -rel                                    # the head turns with rotation.y = -pan
		out.append([clampf(50.0 + pan_deg / max(1.0, float(main.mw.get("servo", {}).get("pan_range", 180.0)) / 2.0) * 50.0, 0.0, 100.0), 50.0])
	return out


func state() -> Dictionary:
	return {"ok": true, "open": visible, "busy": busy, "pct": int(stats.get("pct", 0)), "head_pct": int(stats.get("head_pct", 0)),
			"pos": [snappedf(main.rig.global_position.x, 0.1), snappedf(main.rig.global_position.z, 0.1)],
			"best": {"pos": [snappedf(best["pos"].x, 0.1), snappedf(best["pos"].z, 0.1)], "pct": int(best["pct"])} if not best.is_empty() else null,
			"waypoints": waypoints()}


func search_best() -> void:
	"""try spots round the important area and directions - the one that sees most of it"""
	if busy:
		return
	busy = true
	best_b.disabled = true
	best_b.text = "Suche …"
	var c := area_center()
	var tries := [[cand_pos, cand_yaw]]
	for dist in [4.0, 7.0, 10.0, 14.0]:
		for i in 12:
			var a := TAU * i / 12.0
			var p := c + Vector3(sin(a) * dist, 0, cos(a) * dist)
			if not _free_spot(p):
				continue
			tries.append([p, _yaw_to(p, c)])
	var top := {}
	var k := 0
	for tr in tries:
		var r := _cover(tr[0], tr[1], 2.0, true)
		if top.is_empty() or float(r["pct"]) + 0.3 * float(r["head_pct"]) > float(top["score"]):
			top = {"pos": tr[0], "yaw": tr[1], "pct": r["pct"], "score": float(r["pct"]) + 0.3 * float(r["head_pct"])}
		k += 1
		if k % 3 == 0:
			best_b.text = "Suche … %d %%" % int(100.0 * k / tries.size())
			await get_tree().process_frame
	best = top
	cand_pos = top["pos"]
	cand_yaw = top["yaw"]
	busy = false
	best_b.disabled = false
	best_b.text = "Besten Platz suchen"
	compute()


func _free_spot(p: Vector3) -> bool:
	for o in main._ob_near(Vector2(p.x, p.z)):
		if float(main._ob_closest(o, Vector2(p.x, p.z))[1]) < 0.8:
			return false
	return abs(p.x) < 150.0 and abs(p.z) < 150.0


func place_here() -> void:
	main.set_home(cand_pos, cand_yaw)
	compute()


# ---- the map ----
func _w2m(p: Vector2) -> Vector2:
	var s: Vector2 = map.size
	var k: float = min(s.x, s.y) / span
	var c := area_center()
	return s / 2.0 + (p - Vector2(c.x, c.z)) * k


func _m2w(q: Vector2) -> Vector2:
	var s: Vector2 = map.size
	var k: float = min(s.x, s.y) / span
	var c := area_center()
	return Vector2(c.x, c.z) + (q - s / 2.0) / k


func _draw_map() -> void:
	var s: Vector2 = map.size
	map.draw_rect(Rect2(Vector2.ZERO, s), Color("#0b1310"))
	var k: float = min(s.x, s.y) / span
	var cs := 1.4 * k
	var cols := {0: Color(0, 0, 0, 0), 1: Color(0.25, 0.8, 0.4, 0.35), 2: Color(0.25, 0.55, 1.0, 0.35), 3: Color(0.3, 0.85, 0.85, 0.45)}
	for c in cells:
		var kind: int = int(c[1]) % 10
		var area: bool = int(c[1]) >= 10
		var col: Color = cols[kind]
		if area and kind == 0:
			col = Color(1.0, 0.3, 0.3, 0.55)
		elif area:
			col.a += 0.2
		if col.a > 0.0:
			var m := _w2m(c[0])
			map.draw_rect(Rect2(m - Vector2(cs, cs) / 2.0, Vector2(cs, cs)), col)
	for o in main.obstacles:                             # caravan, houses, hedges, trees
		var m := _w2m(o["c"])
		if o.has("r"):
			map.draw_circle(m, max(1.5, float(o["r"]) * k), Color(0.75, 0.75, 0.7, 0.8))
		else:
			var h: Vector2 = o["h"]
			var b: Basis = o["b"]
			var pts := PackedVector2Array()
			for cc in [Vector2(-h.x, -h.y), Vector2(h.x, -h.y), Vector2(h.x, h.y), Vector2(-h.x, h.y)]:
				var w3: Vector3 = b * Vector3(cc.x, 0, cc.y)
				pts.append(_w2m(o["c"] + Vector2(w3.x, w3.z)))
			map.draw_colored_polygon(pts, Color(0.75, 0.75, 0.7, 0.8))
	var ac := area_center()
	map.draw_arc(_w2m(Vector2(ac.x, ac.z)), zone_r * k, 0, TAU, 64, Color(1, 0.85, 0.3, 0.9), 2.0)
	# MoveEye: spot, «straight ahead», the turning range
	var pm := _w2m(Vector2(cand_pos.x, cand_pos.z))
	var hp := deg_to_rad(_pan_half() + main.CAM_FOV[0] / 2.0)
	for a in [cand_yaw - hp, cand_yaw + hp]:
		var dv := Vector2(-sin(a), -cos(a))
		map.draw_line(pm, pm + dv * 60.0, Color(0.3, 0.9, 0.5, 0.8), 2.0)
	map.draw_line(pm, pm + Vector2(-sin(cand_yaw), -cos(cand_yaw)) * 40.0, Color.WHITE, 3.0)
	map.draw_circle(pm, 9.0, Color("#f59a4a"))
	map.draw_circle(pm, 4.0, Color.WHITE)
	var real: Vector3 = main.rig.global_position
	if real.distance_to(cand_pos) > 0.5:
		map.draw_arc(_w2m(Vector2(real.x, real.z)), 7.0, 0, TAU, 24, Color(1, 1, 1, 0.6), 2.0)
	if not best.is_empty():
		var bm := _w2m(Vector2(best["pos"].x, best["pos"].z))
		map.draw_arc(bm, 13.0, 0, TAU, 32, Color("#ffd24a"), 3.0)
		map.draw_string(get_theme_default_font(), bm + Vector2(15, -10), "bester Platz", HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color("#ffd24a"))
	map.draw_string(get_theme_default_font(), Vector2(10, s.y - 10), "%d m" % int(span), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(1, 1, 1, 0.6))


func _map_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton:
		if ev.button_index == MOUSE_BUTTON_LEFT:
			_drag = ev.pressed
			if ev.pressed:
				var w := _m2w(ev.position)
				cand_pos = Vector3(w.x, main.ground_y(w.x, w.y), w.y)
				map.queue_redraw()
			else:
				compute()
		elif ev.button_index == MOUSE_BUTTON_RIGHT and ev.pressed:
			var w2 := _m2w(ev.position)
			cand_yaw = _yaw_to(cand_pos, Vector3(w2.x, 0, w2.y))
			compute()
	elif ev is InputEventMouseMotion and _drag:
		if not (ev.button_mask & MOUSE_BUTTON_MASK_LEFT):
			_drag = false
			compute()
			return
		var w := _m2w(ev.position)
		cand_pos = Vector3(w.x, main.ground_y(w.x, w.y), w.y)
		map.queue_redraw()
