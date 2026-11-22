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
	var sc: float = m.p["massstab"]
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
