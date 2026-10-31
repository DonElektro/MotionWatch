extends Node
## Paket «Wetter physikalisch» (Zweig real-wetter, Wunsch Daniel 31.10.2026): das Wetter, das es schon gab (Regen, Nebel,
## Schnee, Gewitter, Wind, Tropfen / Beschlag auf der Linse), näher an der Physik - und so, dass MoveEye es im Kamerabild
## wirklich sieht.
##  - Regenstärke (Niesel … Wolkenbruch, mm/h): Tropfengrösse und Fallgeschwindigkeit (Gunn-Kinzer), Menge, schräg im Wind,
##    Spritzer, Sichtweite, Lärm am Mikrofon, wie schnell der Boden nass wird und Pfützen entstehen. Gleiche Regler für Schnee.
##  - Regen im Kamerabild: die Regenstriche waren durchsichtig gezeichnet und fehlten darum in den Bildern für MoveEye
##    (camfx.gdshader liest das Bild vor den durchsichtigen Dingen). Jetzt «Alpha-Hash» (gerastert) - sie sind im Bild.
##  - Tropfen und Beschlag auf der Linse: linse.gd (eigenes Overlay, eigene Schnittstelle) statt der festen Flecken im
##    lens.gdshader. Linsentemperatur folgt der Luft träge, kühlt in klaren Nächten ab; unter dem Taupunkt beschlägt sie.
##  - Nebel mit Sichtweite in Metern (Koschmieder: Dichte = 3.912 / Sichtweite), zieht in Schwaden mit dem Wind,
##    Bodennebel als eigene Schicht im Kamerabild (bodennebel.gdshader, Tiefe pro Bildpunkt).
##  - Schnee bleibt liegen: Schneehöhe wächst beim Schneien (1 mm Wasser ≈ 1 cm Schnee), schmilzt über 0 °C, bei Regen und
##    in der Sonne schneller. Spuren im Schnee: umgebung.gd (u_tracks) nimmt jetzt die liegende Schneedecke.
##  - Wind: Zeltplanen beulen und flattern (Zeltwände), Wäsche und Fahnen ohne Ruckeln (Takt aus dem Wind aufsummiert
##    statt TIME × Wind - bei jeder Böe sprang die Welle vorher). Gras / Bäume macht ein anderes Paket.
##  - Gewitter: der Blitz ist als Strahl am Himmel zu sehen (wenn er im Bild ist), Knopf «Blitz jetzt», Zeiten der Blitze
##    für den Testlauf (Fehlalarm-Ursache «Blitz»), Prüfstand-Plan «wetter».
## Einstellungen in user://wetter.json. Test-Aktion {"action": "wetter", "do": info | set | flash | wipe | splash | fog |
## snow | morning}. Lite (Quality.lite()): weniger Regen / Tropfen, Bodennebel ohne Flecken.

var main
const FILE := "user://wetter.json"
const Linse = preload("res://scripts/linse.gd")
const Quality = preload("res://scripts/quality.gd")
const T = preload("res://scripts/i18n.gd")
# Stufe, Text, mm/h (Wasser), Teilchen Regen, Teilchen Schnee, Spritzer
const RAIN := [["niesel", "Nieselregen (0,5 mm/h)", 0.5, 1800, 1500, 150], ["leicht", "leicht (2 mm/h)", 2.0, 2000, 2200, 380],
		["mittel", "mittel (8 mm/h, wie bisher)", 8.0, 2500, 3000, 700], ["stark", "stark (25 mm/h)", 25.0, 4000, 4500, 1100],
		["wolkenbruch", "Wolkenbruch (60 mm/h)", 60.0, 6000, 6000, 1600]]
const SAVE := ["w_rain", "w_vis", "w_drift", "w_ground", "w_lens", "w_snow_stays", "w_bolt", "w_cloth", "w_rain_cam"]
var w_rain := "mittel"
var w_vis := 90.0             # Sichtweite im Nebel (m); 90 m ≈ der Nebel bis 3D-4.26
var w_drift := true           # Nebel zieht in Schwaden
var w_ground := true          # Bodennebel (Kamerabild: eigene Schicht)
var w_lens := true            # Tropfen und Beschlag physikalisch (linse.gd)
var w_snow_stays := true
var w_bolt := true
var w_cloth := true           # Zeltwände im Wind, Wäsche / Fahnen ohne Ruckeln
var w_rain_cam := true        # Regen im Kamerabild (Alpha-Hash)

var snow_cm := 0.0            # Schneehöhe
var lens_t := -999.0          # Temperatur der Linse (°C)
var dew_c := 0.0
var lenses: Array = []        # Linse pro Kamera (0 Kopf, 1 Weitwinkel)
var fog_mats: Array = []      # bodennebel.gdshader pro Kamera
var fog_quads: Array = []
var test_over := {}           # Prüfstand-Plan «wetter»: Werte dieser Phase
var flashes: Array = []       # [Zeit (main.now), Entfernung m]
var stats := {"flashes": 0, "bolts_in_view": 0}
var _bolt: Node3D = null
var _bolt_until := 0.0
var _phase := 0.0
var _tent_mats: Array = []
var _drift := Vector2.ZERO
var _t_last := -1.0
var _cap_t := [0.0, 0.0]
var _next_test_flash := 0.0
var _vis_now := 0.0
var _gf_dens := 0.0
var _rain_fixed := false
var _ready_done := false
const WIND_DIR := Vector2(0.94, 0.34)  # aus Westen (leicht südlich) - für Regen, Schnee, Nebelschwaden


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		for k in SAVE:
			if d.has(k):
				set(k, d[k] if typeof(get(k)) != TYPE_BOOL else bool(d[k]))
		snow_cm = float(d.get("snow_cm", 0.0))
	w_vis = clampf(float(w_vis), 15.0, 2000.0)
	if _cls(w_rain).is_empty():
		w_rain = "mittel"


func save() -> void:
	var d := {"snow_cm": snappedf(snow_cm, 0.1)}
	for k in SAVE:
		d[k] = get(k)
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


func _put(k: String, v) -> void:
	set(k, v)
	save()
	if k == "w_cloth":
		_set_tents(bool(v))
	if k == "w_lens":
		for L in lenses:
			L.enabled = bool(v)


func _v(k: String):
	"""der Wert einer Einstellung - im Prüfstand-Plan «wetter» der Wert der Phase"""
	if test_over.has(k):
		return test_over[k]
	return get(k)


func _cls(id: String) -> Array:
	for c in RAIN:
		if c[0] == id:
			return c
	return []


func rain_mmh() -> float:
	"""Niederschlag jetzt (mm/h Wasser); 0 ohne Regen / Schnee"""
	if not main.weather in ["rain", "snow"]:
		return 0.0
	var c := _cls(str(_v("w_rain")))
	return float(c[2]) if not c.is_empty() else 8.0


func rain_db() -> float:
	"""Lärm des Regens am Mikrofon gegenüber «mittel» (dB): + 10·log10(R / 8) · 0.6"""
	var r := rain_mmh()
	return 0.0 if r <= 0.0 else 6.0 * log(r / 8.0) / log(10.0)


func snow_lying() -> bool:
	return snow_cm >= 0.5 or (main.weather == "snow" and not w_snow_stays)


func flash_recent(t: float, secs: float) -> bool:
	for f in flashes:
		if t - float(f[0]) >= -0.2 and t - float(f[0]) <= secs:
			return true
	return false


# ---- Bedienfeld -------------------------------------------------------------------------------------------------------
func add_controls() -> void:
	var m = main
	var opts := []
	for c in RAIN:
		opts.append([c[0], c[1]])
	m.add_control("select", "w_rain", "Regenstärke (gilt auch für Schnee)", func(): return w_rain, func(v): _put("w_rain", str(v)), "Wetter", {"options": opts})
	m.add_control("slider", "w_vis", "Sichtweite im Nebel", func(): return w_vis, func(v): _put("w_vis", clampf(float(v), 15.0, 2000.0)), "Wetter",
			{"min": 20, "max": 1000, "step": 5, "unit": "m"})
	var mw := {"sub": "Mehr Wetter"}
	m.add_control("toggle", "w_drift", "Nebel zieht in Schwaden mit dem Wind (die Sichtweite schwankt)", func(): return w_drift, func(v): _put("w_drift", bool(v)), "Wetter", mw)
	m.add_control("toggle", "w_ground", "Bodennebel: dichter über dem Boden, fleckig (im Kamerabild für MoveEye)", func(): return w_ground, func(v): _put("w_ground", bool(v)), "Wetter", mw)
	m.add_control("toggle", "w_snow_stays", "Schnee bleibt liegen (wächst beim Schneien, schmilzt über 0 °C)", func(): return w_snow_stays, func(v): _put("w_snow_stays", bool(v)), "Wetter", mw)
	m.add_control("slider", "w_snow_cm", "Schneehöhe jetzt", func(): return snappedf(snow_cm, 0.5), func(v): snow_cm = clampf(float(v), 0.0, 60.0); save(), "Wetter",
			{"min": 0, "max": 60, "step": 0.5, "unit": "cm", "sub": "Mehr Wetter"})
	m.add_control("toggle", "w_bolt", "Blitze sichtbar am Himmel (bei Gewitter)", func(): return w_bolt, func(v): _put("w_bolt", bool(v)), "Wetter", mw)
	m.add_control("button", "w_flash", "Blitz jetzt (Test: Lichtblitz im Kamerabild – typischer Fehlalarm)", null, func(): main.lightning_strike(), "Wetter", mw)
	m.add_control("toggle", "w_cloth", "Zeltplanen beulen und flattern im Wind, Wäsche und Fahnen ohne Ruckeln", func(): return w_cloth, func(v): _put("w_cloth", bool(v)), "Wetter", {"sub": "Natur und Wind"})
	m.add_control("toggle", "w_lens", "Tropfen und Beschlag physikalisch: Tropfen haften, fliessen zusammen und rinnen, Linse beschlägt unter dem Taupunkt",
			func(): return w_lens, func(v): _put("w_lens", bool(v)), "Kamerabild")
	m.add_control("toggle", "w_rain_cam", "Regen und Spritzer im Kamerabild für MoveEye", func(): return w_rain_cam, func(v): _put("w_rain_cam", bool(v)); _fix_particles(), "Kamerabild", {"expert": true})
	var sb := {"sub": "Schwierige Bedingungen"}
	m.add_control("button", "w_wipe", "Linse putzen (Tropfen und Beschlag weg)", null, func(): wipe(), "Kamerabild", sb)
	m.add_control("button", "w_morning", "Morgen-Test: warme, feuchte Luft – die kalte Linse beschlägt", null, func(): morning(), "Kamerabild", sb)


# ---- jede halbe Sekunde (main._update_sky, nach colors) --------------------------------------------------------------
func sky_tick() -> void:
	if main.env == null or main.rain == null:
		return
	if not _ready_done:
		_ready_done = true
		_setup()
	var t: float = main.now()
	var dt_r: float = 0.0 if _t_last < 0.0 else clampf(t - _t_last, 0.0, 5.0)
	_t_last = t
	var dt: float = dt_r * float(main.speed)
	if not (main.testrun != null and main.testrun.running):
		test_over.clear()
	_precip()
	_fog(dt_r)
	_snow(dt)
	_lens_climate(dt)
	_test_flash(t)
	flashes = flashes.filter(func(f): return t - float(f[0]) < 120.0)
	for tm in _tent_mats:
		if is_instance_valid(tm):
			tm.set_shader_parameter("wet", main.colors.wetness if main.colors != null else 0.0)


func _setup() -> void:
	"""die Overlays vor Kamera 0 und 1 (zwischen camfx und lens), Regen im Kamerabild"""
	for i in range(2):
		var cam: Camera3D = main.cams[i]
		var lay := 32 if i == 0 else 64
		var L = Linse.new(cam, Vector2i(main.CAM_W[i], main.CAM_H[i]), lay, 0.1212, float(main.CAM_FOV[i]))
		L.enabled = w_lens
		lenses.append(L)
		var dist := 0.1218
		var w := 2.0 * dist * tan(deg_to_rad(float(main.CAM_FOV[i])) / 2.0) * 1.04
		var hgt := w * float(main.CAM_H[i]) / float(main.CAM_W[i]) * 1.04
		var q := MeshInstance3D.new()
		var qm := QuadMesh.new()
		qm.size = Vector2(w, hgt) * 1.015
		q.mesh = qm
		q.position = Vector3(0, 0, -dist)
		q.layers = lay
		q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var fm := ShaderMaterial.new()
		fm.shader = load("res://shaders/bodennebel.gdshader")
		q.material_override = fm
		q.visible = false
		cam.add_child(q)
		fog_mats.append(fm)
		fog_quads.append(q)
	_fix_particles()


func _fix_particles() -> void:
	"""Regen und Spritzer gerastert statt durchsichtig: so sind sie im Bild hinter camfx (das liest nur Undurchsichtiges)"""
	var mode := BaseMaterial3D.TRANSPARENCY_ALPHA_HASH if w_rain_cam else BaseMaterial3D.TRANSPARENCY_ALPHA
	for p in [main.rain, main.splashes]:
		if p == null or p.mesh == null:
			continue
		var mt = p.mesh.material
		if mt is StandardMaterial3D:
			(mt as StandardMaterial3D).transparency = mode
			(mt as StandardMaterial3D).alpha_hash_scale = 1.0


func _precip() -> void:
	"""Regen / Schnee nach Stärke: Fallgeschwindigkeit, Menge, schräg im Wind"""
	var c := _cls(str(_v("w_rain")))
	if c.is_empty():
		c = RAIN[2]
	var R: float = float(c[2])
	var wind_ms: float = float(main.wind) * main.gust() / 3.6
	var wv := Vector3(WIND_DIR.x, 0.0, WIND_DIR.y)
	# Regen: mittlerer Tropfen D0 = 0.89 · R^0.21 mm, Endgeschwindigkeit nach Gunn-Kinzer
	var d0 := 0.89 * pow(R, 0.21)
	var v := 9.65 - 10.3 * exp(-0.6 * d0)
	var rp: CPUParticles3D = main.rain
	var want_n: int = Quality.n(int(c[3]))
	if rp.amount != want_n:
		rp.amount = want_n
	var vel := wv * wind_ms * 0.85 + Vector3(0, -v, 0)
	rp.direction = vel.normalized()
	rp.spread = 2.0
	rp.initial_velocity_min = vel.length() * 0.92
	rp.initial_velocity_max = vel.length() * 1.06
	rp.gravity = Vector3.ZERO
	rp.particle_flag_align_y = true
	rp.lifetime = 13.0 / v
	rp.position = Vector3(0, 12, -8) - wv * wind_ms * 0.85 * rp.lifetime * 0.5
	var ln := clampf(v * 0.055, 0.12, 0.5)                # Strich: Weg während der Belichtung
	var bm = rp.mesh
	if bm is BoxMesh and absf((bm as BoxMesh).size.y - ln) > 0.01:
		(bm as BoxMesh).size = Vector3(0.006 + 0.0015 * d0, ln, 0.006 + 0.0015 * d0)
	if bm != null and bm.material is StandardMaterial3D:
		(bm.material as StandardMaterial3D).albedo_color.a = clampf(0.22 + 0.12 * d0, 0.25, 0.6)
	if main.splashes != null:
		var sn: int = Quality.n(int(c[5]))
		if main.splashes.amount != sn:
			main.splashes.amount = sn
	# Schnee: Flocken ~1 m/s, treiben stark mit dem Wind
	var sp: CPUParticles3D = main.snow
	var sn2: int = Quality.n(int(c[4]))
	if sp.amount != sn2:
		sp.amount = sn2
	var sv := wv * wind_ms * 0.95 + Vector3(0, -1.0, 0)
	sp.direction = sv.normalized()
	sp.initial_velocity_min = sv.length() * 0.8
	sp.initial_velocity_max = sv.length() * 1.2
	sp.gravity = Vector3(0, -0.1, 0)
	sp.lifetime = 11.0
	sp.position = Vector3(0, 10, -8) - wv * wind_ms * 0.95 * 5.5


func _fog(dt_r: float) -> void:
	"""Sichtweite (Koschmieder), Schwaden mit dem Wind, Bodennebel"""
	var env: Environment = main.env
	var wind_ms: float = maxf(0.6, float(main.wind) / 3.6)
	_drift += WIND_DIR * wind_ms * dt_r
	var R := rain_mmh()
	var vis := 0.0
	match str(main.weather):
		"fog":
			vis = float(_v("w_vis"))
			if bool(_v("w_drift")):
				# Schwaden von ~150 m ziehen mit dem Wind vorbei: die Sichtweite schwankt um ±35 %
				var ph := _drift.x / 150.0
				vis *= 1.0 + 0.35 * (0.6 * sin(ph * TAU) + 0.4 * sin(ph * TAU * 2.7 + 1.3))
		"rain":
			vis = 650.0 * pow(8.0 / maxf(R, 0.1), 0.6)       # mittel = wie bisher (Dichte 0.006)
		"snow":
			vis = 326.0 * pow(1.6 / maxf(R / 5.0, 0.05), 0.7)
	if vis > 0.0:
		env.fog_density = 3.912 / maxf(vis, 5.0)
	_vis_now = vis if vis > 0.0 else 3.912 / maxf(env.fog_density, 0.0001)
	# Bodennebel: am Boden dichter, oben dünner (Schichthöhe H)
	var gf: float = main.colors.ground_fog if main.colors != null else 0.0
	var dens0 := 0.0
	var H := 1.0
	if bool(_v("w_ground")):
		if main.weather == "fog":
			dens0 = 3.912 / maxf(float(_v("w_vis")) * 0.6, 8.0)
			H = 2.2
		elif gf > 0.01:
			dens0 = 0.07 * gf
			H = 0.9
	_gf_dens = dens0
	if dens0 > 0.0:                                       # die Ansicht im Fenster: Höhennebel der Umgebung (grob)
		env.fog_height = main.ground_y(0.0, -8.0) + H
		env.fog_height_density = maxf(env.fog_height_density, dens0 * 0.35)
	var day: float = clampf((main.sun_el() + 6.0) / 18.0, 0.0, 1.0)
	var fc: Color = env.fog_light_color
	for i in range(fog_mats.size()):
		var fm: ShaderMaterial = fog_mats[i]
		var on := dens0 > 0.0
		fm.set_shader_parameter("dens0", dens0)
		fm.set_shader_parameter("hscale", H)
		fm.set_shader_parameter("ground_y", main.ground_y(0.0, -8.0))
		fm.set_shader_parameter("fcol", Vector3(fc.r, fc.g, fc.b) * (0.6 + 0.4 * day))
		fm.set_shader_parameter("drift", -_drift)
		fm.set_shader_parameter("patchy", 0.6 if bool(_v("w_drift")) and not Quality.lite() else 0.0)
		fog_quads[i].visible = on


func _snow(dt: float) -> void:
	"""Schneedecke: wächst beim Schneien (1 mm Wasser ≈ 1 cm), schmilzt über 0 °C (Grad-Stunden), bei Regen und Sonne schneller"""
	var amb: float = float(main.ambient)
	var R := rain_mmh()
	if w_snow_stays:
		if main.weather == "snow":
			var stick := clampf((2.0 - amb) / 2.0, 0.0, 1.0)     # über 2 °C schmilzt er beim Landen
			snow_cm += (R / 5.0) * 1.0 * stick * dt / 3600.0
		if amb > 0.0 and snow_cm > 0.0:
			var sunk: float = maxf(0.0, main.sun_el()) / 50.0 * (1.0 - main.clouds())
			var melt := 0.25 * amb + (0.06 * R * amb / 5.0 if main.weather == "rain" else 0.0) + 1.2 * sunk
			snow_cm = maxf(0.0, snow_cm - melt * dt / 3600.0)
		snow_cm = minf(snow_cm, 80.0)
	var cover := 0.0
	if w_snow_stays:
		cover = 0.95 * (1.0 - exp(-snow_cm / 1.6))
	elif main.weather == "snow":
		cover = 0.85
	main.grass_mat.set_shader_parameter("snow_amount", cover)
	for gm in main.ground_mats:
		gm.set_shader_parameter("snow_amount", cover)


func _lens_climate(dt: float) -> void:
	"""Linsentemperatur und Taupunkt → Beschlag; was auf die Linse fällt"""
	var amb: float = float(main.ambient)
	var rh: float = clampf(float(main.humidity), 5.0, 100.0)
	var g := log(rh / 100.0) + 17.62 * amb / (243.12 + amb)       # Magnus
	dew_c = 243.12 * g / (17.62 - g)
	var cl: float = main.clouds()
	var sunk: float = maxf(0.0, main.sun_el()) / 50.0 * (1.0 - cl)
	var target := amb + 0.6                                        # das Gehäuse mit dem Pi wärmt ein wenig
	if main.is_dark():
		target -= 2.6 * (1.0 - cl)                                 # Glas strahlt in den klaren Himmel ab
	target += 3.0 * sunk
	if lens_t < -500.0:
		lens_t = target
	lens_t += (target - lens_t) * (1.0 - exp(-dt / 900.0))        # Wärme braucht ~15 Minuten
	var rate := 0.0                                                # Beschlag pro Minute
	if lens_t < dew_c:
		rate = 0.07 * (dew_c - lens_t)
	else:
		rate = -0.05 * (lens_t - dew_c) - 0.04 * sunk - 0.004 * float(main.wind)
	var dry := 0.0
	if not main.weather in ["rain", "snow", "fog"]:
		dry = 0.05 * (1.0 + float(main.wind) / 20.0) * (1.1 - rh / 100.0) * (1.0 + 3.0 * sunk) + (0.06 if lens_t - dew_c > 3.0 else 0.0)
	var R := rain_mmh() if main.lens_drops else 0.0
	var tilt: float = rad_to_deg(main.head_pitch.rotation.x) if main.head_pitch != null else 0.0
	for i in range(lenses.size()):
		var L = lenses[i]
		var r := rate
		if main.cond.get("fogged", false):
			r = maxf(r, 0.5 if L.fog < (0.8 if i == 0 else 0.5) else 0.0)
		if test_over.has("lens_fog") and L.fog < float(test_over["lens_fog"]):
			r = maxf(r, 0.6)
		L.set_climate(r, dry)
		var rain := R if main.weather == "rain" else 0.0
		var snow := R if main.weather == "snow" else 0.0
		L.set_weather(rain, snow, float(main.wind) * main.gust(), tilt if i == 0 else 0.0, float(main.ambient))
		if main.cond.get("drops", false) and L.drops.size() < 25:
			L.splash(3)


func lens_tick() -> void:
	"""nach main._update_lens: die alten festen Tropfen / der alte Schleier aus, wenn linse.gd sie macht"""
	if not w_lens:
		return
	for m in main.lens_mats:
		m.set_shader_parameter("drops", 0.0)
		m.set_shader_parameter("fogged", 0.0)


func before_capture(i: int) -> void:
	"""vor jedem Bild von Kamera i: Linse weiterrechnen, Belichtung mitgeben"""
	if i >= lenses.size():
		return
	var L = lenses[i]
	var t: float = main.now()
	var dt: float = clampf(t - float(_cap_t[i]), 0.0, 1.0) if _cap_t[i] > 0.0 else 0.0
	_cap_t[i] = t
	L.set_expo(float(main.lens_mats[i].get_shader_parameter("expo")))
	L.step(dt, dt * float(main.speed))
	if i < fog_mats.size():
		fog_mats[i].set_shader_parameter("expo", float(main.lens_mats[i].get_shader_parameter("expo")))


func _process(dt: float) -> void:
	if true or not _ready_done:
		return
	# Wäsche, Fahnen, Zeltwände: Takt aus dem Wind aufsummiert (vorher TIME × Wind: jede Böe liess die Welle springen)
	var w: float = clampf(float(main.wind) * main.gust() / 50.0, 0.05, 1.6)
	_phase += dt * (1.0 + 1.5 * w)
	if w_cloth:
		for cm in main.cloth_mats:
			if is_instance_valid(cm):
				cm.set_shader_parameter("phase", fmod(_phase, 6283.0))
	# die Linse weiterrechnen, auch wenn gerade keine Bilder geholt werden (Vorschau im Fenster)
	var t: float = main.now()
	for i in range(lenses.size()):
		if t - float(_cap_t[i]) > 0.3:
			before_capture(i)
	if _bolt != null and t > _bolt_until:
		_bolt.queue_free()
		_bolt = null


func _test_flash(t: float) -> void:
	if test_over.has("flash_every") and main.weather == "rain":
		if _next_test_flash == 0.0 or _next_test_flash - t > 600.0:
			_next_test_flash = t + 6.0
		if t >= _next_test_flash:
			_next_test_flash = t + float(test_over["flash_every"]) * randf_range(0.7, 1.3)
			main.lightning_strike()
	else:
		_next_test_flash = 0.0


# ---- Gewitter --------------------------------------------------------------------------------------------------------
func on_strike(dist: float, dir: Vector3) -> void:
	"""main.lightning_strike: ein neuer Blitz (Ort für den Strahl am Himmel, Zeit für den Testlauf)"""
	flashes.append([main.now(), dist])
	stats["flashes"] += 1
	if not w_bolt:
		return
	if _bolt != null:
		_bolt.queue_free()
	_bolt = _make_bolt(dir * dist, dist)
	_bolt.visible = false
	main.add_child(_bolt)
	_bolt_until = main.now() + 1.2
	var cam: Camera3D = main.cams[0]
	if cam.is_position_in_frustum(dir * dist + Vector3(0, 200, 0)):
		stats["bolts_in_view"] += 1


func on_flash(energy: float) -> void:
	"""main._lightning: jede Stufe des Blitzes (hell / dunkel)"""
	if _bolt != null:
		_bolt.visible = energy > 0.0


func _make_bolt(foot: Vector3, dist: float) -> Node3D:
	"""ein Zickzack-Strahl von der Wolke (450 m) zum Boden, mit einem Ast; hell, auch im Regen noch zu sehen"""
	var n := Node3D.new()
	var mt := StandardMaterial3D.new()
	mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mt.disable_fog = true
	var k := clampf(exp(-dist / maxf(3.0 * _vis_now, 300.0)), 0.25, 1.0)
	mt.albedo_color = Color(0.85, 0.9, 1.0) * k + Color(0.08, 0.08, 0.1) * (1.0 - k)
	var wdt := clampf(dist / 450.0, 2.0, 8.0)                   # mindestens gut 1 Bildpunkt breit
	var pts := [foot + Vector3(0, 450, 0)]
	var p: Vector3 = pts[0]
	for s in range(11):
		p = p + Vector3(randf_range(-45, 45), -450.0 / 11.0, randf_range(-45, 45))
		pts.append(p)
	pts[-1].y = main.ground_y(foot.x, foot.z) if absf(foot.x) < 1500 and absf(foot.z) < 1500 else 0.0
	var br := [pts[4]]
	var q: Vector3 = pts[4]
	for s in range(4):
		q = q + Vector3(randf_range(-70, 70), -35.0, randf_range(-70, 70))
		br.append(q)
	for chain in [pts, br]:
		for j in range(chain.size() - 1):
			var a: Vector3 = chain[j]
			var b: Vector3 = chain[j + 1]
			var mi := MeshInstance3D.new()
			var bx := BoxMesh.new()
			var ln := a.distance_to(b)
			bx.size = Vector3(wdt * (0.6 if chain == br else 1.0), ln, wdt * (0.6 if chain == br else 1.0))
			mi.mesh = bx
			mi.material_override = mt
			mi.layers = 1
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			n.add_child(mi)
			var mid := (a + b) * 0.5
			var up := (b - a).normalized()
			var side := up.cross(Vector3.FORWARD if absf(up.z) < 0.9 else Vector3.RIGHT).normalized()
			mi.transform = Transform3D(Basis(side, up, side.cross(up)), mid)
	return n


# ---- Zeltplanen ------------------------------------------------------------------------------------------------------
func on_scene() -> void:
	"""nach dem Bau einer Szene: Zeltwände (Prismen mit Zelt-Stoff) bekommen den Wind"""
	_tent_mats.clear()
	if main.scenes == null or main.scenes.root == null:
		return
	if w_cloth:
		_set_tents(true)


func _set_tents(on: bool) -> void:
	if main.scenes == null or main.scenes.root == null:
		return
	var todo: Array = [main.scenes.root]
	while not todo.is_empty():
		var nd = todo.pop_back()
		todo.append_array(nd.get_children())
		if not nd is MeshInstance3D or (nd as MeshInstance3D).layers != 1:
			continue
		var mi: MeshInstance3D = nd
		if on and mi.mesh is PrismMesh and not mi.has_meta("zelt_alt"):
			var pm: PrismMesh = mi.mesh
			var mt = mi.material_override
			if pm.size.y < 0.8 or pm.size.y > 3.0 or pm.size.z < 0.6 or not (mt is StandardMaterial3D) or not _is_tent(mt):
				continue
			mi.set_meta("zelt_alt", [pm, mt])
			var np := pm.duplicate() as PrismMesh
			np.subdivide_width = 6
			np.subdivide_height = 4
			np.subdivide_depth = 6
			mi.mesh = np
			var sm := ShaderMaterial.new()
			sm.shader = load("res://shaders/zeltwind.gdshader")
			sm.set_shader_parameter("color", (mt as StandardMaterial3D).albedo_color)
			sm.set_shader_parameter("half_size", pm.size * 0.5)
			sm.set_shader_parameter("seed", randf() * 10.0)
			sm.set_shader_parameter("wind", main.wind)
			mi.material_override = sm
			main.cloth_mats.append(sm)
			_tent_mats.append(sm)
		elif not on and mi.has_meta("zelt_alt"):
			var old: Array = mi.get_meta("zelt_alt")
			main.cloth_mats.erase(mi.material_override)
			mi.mesh = old[0]
			mi.material_override = old[1]
			mi.remove_meta("zelt_alt")
	if not on:
		_tent_mats.clear()
	for cm in main.cloth_mats:
		if is_instance_valid(cm):
			cm.set_shader_parameter("phase", -1.0 if not on else fmod(_phase, 6283.0))


func _is_tent(mt: StandardMaterial3D) -> bool:
	if main.colors == null:
		return false
	for k in main.colors.kind_mats:
		if main.colors.kind_mats[k] == mt:
			return str(k).ends_with("|tent")
	return false


# ---- Knöpfe und Test -------------------------------------------------------------------------------------------------
func wipe() -> void:
	for L in lenses:
		L.wipe()


func morning() -> void:
	"""warme, feuchte Morgenluft: die Luft wird 5 °C wärmer und fast gesättigt, die Linse bleibt erst kalt → sie beschlägt"""
	if lens_t < -500.0:
		lens_t = float(main.ambient)
	lens_t = minf(lens_t, float(main.ambient))
	main.ambient = clampf(float(main.ambient) + 5.0, -15.0, 40.0)
	main.humidity = 95.0
	main._sync_ui()


func test_phase(w: Dictionary) -> void:
	"""testrun.gd: die Wetter-Werte einer Phase (leer = Standard dieser Einstellungen, damit andere Pläne gleich bleiben)"""
	test_over = {"w_rain": "mittel", "w_vis": 90.0, "w_drift": true, "w_ground": true}
	for k in w:
		var kk := str(k)
		match kk:
			"rain":
				test_over["w_rain"] = str(w[k])
			"vis":
				test_over["w_vis"] = float(w[k])
			"drift":
				test_over["w_drift"] = bool(w[k])
			"ground":
				test_over["w_ground"] = bool(w[k])
			_:
				test_over[kk] = w[k]
	snow_cm = float(w.get("snow_cm", 5.0 if main.weather == "snow" else 0.0))   # Schnee-Phase: liegt schon (wie bisher)
	for L in lenses:
		L.wipe()
		if w.has("lens_fog"):
			L.fog_now(float(w["lens_fog"]))
		if w.has("lens_drops"):
			L.splash(int(w["lens_drops"]))
	if w.has("ambient"):
		main.ambient = float(w["ambient"])
	if w.has("humidity"):
		main.humidity = float(w["humidity"])


func info() -> Dictionary:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	d["rain_mmh"] = rain_mmh()
	d["vis_m"] = roundi(_vis_now)
	d["fog_density"] = snappedf(main.env.fog_density, 0.00001) if main.env != null else 0.0
	d["ground_fog_dens0"] = snappedf(_gf_dens, 0.0001)
	d["snow_cm"] = snappedf(snow_cm, 0.1)
	d["snow_lying"] = snow_lying()
	d["lens_t"] = snappedf(lens_t, 0.1)
	d["dew_c"] = snappedf(dew_c, 0.1)
	d["lens"] = lenses.map(func(L): return L.info())
	d["flashes"] = flashes.map(func(f): return snappedf(main.now() - float(f[0]), 0.1))
	d["stats"] = stats
	d["test"] = test_over
	d["tents"] = _tent_mats.size()
	d["rain_amount"] = main.rain.amount if main.rain != null else 0
	d["rain_speed"] = snappedf(main.rain.initial_velocity_max, 0.1) if main.rain != null else 0.0
	d["wetness"] = snappedf(main.colors.wetness, 0.01) if main.colors != null else 0.0
	d["puddle"] = snappedf(main.colors.puddle, 0.01) if main.colors != null else 0.0
	return d


func control(d: Dictionary) -> Dictionary:
	"""{do: info | set (key, value) | flash | wipe | splash (n, cam) | fog (value) | snow (cm) | morning | expo_mul (value)}"""
	var op := str(d.get("do", "info"))
	match op:
		"set":
			var k := str(d.get("key", ""))
			if k in SAVE:
				var cur = get(k)
				_put(k, bool(d.get("value", true)) if typeof(cur) == TYPE_BOOL else (float(d["value"]) if typeof(cur) == TYPE_FLOAT else str(d["value"])))
		"flash":
			main.lightning_strike()
		"wipe":
			wipe()
		"splash":
			for i in range(lenses.size()):
				if int(d.get("cam", -1)) in [-1, i]:
					lenses[i].splash(int(d.get("n", 20)))
		"fog":
			for L in lenses:
				L.fog_now(float(d.get("value", 0.8)))
		"snow":
			snow_cm = clampf(float(d.get("cm", 5.0)), 0.0, 80.0)
		"morning":
			morning()
		"expo_mul":                                          # Test: liest das Overlay ein belichtetes Bild? (1 = nein)
			for L in lenses:
				L.mat.set_shader_parameter("mul_expo", float(d.get("value", 1.0)))
		"test_phase":
			test_phase(d.get("w", {}))
	return {"ok": true, "info": info()}
