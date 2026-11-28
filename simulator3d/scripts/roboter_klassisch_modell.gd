extends "res://scripts/roboter_modell.gd"
## Roboter-Labor, klassische Laufroboter (Besitzer 28.11.2026, Fragebogen 14:40): «Vierbeiner» (ein Körper, 4 Beine, wie
## ein Hund) und «Sechsbeiner» (ein Körper, 6 Beine, wie ein Käfer). Gleiche Physik wie der Segment-Roboter
## (roboter_modell.gd: RigidBody3D je Teil, HingeJoint3D mit Geschwindigkeits-Motor je Servo-Achse, Servo-Last,
## Strom, Kollision rot) - nur der Aufbau ist anders: EIN Körper (Quader), die Beinpaare sitzen gleichmässig verteilt an
## seinen Seiten, vorne die schwenkbare Kamera auf kurzem Mast. Kein Ring, keine Kupplung, keine Segmentgelenke.
## Bein, Servo-Grössen, Massen und Servo-Momente wie beim Segment-Roboter (Startwerte aus dessen START).
##
## Schnittstelle gleich wie beim Segment-Roboter (Steuerung, Gang-KI, Anzeige), siehe gang_ki_schnittstelle.md
## «Klassische Modelle»:
##   · n() = Zahl der Beinpaare (2 / 3), Beinpaar 0 = vorne. Servo-Kennungen hy0l / hp0l / kn0l … wie dort (i = Beinpaar).
##   · segment_xf(i) = Rahmen des Beinpaars i: der Körper-Rahmen, nach vorne zur Hüftlinie des Paars verschoben. Damit
##     rechnet roboter_bewegung.leg_ik(s, fuss) (Fuss im Rahmen des Paars) unverändert; foot_world / foot_contact gleich.
##   · seg_body = [0, 0 …] (alle Paare hängen am selben Körper), pitch_len() = Abstand der Beinpaare.

const START_K := {
	"beine": 4,
	"koerper_laenge": 3.2,          # Einheiten (Massstab wie beim Segment-Roboter: 0.10 m pro Einheit)
	"halbe_breite": 0.45,           # wie Segment-Roboter (Hüfte seitlich am Körper, Bein-Dicke)
	"halbe_hoehe": 0.30,
	"oberschenkel": 1.19, "unterschenkel": 1.05, "mast_hoehe": 0.30, "massstab": 0.10,
	"masse_koerper": 0.60,          # kg (Segment-Roboter: 0.30 kg je Beinpaar)
	"masse_bein": 0.15, "moment_bein": 1.5, "moment_koerper": 3.5, "tempo_servo": 300.0, "reibung": 0.9,
	"strom_stall": 2.5, "strom_ruhe": 0.01,
}
const START_6 := {"beine": 6, "koerper_laenge": 4.0, "masse_koerper": 0.90}
const GRENZEN_K := {
	"beine": [4, 6], "koerper_laenge": [1.5, 8.0], "halbe_breite": [0.2, 1.2], "halbe_hoehe": [0.1, 0.8],
	"oberschenkel": [0.4, 2.0], "unterschenkel": [0.3, 2.0], "mast_hoehe": [0.1, 0.8], "massstab": [0.05, 0.40],
	"masse_koerper": [0.05, 4.0], "masse_bein": [0.02, 1.0], "moment_bein": [0.1, 8.0], "moment_koerper": [0.2, 15.0],
	"tempo_servo": [30.0, 720.0], "reibung": [0.05, 1.5],
}
# Regler im Labor: [key, Name, Einheit, Schritt] (Namen gehen durch T.t)
const FORM_K := [["koerper_laenge", "Körperlänge", "E", 0.05], ["halbe_breite", "Halbe Breite", "E", 0.01],
	["halbe_hoehe", "Halbe Höhe des Körpers", "E", 0.01], ["oberschenkel", "Oberschenkel", "E", 0.01],
	["unterschenkel", "Unterschenkel", "E", 0.01], ["mast_hoehe", "Mast der Kamera", "E", 0.01],
	["massstab", "Massstab (Meter pro Einheit)", "m", 0.005], ["masse_koerper", "Masse des Körpers", "kg", 0.01],
	["masse_bein", "Masse je Bein", "kg", 0.01]]
const PHYSIK_K := [["moment_bein", "Servo-Moment Bein", "N·m", 0.05], ["tempo_servo", "Servo-Tempo", "°/s", 10.0],
	["reibung", "Reibung am Boden", "", 0.05]]
const BEIN_SPANNE := 0.85          # Anteil der Körperlänge zwischen dem vordersten und dem hintersten Beinpaar

var klassisch := true


func _init() -> void:
	p = START_K.duplicate()
	bp = p.duplicate()


static func start_werte(beine: int) -> Dictionary:
	var d := START_K.duplicate()
	if beine == 6:
		d.merge(START_6, true)
	return d


func setze_beine(beine: int) -> void:
	"""the start values of the four- or six-legged robot (the lab puts the saved values on top)"""
	p = start_werte(6 if beine == 6 else 4)
	bp = p.duplicate()


func grenzen() -> Dictionary:
	return GRENZEN_K


# ---- Masse ---------------------------------------------------------------------------------------------------------------
func n() -> int:
	return 3 if int(bp["beine"]) == 6 else 2


func leg_x(i: int) -> float:
	"""where the hips of leg pair i sit along the body (m, + = forward); pair 0 in front"""
	var span := u("koerper_laenge") * BEIN_SPANNE
	return span * 0.5 - span * float(i) / float(maxi(1, n() - 1))


func pitch_len() -> float:
	return u("koerper_laenge") * BEIN_SPANNE / float(maxi(1, n() - 1))


func run_len() -> float:
	return 0.0


func actuator_count() -> int:          # 3 je Bein + Kamera
	return 6 * n() + 1


func set_param(k: String, v) -> void:
	if not p.has(k):
		return
	var g = GRENZEN_K.get(k, null)
	var val = float(v)
	if g != null:
		val = clampf(val, float(g[0]), float(g[1]))
	p[k] = (6 if int(round(val)) >= 5 else 4) if k == "beine" else val


# ---- Aufbau --------------------------------------------------------------------------------------------------------------
func build(at: Transform3D, angles := {}) -> void:
	clear()
	bp = p.duplicate()
	root_xf = at
	_mat_red = StandardMaterial3D.new()
	_mat_red.albedo_color = FARBE["rot"]
	_mat_red.emission_enabled = true
	_mat_red.emission = Color(0.6, 0.0, 0.0)
	var N := n()
	var w := u("halbe_breite")
	var mb := float(bp["masse_bein"])
	var lf := u("oberschenkel")
	var lt := u("unterschenkel")
	var kb := _torso(float(bp["masse_koerper"]))
	for i in range(N):
		seg_body.append(kb)
	for i in range(N):
		for s in [-1, 1]:
			var hb := _body("huefte", i, s, mb * 0.4)
			_servo("hy", i, s, kb, hb, Vector3.UP, s, Vector3(leg_x(i), 0, s * w), Vector3.ZERO, -90, 90, "moment_bein")
			var fb := _body("ober", i, s, mb * 0.4, Transform3D(Basis(), Vector3(0, 0, s * lf * 0.5)))
			_servo("hp", i, s, hb, fb, Vector3.RIGHT, -s, Vector3.ZERO, Vector3.ZERO, -90, 90, "moment_bein")
			var tb := _body("unter", i, s, mb * 0.2, Transform3D(Basis(), Vector3(0, 0, s * lt * 0.5)))
			_servo("kn", i, s, fb, tb, Vector3.RIGHT, s, Vector3(0, 0, s * lf), Vector3.ZERO, -180, 180, "moment_bein")
	pan_servo = _servo("pan", 0, 0, -1, -1, Vector3.UP, 1, Vector3.ZERO, Vector3.ZERO, -170, 170, "moment_bein")
	total_mass = 0.0
	for b in bodies:
		total_mass += (b["rb"] as RigidBody3D).mass
	var zero := fk({})
	for bi in range(bodies.size()):
		(bodies[bi]["rb"] as RigidBody3D).global_transform = zero[bi] * bodies[bi]["off"]
	for si in fk_order:
		_make_joint(si, zero)
	_make_excl()
	for k in angles:
		set_target(str(k), float(angles[k]))
	place(true)
	built_ok = true


func _torso(mass: float) -> int:
	"""the one body: a box (length × 2 half width × 2 half height), the camera on a short mast in front"""
	var rb := RigidBody3D.new()
	rb.mass = maxf(0.005, mass)
	rb.collision_layer = LAYER_ROBOTER
	rb.collision_mask = LAYER_GELAENDE
	rb.contact_monitor = true
	rb.max_contacts_reported = 8
	rb.can_sleep = false
	rb.angular_damp = 0.5
	var pm := PhysicsMaterial.new()
	pm.friction = float(p["reibung"])
	rb.physics_material_override = pm
	rb.name = "koerper_0_1"
	add_child(rb)
	var L := u("koerper_laenge")
	var w := u("halbe_breite")
	var h := u("halbe_hoehe")
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = Vector3(L, 2 * h, 2 * w)
	cs.shape = sh
	rb.add_child(cs)
	var col: Color = FARBE["koerper"]
	var mis := []
	var bm := BoxMesh.new()
	bm.size = sh.size
	mis.append(_mesh(rb, bm, Transform3D(), col))
	# a darker stripe on the back = where the electronics sit (only looks)
	var sm := BoxMesh.new()
	sm.size = Vector3(L * 0.6, 0.004, w * 1.2)
	_mesh(rb, sm, Transform3D(Basis(), Vector3(0, h + 0.002, 0)), FARBE["gelenk"])
	rb.inertia = Vector3(mass * (4 * h * h + 4 * w * w) / 12.0, mass * (L * L + 4 * w * w) / 12.0,
			mass * (L * L + 4 * h * h) / 12.0) + Vector3.ONE * float(ARMATUR["seg"])
	bodies.append({"rb": rb, "kind": "seg", "seg": 0, "side": 0, "off": Transform3D(), "mis": mis, "col": col, "cs": cs})
	_kopf(rb, L, w, h)
	return bodies.size() - 1


func _kopf(rb: RigidBody3D, L: float, w: float, h: float) -> void:
	"""mast + pan head with the camera near the front end (looks forward, +X)"""
	var mh := u("mast_hoehe")
	var mx := L * 0.5 - w * 0.4
	var mast := CylinderMesh.new()
	mast.top_radius = w * 0.12
	mast.bottom_radius = w * 0.12
	mast.height = mh
	_mesh(rb, mast, Transform3D(Basis(), Vector3(mx, h + mh * 0.5, 0)), FARBE["kamera"])
	cam_head = Node3D.new()
	cam_head.name = "kamerakopf"
	cam_head.position = Vector3(mx, h + mh, 0)
	rb.add_child(cam_head)
	var hb := BoxMesh.new()
	hb.size = Vector3(w * 0.66, w * 0.44, w * 0.5)
	_mesh(cam_head, hb, Transform3D(Basis(), Vector3(0, w * 0.28, 0)), FARBE["kamera"])
	var lens := CylinderMesh.new()
	lens.top_radius = w * 0.13
	lens.bottom_radius = w * 0.13
	lens.height = w * 0.18
	_mesh(cam_head, lens, Transform3D(Basis(Vector3.BACK, PI * 0.5), Vector3(w * 0.4, w * 0.28, 0)), FARBE["linse"])
	robot_cam = Node3D.new()
	robot_cam.name = "roboterkamera"
	robot_cam.position = Vector3(w * 0.5, w * 0.28, 0)
	robot_cam.rotation = Vector3(0, -PI * 0.5, 0)
	cam_head.add_child(robot_cam)


func _low_points(bi: int) -> Array:
	var b: Dictionary = bodies[bi]
	if b["kind"] == "seg":
		var L := u("koerper_laenge") * 0.5
		var w := u("halbe_breite")
		var h := u("halbe_hoehe")
		var out := []
		for x in [-L, L]:
			for y in [-h, h]:
				for z in [-w, w]:
					out.append(Vector3(x, y, z))
		return out
	return super._low_points(bi)


# ---- kein Ring, keine Kupplung -------------------------------------------------------------------------------------------
func coupling_error() -> Array:
	return [99.0, 180.0, Vector3.ZERO, Vector3.ZERO]


func _latch_step(_dt: float) -> void:
	latch["state"] = "open"


# ---- Rahmen der Beinpaare --------------------------------------------------------------------------------------------------
func body_xf() -> Transform3D:
	return frame_of(seg_body[0])


func segment_xf(i: int) -> Transform3D:
	"""frame of leg pair i: the body frame moved forward to the hip line of that pair (leg_ik works in it)"""
	return frame_of(seg_body[0]) * Transform3D(Basis(), Vector3(leg_x(clampi(i, 0, n() - 1)), 0, 0))

