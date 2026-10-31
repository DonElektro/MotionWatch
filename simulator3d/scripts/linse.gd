extends RefCounted
## Paket «Wetter physikalisch» (Zweig real-wetter): Tropfen und Beschlag auf der Linse einer Kamera – ein eigenes Overlay mit
## klarer Schnittstelle, damit es mit dem Kamera-Physik-Paket (Rauschen / Belichtung, parallel) kombinierbar bleibt.
##
## Physik (vereinfacht, auf einer kleinen Karte von 128 × 72 Punkten, ein Punkt ≈ 7.5 Bildpunkte der Kopfkamera):
##  - Tropfen landen je nach Regenstärke, Wind und Neigung der Kamera (nach oben = mehr), bleiben haften,
##    fliessen zusammen (Volumen bleibt), werden sie zu schwer, rinnen sie nach unten, sammeln Tropfen auf ihrem Weg ein und
##    lassen eine nasse Spur, die den Beschlag wegwischt. Sie trocknen langsam (Feuchte, Wind, Sonne).
##  - Schnee: Flocken bleiben als weisse Flecken liegen und schmelzen über 0 °C zu Tropfen.
##  - Beschlag: Wasserfilm 0..1, wächst, wenn die Linse kälter als der Taupunkt ist, verdunstet sonst (wetter.gd rechnet
##    Linsentemperatur und Taupunkt; hier nur der Film und wo Spuren ihn weggewischt haben).
##  - Bild: im Tropfen bricht das Wasser das Bild (verkehrt, verschwommen), am Rand dunkel, oben links ein Glanzpunkt;
##    Beschlag = weich gezeichnetes, milchiges Bild (shaders/linse.gdshader liest das Bild hinter dem Viereck).
##
## Schnittstelle (für andere Pakete, z. B. Kamera-Physik):
##   var L = Linse.new(cam, Vector2i(960, 540), layer, 0.1212)  # eigenes Viereck vor der Kamera (zwischen camfx und lens)
##   L.set_weather(rain_mmh, snow_mmh, wind_kmh, tilt_up_deg, air_c)    # was gerade auf die Linse fällt
##   L.set_climate(fog_target_rate, dry_rate)                            # Beschlag: wächst / verdunstet pro Minute (wetter.gd)
##   L.step(dt_real, dt_sim)  -> bool (Karte neu)                         # Physik + Textur (vor jedem Bild der Kamera)
##   L.set_expo(e)            # Belichtung der Kamera (das Bild hinter dem Viereck ist noch nicht belichtet)
##   L.wipe() / L.splash(n) / L.fog_now(f)                               # Test: Linse putzen, n Tropfen, Beschlag setzen
##   L.info() -> {drops, running, fog, cover, ...}                        # Kennzahlen (cover = Anteil der Fläche mit Wasser)
##   L.enabled = false        # Overlay aus (Viereck unsichtbar, Physik ruht)
##   L.strength = 0..1        # wie stark das Overlay wirkt (z. B. für ein Kamera-Paket, das selbst mischt)
## Das Viereck liegt auf der Ebene der Kamera (32 / 64) – die Kamera sieht es, die Ansicht im Fenster nicht.

const Quality = preload("res://scripts/quality.gd")
const W := 128
const H := 72
const R_RUN := 2.7              # ab diesem Radius (Kartenpunkte) rinnt ein Tropfen
const MAX_DROPS := 170

var enabled := true
var strength := 1.0
var mat: ShaderMaterial
var quad: MeshInstance3D
var img: Image
var tex: ImageTexture
var drops: Array = []           # [x, y, r, vy, snow(0/1)]
var trail := PackedFloat32Array()   # nasse Spur 0..1 (wischt den Beschlag weg, trocknet)
var fog := 0.0                  # Beschlag (Wasserfilm) 0..1
var fog_rate := 0.0             # + pro Minute Simulationszeit (wetter.gd)
var dry_rate := 0.02            # Verdunsten der Tropfen: Radius-Punkte pro Minute
var rain_mmh := 0.0
var snow_mmh := 0.0
var wind_kmh := 0.0
var tilt_up := 0.0
var air_c := 10.0
var landed := 0                 # gezählt seit dem Start (Test)
var ran := 0
var _acc := 0.0
var _dirty := true
var _empty_sent := false
var _buf := PackedByteArray()
var _rng := RandomNumberGenerator.new()


func _init(cam: Camera3D, res: Vector2i, layer: int, dist: float, fov_deg: float) -> void:
	_rng.randomize()
	trail.resize(W * H)
	_buf.resize(W * H * 4)
	img = Image.create(W, H, false, Image.FORMAT_RGBA8)
	img.fill(Color(0.5, 0.5, 0.0, 1.0))
	tex = ImageTexture.create_from_image(img)
	var w := 2.0 * dist * tan(deg_to_rad(fov_deg) / 2.0) * 1.04
	var hgt := w * float(res.y) / float(res.x)
	quad = MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(w, hgt) * 1.01
	quad.mesh = qm
	quad.position = Vector3(0, 0, -dist)
	quad.layers = layer
	quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mat = ShaderMaterial.new()
	mat.shader = load("res://shaders/linse.gdshader")
	mat.set_shader_parameter("res", Vector2(res))
	mat.set_shader_parameter("drop_map", tex)
	quad.material_override = mat
	quad.visible = false
	cam.add_child(quad)


func set_weather(rain: float, snow: float, wind: float, tilt_deg: float, air: float) -> void:
	rain_mmh = maxf(rain, 0.0)
	snow_mmh = maxf(snow, 0.0)
	wind_kmh = maxf(wind, 0.0)
	tilt_up = tilt_deg
	air_c = air


func set_climate(fog_per_min: float, dry_per_min: float) -> void:
	fog_rate = fog_per_min
	dry_rate = maxf(dry_per_min, 0.0)


func set_expo(e: float) -> void:
	if mat != null:
		mat.set_shader_parameter("expo", e)


func exposure() -> float:
	"""wie viel vom Niederschlag die Linse trifft: Schirm des Gehäuses, Neigung nach oben, Wind treibt den Regen schräg"""
	var up := clampf((tilt_up + 10.0) / 50.0, 0.0, 1.0)
	return clampf(0.12 + 0.55 * up + wind_kmh / 45.0, 0.0, 1.6)


func step(dt: float, dt_sim: float) -> bool:
	"""Physik für dt Sekunden (echte Zeit für Fallen / Rinnen, Simulationszeit für Trocknen / Beschlag); true = Karte neu"""
	if not enabled:
		if quad.visible:
			quad.visible = false
		return false
	dt = clampf(dt, 0.0, 1.0)
	dt_sim = clampf(dt_sim, 0.0, 600.0)
	var cap := MAX_DROPS if not Quality.lite() else 70
	# 1. neue Tropfen / Flocken (Poisson: im Mittel rate · dt)
	var rate := (2.2 * pow(rain_mmh, 0.7) + 1.6 * pow(snow_mmh, 0.7)) * exposure()
	_acc += rate * dt
	while _acc >= 1.0:
		_acc -= 1.0
		if true:
			var is_snow := snow_mmh > 0.0 and _rng.randf() < snow_mmh / (snow_mmh + rain_mmh + 0.001) and air_c < 1.0
			_land(_rng.randf_range(0.0, W), _rng.randf_range(0.0, H), _rng.randf_range(0.6, 1.5) * (1.4 if is_snow else 1.0) * (1.0 + 0.012 * rain_mmh), is_snow)
	while drops.size() > cap:
		drops.pop_front()
		_dirty = true
	# 2. Tropfen: schmelzen, trocknen, rinnen
	var dry := dry_rate * dt_sim / 60.0
	var keep: Array = []
	for d in drops:
		if d[4] == 1 and air_c > 0.5:                     # Schnee auf der Linse schmilzt zu einem Tropfen
			d[2] *= 0.75
			d[4] = 0
			_dirty = true
		if dry > 0.0:
			d[2] -= dry * (1.0 if d[4] == 0 else 0.3) / maxf(0.6, d[2])   # kleine verschwinden zuerst
			_dirty = true
		if d[2] < 0.35:
			continue
		if d[4] == 0 and d[2] > R_RUN:
			d[3] = minf(d[3] + 18.0 * (d[2] - R_RUN + 0.3) * dt, 12.0 + 4.0 * d[2])   # Kartenpunkte / s
		elif d[3] > 0.0:
			d[3] = maxf(0.0, d[3] - 30.0 * dt)
		if d[3] > 0.0:
			var dy: float = d[3] * dt
			var steps := int(ceil(dy))
			for _s in range(steps):
				d[1] += dy / steps
				d[0] += _rng.randf_range(-0.35, 0.35)
				d[2] -= 0.022                             # lässt Wasser in der Spur
				_mark_trail(d[0], d[1], maxf(0.8, d[2] * 0.55))
			_dirty = true
			if d[1] - d[2] > H:
				ran += 1
				continue
		keep.append(d)
	drops = keep
	# 3. Zusammenfliessen (rinnende Tropfen sammeln die anderen ein)
	_merge()
	# 4. Beschlag und Spuren
	var f0 := fog
	fog = clampf(fog + fog_rate * dt_sim / 60.0, 0.0, 1.0)
	if absf(fog - f0) > 0.002:
		_dirty = true
	_decay_trail(dt_sim)
	quad.visible = strength > 0.01 and (not drops.is_empty() or fog > 0.01 or _trail_any)
	if _dirty and quad.visible:
		_draw()
		_dirty = false
		mat.set_shader_parameter("fog", fog * strength)
		mat.set_shader_parameter("strength", strength)
		return true
	return false


func _land(x: float, y: float, r: float, snow: bool) -> void:
	landed += 1
	drops.append([x, y, r, 0.0, 1 if snow else 0])
	_dirty = true


func _merge() -> void:
	var n := drops.size()
	if n < 2:
		return
	drops.sort_custom(func(a, b): return a[1] < b[1])
	var dead := {}
	for i in range(n):
		if dead.has(i):
			continue
		var a: Array = drops[i]
		for j in range(i + 1, n):
			if dead.has(j):
				continue
			var b: Array = drops[j]
			if b[1] - a[1] > 8.0:
				break
			var dx: float = a[0] - b[0]
			var dy: float = a[1] - b[1]
			var rr: float = (a[2] + b[2]) * 0.8
			if dx * dx + dy * dy < rr * rr:
				# Volumen ~ r³ bleibt; der grössere (oder der rinnende) bestimmt den Ort
				var va: float = pow(a[2], 3.0)
				var vb: float = pow(b[2], 3.0)
				var k: float = vb / (va + vb) if a[3] <= b[3] else 0.8
				a[0] = lerpf(a[0], b[0], k * 0.5)
				a[1] = maxf(a[1], b[1]) if a[3] > 0.0 or b[3] > 0.0 else lerpf(a[1], b[1], k)
				a[2] = pow(va + vb, 1.0 / 3.0)
				a[3] = maxf(a[3], b[3])
				a[4] = mini(a[4], b[4])
				dead[j] = true
				_dirty = true
	if not dead.is_empty():
		var keep: Array = []
		for i in range(n):
			if not dead.has(i):
				keep.append(drops[i])
		drops = keep


var _trail_any := false


func _mark_trail(x: float, y: float, r: float) -> void:
	var x0 := maxi(0, int(x - r))
	var x1 := mini(W - 1, int(x + r))
	var yi := int(y)
	if yi < 0 or yi >= H:
		return
	for xx in range(x0, x1 + 1):
		trail[yi * W + xx] = 1.0
	_trail_any = true


func _decay_trail(dt_sim: float) -> void:
	"""die Spur trocknet in ein paar Minuten; der Beschlag kommt danach wieder"""
	if not _trail_any or dt_sim <= 0.0:
		return
	var k := dt_sim / 240.0
	var any := false
	for i in range(W * H):
		var v: float = trail[i]
		if v > 0.0:
			v = maxf(0.0, v - k)
			trail[i] = v
			any = true
	_trail_any = any
	_dirty = true


func _draw() -> void:
	"""Karte: R, G = Neigung der Oberfläche (Brechung), B = Wasserdicke, A = Beschlag hier (1 = voll, 0 = weggewischt)"""
	var b := _buf
	for i in range(W * H):
		var o := i * 4
		var t: float = trail[i]
		b[o] = 128
		b[o + 1] = 128
		b[o + 2] = int(t * 30.0)                   # dünner Wasserfilm in der Spur
		b[o + 3] = int(255.0 * (1.0 - t))
	for d in drops:
		var cx: float = d[0]
		var cy: float = d[1]
		var r: float = d[2]
		var snow: bool = d[4] == 1
		var x0 := maxi(0, int(cx - r - 1.0))
		var x1 := mini(W - 1, int(cx + r + 1.0))
		var y0 := maxi(0, int(cy - r * (1.25 if d[3] > 0.0 else 1.0) - 1.0))
		var y1 := mini(H - 1, int(cy + r + 1.0))
		for yy in range(y0, y1 + 1):
			for xx in range(x0, x1 + 1):
				var dx: float = (xx + 0.5 - cx) / r
				var dy: float = (yy + 0.5 - cy) / (r * (1.25 if d[3] > 0.0 else 1.0))   # rinnend: länglich
				var q := dx * dx + dy * dy
				if q >= 1.0:
					continue
				var th := sqrt(1.0 - q)                 # Halbkugel
				var o := (yy * W + xx) * 4
				var tb := int(th * 190.0)
				if snow:
					tb = 200 + int(th * 55.0)           # B > 200 = Schnee (weiss, undurchsichtig)
				if tb > b[o + 2]:
					b[o] = clampi(int(128.0 + dx * 120.0), 0, 255)
					b[o + 1] = clampi(int(128.0 + dy * 120.0), 0, 255)
					b[o + 2] = tb
					b[o + 3] = 0                        # unter dem Tropfen kein Beschlag
	img.set_data(W, H, false, Image.FORMAT_RGBA8, b)
	tex.update(img)


func wipe() -> void:
	drops.clear()
	fog = 0.0
	trail.fill(0.0)
	_trail_any = false
	_dirty = true


func splash(n: int) -> void:
	for _i in range(n):
		_land(_rng.randf_range(0.0, W), _rng.randf_range(0.0, H), _rng.randf_range(0.8, 2.4), false)


func fog_now(f: float) -> void:
	fog = clampf(f, 0.0, 1.0)
	_dirty = true


func info() -> Dictionary:
	var running := 0
	var area := 0.0
	for d in drops:
		if d[3] > 0.0:
			running += 1
		area += PI * d[2] * d[2]
	return {"drops": drops.size(), "running": running, "fog": snappedf(fog, 0.01), "cover": snappedf(minf(1.0, area / float(W * H)), 0.001),
			"landed": landed, "ran_off": ran, "exposure": snappedf(exposure(), 0.01), "visible": quad.visible, "enabled": enabled}
