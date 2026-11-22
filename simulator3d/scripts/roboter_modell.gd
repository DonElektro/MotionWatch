extends Node3D
## Roboter-Labor (Besitzer 22.11.2026, Fragebogen 15:36–15:40): der Segment-Roboter des Besitzers als Physik-Modell.
## Form wie segment_roboter/modell.json (Stand 22.11.2026): 8 Segmente mit quadratischem Querschnitt und 45°-Schrägen an
## beiden Enden, 7 Segmentgelenke mit je 2 Servos (hoch / runter ±90°, links / rechts ±90°), 16 Beine mit je 3 Achsen
## (Hüfte vor / zurück, Hüfte hoch / runter, Knie 360°), Kamera auf kurzem Mast auf dem vordersten Segment (Schwenk),
## Kupplung vorne Kegelzapfen, hinten Hülse mit Riegel (verriegelt im Ring 8 × 45°, Rücken innen, Bauch aussen).
## Einheiten der Vorlage sind relativ: «massstab» = Meter pro Einheit (Start 0.10 → ein Segment 16 cm lang).
##
## Physik (Wahl für Stabilität, gemessen in Godot 4.3 / GodotPhysics, 22.11.2026):
##   · jeder Körper ein RigidBody3D, jede Servo-Achse ein HingeJoint3D mit Geschwindigkeits-Motor (der Motor wird im
##     Löser gerechnet, also auch bei harten Servos stabil). Generic6DOFJoint3D taugt NICHT: sein Winkel-Motor beachtet
##     die Kraftgrenze nicht (hält jede Last). Beim Hinge gilt die Grenze pro Löser-Durchgang: wirksames Moment =
##     max_impulse × Durchgänge / dt (gemessen: Hebel 0.98 N·m kippt bei 0.48·10⁻³, hält bei 0.54·10⁻³, 16 Durchgänge,
##     120 Hz) - darum max_impulse = Moment × dt / Durchgänge.
##   · 2-Achs-Gelenke (Segmentgelenk, Hüfte) = zwei Hinges mit einem kleinen «Bügel»-Körper dazwischen (wie im README:
##     «Gelenk über kurzen Bügel»). Der Bügel bekommt ein künstlich grösseres Trägheitsmoment (Ketten bleiben ruhig).
##   · Servo = Lageregler: Sollwert läuft mit der Servo-Geschwindigkeit zum Ziel, Motor-Geschwindigkeit =
##     K · (Soll − Ist), begrenzt; das Moment begrenzt der Motor selbst (Regler «Servo-Moment»).
##   · Kein physikalischer Selbstkontakt der Roboterteile (Ebene 2 stösst nur an Ebene 1 = Gelände): Teile, die sich
##     durchdringen, werden mit einer Formabfrage gefunden und ROT gezeigt (stabiler als harte Selbstkollision).
##   · Servo-Last = quasi-statisches Moment um die Achse aus Schwerkraft und Bodenkontakten (Kontakt-Impulse) aller
##     Teile hinter dem Servo. Im verriegelten Ring ist das statisch unbestimmt (Riegel trägt mit) → Schätzung.
## Index 0 = vorderstes Segment (Kamera, Kegelzapfen), N-1 = hinterstes (Hülse mit Riegel). Segment-Koordinaten:
## X nach vorne, Y nach oben, Z nach rechts; Seite s = +1 rechts, −1 links.

const LAYER_GELAENDE := 1
const LAYER_ROBOTER := 2

# Startwerte aus modell.json (Einheiten relativ) + Physik-Annahmen (reale Masse sind offen)
const START := {
	"segmente": 8, "halbe_breite": 0.45, "halbe_breite_spitze": 0.10, "laenge_mittelteil": 0.80, "abstand_gelenk": 0.12,
	"oberschenkel": 1.19, "unterschenkel": 1.05, "mast_hoehe": 0.30,
	"massstab": 0.10,              # m pro Einheit
	"masse_segment": 0.30,         # kg je Segment (mit den 2 Servos des Gelenks, Anteil Akku / Elektronik)
	"masse_bein": 0.15,            # kg je Bein (3 Servos, Bügel, Ober- und Unterschenkel)
	"moment_koerper": 3.5,         # N·m Segmentgelenk-Servo (z. B. 35 kg·cm)
	"moment_bein": 1.5,            # N·m Bein-Servo
	"tempo_servo": 300.0,          # °/s ohne Last
	"reibung": 0.9,                # Fuss / Bauch auf dem Boden
	"strom_stall": 2.5,            # A je Servo bei vollem Moment (Schätzung)
	"strom_ruhe": 0.01,            # A je Servo im Stillstand ohne Last
}
const GRENZEN := {
	"segmente": [2, 12], "halbe_breite": [0.2, 0.8], "halbe_breite_spitze": [0.04, 0.3], "laenge_mittelteil": [0.3, 1.6],
	"abstand_gelenk": [0.06, 0.4], "oberschenkel": [0.4, 2.0], "unterschenkel": [0.3, 2.0], "mast_hoehe": [0.1, 0.8],
	"massstab": [0.05, 0.40], "masse_segment": [0.05, 2.0], "masse_bein": [0.02, 1.0], "moment_koerper": [0.2, 15.0],
	"moment_bein": [0.1, 8.0], "tempo_servo": [30.0, 720.0], "reibung": [0.05, 1.5],
}
const LOESER := 24                 # Löser-Durchgänge in der eigenen Welt (PhysicsServer3D space param)
# «Armatur» (wie in MuJoCo): das Trägheitsmoment von Motor und Getriebe, das am Gelenk wirkt (Läufer × Übersetzung²,
# bei einem MG996R rund 10⁻³ kg·m²). Es kommt zu dem Teil hinter dem Servo dazu - physikalisch richtig und es hält die
# leichten Beine im iterativen Löser steif (ohne: 2–4° bleibender Fehler bei kleiner Last, gemessen 22.11.2026).
const ARMATUR := {"buegel": 2.0e-3, "seg": 1.0e-3, "huefte": 6.0e-4, "ober": 6.0e-4, "unter": 4.0e-4}
const K_LAGE := 14.0               # 1/s: Motor-Geschwindigkeit pro Winkelfehler
const FARBE := {"koerper": Color("#a3a198"), "gelenk": Color("#7f77dd"), "huefte": Color("#1d9e75"), "bein": Color("#5f5e5a"),
		"knie": Color("#d85a30"), "kamera": Color("#2c2c2a"), "linse": Color("#378add"), "kupplung": Color("#ef9f27"),
		"rot": Color("#ff2d2d"), "locked": Color("#639922")}

var p := START.duplicate()          # what the sliders say (torque, speed, friction, current: live)
var bp := START.duplicate()         # the shape the robot was built with (geometry, masses) - p until the next build
var bodies: Array = []             # {rb, kind, seg, side, off (frame -> body), mis [MeshInstance3D], mat, shape_cs}
var servos: Array = []             # see _servo()
var seg_body: Array = []           # index of the body of segment i
var fk_order: Array = []           # servo indices in parent-before-child order
var root_xf := Transform3D()       # where segment 0 stands when (re)built
var pan_servo := -1                # camera pan (kinematic, mesh only)
var latch := {"state": "open", "joint": null, "err_pos": 99.0, "err_ang": 180.0}   # open | grip | locked
var latch_wanted := true           # Riegel darf schliessen
var cam_head: Node3D               # pan node on segment 0
var robot_cam: Node3D              # where the front camera sits and looks (-Z, like a Camera3D)
var collide := {}                  # body index -> true (rot)
var _excl := []                    # body index -> [RID] not to test against (≤ 2 joints away)
var _tick := 0
var space_rid := RID()
var hold := false                  # «Festhalten»: segment in the middle frozen in the air
var total_current := 0.0
var total_mass := 0.0
var _mat_red: StandardMaterial3D
var built_ok := false


# ---- Masse (Einheiten -> Meter) ------------------------------------------------------------------------------------------
func n() -> int:
	return int(bp["segmente"])

func u(k: String) -> float:
	return float(bp[k]) * float(bp["massstab"])

func run_len() -> float:                 # Länge der 45°-Schräge (Einheit Meter)
	return maxf(0.0, u("halbe_breite") - u("halbe_breite_spitze"))

func pitch_len() -> float:               # Rastermass Segment zu Segment
	return u("laenge_mittelteil") + 2.0 * run_len() + u("abstand_gelenk")

func actuator_count() -> int:            # Servos: 2 je Segmentgelenk + 3 je Bein + Kamera + Riegel
	return 2 * (n() - 1) + 6 * n() + 2


func set_param(k: String, v) -> void:
	if not p.has(k):
		return
	var g = GRENZEN.get(k, null)
	var val = float(v)
	if g != null:
		val = clampf(val, float(g[0]), float(g[1]))
	p[k] = int(round(val)) if k == "segmente" else val


# ---- Aufbau --------------------------------------------------------------------------------------------------------------
func clear() -> void:
	unlock()
	for c in get_children():
		remove_child(c)
		c.free()
	bodies = []
	servos = []
	seg_body = []
	fk_order = []
	collide = {}
	_excl = []
	pan_servo = -1
	cam_head = null
	robot_cam = null
	built_ok = false


func build(at: Transform3D, angles := {}) -> void:
	"""builds the robot with segment 0 at «at» in the zero pose (joints made there), then moves it into the pose «angles»
	(servo id -> degrees; missing = 0) and onto the ground (lowest point at at.origin.y)"""
	clear()
	bp = p.duplicate()
	root_xf = at
	_mat_red = StandardMaterial3D.new()
	_mat_red.albedo_color = FARBE["rot"]
	_mat_red.emission_enabled = true
	_mat_red.emission = Color(0.6, 0.0, 0.0)
	var N := n()
	var P := pitch_len()
	var w := u("halbe_breite")
	var ms := float(bp["masse_segment"])
	var mb := float(bp["masse_bein"])
	var lf := u("oberschenkel")
	var lt := u("unterschenkel")
	# bodies + servos (parent before child)
	seg_body.append(_body("seg", 0, 0, ms * (0.88 if N > 1 else 1.0)))
	for i in range(N):
		var sb: int = seg_body[i]
		for s in [-1, 1]:
			var hb := _body("huefte", i, s, mb * 0.4)
			_servo("hy", i, s, sb, hb, Vector3.UP, s, Vector3(0, 0, s * w), Vector3.ZERO, -90, 90, "moment_bein")
			var fb := _body("ober", i, s, mb * 0.4, Transform3D(Basis(), Vector3(0, 0, s * lf * 0.5)))
			_servo("hp", i, s, hb, fb, Vector3.RIGHT, -s, Vector3.ZERO, Vector3.ZERO, -90, 90, "moment_bein")
			var tb := _body("unter", i, s, mb * 0.2, Transform3D(Basis(), Vector3(0, 0, s * lt * 0.5)))
			_servo("kn", i, s, fb, tb, Vector3.RIGHT, s, Vector3(0, 0, s * lf), Vector3.ZERO, -180, 180, "moment_bein")
		if i < N - 1:
			var jb := _body("buegel", i, 0, ms * 0.12)
			_servo("sy", i, 0, sb, jb, Vector3.UP, 1, Vector3(-P * 0.5, 0, 0), Vector3.ZERO, -90, 90, "moment_koerper")
			var nb := _body("seg", i + 1, 0, ms * 0.88)
			seg_body.append(nb)
			_servo("sp", i, 0, jb, nb, Vector3.BACK, -1, Vector3.ZERO, Vector3(-P * 0.5, 0, 0), -90, 90, "moment_koerper")
	# camera pan + latch (no body of their own)
	pan_servo = _servo("pan", 0, 0, -1, -1, Vector3.UP, 1, Vector3.ZERO, Vector3.ZERO, -170, 170, "moment_bein")
	_servo("riegel", N - 1, 0, -1, -1, Vector3.UP, 1, Vector3.ZERO, Vector3.ZERO, 0, 1, "moment_bein")
	total_mass = 0.0
	for b in bodies:
		total_mass += (b["rb"] as RigidBody3D).mass
	# zero pose -> joints
	var zero := fk({})
	for bi in range(bodies.size()):
		(bodies[bi]["rb"] as RigidBody3D).global_transform = zero[bi] * bodies[bi]["off"]
	for si in fk_order:
		_make_joint(si, zero)
	_make_excl()
	# the wanted pose, on the ground
	for k in angles:
		set_target(str(k), float(angles[k]))
	place(true)
	built_ok = true


func _body(kind: String, seg: int, side: int, mass: float, off := Transform3D()) -> int:
	var rb := RigidBody3D.new()
	rb.mass = maxf(0.005, mass)
	rb.collision_layer = LAYER_ROBOTER
	rb.collision_mask = LAYER_GELAENDE
	rb.contact_monitor = true
	rb.max_contacts_reported = 6
	rb.can_sleep = false
	rb.angular_damp = 0.5
	var pm := PhysicsMaterial.new()
	pm.friction = float(p["reibung"])
	pm.rough = false
	rb.physics_material_override = pm
	rb.name = "%s_%d_%d" % [kind, seg, side + 1]
	add_child(rb)
	var cs := CollisionShape3D.new()
	var mis := []
	var col: Color = FARBE["koerper"]
	var w := u("halbe_breite")
	var t := u("halbe_breite_spitze")
	var L := u("laenge_mittelteil")
	var run := run_len()
	match kind:
		"seg":
			var pts := PackedVector3Array()
			for x in [-L * 0.5, L * 0.5]:
				for y in [-w, w]:
					for z in [-w, w]:
						pts.append(Vector3(x, y, z))
			for x in [-(L * 0.5 + run), L * 0.5 + run]:
				for y in [-t, t]:
					for z in [-t, t]:
						pts.append(Vector3(x, y, z))
			var sh := ConvexPolygonShape3D.new()
			sh.points = pts
			cs.shape = sh
			var bm := BoxMesh.new()
			bm.size = Vector3(L, 2 * w, 2 * w)
			mis.append(_mesh(rb, bm, Transform3D(), col))
			for sg in [-1, 1]:                   # the bevelled ends: frustums with 4 sides (like modell_3d.html)
				var cm := CylinderMesh.new()
				cm.radial_segments = 4
				cm.rings = 1
				cm.height = maxf(0.001, run)
				cm.top_radius = t * sqrt(2.0)
				cm.bottom_radius = w * sqrt(2.0)
				var bas := Basis(Vector3.BACK, -sg * PI * 0.5) * Basis(Vector3.UP, PI * 0.25)
				mis.append(_mesh(rb, cm, Transform3D(bas, Vector3(sg * (L * 0.5 + run * 0.5), 0, 0)), col))
			if seg == 0:
				_front_parts(rb)
			if seg == n() - 1:
				_rear_parts(rb)
		"buegel":
			var sh := SphereShape3D.new()
			sh.radius = maxf(0.004, t * 0.9)
			cs.shape = sh
			var sm := SphereMesh.new()
			sm.radius = maxf(0.004, u("abstand_gelenk") * 0.9)
			sm.height = sm.radius * 2
			col = FARBE["gelenk"]
			mis.append(_mesh(rb, sm, Transform3D(), col))
		"huefte":
			var sh := SphereShape3D.new()
			sh.radius = maxf(0.004, w * 0.2)
			cs.shape = sh
			var sm := SphereMesh.new()
			sm.radius = maxf(0.004, w * 0.22)
			sm.height = sm.radius * 2
			col = FARBE["huefte"]
			mis.append(_mesh(rb, sm, Transform3D(), col))
		"ober", "unter":
			var lg := u("oberschenkel") if kind == "ober" else u("unterschenkel")
			var r := w * (0.13 if kind == "ober" else 0.11)
			var sh := CapsuleShape3D.new()
			sh.radius = r
			sh.height = maxf(lg, 2 * r + 0.001)
			cs.shape = sh
			cs.transform = Transform3D(Basis(Vector3.RIGHT, PI * 0.5), Vector3.ZERO)
			var cm := CapsuleMesh.new()
			cm.radius = r
			cm.height = sh.height
			col = FARBE["bein"]
			mis.append(_mesh(rb, cm, cs.transform, col))
			if kind == "ober":                    # the knee at the far end
				var km := SphereMesh.new()
				km.radius = r * 1.6
				km.height = km.radius * 2
				mis.append(_mesh(rb, km, Transform3D(Basis(), Vector3(0, 0, side * lg * 0.5)), FARBE["knie"]))
	rb.add_child(cs)
	rb.inertia = _inertia(kind, rb.mass) + Vector3.ONE * float(ARMATUR.get(kind, 0.0))
	bodies.append({"rb": rb, "kind": kind, "seg": seg, "side": side, "off": off, "mis": mis, "col": col, "cs": cs})
	return bodies.size() - 1


func _inertia(kind: String, mass: float) -> Vector3:
	"""inertia of the plain shape (box, capsule, sphere) in the body frame"""
	var w := u("halbe_breite")
	match kind:
		"seg":
			var lx := u("laenge_mittelteil") + run_len()
			var b2 := 4.0 * w * w
			return Vector3(mass * 2.0 * b2 / 12.0, mass * (lx * lx + b2) / 12.0, mass * (lx * lx + b2) / 12.0)
		"ober", "unter":
			var lg := u("oberschenkel") if kind == "ober" else u("unterschenkel")
			var ia := mass * lg * lg / 12.0
			return Vector3(ia, ia, mass * pow(w * 0.12, 2) * 0.5)
	var r := w * 0.3
	return Vector3.ONE * 0.4 * mass * r * r


func _mesh(parent: Node3D, m: Mesh, xf: Transform3D, col: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = m
	mi.transform = xf
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	mat.roughness = 0.85
	mi.material_override = mat
	mi.set_meta("mat", mat)
	parent.add_child(mi)
	return mi


func _front_parts(rb: RigidBody3D) -> void:
	"""segment 0: cone pin in front, mast + pan head with the camera on the back"""
	var w := u("halbe_breite")
	var tip := u("laenge_mittelteil") * 0.5 + run_len()
	var cone := CylinderMesh.new()
	cone.top_radius = 0.0
	cone.bottom_radius = u("halbe_breite_spitze") * 0.9
	cone.height = u("abstand_gelenk") * 1.4
	_mesh(rb, cone, Transform3D(Basis(Vector3.BACK, -PI * 0.5), Vector3(tip + cone.height * 0.5, 0, 0)), FARBE["kupplung"])
	var mh := u("mast_hoehe")
	var mast := CylinderMesh.new()
	mast.top_radius = w * 0.12
	mast.bottom_radius = w * 0.12
	mast.height = mh
	_mesh(rb, mast, Transform3D(Basis(), Vector3(0, w + mh * 0.5, 0)), FARBE["kamera"])
	cam_head = Node3D.new()
	cam_head.name = "kamerakopf"
	cam_head.position = Vector3(0, w + mh, 0)
	rb.add_child(cam_head)
	var hb := BoxMesh.new()
	hb.size = Vector3(w * 0.66, w * 0.44, w * 0.5)
	_mesh(cam_head, hb, Transform3D(Basis(), Vector3(0, w * 0.28, 0)), FARBE["kamera"])
	var lens := CylinderMesh.new()
	lens.top_radius = w * 0.13
	lens.bottom_radius = w * 0.13
	lens.height = w * 0.18
	_mesh(cam_head, lens, Transform3D(Basis(Vector3.BACK, PI * 0.5), Vector3(w * 0.4, w * 0.28, 0)), FARBE["linse"])
	robot_cam = Node3D.new()                           # only a marker: the cameras of the lab copy its place
	robot_cam.name = "roboterkamera"
	robot_cam.position = Vector3(w * 0.5, w * 0.28, 0)
	robot_cam.rotation = Vector3(0, -PI * 0.5, 0)      # Camera3D looks along -Z; the head looks along +X
	cam_head.add_child(robot_cam)


func _rear_parts(rb: RigidBody3D) -> void:
	"""segment N-1: sleeve and latch bolt at the rear tip"""
	var tip := u("laenge_mittelteil") * 0.5 + run_len()
	var sl := CylinderMesh.new()
	sl.top_radius = u("halbe_breite_spitze") * 1.3
	sl.bottom_radius = u("halbe_breite_spitze") * 1.3
	sl.height = u("abstand_gelenk") * 0.6
	_mesh(rb, sl, Transform3D(Basis(Vector3.BACK, PI * 0.5), Vector3(-tip - sl.height * 0.3, 0, 0)), FARBE["kupplung"])
	var bolt := BoxMesh.new()
	bolt.size = Vector3(u("abstand_gelenk") * 0.4, u("halbe_breite_spitze") * 1.6, u("abstand_gelenk") * 0.4)
	var mi := _mesh(rb, bolt, Transform3D(Basis(), Vector3(-tip - sl.height * 0.3, u("halbe_breite_spitze") * 2.2, 0)), FARBE["kupplung"])
	mi.name = "riegel"


func _servo(kind: String, seg: int, side: int, parent: int, child: int, axis: Vector3, k: int, pivot: Vector3, post: Vector3,
		lo: float, hi: float, moment_key: String) -> int:
	var sv := {"kind": kind, "seg": seg, "side": side, "parent": parent, "child": child, "axis": axis, "k": k, "pivot": pivot,
			"post": post, "min": lo, "max": hi, "mk": moment_key, "target": 0.0, "cmd": 0.0, "angle": 0.0, "tau": 0.0,
			"load": 0.0, "current": 0.0, "joint": null, "distal": [], "id": servo_id(kind, seg, side)}
	servos.append(sv)
	var si := servos.size() - 1
	if parent >= 0:
		fk_order.append(si)
	return si


static func servo_id(kind: String, seg: int, side: int) -> String:
	"""sy3 / sp3 (Segmentgelenk 3), hy2l / hp2l / kn2l (Bein 2 links), pan, riegel"""
	if kind in ["pan", "riegel"]:
		return kind
	if kind in ["sy", "sp"]:
		return "%s%d" % [kind, seg]
	return "%s%d%s" % [kind, seg, "l" if side < 0 else "r"]


func servo_index(id: String) -> int:
	for i in range(servos.size()):
		if servos[i]["id"] == id:
			return i
	return -1


func set_target(id: String, deg: float) -> void:
	var i := servo_index(id)
	if i >= 0:
		var sv: Dictionary = servos[i]
		sv["target"] = clampf(deg, float(sv["min"]), float(sv["max"]))


func targets() -> Dictionary:
	var d := {}
	for sv in servos:
		d[sv["id"]] = float(sv["target"])
	return d


# ---- Vorwärts-Kinematik: Lage aller Körper aus den Winkeln ---------------------------------------------------------------
func fk(angles: Dictionary, base := Transform3D(), use_base := false) -> Array:
	"""frame of every body (world) for the servo angles (id -> degrees, missing = 0); segment 0 at root_xf (or base)"""
	var fr := []
	fr.resize(bodies.size())
	fr[seg_body[0]] = base if use_base else root_xf
	for si in fk_order:
		var sv: Dictionary = servos[si]
		var a := deg_to_rad(float(angles.get(sv["id"], 0.0)))
		var pf: Transform3D = fr[sv["parent"]]
		fr[sv["child"]] = pf * Transform3D(Basis(), sv["pivot"]) * Transform3D(Basis(sv["axis"], float(sv["k"]) * a), Vector3.ZERO) \
				* Transform3D(Basis(), sv["post"])
	return fr


func _make_joint(si: int, fr: Array) -> void:
	var sv: Dictionary = servos[si]
	var pf: Transform3D = fr[sv["parent"]]
	var ax: Vector3 = (pf.basis * (sv["axis"] as Vector3)).normalized()
	var j := HingeJoint3D.new()
	var zb: Vector3 = ax
	var xb: Vector3 = zb.cross(Vector3.UP if absf(zb.dot(Vector3.UP)) < 0.9 else Vector3.RIGHT).normalized()
	j.transform = Transform3D(Basis(xb, zb.cross(xb), zb), pf * (sv["pivot"] as Vector3))
	j.name = "J_" + str(sv["id"])
	add_child(j)
	j.node_a = (bodies[sv["parent"]]["rb"] as Node).get_path()
	j.node_b = (bodies[sv["child"]]["rb"] as Node).get_path()
	j.set_flag(HingeJoint3D.FLAG_USE_LIMIT, false)
	j.set_flag(HingeJoint3D.FLAG_ENABLE_MOTOR, true)
	j.set_param(HingeJoint3D.PARAM_MOTOR_TARGET_VELOCITY, 0.0)
	sv["joint"] = j
	# bodies behind this servo (for the load)
	var dist := [sv["child"]]
	var k := 0
	while k < dist.size():
		for sj in fk_order:
			if servos[sj]["parent"] == dist[k] and not dist.has(servos[sj]["child"]):
				dist.append(servos[sj]["child"])
		k += 1
	sv["distal"] = dist


func _make_excl() -> void:
	"""for the red marking: parts at most 2 joints apart touch by design and are not tested against each other"""
	var nb := []
	for i in range(bodies.size()):
		nb.append([])
	for si in fk_order:
		nb[servos[si]["parent"]].append(servos[si]["child"])
		nb[servos[si]["child"]].append(servos[si]["parent"])
	_excl = []
	for i in range(bodies.size()):
		var near := {i: true}
		for a in nb[i]:
			near[a] = true
			for b in nb[a]:
				near[b] = true
		if bodies[i]["kind"] == "seg" and (bodies[i]["seg"] == 0 or bodies[i]["seg"] == n() - 1):
			near[seg_body[0]] = true                 # pin and sleeve touch in the ring
			near[seg_body[n() - 1]] = true
		var rids := []
		for b in near:
			rids.append((bodies[b]["rb"] as RigidBody3D).get_rid())
		_excl.append(rids)


func place(snap_cmd: bool) -> void:
	"""puts all bodies into the pose of the targets (no velocity), lowest point on the ground at root_xf.origin.y"""
	unlock()
	var fr := fk(targets())
	var low := 1e9
	for bi in range(bodies.size()):
		for q in _low_points(bi):
			low = minf(low, (fr[bi] * bodies[bi]["off"] * q).y)
	var lift := root_xf.origin.y + 0.003 - low
	for bi in range(bodies.size()):
		var rb: RigidBody3D = bodies[bi]["rb"]
		var xf: Transform3D = fr[bi] * bodies[bi]["off"]
		xf.origin.y += lift
		rb.global_transform = xf
		rb.linear_velocity = Vector3.ZERO
		rb.angular_velocity = Vector3.ZERO
		PhysicsServer3D.body_set_state(rb.get_rid(), PhysicsServer3D.BODY_STATE_TRANSFORM, xf)
	for sv in servos:
		if snap_cmd:
			sv["cmd"] = sv["target"]
		sv["angle"] = sv["target"]
	latch["state"] = "open"
	if hold:
		set_hold(true)


func _low_points(bi: int) -> Array:
	var b: Dictionary = bodies[bi]
	var w := u("halbe_breite")
	match b["kind"]:
		"seg":
			var L := u("laenge_mittelteil") * 0.5
			var out := []
			for x in [-L, L]:
				for y in [-w, w]:
					for z in [-w, w]:
						out.append(Vector3(x, y, z))
			return out
		"unter":
			var r := w * 0.11
			var h := u("unterschenkel") * 0.5 - r
			return [Vector3(0, -r, b["side"] * h), Vector3(0, -r, -b["side"] * h)]
		"ober":
			return [Vector3(0, -w * 0.13, b["side"] * u("oberschenkel") * 0.5)]
	return [Vector3.ZERO]


func set_hold(on: bool) -> void:
	"""«Festhalten»: the middle segment frozen where it is (poses in the air)"""
	hold = on
	for b in bodies:
		(b["rb"] as RigidBody3D).freeze = false
	if on and bodies.size() > 0:
		var rb: RigidBody3D = bodies[seg_body[n() / 2]]["rb"]
		rb.freeze_mode = RigidBody3D.FREEZE_MODE_STATIC
		rb.freeze = true


# ---- Physik-Schritt: Servos, Lesen, Last, Riegel, Kollision ----------------------------------------------------------------
func frame_of(bi: int) -> Transform3D:
	return (bodies[bi]["rb"] as RigidBody3D).global_transform * (bodies[bi]["off"] as Transform3D).affine_inverse()


static func angle_about(r: Basis, axis: Vector3) -> float:
	var v := Vector3.UP if absf(axis.dot(Vector3.UP)) < 0.9 else Vector3.RIGHT
	v = (v - axis * v.dot(axis)).normalized()
	var rv: Vector3 = r * v
	rv = rv - axis * rv.dot(axis)
	return atan2(axis.dot(v.cross(rv)), v.dot(rv))


func read_angles() -> void:
	for sv in servos:
		if sv["parent"] < 0:
			sv["angle"] = sv["cmd"]
			continue
		var pf := frame_of(sv["parent"])
		var cf := frame_of(sv["child"])
		var rel := pf.basis.orthonormalized().inverse() * cf.basis.orthonormalized()
		var a := rad_to_deg(angle_about(rel, sv["axis"])) * float(sv["k"])
		var prev: float = sv["angle"]
		while a - prev > 180.0:                      # the knee turns 360°: keep it continuous
			a -= 360.0
		while a - prev < -180.0:
			a += 360.0
		sv["angle"] = a


func step(dt: float) -> void:
	if not built_ok:
		return
	_tick += 1
	read_angles()
	var vmax := float(p["tempo_servo"])
	var iters := float(LOESER)
	for sv in servos:
		var tg := clampf(float(sv["target"]), float(sv["min"]), float(sv["max"]))
		sv["cmd"] = move_toward(float(sv["cmd"]), tg, vmax * dt)
		var j: HingeJoint3D = sv["joint"]
		if j == null:
			continue
		var err := float(sv["cmd"]) - float(sv["angle"])
		var wv := clampf(K_LAGE * err, -vmax, vmax)            # °/s
		j.set_param(HingeJoint3D.PARAM_MOTOR_TARGET_VELOCITY, -float(sv["k"]) * deg_to_rad(wv))
		j.set_param(HingeJoint3D.PARAM_MOTOR_MAX_IMPULSE, float(p[sv["mk"]]) * dt / iters)
	if cam_head != null and pan_servo >= 0:
		cam_head.rotation = Vector3(0, deg_to_rad(float(servos[pan_servo]["cmd"])), 0)
	_latch_step(dt)
	if _tick % 4 == 0:
		_loads(dt * 4.0)
	if _tick % 6 == 0:
		_self_collision()


func _loads(_dt: float) -> void:
	"""quasi-static torque about every servo axis: gravity + ground contacts of all parts behind it"""
	var g := Vector3(0, -9.81, 0)
	if space_rid.is_valid():
		g = Vector3(0, -float(PhysicsServer3D.area_get_param(space_rid, PhysicsServer3D.AREA_PARAM_GRAVITY)), 0)
	var F := []
	var M := []
	var pdt := 1.0 / float(Engine.physics_ticks_per_second)
	for b in bodies:
		var rb: RigidBody3D = b["rb"]
		var f: Vector3 = g * rb.mass
		var com: Vector3 = rb.global_transform * rb.center_of_mass
		var m: Vector3 = com.cross(f)
		var st := PhysicsServer3D.body_get_direct_state(rb.get_rid())
		if st != null:
			for ci in range(st.get_contact_count()):
				var fc: Vector3 = st.get_contact_impulse(ci) / pdt
				var pc: Vector3 = st.get_contact_local_position(ci)
				f += fc
				m += pc.cross(fc)
		F.append(f)
		M.append(m)
	var taus := []
	var rows := []                                   # ring: [g (6), servo index] for the joints in the loop
	var h := Vector3.ZERO
	if latch["state"] == "locked":
		h = frame_of(seg_body[n() - 1]) * Vector3(-pitch_len() * 0.5, 0, 0)
	for si in range(servos.size()):
		var sv: Dictionary = servos[si]
		var tau := 0.0
		if sv["parent"] >= 0:
			var pf := frame_of(sv["parent"])
			var piv: Vector3 = pf * (sv["pivot"] as Vector3)
			var ax: Vector3 = (pf.basis.orthonormalized() * (sv["axis"] as Vector3)).normalized()
			var fs := Vector3.ZERO
			var msum := Vector3.ZERO
			for bi in sv["distal"]:
				fs += F[bi]
				msum += M[bi]
			tau = -(msum - piv.cross(fs)).dot(ax)
			if latch["state"] == "locked" and sv["kind"] in ["sy", "sp"]:
				var c := ax.cross(h - piv)
				rows.append([[c.x, c.y, c.z, ax.x, ax.y, ax.z], si])
		taus.append(tau)
	if rows.size() >= 6:
		# closed ring: the latch carries an unknown wrench (force + moment) - take the one with the smallest servo torques
		var A := []
		var bv := [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
		for i in range(6):
			A.append([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
			A[i][i] = 1e-6
		for r in rows:
			var g6: Array = r[0]
			for i in range(6):
				bv[i] += g6[i] * taus[r[1]]
				for k in range(6):
					A[i][k] += g6[i] * g6[k]
		var x := _solve6(A, bv)
		for r in rows:
			var g6: Array = r[0]
			var d := 0.0
			for i in range(6):
				d += g6[i] * x[i]
			taus[r[1]] -= d
	total_current = 0.0
	for si in range(servos.size()):
		var sv: Dictionary = servos[si]
		var tau: float = taus[si]
		var tmax := float(p[sv["mk"]])
		sv["tau"] = tau
		sv["load"] = absf(tau) / maxf(0.001, tmax)
		var moving := absf(float(sv["target"]) - float(sv["cmd"])) > 0.5
		var cur := float(p["strom_ruhe"]) + float(p["strom_stall"]) * minf(1.0, sv["load"]) + (0.15 if moving else 0.0)
		if sv["kind"] == "riegel":
			cur = float(p["strom_ruhe"])
		sv["current"] = cur
		total_current += cur


static func _solve6(A: Array, b: Array) -> Array:
	"""Gauss elimination with pivoting (small dense system)"""
	var nn := b.size()
	var M2 := []
	for i in range(nn):
		M2.append((A[i] as Array).duplicate() + [b[i]])
	for c in range(nn):
		var piv := c
		for r in range(c + 1, nn):
			if absf(M2[r][c]) > absf(M2[piv][c]):
				piv = r
		var tmp = M2[c]
		M2[c] = M2[piv]
		M2[piv] = tmp
		if absf(M2[c][c]) < 1e-12:
			continue
		for r in range(nn):
			if r != c:
				var f: float = M2[r][c] / M2[c][c]
				for k in range(c, nn + 1):
					M2[r][k] -= f * M2[c][k]
	var x := []
	for i in range(nn):
		x.append(M2[i][nn] / M2[i][i] if absf(M2[i][i]) > 1e-12 else 0.0)
	return x


func _self_collision() -> void:
	collide = {}
	var w3 := get_world_3d()
	if w3 == null:
		return
	var ds := w3.direct_space_state
	var q := PhysicsShapeQueryParameters3D.new()
	q.collision_mask = LAYER_ROBOTER
	q.margin = 0.0
	for bi in range(bodies.size()):
		var b: Dictionary = bodies[bi]
		var cs: CollisionShape3D = b["cs"]
		q.shape = cs.shape
		q.transform = cs.global_transform
		q.exclude = _excl[bi]
		var hits := ds.intersect_shape(q, 4)
		for h in hits:
			var other = h.get("collider")
			collide[bi] = true
			for bj in range(bodies.size()):
				if bodies[bj]["rb"] == other:
					collide[bj] = true
	_paint()


func _paint() -> void:
	for bi in range(bodies.size()):
		var red := collide.has(bi)
		for mi in bodies[bi]["mis"]:
			(mi as MeshInstance3D).material_override = _mat_red if red else (mi as MeshInstance3D).get_meta("mat")


func colliding_names() -> Array:
	var out := []
	for bi in collide:
		out.append(str((bodies[bi]["rb"] as Node).name))
	return out


# ---- Kupplung: Kegelzapfen zieht in die Hülse, dann Riegel zu ------------------------------------------------------------
func coupling_error() -> Array:
	"""[position error m, angle error °] between segment 0 and where the closed ring wants it"""
	var N := n()
	if N < 3 or bodies.is_empty():
		return [99.0, 180.0]
	var P := pitch_len()
	var rear := frame_of(seg_body[N - 1])
	var want := rear * Transform3D(Basis(), Vector3(-P * 0.5, 0, 0)) * Transform3D(Basis(Vector3.BACK, -deg_to_rad(360.0 / N)), Vector3.ZERO) \
			* Transform3D(Basis(), Vector3(-P * 0.5, 0, 0))
	var front := frame_of(seg_body[0])
	var pin: Vector3 = front * Vector3(P * 0.5, 0, 0)
	var hole: Vector3 = rear * Vector3(-P * 0.5, 0, 0)
	var rel := want.basis.orthonormalized().inverse() * front.basis.orthonormalized()
	var ang := rad_to_deg(rel.get_rotation_quaternion().get_angle())
	return [pin.distance_to(hole), ang, pin, hole]


func _latch_step(dt: float) -> void:
	var e := coupling_error()
	latch["err_pos"] = e[0]
	latch["err_ang"] = e[1]
	var ri := servo_index("riegel")
	var P := pitch_len()
	if latch["state"] == "locked":
		if not latch_wanted:
			unlock()
		return
	if not latch_wanted or float(e[0]) > P * 0.25 or float(e[1]) > 25.0:
		latch["state"] = "open"
		if ri >= 0:
			servos[ri]["target"] = 0.0
		return
	latch["state"] = "grip"
	# the cone centres itself: a spring between pin and sleeve
	var front: RigidBody3D = bodies[seg_body[0]]["rb"]
	var rear: RigidBody3D = bodies[seg_body[n() - 1]]["rb"]
	var d: Vector3 = (e[3] as Vector3) - (e[2] as Vector3)
	var k := 40.0 * total_mass
	var f := d * k - (front.linear_velocity - rear.linear_velocity) * 2.0 * sqrt(k * front.mass)
	f = f.limit_length(9.81 * total_mass * 0.5)
	front.apply_force(f, (e[2] as Vector3) - front.global_position)
	rear.apply_force(-f, (e[3] as Vector3) - rear.global_position)
	if float(e[0]) < 0.004 and float(e[1]) < 6.0:
		var j := Generic6DOFJoint3D.new()           # all axes locked (default): the latch is rigid
		j.name = "riegel_lock"
		j.transform = Transform3D(Basis(), e[3])
		add_child(j)
		j.node_a = rear.get_path()
		j.node_b = front.get_path()
		latch["joint"] = j
		latch["state"] = "locked"
		if ri >= 0:
			servos[ri]["target"] = 1.0
		_paint_bolt(true)


func unlock() -> void:
	var j = latch.get("joint")
	if j != null and is_instance_valid(j):
		(j as Node).queue_free()
	latch["joint"] = null
	latch["state"] = "open"
	var ri := servo_index("riegel")
	if ri >= 0:
		servos[ri]["target"] = 0.0
	_paint_bolt(false)


func _paint_bolt(closed: bool) -> void:
	if seg_body.size() < n():
		return
	var rb: RigidBody3D = bodies[seg_body[n() - 1]]["rb"]
	var bolt := rb.get_node_or_null("riegel") as MeshInstance3D
	if bolt != null:
		(bolt.get_meta("mat") as StandardMaterial3D).albedo_color = FARBE["locked"] if closed else FARBE["kupplung"]


# ---- Zahlen für Anzeigen und Tests ---------------------------------------------------------------------------------------
func com() -> Vector3:
	var s := Vector3.ZERO
	var m := 0.0
	for b in bodies:
		var rb: RigidBody3D = b["rb"]
		s += (rb.global_transform * rb.center_of_mass) * rb.mass
		m += rb.mass
	return s / maxf(m, 1e-6)


func max_speed() -> float:
	var v := 0.0
	for b in bodies:
		v = maxf(v, (b["rb"] as RigidBody3D).linear_velocity.length())
	return v


func segment_xf(i: int) -> Transform3D:
	return frame_of(seg_body[clampi(i, 0, n() - 1)])


func foot_world(i: int, s: int) -> Vector3:
	for bi in range(bodies.size()):
		var b: Dictionary = bodies[bi]
		if b["kind"] == "unter" and b["seg"] == i and b["side"] == s:
			return frame_of(bi) * Vector3(0, 0, s * u("unterschenkel"))
	return Vector3.ZERO


func feet_on_ground() -> Array:
	"""world points of the feet that touch something right now"""
	var out := []
	for bi in range(bodies.size()):
		var b: Dictionary = bodies[bi]
		if b["kind"] != "unter":
			continue
		var st := PhysicsServer3D.body_get_direct_state((b["rb"] as RigidBody3D).get_rid())
		if st != null and st.get_contact_count() > 0:
			out.append(foot_world(b["seg"], b["side"]))
	return out


func overloaded() -> Array:
	var out := []
	for sv in servos:
		if float(sv["load"]) > 1.0:
			out.append(sv["id"])
	return out


func contact_points(kinds := []) -> Array:
	"""world points where the robot touches the ground right now (feet, belly, legs; or only these body kinds)"""
	var out := []
	for b in bodies:
		if not kinds.is_empty() and not kinds.has(b["kind"]):
			continue
		var st := PhysicsServer3D.body_get_direct_state((b["rb"] as RigidBody3D).get_rid())
		if st == null:
			continue
		for ci in range(st.get_contact_count()):
			out.append(st.get_contact_local_position(ci))
	return out
