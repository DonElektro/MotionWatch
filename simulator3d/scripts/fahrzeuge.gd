extends Node
## Paket «Fahrzeuge» (31.10.2026, Zweig real-fahrzeuge): Autos, Lieferwagen, Wohnmobile, Töffs, Traktoren, Velos und
## E-Trottinette fahren wie echt - eine typische Fehlalarm-Quelle (Licht, Wärme, Bewegung am Bildrand).
## Erweitert die bestehenden Fahrzeuge (actor.gd kind «car» mit den Varianten "", van, moto, tractor + neu camper;
## main.car(), main.visit("car_park"), events.homecoming) statt sie zu doppeln:
##   - Tempo nach Ort: Strasse ~50 km/h (Töff 55, Wohnmobil 45, Traktor 28), auf dem Platz / Parkplatz 10 km/h;
##     anfahren und bremsen mit echten Beschleunigungen, vor Kurven und Halten abbremsen (drive(), Haken in actor._step)
##   - Licht: Tagfahrlicht am Tag, nachts Abblendlicht (leicht nach unten) oder Fernlicht (blendet ab, wenn einer
##     entgegenkommt), Rücklichter, Bremslichter, Blinker vor dem Abbiegen, Innenlicht bei offener Tür, «Coming home»
##     (Scheinwerfer brennen nach dem Parkieren noch 25 s), Blinken beim Ab- und Aufschliessen
##   - Blendung: leuchten Scheinwerfer in eine Kamera, überstrahlen sie das Bild (lens.gdshader «glare», Ort im Bild)
##   - Parkieren (visit «car_park»): Auto biegt ab, parkiert am Strassenrand / auf einem freien Platz, Türen gehen auf,
##     1–3 Personen steigen aus und gehen weg; nach einigen Minuten kommt jemand zurück und fährt weg (Schalter)
##   - Wärme: Motorhaube, Auspuff, Reifen, Scheinwerferglas kühlen nach dem Abstellen ab (Newton, gleiche Werte wie
##     waerme.gd ENGINE vom Paket «Wärme»; gibt es scripts/waerme.gd, kommen die Werte von dort). Läuft schon
##     waerme_welt.gd (Paket «Wärme»), überlässt diese Datei ihr die Motorwärme.
##   - Velo / E-Trottinett: Licht vorne und hinten (E-Trottinett neu), nachts fahren einige ohne Licht
## Lite (Quality.lite()): nur ein Scheinwerfer-Licht pro Fahrzeug, kein Innenlicht.
## Einstellungen in user://fahrzeuge.json (Besuch → Fahrzeuge). Test: /control {"action": "fahrzeuge", "do": info | set |
## spawn (kind) | arrive | leave | glare}.

const Quality = preload("res://scripts/quality.gd")
const T = preload("res://scripts/i18n.gd")
const FILE := "user://fahrzeuge.json"
const SAVE := ["fz_real", "fz_beam", "fz_glare", "fz_return"]
var main
var fz_real := true            # vehicles like real (speed, lights, doors, heat)
var fz_beam := "some"          # high beam at night: never | some | often
var fz_glare := true           # headlights into the lens blind the picture
var fz_return := true          # a parked car drives away again after a few minutes

# speeds (km/h) on the road and on the place (campsite lanes, car park); accelerations (m/s²)
const ROAD_KMH := {"": 50.0, "van": 48.0, "camper": 45.0, "moto": 55.0, "tractor": 28.0}
const SITE_KMH := {"": 10.0, "van": 10.0, "camper": 8.0, "moto": 12.0, "tractor": 10.0}
const ACC := {"": 2.4, "van": 1.8, "camper": 1.3, "moto": 3.5, "tractor": 1.0}
const BRAKE := 3.2             # comfortable braking (m/s²) - the planned slowing down before a corner or a stop
const BRAKE_MAX := 6.0
const LAT := 2.2               # sideways acceleration in a corner (m/s²): v = sqrt(LAT · radius)
# where the lamps are (local: front −z): [front z, lamp height, lamp x, rear z, tail height, tail x, blinker x]
const GEO := {"": [-2.13, 0.72, 0.6, 2.14, 0.72, 0.6, 0.78], "van": [-2.13, 0.72, 0.6, 2.31, 0.95, 0.85, 0.9],
		"camper": [-3.63, 0.78, 0.78, 3.12, 0.95, 1.0, 1.08], "moto": [-0.97, 0.9, 0.0, 0.76, 0.82, 0.0, 0.18],
		"tractor": [-1.75, 1.25, 0.35, 1.3, 1.25, 0.6, 0.62]}
# doors: [side (-1 left = driver), hinge z, length, bottom, height]
const DOORS := {"": [[-1, -0.62, 1.05, 0.32, 1.0], [1, -0.62, 1.05, 0.32, 1.0]], "van": [[-1, -1.0, 0.9, 0.35, 1.5], [1, -1.0, 0.9, 0.35, 1.5]],
		"camper": [[-1, -3.45, 1.0, 0.4, 1.6], [1, 0.35, 0.72, 0.4, 1.95]]}
# 3D-4.46: the engine heat comes from the heat table waerme.gd (Waerme.engine: hood, grille, exhaust, tyre, block);
# only the lamp (not in waerme.gd) has its own value here: K above the air right after switching off, cooling time (minutes)
const Waerme = preload("res://scripts/waerme.gd")
const LAMP := [30.0, 8.0]

var cars: Array = []           # one state per vehicle (Dictionary, see _register)
var stats := {"vehicles": 0, "parked": 0, "exits": 0, "returns": 0, "high_beam": 0, "glare_max": 0.0, "bikes_dark": 0}
var _glare := [0.0, 0.0]       # per camera (0 = head, 1 = fixed)
var _glare_pos := [Vector2(0.5, 0.5), Vector2(0.5, 0.5)]
var _t10 := 0.0
var _t2 := 0.0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.randomize()
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		for k in SAVE:
			if d.has(k):
				set(k, d[k] if k == "fz_beam" else bool(d[k]))


func save() -> void:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


func _put(k: String, v) -> void:
	set(k, v)
	save()


func add_controls() -> void:
	var m = main
	var fz := {"sub": "Fahrzeuge"}
	m.add_control("toggle", "fz_real", "Fahrzeuge wie echt: Tempo nach Strasse (50 km/h, auf dem Platz 10 km/h), bremsen vor Kurven, Blinker, Brems- und Rücklichter, Türen auf und zu, Leute steigen aus, der Motor kühlt nach dem Parkieren ab",
			func(): return fz_real, func(v): _put("fz_real", bool(v)), "Besuch", fz)
	m.add_control("select", "fz_beam", "Fernlicht in der Nacht (blendet ab, wenn einer entgegenkommt)",
			func(): return fz_beam, func(v): _put("fz_beam", str(v)), "Besuch", {"sub": "Fahrzeuge", "expert": true,
			"options": [["never", "nie"], ["some", "manchmal"], ["often", "oft"]]})
	m.add_control("toggle", "fz_glare", "Blendung: Scheinwerfer, die in die Kamera leuchten, überstrahlen das Bild",
			func(): return fz_glare, func(v): _put("fz_glare", bool(v)), "Besuch", {"sub": "Fahrzeuge", "expert": true})
	m.add_control("toggle", "fz_return", "Parkierte Autos: nach einigen Minuten kommt jemand zurück und fährt weg",
			func(): return fz_return, func(v): _put("fz_return", bool(v)), "Besuch", {"sub": "Fahrzeuge", "expert": true})
	m.add_control("button", "fz_camper", "Wohnmobil", null, func(): main.car("camper"), "Besuch", fz)
	m.add_control("button", "fz_camper_park", "Wohnmobil kommt an und parkiert", null, func(): arrive("camper"), "Besuch", fz)


# ---- vehicles: register, build ------------------------------------------------------------------------------------
func on_spawn(v) -> void:
	"""main.spawn: every new visitor (cars get their lights, doors and heat; bikes their lamps)"""
	if not fz_real or v == null or v.get("kind") == null or v.preview:
		return
	if v.kind == "car":
		_register(v)
	elif v.kind == "person" and str(v.variant) in ["cyclist", "escooter"]:
		_bike(v)


func build_camper(a) -> void:
	"""a camper van (Wohnmobil): driver's cab with the hot engine in front, living box with alcove over the cab
	(called from actor._build_car, variant «camper»)"""
	var amb: float = main.ambient
	var white: Color = [Color(0.93, 0.93, 0.9), Color(0.9, 0.88, 0.82), Color(0.85, 0.87, 0.9)][randi() % 3]
	var glass := Color(0.15, 0.2, 0.25)
	var br: Node3D = a.body_root
	a._part(br, a._box(2.15, 0.85, 1.55), Vector3(0, 0.82, -2.85), white, amb + 4.0)                        # cab, lower part
	a._part(br, a._box(1.95, 0.7, 0.06), Vector3(0, 1.58, -3.38), glass, amb + 2.0, Vector3(-0.42, 0, 0))   # windscreen
	for s in [-1, 1]:
		a._part(br, a._box(0.05, 0.6, 1.0), Vector3(1.06 * s, 1.55, -2.9), glass, amb + 2.0)               # cab side windows
	a._part(br, a._box(2.15, 0.45, 0.9), Vector3(0, 1.48, -2.45), white, amb + 3.0)                          # cab back / roof joint
	a._part(br, a._box(2.3, 2.5, 5.0), Vector3(0, 1.75, 0.6), white, amb + 3.0)                              # living box
	a._part(br, a._box(2.3, 0.72, 1.35), Vector3(0, 2.62, -2.6), white, amb + 3.0)                           # alcove over the cab
	a._part(br, a._box(2.32, 0.14, 5.0), Vector3(0, 1.15, 0.6), Color(0.35, 0.38, 0.42), amb + 3.0)         # stripe
	for z in [-0.6, 1.9]:
		for s in [-1, 1]:
			a._part(br, a._box(0.04, 0.55, 0.95), Vector3(1.16 * s, 2.05, z), glass, amb + 2.0)            # living windows
	a._part(br, a._box(1.7, 0.08, 0.6), Vector3(0, 3.04, 1.4), Color(0.85, 0.85, 0.85), amb + 2.0)          # roof hatch
	a._part(br, a._box(1.5, 0.5, 0.8), Vector3(0, 0.75, -3.15), white, 75.0)                                 # hot engine (front)
	a._part(br, a._box(2.2, 0.2, 0.14), Vector3(0, 0.45, -3.62), Color(0.15, 0.15, 0.15), amb + 3.0)        # bumpers
	a._part(br, a._box(2.2, 0.2, 0.14), Vector3(0, 0.45, 3.12), Color(0.15, 0.15, 0.15), amb + 3.0)
	a._part(br, a._box(0.12, 0.12, 0.3), Vector3(0.6, 0.35, -1.6), Color(0.2, 0.2, 0.2), 90.0)               # exhaust (under the middle)
	for x in [-0.95, 0.95]:
		for z in [-2.75, 1.85]:
			a._part(br, a._cyl(0.38, 0.38, 0.26, 16), Vector3(x, 0.38, z), Color(0.05, 0.05, 0.05), amb + 12.0, Vector3(0, 0, PI / 2))
			a._part(br, a._cyl(0.2, 0.2, 0.27, 12), Vector3(x, 0.38, z), Color(0.6, 0.6, 0.62), amb + 10.0, Vector3(0, 0, PI / 2))
	for x2 in [-0.78, 0.78]:
		a._headlight(Vector3(x2, 0.78, -3.66))
	a.body_h = 3.0
	a.body_r = 3.4


func _register(a) -> void:
	var vr: String = str(a.variant)
	if not GEO.has(vr):
		vr = ""
	var g: Array = GEO[vr]
	var s := {"a": a, "v": vr, "spots": [], "heads": [], "tails": [], "blinks": [], "doors": [], "inner": null, "inner_mat": null,
			"engine": true, "min": 0.0, "lamp_min": 0.0, "th": [], "brake_t": -10.0, "blink_side": 0, "blink_until": -10.0,
			"flash_until": -10.0, "home_until": -10.0, "high": false, "beam": "", "park": "", "t": 0.0, "persons": [],
			"stay_min": 0.0, "away": Vector3.ZERO, "exit": Vector3.ZERO, "spot": Vector3.ZERO, "leave": [], "free_spot": null,
			"g": g, "last_v": 0.0}
	for l in a.lights:
		if l is SpotLight3D:
			s["spots"].append(l)
		elif l is StandardMaterial3D:
			s["heads"].append(l)
	var ts: float = ROAD_KMH.get(vr, 50.0) / 3.6
	var r := _rng.randf()
	ts *= _rng.randf_range(0.9, 1.06) if r > 0.08 else _rng.randf_range(1.12, 1.25)   # a few drive too fast
	a.speed = ts
	s["vsite"] = SITE_KMH.get(vr, 10.0) / 3.6 * _rng.randf_range(0.85, 1.15)
	var hb: float = {"never": 0.0, "some": 0.3, "often": 0.7}.get(fz_beam, 0.3)
	s["high"] = _rng.randf() < hb
	if s["high"]:
		stats["high_beam"] += 1
	var amb: float = main.ambient
	var br: Node3D = a.body_root
	# rear lights (red), blinkers (orange) - with their own glowing material
	var txs: Array = [float(g[5])] if float(g[5]) == 0.0 else [-float(g[5]), float(g[5])]
	for tx in txs:
		var tm := _glow(Color(0.75, 0.04, 0.03), Color(1.0, 0.05, 0.02))
		var tl: MeshInstance3D = a._part(br, a._box(0.26 if vr != "van" else 0.12, 0.11 if vr != "van" else 0.3, 0.03), Vector3(tx, float(g[4]), float(g[3]) + 0.02), Color(0.75, 0.04, 0.03), amb + 3.0)
		tl.material_override = tm
		s["tails"].append(tm)
	var bx: float = float(g[6])
	for side in [-1, 1]:
		for front in [true, false]:
			var bm := _glow(Color(0.85, 0.45, 0.05), Color(1.0, 0.55, 0.05))
			var z: float = float(g[0]) + 0.03 if front else float(g[3]) + 0.03
			var y: float = float(g[1]) if front else float(g[4]) + (0.14 if vr != "van" else 0.22)
			var bl: MeshInstance3D = a._part(br, a._box(0.1, 0.07, 0.03), Vector3(side * bx, y, z), Color(0.85, 0.45, 0.05), amb + 2.0)
			bl.material_override = bm
			s["blinks"].append([bm, side])
	# doors that open (cars, vans, campers)
	var col := _body_color(a)
	for dd in DOORS.get(vr, []):
		var side_: int = int(dd[0])
		var hx: float = 0.9 if vr == "" else (0.99 if vr == "van" else 1.17)
		if vr == "camper" and side_ < 0:
			hx = 1.09
		var pv := Node3D.new()
		pv.position = Vector3(side_ * hx, 0, float(dd[1]))
		br.add_child(pv)
		var ln: float = float(dd[2])
		var h: float = float(dd[4])
		var low_h: float = h * (0.55 if vr != "camper" or side_ < 0 else 1.0)
		a._part(pv, a._box(0.04, low_h, ln), Vector3(0, float(dd[3]) + low_h * 0.5, ln * 0.5), col, amb + 3.0)
		if low_h < h:
			a._part(pv, a._box(0.03, h - low_h - 0.06, ln - 0.1), Vector3(0, float(dd[3]) + low_h + (h - low_h) * 0.5, ln * 0.5), Color(0.15, 0.2, 0.25), amb + 2.0)
		s["doors"].append({"n": pv, "side": side_, "k": 0.0, "want": 0.0, "z": float(dd[1]) + ln * 0.5, "x": side_ * hx})
	if not Quality.lite() and vr in ["", "van", "camper"]:
		var om := OmniLight3D.new()                         # light inside (when a door is open at night)
		om.position = Vector3(0, 1.25, float(g[0]) + 1.6)
		om.omni_range = 2.6
		om.light_energy = 0.0
		om.light_color = Color(1.0, 0.85, 0.6)
		om.shadow_enabled = false
		br.add_child(om)
		s["inner"] = om
	# own thermal materials for the hot parts (they cool down when the engine is off)
	if main.get("waerme_welt") == null:
		s["th"] = _hot_parts(a, amb)
	cars.append(s)
	stats["vehicles"] += 1


func _glow(albedo: Color, em: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = albedo
	m.emission_enabled = true
	m.emission = em
	m.emission_energy_multiplier = 0.0
	return m


func _body_color(a) -> Color:
	"""the colour of the biggest visible part (the body)"""
	var best := 0.0
	var c := Color(0.7, 0.7, 0.72)
	for ch in a.body_root.get_children():
		if ch is MeshInstance3D and ch.layers == 1 and ch.mesh is BoxMesh and ch.material_override is StandardMaterial3D:
			var sz: Vector3 = (ch.mesh as BoxMesh).size
			var vol := sz.x * sz.y * sz.z
			if vol > best:
				best = vol
				c = (ch.material_override as StandardMaterial3D).albedo_color
	return c


func _hot_parts(a, amb: float) -> Array:
	"""the thermal twins (layer 2) of the engine, exhaust, tyres and headlight glass get their own material"""
	var by_part := {}
	for ch in _all(a.body_root):
		if not (ch is MeshInstance3D and ch.layers == 2 and ch.material_override is ShaderMaterial):
			continue
		var tv = (ch.material_override as ShaderMaterial).get_shader_parameter("temp")
		if tv == null:
			continue
		var t: float = float(tv)
		var part := ""
		if t >= 85.0:
			part = "exhaust"
		elif t >= 60.0:
			part = "block" if str(a.variant) in ["tractor", "moto"] else "hood"
		elif absf(t - (amb + 30.0)) < 0.6:
			part = "lamp"
		elif t > amb + 9.4 and t < amb + 12.6:
			part = "tyre"
		if part == "":
			continue
		if not by_part.has(part):
			var m := ShaderMaterial.new()
			m.shader = (ch.material_override as ShaderMaterial).shader
			m.set_shader_parameter("temp", _engine_t(part, 0.0, amb))
			m.set_shader_parameter("spread", 0.5)
			by_part[part] = m
		ch.material_override = by_part[part]
	var out := []
	for p in by_part:
		out.append([by_part[p], p])
	return out


func _all(n: Node) -> Array:
	var out := []
	for c in n.get_children():
		out.append(c)
		out.append_array(_all(c))
	return out


func _engine_t(part: String, minutes: float, amb: float) -> float:
	if part == "lamp":
		return amb + float(LAMP[0]) * exp(-maxf(0.0, minutes) / float(LAMP[1]))
	return Waerme.engine(part, minutes, amb)


func _bike(v) -> void:
	"""bikes and e-scooters: lamps front and back (the e-scooter gets them here), a few ride without light at night"""
	if str(v.variant) == "escooter" and v.bike_lamp.is_empty():
		var br: Node3D = v.body_root
		var flm := _glow(Color(1, 1, 0.95), Color(1, 1, 0.95))
		var fl := MeshInstance3D.new()
		fl.mesh = v._sph(0.03)
		fl.material_override = flm
		fl.position = Vector3(0, 1.0, -0.47)
		br.add_child(fl)
		var rlm := _glow(Color(0.9, 0.05, 0.05), Color(1, 0.05, 0.05))
		var rl := MeshInstance3D.new()
		rl.mesh = v._sph(0.025)
		rl.material_override = rlm
		rl.position = Vector3(0, 0.22, 0.42)
		br.add_child(rl)
		var bl := SpotLight3D.new()
		bl.spot_range = 10.0
		bl.spot_angle = 24.0
		bl.position = Vector3(0, 1.0, -0.5)
		bl.rotation = Vector3(-0.2, 0, 0)
		bl.shadow_enabled = false
		br.add_child(bl)
		v.bike_lamp = [bl, flm, rlm]
	var e_bike: bool = str(v.variant) == "cyclist" and _rng.randf() < 0.3
	v.speed = _rng.randf_range(6.0, 7.0) if e_bike else (_rng.randf_range(4.2, 5.5) if str(v.variant) == "cyclist" else _rng.randf_range(4.8, 5.5))
	if main.is_dark() and _rng.randf() < (0.15 if str(v.variant) == "cyclist" else 0.2) and not v.bike_lamp.is_empty():
		v.bike_lamp[0].light_energy = 0.0                  # rides without light
		v.bike_lamp[1].emission_energy_multiplier = 0.0
		v.bike_lamp[2].emission_energy_multiplier = 0.0
		v.bike_lamp = []
		stats["bikes_dark"] += 1
	else:
		v.set_night(main.is_dark())


# ---- driving (from actor._step) -----------------------------------------------------------------------------------
func _st(a) -> Variant:
	for s in cars:
		if s["a"] == a:
			return s
	return null


func drive(a, dt: float, want: float, dist: float) -> float:
	"""the new speed of a car: road or place speed, slows down before corners and stops, accelerates like a car"""
	var s = _st(a)
	if s == null:
		return move_toward(a.cur_speed, want, dt * 3.0 * maxf(1.0, want))
	var ts: float = main.time_scale_visitors()
	var top: float = want
	if _on_site(a.position) or _on_site(a.target):
		top = minf(top, float(s["vsite"]) * ts)
	# look ahead over the next points: at each the speed of its corner (a stop = 0), reachable with comfortable braking
	var allow: float = top
	var pts: Array = [a.target]
	var stop_i := -1
	for i in range(mini(a.route.size(), 5)):
		var nx = a.route[i]
		var np: Vector3 = nx[0] if typeof(nx) == TYPE_ARRAY else nx
		if typeof(nx) == TYPE_ARRAY and np.distance_to(pts[-1]) < 1.0:
			stop_i = pts.size() - 1                     # waits at the last point
			break
		pts.append(np)
	var along: float = dist
	var prev: Vector3 = a.position
	var turn := 0
	for i in range(pts.size()):
		if i > 0:
			along += (pts[i] as Vector3).distance_to(pts[i - 1])
		var vc: float = top
		if i == stop_i:
			vc = 0.0
		elif i + 1 < pts.size():
			var r3 := _corner3(prev, pts[i], pts[i + 1])
			vc = minf(top, sqrt(LAT * 10.0 / maxf(r3.x, 0.05)))
			if r3.x > 0.6 and along < 45.0 and turn == 0:
				turn = int(r3.y)
		allow = minf(allow, sqrt(vc * vc + 2.0 * BRAKE * maxf(0.0, along - 0.4)))
		prev = pts[i]
		if along > 120.0:
			break
	var goal: float = minf(top, allow)
	var cur: float = a.cur_speed
	var acc: float = float(ACC.get(s["v"], 2.4))
	var nv: float = move_toward(cur, goal, dt * (acc if goal > cur else BRAKE_MAX))
	var t: float = main.now()
	if nv < cur - dt * 0.8 or (nv < 0.3 and s["engine"]):
		s["brake_t"] = t + 0.35
	if turn != 0:
		s["blink_side"] = turn
		s["blink_until"] = t + 1.2
	return nv


func _corner3(p0: Vector3, p1: Vector3, p2: Vector3) -> Vector2:
	"""angle between the leg p0 → p1 and the next p1 → p2 (rad) and the side of the turn (+1 right, -1 left)"""
	var d1: Vector3 = p1 - p0
	var d2: Vector3 = p2 - p1
	d1.y = 0
	d2.y = 0
	if d1.length() < 0.1 or d2.length() < 0.1:
		return Vector2.ZERO
	var th := d1.normalized().angle_to(d2.normalized())
	var cr: float = d1.cross(d2).y
	return Vector2(th, 1.0 if cr < 0.0 else -1.0)


func lane_z(dirx: float) -> float:
	"""main.car(): right-hand traffic - driving towards +x on the lane at +z of the middle of the road"""
	return _road_c() + 1.25 * signf(dirx)


func _road_c() -> float:
	return float(main.scenes.data.get("road_z", -27.8)) - 1.2


func _on_site(p: Vector3) -> bool:
	"""on the place (campsite lane, car park, shoulder) - not on the road"""
	if not main.scenes.data.has("road_z") or main.scenes.data.has("road_line"):
		return false
	return absf(p.z - _road_c()) > 4.2


# ---- every frame: lights, doors, parking, heat, glare ---------------------------------------------------------------
func _process(dt: float) -> void:
	if main == null or cars.is_empty():
		if _glare[0] > 0.0 or _glare[1] > 0.0:
			_set_glare([0.0, 0.0])
		return
	var t: float = main.now()
	var keep := []
	for s in cars:
		var a = s["a"]
		if not is_instance_valid(a) or a.is_queued_for_deletion():
			if s["free_spot"] != null and main.scenes.data.has("free"):
				main.scenes.data["free"].append(s["free_spot"])    # the spot is free again
			continue
		keep.append(s)
		if not fz_real:
			continue
		_doors(s, dt)
		_park_tick(s, t)
	cars = keep
	if not fz_real:
		return
	_t10 -= dt
	if _t10 <= 0.0:
		_t10 = 0.1
		for s in cars:
			_lights(s, t)
		_glare_tick()
	_t2 -= dt
	if _t2 <= 0.0:
		var dmin: float = (0.5 - _t2) * maxf(1.0, float(main.speed)) / 60.0
		_t2 = 0.5
		_heat(dmin)


func _beam(s, dark: bool) -> String:
	if not s["engine"]:
		return "low" if main.now() < float(s["home_until"]) and dark else "off"
	if not dark:
		return "drl"
	if not s["high"] or _on_site(s["a"].position):
		return "low"
	var a = s["a"]
	var fw: Vector3 = -a.global_transform.basis.z
	for o in cars:                                      # dims when somebody comes the other way
		if o == s or not is_instance_valid(o["a"]):
			continue
		var d: Vector3 = o["a"].global_position - a.global_position
		if d.length() < 160.0 and d.dot(fw) > 0.0 and (-o["a"].global_transform.basis.z).dot(fw) < -0.5:
			return "low"
	return "high"


func _lights(s, t: float) -> void:
	var dark: bool = main.light_level() < 0.2
	var bm := _beam(s, dark)
	s["beam"] = bm
	var lite: bool = Quality.lite()
	var i := 0
	for sp in s["spots"]:
		var l: SpotLight3D = sp
		if bm == "low":
			l.light_energy = 3.5 * (1.4 if lite else 1.0)
			l.spot_range = 55.0
			l.spot_angle = 30.0
			l.rotation = Vector3(-0.04, -0.03 if l.position.x < 0 else 0.03, 0)
		elif bm == "high":
			l.light_energy = 9.0 * (1.4 if lite else 1.0)
			l.spot_range = 120.0
			l.spot_angle = 15.0
			l.rotation = Vector3.ZERO
		else:
			l.light_energy = 0.0
		if lite and i > 0:
			l.light_energy = 0.0                           # Lite: one lamp light per vehicle
		i += 1
	for hm in s["heads"]:
		(hm as StandardMaterial3D).emission_energy_multiplier = {"low": 4.0, "high": 7.0, "drl": 1.3}.get(bm, 0.0)
	var braking: bool = t < float(s["brake_t"]) and s["engine"]
	var tail_on: bool = s["engine"] and dark
	for tm in s["tails"]:
		(tm as StandardMaterial3D).emission_energy_multiplier = 8.0 if braking else (2.2 if tail_on else 0.0)
	var on := fmod(t * 1.5, 1.0) < 0.5
	var flash: bool = t < float(s["flash_until"]) and fmod(t * 3.0, 1.0) < 0.5
	for b in s["blinks"]:
		var lit: bool = flash or (t < float(s["blink_until"]) and int(b[1]) == int(s["blink_side"]) and on)
		(b[0] as StandardMaterial3D).emission_energy_multiplier = 6.0 if lit else 0.0
	var open := false
	for d in s["doors"]:
		open = open or float(d["k"]) > 0.05
	if s["inner"] != null:
		(s["inner"] as OmniLight3D).light_energy = 0.9 if open and dark else 0.0


func _doors(s, dt: float) -> void:
	for d in s["doors"]:
		var k: float = move_toward(float(d["k"]), float(d["want"]), dt * 1.4)
		d["k"] = k
		(d["n"] as Node3D).rotation.y = float(d["side"]) * 1.15 * (k * k * (3.0 - 2.0 * k))


func door(a, side: int, open: bool) -> void:
	"""open / close the door on this side (-1 left = driver, +1 right)"""
	var s = _st(a)
	if s == null:
		return
	for d in s["doors"]:
		if int(d["side"]) == side:
			d["want"] = 1.0 if open else 0.0
			return


func side_towards(a, p: Vector3) -> int:
	"""the door on the side of p (-1 left, +1 right)"""
	var loc: Vector3 = a.global_transform.affine_inverse() * p
	return 1 if loc.x > 0.0 else -1


func exit_point(a, side: int) -> Vector3:
	"""where somebody stands who gets out on this side"""
	var s = _st(a)
	var z := -0.1
	var x := 1.5
	if s != null:
		for d in s["doors"]:
			if int(d["side"]) == side:
				z = float(d["z"]) + 0.2
				x = absf(float(d["x"])) + 0.65
	return a.global_transform * Vector3(side * x, 0, z)


func _heat(dmin: float) -> void:
	var amb: float = main.ambient
	for s in cars:
		if s["engine"]:
			s["min"] = maxf(0.0, float(s["min"]) - dmin * 3.0)   # the engine runs: warms up again (3× quicker than it cools)
		else:
			s["min"] = float(s["min"]) + dmin
		var lamp_on: bool = s["beam"] in ["low", "high"]
		s["lamp_min"] = 0.0 if lamp_on else float(s["lamp_min"]) + dmin
		for mp in s["th"]:
			var part: String = mp[1]
			(mp[0] as ShaderMaterial).set_shader_parameter("temp", _engine_t(part, float(s["lamp_min"]) if part == "lamp" else float(s["min"]), amb))


# ---- glare: headlights into the lens -------------------------------------------------------------------------------
func _glare_tick() -> void:
	var out := [0.0, 0.0]
	if not fz_glare or main.cams.size() < 2:
		_set_glare(out)
		return
	for i in range(2):
		var cam: Camera3D = main.cams[i]
		if cam == null:
			continue
		var cp: Vector3 = cam.global_position
		var best := 0.0
		var bpos := Vector2(0.5, 0.5)
		for s in cars:
			var bm: String = s["beam"]
			if bm != "low" and bm != "high":
				continue
			var a = s["a"]
			var g: Array = s["g"]
			var lamp: Vector3 = a.global_transform * Vector3(0, float(g[1]), float(g[0]))
			var fw: Vector3 = -a.global_transform.basis.z
			var to := cp - lamp
			var d := to.length()
			if d < 1.0 or d > 160.0:
				continue
			var ca: float = fw.dot(to / d)
			if ca < 0.6:
				continue
			var ang: float = rad_to_deg(acos(clampf(ca, -1.0, 1.0)))
			var k: float
			if bm == "high":
				k = pow(clampf(1.0 - ang / 14.0, 0.0, 1.0), 1.5) * clampf(pow(55.0 / d, 1.2), 0.0, 1.2)
			else:
				var el: float = rad_to_deg(asin(clampf(to.y / d, -1.0, 1.0)))   # low beam: little light above the cut-off
				k = pow(clampf(1.0 - ang / 24.0, 0.0, 1.0), 1.5) * clampf(pow(22.0 / d, 1.3), 0.0, 1.2) * (0.3 if el > 1.2 else 0.85)
			if k <= best or not cam.is_position_in_frustum(lamp):
				continue
			if not main.line_free(cp, lamp + fw * 0.4):
				continue
			best = k
			var vs: Vector2 = cam.get_viewport().get_visible_rect().size
			bpos = cam.unproject_position(lamp) / Vector2(maxf(1.0, vs.x), maxf(1.0, vs.y))
		out[i] = clampf(best * 0.75, 0.0, 0.8)
		_glare_pos[i] = bpos
	_set_glare(out)


func _set_glare(g: Array) -> void:
	for i in range(mini(2, main.lens_mats.size())):
		if float(g[i]) > 0.01 or float(_glare[i]) > 0.01:
			var m: ShaderMaterial = main.lens_mats[i]
			m.set_shader_parameter("glare", float(g[i]))
			m.set_shader_parameter("glare_pos", _glare_pos[i])
		_glare[i] = float(g[i])
	stats["glare_max"] = maxf(float(stats["glare_max"]), maxf(float(g[0]), float(g[1])))


func glaring(i: int) -> bool:
	"""main._update_lens leaves the glare of camera i alone while headlights blind it"""
	return fz_real and i < 2 and float(_glare[i]) > 0.01


func glare_now(i := 0) -> float:
	return float(_glare[i]) if i < 2 else 0.0


# ---- parking: arrive, get out, come back, drive away --------------------------------------------------------------
func arrive(kind := "car") -> Node3D:
	"""a car (or camper) turns off the road, parks, the doors open, 1-3 people get out and walk away"""
	if not fz_real:
		main.visit("car_park" if kind == "car" else kind)
		return null
	var data: Dictionary = main.scenes.data
	var side := 1.0 if _rng.randf() < 0.5 else -1.0
	var a = null
	var spot: Vector3
	var leave := []
	var free_spot = null
	if data.has("free") and not (data["free"] as Array).is_empty() and kind == "car" and main.scene == "parkplatz":
		var fr: Array = data["free"]
		free_spot = fr[_rng.randi() % fr.size()]
		fr.erase(free_spot)
		spot = free_spot
		var lane := Vector3(spot.x, 0, -15.0)
		a = main.spawn(kind, Vector3(90, 0, -31.0), Vector3(26, 0, -31.0))
		a.route = [Vector3(26, 0, -15), lane + Vector3(-3.0 if spot.x > 26 else 3.0, 0, 0), spot, [spot, 1.0e6, 0.0]]
		leave = [lane, Vector3(-26, 0, -15), Vector3(-26, 0, -32.5), Vector3(-90, 0, -32.5)]
	elif data.has("road_z") and not data.has("road_line"):
		var zc := _road_c()
		var toward: float = 1.0 if zc < float(main.rig.global_position.z) else -1.0   # the side of the road towards the camera
		var dirx := toward                               # right-hand traffic: it parks on its right side (towards the camera)
		var lane_z: float = zc + 1.25 * dirx
		var sx: float = float(main.rig.global_position.x) + _rng.randf_range(-12.0, 12.0)
		var sz: float = zc + toward * (3.4 if kind != "camper" else 4.0)
		for i in range(10):                              # a free place at the side of the road
			if not main.blocked(Vector2(sx, sz), 2.6 if kind != "camper" else 3.8, false):
				break
			sx += 4.0 * (1.0 if i % 2 == 0 else -1.0) * (i + 1)
		spot = Vector3(sx, 0, sz)
		a = main.spawn(kind, Vector3(sx - dirx * 90.0, 0, lane_z), Vector3(sx - dirx * 22.0, 0, lane_z))
		a.route = [Vector3(sx - dirx * 11.0, 0, lane_z), Vector3(sx - dirx * 5.5, 0, (lane_z + sz) * 0.5), spot, [spot, 1.0e6, 0.0]]
		leave = [Vector3(sx + dirx * 7.0, 0, (lane_z + sz) * 0.5), Vector3(sx + dirx * 16.0, 0, lane_z), Vector3(sx + dirx * 90.0, 0, lane_z)]
	else:                                                # no straight road: from far in front to a place 14 m in front
		var base: Vector3 = main.rig.global_position
		var az: float = -rad_to_deg(main.rig.rotation.y) + _rng.randf_range(-25.0, 25.0)
		spot = main.free_spot(base + main.pos_of(az, 14.0), 2.4, false)
		var far: Vector3 = base + main.pos_of(az + 10.0, 70.0)
		a = main.spawn(kind, Vector3(far.x, 0, far.z), Vector3(spot.x, 0, spot.z))
		a.route = [[Vector3(spot.x, 0, spot.z), 1.0e6, 0.0]]
		leave = [Vector3(far.x, 0, far.z)]
	if a == null:
		return null
	var s = _st(a)
	if s == null:
		return a
	s["park"] = "arrive"
	s["spot"] = spot
	s["leave"] = leave
	s["free_spot"] = free_spot
	return a


func leave(a) -> void:
	"""somebody comes back to the car (or: the car simply drives away)"""
	var s = _st(a)
	if s == null:
		return
	if s["park"] == "parked":
		s["stay_min"] = 1.0e6
		_come_back(s)


func _park_tick(s, t: float) -> void:
	var a = s["a"]
	var ph: String = s["park"]
	if ph == "":
		return
	if ph == "arrive":
		var ds: float = a.position.distance_to(s["spot"])
		if ds < 40.0 and ds > 2.0:
			s["blink_side"] = side_towards(a, s["spot"])  # signals before it turns off to park
			s["blink_until"] = t + 0.5
		if ds < 0.6 and a.cur_speed < 0.25:
			s["park"] = "stopped"
			s["t"] = t
	elif ph == "stopped":
		var dt_: float = t - float(s["t"])
		if dt_ > 1.0 and s["engine"]:
			s["engine"] = false                          # engine off: the heat now cools down
			s["home_until"] = t + 25.0                    # «coming home»: the headlights stay on for a while
			s["t"] = t
			_get_out(s)
	elif ph == "parked":
		var min_: float = float(s["stay_min"]) - (main.now() - float(s["t"])) * maxf(1.0, float(main.speed)) / 60.0
		if fz_return and min_ <= 0.0 and float(s["stay_min"]) < 1.0e5:
			_come_back(s)
	elif ph == "leaving":
		if t - float(s["t"]) > 3.5:
			s["park"] = ""
			a.route = s["leave"].duplicate()
			a.wait_until = 0.0
			a.route.push_front(s["spot"] + (-a.global_transform.basis.z) * 3.0)
			s["blink_side"] = -1 if a.route.size() > 1 else 0
			s["blink_until"] = t + 3.0


func _get_out(s) -> void:
	var a = s["a"]
	var n: int = [1, 1, 2, 2, 3][_rng.randi() % 5]
	if s["v"] == "camper":
		n = mini(n, 2)
	var sides := [-1, 1, 1]
	var fw: Vector3 = -a.global_transform.basis.z
	var away_dir: Vector3 = (fw if _rng.randf() < 0.5 else -fw)
	var away: Vector3 = a.global_position + away_dir * 45.0 + fw.cross(Vector3.UP) * _rng.randf_range(-6.0, 6.0)
	s["away"] = away
	var data_tr = main.testrun if main.testrun != null and main.testrun.running else null
	for i in range(n):
		var sd: int = sides[i]
		var delay: float = 1.0 + i * 0.9
		get_tree().create_timer(delay).timeout.connect(func():
			if not is_instance_valid(a):
				return
			door(a, sd, true)
			get_tree().create_timer(0.9).timeout.connect(func():
				if not is_instance_valid(a):
					return
				var ex := exit_point(a, sd)
				var p = main.spawn("person", ex, away + Vector3(i * 0.9, 0, 0))
				if p != null:
					p.next_idle = main.now() + 6.0
					if main.is_dark() and _rng.randf() < 0.4:
						p.phone_out = true
					stats["exits"] += 1
					s["persons"].append(p)
					if data_tr != null and is_instance_valid(data_tr) and data_tr.running:
						data_tr._note_visitor(p, "person")       # the people who get out are the truth of a test run
				get_tree().create_timer(1.8).timeout.connect(func():
					if is_instance_valid(a):
						door(a, sd, false))))
	get_tree().create_timer(1.0 + n * 0.9 + 3.6).timeout.connect(func():
		if is_instance_valid(a) and not s["engine"]:
			s["flash_until"] = main.now() + 0.7          # locked: the blinkers flash
			s["park"] = "parked"
			s["t"] = main.now()
			s["stay_min"] = _rng.randf_range(4.0, 10.0) if not (main.testrun != null and main.testrun.running) else 0.7
			stats["parked"] += 1)


func _come_back(s) -> void:
	var a = s["a"]
	s["park"] = "back"
	var ex := exit_point(a, -1)
	var p = main.spawn("person", s["away"], ex)
	if p == null:
		return
	p.next_idle = main.now() + 999.0
	stats["returns"] += 1
	if main.testrun != null and main.testrun.running:
		main.testrun._note_visitor(p, "person")
	if main.is_dark() and _rng.randf() < 0.5:
		p.add_torch()
	p.route = [[ex, 1.2, 0.0, a.global_position]]
	_wait_for(p, ex, func():
		if not is_instance_valid(a):
			return
		s["flash_until"] = main.now() + 0.4              # unlocked
		door(a, -1, true)
		get_tree().create_timer(1.3).timeout.connect(func():
			if is_instance_valid(p):
				p.done = true
				p.queue_free()                          # got in
			get_tree().create_timer(1.0).timeout.connect(func():
				if not is_instance_valid(a):
					return
				door(a, -1, false)
				s["engine"] = true                      # engine on, lights on
				s["park"] = "leaving"
				s["t"] = main.now())))


func _wait_for(p, at: Vector3, then: Callable, max_s := 120.0) -> void:
	var t0: float = main.now()
	while is_instance_valid(p) and not p.done and main.now() - t0 < max_s:
		if p.position.distance_to(at) < 0.7:
			then.call()
			return
		await get_tree().create_timer(0.25).timeout


# ---- test runs (testrun.gd) ---------------------------------------------------------------------------------------
const TEST_KINDS := ["fz_pass", "fz_pass_high", "fz_toward", "fz_arrive", "fz_moto", "fz_bike", "fz_trotti", "fz_camper"]


func is_test_kind(k: String) -> bool:
	return k in TEST_KINDS


func test_visit(k: String, tr):
	"""one visitor of the test plan «fahrzeuge»: returns the actor that counts as truth (bikes: the rider = a person) or
	null (vehicles are no persons - the people who get out count, they are noted when they get out)"""
	match k:
		"fz_pass", "fz_pass_high", "fz_moto", "fz_camper":
			_pass_in_view({"fz_moto": "moto", "fz_camper": "camper"}.get(k, "car"), k == "fz_pass_high")
		"fz_toward":                                     # drives towards the camera, turns off 11 m before it
			_toward()
		"fz_arrive":
			var a = arrive("car")
			var s = _st(a) if a != null else null
			if s != null:
				s["high"] = false
		"fz_bike", "fz_trotti":
			var rt: Array = tr._route(tr.visit_i, tr.PHASES[tr.phase])
			return main.spawn("cyclist" if k == "fz_bike" else "e_trotti", rt[0], rt[1])
	return null


func _pass_in_view(kind: String, high: bool):
	"""a vehicle crosses the picture of the head camera: on the road of the scene when the camera looks at it (up to 55 m),
	else on a lane 24 m in front (from 70° left to 70° right)"""
	var v = null
	var cam: Camera3D = main.cams[0]
	var road_ok := false
	if main.scenes.data.has("road_line"):
		road_ok = true
	elif main.scenes.data.has("road_z"):
		var fw: Vector3 = -cam.global_transform.basis.z
		fw.y = 0.0
		var dz: float = _road_c() - cam.global_position.z
		if absf(fw.z) > 0.2 and dz / fw.z > 0.0:
			var hit: Vector3 = cam.global_position + fw.normalized() * (dz / fw.normalized().z)
			hit.y = 0.0
			road_ok = hit.distance_to(Vector3(cam.global_position.x, 0, cam.global_position.z)) < 55.0
	if road_ok:
		var before: int = main.visitors.get_child_count()
		main.car(kind)
		if main.visitors.get_child_count() > before:
			v = main.visitors.get_child(main.visitors.get_child_count() - 1)
	else:
		var base: Vector3 = main.rig.global_position
		var az: float = -rad_to_deg(cam.global_rotation.y)
		var p1: Vector3 = base + main.pos_of(az - 70.0, 24.0 / cos(deg_to_rad(70.0)))
		var p2: Vector3 = base + main.pos_of(az + 70.0, 24.0 / cos(deg_to_rad(70.0)))
		if _rng.randf() < 0.5:
			var t_ := p1
			p1 = p2
			p2 = t_
		v = main.spawn(kind, Vector3(p1.x, 0, p1.z), Vector3(p2.x, 0, p2.z))
	var s = _st(v) if v != null else null
	if s != null:
		s["high"] = high
	return v


func _toward():
	"""headlights come straight at the camera, then the car turns off (a classic: the light sweeps over the place)"""
	var base: Vector3 = main.rig.global_position
	var az: float = -rad_to_deg(main.cams[0].global_rotation.y) + _rng.randf_range(-8.0, 8.0)
	var far: Vector3 = base + main.pos_of(az, 70.0)
	var near: Vector3 = base + main.pos_of(az, 11.0)
	var off: Vector3 = base + main.pos_of(az + 90.0 * (1.0 if _rng.randf() < 0.5 else -1.0), 40.0)
	var v = main.spawn("car", Vector3(far.x, 0, far.z), Vector3(near.x, 0, near.z))
	if v != null:
		v.route = [Vector3(off.x, 0, off.z)]
		var s = _st(v)
		if s != null:
			s["high"] = false
	return v


func cause(tr) -> String:
	"""a false push while a vehicle was in the picture of the head camera (or its headlights blinded it)"""
	if float(_glare[0]) > 0.08:
		return "Fahrzeug (Scheinwerfer blenden)"
	var cam: Camera3D = main.cams[0]
	for s in cars:
		var a = s["a"]
		if is_instance_valid(a) and cam.is_position_in_frustum(a.global_position + Vector3(0, 0.8, 0)) and a.global_position.distance_to(cam.global_position) < 70.0:
			return "Fahrzeug (Licht und Bewegung)" if s["beam"] in ["low", "high"] else "Fahrzeug (Bewegung)"
	return ""


func report_extra(tr) -> Dictionary:
	var f := 0
	var ok := 0
	var fz_false := 0
	for p in tr.pushes:
		if bool(p.get("dup", false)):
			continue
		if bool(p.get("ok", false)):
			ok += 1
		else:
			f += 1
			if str(p.get("who", "")).begins_with("Fahrzeug"):
				fz_false += 1
	return {"art": "fahrzeuge", "fahrzeuge": int(stats["vehicles"]), "fernlicht": int(stats["high_beam"]), "ausgestiegen": int(stats["exits"]),
			"zurueck": int(stats["returns"]), "blendung_max": snappedf(float(stats["glare_max"]), 0.01), "velos_ohne_licht": int(stats["bikes_dark"]),
			"push_falsch": f, "push_falsch_fahrzeug": fz_false, "push_richtig": ok}


func reset_stats() -> void:
	for k in stats:
		stats[k] = 0.0 if k == "glare_max" else 0


# ---- /control {"action": "fahrzeuge"} -------------------------------------------------------------------------------
func info() -> Dictionary:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	var lst := []
	for s in cars:
		var a = s["a"]
		if not is_instance_valid(a):
			continue
		var hood := 0.0
		for mp in s["th"]:
			if mp[1] in ["hood", "block"]:
				hood = float((mp[0] as ShaderMaterial).get_shader_parameter("temp"))
		var dk := []
		for dd in s["doors"]:
			dk.append(snappedf(float(dd["k"]), 0.01))
		lst.append({"variant": s["v"], "kmh": snappedf(float(a.cur_speed) * 3.6, 0.1), "beam": s["beam"], "engine": s["engine"],
				"park": s["park"], "min_off": snappedf(float(s["min"]), 0.01), "hood_c": snappedf(hood, 0.1), "doors": dk,
				"brake": main.now() < float(s["brake_t"]), "blink": int(s["blink_side"]) if main.now() < float(s["blink_until"]) else 0,
				"pos": [snappedf(a.global_position.x, 0.1), snappedf(a.global_position.z, 0.1)], "on_site": _on_site(a.position)})
	d["cars"] = lst
	d["glare"] = [snappedf(float(_glare[0]), 0.01), snappedf(float(_glare[1]), 0.01)]
	d["stats"] = stats
	d["waerme"] = "waerme.gd"
	d["lite"] = Quality.lite()
	return d


func control(d: Dictionary) -> Dictionary:
	"""{do: info | set (key, value) | spawn (kind: car, van, camper, moto, tractor, cyclist, e_trotti) | arrive (kind) |
	leave | toward | reset}"""
	var op := str(d.get("do", "info"))
	if op == "set" and str(d.get("key", "")) in SAVE:
		var k := str(d["key"])
		_put(k, str(d.get("value", "some")) if k == "fz_beam" else bool(d.get("value", true)))
	elif op == "spawn":
		var kd := str(d.get("kind", "car"))
		if kd in ["car", "van", "camper", "moto", "tractor"]:
			if bool(d.get("high", false)):
				_pass_in_view(kd, true)
			else:
				main.car(kd)
		else:
			main.visit(kd)
	elif op == "arrive":
		arrive(str(d.get("kind", "car")))
	elif op == "toward":
		_toward()
	elif op == "leave":
		for s in cars:
			if s["park"] == "parked":
				leave(s["a"])
	elif op == "reset":
		reset_stats()
	elif op != "info":
		return {"ok": false, "error": "do: info | set | spawn | arrive | toward | leave | reset"}
	var r := info()
	r["ok"] = true
	return r
