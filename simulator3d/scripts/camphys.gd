extends Node
## «Kamera-Physik» (Zweig real-kamera, 31.10.2026): the cameras like the real Raspberry Pi Camera Module 3 NoIR (Sony IMX708,
## rolling shutter, f/1.8, 66° × 41° = 75° diagonal, no IR-cut filter). A post effect on camfx.gdshader with a SMALL API, so
## other cameras (package «Weitwinkel-Kamera», later more) use the same physics with their own sensor / lens data.
##
## API (main.camphys):
##   set_spec(i, spec)          sensor / lens of camera i (Dictionary, missing keys from CM3_NOIR) - e.g. the wide package:
##                              main.camphys.set_spec(1, main.camphys.CM3_WIDE_NOIR)
##   spec(i) -> Dictionary      the data in use
##   apply(i, mat)              compute this camera's exposure and set all sensor uniforms of a camfx ShaderMaterial
##                              (before_capture(i) does it for main.camfx_mats[i]; a new camera calls it for its own material)
##   state(i) -> Dictionary     what the sensor does now: t_exp (s), gain (×), lux, under_ev, night, own_light, expo_k
##   expo_scale(i) -> float     brightness factor of the picture (1 = well exposed; < 1 = the sensor gets too little light)
##   active() -> bool           «Kamera wie echt» (realism.fx_on) - off: nothing here touches the picture
##   status() -> String         one line for the panel; control(d) for /control {"action": "camphys", "do": info | set}
## main._capture calls before_capture(i) LAST (after realism.gd, simreal.gd, weitwinkel.gd): this script has the final word on
## the sensor part of camfx (noise, exposure, blur strength, colours of the NoIR sensor, glow of bright lights).
##
## What it does:
##   - automatic exposure with the limits of the real camera: exposure time and analogue gain from the light at the scene
##     (lux), split like libcamera's AGC (first longer exposure, then more gain), never longer than one frame (≤ 1/10 s), gain
##     ≤ 16×; when that is not enough the picture gets darker (expo_scale) - at night without own light almost black
##   - sensor noise from the gain: luminance grain (1 px, the 1280 × 720 stream is scaled from the binned 2304 × 1296 mode)
##     and colour blotches (~2 px, what the colour denoise of the ISP leaves), a few fixed hot pixels at long exposure + high
##     gain; by day clean
##   - motion blur from the exposure time: «trail» = exposure / time since the last picture (moving things smear), «pan_blur»
##     = head turning during the exposure; rolling shutter skew from the readout time of the sensor (≈ 18 ms)
##   - NoIR colours: pink / magenta cast and light vegetation by day, the white balance follows a change of light slowly
##     (≈ 1.5 s); infrared picture nearly grey with a magenta touch, LED hot spot + stronger vignette; white light = colours
##   - lens: barrel distortion (simreal.gd «distort», from spec), residual vignette after the lens shading correction; at night
##     bright lights (headlights, torch, lamps) bloom and glow at high gain
## Settings (card «Kamerabild», part «Wie echt»): «Kamera wie echt» (real_fx, default on), expert: «Rauschen» (lens_noise),
## «Bewegungsunschärfe» (cam_blur), «NoIR-Farben» (cam_noir). Lite (Quality.lite()): noise per pixel (no blotches), no glow.
## Hook for the weather package (drops / dirt on the lens, lens.gdshader «drops», «dirt», «fogged»): state(i) tells exposure,
## gain and light, so drops can glow in the own light or vanish in the dark.

const Quality = preload("res://scripts/quality.gd")
const T = preload("res://scripts/i18n.gd")

var main
const FILE := "user://camphys.json"
const SAVE := ["blur_k", "noir_k"]
var blur_k := 1.0                  # «Bewegungsunschärfe» 0..2 (× the physical value)
var noir_k := 1.0                  # «NoIR-Farben» 0..1.5 (× the pink cast / light vegetation / magenta infrared)

# ---- datasheet values ------------------------------------------------------------------------------------------------
# Camera Module 3 product brief (Raspberry Pi Ltd, 2023): IMX708, 4608 × 2592, 1.4 µm, f/1.8, 66° × 41° (75° diagonal);
# Wide: f/2.2, 102° × 67° (120° diagonal). Analogue gain: libcamera cam_helper_imx708.cpp gain = 1024 / (1024 - code),
# code ≤ 960 → 16×. Readout of the binned 2304 × 1296 mode (56 fps): ≈ 18 ms top to bottom (rolling shutter).
# Exposure profile like libcamera's AGC (rpi tuning imx708_noir.json, «normal»: shutter 100 µs, 15, 30, 60 ms with gain
# 1, 1, 2, 4) - the last stage is the frame duration (MoveEye 200 sets FrameRate, so the exposure is never longer than one
# frame, at most 1/10 s) with the sensor maximum 16×.
const CM3_NOIR := {"name": "Camera Module 3 NoIR", "f": 1.8, "gain_max": 16.0, "t_max": 0.1, "readout": 0.018,
		"distort": 0.05, "vig": 0.12, "ir_vig": 0.35, "noir": 1.0, "read": 0.0025, "shot": 0.012}
const CM3_WIDE_NOIR := {"name": "Camera Module 3 Wide NoIR", "f": 2.2, "gain_max": 16.0, "t_max": 0.125, "readout": 0.018,
		"distort": 0.16, "vig": 0.2, "ir_vig": 0.45, "noir": 1.0, "read": 0.0025, "shot": 0.012}
const STAGE_T := [0.0001, 0.015, 0.03, 0.06]
const STAGE_G := [1.0, 1.0, 2.0, 4.0]
# Incident-light exposure equation E · t = C · N² / S (ISO 2720, C ≈ 250): f/1.8, gain 1 ≈ ISO 100 → 8.1 lx·s
# (f/2.2: × (2.2 / 1.8)²).
const K_EXPO := 8.1
# Light at the scene (lux) for main.light_level(): starlight 0.002, full moon 0.25, end of civil twilight 3.4,
# overcast / sunrise ~400, daylight 30000 (Wikipedia «Lux», «Twilight»). Interpolated in log10.
const LUX_TABLE := [[0.015, 0.002], [0.055, 0.25], [0.12, 3.4], [0.3, 400.0], [0.95, 30000.0]]
# 850 nm LED module (arm 2, PCA9685 ch 3): small 3 W modules are sold as «8-10 m». Here: at main.ir_range (default 10 m)
# the sensor gets what it needs at full exposure (1/10 s, 16×) minus 2 EV - the usable limit. Inverse square law.
# White LED (arm 1, ch 2): ~100 lm in a 60° cone ≈ 120 cd → 120 lx / d².
const WHITE_CD := 120.0
const UNDER_OK := 1.5              # EV the ISP still makes up with digital gain (the picture is noisy but not darker)

var specs: Array = [CM3_NOIR.duplicate(), CM3_WIDE_NOIR.duplicate()]
var t_exp := [0.004, 0.004]        # exposure time (s) per camera
var a_gain := [1.0, 1.0]           # analogue gain
var lux_m := [1000.0, 1000.0]      # light at the metered part of the scene
var under := [0.0, 0.0]            # EV the picture is darker than wanted (0 = well exposed)
var own := [false, false]          # the camera's own light (infrared / white LED) lights the scene
var ek := [1.0, 1.0]               # brightness factor applied to the picture (expo_scale)
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


# ---- API ------------------------------------------------------------------------------------------------------------------
func set_spec(i: int, s: Dictionary) -> void:
	"""sensor / lens of camera i; keys missing in s come from CM3_NOIR"""
	while specs.size() <= i:
		specs.append(CM3_NOIR.duplicate())
		for a in [t_exp, a_gain, lux_m, under, own, ek, _lh, _awb, _last]:
			a.append(a[0])
	var d: Dictionary = CM3_NOIR.duplicate()
	d.merge(s, true)
	specs[i] = d


func spec(i: int) -> Dictionary:
	return specs[clampi(i, 0, specs.size() - 1)]


func active() -> bool:
	return main.realism != null and main.realism.fx_on


func state(i: int) -> Dictionary:
	"""for other parts (weather: drops / dirt on the lens, the wide package): what the sensor does right now"""
	i = clampi(i, 0, specs.size() - 1)
	return {"t_exp": t_exp[i], "gain": a_gain[i], "lux": lux_m[i], "under_ev": under[i], "night": main.is_dark(),
			"own_light": own[i], "expo_k": ek[i], "spec": str(spec(i)["name"])}


func lens_state(i: int) -> Dictionary:     # the name of the first draft (kept for the weather package)
	return state(i)


func expo_scale(i: int) -> float:
	return float(ek[clampi(i, 0, ek.size() - 1)]) if active() else 1.0


func _lite() -> bool:
	return Quality.lite() or main.quality == "simple"


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
	var s := T.t("Kopfkamera: Belichtung %s · Verstärkung %.1f× · Licht %s", [ts, a_gain[0], _lux_txt(lux_m[0])])
	if under[0] > 0.7:
		s += T.t(" · %.1f Blenden zu dunkel", [under[0]])
	return s


static func _lux_txt(l: float) -> String:
	if l >= 100.0:
		return "%d lx" % int(round(l / 10.0) * 10.0)
	if l >= 1.0:
		return "%.0f lx" % l
	return "%.2f lx" % l


func control(d: Dictionary) -> Dictionary:
	"""control API {action: camphys, do: info | set (key: blur_k | noir_k, value)}"""
	if str(d.get("do", "info")) == "set" and str(d.get("key", "")) in SAVE:
		set(str(d["key"]), clampf(float(d.get("value", 1.0)), 0.0, 2.0))
		save()
	var cams := []
	for i in range(specs.size()):
		cams.append({"t_exp": snappedf(t_exp[i], 0.0001), "gain": snappedf(a_gain[i], 0.01), "lux": snappedf(lux_m[i], 0.001),
				"under_ev": snappedf(under[i], 0.01), "own_light": own[i], "expo_k": snappedf(ek[i], 0.001), "spec": spec(i)["name"]})
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


func _ir_lit(i: int) -> bool:
	if i == 0:
		return main.ir_on()
	return main.ir_on() or (main.weit != null and main.weit.has_method("ir_wide_on") and main.weit.ir_wide_on())


func _white_lit() -> bool:
	return main.white_light != null and main.white_light.light_energy > 0.05


func _scene_lux(i: int) -> float:
	var e: float = amb_lux(clampf(float(main.light_level()), 0.0, 1.0))
	own[i] = false
	if not main.is_dark():
		return e
	var d := _meter_dist(i)
	var o := 0.0
	var sp := spec(i)
	if _ir_lit(i):                                          # NoIR: the 850 nm light counts like visible light
		var r: float = maxf(2.0, float(main.ir_range))
		var i_ir: float = K_EXPO / (float(sp["t_max"]) * float(sp["gain_max"])) / 4.0 * r * r   # 2 EV under at the range
		o += i_ir * (1.0 if i == 0 else 0.6) / (d * d)
	if _white_lit() and i == 0:
		o += WHITE_CD / (d * d)
	own[i] = o > 0.0
	return e + o


func _split(h: float, tmax: float, gmax: float) -> Array:
	"""the wanted exposure (seconds × gain) into exposure time and gain, stage by stage like libcamera's AGC"""
	var st: Array = STAGE_T.duplicate()
	var sg: Array = STAGE_G.duplicate()
	st.append(tmax)
	sg.append(gmax)
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
	if i >= main.camfx_mats.size() or i >= specs.size():
		return
	apply(i, main.camfx_mats[i])
	if not active():
		return
	# the picture gets darker when the sensor cannot collect enough light (main sets «expo» fresh for every picture)
	for mats in [main.expo_mats, main.lens_mats]:
		if i < mats.size():
			var ex = mats[i].get_shader_parameter("expo")
			if ex != null:
				mats[i].set_shader_parameter("expo", float(ex) * float(ek[i]))
	# the 850 nm LED: 1/r² up to the range and a soft fade behind it (Godot's spot_range cuts the light off at the range;
	# the real light goes on, the camera just does not get enough of it - that is what expo / noise above do)
	if i == 0 and main.simreal != null and main.simreal.ir_real and main.ir_light != null:
		main.ir_light.spot_range = float(main.ir_range) * 1.6


func apply(i: int, m: ShaderMaterial) -> void:
	"""all sensor uniforms of a camfx material for camera i"""
	if m == null:
		return
	if not active():
		m.set_shader_parameter("sn_on", 0.0)
		m.set_shader_parameter("flare", 0.0)
		m.set_shader_parameter("ir_tint", 0.0)
		m.set_shader_parameter("vig", 0.0)
		ek[i] = 1.0
		return
	var sp := spec(i)
	var now_t: float = main.now()
	var dt: float = clampf(now_t - float(_last[i]), 0.02, 2.0)
	_last[i] = now_t
	var fps: float = float(main.CAM_FPS[i]) if i < main.CAM_FPS.size() else 10.0
	if main.simreal != null and main.simreal.pi_on and i == 0:
		fps = minf(fps, float(main.simreal.pi_fps))
	var tmax: float = minf(float(sp["t_max"]), 1.0 / maxf(1.0, fps))   # never longer than one frame
	var gmax: float = float(sp["gain_max"])
	# automatic exposure: wanted exposure from the light, smoothed in log (≈ 1 s to follow, like a real AGC)
	var lux: float = _scene_lux(i)
	lux_m[i] = lux
	var kf: float = K_EXPO * pow(float(sp["f"]) / 1.8, 2.0)
	var want: float = log(kf / maxf(lux, 0.00001)) / log(10.0)
	_lh[i] = lerpf(float(_lh[i]), want, 1.0 - exp(-dt / 0.6))
	var h: float = pow(10.0, float(_lh[i]))
	var spl: Array = _split(h, tmax, gmax)
	t_exp[i] = spl[0]
	a_gain[i] = clampf(spl[1], 1.0, gmax)
	under[i] = maxf(0.0, log(h / (t_exp[i] * a_gain[i])) / log(2.0))
	# brightness: only where no own light is on - the infrared / white picture already falls off with 1/r² in the render
	# and has its own exposure (main.ir_ex), so only the dark night without own light gets darker here
	var dark: bool = main.is_dark()
	ek[i] = 1.0 if own[i] or not dark else pow(2.0, -clampf(under[i] - UNDER_OK, 0.0, 6.0))
	var g: float = a_gain[i]
	var lite := _lite()
	# motion blur: what moved during the exposure smears. «trail» = share of the last picture: exposure / time since the
	# last picture (1/10 s of a walking person at 1.4 m/s = 14 cm); at most half (an average of the two pictures)
	var tr = m.get_shader_parameter("trail")
	if tr != null and float(tr) > 0.0:
		m.set_shader_parameter("trail", clampf(0.5 * t_exp[i] / dt * blur_k, 0.0, 0.5))
	if i == 0:
		var fov: float = deg_to_rad(float(main.CAM_FOV[0]))
		m.set_shader_parameter("pan_blur", Vector2(float(main.pan_vel) * t_exp[i] / fov, float(main.tilt_vel) * t_exp[i] / (fov * 9.0 / 16.0)) * blur_k)
		if main.simreal != null and main.simreal.lens_on and main.simreal.test_rs == 0.0:
			# rolling shutter: the rows are read one after the other in «readout» seconds - a turning head skews the picture
			m.set_shader_parameter("rshutter", clampf(-float(main.pan_vel) * float(sp["readout"]) / fov, -0.08, 0.08))
	else:
		var pb = m.get_shader_parameter("pan_blur")
		if pb is Vector2:
			m.set_shader_parameter("pan_blur", (pb as Vector2) * blur_k)
	if main.simreal != null and main.simreal.lens_on:
		var dist_now = m.get_shader_parameter("distort")
		if dist_now != null and float(dist_now) > 0.0:
			m.set_shader_parameter("distort", float(sp["distort"]))
	# noise: replaces the old light-only grain (simreal «shot», realism «cnoise», lens.gdshader «noise» - see main._update_lens)
	var nk: float = clampf(float(main.lens_noise) / 0.5, 0.0, 2.0) * (main.realism.noise_scale() if main.realism != null else 1.0)
	m.set_shader_parameter("shot", 0.0)
	m.set_shader_parameter("cnoise", 0.0)
	m.set_shader_parameter("sn_on", 1.0 if nk > 0.0 else 0.0)
	# the ISP's digital gain on top of the analogue gain amplifies the noise too
	# (up to UNDER_OK EV - beyond that the picture gets darker instead, see ek)
	var dg: float = pow(2.0, minf(under[i], UNDER_OK))
	m.set_shader_parameter("sn_read", float(sp["read"]) * g * sqrt(dg) * nk)     # read noise × gain (in the picture: dark parts)
	m.set_shader_parameter("sn_shot", float(sp["shot"]) * sqrt(g * dg) * nk)  # photon noise: grows with the square root
	m.set_shader_parameter("sn_chroma", (0.0 if g < 2.0 else 0.55 * smoothstep(2.0, 12.0, g)) * nk)
	m.set_shader_parameter("sn_blob", 0.0 if lite else 1.0)
	# hot pixels: dark current grows with exposure time and gain; the ISP removes most of them (defect pixel correction)
	m.set_shader_parameter("hotpx", clampf(g / gmax * t_exp[i] / float(sp["t_max"]), 0.0, 1.0) * 0.7 if g > 6.0 else 0.0)
	m.set_shader_parameter("seed", float(main.frame_no[i] % 997) * 3.1)
	# colours of the NoIR camera
	var grey: bool = dark and _ir_lit(i) and not (i == 0 and _white_lit())
	if i == 1 and main.weit != null and main.weit.has_method("grey"):
		grey = main.weit.grey(1)
	var nr = m.get_shader_parameter("noir")
	m.set_shader_parameter("noir", clampf((float(nr) if nr != null else 0.0) * float(sp["noir"]) * noir_k, 0.0, 1.0))
	m.set_shader_parameter("ir_tint", clampf(0.35 * noir_k, 0.0, 1.0) if grey else 0.0)   # 850 nm through the Bayer filter: grey, a magenta touch
	# lens shading: the ISP corrects most of it for daylight; in the light of the LED (brightest in the middle) more stays
	m.set_shader_parameter("vig", float(sp["ir_vig"]) if grey else float(sp["vig"]))
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
