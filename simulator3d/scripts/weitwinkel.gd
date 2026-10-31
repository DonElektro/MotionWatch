extends Node
## 3D-4.17 (Plan Daniel 30.10.2026, docs/Gehaeuse_Variante2_Weitwinkel.md «Simulator-Einbindung der Weitwinkel-Kamera"):
## the former «feste Kamera» (cams[1]) is now ONE wide-angle camera (Camera Module 3 Wide NoIR: 102° × 67°, 640×360, 8 fps,
## rendered only when somebody asks for it - main._wanted_fps / eco as before) with a mount:
##   case        P9 (31.10.2026): «Im Gehäuse (v5.2)» - exactly where case v5.2 holds it: front wall of the lower part (PIR
##               side = pan 0), fixed, lens 56 mm above the bottom of the case, 12° down; the head turns above it (default)
##   scene       on the mast 3 m beside the device (the old «feste Kamera»)
##   base        on the lower part of the device, under the head near the pan axis, looks ahead, tilted down (does not turn)
##   head_front  on the head, looks where the head camera looks (turns with the pan; tilt optional)
##   head_rear   on the head, looks back (yaw offset 180°)
##   none        P9: not built in - blind cover (part 12_Blindstopfen_Weitwinkel): no picture at all, /cam/1 answers 404
## On the head: only pan (stays level) or pan + tilt (tilt_follow). Tilt slider.
## P9 lens: «Fischauge» = the equidistant fisheye model of the case report (check52.py fov_rays: the angle from the middle
## grows linearly with the distance in the picture, 51° to the side edge, 33.5° to the top edge, ~61° = 122° diagonal in the
## corner). The camera renders a wider straight (rectilinear) picture, camfx.gdshader bends it (fe_*), a bit oversampled
## (OVERSAMPLE, not in Lite) so the middle stays sharp; + the dark corners the ISP leaves (fe_vig). Off = straight 102°.
## Second infrared LED (PCA9685 channel 4 at MoveEye, lights.ir_wide) as an IR spot at the mount: in the case a single
## 5 mm 850 nm LED (lights only the near field, ~4 m), at the other mounts the 120° module of the first plan (16 m).
## Head mounts: a pan limit (second flat cable; 360° servos would need a slip ring) and a slightly heavier head.
## /info cameras[1] and the reply to POST /state («wide») tell MoveEye the mount (part 163 sets «Übersicht lenkt den Kopf»).
## Hook for the camera physics (camphys.gd, branch real-kamera): sensor_info() - aperture, NoIR, installed - so the same
## sensor post-process (exposure, gain, noise) can run for i == 1 too; this file only does the optics (lens, vignetting).

const Quality := preload("res://scripts/quality.gd")
const FILE := "user://weitwinkel.json"
const SAVE := ["mount", "tilt", "tilt_follow", "fisheye", "pan_limit", "heavy"]
const MOUNTS := [["case", "Im Gehäuse (v5.2) – Stirnwand über dem PIR, fest, 12° nach unten"],
		["scene", "Mast (Szene) – 3 m neben dem Gerät"], ["base", "Unterteil vorne, fest (unter dem Kopf, dreht nicht)"],
		["head_front", "Kopf vorne (dreht mit)"], ["head_rear", "Kopf hinten (dreht mit, schaut zurück)"],
		["none", "Nicht verbaut (Blindstopfen) – kein Weitwinkel-Bild"]]
const FOV_H := 102.0
const FOV_V := 67.0
# ---- case v5.2 (Gehäuse-Modell v52.py / v5.py / pantilt.py, LIESMICH_Montage_v5-2.md) ---------------------------------
# lens: WC_LENS = (0.5, AY, 56.0) - 0.5 mm behind the inside of the front wall, centred, 56 mm above the bottom of the case;
# the pan axis is AX = 40 mm behind the inside of the front wall -> the lens is 39.5 mm in front of the pan axis.
# tilt axis: PAN_Z0 85.8 + AXZ 40.0 = 125.8 mm above the bottom -> the lens is 69.8 mm below the tilt axis (= main.head).
const CASE_FWD := 0.0395
const CASE_DOWN := 0.0698
const CASE_TILT := -12.0          # WC_TILT = 12° down
# 5 mm IR LED: IR_Y 26 / IR_Z 40 - 20 mm beside the lens (left of the PIR seen from the device), 16 mm below it, tip flush
# with the outside of the wall (2.5 mm wall + 0.5 mm) - separated by the wall, it does not shine into the window.
const CASE_IR := Vector3(-0.020, -0.016, -0.003)
# Lens: Camera Module 3 Wide product brief (Raspberry Pi Ltd, 2023): IMX708, f/2.2, 120° diagonal / 102° × 67°.
# Equidistant model as in the case report (check52.py): half angles 51° (to the side edge) and 33.5° (top / bottom edge).
const F_NUMBER := 2.2
const OVERSAMPLE := 1.5           # render 960 × 540 for the 640 × 360 picture (Lite: 1.0)
# Residual dark corners: libcamera's tuning file imx708_wide_noir.json corrects the lens shading only half for brightness
# («luminance_strength»: 0.5); the raw fall-off of the wide lens is not published - estimated ~45 % in the corner -> ~22 %
# darker corners in the picture. Estimate, compare with a real picture of the Wide as soon as it is built in.
const FE_VIG := 0.22
# The 5 mm 850 nm LED with ~120° (instead of the module with lens): about 50 mA (LIESMICH v5.2: 68 Ω at 5 V). Small 5 mm IR
# LEDs give a few mW/sr - single-LED cameras state 3-5 m. Here: inverse square law (Godot spot attenuation 2.0), usable to
# ~4 m, fades out at 7 m. Estimate, not measured.
const CASE_IR_RANGE := 7.0
const CASE_IR_ENERGY := 14.0

var main
var mount := "case"              # P9: the real device (case v5.2) - old saved setups keep theirs
var tilt := -12.0                 # degrees, - = down (base: 10-15° down; head: added to the head's tilt or to level)
var tilt_follow := false          # on the head: also tilts with the head (otherwise only pans and stays level)
var fisheye := true               # P9: the equidistant fisheye of the Wide (off = straight 102° picture)
var pan_limit := 170.0            # head mounts: the head turns at most ± this (cable)
var heavy := true                 # head mounts + «Servos wie echt»: the head is a bit slower (more load on the MG90S)
var ir_spot: SpotLight3D
var ir_ex := 0.5                  # exposure of the grey infrared picture of this camera (like main.ir_ex for the head camera)
var _sig := ""
var _proj := ""                   # P9: the projection that is set now (fisheye / straight, oversample)
var _quads: Array = []            # P9: [node, size] of the lens / exposure / effect quads in front of camera 1


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
		mount = "case"
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
	return not mount in ["scene", "none"]


func installed() -> bool:
	"""P9: false = blind cover (12_Blindstopfen_Weitwinkel) - no wide camera, no picture"""
	return mount != "none"


func in_case() -> bool:
	return mount == "case"


func on_head() -> bool:
	return mount == "head_front" or mount == "head_rear"


func tilt_deg() -> float:
	if mount == "case":
		return CASE_TILT
	return -10.0 if mount == "scene" else tilt


func yaw_offset() -> float:
	return 180.0 if mount == "head_rear" else 0.0


# ---- where the camera is -------------------------------------------------------------------------------------------
func place() -> void:
	"""every frame (main._process): the transform of cams[1] (+ the wide infrared spot)"""
	var cam: Camera3D = main.cams[1]
	if mount == "scene" or main.head == null:
		cam.global_transform = Transform3D(Basis.from_euler(Vector3(deg_to_rad(-10.0), -deg_to_rad(float(main.cam1_yaw)), 0)), Vector3(-3.0, 2.4, 3.0))
	elif mount == "case" or mount == "none":
		var rc: Basis = main.rig.global_transform.basis.orthonormalized()
		var pc: Vector3 = main.head.global_position + rc * Vector3(0, -CASE_DOWN, -CASE_FWD)
		cam.global_transform = Transform3D(rc * Basis.from_euler(Vector3(deg_to_rad(CASE_TILT), 0, 0)), pc)
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
	if mount == "case" or mount == "none":
		var rl: Basis = main.rig.global_transform.basis.orthonormalized()     # the LED sits straight in the wall (not tilted)
		ir_spot.global_transform = Transform3D(rl, cam.global_position + rl * CASE_IR)
		ir_spot.spot_range = CASE_IR_RANGE
		ir_spot.spot_attenuation = 2.0         # inverse square law
	else:
		ir_spot.global_transform = cam.global_transform.translated_local(Vector3(0, -0.03, 0))
		ir_spot.spot_range = 16.0
		ir_spot.spot_attenuation = 1.4
	_projection()


# ---- P9: the lens (equidistant fisheye) ----------------------------------------------------------------------------
func fe_half() -> Vector2:
	"""half angles of the picture (radians) of the equidistant model: to the side edge, to the top edge"""
	return Vector2(deg_to_rad(FOV_H / 2.0), deg_to_rad(FOV_V / 2.0))


func fe_render_tan() -> float:
	"""how wide the straight picture behind the fisheye must be (tan of its half width, 16:9): the rays of all edge pixels
	(the corners are the widest - 61° from the middle)"""
	var h := fe_half()
	var tx := 0.0
	var ty := 0.0
	for k in range(201):
		var sv := -1.0 + 2.0 * float(k) / 200.0
		for q in [Vector2(1.0, sv), Vector2(sv, 1.0)]:
			var a: Vector2 = q * h
			var th := a.length()
			if th < 0.0001:
				continue
			var t := tan(th)
			tx = maxf(tx, absf(t * a.x / th))
			ty = maxf(ty, absf(t * a.y / th))
	var aspect := float(main.CAM_W[1]) / float(main.CAM_H[1])
	return maxf(tx, ty * aspect) * 1.02


func oversample() -> float:
	return 1.0 if (Quality.lite() or not fisheye) else OVERSAMPLE


func _projection() -> void:
	"""the camera and the quads in front of it: fisheye = a wider straight picture (bent by camfx), else straight 102°"""
	var sig := "%s/%s" % [fisheye, oversample()]
	if sig == _proj or main.camfx_mats.size() < 2:
		return
	_proj = sig
	var cam: Camera3D = main.cams[1]
	if _quads.is_empty():
		for ch in cam.get_children():
			if ch is MeshInstance3D and (ch as MeshInstance3D).mesh is QuadMesh:
				_quads.append([ch, ((ch as MeshInstance3D).mesh as QuadMesh).size])
	var t0 := tan(deg_to_rad(float(main.CAM_FOV[1])) / 2.0)
	var t1 := fe_render_tan() if fisheye else t0
	cam.fov = rad_to_deg(2.0 * atan(t1))
	for q in _quads:
		((q[0] as MeshInstance3D).mesh as QuadMesh).size = (q[1] as Vector2) * (t1 / t0)
	var os := oversample()
	main.vps[1].size = Vector2i(int(round(main.CAM_W[1] * os)), int(round(main.CAM_H[1] * os)))
	var m: ShaderMaterial = main.camfx_mats[1]
	m.set_shader_parameter("fe_on", 1.0 if fisheye else 0.0)
	m.set_shader_parameter("fe_half", fe_half())
	m.set_shader_parameter("fe_tan", Vector2(t1, t1 * float(main.CAM_H[1]) / float(main.CAM_W[1])))
	m.set_shader_parameter("fe_vig", FE_VIG if fisheye else 0.0)
	print("wide camera: %s, render fov %.1f°, %d × %d" % ["fisheye (equidistant)" if fisheye else "straight", cam.fov, main.vps[1].size.x, main.vps[1].size.y])


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
	if not installed():
		return false                       # P9: blind cover - the LED hole has its stopper too (13_Stopfen_IR_LED)
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
		var e := CASE_IR_ENERGY if mount == "case" else 6.0
		ir_spot.light_energy = e if (i < 2 and ir_wide_on() and installed()) else 0.0   # the head camera (NoIR) sees the wide light too
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
		m.set_shader_parameter("distort", 0.0)       # P9: the lens is the equidistant fisheye (fe_*, _projection) - not the old barrel
		if mount == "case" and main.lens_mats.size() > 1:
			# the lens sits 3 mm deep behind the window under the rain lip (v5.2): drops reach it far less than an open lens
			var lm: ShaderMaterial = main.lens_mats[1]
			var dv = lm.get_shader_parameter("drops")
			lm.set_shader_parameter("drops", minf(float(dv) if dv != null else 0.0, 0.15 if main.cond.get("drops", false) else 0.05))
		if main.realism != null and main.realism.fx_on:
			m.set_shader_parameter("noir", 0.6 if (not dark) else 0.0)     # NoIR by day: a pink cast like the head camera
		if on_head():
			var fov: float = deg_to_rad(FOV_H)
			var te: float = main.realism.exposure_time() if main.realism != null else 0.02
			m.set_shader_parameter("pan_blur", Vector2(float(main.pan_vel) * te / fov, 0.0) if (main.realism != null and main.realism.fx_on) else Vector2.ZERO)


func after_capture(i: int, img: Image) -> void:
	if ir_spot != null:
		ir_spot.light_energy = 0.0
	if i == 1 and img != null and not img.is_empty() and img.get_width() != int(main.CAM_W[1]):
		img.resize(int(main.CAM_W[1]), int(main.CAM_H[1]), Image.INTERPOLATE_BILINEAR)   # P9: oversampled -> 640 × 360
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
			"fisheye": fisheye, "pan_limit": pan_limit if on_head() else null, "ir_wide": ir_wide_on(),
			"installed": installed(), "case": "v5.2" if in_case() else null, "lens": "equidistant" if fisheye else "rectilinear",
			"f_number": F_NUMBER}


func sensor_info() -> Dictionary:
	"""P9 hook for the camera physics (camphys.gd): what differs from the head camera, so the same sensor post-process can
	run for camera 1 - same IMX708 sensor, f/2.2 instead of f/1.8 (= (1.8/2.2)² ≈ 0.67 × the light), NoIR, and nothing at
	all when the blind cover is in. The optics (fisheye, dark corners) stay here."""
	return {"installed": installed(), "f_number": F_NUMBER, "light_k": pow(1.8 / F_NUMBER, 2.0), "noir": true, "sensor": "IMX708",
			"mount": mount, "fisheye": fisheye, "vignette": FE_VIG if fisheye else 0.0}


func state() -> Dictionary:
	"""a short form for the reply to POST /state: MoveEye sees a change of the mount at once"""
	return {"mount": mount, "tilt_deg": snappedf(tilt_deg(), 0.1), "yaw_offset": yaw_offset(), "pan_follow": on_head(),
			"tilt_follow": on_head() and tilt_follow, "on_head": on_head(), "fov_h": FOV_H, "fov_v": FOV_V,
			"pan_limit": pan_limit if on_head() else null, "installed": installed()}


# ---- settings (card «Kamerabild», part «Weitwinkel-Kamera») ---------------------------------------------------------
func add_controls() -> void:
	var m = main
	var sub := {"sub": "Weitwinkel-Kamera"}
	m.add_control("select", "wide_mount", "Weitwinkel-Kamera (Camera Module 3 Wide NoIR, 102° × 67°, 120° diagonal): Montage",
			func(): return mount, func(v): set_mount(str(v)), "Kamerabild", {"sub": "Weitwinkel-Kamera", "options": MOUNTS})
	m.add_control("slider", "wide_tilt", "Weitwinkel: Neigung (− = nach unten; Unterteil 10–15° nach unten; im Gehäuse v5.2 fest 12°)",
			func(): return tilt, func(v): _put("tilt", clampf(float(v), -40.0, 20.0)), "Kamerabild", {"sub": "Weitwinkel-Kamera", "min": -40, "max": 20, "step": 1, "unit": "°"})
	m.add_control("toggle", "wide_tilt_follow", "Weitwinkel auf dem Kopf: auch mitneigen (aus = nur mitschwenken, bleibt waagrecht)",
			func(): return tilt_follow, func(v): _put("tilt_follow", bool(v)), "Kamerabild", sub)
	m.add_control("toggle", "wide_fisheye", "Weitwinkel: Fischauge wie das Objektiv der Wide (gebogene Linien am Rand, dunklere Ecken)",
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
	if v == "none":
		main.jpgs[1] = PackedByteArray()          # the last picture must not stay: there is no camera
	save()
	print("wide camera: mount %s" % v)
	return true


func control(d: Dictionary) -> Dictionary:
	"""control API {action: weit, mount?, tilt?, tilt_follow?, fisheye?, pan_limit?, do: info | probe | spawn}"""
	if d.has("mount") and not set_mount(str(d["mount"])):
		return {"ok": false, "error": "unknown mount"}
	if d.has("tilt"):
		_put("tilt", clampf(float(d["tilt"]), -40.0, 20.0))
	for k in ["tilt_follow", "fisheye", "heavy"]:     # (fisheye: _projection() follows in the next place())
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
				"head": _in_view(main.cams[0], p, main.CAM_FOV[0]), "wide": installed() and _in_view(main.cams[1], p, FOV_H)})
	return {"head_deg": snappedf(-rad_to_deg(main.head.rotation.y), 0.1), "mount": mount, "visitors": out}


func _in_view(cam: Camera3D, p: Vector3, fov_h: float) -> bool:
	var lp: Vector3 = cam.global_transform.affine_inverse() * p
	if lp.z > -0.3:
		return false
	var ah := rad_to_deg(atan2(absf(lp.x), -lp.z))
	var av := rad_to_deg(atan2(absf(lp.y), -lp.z))
	var fv := rad_to_deg(2.0 * atan(tan(deg_to_rad(fov_h) / 2.0) * 9.0 / 16.0))
	return ah < fov_h / 2.0 * 0.92 and av < fv / 2.0 * 0.95
