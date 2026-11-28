extends "res://scripts/roboter_bewegung.gd"
## Roboter-Labor: Bewegungen der klassischen Laufroboter (roboter_klassisch_modell.gd, Besitzer 28.11.2026 14:40).
## Bein-Rechnung (leg_ik / leg_fk), stand_foot, level_foot, _ground_at, apply, stop, set_goal und _plan_goal kommen
## unverändert vom Segment-Roboter (roboter_bewegung.gd): die Füsse rechnen im Rahmen des Beinpaars (m.segment_xf(i)).
## Eigene Posen (stehen, sitzen, liegen, Beine eingeklappt), eigene Gangarten, kein Ring.
##
## Gangarten (τ = Zeitpunkt, an dem das Bein abhebt, als Anteil des Schrittzyklus; β = Anteil am Boden):
##   Vierbeiner  schritt  statisch stabil: ein Bein nach dem anderen (hinten links, vorne links, hinten rechts, vorne
##                        rechts), β 0.8; der Körper schiebt sich vorher über das Dreieck der drei stehenden Füsse
##               trab     diagonal: vorne links + hinten rechts, dann vorne rechts + hinten links, β 0.55
##               pass     Passgang: beide linken, dann beide rechten Beine, β 0.55 (der Körper wiegt sich seitlich)
##   Sechsbeiner dreifuss vorne links, Mitte rechts, hinten links - dann die anderen drei, β 0.55 (schnell, immer 3 Füsse)
##               welle    Wellengang: ein Bein aufs Mal, hinten nach vorne, erst links, dann rechts, β 0.84 (langsam)
##               raupe    Raupengang («ripple»): je Seite eine Welle hinten → vorne, die Seiten um einen halben Zyklus
##                        versetzt, β 0.72
##   auto        wählt selbst: Vierbeiner Schritt bei langsamem Tempo oder Überlast, sonst Trab; Sechsbeiner Welle bei
##               Überlast, Raupengang langsam, sonst Dreifuss
## Richtungen: jeder Fuss bekommt seinen Schritt-Vektor = Körper-Geschwindigkeit + Drehung × Hebel (vor / zurück,
## seitwärts, schräg, an Ort drehen und Kurven = vorwärts + drehen). «anpassen»: Höhe je Beinpaar über dem Boden
## (Ausgleichsgerade über die Paare: der Körper neigt sich mit dem Hang), jeder Fuss sucht seinen Boden und hält an,
## wenn er früher aufsetzt.

const POSEN_K := [["stehen", "Stehen"], ["sitzen", "Sitzen"], ["liegen", "Liegen"], ["eingeklappt", "Beine eingeklappt"]]
const GAENGE_4 := [["schritt", "Schritt"], ["trab", "Trab"], ["pass", "Passgang"], ["auto", "Automatisch"]]
const GAENGE_6 := [["dreifuss", "Dreifuss"], ["welle", "Wellengang"], ["raupe", "Raupengang"], ["auto", "Automatisch"]]
const ABLAEUFE_K := [["aufstehen", "Aufstehen"], ["hinlegen", "Hinlegen"]]
const BETA_K := {"schritt": 0.8, "trab": 0.55, "pass": 0.55, "dreifuss": 0.55, "welle": 0.84, "raupe": 0.72}
const SCHIEBEN_K := {"schritt": 0.9, "pass": 0.7, "welle": 0.6, "raupe": 0.35}   # body shift over the standing feet (share; pass = sway to the side)

var schieben := Vector2.ZERO           # body shift now (m, x vor, y = z rechts) - for tests and the display
var stuetz_fuesse := 0                 # feet on the ground in the plan right now


func posen() -> Array:
	return POSEN_K


func gaenge() -> Array:
	return GAENGE_6 if m != null and m.n() == 3 else GAENGE_4


func ablaeufe() -> Array:
	return ABLAEUFE_K


# ---- Posen ---------------------------------------------------------------------------------------------------------------
func pose(name: String) -> Dictionary:
	"""servo id -> degrees; unknown names (also «gerade» of the segment robot) = «stehen»"""
	var d := {}
	var N: int = m.n()
	var hk: float = float(m.bp["halbe_hoehe"])
	for i in range(N):
		var k := float(i) / float(maxi(1, N - 1))       # 0 front … 1 rear
		match name:
			"eingeklappt":
				for sd in ["l", "r"]:
					d["hy%d%s" % [i, sd]] = 0.0
					d["hp%d%s" % [i, sd]] = 75.0
					d["kn%d%s" % [i, sd]] = 165.0
			"liegen":
				var fl := stand_foot(-1, hk * 0.6)
				var fr := stand_foot(1, hk * 0.6)
				fl.z -= spreiz * float(m.bp["massstab"]) * 0.2
				fr.z += spreiz * float(m.bp["massstab"]) * 0.2
				_legs(d, i, fl, fr)
			"sitzen":
				var h := lerpf(hoehe * 1.3, hk * 1.1, k)       # front high, rear low: the body sits on its back end
				var fl2 := stand_foot(-1, h)
				var fr2 := stand_foot(1, h)
				var fx := lerpf(0.0, 0.4, k) * float(m.bp["massstab"])   # rear feet a little forward (under the hips)
				fl2.x += fx
				fr2.x += fx
				_legs(d, i, fl2, fr2)
			_:
				_legs(d, i, stand_foot(-1), stand_foot(1))
	d["pan"] = 0.0
	return d


# ---- Gangarten -----------------------------------------------------------------------------------------------------------
func start_gang(g: String) -> void:
	var ids := gaenge().map(func(x): return x[0])
	gang = g if g in ids else "auto"
	_prog_t = 0.0
	_prog_p = m.segment_xf(0).origin if m != null and m.built_ok else Vector3.ZERO
	mode = "gang"
	seq = []
	seq_name = ""


func phase_of(g: String, i: int, s: int) -> float:
	"""τ: when this leg lifts off (share of the step cycle); i = leg pair (0 front), s = side (−1 links)"""
	var N: int = m.n()
	var left := s < 0
	match g:
		"schritt":
			if i == N - 1:
				return 0.0 if left else 0.5
			return 0.25 if left else 0.75
		"trab":
			return 0.0 if (i == 0) == left else 0.5
		"pass":
			return 0.0 if left else 0.5
		"dreifuss":
			return 0.0 if (i % 2 == 0) == left else 0.5
		"welle":
			return (float(N - 1 - i) + (0.0 if left else float(N))) / float(2 * N)
		"raupe":
			return fposmod(float(N - 1 - i) / float(N) + (0.0 if left else 0.5), 1.0)
	return 0.0


func _auto_gang(speed: float) -> String:
	var over_leg := false
	for id in m.overloaded():
		if str(id).substr(0, 2) in ["hy", "hp", "kn"]:
			over_leg = true
	if m.n() == 3:
		if over_leg:
			return "welle"
		return "dreifuss" if speed > 0.05 else "raupe"
	return "trab" if speed > 0.05 and not over_leg else "schritt"


func _gang_step(dt: float) -> void:
	var sc: float = m.bp["massstab"]
	var N: int = m.n()
	var want := cmd
	if goal != null and cmd == Vector3.ZERO:
		want = _plan_goal()
	side = move_toward(side, want.x, dt * 2.0)
	drive = move_toward(drive, want.y, dt * 2.0)
	turn = move_toward(turn, want.z, dt * 1.5)
	var vx := drive * tempo
	var vz := -side * tempo                                     # + side = links = −Z
	var foot_z: float = stand_foot(1).z
	var rmax := maxf(0.05, Vector2(m.leg_x(0), foot_z).length())
	var om := turn * tempo / rmax                               # rad/s, + = links: the outer feet at «tempo»
	var speed := 0.0
	for i in range(N):
		for s in [-1, 1]:
			speed = maxf(speed, Vector2(vx + om * s * foot_z, vz - om * m.leg_x(i)).length())
	gang_now = _auto_gang(speed) if gang == "auto" else gang
	if gang == "auto" and speed > 0.01 and absf(vx) > 0.5 * speed:
		_prog_t += dt
		if _prog_t >= 3.0:
			var pnow: Vector3 = m.segment_xf(0).origin
			if not angepasst and pnow.distance_to(_prog_p) < 0.25 * speed * _prog_t:
				angepasst = true                                # stuck: higher steps, body higher
				schritt_hoehe = maxf(schritt_hoehe, 0.8)
				hoehe = maxf(hoehe, 1.2)
			_prog_t = 0.0
			_prog_p = pnow
	var beta: float = BETA_K.get(gang_now, 0.75)
	var amax := schritt_laenge * sc * 0.5
	var moving := speed > 0.002
	_amp = move_toward(_amp, amax if moving else 0.0, dt * amax * 2.0)
	var T := 1.0
	if _amp > 0.0005:
		T = clampf(2.0 * amax / (beta * maxf(speed, 0.01)), 0.4, 6.0)
		phase = fposmod(phase + dt / T, 1.0)
	var kamp := clampf(_amp / maxf(amax, 1e-4), 0.0, 1.0)
	var lift := schritt_hoehe * sc * kamp * (1.4 if gang_now == "pass" else 1.0)
	var hh: float = hoehe * sc
	var bx: Transform3D = m.body_xf()
	var fx := bx.basis.x
	fx.y = 0.0
	fx = fx.normalized() if fx.length() > 0.1 else Vector3.RIGHT
	var lvl := Basis(fx, Vector3.UP, fx.cross(Vector3.UP))
	# wanted height of every leg pair: ground under its feet / the body, a straight line over the pairs (rigid body)
	var ydes := []
	for i in range(N):
		var po: Vector3 = m.segment_xf(i).origin
		if not anpassen:
			ydes.append(po.y)
			continue
		var gs := 0.0
		for s in [-1, 1]:
			gs += _ground_at(po + lvl * Vector3(0, 0, s * foot_z), po.y + 0.4, po.y - hh)
		var g := maxf(gs * 0.5, _ground_at(po, po.y + 0.4, po.y - hh) + float(m.u("halbe_hoehe")) + 0.01 - hh)
		ydes.append(g + hh)
	if anpassen and N > 2:
		var sx := 0.0
		var sy := 0.0
		var sxx := 0.0
		var sxy := 0.0
		for i in range(N):
			var x: float = m.leg_x(i)
			sx += x
			sy += float(ydes[i])
			sxx += x * x
			sxy += x * float(ydes[i])
		var b := (N * sxy - sx * sy) / maxf(1e-9, N * sxx - sx * sx)
		var a := (sy - b * sx) / N
		for i in range(N):
			ydes[i] = maxf(a + b * m.leg_x(i), float(ydes[i]) - 0.01)
	# shift the body over the standing feet before a leg lifts (statically stable gaits)
	var kshift: float = SCHIEBEN_K.get(gang_now, 0.0) * kamp
	var width := clampf(1.0 - beta + 0.08, 0.15, 0.5)
	var cen := Vector2.ZERO
	var wsum := 0.0
	var mean := Vector2.ZERO
	for i in range(N):
		for s in [-1, 1]:
			var nominal := Vector2(m.leg_x(i), s * foot_z)
			mean += nominal / (2.0 * N)
			var mid := fposmod(phase - phase_of(gang_now, i, s) - (1.0 - beta) * 0.5, 1.0)   # 0 = middle of its swing
			mid = minf(mid, 1.0 - mid)
			var wgt := clampf(mid / width, 0.0, 1.0)
			cen += nominal * wgt
			wsum += wgt
	var want_shift := (cen / wsum - mean) * kshift if wsum > 0.01 else Vector2.ZERO
	schieben = schieben.lerp(want_shift, clampf(dt * 12.0, 0.0, 1.0))
	var d := {}
	stuetz_fuesse = 0
	for i in range(N):
		var xf: Transform3D = m.segment_xf(i)
		var xi: float = m.leg_x(i)
		for s in [-1, 1]:
			var f := stand_foot(s)
			var vf := Vector2(vx + om * f.z, vz - om * xi)
			var a2 := vf * beta * T * 0.5
			if a2.length() > amax:
				a2 = a2.normalized() * amax
			a2 *= kamp
			var u := fposmod(phase - phase_of(gang_now, i, s), 1.0)   # 0 … 1−β swing, then stance
			var off := Vector2.ZERO
			var y := 0.0
			var swing_down := false
			var sw := 1.0 - beta
			if u >= sw or kamp < 0.02:
				off = a2 * (1.0 - 2.0 * (u - sw) / beta) if u >= sw else Vector2.ZERO
				stuetz_fuesse += 1
			else:
				var q := u / sw
				swing_down = q > 0.5
				var qs := q * q * (3.0 - 2.0 * q)
				off = a2 * (-1.0 + 2.0 * qs)
				y = lift * sin(PI * q)
			f.x += off.x - schieben.x
			f.z += off.y - schieben.y
			if anpassen:
				var fw: Vector3 = xf.origin + lvl * Vector3(f.x, 0.0, f.z)
				var gf := _ground_at(fw, xf.origin.y + 0.3, float(ydes[i]) - hh)
				f.y = gf - float(ydes[i]) + y
				if swing_down and m.foot_contact(i, s):
					var meas: Vector3 = m.foot_world(i, s)
					f.y = maxf(f.y, meas.y - float(ydes[i]))
			else:
				f.y += y
			var fs: Vector3 = xf.basis.orthonormalized().inverse() * (lvl * f) if anpassen else level_foot(i, s, f)
			var a := leg_ik(s, fs)
			var sd := "l" if s < 0 else "r"
			d["hy%d%s" % [i, sd]] = a[0]
			d["hp%d%s" % [i, sd]] = a[1]
			d["kn%d%s" % [i, sd]] = a[2]
	apply(d)


# ---- Abläufe -------------------------------------------------------------------------------------------------------------
func start_ablauf(name: String) -> void:
	match name:
		"aufstehen":
			seq = [{"t": 1.5, "pose": pose("eingeklappt")}, {"t": 1.5, "pose": pose("liegen")}, {"t": 2.0, "pose": pose("stehen")}]
		"hinlegen":
			seq = [{"t": 2.0, "pose": pose("liegen")}]
		_:
			return
	seq_name = name
	seq_i = 0
	seq_t = 0.0
	mode = "ablauf"
	goal = null
	_seq_from = m.targets()


# ---- kein Ring -----------------------------------------------------------------------------------------------------------
func start_ring() -> void:
	pass


func _ring_step(_dt: float) -> void:
	ring_info = {"ok": false}


func ring_height_max() -> float:
	return 0.0


func corner_height() -> float:
	return 0.0
