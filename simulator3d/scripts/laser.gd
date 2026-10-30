extends Node3D
## 3D-3.96: «Blickrichtung» for beginners (wish of Daniel): a red laser beam from the head of MoveEye in the direction the
## camera looks, a dot where it hits the ground, and two faint lines for the left and right edge of the picture.
## Only for the operator (HELPER_LAYER) - the cameras of MoveEye never see it. Switch: toolbar «Ansicht» → «Blickrichtung».

var main
var beam: MeshInstance3D
var dot: MeshInstance3D
var edges: Array = []
const MAXD := 60.0


func _ready() -> void:
	beam = _bar(Color(1.0, 0.1, 0.08), 0.018, 0.95)
	dot = MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = 0.09
	s.height = 0.06
	dot.mesh = s
	dot.material_override = _mat(Color(1.0, 0.15, 0.1), 1.0)
	dot.layers = main.HELPER_LAYER
	add_child(dot)
	for i in range(2):
		edges.append(_bar(Color(1.0, 0.35, 0.3), 0.01, 0.35))
	visible = false


func _mat(c: Color, a: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = Color(c.r, c.g, c.b, a)
	if a < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.no_depth_test = false
	return m


func _bar(c: Color, w: float, a: float) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = Vector3(w, w, 1.0)
	mi.mesh = b
	mi.material_override = _mat(c, a)
	mi.layers = main.HELPER_LAYER
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	return mi


func _hit(o: Vector3, d: Vector3) -> Vector3:
	"""where the ray from o in direction d meets the ground (steps of 0.25 m), else after MAXD"""
	var p := o
	var step := 0.25
	var t := 0.0
	while t < MAXD:
		t += step
		p = o + d * t
		if p.y <= main.ground_y(p.x, p.z):
			return p
		step = minf(1.0, step * 1.08)
	return o + d * MAXD


func _place(bar: MeshInstance3D, a: Vector3, b: Vector3) -> void:
	var l := a.distance_to(b)
	if l < 0.01:
		bar.visible = false
		return
	bar.visible = true
	bar.global_transform = Transform3D(Basis.looking_at((b - a).normalized(), Vector3.UP if absf((b - a).normalized().y) < 0.99 else Vector3.FORWARD), (a + b) * 0.5)
	bar.scale = Vector3(1, 1, l)


func _process(_dt: float) -> void:
	visible = (bool(main.show_laser) or (main.parcours != null and main.parcours.overlay_on())) and main.cams.size() > 0   # 3D-4.18: also the aim ray of the parcours overlay
	if not visible:
		return
	var cam: Camera3D = main.cams[0]
	var tr: Transform3D = cam.global_transform
	var o := tr.origin
	var fwd := -tr.basis.z.normalized()
	var h := _hit(o, fwd)
	_place(beam, o, h)
	dot.global_position = h
	dot.visible = h.distance_to(o) < MAXD - 0.5
	var half := deg_to_rad(float(main.CAM_FOV[0]) / 2.0)
	for i in range(2):
		var d := fwd.rotated(tr.basis.y.normalized(), half * (1.0 if i == 0 else -1.0)).normalized()
		_place(edges[i], o, _hit(o, d))
