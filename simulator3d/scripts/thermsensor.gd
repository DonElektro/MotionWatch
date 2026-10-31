extends Node
## «Wärmebild wie echt» – das Wärmebild-Modul wie das echte (Paket P2, 31.10.2026, Daniel).
## Echtes Gerät: Waveshare Thermal-90 (SKU 31941), Meridian MI48 «SenXor»: 80 × 62 Pixel, 90° × 67°, 8–14 µm, bis 25 Bilder/s
## (der Treiber von MoveEye stellt 15 ein, Teil 080), NETD 125 mK RMS bei 1 Hz, −40 … +400 °C, Genauigkeit ±1.5 °C
## (10 … 70 °C), Temperatur-Stabilität −0.21 °C pro °C Modul-Temperatur, OHNE Verschluss («shutterless»: kein Einfrieren,
## keine Klick-Kalibrierung). Quellen: Waveshare-Wiki «Thermal Camera HAT» und Datenblatt-Auszug bei Core Electronics
## (Thermal Imaging Camera 90° FOV 80×62), beide abgerufen am 31.10.2026.
## Was dieses Modell mit dem idealen Bild (main.decode_thermal_img: °C pro Pixel, die Luft dazwischen schon im Shader) macht:
##   1. Optik: ein Pixel sieht 1.1°, das kleine Objektiv verschmiert etwa ein Pixel (Punktbild ~1 px) – kleine warme Dinge
##      (Kerzenflamme, Igel weit weg) werden mit der Umgebung gemittelt
##   2. Wasser auf dem Sensorfenster bei Regen / Schnee: Wasser ist für 8–14 µm undurchsichtig – Tropfen auf dem Fenster sind
##      kalte, verschwommene Flecken, hinter denen nichts zu sehen ist (der eigentliche Grund, warum Regen das Wärmebild
##      blind macht; die Regentropfen in der Luft dämpfen kaum, waerme.gd air_k)
##   3. Rauschen: NETD 125 mK gilt bei 1 Bild/s, bei 15 Bildern/s ist das Einzelbild √15-mal so verrauscht; der Treiber von
##      MoveEye schaltet den zeitlichen Filter des Moduls ein (enable_filter f1 + f2) – hier ein gleitender Mittelwert
##      (α = 0.3 pro Modul-Bild: ~0.2 K Rauschen, bewegte Dinge ziehen ~0.2 s einen Schatten nach)
##   4. Muster des Sensors: jede Spalte und jedes Pixel ein wenig anders (±0.1 K), Rand ~0.4 K kühler (Genauigkeit Mitte
##      ±0.8 °C, ganzes Bild ±1.0 °C)
##   5. Drift: das Modul sitzt über dem warmen Pi – jede °C Modul-Temperatur über 25 °C verschiebt die Werte um −0.21 °C,
##      dazu ein Geräte-Fehler (±0.6 °C, fest) und ein langsames Wandern (±0.4 °C)
##   6. Verschluss-Kalibrierung (FFC): hat der Thermal-90 nicht – nur als Schalter für Module mit Verschluss (aus): alle paar
##      Minuten steht das Bild 0.4 s still, danach springt es leicht
##   7. Messbereich −40 … +400 °C, Auflösung 0.1 °C (der Treiber liefert Zehntel-Kelvin)
## Die Anzeige im Simulator: automatischer Bereich wie die Waveshare-App (1 … 99.5 %, sanft nachgeführt, mindestens 4 K),
## Farbpalette wählbar. MoveEye bekommt immer die °C-Werte (/thermal.bin) und macht seine eigene Skala.
## Lite (Raspberry Pi): keine Optik-Unschärfe und höchstens 8 Wärmebilder pro Sekunde (Quality.lite()).
## Einstellungen: user://thermsensor.json; der Hauptschalter «Wärmebild wie echt» ist simreal.th_real (gilt auch für P3).

const Waerme = preload("res://scripts/waerme.gd")
const Quality = preload("res://scripts/quality.gd")
const FILE := "user://thermsensor.json"
const SAVE := ["psf_on", "drops_on", "filter_on", "ffc_on", "ffc_every", "noise_k", "drift_k", "atm_x", "palette", "tent_person"]
const MODULE_FPS := 15.0           # so viele Bilder macht das Modul (Treiber von MoveEye, Teil 080: set_fps(15))
const ALPHA := 0.3                 # zeitlicher Filter des Moduls pro Modul-Bild (Annahme: f1 des MI48, Wert nicht veröffentlicht)
const T_MIN := -40.0
const T_MAX := 400.0
const LITE_FPS := 8.0
const PALETTES := [["inferno", "Inferno"], ["ironbow", "Ironbow (Eisen)"], ["white", "Weiss = warm"], ["black", "Schwarz = warm"]]

var main
var psf_on := true
var drops_on := true
var filter_on := true
var ffc_on := false
var ffc_every := 180.0
var noise_k := 1.0
var drift_k := 1.0
var atm_x := 1.0                   # Dämpfung durch Nebel / Schnee / Feuchte × (1 = Physik wie in waerme.gd)
var palette := "inferno"
var tent_person := true            # P3: nachts schläft jemand im eigenen Zelt (waerme_welt.gd)

var _state := PackedFloat32Array()
var _last := PackedFloat32Array()
var _last_t := 0.0
var _fpn := PackedFloat32Array()   # fester Pixel-Fehler + Spalten + Rand
var _unit := 0.0
var _walk := 0.0
var _case := -100.0                # Temperatur des Moduls (°C)
var _ffc_next := 0.0
var _ffc_until := 0.0
var _drops: Array = []             # [{x, y, r, life}]
var _lo := 0.0
var _hi := 0.0
var _lut := PackedColorArray()
var _lut_name := ""
var cost_us := 0.0                 # Rechenzeit pro Bild (gemittelt) - /control {"action": "thermsensor"}
var frames := 0


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
	ffc_every = clampf(ffc_every, 30.0, 900.0)
	noise_k = clampf(noise_k, 0.0, 4.0)
	drift_k = clampf(drift_k, 0.0, 4.0)
	atm_x = clampf(atm_x, 0.0, 5.0)
	var rng := RandomNumberGenerator.new()
	rng.seed = 31941                                   # immer dasselbe «Gerät» (Teilenummer des Moduls)
	_unit = rng.randf_range(-0.6, 0.6)


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


func on() -> bool:
	return main != null and main.simreal != null and main.simreal.th_real


func add_controls() -> void:
	"""Karte «Kamerabild» → «Wärmebild» (neben dem Modell und der warmen Hand von simint.gd)"""
	var m = main
	var g := "Kamerabild"
	var opts := []
	for p in PALETTES:
		opts.append([p[0], p[1]])
	m.add_control("select", "th_palette", "Farben des Wärmebilds (nur die Anzeige hier – MoveEye bekommt die °C-Werte)", func(): return palette,
			func(v): _put("palette", str(v)), g, {"sub": "Wärmebild", "options": opts})
	m.add_control("toggle", "th_tent_person", "Nachts schläft jemand im Zelt (schwacher warmer Fleck an der Zeltwand)", func(): return tent_person,
			func(v): _put("tent_person", bool(v)), g, {"sub": "Wärmebild"})
	m.add_control("button", "th_car_warm", "Geparktes Auto: Motor warm (eben angekommen, kühlt in 1–2 h ab)", null,
			func(): main.start_info = main.waerme_welt.car_arrived() if main.waerme_welt != null else "", g, {"sub": "Wärmebild"})
	m.add_control("button", "th_glass", "Glasscheibe vor MoveEye (Test: die Kamera sieht durch, das Wärmebild nicht) – nochmals drücken: weg", null,
			func(): main.start_info = main.waerme_welt.glass_pane() if main.waerme_welt != null else "", g, {"sub": "Wärmebild"})
	var X := {"sub": "Wärmebild", "expert": true}
	m.add_control("slider", "th_noise_k", "Rauschen des Sensors (1 = Datenblatt: 125 mK bei 1 Bild/s)", func(): return noise_k,
			func(v): _put("noise_k", float(v)), g, {"sub": "Wärmebild", "expert": true, "min": 0.0, "max": 4.0, "step": 0.25, "unit": "×"})
	m.add_control("slider", "th_drift_k", "Drift (Modul wird mit dem Pi warm, Geräte-Fehler, langsames Wandern)", func(): return drift_k,
			func(v): _put("drift_k", float(v)), g, {"sub": "Wärmebild", "expert": true, "min": 0.0, "max": 4.0, "step": 0.25, "unit": "×"})
	m.add_control("slider", "th_atm_x", "Nebel, Schnee und feuchte Luft schlucken Wärmestrahlung (1 = Physik)", func(): return atm_x,
			func(v): _put("atm_x", float(v)), g, {"sub": "Wärmebild", "expert": true, "min": 0.0, "max": 5.0, "step": 0.25, "unit": "×"})
	m.add_control("toggle", "th_psf", "Unschärfe des kleinen Objektivs (ca. 1 Pixel)", func(): return psf_on, func(v): _put("psf_on", bool(v)), g, X)
	m.add_control("toggle", "th_drops", "Wasser auf dem Sensorfenster bei Regen und Schnee (kalte Flecken, dahinter nichts)", func(): return drops_on,
			func(v): _put("drops_on", bool(v)); _drops.clear(), g, X)
	m.add_control("toggle", "th_filter", "Zeitlicher Filter des Moduls (wie der Treiber von MoveEye: weniger Rauschen, kurzer Nachzieh-Schatten)", func(): return filter_on,
			func(v): _put("filter_on", bool(v)), g, X)
	m.add_control("toggle", "th_ffc", "Verschluss-Kalibrierung (FFC) wie bei Modulen mit Verschluss – der Thermal-90 hat keinen", func(): return ffc_on,
			func(v): _put("ffc_on", bool(v)); _ffc_next = 0.0, g, X)
	m.add_control("slider", "th_ffc_s", "FFC alle", func(): return ffc_every, func(v): _put("ffc_every", float(v)), g,
			{"sub": "Wärmebild", "expert": true, "min": 30, "max": 900, "step": 30, "unit": "s"})


# ---- the air (uniforms of all thermal materials, see shaders/thermal_inc.gdshaderinc) ---------------------------------------------
func air_update() -> void:
	"""called with main._update_temps (twice a second): air temperature and how much the air swallows"""
	var k := 0.0
	if on():
		k = Waerme.air_k(str(main.weather), float(main.ambient), float(main.humidity), float(main.env.fog_density) if main.env != null else 0.0) * atm_x
	main.th_uniforms({"th_air": float(main.ambient), "th_atm_k": k})


func fps_cap(f: float) -> float:
	return minf(f, LITE_FPS) if Quality.lite() else f


# ---- the sensor --------------------------------------------------------------------------------------------------------
func process(a: PackedFloat32Array, w: int, h: int) -> PackedFloat32Array:
	var t0 := Time.get_ticks_usec()
	var t: float = main.now()
	var dt := t - _last_t
	_last_t = t
	var n := w * h
	if _fpn.size() != n:
		_make_fpn(w, h)
	if dt > 1.5 or dt <= 0.0 or _state.size() != n:
		_state = a.duplicate()                         # first picture / long pause: the filter starts again
		dt = 1.0 / MODULE_FPS
	# 6. FFC (only with the switch): the picture stands still for 0.4 s, then the wandering part of the drift is gone
	if ffc_on:
		if _ffc_next <= 0.0:
			_ffc_next = t + ffc_every * randf_range(0.8, 1.2)
		if t >= _ffc_next:
			_ffc_until = t + 0.4
			_ffc_next = t + ffc_every * randf_range(0.8, 1.2)
			_walk = randf_range(-0.15, 0.15)
		if t < _ffc_until and _last.size() == n:
			return _last
	# 1. optics: about one pixel blur (3 × 3, weights 1-2-1)
	if psf_on and not Quality.lite():
		a = _blur(a, w, h, 0.6)
	# 2. water on the window
	if drops_on:
		_drops_tick(dt, w, h)
		if not _drops.is_empty():
			a = _drops_apply(a, w, h)
	# 5. drift: the module gets warm with the Pi, a fixed error of this unit, a slow wandering
	var amb: float = main.ambient
	var pi_t: float = amb + 30.0
	if main.simwerte != null and main.simwerte.get("temp_c") != null:
		pi_t = float(main.simwerte.temp_c)
	var case_want := amb + 0.25 * maxf(0.0, pi_t - amb)
	if _case < -50.0:
		_case = case_want
	_case += (case_want - _case) * clampf(dt * maxf(1.0, float(main.speed)) / 600.0, 0.0, 1.0)   # housing: ~10 min
	_walk = clampf(_walk * (1.0 - dt / 900.0) + randfn(0.0, 0.015) * sqrt(dt), -0.4, 0.4)
	var off := (_unit - 0.21 * (_case - 25.0) + _walk) * drift_k
	# 3. noise + the time filter of the module (independent of how often the simulator takes a picture)
	var a_e := 1.0
	var sig_out: float = float(main.th_noise) * sqrt(MODULE_FPS) * noise_k     # th_noise = NETD of the model (simint.gd)
	if filter_on:
		a_e = 1.0 - pow(1.0 - ALPHA, clampf(dt * MODULE_FPS, 1.0, 30.0))
		sig_out *= sqrt(ALPHA / (2.0 - ALPHA))
	var sig_in := sig_out * sqrt((2.0 - a_e) / a_e)
	var out := PackedFloat32Array()
	out.resize(n)
	for i in range(n):
		var s: float = _state[i] + a_e * (a[i] + randfn(0.0, sig_in) - _state[i])
		_state[i] = s
		# 4. pattern of the sensor, 7. range and 0.1 °C steps
		out[i] = snappedf(clampf(s + _fpn[i] + off, T_MIN, T_MAX), 0.1)
	_last = out
	frames += 1
	cost_us += (float(Time.get_ticks_usec() - t0) - cost_us) * 0.1
	return out


func _make_fpn(w: int, h: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 3194131941
	var cols := PackedFloat32Array()
	for x in range(w):
		cols.append(rng.randf_range(-0.12, 0.12))
	_fpn.resize(w * h)
	var cx := (w - 1) * 0.5
	var cy := (h - 1) * 0.5
	for y in range(h):
		var dy := (y - cy) / cy
		for x in range(w):
			var dx := (x - cx) / cx
			_fpn[y * w + x] = cols[x] + rng.randfn(0.0, 0.06) - 0.4 * (dx * dx + dy * dy) * 0.5


func _blur(a: PackedFloat32Array, w: int, h: int, k: float) -> PackedFloat32Array:
	var tmp := PackedFloat32Array()
	tmp.resize(a.size())
	for y in range(h):
		var r := y * w
		for x in range(w):
			var l: float = a[r + maxi(x - 1, 0)]
			var rr: float = a[r + mini(x + 1, w - 1)]
			tmp[r + x] = (l + 2.0 * a[r + x] + rr) * 0.25
	var out := PackedFloat32Array()
	out.resize(a.size())
	for y in range(h):
		var u := maxi(y - 1, 0) * w
		var c := y * w
		var d := mini(y + 1, h - 1) * w
		for x in range(w):
			var b: float = (tmp[u + x] + 2.0 * tmp[c + x] + tmp[d + x]) * 0.25
			out[c + x] = a[c + x] + (b - a[c + x]) * k
	return out


func _drops_tick(dt: float, w: int, h: int) -> void:
	"""new drops while it rains / snows (wind blows more onto the window), old ones dry up in a few minutes"""
	var wet: String = str(main.weather)
	var rate := 0.0
	if wet == "rain":
		rate = 1.0 / 14.0 * (1.0 + clampf(float(main.wind) / 30.0, 0.0, 2.0))
	elif wet == "snow":
		rate = 1.0 / 40.0
	var sp := clampf(dt * maxf(1.0, float(main.speed)), 0.0, 30.0)
	if rate > 0.0 and _drops.size() < 9 and randf() < rate * sp:
		_drops.append({"x": randf_range(0.0, w), "y": randf_range(0.0, h * 0.9), "r": randf_range(2.5, 7.0), "life": 1.0})
	var keep := []
	for d in _drops:
		if rate <= 0.0:
			d["life"] = float(d["life"]) - sp / 240.0       # dries in ~4 min
		elif randf() < sp / 90.0:
			d["y"] = minf(float(d["y"]) + randf_range(1.0, 4.0), h + 8.0)   # now and then a drop runs down
		if float(d["life"]) > 0.0 and float(d["y"]) < h + 6.0:
			keep.append(d)
	_drops = keep


func _drops_apply(a: PackedFloat32Array, w: int, h: int) -> PackedFloat32Array:
	var tw: float = float(main.ambient) - 0.5                # the water on the window: about the air (a little cooler: evaporating)
	for d in _drops:
		var r: float = float(d["r"]) * clampf(float(d["life"]) * 1.3, 0.3, 1.0)
		var cx: float = d["x"]
		var cy: float = d["y"]
		var x0 := maxi(0, int(cx - 2.0 * r))
		var x1 := mini(w - 1, int(cx + 2.0 * r))
		var y0 := maxi(0, int(cy - 2.0 * r))
		var y1 := mini(h - 1, int(cy + 2.0 * r))
		for y in range(y0, y1 + 1):
			for x in range(x0, x1 + 1):
				var q := ((x - cx) * (x - cx) + (y - cy) * (y - cy)) / (r * r)
				if q < 4.0:
					var k := 0.93 * exp(-q * 1.2)
					var i := y * w + x
					a[i] = a[i] + (tw - a[i]) * k
	return a


# ---- the picture in the simulator (AGC + palette) ----------------------------------------------------------------------
func preview(vals: PackedFloat32Array, w: int, h: int) -> Image:
	var n := vals.size()
	var lo := 0.0
	var hi := 1.0
	if on():
		var s := vals.duplicate()
		s.sort()
		var l1: float = s[int(n * 0.01)]
		var h1: float = s[mini(n - 1, int(n * 0.995))]
		if h1 - l1 < 4.0:
			var mid := (h1 + l1) * 0.5
			l1 = mid - 2.0
			h1 = mid + 2.0
		if _hi <= _lo:
			_lo = l1
			_hi = h1
		_lo += (l1 - _lo) * 0.2                          # the range follows gently (like the app: no jumping)
		_hi += (h1 - _hi) * 0.2
		lo = _lo
		hi = _hi
	else:
		lo = 1e9
		hi = -1e9
		for v in vals:
			lo = minf(lo, v)
			hi = maxf(hi, v)
		hi = maxf(hi, lo + 2.0)
	var pal := palette if on() else "inferno"
	if _lut_name != pal:
		_make_lut(pal)
	var span := maxf(0.01, hi - lo)
	var data := PackedByteArray()
	data.resize(n * 3)
	for i in range(n):
		var c: Color = _lut[clampi(int((vals[i] - lo) / span * 255.0), 0, 255)]
		data[i * 3] = int(c.r * 255.0)
		data[i * 3 + 1] = int(c.g * 255.0)
		data[i * 3 + 2] = int(c.b * 255.0)
	return Image.create_from_data(w, h, false, Image.FORMAT_RGB8, data)


func _make_lut(name: String) -> void:
	var stops: Array
	match name:
		"ironbow":
			stops = [Color(0, 0, 0.05), Color(0.2, 0.0, 0.45), Color(0.6, 0.0, 0.55), Color(0.9, 0.25, 0.1), Color(1.0, 0.65, 0.0), Color(1.0, 0.95, 0.6), Color(1, 1, 1)]
		"white":
			stops = [Color(0, 0, 0), Color(1, 1, 1)]
		"black":
			stops = [Color(1, 1, 1), Color(0, 0, 0)]
		_:
			stops = [Color(0, 0, 0.02), Color(0.34, 0.06, 0.43), Color(0.73, 0.21, 0.33), Color(0.98, 0.55, 0.04), Color(0.99, 1.0, 0.64)]
	_lut = PackedColorArray()
	for i in range(256):
		var f := i / 255.0 * (stops.size() - 1)
		var j := mini(int(f), stops.size() - 2)
		_lut.append((stops[j] as Color).lerp(stops[j + 1], f - j))
	_lut_name = name


func info() -> Dictionary:
	return {"on": on(), "psf": psf_on, "drops": _drops.size(), "filter": filter_on, "ffc": ffc_on, "noise_k": noise_k, "drift_k": drift_k,
			"atm_x": atm_x, "case_c": snappedf(_case, 0.1), "offset_c": snappedf((_unit - 0.21 * (_case - 25.0) + _walk) * drift_k, 0.01),
			"agc": [snappedf(_lo, 0.1), snappedf(_hi, 0.1)], "palette": palette, "cost_ms": snappedf(cost_us / 1000.0, 0.01), "frames": frames,
			"lite": Quality.lite()}
