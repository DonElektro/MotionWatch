extends Node3D
## 3D-3.83 (Makeover 10 + 11), nur für den Bediener (HELPER_LAYER - die Kameras von MoveEye sehen nichts davon):
##  10  die Zonen von MoveEye auf dem Boden: MoveEye schickt sie in seinem Zustand («zones», Punkte 0..1 im Bild der
##      Kopfkamera); jeder Punkt wird durch die Kopfkamera auf den Boden gelegt - die Zonen drehen also mit dem Kopf mit,
##      genau wie in MoveEye. Grau = ignorieren, grün = nur hier melden, violett = Privatsphäre.
##  11  die Erkennung live: jeder Rahmen von MoveEye (det.boxes) wird über die Figur in der Welt gelegt - grün mit «erkannt»,
##      wenn dort ein Besucher ist, rot «Fehlalarm», wenn nicht. Besucher gut im Bild, aber ohne Rahmen: orange «übersehen».

var main
var im: ImmediateMesh
var mi: MeshInstance3D
var _labels: Array = []
var _t := 0.0
var stats := {"ok": 0, "false": 0, "missed": 0}

const ZONE_COL := {"ignore": Color(0.75, 0.78, 0.82), "only": Color(0.25, 0.9, 0.45), "privacy": Color(0.72, 0.5, 1.0)}


func _ready() -> void:
	im = ImmediateMesh.new()
	mi = MeshInstance3D.new()
	mi.mesh = im
	mi.layers = main.HELPER_LAYER
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.vertex_color_use_as_albedo = true
	m.no_depth_test = true
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mi.material_override = m
	add_child(mi)
	for i in range(10):
		var l := Label3D.new()
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.no_depth_test = true
		l.font_size = 64
		l.pixel_size = 0.01
		l.fixed_size = false
		l.render_priority = 10
		l.outline_size = 10
		l.layers = main.HELPER_LAYER
		l.visible = false
		add_child(l)
		_labels.append(l)


func _process(dt: float) -> void:
	_t += dt
	if _t < 0.1:
		return
	_t = 0.0
	im.clear_surfaces()
	for l in _labels:
		l.visible = false
	var on_z: bool = main.show_zones3d
	var on_d: bool = main.show_det3d
	if not (on_z or on_d) or main.cams.is_empty() or main.now() - main.mw_t > 4.0:
		return
	var cam: Camera3D = main.cams[0]
	var vs := Vector2(main.vps[0].size)
	var li := 0
	im.surface_begin(Mesh.PRIMITIVE_LINES)
	var drew := false
	if on_z:
		var zs = main.mw.get("zones", [])
		if typeof(zs) == TYPE_ARRAY:
			for z in zs:
				if typeof(z) != TYPE_DICTIONARY:
					continue
				var pts = z.get("points", [])
				if typeof(pts) != TYPE_ARRAY or pts.size() < 3:
					continue
				var col: Color = ZONE_COL.get(str(z.get("mode", "ignore")), Color.WHITE)
				var prev := Vector3.INF
				var first := Vector3.INF
				var cen := Vector3.ZERO
				var n := 0
				for i in range(pts.size() + 1):
					var a = pts[i % pts.size()]
					var b = pts[(i + 1) % pts.size()]
					if i == pts.size():
						break
					for k in range(8):                     # each edge in 8 pieces: the projection bends it
						var u := Vector2(float(a[0]), float(a[1])).lerp(Vector2(float(b[0]), float(b[1])), k / 8.0)
						var g := _ground(cam, u * vs)
						if prev != Vector3.INF:
							_line(prev, g, col)
							drew = true
						prev = g
						if first == Vector3.INF:
							first = g
						cen += g
						n += 1
				if first != Vector3.INF and prev != Vector3.INF:
					_line(prev, first, col)
				if n > 0 and li < _labels.size():
					_label(_labels[li], cen / n + Vector3(0, 0.4, 0), "▱ " + str(z.get("name", "Zone")), col)
					li += 1
	if on_z:                                           # makeover 9: the patrol points of MoveEye as rays from the head
		var wp = main.mw.get("waypoints", [])
		if typeof(wp) == TYPE_ARRAY:
			var o: Vector3 = cam.global_position
			for i in range(wp.size()):
				var w = wp[i]
				if typeof(w) != TYPE_ARRAY or w.size() < 2:
					continue
				var az := deg_to_rad(-rad_to_deg(main.rig.rotation.y) + float(w[0]))
				var el := deg_to_rad(float(w[1]) - 6.0)
				var dir := Vector3(sin(az) * cos(el), sin(el), -cos(az) * cos(el))
				var e: Vector3 = o + dir * 20.0
				if dir.y < -0.01:
					e = o + dir * minf(40.0, -o.y / dir.y)
				_line(o, e, Color(0.35, 0.65, 1.0, 0.8))
				_ring(Vector3(e.x, 0.0, e.z), 0.35, Color(0.35, 0.65, 1.0))
				drew = true
				if li < _labels.size():
					_label(_labels[li], e + Vector3(0, 0.5, 0), "P%d" % (i + 1), Color(0.45, 0.75, 1.0))
					li += 1
	if on_d and main.now() - main.mw_det_t < 1.5:
		var boxes := []
		var b_ = main.mw_det.get("boxes", [])
		if typeof(b_) == TYPE_ARRAY:
			boxes = b_
		var used := {}
		for bx in boxes:
			if typeof(bx) != TYPE_ARRAY or bx.size() != 4:
				continue
			var feet := _ground(cam, Vector2(float(bx[0]) + float(bx[2]) / 2.0, float(bx[1]) + float(bx[3])) * vs)
			var best = null
			var bd := 3.0
			for v in main.visitors.get_children() + get_tree().get_nodes_in_group("erleben_fig"):   # + the figures of the Erlebniswelt (erlebniswelt.gd)
				if not (v is Node3D) or used.has(v) or not v.is_visible_in_tree():
					continue
				var d: float = Vector2(v.global_position.x - feet.x, v.global_position.z - feet.z).length()
				if d < bd:
					bd = d
					best = v
			if best != null:
				used[best] = true
				_frame(best.global_position, Color(0.25, 1.0, 0.45))
				if li < _labels.size():
					_label(_labels[li], best.global_position + Vector3(0, 2.2, 0), "✓ erkannt", Color(0.25, 1.0, 0.45))
					li += 1
			else:
				_ring(feet, 0.8, Color(1.0, 0.3, 0.3))
				drew = true
				if li < _labels.size():
					_label(_labels[li], feet + Vector3(0, 1.0, 0), "✗ Fehlalarm", Color(1.0, 0.35, 0.35))
					li += 1
			drew = true
		# who is well in the picture but has no frame: missed (only people)
		if main.mw_det.has("boxes"):
			for v in main.visitors.get_children():
				if used.has(v) or not (v is Node3D) or not _is_person(v):
					continue
				var p: Vector3 = v.global_position
				if cam.is_position_behind(p) or p.distance_to(cam.global_position) > 25.0:
					continue
				var s := cam.unproject_position(p + Vector3(0, 1.0, 0)) / vs
				if s.x < 0.05 or s.x > 0.95 or s.y < 0.05 or s.y > 0.95:
					continue
				_ring(p, 0.6, Color(1.0, 0.65, 0.2))
				drew = true
				if li < _labels.size():
					_label(_labels[li], p + Vector3(0, 2.2, 0), "? übersehen", Color(1.0, 0.65, 0.2))
					li += 1
	if not drew:
		_line(Vector3(0, -50, 0), Vector3(0, -50.01, 0), Color(0, 0, 0, 0))   # a surface needs a vertex
	im.surface_end()


func _is_person(v) -> bool:
	var k := str(v.get("kind")) if v.get("kind") != null else ""
	return k in ["person", "child", "jogger", "burglar", "thief", "drunk", "courier", "police", "cyclist", "couple", "dogwalk", "sneaker", "stroller"]


func _ground(cam: Camera3D, px: Vector2) -> Vector3:
	var o := cam.project_ray_origin(px)
	var d := cam.project_ray_normal(px)
	if d.y < -0.01:
		var k := -o.y / d.y
		if k < 60.0:
			return o + d * k + Vector3(0, 0.06, 0)
	var f := Vector3(d.x, 0, d.z).normalized() * 60.0
	return Vector3(o.x + f.x, 0.06, o.z + f.z)


func _line(a: Vector3, b: Vector3, c: Color) -> void:
	im.surface_set_color(c)
	im.surface_add_vertex(a)
	im.surface_set_color(c)
	im.surface_add_vertex(b)


func _ring(p: Vector3, r: float, c: Color) -> void:
	for i in range(16):
		var a := TAU * i / 16.0
		var b := TAU * (i + 1) / 16.0
		_line(p + Vector3(cos(a) * r, 0.06, sin(a) * r), p + Vector3(cos(b) * r, 0.06, sin(b) * r), c)


func _frame(p: Vector3, c: Color) -> void:
	"""corner brackets round a standing figure (like the frames of MoveEye), facing the operator's view"""
	var vc: Camera3D = get_viewport().get_camera_3d()
	var right := Vector3.RIGHT
	if vc != null:
		right = vc.global_transform.basis.x
		right.y = 0
		right = right.normalized()
	var w := 0.5
	var h := 1.95
	var l := 0.35
	for sx in [-1.0, 1.0]:
		var x: Vector3 = p + right * w * sx
		_line(x + Vector3(0, 0.05, 0), x + Vector3(0, 0.05 + l, 0), c)
		_line(x + Vector3(0, 0.05, 0), x - right * l * sx + Vector3(0, 0.05, 0), c)
		_line(x + Vector3(0, h, 0), x + Vector3(0, h - l, 0), c)
		_line(x + Vector3(0, h, 0), x - right * l * sx + Vector3(0, h, 0), c)
	_ring(p, 0.55, c)


func _label(l: Label3D, p: Vector3, t: String, c: Color) -> void:
	l.position = p
	l.text = t
	l.modulate = c
	l.visible = true


func info() -> Dictionary:
	var n := 0
	var tx := []
	for l in _labels:
		if l.visible:
			n += 1
			tx.append(l.text)
	return {"labels": n, "texts": tx}
