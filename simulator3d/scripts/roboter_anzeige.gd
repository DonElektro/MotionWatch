extends Node3D
## Roboter-Labor: Physik-Anzeigen in der 3D-Welt (Besitzer 22.11.2026)
##   · Servo-Last: die Gelenk-Kugeln grün → orange → ROT (überlastet: das nötige Moment ist grösser als das Servo-Moment)
##   · Schwerpunkt: Kugel mit Lot auf den Boden; Stützfläche = konvexe Hülle aller Bodenkontakte (Füsse, Bauch);
##     Kipp-Reserve = Abstand des Lots vom nächsten Rand (innen +, aussen −), Warnung unter KIPP_WARN
##   · Ziel (Klick in die Welt) als Ring am Boden
## Die Zahlen (Strom, Last, Reserve) rechnet roboter_modell.gd bzw. diese Datei; das Bedienfeld zeigt sie an.

const KIPP_WARN := 0.01            # m
const GRUEN := Color("#3fcf6b")
const ORANGE := Color("#f59a4a")
const ROT := Color("#ff2d2d")

var m                              # roboter_modell.gd
var show_load := true
var show_support := true
var margin := 0.0                  # Kipp-Reserve (m)
var support := PackedVector2Array()
var com_pt := Vector3.ZERO
var tipping := false
var goal = null
var _im: ImmediateMesh
var _mi: MeshInstance3D
var _com: MeshInstance3D
var _goal: MeshInstance3D
var _painted := false


func _ready() -> void:
	_im = ImmediateMesh.new()
	_mi = MeshInstance3D.new()
	_mi.mesh = _im
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.no_depth_test = true
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_mi.material_override = mat
	add_child(_mi)
	_com = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.012
	sm.height = 0.024
	_com.mesh = sm
	var cm := StandardMaterial3D.new()
	cm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	cm.albedo_color = Color("#ffd43b")
	cm.no_depth_test = true
	_com.material_override = cm
	add_child(_com)
	_goal = MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.07
	tm.outer_radius = 0.09
	_goal.mesh = tm
	var gm := StandardMaterial3D.new()
	gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	gm.albedo_color = Color("#3b8cff")
	_goal.material_override = gm
	_goal.visible = false
	add_child(_goal)


static func hull(pts: PackedVector2Array) -> PackedVector2Array:
	if pts.size() < 3:
		return pts
	var h := Geometry2D.convex_hull(pts)
	if h.size() > 1 and h[0] == h[h.size() - 1]:
		h.remove_at(h.size() - 1)
	return h


static func signed_margin(p: Vector2, poly: PackedVector2Array) -> float:
	"""distance of p to the edge of the convex polygon: + inside, − outside"""
	if poly.size() == 0:
		return -1.0
	if poly.size() < 3:
		var dmin := 1e9
		for q in poly:
			dmin = minf(dmin, p.distance_to(q))
		return -dmin
	var d := 1e9
	for i in range(poly.size()):
		var a: Vector2 = poly[i]
		var b: Vector2 = poly[(i + 1) % poly.size()]
		d = minf(d, p.distance_to(Geometry2D.get_closest_point_to_segment(p, a, b)))
	return d if Geometry2D.is_point_in_polygon(p, poly) else -d


func update_all() -> void:
	if m == null or not m.built_ok:
		return
	com_pt = m.com()
	var pts := PackedVector2Array()
	var ys := 0.0
	var cps: Array = m.contact_points()
	for c in cps:
		pts.append(Vector2((c as Vector3).x, (c as Vector3).z))
		ys += (c as Vector3).y
	support = hull(pts)
	margin = signed_margin(Vector2(com_pt.x, com_pt.z), support)
	tipping = margin < KIPP_WARN
	var gy := ys / cps.size() if cps.size() > 0 else 0.0
	_im.clear_surfaces()
	if show_support:
		_com.visible = true
		_com.position = com_pt
		_im.surface_begin(Mesh.PRIMITIVE_LINES)
		var col := ROT if tipping else Color("#ffd43b")
		_im.surface_set_color(col)
		_im.surface_add_vertex(com_pt)
		_im.surface_set_color(col)
		_im.surface_add_vertex(Vector3(com_pt.x, gy, com_pt.z))
		var pc := ROT if tipping else Color("#3b8cff")
		for i in range(support.size()):
			var a: Vector2 = support[i]
			var b: Vector2 = support[(i + 1) % support.size()]
			_im.surface_set_color(pc)
			_im.surface_add_vertex(Vector3(a.x, gy + 0.002, a.y))
			_im.surface_set_color(pc)
			_im.surface_add_vertex(Vector3(b.x, gy + 0.002, b.y))
		# the foot of the plumb line: a small cross
		for dv in [Vector3(0.015, 0, 0), Vector3(0, 0, 0.015)]:
			_im.surface_set_color(col)
			_im.surface_add_vertex(Vector3(com_pt.x, gy + 0.002, com_pt.z) - dv)
			_im.surface_set_color(col)
			_im.surface_add_vertex(Vector3(com_pt.x, gy + 0.002, com_pt.z) + dv)
		_im.surface_end()
	else:
		_com.visible = false
	_goal.visible = goal != null
	if goal != null:
		_goal.position = (goal as Vector3) + Vector3(0, 0.003, 0)
	_paint_load()


static func load_color(l: float) -> Color:
	if l >= 1.0:
		return ROT
	if l < 0.5:
		return GRUEN.lerp(ORANGE, l / 0.5 * 0.4)
	return GRUEN.lerp(ORANGE, 0.4 + (l - 0.5) / 0.5 * 0.6)


func _paint_load() -> void:
	if not show_load and not _painted:
		return
	for b in m.bodies:
		var ids := []
		var mesh_i := 0
		match b["kind"]:
			"buegel":
				ids = ["sy%d" % b["seg"], "sp%d" % b["seg"]]
			"huefte":
				var sd := "l" if b["side"] < 0 else "r"
				ids = ["hy%d%s" % [b["seg"], sd], "hp%d%s" % [b["seg"], sd]]
			"ober":
				ids = ["kn%d%s" % [b["seg"], "l" if b["side"] < 0 else "r"]]
				mesh_i = 1
			_:
				continue
		var mis: Array = b["mis"]
		if mis.size() <= mesh_i:
			continue
		var mat: StandardMaterial3D = (mis[mesh_i] as MeshInstance3D).get_meta("mat")
		if not show_load:
			mat.albedo_color = (m.FARBE["knie"] if b["kind"] == "ober" else b["col"])
			mat.emission_enabled = false
			continue
		var l := 0.0
		for id in ids:
			var si: int = m.servo_index(id)
			if si >= 0:
				l = maxf(l, float(m.servos[si]["load"]))
		var c := load_color(l)
		mat.albedo_color = c
		mat.emission_enabled = l >= 1.0
		mat.emission = ROT * 0.6
	_painted = show_load


func top_loads(k: int) -> Array:
	"""the k servos with the highest load: [[id, load, tau N·m], …]"""
	var arr := []
	for sv in m.servos:
		if sv["parent"] >= 0:
			arr.append([sv["id"], float(sv["load"]), float(sv["tau"])])
	arr.sort_custom(func(a, b): return a[1] > b[1])
	return arr.slice(0, k)


func currents() -> Dictionary:
	var body := 0.0
	var legs := 0.0
	var other := 0.0
	for sv in m.servos:
		var c := float(sv["current"])
		if sv["kind"] in ["sy", "sp"]:
			body += c
		elif sv["kind"] in ["hy", "hp", "kn"]:
			legs += c
		else:
			other += c
	return {"koerper": body, "beine": legs, "rest": other, "total": body + legs + other}
