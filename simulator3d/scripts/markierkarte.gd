extends Node3D
## «📍 Markier-Karte» (Vorschau, MoveEye mw-markier-karte): eine gedruckte Karte mit einem grossen ArUco-Marker und einem
## kleinen QR-Code, die eine Person trägt oder die irgendwo steht. MoveEye folgt dem Marker mit dem Kopf; dreht der Besitzer
## die Karte kurz weg und zeigt sie wieder, speichert MoveEye die Kopfstellung als Teach-in-Punkt.
## Steuerung (/control, main_steuerung.gd): {"action": "markierkarte", "do": …}
##   on    {bits: [[0/1 × n] × n] (Marker mit schwarzem Rand, Zeilen von oben, 1 = weiss), qr: "Text", size: "A4" | "A5",
##          carry: true (die zuletzt erschienene Person, oder spawn: {from: [x, z], to: [x, z], wait: s}) | pos: [x, y, z],
##          yaw: Grad (schräg halten), height: m}
##   hide  {secs: 1.5} - die Karte kurz wegdrehen (Rückseite weiss), danach von selbst wieder zeigen
##   walk  {to: [x, z], wait: s} - der Träger geht weiter
##   moveto {to: [x, z], speed: m/s} - ohne Person: die Karte selbst wandert (auf Brusthöhe über dem Boden), für Tests
##   step  {pan, tilt} - für Tests: den Kopf dorthin stellen (wie der Zustand von MoveEye) und info zurück
##   tempo {value} - für Tests auf langsamen Rechnern: Engine.time_scale (0.02 … 1); die Uhr der Karte läuft mit
##   info  - wo die Karte ist, Abstand und Winkel zum Kopf, «clock» = Simulator-Zeit der Karte (s)
##   off   - weg
## Nur ein Test- und Vorführ-Ding: keine Einstellung, nichts gespeichert.

const SIZES := {"A4": [0.210, 0.297, 0.180], "A5": [0.148, 0.210, 0.128]}   # Blatt b × h, Marker-Seite (m)
const PX_PER_M := 2000.0                              # Textur: 2 px pro mm

var main
var carrier: Node3D = null
var fixed_pos := Vector3.ZERO
var yaw_deg := 0.0
var height := 1.25
var hide_until := 0.0
var turn := 0.0                                       # 0 = Vorderseite zum Kopf, 1 = weggedreht
var front: MeshInstance3D
var back: MeshInstance3D
var size_name := "A4"
var hides := 0
var goal := Vector3.INF                              # moveto: wohin die Karte ohne Träger wandert
var goal_v := 1.0
var clock := 0.0                                      # s Simulator-Zeit (mit Engine.time_scale), für «hide» und Tests


static func control(m, d: Dictionary) -> Dictionary:
	var k = m.get_meta("markierkarte") if m.has_meta("markierkarte") else null
	var what := str(d.get("do", "info"))
	if what == "tempo":
		Engine.time_scale = clampf(float(d.get("value", 1.0)), 0.02, 1.0)
		return {"ok": true, "tempo": Engine.time_scale}
	if what == "off":
		if k != null and is_instance_valid(k):
			k.queue_free()
		if m.has_meta("markierkarte"):
			m.remove_meta("markierkarte")
		return {"ok": true}
	if what == "on":
		if k != null and is_instance_valid(k):
			k.queue_free()
		k = load("res://scripts/markierkarte.gd").new()
		k.main = m
		m.add_child(k)
		m.set_meta("markierkarte", k)
		var err: String = k.setup(d)
		if err != "":
			return {"ok": false, "error": err}
		return k.info()
	if k == null or not is_instance_valid(k):
		return {"ok": false, "error": "no card"}
	if what == "hide":
		k.hide_until = k.clock + clampf(float(d.get("secs", 1.5)), 0.2, 10.0)
		k.hides += 1
	elif what == "walk":
		if k.carrier == null or not is_instance_valid(k.carrier):
			return {"ok": false, "error": "nobody carries the card"}
		var t: Array = d.get("to", [0, 10])
		var tv := Vector3(float(t[0]), 0, float(t[1]))
		k.carrier.target = tv
		k.carrier.route = [[tv, float(d.get("wait", 999.0)), 0.0, Vector3.ZERO], tv + Vector3(40.0, 0, 0)]
		k.carrier.next_idle = m.now() + 999.0
	elif what == "moveto":
		var t2: Array = d.get("to", [0, 10])
		k.carrier = null
		k.goal = Vector3(float(t2[0]), 0.0, float(t2[1]))
		k.goal_v = clampf(float(d.get("speed", 1.0)), 0.1, 3.0)
	elif what == "step":
		var sv: Dictionary = m.mw.get("servo", {})
		sv["pan_deg"] = float(d.get("pan", 0.0))
		sv["tilt_deg"] = float(d.get("tilt", 0.0))
		sv.erase("pan_dps")
		sv.erase("tilt_dps")
		m.mw["servo"] = sv
		m.mw_t = m.now()
	elif what == "yaw":
		k.yaw_deg = float(d.get("value", 0.0))
	return k.info()


func setup(d: Dictionary) -> String:
	size_name = str(d.get("size", "A4")).to_upper()
	if not SIZES.has(size_name):
		size_name = "A4"
	var bits = d.get("bits", [])
	if typeof(bits) != TYPE_ARRAY or bits.size() < 4 or bits.size() > 12:
		return "bits: n × n (4 … 12)"
	yaw_deg = float(d.get("yaw", 0.0))
	height = clampf(float(d.get("height", 1.25)), 0.2, 2.2)
	var sz: Array = SIZES[size_name]
	var img := _texture(bits, str(d.get("qr", "")), sz)
	var tex := ImageTexture.create_from_image(img)
	front = _quad(Vector2(sz[0], sz[1]), tex, Color(1, 1, 1))
	back = _quad(Vector2(sz[0], sz[1]), null, Color(0.93, 0.93, 0.9))
	back.rotation.y = PI                                  # Rückseite: weiss, schaut nach hinten
	back.position.z = -0.001
	if d.has("pos"):
		var p: Array = d["pos"]
		fixed_pos = Vector3(float(p[0]), float(p[1]), float(p[2]))
	elif d.has("spawn"):
		var s: Dictionary = d["spawn"]
		var f: Array = s.get("from", [0, 3])
		var t: Array = s.get("to", [0, 15])
		var tv := Vector3(float(t[0]), 0, float(t[1]))
		carrier = main.spawn("person", Vector3(float(f[0]), 0, float(f[1])), tv)
		if carrier != null:
			carrier.route = [[tv, float(s.get("wait", 999.0)), 0.0, Vector3.ZERO], tv + Vector3(40.0, 0, 0)]
			carrier.next_idle = main.now() + 999.0
			if s.has("speed") and carrier.get("speed") != null:
				carrier.speed = float(s["speed"])
	elif bool(d.get("carry", false)) and main.visitors != null and main.visitors.get_child_count() > 0:
		carrier = main.visitors.get_child(main.visitors.get_child_count() - 1)
	_place(0.0)
	return ""


func _texture(bits: Array, qr: String, sz: Array) -> Image:
	"""das Blatt als Bild: weiss, oben der Marker (Zellen aus bits), darunter der kleine QR-Code und eine graue Zeile"""
	var w := int(sz[0] * PX_PER_M)
	var h := int(sz[1] * PX_PER_M)
	var img := Image.create(w, h, false, Image.FORMAT_RGB8)
	img.fill(Color(0.96, 0.96, 0.94))                     # Papier, nicht ganz weiss
	var n := bits.size()
	var ms := int(sz[2] * PX_PER_M)
	var x0 := (w - ms) / 2
	var cell := float(ms) / n
	var ink := Color(0.07, 0.07, 0.08)
	for r in n:
		var row: Array = bits[r]
		for c in n:
			if int(row[c]) == 0:
				img.fill_rect(Rect2i(x0 + int(c * cell), x0 + int(r * cell), int(ceil(cell)), int(ceil(cell))), ink)
	if qr != "":
		var mtx: Array = preload("res://scripts/qr.gd").matrix(qr)
		if not mtx.is_empty():
			var qs := int(0.035 * PX_PER_M)               # QR 35 mm, links unter dem Marker
			var qn := mtx.size()
			var qc := float(qs) / qn
			var qy := x0 + ms + int(0.008 * PX_PER_M)
			for r in qn:
				for c in qn:
					if mtx[r][c]:
						img.fill_rect(Rect2i(x0 + int(c * qc), qy + int(r * qc), int(ceil(qc)), int(ceil(qc))), ink)
			img.fill_rect(Rect2i(x0 + qs + int(0.01 * PX_PER_M), qy + qs / 3, ms - qs - int(0.01 * PX_PER_M), qs / 6), Color(0.55, 0.55, 0.55))
	img.generate_mipmaps()                                # weit weg wird die Karte weich (wie in echt), nicht flimmernd
	return img


func _quad(s: Vector2, tex: Texture2D, col: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = s
	mi.mesh = q
	var mt := StandardMaterial3D.new()
	mt.albedo_color = col
	if tex != null:
		mt.albedo_texture = tex
		mt.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	mt.roughness = 0.92                                   # mattes Papier
	mt.cull_mode = BaseMaterial3D.CULL_BACK
	mi.material_override = mt
	mi.layers = 1 | 2                                     # Kopf- und Weitwinkel-Kamera sehen sie
	add_child(mi)
	return mi


func _head_pos() -> Vector3:
	return main.head.global_position if main.head != null else Vector3(0, 1.2, 0)


func _process(dt: float) -> void:
	clock += dt
	_place(dt)


func _place(dt: float) -> void:
	var want := 1.0 if clock < hide_until else 0.0
	turn = move_toward(turn, want, dt / 0.35) if dt > 0.0 else want    # in etwa 0,35 s weg- / hergedreht
	var hp := _head_pos()
	if goal != Vector3.INF and dt > 0.0:
		var flat := Vector3(fixed_pos.x, 0.0, fixed_pos.z)
		flat = flat.move_toward(goal, goal_v * dt)
		var gy: float = main.ground_y(flat.x, flat.z) if main.has_method("ground_y") else 0.0
		fixed_pos = Vector3(flat.x, gy + height, flat.z)
	var p := fixed_pos
	if carrier != null and is_instance_valid(carrier):
		var base: Vector3 = carrier.global_position
		var to_head := hp - base
		to_head.y = 0.0
		p = base + Vector3(0, height, 0) + to_head.normalized() * 0.32    # vor dem Körper, zum Kopf hin
	global_position = p
	var away := p + (p - hp)                                # -Z schaut weg vom Kopf -> die Vorderseite (+Z) zum Kopf
	if (away - p).length() > 0.01:
		look_at(away, Vector3.UP)
	rotate_object_local(Vector3.UP, deg_to_rad(yaw_deg) + PI * turn)


func info() -> Dictionary:
	var hp := _head_pos()
	var dist := global_position.distance_to(hp)
	var az := rad_to_deg(atan2(global_position.x - hp.x, -(global_position.z - hp.z)))
	var el := rad_to_deg(atan2(global_position.y - hp.y, Vector2(global_position.x - hp.x, global_position.z - hp.z).length()))
	return {"ok": true, "size": size_name, "pos": [global_position.x, global_position.y, global_position.z], "dist": dist,
			"az": az, "el": el, "rig_yaw": rad_to_deg(main.rig.rotation.y) if main.rig != null else 0.0,
			"head_yaw": rad_to_deg(main.head.rotation.y) if main.head != null else 0.0,
			"head_pitch": rad_to_deg(main.head_pitch.rotation.x) if main.head_pitch != null else 0.0,
			"hidden": turn > 0.5, "hides": hides, "carried": carrier != null and is_instance_valid(carrier),
			"head": [hp.x, hp.y, hp.z], "clock": clock, "tempo": Engine.time_scale}
