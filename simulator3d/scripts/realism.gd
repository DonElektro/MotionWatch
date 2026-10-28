extends Node
## 3D-3.94: the cameras like real ones - and like YOUR real one.
##  - camfx.gdshader on both cameras: motion blur from the exposure time (night: long), blur when the head turns, softness,
##    saturation / contrast / tint, the pink cast of the NoIR camera by day
##  - slower automatic exposure (1-2 s: headlights blind for a moment), JPEG quality like the camera module
##  - «Echt-Abgleich»: MoveEye 2.98.6 sends the look of its real pictures (brightness, contrast, colour, sharpness, grain -
##    day and night, from the diary and the alarm pictures); the simulator measures its own picture the same way every
##    few seconds and moves its settings towards it. Stored in user://echt_abgleich.json.
## Only picture data, no map data (rule of Daniel).

var main
var fx_on := true                  # camera effects (blur, colours, NoIR)
var real_on := true                # adjust to the real pictures of MoveEye
var servo_real := true             # servos with play and a little swinging after a stop
var jpg_q := 0.72                  # MJPEG of the camera module is not perfect either
const FILE := "user://echt_abgleich.json"
const DEF := {"ae": 0.35, "con": 1.0, "sat": 1.0, "tr": 1.0, "tb": 1.0, "soft": 0.3, "noise": 1.0}
var calib := {"day": DEF.duplicate(), "night": DEF.duplicate()}
var info := "noch keine echten Bilder von MoveEye"
var last_sim := {}
var _t := 0.0
var _prev: Array = [null, null]    # ImageTexture of the last picture per camera
var _dirty := false


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		for k in ["day", "night"]:
			if typeof(d.get(k)) == TYPE_DICTIONARY:
				for p in DEF:
					calib[k][p] = float(d[k].get(p, DEF[p]))
		fx_on = bool(d.get("fx_on", true))
		real_on = bool(d.get("real_on", true))
		servo_real = bool(d.get("servo_real", true))


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"day": calib["day"], "night": calib["night"], "fx_on": fx_on, "real_on": real_on, "servo_real": servo_real}))
		f.close()
	_dirty = false


func reset() -> void:
	calib = {"day": DEF.duplicate(), "night": DEF.duplicate()}
	save()
	info = "Abgleich zurückgesetzt"


func cur() -> Dictionary:
	return calib["night" if main.is_dark() else "day"]


func exposure_time() -> float:
	"""seconds the sensor collects light: short by day, long at night (that is what makes moving people blurry)"""
	var amb: float = clampf(main.light_level() if main.has_method("light_level") else (0.0 if main.is_dark() else 1.0), 0.0, 1.0)
	return lerpf(0.11, 0.004, amb)


func ae_target() -> float:
	return clampf(float(cur()["ae"]), 0.12, 0.6) if real_on else 0.35


func noise_scale() -> float:
	return clampf(float(cur()["noise"]), 0.3, 3.0) if (real_on and fx_on) else 1.0


func before_capture(i: int) -> void:
	"""the uniforms of the camera effect for this picture"""
	if i >= main.camfx_mats.size():
		return
	var m: ShaderMaterial = main.camfx_mats[i]
	var c: Dictionary = cur()
	if not fx_on:
		m.set_shader_parameter("trail", 0.0)
		m.set_shader_parameter("pan_blur", Vector2.ZERO)
		m.set_shader_parameter("soft", 0.0)
		m.set_shader_parameter("sat", 1.0)
		m.set_shader_parameter("con", 1.0)
		m.set_shader_parameter("tint", Vector3.ONE)
		m.set_shader_parameter("noir", 0.0)
		return
	var te := exposure_time()
	var fps: float = float(main.CAM_FPS[i]) if i < main.CAM_FPS.size() else 10.0
	m.set_shader_parameter("trail", clampf(te * fps * 0.9, 0.0, 0.55) if _prev[i] != null else 0.0)
	if _prev[i] != null:
		m.set_shader_parameter("prev_tex", _prev[i])
	var pb := Vector2.ZERO
	if i == 0:
		var fov: float = deg_to_rad(float(main.CAM_FOV[0]))
		pb = Vector2(float(main.pan_vel) * te / fov, float(main.tilt_vel) * te / (fov * 9.0 / 16.0))
	m.set_shader_parameter("pan_blur", pb)
	m.set_shader_parameter("soft", float(c["soft"]) if real_on else 0.3)
	m.set_shader_parameter("sat", float(c["sat"]) if real_on else 1.0)
	m.set_shader_parameter("con", float(c["con"]) if real_on else 1.0)
	m.set_shader_parameter("tint", Vector3(float(c["tr"]), 1.0, float(c["tb"])) if real_on else Vector3.ONE)
	var grey: bool = main.is_dark() and main.ir_on()
	m.set_shader_parameter("noir", 0.6 if (i == 0 and not grey and not main.is_dark()) else 0.0)


func after_capture(i: int, img: Image) -> void:
	"""keep the picture for the motion blur of the next one; now and then: compare with the real look"""
	if not fx_on or img == null or img.is_empty():
		return
	if _prev[i] == null:
		_prev[i] = ImageTexture.create_from_image(img)
	else:
		(_prev[i] as ImageTexture).update(img)
	if i != 0:
		return
	_t -= 1.0 / maxf(1.0, float(main.CAM_FPS[0]))
	if _t > 0.0:
		return
	_t = 8.0
	var tg = main.mw.get("real_look", null) if main.now() - main.mw_t < 5.0 else null
	if typeof(tg) != TYPE_DICTIONARY:
		info = "wartet auf MoveEye (ab 2.98.6) mit echten Bildern" if main.now() - main.mw_t >= 5.0 else "MoveEye hat noch keine echten Bilder (Tagebuch, Alarmbilder)"
		return
	var key := "night" if main.is_dark() else "day"
	var t = tg.get(key, null)
	if typeof(t) != TYPE_DICTIONARY or int(t.get("n", 0)) < 3:
		info = "zu wenige echte %s-Bilder (%d)" % ["Nacht" if key == "night" else "Tag", int((t if typeof(t) == TYPE_DICTIONARY else {}).get("n", 0))]
		return
	var s := stats(img)
	last_sim = s
	if not real_on or float(s["mean"]) < 0.03:
		return
	var c: Dictionary = calib[key]
	c["ae"] = lerpf(float(c["ae"]), clampf(float(t["mean"]), 0.12, 0.6), 0.3)
	c["con"] = clampf(float(c["con"]) * pow((float(t["std"]) + 0.01) / (float(s["std"]) + 0.01), 0.35), 0.6, 1.6)
	c["sat"] = clampf(float(c["sat"]) * pow((float(t["sat"]) + 0.01) / (float(s["sat"]) + 0.01), 0.45), 0.2, 1.8)
	c["tr"] = clampf(float(c["tr"]) * pow(float(t["r"]) / maxf(0.05, float(s["r"])), 0.45), 0.7, 1.4)
	c["tb"] = clampf(float(c["tb"]) * pow(float(t["b"]) / maxf(0.05, float(s["b"])), 0.45), 0.7, 1.4)
	if float(s["sharp"]) > float(t["sharp"]) * 1.1:
		c["soft"] = minf(2.0, float(c["soft"]) + 0.12)
	elif float(s["sharp"]) < float(t["sharp"]) * 0.9:
		c["soft"] = maxf(0.0, float(c["soft"]) - 0.12)
	c["noise"] = clampf(float(c["noise"]) * pow((float(t["noise"]) + 0.002) / (float(s["noise"]) + 0.002), 0.4), 0.3, 3.0)
	info = "%s: angeglichen an %d echte Bilder · Helligkeit %.2f/%.2f · Farbe %.2f/%.2f" % ["Nacht" if key == "night" else "Tag", int(t["n"]),
			float(s["mean"]), float(t["mean"]), float(s["sat"]), float(t["sat"])]
	save()


static func stats(img: Image) -> Dictionary:
	"""the look of a picture - the same measure as MoveEye (146_echt_abgleich.py): 160 x 90, brightness, contrast,
	saturation, red and blue relative to green, sharpness (edges), grain (difference to the neighbours)"""
	var s: Image = img.duplicate()
	if s.get_format() != Image.FORMAT_RGB8:
		s.convert(Image.FORMAT_RGB8)
	s.resize(160, 90, Image.INTERPOLATE_BILINEAR)
	var d := s.get_data()
	var n := 160 * 90
	var L := PackedFloat32Array()
	L.resize(n)
	var sr := 0.0
	var sg := 0.0
	var sb := 0.0
	var sl := 0.0
	var sl2 := 0.0
	var ss := 0.0
	for p in range(n):
		var r := d[p * 3] / 255.0
		var g := d[p * 3 + 1] / 255.0
		var b := d[p * 3 + 2] / 255.0
		var l := 0.299 * r + 0.587 * g + 0.114 * b
		L[p] = l
		sr += r
		sg += g
		sb += b
		sl += l
		sl2 += l * l
		ss += maxf(r, maxf(g, b)) - minf(r, minf(g, b))
	var mean := sl / n
	var sharp := 0.0
	var noise := 0.0
	var m := 0
	for y in range(1, 89):
		for x in range(1, 159):
			var p := y * 160 + x
			sharp += absf(L[p] - L[p - 1])
			noise += absf(L[p] - (L[p - 1] + L[p + 1] + L[p - 160] + L[p + 160]) * 0.25)
			m += 1
	return {"mean": mean, "std": sqrt(maxf(0.0, sl2 / n - mean * mean)), "sat": ss / n, "r": sr / maxf(0.001, sg), "b": sb / maxf(0.001, sg),
			"sharp": sharp / m, "noise": noise / m}
