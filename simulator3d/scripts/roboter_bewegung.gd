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
	if name == "ring" and not m.ring_ok():
		name = "gerade"                        # 2 / 3 Segmente: kein Ring (Gelenke ±90°), stehen bleiben
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
const ANZ = preload("res://scripts/roboter_anzeige.gd")
const GAENGE := [["welle", "Wellengang"], ["dreifuss", "Dreifuss"], ["raupe", "Raupengang"], ["auto", "Automatisch"]]
const ABLAEUFE := [["raupenwelle", "Raupenwelle"], ["schlange", "Kurve (Schlange)"], ["einrollen", "Einrollen und öffnen"],
		["aufstehen", "Aufstehen"]]
const BETA := {"welle": 0.75, "dreifuss": 0.55, "raupe": 0.8}
const BETA_2 := {"welle": 0.8, "raupe": 0.85, "dreifuss": 0.7}   # 2 Segmente: längere Standzeit (Pausen mit 4 Füssen am Boden)

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
# Ring öffnen (Besitzer 28.11.2026: «Gerade» kämpfte gegen den geschlossenen Riegel): der Riegel geht auf, die Kette streckt
# sich weich; «Riegel darf schliessen» kommt erst zurück, wenn die Enden weit auseinander sind (sonst zieht der Greif-Zug
# sie gleich wieder zusammen)
var latch_back := true                 # the value of the switch «Riegel darf schliessen (Ring)» while the ring opens
var latch_wait := false                # true: latch_wanted is off until the ends are apart


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
	if N == 2:
		# 4 Beine (Besitzer 28.11.2026): Wellengang = Schritt hinten links, vorne links, hinten rechts, vorne rechts - immer
		# nur ein Bein in der Luft (statisch stabil); «Dreifuss» = Trab (diagonale Paare). Raupe: ein Paar zugleich kippt
		# über die Querachse, beide hinteren nacheinander schaukeln quer (gemessen bis 38° / 83°) - darum dieselbe Reihenfolge
		# wie der Schritt, nur mit längerer Standzeit (BETA_2) und ohne Welle im Rücken
		var r := 1 if s > 0 else 0
		if g == "dreifuss":
			return 0.5 * float((i + r) % 2)
		return fposmod(-0.25 * float(1 - i) - 0.5 * float(r), 1.0)   # Abheben der Reihe nach: HL, VL, HR, VR
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
	if latch_wait and not (mode == "ablauf" and seq_name == "oeffnen") and m.latch["state"] == "open" and ends_apart():
		latch_restore()


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
		gang_now = "dreifuss" if speed > 0.1 and not over_leg and N > 2 else "welle"   # 4 Beine: immer der Schritt
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
	if N == 2:
		beta = BETA_2.get(gang_now, beta)
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
		if gang_now == "raupe" and _amp > 0.001 and N > 2:          # 2 Segmente: keine Welle im Rücken (kippt)
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
	if name == "einrollen" and not m.ring_ok():
		return                                 # 2 / 3 Segmente: kein Ring
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
	if name != "oeffnen":
		latch_restore()
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
		"oeffnen":
			# the open ring cannot carry its own halves (the segment servos are too weak, the halves fold through each
			# other): first roll the latch to the top, then open there - the joints at the bottom straighten first, the
			# two arms fold down outward one joint pair after the other (≈ 3.5 s rolling + 4 s opening + 1.5 s pose)
			var gap := 0.8                                 # s between the joint pairs
			var dur := 1.6                                 # s one joint needs to straighten
			var steps := int(N / 2)
			seq = [{"t": 14.0, "roll": true}, {"t": 0.0, "do": "latch_off"},
					{"t": gap * (steps - 1) + dur, "fn": func(t: float) -> Dictionary:
						var d := {}
						for i in range(N - 1):
							var r := steps - 1 - mini(i, N - 2 - i)   # 0 = the joint at the bottom (the latch is on top)
							var k := clampf((t - r * gap) / dur, 0.0, 1.0)
							k = k * k * (3.0 - 2.0 * k)
							for key in ["sp%d" % i, "sy%d" % i]:
								d[key] = lerpf(float(_open_s0.get(key, 0.0)), 0.0, k)
						return d},
					{"t": 1.5, "pose": pose(open_to)}]
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


var open_to := "gerade"                # Ring öffnen: the pose at the end
var _open_s0 := {}                     # Ring öffnen: the joint targets when the latch opens


func latch_phi() -> float:
	"""angle of the latch (between segment 0 and N-1) about the ring axle, 0 = on top (rad)"""
	var rs := ring_state()
	var v: Vector3 = (m.segment_xf(0).origin + m.segment_xf(m.n() - 1).origin) * 0.5 - (rs["c"] as Vector3)
	var ax: Vector3 = rs["ax"]
	var up := (Vector3.UP - ax * Vector3.UP.dot(ax)).normalized()
	return atan2(ax.cross(up).dot(v), up.dot(v))


func start_oeffnen(to := "gerade") -> void:
	"""Ring öffnen: stop, latch off (unlock), in 4.5 s softly into the pose `to` (like the opening in «Einrollen und öffnen»);
	afterwards latch_wanted = the switch again, once the ends are far enough apart (see step)"""
	if not latch_wait:
		latch_back = m.latch_wanted
	latch_wait = true
	open_to = to if to != "ring" else "gerade"
	drive = 0.0
	turn = 0.0
	keys = Vector2.ZERO
	cmd = Vector3.ZERO
	side = 0.0
	_amp = 0.0
	start_ablauf("oeffnen")


func ends_apart() -> bool:
	"""the latch ends are clearly outside the zone where the cone pulls them together (P / 4 and 25°, roboter_modell.gd)"""
	return float(m.latch["err_pos"]) > m.pitch_len() * 0.6 or float(m.latch["err_ang"]) > 45.0


func latch_restore() -> void:
	"""give the switch «Riegel darf schliessen» its say again (a new sequence, rolling in the ring, the ring pose)"""
	if latch_wait:
		latch_wait = false
		m.latch_wanted = latch_back


func _seq_step(dt: float) -> void:
	if seq_i >= seq.size():
		mode = ""
		seq_name = ""
		return
	var e: Dictionary = seq[seq_i]
	seq_t += dt
	var dur := float(e.get("t", 0.0))
	var k := clampf(seq_t / maxf(dur, 1e-3), 0.0, 1.0)
	if e.has("roll"):
		# Ring öffnen: roll (feet push) until the latch is on top; not locked (grip, open): nothing to roll
		if m.latch["state"] != "locked" or absf(latch_phi()) < deg_to_rad(12.0):
			seq_t = dur
			keys = Vector2.ZERO
		else:
			keys = Vector2(0.0, 1.0)
			_ring_step(dt)
	elif e.has("do"):
		m.latch_wanted = e["do"] == "latch_on"
		if e["do"] == "latch_off":
			m.unlock()
			_open_s0 = m.targets()
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
	gy = _ground_at(c, c.y + 0.1, gy)                     # the ground right under the centre (it may stand on its legs)
	return {"c": c, "ax": ax, "fw": fw, "lean": rad_to_deg(asin(clampf(ax.y, -1.0, 1.0))), "gy": gy}


# ---- Rund rollen (Besitzer 22.11.2026 21:33 / 21:36): Methoden, wie die Beine den Ring rollen lassen ---------------------
#   stossen  wie bisher (8er): die Beine unten hinten stossen, sonst nichts
#   a        «Beine stemmen an den Ecken»: zusätzlich halten die unteren Beine die Ringmitte auf Eckhöhe (der Ring liegt nie
#            auf einer Seite auf → rollt wie über die Ecken, ohne abzusinken)
#   b        «Beine als Speichen-Kreis»: alle Beine als Speichen in der Ringebene (gleichmässig verteilt), die Füsse
#            auf einem Kreis; rollen durch längere Speichen hinten / kürzere vorne, lenken durch eine längere Seite
#   c        «Füsse passen sich an»: wie a, dazu Regelung über die ganze Drehung - Höhe der Mitte (mit Integral), gleichmässiges
#            Tempo (Stoss stärker / schwächer) und Vorhalt aus dem Ringwinkel (die nächste Ecke kommt)
# Rundheit: über eine ganze Drehung (nach 30° Anlauf) die Schwankung der Mittenhöhe (cm) und des Tempos (% vom Mittel).
const RING_METHODEN := [["stossen", "Nur stossen"], ["a", "A: Beine stemmen an den Ecken"], ["b", "B: Beine als Speichen-Kreis"],
		["c", "C: Füsse passen sich an"]]
var ring_methode := "stossen"
var ring_meas := {}                    # running measurement
var ring_result := {}                  # last finished measurement
var _ring_i := 0.0                     # integral of the height error (c)
var _ring_v := 0.0                     # smooth forward speed (c, measurement)
var _ring_vt := 0.0                    # slow mean speed = the even speed wanted (c)
var _ring_prev := Vector3.ZERO
var _ring_phi := 0.0
var ring_hoehe := 0.0                  # «Höhe über Boden» (m): body clearance while rolling (0 = on its corners, more = on stilts)
var spur_rollen := 0.141               # «Spurbreite» beim Rollen (m): left foot to right foot (default = the tested 8er rolling)
var c_lead := 0.15                     # c: s the wanted ring pose runs ahead
var c_kh := 0.6                        # c: share of the height error corrected
var c_kv := 0.6                        # c: share of the speed error corrected
var c_win := 100.0                     # c: ° around the bottom where legs stand on the ground
var c_tilt := -0.5                     # c: share of the lean error the wanted pose corrects (sign tested)
var c_speed := 2.0                     # c: wanted roll speed = tempo × this (at least 8 cm/s)
var _latch_ft := {}                    # c: planted feet (leg key -> world point), the ring rolls over them
var _tip_t := 0
var spoke_k := 0.18                    # b: relative spoke length change at full drive
var spoke_turn := 0.08                 # b: one side longer for curves


func ring_height_max() -> float:
	"""the most clearance the legs can carry: the hips of the bottom segment must still reach the ground"""
	if not m.ring_ok():
		return 0.0
	var a: float = m.pitch_len() * 0.5 / tan(PI / m.n())
	var reach: float = (m.u("oberschenkel") + m.u("unterschenkel")) * 0.85
	return maxf(0.0, a + reach - corner_height())


func ring_target() -> float:
	"""wanted height of the ring centre above the ground"""
	return corner_height() + clampf(ring_hoehe, 0.0, ring_height_max())


func ring_lat() -> float:
	"""lateral offset of a rolling foot from its hip (from the track width, within reach)"""
	var w: float = m.u("halbe_breite")
	var reach: float = m.u("oberschenkel") + m.u("unterschenkel")
	return clampf(spur_rollen * 0.5 - w, 0.0, reach * 0.6)


func spur_gehen() -> float:
	"""track width when walking (m) = left foot to right foot"""
	return 2.0 * (m.u("halbe_breite") + spreiz * float(m.bp["massstab"]))


func set_spur_gehen(v: float) -> void:
	var sc: float = m.bp["massstab"]
	var reach: float = m.u("oberschenkel") + m.u("unterschenkel")
	spreiz = clampf((v * 0.5 - m.u("halbe_breite")) / sc, 0.1, reach * 0.95 / sc)


func ring_methods() -> Array:
	return RING_METHODEN


func _support(c: Vector3, ax: Vector3, ahead := 0.0) -> float:
	"""how far the ring body reaches below its centre now (or turned «ahead» rad further about the axle)"""
	var low := 0.0
	var rot := Basis(ax, ahead)
	for i in range(m.n()):
		var bi: int = m.seg_body[i]
		var xf: Transform3D = m.frame_of(bi)
		var sh = (m.bodies[bi]["cs"] as CollisionShape3D).shape
		if sh is ConvexPolygonShape3D:
			for q in (sh as ConvexPolygonShape3D).points:
				var p: Vector3 = rot * (xf * q - c)
				low = maxf(low, -p.y)
	return low


var _corner := {}


func corner_height() -> float:
	"""the highest the ring centre gets when it rolls over its own body (on a corner)"""
	if not m.built_ok or m.seg_body.size() < m.n():
		return m.pitch_len() * 0.5 / tan(PI / m.n()) + m.u("halbe_breite")   # not built yet: a rough value, not kept
	var key := "%d_%s" % [m.n(), str(m.bp.hash())]
	if _corner.has(key):
		return _corner[key]
	_corner = {key: _corner_calc()}
	return _corner[key]


func _corner_calc() -> float:
	var fr: Array = m.fk(pose("ring"), Transform3D(), true)
	var pts := []
	var c := Vector3.ZERO
	for i in range(m.n()):
		c += (fr[m.seg_body[i]] as Transform3D).origin
	c /= m.n()
	for i in range(m.n()):
		var sh = (m.bodies[m.seg_body[i]]["cs"] as CollisionShape3D).shape
		for q in (sh as ConvexPolygonShape3D).points:
			pts.append((fr[m.seg_body[i]] as Transform3D) * q - c)
	var best := 0.0
	for k in range(180):
		var dd := Vector3(cos(TAU * k / 180.0), sin(TAU * k / 180.0), 0.0)
		var sup := 0.0
		for p in pts:
			sup = maxf(sup, (p as Vector3).dot(dd))
		best = maxf(best, sup)
	return best


func ring_phi(rs: Dictionary) -> float:
	"""angle of segment 0 about the axle (rad, world)"""
	var v: Vector3 = m.segment_xf(0).origin - (rs["c"] as Vector3)
	var ax: Vector3 = rs["ax"]
	var up := Vector3.UP - ax * Vector3.UP.dot(ax)
	up = up.normalized()
	return atan2(ax.cross(up).dot(v), up.dot(v))


func start_ring_measure() -> void:
	ring_meas = {"rot": 0.0, "h": [], "v": [], "k": [], "low": [], "t": 0.0, "warm": deg_to_rad(30.0)}
	ring_result = {}
	_ring_phi = ring_phi(ring_state())
	_ring_prev = ring_state()["c"]


func _ring_measure(dt: float, rs: Dictionary, hgt: float) -> void:
	var phi := ring_phi(rs)
	var dphi := wrapf(phi - _ring_phi, -PI, PI)
	_ring_phi = phi
	var c: Vector3 = rs["c"]
	var v := (c - _ring_prev).dot(rs["fw"]) / maxf(dt, 1e-4)
	_ring_prev = c
	_ring_v = lerpf(_ring_v, v, clampf(dt * 8.0, 0.0, 1.0))
	if ring_meas.is_empty():
		return
	ring_meas["t"] = float(ring_meas["t"]) + dt
	ring_meas["rot"] = float(ring_meas["rot"]) + absf(dphi)
	if float(ring_meas["rot"]) < float(ring_meas["warm"]):
		return
	(ring_meas["h"] as Array).append(hgt)
	(ring_meas["v"] as Array).append(absf(_ring_v))
	_tip_t += 1
	if _tip_t % 6 == 0:
		var pts := PackedVector2Array()
		for q in m.contact_points():
			pts.append(Vector2((q as Vector3).x, (q as Vector3).z))
		if pts.size() > 0:                                 # in the air for a moment: no support area, not counted here
			var cm: Vector3 = m.com()
			var mg: float = ANZ.signed_margin(Vector2(cm.x, cm.z), ANZ.hull(pts))
			ring_meas["tip"] = minf(float(ring_meas.get("tip", 9.0)), mg)
	var kc: int = m.ground_contacts()
	(ring_meas["k"] as Array).append(kc)
	if kc < 3:                                            # where (ring angle since the start of the turn) it drops below 3
		var deg := int(rad_to_deg(float(ring_meas["rot"]) - float(ring_meas["warm"])))
		var low: Array = ring_meas["low"]
		if low.is_empty() or deg - int(low[low.size() - 1][1]) > 3:
			low.append([deg, deg])
		else:
			low[low.size() - 1][1] = deg
	if float(ring_meas["rot"]) >= float(ring_meas["warm"]) + TAU:
		var hs: Array = ring_meas["h"]
		var vs: Array = ring_meas["v"]
		var vm := 0.0
		for x in vs:
			vm += float(x)
		vm /= maxf(1.0, vs.size())
		var var_ := 0.0
		for x in vs:
			var_ += pow(float(x) - vm, 2)
		var sd := sqrt(var_ / maxf(1.0, vs.size()))
		var ks: Array = ring_meas["k"]
		var km := 0.0
		for x in ks:
			km += float(x)
		ring_result = {"ok": true, "dh": (hs.max() - hs.min()) * 100.0, "v": vm * 100.0, "dv": sd / maxf(vm, 1e-4) * 100.0,
				"t": float(ring_meas["t"]), "methode": ring_methode, "hoehe": ring_hoehe * 100.0, "kmin": ks.min(),
				"kavg": km / maxf(1.0, ks.size()), "unter3": (ring_meas["low"] as Array).slice(0, 6),
				"kipp": float(ring_meas.get("tip", 0.0)) * 100.0, "spur": spur_rollen * 100.0}
		ring_meas = {}


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
	var meth := ring_methode
	_ring_measure(dt, rs, c.y - gy)
	if meth == "b":
		_ring_spokes(rs)
		return
	var l1: float = m.u("oberschenkel")
	var l2: float = m.u("unterschenkel")
	var reach := (l1 + l2) * 0.97
	var w: float = m.u("halbe_breite")
	var lat := ring_lat()
	var dirv := 1.0 if drive >= 0.0 else -1.0
	var lean_err := deg_to_rad(turn * ring_lean_max - ring_lean)
	if meth == "c":
		_ring_c(dt, rs, lean_err)
		return
	_latch_ft = {}
	# a: hold the centre at corner height (the legs carry the ring over its flat sides)
	var hold := meth == "a"
	var lift := 0.0
	var push_k := 1.0
	if hold:
		var ht := ring_target()
		ring_info["ht"] = ht
		var herr := ht - (c.y - gy)                      # > 0: centre too low
		lift = herr
		if meth == "c":
			_ring_i = clampf(_ring_i + herr * dt, -0.02, 0.02)
			var om: float = (m.bodies[m.seg_body[0]]["rb"] as RigidBody3D).angular_velocity.dot(ax)
			var ahead := _support(c, ax, om * 0.12) - _support(c, ax)   # the support shrinks soon (a corner passes): extend before
			lift = herr + 4.0 * _ring_i - ahead
			if m.ground_contacts() < 3:
				lift += 0.01                                   # fewer than 3 contacts: press the planted feet harder
			_ring_vt = lerpf(_ring_vt, absf(_ring_v), clampf(dt * 0.3, 0.0, 1.0))
			if _ring_vt > 0.02:
				push_k = clampf(1.0 + 1.5 * (_ring_vt - absf(_ring_v)) / _ring_vt, 0.3, 1.6)
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
			if hold:
				press = clampf(lift, -0.02, 0.08) + clampf(float(s) * lean_err * ring_k, -0.03, 0.03)
			var foot := Vector3.ZERO
			var use := false
			if absf(drive) > 0.05 and behind > ring_push[0] and behind < ring_push[1]:
				var back := sqrt(maxf(0.0, reach * reach - lat * lat - (h + press) * (h + press))) * absf(drive) * minf(push_k, 1.0 / 0.97)
				foot = hip + ax * float(s) * lat - fw * dirv * back
				use = true
				pushing += 1
			elif (hold and absf(ang) < (100.0 if meth == "c" else 70.0)) or (absf(drive) <= 0.05 and absf(ang) < 55.0):
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
	ring_info["ok"] = true
	ring_info["lean"] = ring_lean
	ring_info["pushing"] = pushing
	ring_info["centre"] = c


func _ring_c(dt: float, rs: Dictionary, lean_err: float) -> void:
	"""c «Füsse passen sich an» (abrollen): every leg near the bottom plants its foot and keeps it there, the ring rolls
	over the feet. Each step the legs aim at a wanted ring pose a little ahead: forward by the wanted speed, up / down to
	the wanted height, turned as a wheel of that height would turn, tilted for curves. ≥ 3 contacts: all legs within
	±100° of the bottom that reach the ground stand on it; fewer than 3 → they press harder."""
	var N: int = m.n()
	var c: Vector3 = rs["c"]
	var ax: Vector3 = rs["ax"]
	var fw: Vector3 = rs["fw"]
	var gy: float = rs["gy"]
	var w: float = m.u("halbe_breite")
	var reach: float = (m.u("oberschenkel") + m.u("unterschenkel")) * 0.97
	var lat := ring_lat()
	var ht := ring_target()
	var vt := drive * maxf(tempo * c_speed, 0.08)
	var dx := vt * c_lead + c_kv * (vt - _ring_v) * c_lead
	var dy := c_kh * (ht - (c.y - gy))
	var pivot := c
	var des := Transform3D(Basis(fw, lean_err * c_tilt) * Basis(ax, -dx / maxf(ht, 0.05)), Vector3.ZERO)
	des = Transform3D(des.basis, pivot + fw * dx + Vector3.UP * dy - des.basis * pivot)
	var press := 0.004 + (0.006 if m.ground_contacts() < 3 else 0.0)
	var d := {}
	var planted := 0
	for i in range(N):
		var xf: Transform3D = m.segment_xf(i)
		var dxf: Transform3D = des * xf
		var r := xf.origin - c
		var ang := rad_to_deg(atan2(Vector3.DOWN.cross(r).dot(ax), Vector3.DOWN.dot(r)))
		for s in [-1, 1]:
			var key := "%d%d" % [i, s]
			var sd := "l" if s < 0 else "r"
			var hip: Vector3 = xf * Vector3(0, 0, s * w)
			var want: Vector3 = hip + ax * float(s) * lat
			var g := _ground_at(want, hip.y + 0.05, gy)
			var ok := absf(ang) < c_win and hip.y - g < reach * 0.95
			if ok and not _latch_ft.has(key):
				_latch_ft[key] = Vector3(want.x, g, want.z)      # touch down below the hip
			if _latch_ft.has(key) and (not ok or ((_latch_ft[key] as Vector3) - hip).length() > reach):
				_latch_ft.erase(key)                            # left the window or stretched out: lift
			if _latch_ft.has(key):
				var ft: Vector3 = _latch_ft[key] - Vector3(0, press, 0)
				var a := leg_ik(s, dxf.affine_inverse() * ft)
				d["hy%d%s" % [i, sd]] = a[0]
				d["hp%d%s" % [i, sd]] = a[1]
				d["kn%d%s" % [i, sd]] = a[2]
				planted += 1
			else:
				d["hy%d%s" % [i, sd]] = 0.0
				d["hp%d%s" % [i, sd]] = 0.0
				d["kn%d%s" % [i, sd]] = 0.0
	apply(d)
	ring_info["ok"] = true
	ring_info["lean"] = ring_lean
	ring_info["pushing"] = planted
	ring_info["centre"] = c
	ring_info["ht"] = ht


func spoke_radius() -> float:
	"""b: the biggest foot circle every leg reaches with room for ±spoke_k"""
	var a: float = m.pitch_len() * 0.5 / tan(PI / m.n())
	var reach: float = (m.u("oberschenkel") + m.u("unterschenkel")) * 0.92 / (1.0 + spoke_k)
	var off := deg_to_rad(90.0 / m.n())                   # 2 N spokes, evenly spread (4er: ±22.5°, 6er: ±15°, 8er: ±11.25°)
	var sn := sin(off)
	var cs := cos(off)
	# |(R sn, R cs − a)| = reach  →  R² − 2 R a cs + a² − reach² = 0
	var disc := a * a * cs * cs - (a * a - reach * reach)
	return a * cs + sqrt(maxf(0.0, disc))


func _ring_spokes(rs: Dictionary) -> void:
	"""b: every leg a spoke in the ring plane, the feet on a circle; drive = longer spokes behind, shorter ahead"""
	var c: Vector3 = rs["c"]
	var ax: Vector3 = rs["ax"]
	var w: float = m.u("halbe_breite")
	var rf := clampf(ring_target(), corner_height() + 0.005, spoke_radius())
	var dirv := 1.0 if drive >= 0.0 else -1.0
	var d := {}
	for i in range(m.n()):
		var xf: Transform3D = m.segment_xf(i)
		var radial: Vector3 = -xf.basis.y.normalized()
		for s in [-1, 1]:
			var dir := Basis(ax, deg_to_rad(90.0 / m.n()) * float(s)) * radial
			var ang := atan2(Vector3.DOWN.cross(dir).dot(ax), Vector3.DOWN.dot(dir))   # + = ahead of the bottom
			var k := 1.0 - spoke_k * drive * sin(clampf(ang * dirv, -PI * 0.5, PI * 0.5)) * dirv
			k *= 1.0 + spoke_turn * turn * float(s)
			var foot: Vector3 = c + dir * rf * k + ax * float(s) * (w + ring_lat())
			var a := leg_ik(s, xf.affine_inverse() * foot)
			var sd := "l" if s < 0 else "r"
			d["hy%d%s" % [i, sd]] = a[0]
			d["hp%d%s" % [i, sd]] = a[1]
			d["kn%d%s" % [i, sd]] = a[2]
	apply(d)
	ring_info["ok"] = true
	ring_info["lean"] = ring_lean
	ring_info["centre"] = c


func _ground_at(p: Vector3, from_y: float, fallback: float) -> float:
	"""height of the terrain under p (ray down, terrain layer only)"""
	var w3: World3D = m.get_world_3d()
	if w3 == null:
		return fallback
	var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, from_y, p.z), Vector3(p.x, from_y - 1.0, p.z), m.LAYER_GELAENDE)
	var hit := w3.direct_space_state.intersect_ray(q)
	return float((hit["position"] as Vector3).y) if not hit.is_empty() else fallback


func start_ring() -> void:
	if not m.ring_ok():
		return                                 # 2 / 3 Segmente: kein Ring
	latch_restore()
	mode = "ring"
	seq = []
	seq_name = ""
	goal = null
