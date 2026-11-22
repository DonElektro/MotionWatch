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
var keys := Vector2.ZERO               # ring: x = turn (+ links), y = drive
var cmd := Vector3.ZERO                # walking: x = seitwärts (+ links), y = vor / zurück, z = drehen (+ links)
var side := 0.0                        # smooth strafe -1 … 1 (+ links)
var anpassen := true                   # «Körper passt sich dem Untergrund an» (Stufe 4, Standard an)
var plan := ""                         # what the goal planner does: kurve | seitwaerts | drehen | angekommen
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
var angepasst := false                 # «auto» raised the steps and the body because it got stuck
var _prog_t := 0.0
var _prog_p := Vector3.ZERO


func start_gang(g: String) -> void:
	gang = g if g in GAENGE.map(func(x): return x[0]) else "auto"
	_prog_t = 0.0
	_prog_p = m.segment_xf(0).origin if m != null and m.built_ok else Vector3.ZERO
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
	cmd = Vector3.ZERO
	side = 0.0
	_amp = 0.0
	apply(pose("ring" if m.latch["state"] == "locked" else "gerade"))   # never straighten against the closed latch


func set_goal(p: Vector3) -> void:
	goal = p
	goal_reached = false
	if mode == "ring" or m.latch["state"] == "locked":
		mode = "ring"
	elif mode != "gang":
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
	elif mode == "ring":
		_ring_step(dt)


func _gang_step(dt: float) -> void:
	"""Stufe 4 (Besitzer 22.11.2026 19:05): in alle Richtungen - vor / zurück, seitwärts (Krebsgang), schräg, an Ort drehen,
	Kurven (der Körper biegt sich auf den Bogen). Jeder Fuss bekommt seinen eigenen Schritt-Vektor = Körper-Geschwindigkeit
	+ Drehung × Hebel (Hüfte zur Körpermitte). Mit «anpassen» folgt der Körper dem Untergrund (Höhe je Segment, Neigung der
	Segmentgelenke, jeder Fuss sucht seinen Boden und hält an, wenn er früher aufsetzt)."""
	var sc: float = m.bp["massstab"]
	var N: int = m.n()
	var P: float = m.pitch_len()
	var want := cmd
	if goal != null and cmd == Vector3.ZERO:
		want = _plan_goal()
	side = move_toward(side, want.x, dt * 2.0)
	drive = move_toward(drive, want.y, dt * 2.0)
	turn = move_toward(turn, want.z, dt * 1.5)
	# arc (walk a curve: forward + turn) or omni (body straight: strafe, diagonal, turn on the spot)
	var arc := absf(drive) > 0.25 and absf(side) < 0.15 and absf(turn) > 0.05
	var vx := drive * tempo
	var vz := -side * tempo                                    # + side = links = −Z of the robot
	var half_len := maxf(P * N * 0.5, 0.05)
	var om := 0.0 if arc else turn * 2.0 * tempo / half_len    # rad/s, + = links (the end feet at twice the walking speed)
	var speed := Vector2(vx, vz).length() + absf(om) * half_len
	gang_now = gang
	if gang == "auto":
		var over_leg := false
		for id in m.overloaded():
			if not str(id).begins_with("s"):
				over_leg = true
		gang_now = "dreifuss" if speed > 0.1 and not over_leg else "welle"
	if gang == "auto" and speed > 0.01 and absf(vx) > 0.5 * speed:
		_prog_t += dt
		if _prog_t >= 3.0:
			var pnow: Vector3 = m.segment_xf(0).origin
			if not angepasst and pnow.distance_to(_prog_p) < 0.25 * speed * _prog_t:
				angepasst = true                  # stuck: higher steps, body higher (e.g. at a step or in gravel)
				schritt_hoehe = maxf(schritt_hoehe, 0.8)
				hoehe = maxf(hoehe, 1.2)
			_prog_t = 0.0
			_prog_p = pnow
	var beta: float = BETA.get(gang_now, 0.75)
	var amax := schritt_laenge * sc * 0.5
	var moving := speed > 0.002
	_amp = move_toward(_amp, amax if moving else 0.0, dt * amax * 2.0)
	var T := 1.0
	if _amp > 0.0005:
		T = clampf(2.0 * amax / (beta * maxf(speed, 0.01)), 0.45, 6.0)
		phase = fposmod(phase + dt / T, 1.0)
	var kamp := clampf(_amp / maxf(amax, 1e-4), 0.0, 1.0)
	var lift := schritt_hoehe * sc * kamp
	var hh: float = hoehe * sc
	var w: float = m.u("halbe_breite")
	# terrain: wanted height of every segment (ground under it, gaps narrower than ~2 segments bridged)
	var ydes := []
	var lvl := []
	for i in range(N):
		var xf: Transform3D = m.segment_xf(i)
		var fx := xf.basis.x
		fx.y = 0.0
		fx = fx.normalized() if fx.length() > 0.1 else Vector3.RIGHT
		lvl.append(Basis(fx, Vector3.UP, fx.cross(Vector3.UP)))
		if anpassen:
			var g := -1e9
			for k in [-1.0, 0.0, 1.0]:
				g = maxf(g, _ground_at(xf.origin + fx * P * k, xf.origin.y + 0.4, xf.origin.y - hh))
			ydes.append(g + hh)
		else:
			ydes.append(xf.origin.y)
	var d := {}
	for i in range(N):
		var xf: Transform3D = m.segment_xf(i)
		var xi := (float(N - 1) * 0.5 - i) * P
		for s in [-1, 1]:
			var f := stand_foot(s)
			var vf := Vector2(vx, vz) if arc else Vector2(vx + om * f.z, vz - om * xi)
			var a2 := vf * beta * T * 0.5
			if a2.length() > amax:
				a2 = a2.normalized() * amax
			a2 *= kamp
			var u := fposmod(phase + phase_of(gang_now, i, s), 1.0)
			var off := Vector2.ZERO
			var y := 0.0
			var swing_down := false
			if u < beta:
				off = a2 * (1.0 - 2.0 * u / beta)
			else:
				var q := (u - beta) / (1.0 - beta)
				swing_down = q > 0.5
				var qs := q * q * (3.0 - 2.0 * q)
				off = a2 * (-1.0 + 2.0 * qs)
				y = lift * sin(PI * q)
			f.x += off.x
			f.z += off.y
			if anpassen:
				var fw: Vector3 = xf.origin + (lvl[i] as Basis) * Vector3(f.x, 0.0, f.z)
				var gf := _ground_at(fw, xf.origin.y + 0.3, float(ydes[i]) - hh)
				f.y = gf - float(ydes[i]) + y                      # as if the segment were at its wanted height
				if swing_down and m.foot_contact(i, s):             # touched down early (stone, step): stop there
					var meas: Vector3 = m.foot_world(i, s)
					f.y = maxf(f.y, meas.y - float(ydes[i]))
			else:
				f.y += y
			var fs: Vector3 = xf.basis.orthonormalized().inverse() * ((lvl[i] as Basis) * f) if anpassen else level_foot(i, s, f)
			var a := leg_ik(s, fs)
			var sd := "l" if s < 0 else "r"
			d["hy%d%s" % [i, sd]] = a[0]
			d["hp%d%s" % [i, sd]] = a[1]
			d["kn%d%s" % [i, sd]] = a[2]
	# body joints: yaw for the arc, pitch following the ground profile (+ the wave of the caterpillar gait)
	var alpha := []
	if anpassen:
		var hj := []                                          # wanted height at the tips and joints, front to back
		for k in range(N + 1):
			var xf: Transform3D = m.segment_xf(mini(k, N - 1))
			var p: Vector3 = xf * Vector3(P * 0.5 if k < N else -P * 0.5, 0, 0)
			var g := -1e9
			for dk in [-0.5, 0.0, 0.5]:
				g = maxf(g, _ground_at(p + xf.basis.x * P * dk, xf.origin.y + 0.4, xf.origin.y - hh))
			hj.append(g + hh)
		for i in range(N):
			alpha.append(rad_to_deg(atan2(float(hj[i]) - float(hj[i + 1]), P)))
	for i in range(N - 1):
		d["sy%d" % i] = -turn * kurve_max if arc else 0.0
		var sp := 0.0
		if anpassen:
			sp = clampf(float(alpha[i]) - float(alpha[i + 1]), -40.0, 40.0)
		if gang_now == "raupe" and _amp > 0.001:
			sp += 8.0 * sin(TAU * (2.0 * phase - float(i) / maxf(1.0, N - 1)))
		d["sp%d" % i] = sp
	apply(d)


func _plan_goal() -> Vector3:
	"""the walk to the goal: [strafe, forward, turn]. Behind → turn on the spot; small side offset close by → walk
	sideways / diagonally; otherwise forward on a curve"""
	var p0: Vector3 = m.segment_xf(0).origin
	var hd: Vector3 = m.segment_xf(0).origin - m.segment_xf(m.n() - 1).origin
	hd.y = 0.0
	hd = hd.normalized() if hd.length() > 0.01 else Vector3.RIGHT
	var left := Vector3(hd.z, 0.0, -hd.x)
	var to: Vector3 = (goal as Vector3) - p0
	to.y = 0.0
	var dist := to.length()
	if dist < 0.12 or goal_reached:
		goal_reached = true
		plan = "angekommen"
		return Vector3.ZERO
	var xr := to.dot(hd)
	var zl := to.dot(left)
	var err := atan2(zl, xr)                                   # + = goal on the left
	if absf(err) > deg_to_rad(110.0) and dist > 0.3:
		plan = "drehen"
		return Vector3(0.0, 0.0, signf(err))
	if dist < 0.6 and absf(zl) < 0.3:
		plan = "seitwaerts"
		var v := Vector2(zl, xr).normalized() * clampf(dist / 0.3, 0.4, 1.0)
		return Vector3(v.x, v.y, 0.0)
	plan = "kurve"
	var tv := clampf(err / 0.6, -1.0, 1.0)
	return Vector3(0.0, clampf(dist / 0.3, 0.3, 1.0) * (1.0 - 0.5 * absf(tv)), tv)


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


# ==== Stufe 3: im Ring rollen (Besitzer: «die Füsse stossen ihn vorwärts, den Ring kippen = Kurve») ======================
# Nur bei verriegeltem Ring. Die Beine der Segmente unten hinten (in Rollrichtung gesehen) greifen seitlich neben dem Ring
# auf den Boden und stossen nach hinten-unten → der Ring rollt vorwärts. Die anderen Beine stehen als Speichen seitlich ab.
# Lenken: der Ring neigt sich wie eine rollende Münze und fährt dann eine Kurve; die Füsse einer Seite drücken dafür tiefer.
# Ohne Fahrbefehl stützen die unteren Beine beidseits (der Ring bleibt stehen und aufrecht).
var ring_lean := 0.0                   # measured lean (°, + = top to the left)
var ring_push := [5.0, 80.0]           # window behind the bottom (°) where the legs push
var ring_lean_max := 14.0              # ° at full turn
var ring_k := 0.3                      # m of extra press per rad of lean error
var ring_info := {}


func ring_state() -> Dictionary:
	"""centre, axle (segment Z, right), forward (horizontal, ⟂ axle), lean (°), ground height"""
	var N: int = m.n()
	var c := Vector3.ZERO
	var ax := Vector3.ZERO
	for i in range(N):
		var xf: Transform3D = m.segment_xf(i)
		c += xf.origin
		ax += xf.basis.z
	c /= N
	ax = ax.normalized()
	var fw := Vector3.UP.cross(ax)
	fw.y = 0.0
	fw = fw.normalized() if fw.length() > 0.1 else Vector3.RIGHT
	var gy: float = c.y - (float(m.pitch_len()) * 0.5 / tan(PI / N) + float(m.u("halbe_breite")))
	var cps: Array = m.contact_points(["seg", "buegel"])
	if not cps.is_empty():
		gy = 1e9
		for q in cps:
			gy = minf(gy, (q as Vector3).y)
	return {"c": c, "ax": ax, "fw": fw, "lean": rad_to_deg(asin(clampf(ax.y, -1.0, 1.0))), "gy": gy}


func _ring_step(dt: float) -> void:
	if m.latch["state"] != "locked":
		ring_info = {"ok": false}
		return
	var N: int = m.n()
	var dv := keys.y
	var tv := keys.x
	var rs := ring_state()
	if goal != null and keys == Vector2.ZERO:
		var to: Vector3 = (goal as Vector3) - (rs["c"] as Vector3)
		to.y = 0.0
		var hd: Vector3 = rs["fw"]
		if to.length() < 0.2 or goal_reached:
			goal_reached = true
			dv = 0.0
			tv = 0.0
		else:
			var err := atan2(hd.z * to.x - hd.x * to.z, hd.dot(to))
			if absf(err) > PI * 0.6:                      # behind: roll backwards is shorter
				dv = -1.0
				err = -(PI - absf(err)) * signf(err)
			else:
				dv = 1.0
			tv = clampf(err / 0.8, -1.0, 1.0) * signf(dv)
	drive = move_toward(drive, dv, dt * 1.5)
	turn = move_toward(turn, tv, dt * 1.5)
	ring_lean = rs["lean"]
	var c: Vector3 = rs["c"]
	var ax: Vector3 = rs["ax"]
	var fw: Vector3 = rs["fw"]
	var gy: float = rs["gy"]
	var l1: float = m.u("oberschenkel")
	var l2: float = m.u("unterschenkel")
	var reach := (l1 + l2) * 0.97
	var w: float = m.u("halbe_breite")
	var lat := w * 0.4 + spreiz * float(m.bp["massstab"]) * 0.6
	var dirv := 1.0 if drive >= 0.0 else -1.0
	var lean_err := deg_to_rad(turn * ring_lean_max - ring_lean)
	var d := {}
	var pushing := 0
	for i in range(N):
		var xf: Transform3D = m.segment_xf(i)
		var r := xf.origin - c
		var ang := rad_to_deg(atan2(Vector3.DOWN.cross(r).dot(ax), Vector3.DOWN.dot(r)))   # + = ahead of the bottom
		var behind := -ang * dirv
		for s in [-1, 1]:
			var sd := "l" if s < 0 else "r"
			var hip: Vector3 = xf * Vector3(0, 0, s * w)
			var h := hip.y - gy
			var press := 0.012 + clampf(float(s) * lean_err * ring_k, -0.05, 0.04)   # lean: one side presses, the other lifts
			var foot := Vector3.ZERO
			var use := false
			if absf(drive) > 0.05 and behind > ring_push[0] and behind < ring_push[1]:
				var back := sqrt(maxf(0.0, reach * reach - lat * lat - (h + press) * (h + press))) * absf(drive)
				foot = hip + ax * float(s) * lat - fw * dirv * back
				use = true
				pushing += 1
			elif absf(drive) <= 0.05 and absf(ang) < 55.0:
				foot = hip + ax * float(s) * lat
				use = true
			if use:
				var gl := _ground_at(foot, hip.y + 0.05, gy)       # every foot finds its own ground (step, gravel)
				if gl < gy - 0.03 and absf(drive) > 0.05:          # a gap (ditch) under the foot: look further back
					for k in [0.6, 0.3, 1.3]:
						var alt: Vector3 = hip + ax * float(s) * lat - fw * dirv * (foot - hip).dot(-fw * dirv) * float(k)
						var ga := _ground_at(alt, hip.y + 0.05, gy)
						if ga >= gy - 0.03:
							foot = alt
							gl = ga
							break
				h = hip.y - gl
				foot.y = gl - press
			if use and h < reach:
				var a := leg_ik(s, xf.affine_inverse() * foot)
				d["hy%d%s" % [i, sd]] = a[0]
				d["hp%d%s" % [i, sd]] = a[1]
				d["kn%d%s" % [i, sd]] = a[2]
			else:
				d["hy%d%s" % [i, sd]] = 0.0
				d["hp%d%s" % [i, sd]] = 0.0
				d["kn%d%s" % [i, sd]] = 0.0
	apply(d)
	ring_info = {"ok": true, "lean": ring_lean, "pushing": pushing, "centre": c}


func _ground_at(p: Vector3, from_y: float, fallback: float) -> float:
	"""height of the terrain under p (ray down, terrain layer only)"""
	var w3: World3D = m.get_world_3d()
	if w3 == null:
		return fallback
	var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, from_y, p.z), Vector3(p.x, from_y - 1.0, p.z), m.LAYER_GELAENDE)
	var hit := w3.direct_space_state.intersect_ray(q)
	return float((hit["position"] as Vector3).y) if not hit.is_empty() else fallback


func start_ring() -> void:
	mode = "ring"
	seq = []
	seq_name = ""
	goal = null
