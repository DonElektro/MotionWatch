extends Node
## 3D-3.98 (realism): tracks in the snow. While it snows (or snow lies), people, animals and cars leave prints on the
## ground; MoveEye sees them like a real camera would (also in the morning, after the visitor is gone).
## Prints are flat dark-blue patches below the scene (scene_parent: gone with a scene change), at most MAX, the oldest go
## first, all fade 20 minutes after the snow has stopped.

var main
const MAX := 700
var prints: Array = []                 # MeshInstance3D, oldest first
var _mat: StandardMaterial3D
var _meshes := {}
var _no_snow_t := 0.0
var _t := 0.0


func _ready() -> void:
	_mat = StandardMaterial3D.new()
	_mat.albedo_color = Color(0.56, 0.6, 0.7)
	_mat.roughness = 1.0
	for k in [["foot", Vector2(0.11, 0.27)], ["paw", Vector2(0.08, 0.09)], ["hoof", Vector2(0.07, 0.08)], ["tyre", Vector2(0.2, 0.7)]]:
		var pm := PlaneMesh.new()
		pm.size = k[1]
		_meshes[k[0]] = pm


func _kind_of(v) -> String:
	var k := str(v.get("kind"))
	if k == "car":
		return "tyre"
	if k in ["deer", "boar", "cow", "horse", "chamois", "ibex", "sheep"]:
		return "hoof"
	if k == "person":
		return "foot"
	return "paw"


func _process(dt: float) -> void:
	_t += dt
	if _t < 0.15:
		return
	_t = 0.0
	var snowy: bool = main.weather == "snow"
	if not snowy:
		_no_snow_t += 0.15 * float(main.speed)
		if _no_snow_t > 1200.0 and not prints.is_empty():
			for p in prints:
				if is_instance_valid(p):
					p.queue_free()
			prints.clear()
		return
	_no_snow_t = 0.0
	if main.visitors == null or main.scene_parent == null:
		return
	for v in main.visitors.get_children():
		if not v is Node3D or v.get("kind") == null or float(v.get("cur_speed")) < 0.05:
			continue
		var pos: Vector3 = (v as Node3D).global_position
		var kind := _kind_of(v)
		var step := 0.65 if kind == "foot" else (1.2 if kind == "tyre" else 0.45)
		var last = v.get_meta("trk", null)
		if last is Vector3 and Vector2(pos.x - last.x, pos.z - last.z).length() < step:
			continue
		var side: float = -1.0 if bool(v.get_meta("trk_l", false)) else 1.0
		v.set_meta("trk_l", side > 0.0)
		v.set_meta("trk", pos)
		var dir := Vector3(pos.x - last.x, 0, pos.z - last.z).normalized() if last is Vector3 else -(v as Node3D).global_transform.basis.z
		var right := dir.cross(Vector3.UP).normalized()
		if kind == "tyre":
			for s_ in [-0.8, 0.8]:
				_put(pos + right * s_, dir, kind)
		else:
			_put(pos + right * side * (0.09 if kind == "foot" else 0.05), dir, kind)


func _put(p: Vector3, dir: Vector3, kind: String) -> void:
	var mi := MeshInstance3D.new()
	mi.mesh = _meshes[kind]
	mi.material_override = _mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	main.scene_parent.add_child(mi)
	var y: float = main.ground_y(p.x, p.z) + 0.015
	mi.global_position = Vector3(p.x, y, p.z)
	mi.rotation.y = atan2(dir.x, dir.z)
	prints.append(mi)
	while prints.size() > MAX:
		var o = prints.pop_front()
		if is_instance_valid(o):
			o.queue_free()
