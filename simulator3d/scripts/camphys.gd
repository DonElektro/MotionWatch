extends Node
## 3D-4.x «Kamera-Physik» (P1, 31.10.2026): the head camera like the real Raspberry Pi Camera Module 3 NoIR (Sony IMX708).
## main._capture calls before_capture(i) LAST (after realism.gd, simreal.gd, weitwinkel.gd) - this script has the final word
## on the sensor part of camfx.gdshader:
##   - automatic exposure with the limits of the real camera: exposure time and analogue gain from the light at the scene
##     (lux), split like libcamera's AGC (first longer exposure, then more gain), at most one frame long (≤ 1/10 s) and 16×
##   - sensor noise from the gain: luminance grain (1 px, like the 1280 × 720 stream scaled from the binned 2304 × 1296 mode)
##     and colour blotches (~2 px, what the colour denoise of the ISP leaves), a few hot pixels at long exposure + high gain;
##     by day clean
##   - motion blur from the exposure time (realism.gd's «trail» = share of the last picture, «pan_blur» = head turning)
##   - NoIR colours: pink / magenta cast and light vegetation by day (no IR-cut filter), the white balance follows changes of
##     the light only slowly (≈ 1.5 s), the infrared picture slightly magenta instead of pure grey
##   - at night bright lights (headlights, torches, lamps) bloom and glow at high gain
## Every number with its source below. Switch: «Kamera wie echt» (realism.fx_on, also what the test bench's --realismus aus
## turns off); sliders «Rauschen» (main.lens_noise), «Bewegungsunschärfe», «NoIR-Farben» (Kamerabild → Wie echt).
## Lite: _lite() - cheap noise only (no colour blotches, no glow). The coordinator joins it with the Lite package.
## Hook for the weather package (dirt, drops on the lens): lens.gdshader already has «drops», «dirt», «fogged»;
## lens_state(i) gives exposure / gain / light so drops and dirt can glow in headlights or vanish in the dark.

var main
const FILE := "user://camphys.json"
const SAVE := ["blur_k", "noir_k"]
var blur_k := 1.0                  # «Bewegungsunschärfe» 0..2 (× the physical value)
var noir_k := 1.0                  # «NoIR-Farben» 0..1.5 (× the pink cast / light vegetation)

# ---- datasheet values ------------------------------------------------------------------------------------------------
# Camera Module 3 product brief (Raspberry Pi Ltd, 2023): IMX708, 4608 × 2592, 1.4 µm, f/1.8, 66° × 41° (75° diagonal).
# Analogue gain: libcamera cam_helper_imx708.cpp gain = 1024 / (1024 - code), code ≤ 960 → 16×.
const AGAIN_MAX := 16.0
# Exposure profile like libcamera's AGC (rpi tuning imx708_noir.json, «normal»: shutter 100 µs, 15, 30, 60, 120 ms with
# gain 1, 1, 2, 4, 6) - here the last stage is the frame duration (MoveEye 200 sets FrameRate, so the exposure can never
# be longer than one frame, at most 1/10 s) and the sensor maximum 16× (night).
const STAGE_T := [0.0001, 0.015, 0.03, 0.06]
const STAGE_G := [1.0, 1.0, 2.0, 4.0]
const T_MAX := 0.1                 # 1/10 s
# Incident-light exposure equation E · t = C · N² / S (ISO 2720, C ≈ 250): f/1.8, gain 1 ≈ ISO 100 → 8.1 lx·s.
const K_EXPO := 8.1
# Light at the scene (lux) for main.light_level(): starlight 0.002, full moon 0.25, end of civil twilight 3.4,
# overcast / sunrise ~400, daylight 30000 (Wikipedia «Lux», «Twilight»). Interpolated in log10.
const LUX_TABLE := [[0.015, 0.002], [0.055, 0.25], [0.12, 3.4], [0.3, 400.0], [0.95, 30000.0]]
# 850 nm LED module (arm 2, PCA9685 ch 3): small 3 W modules are sold as «8-10 m». Here: at main.ir_range (default 10 m)
# the sensor gets exactly what it needs at full exposure (1/10 s, 16×) minus 2 EV - the usable limit. Inverse square law.
# White LED (arm 1, ch 2): ~100 lm in a 60° cone ≈ 120 cd → 120 lx / d².
const WHITE_CD := 120.0

var t_exp := [0.004, 0.004]        # exposure time (s) per camera
var a_gain := [1.0, 1.0]           # analogue gain
var lux_m := [1000.0, 1000.0]      # light at the metered part of the scene
var under := [0.0, 0.0]            # EV the picture is darker than wanted (0 = well exposed)
var _lh := [-2.0, -2.0]            # log10 of the wanted exposure (smoothed: the AE needs ~1 s)
var _awb: Array = [Vector3.ONE, Vector3.ONE]
var _last := [0.0, 0.0]


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		blur_k = clampf(float(d.get("blur_k", 1.0)), 0.0, 2.0)
		noir_k = clampf(float(d.get("noir_k", 1.0)), 0.0, 1.5)


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"blur_k": blur_k, "noir_k": noir_k}))
		f.close()


func _lite() -> bool:
	"""the light graphics (Pi / weak PC): until the Lite package brings Quality.lite(), our own check + the old «simple»"""
	return (Engine.has_meta("lite") and bool(Engine.get_meta("lite"))) or main.quality == "simple"


func active() -> bool:
	return main.realism != null and main.realism.fx_on


func add_controls() -> void:
	main.add_control("slider", "cam_blur", "Bewegungsunschärfe (aus der Belichtungszeit: nachts bis 1/10 s)", func(): return blur_k,
			func(v): blur_k = float(v); save(), "Kamerabild", {"sub": "Wie echt", "min": 0.0, "max": 2.0, "step": 0.1, "unit": "×", "expert": true})
	main.add_control("slider", "cam_noir", "NoIR-Farben (ohne Infrarot-Filter: Rosastich am Tag, helle Pflanzen)", func(): return noir_k,
			func(v): noir_k = float(v); save(), "Kamerabild", {"sub": "Wie echt", "min": 0.0, "max": 1.5, "step": 0.1, "unit": "×", "expert": true})


func status() -> String:
	"""one line for the panel (Kamerabild → Wie echt)"""
	if not active():
		return ""
	var t: float = t_exp[0]
	var ts := ("1/%d s" % int(round(1.0 / t))) if t < 0.5 else ("%.1f s" % t)
	var s := "Kopfkamera: Belichtung %s · Verstärkung %.1f× · Licht %s" % [ts, a_gain[0], _lux_txt(lux_m[0])]
	if under[0] > 0.7:
		s += " · %.1f Blenden zu dunkel" % under[0]
	return s


static func _lux_txt(l: float) -> String:
	if l >= 100.0:
		return "%d lx" % int(round(l / 10.0) * 10.0)
	if l >= 1.0:
		return "%.0f lx" % l
	return "%.2f lx" % l


func lens_state(i: int) -> Dictionary:
	"""for other parts (weather: drops / dirt on the lens): what the sensor does right now"""
	i = clampi(i, 0, 1)
	return {"t_exp": t_exp[i], "gain": a_gain[i], "lux": lux_m[i], "under_ev": under[i], "night": main.is_dark()}


func control(d: Dictionary) -> Dictionary:
	"""control API {action: camphys, do: info | set (key, value)}"""
	if str(d.get("do", "info")) == "set" and str(d.get("key", "")) in SAVE:
		set(str(d["key"]), float(d.get("value", 1.0)))
		save()
	var cams := []
	for i in range(2):
		cams.append({"t_exp": snappedf(t_exp[i], 0.0001), "gain": snappedf(a_gain[i], 0.01), "lux": snappedf(lux_m[i], 0.001), "under_ev": snappedf(under[i], 0.01)})
	return {"ok": true, "active": active(), "lite": _lite(), "blur_k": blur_k, "noir_k": noir_k, "cams": cams, "status": status()}


# ---- the light at the scene ---------------------------------------------------------------------------------------------
static func amb_lux(ll: float) -> float:
	if ll <= LUX_TABLE[0][0]:
		return LUX_TABLE[0][1]
	for k in range(1, LUX_TABLE.size()):
		if ll <= LUX_TABLE[k][0]:
			var a: Array = LUX_TABLE[k - 1]
			var b: Array = LUX_TABLE[k]
			var f: float = (ll - a[0]) / (b[0] - a[0])
			return pow(10.0, lerpf(log(a[1]) / log(10.0), log(b[1]) / log(10.0), f))
	return LUX_TABLE[-1][1]


func _meter_dist(i: int) -> float:
	"""how far the middle of the picture is (centre-weighted metering): the ground along the view, or a visitor close to
	the middle (a person walking up to the camera in the infrared light gets brighter - the AE turns the gain down)"""
	var cam: Camera3D = main.cams[i]
	var p: Vector3 = cam.global_position
	var fwd: Vector3 = -cam.global_transform.basis.z
	var hgt: float = maxf(0.3, p.y - float(main.ground_y(p.x, p.z)))
	var d: float = 30.0 if fwd.y > -0.03 else clampf(hgt / -fwd.y, 1.0, 30.0)
	if main.visitors != null:
		for v in main.visitors.get_children():
			if not (v is Node3D):
				continue
			var q: Vector3 = (v as Node3D).global_position + Vector3(0, 1.0, 0) - p
			var l := q.length()
			if l < d and l > 0.3 and fwd.dot(q / l) > 0.94:      # within ~20° of the middle
				d = lerpf(d, l, 0.6)
	return d


func _scene_lux(i: int) -> float:
	var e: float = amb_lux(clampf(float(main.light_level()), 0.0, 1.0))
	if not main.is_dark():
		return e
	var d := _meter_dist(i)
	var own := 0.0
	var ir: bool = main.ir_on() or (i == 1 and main.weit != null and main.weit.has_method("ir_wide_on") and main.weit.ir_wide_on())
	if ir:                                                  # NoIR: the 850 nm light counts like visible light
		var r: float = maxf(2.0, float(main.ir_range))
		var i_ir: float = K_EXPO / (T_MAX * AGAIN_MAX) / 4.0 * r * r   # 2 EV under at the end of the range (see above)
		var cone := 1.0 if i == 0 else 0.6
		own += i_ir * cone / (d * d)
	if main.white_light != null and main.white_light.light_energy > 0.05:
		own += WHITE_CD / (d * d)
	return e + own


func _split(h: float, tmax: float) -> Array:
	"""the wanted exposure (seconds × gain) into exposure time and gain, stage by stage like libcamera's AGC"""
	var st: Array = STAGE_T.duplicate()
	var sg: Array = STAGE_G.duplicate()
	st.append(tmax)
	sg.append(AGAIN_MAX)
	if h <= st[0] * sg[0]:
		return [maxf(h, 0.00002), 1.0]
	var t: float = st[0]
	var g: float = sg[0]
	for k in range(1, st.size()):
		var tk: float = minf(st[k], tmax)
		if tk * g >= h:
			return [h / g, g]
		if tk * sg[k] >= h:
			return [tk, h / tk]
		t = tk
		g = sg[k]
	return [t, g]


# ---- per picture ----------------------------------------------------------------------------------------------------------
func before_capture(i: int) -> void:
	if i > 1 or i >= main.camfx_mats.size():
		return
	var m: ShaderMaterial = main.camfx_mats[i]
	if not active():
		m.set_shader_parameter("sn_on", 0.0)
		m.set_shader_parameter("flare", 0.0)
		return
	var now_t: float = main.now()
	var dt: float = clampf(now_t - float(_last[i]), 0.02, 2.0)
	_last[i] = now_t
	var fps: float = float(main.CAM_FPS[i]) if i < main.CAM_FPS.size() else 10.0
	if main.simreal != null and main.simreal.pi_on and i == 0:
		fps = minf(fps, float(main.simreal.pi_fps))
	var tmax: float = minf(T_MAX, 1.0 / maxf(1.0, fps))   # never longer than one frame
	# automatic exposure: wanted exposure from the light, smoothed in log (≈ 1 s to follow, like a real AGC)
	var lux: float = _scene_lux(i)
	lux_m[i] = lux
	var want: float = log(K_EXPO / maxf(lux, 0.00001)) / log(10.0)
	_lh[i] = lerpf(float(_lh[i]), want, 1.0 - exp(-dt / 0.6))
	var h: float = pow(10.0, float(_lh[i]))
	var sp: Array = _split(h, tmax)
	t_exp[i] = sp[0]
	a_gain[i] = clampf(sp[1], 1.0, AGAIN_MAX)
	under[i] = maxf(0.0, log(h / (t_exp[i] * a_gain[i])) / log(2.0))
	var g: float = a_gain[i]
	var lite := _lite()
	# motion blur: realism.gd set «trail» (share of the last picture) and «pan_blur» from realism.exposure_time(), which now
	# comes from here - only the slider on top. The blur is the exposure time × the speed: 1/10 s of a walking person
	# (1.4 m/s) at 5 m = 14 cm.
	var tr = m.get_shader_parameter("trail")
	if tr != null and float(tr) > 0.0:
		m.set_shader_parameter("trail", clampf(t_exp[i] * fps * 0.9 * blur_k, 0.0, 0.7))
	var pb = m.get_shader_parameter("pan_blur")
	if pb is Vector2:
		var pbv: Vector2 = pb
		m.set_shader_parameter("pan_blur", pbv * blur_k)
	# noise: replaces the old light-only grain (simreal «shot», realism «cnoise», lens.gdshader «noise» - see main._update_lens)
	var nk: float = clampf(float(main.lens_noise) / 0.5, 0.0, 2.0) * (main.realism.noise_scale() if main.realism != null else 1.0)
	m.set_shader_parameter("shot", 0.0)
	m.set_shader_parameter("cnoise", 0.0)
	m.set_shader_parameter("sn_on", 1.0)
	m.set_shader_parameter("sn_read", 0.0035 * g * nk)          # read noise × gain (in the picture: dark parts)
	m.set_shader_parameter("sn_shot", 0.012 * sqrt(g) * nk)     # photon noise: grows with the square root of the signal
	m.set_shader_parameter("sn_chroma", (0.0 if g < 2.0 else 0.55 * smoothstep(2.0, 12.0, g)) * nk)
	m.set_shader_parameter("sn_blob", 0.0 if lite else 1.0)
	# hot pixels: dark current grows with exposure time and gain; the ISP removes most of them (defect pixel correction)
	m.set_shader_parameter("hotpx", clampf(g / AGAIN_MAX * t_exp[i] / T_MAX, 0.0, 1.0) * 0.7 if g > 6.0 else 0.0)
	m.set_shader_parameter("seed", float(main.frame_no[i] % 997) * 3.1)
	# colours of the NoIR camera
	var dark: bool = main.is_dark()
	var grey: bool = dark and (main.ir_on() if i == 0 else (main.weit != null and main.weit.has_method("grey") and main.weit.grey(1))) \
			and not main.white_light.light_energy > 0.0
	var nr = m.get_shader_parameter("noir")
	m.set_shader_parameter("noir", clampf((float(nr) if nr != null else 0.0) * noir_k, 0.0, 1.0))
	m.set_shader_parameter("ir_tint", 0.35 * noir_k if grey else 0.0)    # 850 nm through the Bayer filter: grey with a magenta touch
	# white balance: follows a change of the light (white LED on, lamp, dusk) in ≈ 1.5 s, not at once
	var tn = m.get_shader_parameter("tint")
	var target: Vector3 = tn if tn is Vector3 else Vector3.ONE
	var a := 1.0 - exp(-dt / 1.5)
	_awb[i] = (_awb[i] as Vector3).lerp(target, a)
	if (_awb[i] as Vector3).distance_to(target) > 0.6:
		_awb[i] = target
	m.set_shader_parameter("tint", _awb[i])
	# glow of bright lights at night (headlights, torch, lamps): the more gain, the more they blow out
	var fl := 0.0
	if dark and not lite:
		fl = smoothstep(2.0, 16.0, g) * 0.9 + (0.25 if grey else 0.0)
	m.set_shader_parameter("flare", fl)
