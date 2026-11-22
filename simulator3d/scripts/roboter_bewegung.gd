extends RefCounted
## Roboter-Labor: Bewegungen des Segment-Roboters (roboter_modell.gd) - Bein-Rechnung (inverse Kinematik), fertige Posen.
## Stufe 2 / 3 bauen hier weiter (ganze Abläufe, Gangarten, automatische Steuerung, Ring rollen).
## Alle Winkel in Grad, Servo-Kennungen wie roboter_modell.gd servo_id (sy3, sp3, hy2l, hp2l, kn2l, pan, riegel).
## Vorzeichen: sp + = hoch (Richtung Ring, Rücken innen), sy + = Kette biegt nach rechts (Kopf rechts), hy + = Fuss nach
## vorne, hp + = Oberschenkel hoch, kn + = Unterschenkel nach unten.

const POSEN := [["gerade", "Gerade"], ["kurve_links", "Kurve links"], ["kurve_rechts", "Kurve rechts"], ["bogen", "Bogen"],
		["ring", "Ring"], ["eingeklappt", "Beine eingeklappt"]]

var m                                  # roboter_modell.gd
var hoehe := 0.9                       # Körpermitte über dem Boden in Einheiten der Vorlage (Startwert)
var spreiz := 1.25                     # Fuss seitlich ausserhalb des Segments (Einheiten)


func leg_ik(s: int, foot: Vector3) -> Array:
	"""[hy, hp, kn] in degrees so that the foot of the leg on side s is at «foot» (segment frame, metres); knee up"""
	var w: float = m.u("halbe_breite")
	var l1: float = m.u("oberschenkel")
	var l2: float = m.u("unterschenkel")
	var d := foot - Vector3(0, 0, s * w)
	var a := atan2(d.x, s * d.z)
	var r := sqrt(d.x * d.x + d.z * d.z)
	var y := d.y
	var dd := clampf(sqrt(r * r + y * y), absf(l1 - l2) + 1e-4, l1 + l2 - 1e-4)
	var cg := clampf((dd * dd - l1 * l1 - l2 * l2) / (2.0 * l1 * l2), -1.0, 1.0)
	var g := acos(cg)
	var b := atan2(y, r) + atan2(l2 * sin(g), l1 + l2 * cos(g))
	return [rad_to_deg(a), rad_to_deg(b), rad_to_deg(g)]


func leg_fk(s: int, hy: float, hp: float, kn: float) -> Vector3:
	"""foot in the segment frame (metres) for the three leg angles (degrees) - the same maths as roboter_modell.fk"""
	var w: float = m.u("halbe_breite")
	var l1: float = m.u("oberschenkel")
	var l2: float = m.u("unterschenkel")
	var fr := Transform3D(Basis(), Vector3(0, 0, s * w)) * Transform3D(Basis(Vector3.UP, s * deg_to_rad(hy)), Vector3.ZERO) \
			* Transform3D(Basis(Vector3.RIGHT, -s * deg_to_rad(hp)), Vector3.ZERO)
	var tb := fr * Transform3D(Basis(), Vector3(0, 0, s * l1)) * Transform3D(Basis(Vector3.RIGHT, s * deg_to_rad(kn)), Vector3.ZERO)
	return tb * Vector3(0, 0, s * l2)


func _legs(d: Dictionary, i: int, foot_l: Vector3, foot_r: Vector3) -> void:
	for s in [-1, 1]:
		var a := leg_ik(s, foot_l if s < 0 else foot_r)
		var sd := "l" if s < 0 else "r"
		d["hy%d%s" % [i, sd]] = a[0]
		d["hp%d%s" % [i, sd]] = a[1]
		d["kn%d%s" % [i, sd]] = a[2]


func stand_foot(s: int, h := -1.0) -> Vector3:
	var sc: float = m.bp["massstab"]
	var hh := (hoehe if h < 0 else h) * sc
	return Vector3(0, -hh, s * (m.u("halbe_breite") + spreiz * sc))


func pose(name: String) -> Dictionary:
	"""servo id -> degrees for a ready pose"""
	var d := {}
	var N: int = m.n()
	var sy := 0.0
	var sp := 0.0
	match name:
		"kurve_links":
			sy = -15.0
		"kurve_rechts":
			sy = 15.0
		"bogen":
			sp = -12.0
		"ring":
			sp = 360.0 / N
	for i in range(N - 1):
		d["sy%d" % i] = sy
		d["sp%d" % i] = sp
	for i in range(N):
		match name:
			"ring":
				for sd in ["l", "r"]:
					d["hy%d%s" % [i, sd]] = 0.0
					d["hp%d%s" % [i, sd]] = 0.0
					d["kn%d%s" % [i, sd]] = 0.0
			"eingeklappt":
				for sd in ["l", "r"]:
					d["hy%d%s" % [i, sd]] = 0.0
					d["hp%d%s" % [i, sd]] = 75.0
					d["kn%d%s" % [i, sd]] = 165.0
			_:
				_legs(d, i, stand_foot(-1), stand_foot(1))
	d["pan"] = 0.0
	return d


func apply(d: Dictionary) -> void:
	for k in d:
		m.set_target(str(k), float(d[k]))


# ==== Stufe 2: Steuerung (jeden Physik-Schritt vor dem Modell) ==========================================================
# Gangarten (alle mit automatischen Kurven: die Segmentgelenke biegen die Kette auf einen Bogen, jedes Segment läuft
# entlang seiner eigenen Längsachse wie ein Zug auf der Schiene - so folgt der ganze Körper derselben Kurve):
#   welle     Wellengang: hinten beginnt, die Welle läuft nach vorne, 3/4 der Beine stehen immer (langsam, sehr stabil)
#   dreifuss  «Dreifuss»-artig: abwechselnd jedes zweite Bein (links / rechts versetzt), die Hälfte steht (schnell)
#   raupe     Raupengang: links und rechts zusammen, zwei Wellen über den Körper, dazu eine kleine Welle im Rücken
#   auto      wählt selbst: Wellengang langsam oder wenn ein Bein-Servo überlastet ist, sonst «Dreifuss»
# Die Füsse rechnen in einem waagrechten Rahmen je Segment (Neigung aus der Physik): auf der Rampe bleiben die Beine
# senkrecht, eine Welle im Rücken hebt die Füsse nicht vom Boden.
const GAENGE := [["welle", "Wellengang"], ["dreifuss", "Dreifuss"], ["raupe", "Raupengang"], ["auto", "Automatisch"]]
const ABLAEUFE := [["raupenwelle", "Raupenwelle"], ["schlange", "Kurve (Schlange)"], ["einrollen", "Einrollen und öffnen"],
		["aufstehen", "Aufstehen"]]
const BETA := {"welle": 0.75, "dreifuss": 0.55, "raupe": 0.8}

var mode := ""                         # "" (von Hand / Pose) | "gang" | "ablauf"
var gang := "auto"
var gang_now := "welle"                # what «auto» picked
var tempo := 0.06                      # m/s at full drive
var drive := 0.0                       # -1 … 1 (W / S, the goal)
var turn := 0.0                        # -1 … 1, + = links (A / D, the goal)
var keys := Vector2.ZERO               # held keys: x = turn (+ links), y = drive
var schritt_laenge := 0.7              # Einheiten
var schritt_hoehe := 0.35              # Einheiten
var kurve_max := 20.0                  # ° per segment joint at full turn
var goal = null                        # Vector3 (world) or null
var goal_reached := false
var phase := 0.0
var _amp := 0.0                        # stride that is used now (m, smooth)
var seq := []                          # the running sequence: [{t, pose | fn | do}]
var seq_name := ""
var seq_i := 0
var seq_t := 0.0
var _seq_from := {}
var legs_level := false                # sequence: legs stand level under the body each step
var traveled := 0.0                    # metres the front segment went (gait test)


func start_gang(g: String) -> void:
	gang = g if g in GAENGE.map(func(x): return x[0]) else "auto"
	mode = "gang"
	seq = []
	seq_name = ""


func stop() -> void:
	"""everything stands still in the standing pose"""
	mode = ""
	seq = []
	seq_name = ""
	goal = null
	drive = 0.0
	turn = 0.0
	keys = Vector2.ZERO
	_amp = 0.0
	apply(pose("gerade"))


func set_goal(p: Vector3) -> void:
	goal = p
	goal_reached = false
	if mode != "gang":
		start_gang(gang)


func level_foot(i: int, s: int, foot_level: Vector3) -> Vector3:
	"""a foot point given in the level frame of segment i (yaw of the segment, no tilt) -> segment frame"""
	if m.bodies.is_empty():
		return foot_level
	var b: Basis = m.segment_xf(i).basis.orthonormalized()
	var fx := b.x
	fx.y = 0.0
	if fx.length() < 0.1:
		return foot_level
	fx = fx.normalized()
	var lvl := Basis(fx, Vector3.UP, fx.cross(Vector3.UP))
	return b.inverse() * (lvl * foot_level)


func _legs_level_targets(d: Dictionary, h_units: float) -> void:
	for i in range(m.n()):
		var fl := level_foot(i, -1, stand_foot(-1, h_units))
		var fr := level_foot(i, 1, stand_foot(1, h_units))
		_legs(d, i, fl, fr)


func phase_of(g: String, i: int, s: int) -> float:
	var N: int = m.n()
	match g:
		"dreifuss":
			return 0.5 * float((i + (1 if s > 0 else 0)) % 2)
		"raupe":
			return fposmod(2.0 * float(N - 1 - i) / N, 1.0)
	return fposmod(float(N - 1 - i) / N + (0.5 if s > 0 else 0.0), 1.0)


func step(dt: float) -> void:
	if m == null or not m.built_ok:
		return
	if mode == "ablauf":
		_seq_step(dt)
	elif mode == "gang":
		_gang_step(dt)


func _gang_step(dt: float) -> void:
	var sc: float = m.bp["massstab"]
	var N: int = m.n()
	# what is wanted: keys, else the goal
	var dv := keys.y
	var tv := keys.x
	if goal != null and keys == Vector2.ZERO:
		var p0: Vector3 = m.segment_xf(0).origin
		var hd: Vector3 = m.segment_xf(0).basis.x
		var to: Vector3 = (goal as Vector3) - p0
		to.y = 0.0
		hd.y = 0.0
		var dist := to.length()
		if dist < 0.12 or goal_reached:
			goal_reached = true
			dv = 0.0
			tv = 0.0
		else:
			var err := atan2(hd.z * to.x - hd.x * to.z, hd.dot(to))     # + = goal on the left
			tv = clampf(err / 0.6, -1.0, 1.0)
			dv = clampf(dist / 0.3, 0.3, 1.0) * (1.0 - 0.5 * absf(tv))
	drive = move_toward(drive, dv, dt * 2.0)
	turn = move_toward(turn, tv, dt * 1.5)
	var v := drive * tempo
	if absf(turn) > 0.05 and absf(v) < 0.3 * tempo:
		v = 0.3 * tempo * (1.0 if v >= 0.0 else -1.0)            # curves need a little forward speed (the body follows its arc)
	# the gait
	gang_now = gang
	if gang == "auto":
		var over_leg := false
		for id in m.overloaded():
			if not str(id).begins_with("s"):
				over_leg = true
		gang_now = "dreifuss" if absf(v) > 0.1 and not over_leg else "welle"
	var beta: float = BETA.get(gang_now, 0.75)
	var amax := schritt_laenge * sc * 0.5
	var moving := absf(v) > 0.002
	_amp = move_toward(_amp, amax if moving else 0.0, dt * amax * 2.0)
	if _amp > 0.0005:
		var T := clampf(2.0 * amax / (beta * maxf(absf(v), 0.01)), 0.45, 6.0)
		phase = fposmod(phase + dt / T, 1.0)
	var dirx := 1.0 if v >= 0.0 else -1.0
	var lift := schritt_hoehe * sc * clampf(_amp / maxf(amax, 1e-4), 0.0, 1.0)
	var d := {}
	for i in range(N):
		for s in [-1, 1]:
			var u := fposmod(phase + phase_of(gang_now, i, s), 1.0)
			var x := 0.0
			var y := 0.0
			if u < beta:
				x = _amp * (1.0 - 2.0 * u / beta)
			else:
				var q := (u - beta) / (1.0 - beta)
				q = q * q * (3.0 - 2.0 * q)
				x = _amp * (-1.0 + 2.0 * q)
				y = lift * sin(PI * (u - beta) / (1.0 - beta))
			var f := stand_foot(s)
			f.x = x * dirx
			f.y += y
			var fs := level_foot(i, s, f)
			var a := leg_ik(s, fs)
			var sd := "l" if s < 0 else "r"
			d["hy%d%s" % [i, sd]] = a[0]
			d["hp%d%s" % [i, sd]] = a[1]
			d["kn%d%s" % [i, sd]] = a[2]
	for i in range(N - 1):
		d["sy%d" % i] = -turn * kurve_max
		d["sp%d" % i] = 8.0 * sin(TAU * (2.0 * phase - float(i) / maxf(1.0, N - 1))) if gang_now == "raupe" and _amp > 0.001 else 0.0
	apply(d)


# ---- ganze Abläufe -------------------------------------------------------------------------------------------------------
func start_ablauf(name: String) -> void:
	var N: int = m.n()
	var ring_legs := {}
	for i in range(N):
		for sd in ["l", "r"]:
			ring_legs["hy%d%s" % [i, sd]] = 0.0
			ring_legs["hp%d%s" % [i, sd]] = 0.0
			ring_legs["kn%d%s" % [i, sd]] = 0.0
	var straight := {}
	for i in range(N - 1):
		straight["sy%d" % i] = 0.0
		straight["sp%d" % i] = 0.0
	var ring_body := {}
	for i in range(N - 1):
		ring_body["sp%d" % i] = 360.0 / N
		ring_body["sy%d" % i] = 0.0
	match name:
		"raupenwelle":
			seq = [{"t": 1.0, "pose": pose("gerade")},
					{"t": 8.0, "level": true, "fn": func(t: float) -> Dictionary:
						var d := {}
						for i in range(N - 1):
							d["sp%d" % i] = 18.0 * sin(TAU * (t / 2.0 - float(i) / (N - 1))) * minf(1.0, t)
						return d},
					{"t": 1.0, "pose": pose("gerade")}]
		"schlange":
			seq = [{"t": 1.0, "pose": pose("gerade")},
					{"t": 8.0, "level": true, "fn": func(t: float) -> Dictionary:
						var d := {}
						for i in range(N - 1):
							d["sy%d" % i] = 18.0 * sin(TAU * (t / 2.5 - float(i) / (N - 1))) * minf(1.0, t)
						return d},
					{"t": 1.0, "pose": pose("gerade")}]
		"einrollen":
			var ring_all := ring_legs.duplicate()
			ring_all.merge(ring_body)
			var lie := ring_legs.duplicate()
			lie.merge(straight)
			seq = [{"t": 1.2, "pose": lie}, {"t": 0.0, "do": "latch_on"}, {"t": 5.0, "pose": ring_all}, {"t": 2.5, "pose": ring_all},
					{"t": 0.0, "do": "latch_off"}, {"t": 5.0, "pose": lie}, {"t": 0.0, "do": "latch_on"},
					{"t": 2.0, "pose": pose("gerade")}]
		"aufstehen":
			var low := {}
			for i in range(N):
				_legs(low, i, stand_foot(-1, 0.4), stand_foot(1, 0.4))
			low.merge(straight)
			seq = [{"t": 1.5, "pose": pose("eingeklappt")}, {"t": 1.5, "pose": low}, {"t": 2.0, "pose": pose("gerade")}]
		_:
			return
	seq_name = name
	seq_i = 0
	seq_t = 0.0
	mode = "ablauf"
	goal = null
	_seq_from = m.targets()


func _seq_step(dt: float) -> void:
	if seq_i >= seq.size():
		mode = ""
		seq_name = ""
		return
	var e: Dictionary = seq[seq_i]
	seq_t += dt
	var dur := float(e.get("t", 0.0))
	var k := clampf(seq_t / maxf(dur, 1e-3), 0.0, 1.0)
	if e.has("do"):
		m.latch_wanted = e["do"] == "latch_on"
		if e["do"] == "latch_off":
			m.unlock()
	elif e.has("pose"):
		var d := {}
		var to: Dictionary = e["pose"]
		for key in to:
			var a := float(_seq_from.get(key, to[key]))
			d[key] = lerpf(a, float(to[key]), k * k * (3.0 - 2.0 * k))
		apply(d)
	elif e.has("fn"):
		var d2: Dictionary = (e["fn"] as Callable).call(seq_t)
		if bool(e.get("level", false)):
			_legs_level_targets(d2, hoehe)
		apply(d2)
	if seq_t >= dur:
		seq_i += 1
		seq_t = 0.0
		_seq_from = m.targets()
