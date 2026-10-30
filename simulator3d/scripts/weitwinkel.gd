extends Node
## 3D-4.17 (Plan Daniel 30.10.2026, docs/Gehaeuse_Variante2_Weitwinkel.md «Simulator-Einbindung der Weitwinkel-Kamera"):
## the former «feste Kamera» (cams[1]) is now ONE wide-angle camera (Camera Module 3 Wide NoIR: 102° × 67°, 640×360, 8 fps,
## rendered only when somebody asks for it - main._wanted_fps / eco as before) with a mount:
##   scene       on the mast 3 m beside the device (as before, default - old setups stay as they are)
##   base        on the lower part of the device, under the head near the pan axis, looks ahead, tilted down (does not turn)
##   head_front  on the head, looks where the head camera looks (turns with the pan; tilt optional)
##   head_rear   on the head, looks back (yaw offset 180°)
## On the head: only pan (stays level) or pan + tilt (tilt_follow). Tilt slider. Light fisheye at the edges (camfx distort).
## Second infrared LED 120° (PCA9685 channel 4 at MoveEye, lights.ir_wide) as a wide IR spot at the mount.
## Head mounts: a pan limit (second flat cable; 360° servos would need a slip ring) and a slightly heavier head.
## /info cameras[1] and the reply to POST /state («wide») tell MoveEye the mount (part 163 sets «Übersicht lenkt den Kopf»).

const FILE := "user://weitwinkel.json"
const SAVE := ["mount", "tilt", "tilt_follow", "fisheye", "pan_limit", "heavy"]
const MOUNTS := [["scene", "Mast (Szene) – wie bisher, 3 m neben dem Gerät"], ["base", "Unterteil vorne, fest (unter dem Kopf, dreht nicht)"],
		["head_front", "Kopf vorne (dreht mit)"], ["head_rear", "Kopf hinten (dreht mit, schaut zurück)"]]
const FOV_H := 102.0
const FOV_V := 67.0

var main
var mount := "scene"
var tilt := -12.0                 # degrees, - = down (base: 10-15° down; head: added to the head's tilt or to level)
var tilt_follow := false          # on the head: also tilts with the head (otherwise only pans and stays level)
var fisheye := true               # light barrel distortion at the edges (lens of the Wide)
var pan_limit := 170.0            # head mounts: the head turns at most ± this (cable)
var heavy := true                 # head mounts + «Servos wie echt»: the head is a bit slower (more load on the MG90S)
var ir_spot: SpotLight3D
var ir_ex := 0.5                  # exposure of the grey infrared picture of this camera (like main.ir_ex for the head camera)
var _sig := ""


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		for k in SAVE:
			if d.has(k):
				var old = get(k)
				match typeof(old):
					TYPE_FLOAT:
						set(k, float(d[k]))
					TYPE_BOOL:
						set(k, bool(d[k]))
					_:
						set(k, str(d[k]))
	if not mount in MOUNTS.map(func(m): return m[0]):
		mount = "scene"
	tilt = clampf(tilt, -40.0, 20.0)
	pan_limit = clampf(pan_limit, 60.0, 180.0)


func save() -> void:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))
		f.close()


func _put(k: String, v) -> void:
	set(k, v)
	save()


func on_device() -> bool:
	return mount != "scene"


func on_head() -> bool:
	return mount == "head_front" or mount == "head_rear"


func tilt_deg() -> float:
	return -10.0 if mount == "scene" else tilt


func yaw_offset() -> float:
	return 180.0 if mount == "head_rear" else 0.0


# ---- where the camera is -------------------------------------------------------------------------------------------
func place() -> void:
	"""every frame (main._process): the transform of cams[1] (+ the wide infrared spot)"""
	var cam: Camera3D = main.cams[1]
	if mount == "scene" or main.head == null:
		cam.global_transform = Transform3D(Basis.from_euler(Vector3(deg_to_rad(-10.0), -deg_to_rad(float(main.cam1_yaw)), 0)), Vector3(-3.0, 2.4, 3.0))
	elif mount == "base":
		var rb: Basis = main.rig.global_transform.basis.orthonormalized()
		var p: Vector3 = main.head.global_position + Vector3(0, -0.24, 0) + rb * Vector3(0, 0, -0.07)
		cam.global_transform = Transform3D(rb * Basis.from_euler(Vector3(deg_to_rad(tilt), 0, 0)), p)
	else:
		var hb: Basis = (main.head_pitch.global_transform.basis if tilt_follow else main.head.global_transform.basis).orthonormalized()
		var rear := mount == "head_rear"
		var local := Vector3(0, -0.13, 0.13) if rear else Vector3(0, -0.14, -0.08)   # below the head box (front) / behind it (rear)
		var b := hb * Basis.from_euler(Vector3(0, PI if rear else 0.0, 0)) * Basis.from_euler(Vector3(deg_to_rad(tilt), 0, 0))
		cam.global_transform = Transform3D(b, main.head.global_position + hb * local)
	if ir_spot == null:
		ir_spot = SpotLight3D.new()
		ir_spot.spot_angle = 60.0              # 120° LED
		ir_spot.spot_angle_attenuation = 1.2
		ir_spot.spot_range = 16.0
		ir_spot.spot_attenuation = 1.4
		ir_spot.light_energy = 0.0
		main.add_child(ir_spot)
	ir_spot.global_transform = cam.global_transform.translated_local(Vector3(0, -0.03, 0))


func pan_clamp(want_pan: float) -> float:
	"""head mounts: the cable allows at most ± pan_limit (radians of head.rotation.y = -pan)"""
	if not on_head():
		return want_pan
	var lim := deg_to_rad(pan_limit)
	return clampf(want_pan, -lim, lim)


func servo_k() -> float:
	"""the head is heavier with the camera on it (MG90S): a bit slower when «Servos wie echt» is on"""
	var sreal: bool = main.realism != null and main.realism.servo_real
	return 0.85 if (on_head() and heavy and sreal) else 1.0


func ir_wide_on() -> bool:
	var L: Dictionary = main.mw.get("lights", {})
	return bool(L.get("ir_wide", false)) or (bool(main.cond.get("ir", false)) and on_device())


func grey(i: int) -> bool:
	"""the infrared picture (black and white) of camera i: dark, an infrared light on, no white light"""
	if i != 1 or not main.is_dark() or main.white_light.light_energy > 0.0:
		return false
	return main.ir_on() or ir_wide_on()


# ---- the pictures --------------------------------------------------------------------------------------------------
func before_capture(i: int) -> void:
	"""main._capture after realism / simreal: both NoIR cameras see both infrared lights; camera 1 its own look"""
	if ir_spot != null:
		ir_spot.light_energy = 6.0 if (i < 2 and ir_wide_on()) else 0.0   # the head camera (NoIR) sees the wide light too
	if i != 1:
		return
	main.ir_light.light_energy = 9.0 if main.ir_on() else 0.0      # the NoIR Wide sees the IR light of the head too
	var dark: bool = main.is_dark()
	var g := grey(1)
	if dark and main.night_envs[0] != null:
		main.cams[1].environment = main.night_envs[0] if g else main.night_envs[1]
	if g and main.expo_mats.size() > 1:
		main.expo_mats[1].set_shader_parameter("expo", ir_ex)
		main.lens_mats[1].set_shader_parameter("expo", ir_ex)
	if main.camfx_mats.size() > 1:
		var m: ShaderMaterial = main.camfx_mats[1]
		m.set_shader_parameter("distort", 0.16 if fisheye else 0.0)
		if main.realism != null and main.realism.fx_on:
			m.set_shader_parameter("noir", 0.6 if (not dark) else 0.0)     # NoIR by day: a pink cast like the head camera
		if on_head():
			var fov: float = deg_to_rad(FOV_H)
			var te: float = main.realism.exposure_time() if main.realism != null else 0.02
			m.set_shader_parameter("pan_blur", Vector2(float(main.pan_vel) * te / fov, 0.0) if (main.realism != null and main.realism.fx_on) else Vector2.ZERO)


func after_capture(i: int, img: Image) -> void:
	if ir_spot != null:
		ir_spot.light_energy = 0.0
	if i != 1 or img == null or img.is_empty() or not grey(1):
		return
	var sm: Image = img.duplicate()
	sm.resize(32, 18, Image.INTERPOLATE_BILINEAR)
	var s := 0.0
	for y in range(18):
		for x in range(32):
			var c := sm.get_pixel(x, y)
			s += (c.r + c.g + c.b) / 3.0
	var mean: float = maxf(0.01, s / (18.0 * 32.0))
	ir_ex = clampf(ir_ex * pow(0.36 / mean, 0.6), 0.01, 1.0)


func is_grey_capture(i: int) -> bool:
	return i == 1 and grey(1)


# ---- what MoveEye learns -------------------------------------------------------------------------------------------
func cam_info() -> Dictionary:
	return {"id": 1, "name": "Wide camera (NoIR Wide)", "w": main.CAM_W[1], "h": main.CAM_H[1], "fps": main.CAM_FPS[1],
			"fov_h": FOV_H, "fov_v": FOV_V, "on_head": on_head(), "noir": true, "mount": mount, "tilt_deg": snappedf(tilt_deg(), 0.1),
			"yaw_offset": yaw_offset(), "pan_follow": on_head(), "tilt_follow": on_head() and tilt_follow,
			"fisheye": fisheye, "pan_limit": pan_limit if on_head() else null, "ir_wide": ir_wide_on()}


func state() -> Dictionary:
	"""a short form for the reply to POST /state: MoveEye sees a change of the mount at once"""
	return {"mount": mount, "tilt_deg": snappedf(tilt_deg(), 0.1), "yaw_offset": yaw_offset(), "pan_follow": on_head(),
			"tilt_follow": on_head() and tilt_follow, "on_head": on_head(), "fov_h": FOV_H, "fov_v": FOV_V,
			"pan_limit": pan_limit if on_head() else null}


# ---- settings (card «Kamerabild», part «Weitwinkel-Kamera») ---------------------------------------------------------
func add_controls() -> void:
	var m = main
	var sub := {"sub": "Weitwinkel-Kamera"}
	m.add_control("select", "wide_mount", "Weitwinkel-Kamera (Camera Module 3 Wide NoIR, 102° × 67°): Montage",
			func(): return mount, func(v): set_mount(str(v)), "Kamerabild", {"sub": "Weitwinkel-Kamera", "options": MOUNTS})
	m.add_control("slider", "wide_tilt", "Weitwinkel: Neigung (− = nach unten; Unterteil 10–15° nach unten)",
			func(): return tilt, func(v): _put("tilt", clampf(float(v), -40.0, 20.0)), "Kamerabild", {"sub": "Weitwinkel-Kamera", "min": -40, "max": 20, "step": 1, "unit": "°"})
	m.add_control("toggle", "wide_tilt_follow", "Weitwinkel auf dem Kopf: auch mitneigen (aus = nur mitschwenken, bleibt waagrecht)",
			func(): return tilt_follow, func(v): _put("tilt_follow", bool(v)), "Kamerabild", sub)
	m.add_control("toggle", "wide_fisheye", "Weitwinkel: leichtes Fischauge am Bildrand (wie das Objektiv der Wide)",
			func(): return fisheye, func(v): _put("fisheye", bool(v)), "Kamerabild", sub)
	m.add_control("slider", "wide_pan_limit", "Kamera auf dem Kopf: Drehgrenze ± (zweites Flachkabel; für 360°-Servos wäre ein Schleifring nötig)",
			func(): return pan_limit, func(v): _put("pan_limit", clampf(float(v), 60.0, 180.0)), "Kamerabild", {"sub": "Weitwinkel-Kamera", "min": 60, "max": 180, "step": 5, "unit": "°", "expert": true})
	m.add_control("toggle", "wide_heavy", "Kamera auf dem Kopf: Kopf etwas träger (Mehrlast MG90S, mit «Servos wie echt»)",
			func(): return heavy, func(v): _put("heavy", bool(v)), "Kamerabild", {"sub": "Weitwinkel-Kamera", "expert": true})


func set_mount(v: String) -> bool:
	if not v in MOUNTS.map(func(m): return m[0]):
		return false
	if v == mount:
		return true
	mount = v
	if v != "scene" and absf(tilt) < 0.5:
		tilt = -12.0
	save()
	print("wide camera: mount %s" % v)
	return true


func control(d: Dictionary) -> Dictionary:
	"""control API {action: weit, mount?, tilt?, tilt_follow?, fisheye?, pan_limit?, do: info | probe | spawn}"""
	if d.has("mount") and not set_mount(str(d["mount"])):
		return {"ok": false, "error": "unknown mount"}
	if d.has("tilt"):
		_put("tilt", clampf(float(d["tilt"]), -40.0, 20.0))
	for k in ["tilt_follow", "fisheye", "heavy"]:
		if d.has(k):
			_put(k, bool(d[k]))
	if d.has("pan_limit"):
		_put("pan_limit", clampf(float(d["pan_limit"]), 60.0, 180.0))
	var op := str(d.get("do", "info"))
	if op == "probe":
		return {"ok": true, "wide": cam_info(), "probe": probe()}
	if op == "spawn":                                   # Prüfstand: a visitor relative to the device (bearing ° clockwise, metres)
		var a: Vector3 = _rel(float(d.get("bearing", 60.0)), float(d.get("dist", 10.0)))
		var b: Vector3 = _rel(float(d.get("to_bearing", d.get("bearing", 60.0))), float(d.get("to_dist", d.get("dist", 10.0))))
		var v = main.spawn(str(d.get("kind", "person")), a, b)
		if v != null and d.has("speed"):
			v.set("speed", float(d["speed"]))
		return {"ok": v != null, "from": [a.x, a.z], "to": [b.x, b.z]}
	return {"ok": true, "wide": cam_info()}


func _rel(bearing: float, dist: float) -> Vector3:
	"""a place on the ground: bearing in degrees clockwise from where the device looks (pan 0), distance in metres"""
	var rb: Basis = main.rig.global_transform.basis.orthonormalized()
	var fwd: Vector3 = -rb.z
	var right: Vector3 = rb.x
	var r := deg_to_rad(bearing)
	var p: Vector3 = main.rig.global_position + (fwd * cos(r) + right * sin(r)) * dist
	p.y = 0.0
	return p


func probe() -> Dictionary:
	"""Prüfstand «Übersicht → Kopf findet Ziel»: the head and the persons - in which picture is who"""
	var hp: Vector3 = main.head.global_position
	var out := []
	for v in main.visitors.get_children():
		if not (v is Node3D) or str(v.get("kind")) in ["", "car", "van", "moto", "tractor"]:
			continue
		var p: Vector3 = (v as Node3D).global_position + Vector3(0, 1.0, 0)
		var rb: Basis = main.rig.global_transform.basis.orthonormalized()
		var d3: Vector3 = p - hp
		var br := rad_to_deg(atan2(d3.dot(rb.x), d3.dot(-rb.z)))
		out.append({"kind": str(v.get("kind")), "bearing": snappedf(br, 0.1), "dist": snappedf(Vector2(d3.x, d3.z).length(), 0.1),
				"head": _in_view(main.cams[0], p, main.CAM_FOV[0]), "wide": _in_view(main.cams[1], p, FOV_H)})
	return {"head_deg": snappedf(-rad_to_deg(main.head.rotation.y), 0.1), "mount": mount, "visitors": out}


func _in_view(cam: Camera3D, p: Vector3, fov_h: float) -> bool:
	var lp: Vector3 = cam.global_transform.affine_inverse() * p
	if lp.z > -0.3:
		return false
	var ah := rad_to_deg(atan2(absf(lp.x), -lp.z))
	var av := rad_to_deg(atan2(absf(lp.y), -lp.z))
	var fv := rad_to_deg(2.0 * atan(tan(deg_to_rad(fov_h) / 2.0) * 9.0 / 16.0))
	return ah < fov_h / 2.0 * 0.92 and av < fv / 2.0 * 0.95
