extends Node
## A second MoveEye device in the same world (3D-3.27): its own pole with a pan/tilt head camera and a fixed camera,
## its own lamps, at another place (opposite, left or right). It answers on its own port (the port of the simulator + 20,
## normally 8785) exactly like the simulator itself, so a second MoveEye (or a second copy on the PC) connects to it
## like to a simulator. A person crossing the place is then seen by both, one after the other.

var main
var Net = preload("res://scripts/net.gd")
var net
var port := 8785
var on := false
var place := "opposite"
var rig: Node3D
var head: Node3D
var head_pitch: Node3D
var white: SpotLight3D
var ir: SpotLight3D
var vps: Array = []
var cams: Array = []
var jpgs: Array = [PackedByteArray(), PackedByteArray()]
var frame_no := [0, 0]
var last_cap := [0.0, 0.0]
var snap_want := [0.0, 0.0]
var busy := false
var mw := {"servo": {"pan_deg": 0.0, "tilt_deg": 0.0}, "lights": {}}
var mw_t := 0.0

const PLACES := {"opposite": Vector3(0, 0, -30), "left": Vector3(-20, 0, -12), "right": Vector3(20, 0, -12)}
# the interface net.gd needs (the same names as in main.gd)
var CAM_FPS := [10.0, 6.0]
var TH_W := 80
var TH_H := 62
var VERSION := ""
var game:
	get:
		return main.game
var view_no:
	get:
		return main.view_no
var view_want_t:
	get:
		return main.view_want_t
	set(v):
		main.view_want_t = v
var view_jpg:
	get:
		return main.view_jpg
var view_fps:
	get:
		return main.view_fps
	set(v):
		main.view_fps = v


func now() -> float:
	return main.now()


func set_on(v: bool) -> void:
	if v == on:
		return
	on = v
	if on:
		VERSION = main.VERSION
		TH_W = main.TH_W
		TH_H = main.TH_H
		_build()
		net = Net.new()
		net.main = self
		add_child(net)
		port = int(main.stream_port) + 20
		net.start(port)
	else:
		if net != null:
			net.stop()
			net.queue_free()
			net = null
		for n in [rig] + vps:
			if n != null:
				n.queue_free()
		rig = null
		vps.clear()
		cams.clear()


func status() -> String:
	if not on:
		return ""
	var c := "verbunden" if main.now() - mw_t < 3.0 else "wartet auf MoveEye"
	return "Gerät 2: Port %d, %s" % [port, c] + ("" if net == null or net.listening else " (Port belegt!)")


func set_place(p: String) -> void:
	place = p if PLACES.has(p) else "opposite"
	if rig != null:
		_put()


func _put() -> void:
	var p: Vector3 = PLACES[place]
	p.y = main.ground_y(p.x, p.z)
	rig.position = p
	var to := -p
	rig.rotation.y = atan2(-to.x, -to.z)                  # it looks towards the first device


func _build() -> void:
	rig = Node3D.new()
	main.add_child(rig)
	head = Node3D.new()
	head.position = Vector3(0, main.HEAD_H, 0)
	rig.add_child(head)
	head_pitch = Node3D.new()
	head.add_child(head_pitch)
	white = SpotLight3D.new()
	white.spot_range = 40.0
	white.spot_angle = 32.0
	white.light_energy = 0.0
	white.light_color = Color(1.0, 0.97, 0.92)
	head_pitch.add_child(white)
	ir = SpotLight3D.new()
	ir.spot_range = 28.0
	ir.spot_angle = 48.0
	ir.light_energy = 0.0
	head_pitch.add_child(ir)
	var hm := MeshInstance3D.new()
	hm.mesh = main.box(0.25, 0.18, 0.2)
	hm.material_override = main.mat(Color(0.75, 0.2, 0.15))   # a red head: the second device is easy to find
	head_pitch.add_child(hm)
	var pole := MeshInstance3D.new()
	pole.mesh = main.box(0.06, main.HEAD_H, 0.06)
	pole.position = Vector3(0, -main.HEAD_H / 2.0, 0)
	pole.material_override = main.mat(Color(0.2, 0.2, 0.2))
	head.add_child(pole)
	for i in range(2):
		var vp := SubViewport.new()
		vp.size = Vector2i(main.CAM_W[i], main.CAM_H[i])
		vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		vp.msaa_3d = Viewport.MSAA_2X
		vp.world_3d = main.get_viewport().world_3d
		add_child(vp)
		var cam := Camera3D.new()
		cam.keep_aspect = Camera3D.KEEP_WIDTH
		cam.fov = main.CAM_FOV[i]
		cam.near = 0.1
		cam.far = 2000.0
		cam.cull_mask = 1
		vp.add_child(cam)
		vps.append(vp)
		cams.append(cam)
	_put()


func _process(dt: float) -> void:
	if not on or rig == null:
		return
	var s: Dictionary = mw.get("servo", {})
	var step := deg_to_rad(main.SERVO_DEG_S) * dt
	head.rotation.y = move_toward(head.rotation.y, -deg_to_rad(float(s.get("pan_deg", 0.0))), step)
	head_pitch.rotation.x = move_toward(head_pitch.rotation.x, deg_to_rad(float(s.get("tilt_deg", 0.0)) - 6.0), step)
	cams[0].global_transform = head_pitch.global_transform.translated_local(Vector3(0, 0, -0.13))
	cams[1].global_transform = rig.global_transform * Transform3D(Basis.from_euler(Vector3(deg_to_rad(-10.0), 0, 0)), Vector3(0, 2.4, 0.5))
	var L: Dictionary = mw.get("lights", {})
	white.light_energy = 9.0 if L.get("white", false) else 0.0
	if busy:
		return
	var d: Dictionary = net.stream_demand() if net != null else {}
	for i in range(2):
		var f := float(d.get(i, 0.0))
		if main.now() - float(snap_want[i]) < 3.0:
			f = max(f, 2.0)
		if f > 0.0 and (main.now() - float(last_cap[i])) * f >= 1.0:
			_capture(i)
			return


func _capture(i: int) -> void:
	busy = true
	last_cap[i] = main.now()
	var dark: bool = main.is_dark()
	var L: Dictionary = mw.get("lights", {})
	ir.light_energy = 6.0 if i == 0 and L.get("ir", false) else 0.0
	cams[i].environment = main.night_envs[0 if (i == 0 and L.get("ir", false)) else 1] if dark and main.night_envs[0] != null else null
	vps[i].render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	if vps.size() > i:
		var img: Image = vps[i].get_texture().get_image()
		if img != null and not img.is_empty():
			jpgs[i] = img.save_jpg_to_buffer(0.8)
			frame_no[i] += 1
	ir.light_energy = 0.0
	busy = false


# ---- what net.gd asks --------------------------------------------------------------------------------------------
func beacon_name() -> String:
	return "MW Sim · 3D %s · Gerät 2" % main.VERSION


func cpu_now() -> Dictionary:
	return main.cpu_now()


func host_name() -> String:
	return main.host_name()


func info() -> Dictionary:
	var d: Dictionary = main.info()
	d["name"] = beacon_name()
	d["sensors"] = []
	d["device"] = 2
	return d


func latest_jpg(i: int) -> PackedByteArray:
	return jpgs[clampi(i, 0, 1)]


func want_snapshot(i: int) -> void:
	snap_want[clampi(i, 0, 1)] = main.now()


func on_state(d: Dictionary, _host: String) -> void:
	mw = d
	mw_t = main.now()


func world_reply() -> Dictionary:
	var r: Dictionary = main.world_reply()
	r["last_event"] = 0
	r["mover"] = false
	return r


func events_since(_n: int) -> Array:
	return []


func thermal_values() -> PackedFloat32Array:
	var a := PackedFloat32Array()
	a.resize(TH_W * TH_H)
	a.fill(float(main.ambient))
	return a


func control(d: Dictionary) -> Dictionary:
	return main.control(d)


func control_info() -> Dictionary:
	return main.control_info()
