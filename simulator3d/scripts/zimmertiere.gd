extends Node
## Paket «Erlebniswelt: mehr Tiere drinnen» (Daniel 31.10.2026): Tiere im Innenraum - in der Szene «Schlafzimmer» (der
## einzige Raum, in dem MoveEye drinnen steht; die Erlebniswelt erlebniswelt.gd ist draussen im Ferienpark). Drei
## glaubwürdige Fehlalarm-Fälle für MoveEye in der Wohnung, gebaut wie die Vignetten der Erlebniswelt (kleine
## Zustandsmaschinen, Grundformen mit Wärme-Zwilling):
##   Hamster  Goldhamster im Glas-Nagerheim auf der Kommode (vorne rechts der Tür): tagsüber schläft er im Häuschen, nachts
##            (ca. 20:30–05:30) rennt er immer wieder im Laufrad - kleine, ständige Bewegung (Rad mit Streifen), dazwischen
##            fressen, trinken, herumlaufen. Wärmebild: durch die Glasscheiben sieht es ihn nicht (Glas ist für 8–14 µm
##            undurchsichtig, waerme.gd window_glass_e) - nur durch das offene Gitter oben.
##   Vogel    Wellensittich im Käfig auf dem Ständer (vorne links): am Tag hüpfen, flattern, kurz fliegen, putzen, ans
##            Glöckchen picken; nachts schläft er aufgeplustert auf der obersten Stange, Kopf nach hinten (ruhig).
##   Spinne   Hauswinkelspinne (Eratigena atrica): krabbelt langsam an der Wand und an der Decke (nachts mehr), mit kurzen
##            Sprints; manchmal seilt sie sich vor der Kopfkamera ab, hängt einige Zentimeter vor der Linse, dreht und
##            pendelt am Faden und krabbelt über das Gehäuse vor der Linse. So nah ist sie stark unscharf (Zerstreuungskreis
##            des Objektivs, lens.gdshader «spider»), nachts im Infrarot von MoveEye weiss überstrahlt - ein echter, häufiger
##            Fehlalarm. Wärmebild: Raumtemperatur (unsichtbar), PIR: nichts (kein Wärmeunterschied).
## Wärme: waerme.gd (Waerme.animal «hamster» / «budgie» / «spider», Waerme.T("room_air")).
## Tageszeiten: main.hour() / main.is_dark(). Nichts davon während Testlauf / Prüfstand / Messung (wie erlebniswelt.gd).
## Steuerung: Gruppe «Wildbeobachtung» (heisst im Bedienfeld «Wildtier»): zt_pets, zt_spider, zt_spider_lens.
## Steuerbefehl: /control {"action": "zimmertiere", "do": "info" | "lens" (dist m, hold) | "set" (pets, spider) |
##   "state" (who: hamster | vogel | spinne, state, hold)}
## Lite: _lite() = Quality.lite() (central switch, quality.gd) - weniger Gitterstäbe, einfachere Beine, keine Schatten.

const T = preload("res://scripts/i18n.gd")
const Waerme = preload("res://scripts/waerme.gd")
const Quality = preload("res://scripts/quality.gd")
const SAVE := "user://zimmertiere.json"

# ---- optics of the cameras of MoveEye (for the spider right in front of the lens) ----------------------------------------
# [focal length mm, f-number] - Raspberry Pi Camera Module 3: 4.74 mm, f/1.8, 66° horizontal, focus 10 cm … ∞;
# Camera Module 3 Wide: 2.75 mm, f/2.2, 102° horizontal, focus 5 cm … ∞ (Raspberry Pi product brief / datasheet).
# Sensor Sony IMX708: 4608 px × 1.4 µm = 6.45 mm wide.
const OPTIK := [[4.74, 1.8], [2.75, 2.2]]
const SENSOR_W_MM := 6.45
const FOCUS_M := 2.0           # assumption: focused on the room (MoveEye sets no autofocus - quelle/ has no AfMode)
const NEAR_M := 0.30           # nearer than this to a camera: the spider is drawn by the lens shader (blurred), not in 3D
# (at 0.3 m the circle of confusion is ~5 px of 960 - the switch from the sharp 3D spider is hardly visible)

# ---- the bedroom (scenes.gd _schlafzimmer: x -3 … 3.5, z -5 … 1.5, 2.6 m high; MoveEye at the origin) -------------------
const FZ := -4.94              # inner face of the front wall (door at x -2 … -1)
const LX := -2.94              # inner face of the left wall (window at z -3 … -1.5)
const CY := 2.565              # under the ceiling

var main
var pets_on := true
var spider_on := true
var lite := false
var room: Node3D = null        # under the scene root (freed with the scene)
var hamster: Hamster = null
var vogel: Vogel = null
var spinne: Spinne = null
var _quiet := false
var _tick := 0.0
var _lens_set := [false, false] # the lens shader of camera i has the spider now
var stats := {"us": 0.0}


static func _lite() -> bool:
	"""Lite graphics (Raspberry Pi): quality.gd (one central switch, set by main.lite_update)"""
	return Quality.lite()


func _ready() -> void:
	name = "zimmertiere"
	_load()


func _load() -> void:
	if not FileAccess.file_exists(SAVE):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(SAVE))
	if typeof(d) == TYPE_DICTIONARY:
		pets_on = bool(d.get("pets", true))
		spider_on = bool(d.get("spider", true))


func save() -> void:
	var f := FileAccess.open(SAVE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"pets": pets_on, "spider": spider_on}))


func add_controls() -> void:
	main.add_control("toggle", "zt_pets", "Haustiere im Schlafzimmer: Hamster (nachts im Laufrad) und Wellensittich (am Tag)",
			func(): return pets_on, func(v): set_on(bool(v), spider_on), "Wildbeobachtung")
	main.add_control("toggle", "zt_spider", "Spinne im Schlafzimmer (krabbelt an Wand und Decke, seilt sich manchmal vor der Linse ab)",
			func(): return spider_on, func(v): set_on(pets_on, bool(v)), "Wildbeobachtung")
	main.add_control("button", "zt_spider_lens", "Spinne vor die Linse – jetzt (Fehlalarm-Test, Szene Schlafzimmer)", null,
			func(): lens_now(), "Wildbeobachtung")


func set_on(pets: bool, spider: bool) -> void:
	pets_on = pets
	spider_on = spider
	save()
	_update_shown(true)


# ---- building: main._build_scene -> on_scene() ------------------------------------------------------------------------------
func on_scene() -> void:
	"""after scenes.build: the animals into the bedroom (other scenes: nothing)"""
	hamster = null
	vogel = null
	spinne = null
	room = null
	_lens_off()
	if main.scene != "schlafzimmer" or main.scenes == null or main.scenes.root == null:
		return
	lite = _lite() or str(main.quality) == "simple"
	room = Node3D.new()
	room.name = "zimmertiere"
	main.scenes.root.add_child(room)
	hamster = Hamster.new(self)
	vogel = Vogel.new(self)
	spinne = Spinne.new(self)
	for a in [hamster, vogel, spinne]:
		a.build()
	_register()
	_update_shown(true)


func room_t() -> float:
	return Waerme.T("room_air")


func valid() -> bool:
	return room != null and is_instance_valid(room) and room.is_inside_tree()


# ---- small helpers (like erlebniswelt.gd) -----------------------------------------------------------------------------------
func node(parent: Node3D, p: Vector3, ry := 0.0) -> Node3D:
	var n := Node3D.new()
	n.position = p
	n.rotation.y = ry
	parent.add_child(n)
	return n


func part(parent: Node3D, mesh: Mesh, p: Vector3, col: Color, tk, rot := Vector3.ZERO, scl := Vector3.ONE) -> MeshInstance3D:
	"""a visible part + its twin for the thermal camera (tk: °C or a surface key)"""
	var mi: MeshInstance3D = main.add_mesh(parent, mesh, p, main.mat(col), tk, rot, scl)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if lite else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	return mi


func glass(parent: Node3D, size: Vector3, p: Vector3) -> void:
	"""a pane of glass: see-through for the cameras, opaque for the thermal camera (room temperature, waerme.gd window_glass_e)"""
	var gm := StandardMaterial3D.new()
	gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	gm.albedo_color = Color(0.85, 0.92, 0.95, 0.12)
	gm.roughness = 0.05
	gm.metallic_specular = 0.9
	var mi: MeshInstance3D = main.add_mesh(parent, boxm(size.x, size.y, size.z), p, gm, room_t())
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func bars(parent: Node3D, xs: Array, col: Color, r: float) -> MultiMeshInstance3D:
	"""thin wire bars [[from, to], …] as ONE draw call (no thermal twin: 2-3 mm wire at room temperature is not seen)"""
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var cm := CylinderMesh.new()
	cm.top_radius = r
	cm.bottom_radius = r
	cm.height = 1.0
	cm.radial_segments = 4
	cm.rings = 1
	mm.mesh = cm
	mm.instance_count = xs.size()
	for i in range(xs.size()):
		var a: Vector3 = xs[i][0]
		var b: Vector3 = xs[i][1]
		var d := b - a
		var bs := Basis(Quaternion(Vector3.UP, d.normalized())) if d.length() > 0.0001 else Basis()
		mm.set_instance_transform(i, Transform3D(bs * Basis.from_scale(Vector3(1, d.length(), 1)), (a + b) * 0.5))
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	mi.material_override = main.mat(col)
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


func stick(parent: Node3D, a: Vector3, b: Vector3, r: float, col: Color, tk) -> MeshInstance3D:
	"""a thin cylinder from a to b (legs)"""
	var d := b - a
	var bs := Basis(Quaternion(Vector3.UP, d.normalized())) if d.length() > 0.00001 else Basis()
	var mi := part(parent, cylm(r, r * 0.8, d.length(), 4), (a + b) * 0.5, col, tk, bs.get_euler())
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi


func boxm(x: float, y: float, z: float) -> BoxMesh:
	var b := BoxMesh.new()
	b.size = Vector3(x, y, z)
	return b


func sphm(r: float, h := -1.0, seg := 10) -> SphereMesh:
	var sm := SphereMesh.new()
	sm.radius = r
	sm.height = h if h > 0.0 else r * 2.0
	sm.radial_segments = seg if not lite else maxi(6, seg / 2)
	sm.rings = maxi(3, seg / 2)
	return sm


func cylm(rt: float, rb: float, h: float, seg := 10) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = rt
	c.bottom_radius = rb
	c.height = h
	c.radial_segments = seg if not lite else maxi(4, seg / 2)
	c.rings = 1
	return c


func hour() -> float:
	return float(main.hour())


func dark() -> bool:
	return bool(main.is_dark())


func ent():
	var e = main.get("entdecken")
	return e if e != null and e.has_method("register") else null


# ---- running ------------------------------------------------------------------------------------------------------------
func _is_quiet() -> bool:
	var e = ent()
	if e != null and e.has_method("_quiet"):
		return bool(e._quiet())
	return bool(main.measuring())


func _update_shown(force := false) -> void:
	if not valid():
		return
	var q := _is_quiet()
	if q != _quiet or force:
		_quiet = q
	hamster.set_shown(pets_on and not q)
	vogel.set_shown(pets_on and not q)
	spinne.set_shown(spider_on and not q)
	if not spinne.shown:
		_lens_off()


func _process(dt: float) -> void:
	if main == null or not valid():
		return
	dt = minf(dt, 0.25)
	_tick -= dt
	if _tick <= 0.0:
		_tick = 0.6 if lite else 0.3
		_update_shown()
	var t0 := Time.get_ticks_usec()
	for a in [hamster, vogel, spinne]:
		if a.shown:
			if a.hold:
				a.tick(0.0)
				continue
			a.t += dt
			a.st_t += dt
			a.tick(dt)
	if spinne.shown:
		_lens_update()
	stats["us"] = lerpf(float(stats["us"]), float(Time.get_ticks_usec() - t0), 0.1)


# ---- the spider in front of a lens: the parameters of lens.gdshader -------------------------------------------------------
static func coc_mm(f_mm: float, n: float, d_m: float, s_m: float) -> float:
	"""diameter of the circle of confusion on the sensor (mm) for a point at d_m when the lens is focused at s_m
	(thin lens: c = A · |s − d| / d · f / (s − f), A = f / N)"""
	var f := f_mm / 1000.0
	return (f_mm / n) * absf(s_m - d_m) / maxf(d_m, 0.001) * f / maxf(s_m - f, 0.001)


func _lens_off() -> void:
	if main == null:
		return
	for i in range(mini(2, main.lens_mats.size())):
		if _lens_set[i]:
			(main.lens_mats[i] as ShaderMaterial).set_shader_parameter("spider", 0.0)
			_lens_set[i] = false


func _lens_update() -> void:
	var gp: Vector3 = spinne.gpos()
	var near_any := false
	for i in range(mini(2, main.lens_mats.size())):
		var cam: Camera3D = main.cams[i]
		var lm: ShaderMaterial = main.lens_mats[i]
		var ci := cam.global_transform.affine_inverse()
		var q: Vector3 = ci * gp
		var d := -q.z
		var on := spinne.visible_now() and d > 0.004 and d < NEAR_M
		var asp := float(main.CAM_W[i]) / float(main.CAM_H[i])
		var tw := tan(deg_to_rad(float(main.CAM_FOV[i])) * 0.5)
		var uv := Vector2.ZERO
		if on:
			uv = Vector2(0.5 + 0.5 * q.x / (d * tw), 0.5 - 0.5 * q.y / (d * tw / asp))
			on = absf(uv.x - 0.5) < 1.6 and absf(uv.y - 0.5) < 1.6     # partly in the picture (legs reach far)
		if not on:
			if _lens_set[i]:
				lm.set_shader_parameter("spider", 0.0)
				_lens_set[i] = false
			continue
		near_any = true
		var o: Array = OPTIK[i]
		var c := coc_mm(float(o[0]), float(o[1]), d, FOCUS_M)
		var b_h := 0.5 * c * asp / SENSOR_W_MM                          # blur radius in picture heights
		var cb := ci.basis
		var fw: Vector3 = cb * spinne.fwd_g()
		var nn: Vector3 = cb * spinne.up_g()
		var sd := Vector2(fw.x, -fw.y)
		var lit := dark() and (main.ir_on() or (main.white_light != null and main.white_light.light_energy > 0.01))
		var vis := 1.0
		if dark() and not lit:
			vis = 0.06                                                   # dark room, no light of MoveEye: almost nothing
		lm.set_shader_parameter("spider", vis)
		lm.set_shader_parameter("sp_c", uv)
		lm.set_shader_parameter("sp_k", asp / (2.0 * d * tw))           # metres -> picture heights
		lm.set_shader_parameter("sp_dir", sd.normalized() if sd.length() > 0.001 else Vector2(0, 1))
		lm.set_shader_parameter("sp_blur", minf(b_h, 0.8))
		lm.set_shader_parameter("sp_lit", 1.0 if lit else 0.0)            # IR LEDs a few cm away: always over-exposed
		lm.set_shader_parameter("sp_leg", spinne.leg_phase)
		lm.set_shader_parameter("sp_squash", clampf(absf(nn.z), 0.25, 1.0))
		lm.set_shader_parameter("sp_thread", 1.0 if spinne.on_thread() else 0.0)
		lm.set_shader_parameter("sp_size", spinne.size_k)
		_lens_set[i] = true
	spinne.set_near(near_any)


func lens_now(dist := 0.0, hold := false) -> Dictionary:
	if not valid():
		return {"ok": false, "error": "nur in der Szene Schlafzimmer"}
	if not spider_on:
		spider_on = true
		save()
		_update_shown(true)
	return spinne.start_lens(dist, hold)


# =============================================================================================================================
# ---- the animals -------------------------------------------------------------------------------------------------------------
# =============================================================================================================================
class Tier:
	var zt
	var id := ""
	var vroot: Node3D
	var t := 0.0
	var st := ""
	var st_t := 0.0
	var shown := true
	var hold := false

	func _init(z) -> void:
		zt = z
		vroot = Node3D.new()
		z.room.add_child(vroot)

	func build() -> void:
		pass

	func go(s_: String) -> void:
		st = s_
		st_t = 0.0

	func tick(_dt: float) -> void:
		pass

	func set_shown(on: bool) -> void:
		if on != shown:
			shown = on
			vroot.visible = on

	func info() -> Dictionary:
		return {"id": id, "state": st, "shown": shown, "t": snappedf(t, 0.1)}


# ---- golden hamster in a glass cage on the chest of drawers -------------------------------------------------------------------
# Goldhamster (Mesocricetus auratus): 13–18 cm, 100–150 g. In der Haltung nachtaktiv: Laufrad fast nur in der Dunkelphase
# (Gattermann R. et al. 2008, «Golden hamsters are nocturnal in captivity but diurnal in nature», Biology Letters 4:
# 253–255). Läuft in Schüben von Sekunden bis Minuten; oft genannt 5–9 km pro Nacht (Halter-Angaben, Schätzwert).
# Tempo im Rad hier 0.5–1.0 m/s (Schätzwert), Gehen 0.15–0.3 m/s. Rad 28 cm Durchmesser (empfohlene Mindestgrösse).
class Hamster extends Tier:
	const WR := 0.14                # wheel radius m
	var cage: Node3D
	var ham: Node3D
	var legs: Array = []
	var wheel: Node3D               # turns (the stripes on the back show it)
	var w_c := Vector3.ZERO         # wheel centre (cage)
	var w_ang := 0.0
	var w_om := 0.0                 # rad/s
	var run_v := 0.0
	var pos := Vector3.ZERO         # hamster in the cage (x, z on the bedding)
	var tgt := Vector3.ZERO
	var dur := 0.0
	var house := Vector3(-0.27, 0, 0.02)
	var bowl := Vector3(-0.05, 0, 0.1)
	var bottle := Vector3(0.12, 0, -0.15)
	const FLOOR := 0.06            # top of the bedding (cage)

	func build() -> void:
		id = "hamster"
		var lite: bool = zt.lite
		# chest of drawers 1.1 × 0.75 × 0.45 m against the front wall, right of the door
		var ch: Node3D = zt.node(vroot, Vector3(0.45, 0.04, -4.7))
		zt.part(ch, zt.boxm(1.1, 0.75, 0.45), Vector3(0, 0.375, 0), Color(0.86, 0.84, 0.8), "stone")
		for k in range(3):
			zt.part(ch, zt.boxm(0.02, 0.02, 0.01), Vector3(0, 0.15 + k * 0.22, 0.228), Color(0.5, 0.45, 0.38), "stone")
		zt.main.add_obstacle(Vector3(0.45, 0, -4.7), 0.6)
		# glass cage 80 × 40 × 40 cm on it (plastic tray, wire lid)
		cage = zt.node(vroot, Vector3(0.45, 0.79, -4.7))
		zt.part(cage, zt.boxm(0.8, 0.012, 0.4), Vector3(0, 0.006, 0), Color(0.35, 0.55, 0.75), "stone")
		zt.part(cage, zt.boxm(0.78, 0.05, 0.38), Vector3(0, 0.035, 0), Color(0.86, 0.78, 0.58), zt.room_t())   # bedding (wood chips)
		zt.glass(cage, Vector3(0.8, 0.4, 0.004), Vector3(0, 0.2, 0.2))
		zt.glass(cage, Vector3(0.8, 0.4, 0.004), Vector3(0, 0.2, -0.2))
		zt.glass(cage, Vector3(0.004, 0.4, 0.4), Vector3(0.4, 0.2, 0))
		zt.glass(cage, Vector3(0.004, 0.4, 0.4), Vector3(-0.4, 0.2, 0))
		var lid := []
		var step := 0.05 if lite else 0.025
		var x := -0.4
		while x <= 0.401:
			lid.append([Vector3(x, 0.4, -0.2), Vector3(x, 0.4, 0.2)])
			x += step
		lid.append([Vector3(-0.4, 0.4, -0.2), Vector3(0.4, 0.4, -0.2)])
		lid.append([Vector3(-0.4, 0.4, 0.2), Vector3(0.4, 0.4, 0.2)])
		zt.bars(cage, lid, Color(0.75, 0.75, 0.75), 0.0015)
		# little wooden house (entrance towards the middle), bowl, drinking bottle
		zt.part(cage, zt.boxm(0.16, 0.12, 0.14), Vector3(house.x - 0.02, FLOOR + 0.06, house.z), Color(0.62, 0.45, 0.28), zt.room_t() + 1.0)   # a sleeping hamster warms it a little
		zt.part(cage, zt.boxm(0.003, 0.06, 0.05), Vector3(house.x + 0.061, FLOOR + 0.035, house.z), Color(0.08, 0.06, 0.05), zt.room_t() + 2.0)   # the dark entrance
		zt.part(cage, zt.cylm(0.04, 0.035, 0.025, 10), Vector3(bowl.x, FLOOR + 0.012, bowl.z), Color(0.85, 0.5, 0.3), zt.room_t())
		zt.part(cage, zt.cylm(0.025, 0.025, 0.14, 8), Vector3(bottle.x, 0.26, -0.185), Color(0.7, 0.85, 0.95), zt.room_t(), Vector3(0, 0, 0))
		zt.part(cage, zt.cylm(0.003, 0.003, 0.08, 4), Vector3(bottle.x, 0.16, -0.17), Color(0.7, 0.7, 0.7), zt.room_t(), Vector3(0.5, 0, 0))
		# wheel 28 cm, axis towards the camera (front open), on a stand on the right
		w_c = Vector3(0.22, FLOOR + 0.025 + WR, -0.05)
		zt.part(cage, zt.boxm(0.04, w_c.y - FLOOR, 0.03), Vector3(w_c.x, FLOOR + (w_c.y - FLOOR) / 2.0, w_c.z - 0.05), Color(0.3, 0.6, 0.85), zt.room_t())
		wheel = zt.node(cage, w_c)
		zt.part(wheel, zt.cylm(WR, WR, 0.006, 20), Vector3(0, 0, -0.04), Color(0.3, 0.6, 0.85), zt.room_t(), Vector3(PI / 2.0, 0, 0))   # back plate
		var rim := TorusMesh.new()
		rim.inner_radius = WR - 0.006
		rim.outer_radius = WR + 0.004
		rim.rings = 20 if not lite else 12
		rim.ring_segments = 4
		zt.part(wheel, rim, Vector3(0, 0, 0.035), Color(0.3, 0.6, 0.85), zt.room_t(), Vector3(PI / 2.0, 0, 0))
		for k in range(3):                                     # stripes on the back plate: show that it turns
			zt.part(wheel, zt.boxm(0.012, WR * 1.9, 0.003), Vector3(0, 0, -0.035), Color(0.92, 0.95, 0.98), zt.room_t(), Vector3(0, 0, k * PI / 3.0))
		# the hamster: body 15 cm (golden, white belly), head, ears, black eyes, four short legs
		ham = zt.node(cage, Vector3(house.x, FLOOR, house.z))
		var gold := Color(0.8, 0.55, 0.3)
		var body_t: float = Waerme.animal("hamster", zt.room_t(), "body")
		var head_t: float = Waerme.animal("hamster", zt.room_t(), "head")
		zt.part(ham, zt.sphm(0.045, 0.08, 10), Vector3(0, 0.04, 0.01), gold, body_t, Vector3.ZERO, Vector3(1.0, 1.0, 1.45))
		zt.part(ham, zt.sphm(0.035, 0.05, 8), Vector3(0, 0.025, 0.015), Color(0.95, 0.92, 0.86), body_t, Vector3.ZERO, Vector3(1.0, 1.0, 1.4))
		zt.part(ham, zt.sphm(0.03, 0.055, 8), Vector3(0, 0.05, -0.065), gold, head_t)
		for sx in [-1, 1]:
			zt.part(ham, zt.sphm(0.011, 0.008, 6), Vector3(0.018 * sx, 0.08, -0.06), Color(0.6, 0.35, 0.3), head_t)
			zt.part(ham, zt.sphm(0.005), Vector3(0.02 * sx, 0.06, -0.088), Color(0.03, 0.03, 0.03), head_t)
		for k in range(4):
			var lx := 0.025 * (1 if k % 2 == 0 else -1)
			var lz := -0.04 if k < 2 else 0.05
			var lg: Node3D = zt.node(ham, Vector3(lx, 0.02, lz))
			zt.part(lg, zt.boxm(0.012, 0.022, 0.016), Vector3(0, -0.011, 0), Color(0.9, 0.75, 0.68), Waerme.animal("hamster", zt.room_t(), "legs"))
			legs.append(lg)
		pos = house
		go("sleep")

	func active_time() -> bool:
		var h: float = zt.hour()
		return h >= 20.5 or h < 5.5 or (zt.dark() and (h >= 18.0 or h < 7.0))

	func _place(p: Vector3, yaw: float, bob := 0.0) -> void:
		ham.position = Vector3(p.x, FLOOR + bob, p.z)
		ham.rotation = Vector3(0, yaw, 0)

	func _walk(dt: float, spd: float) -> bool:
		var d := tgt - pos
		d.y = 0.0
		var L := d.length()
		if L < 0.01:
			return true
		pos += d / L * minf(spd * dt, L)
		var yaw := atan2(-d.x, -d.z)
		ham.rotation.y = rotate_toward(ham.rotation.y, yaw, dt * 8.0)
		var ph := t * 14.0
		for i in range(legs.size()):
			(legs[i] as Node3D).rotation.x = sin(ph + (PI if (i == 1 or i == 2) else 0.0)) * 0.6
		ham.position = Vector3(pos.x, FLOOR + absf(sin(ph)) * 0.004, pos.z)
		return false

	func _rand_spot() -> Vector3:
		for _i in range(8):
			var p := Vector3(randf_range(-0.33, 0.33), 0, randf_range(-0.15, 0.15))
			if p.distance_to(Vector3(w_c.x, 0, w_c.z)) > 0.18 and p.distance_to(house) > 0.12:
				return p
		return Vector3(0.0, 0, 0.05)

	func _next() -> void:
		"""what next (at night)"""
		var r := randf()
		if r < 0.5:
			tgt = Vector3(w_c.x - 0.02, 0, w_c.z)
			go("to_wheel")
		elif r < 0.7:
			tgt = _rand_spot()
			go("walk")
		elif r < 0.85:
			tgt = bowl + Vector3(0.06, 0, -0.01)
			go("to_eat")
		else:
			tgt = bottle + Vector3(0, 0, 0.06)
			go("to_drink")

	func tick(dt: float) -> void:
		# the wheel turns on with its own inertia (coasts down when the hamster is not running)
		if st == "wheel":
			w_om = move_toward(w_om, run_v / WR, dt * 18.0)
		else:
			w_om = move_toward(w_om, 0.0, dt * (1.2 + absf(w_om) * 0.25))
		w_ang += w_om * dt
		wheel.rotation.z = w_ang
		match st:
			"sleep":                              # in the house: not seen
				ham.visible = false
				if active_time() and st_t > 2.0:
					ham.visible = true
					pos = house + Vector3(0.09, 0, 0)
					_place(pos, -PI / 2.0)
					go("wake")
			"wake":                               # sits in front of the house, sniffs, cleans its face
				ham.visible = true
				ham.rotation.x = -0.25 * absf(sin(st_t * 3.0)) if st_t < 3.0 else 0.0
				if st_t > 4.0:
					ham.rotation.x = 0.0
					_next()
			"walk":
				if _walk(dt, 0.22):
					dur = randf_range(1.0, 5.0)
					go("pause")
			"pause":                              # stands, sniffs (head bobs a little)
				ham.position.y = FLOOR + 0.003 * absf(sin(st_t * 9.0))
				if st_t > dur:
					if not active_time():
						tgt = house + Vector3(0.09, 0, 0)
						go("to_house")
					else:
						_next()
			"to_eat", "to_drink":
				if _walk(dt, 0.2):
					dur = randf_range(8.0, 30.0) if st == "to_eat" else randf_range(4.0, 12.0)
					var look := bowl if st == "to_eat" else bottle
					ham.rotation.y = atan2(-(look.x - pos.x), -(look.z - pos.z))
					go("eat" if st == "to_eat" else "drink")
			"eat":                                # sits up, nibbles (head and front moves fast and small)
				ham.rotation.x = -0.35
				ham.position.y = FLOOR + 0.004 * absf(sin(st_t * 11.0))
				if st_t > dur:
					ham.rotation.x = 0.0
					_next()
			"drink":
				ham.rotation.x = -0.6
				if st_t > dur:
					ham.rotation.x = 0.0
					_next()
			"to_wheel":
				if _walk(dt, 0.25):
					run_v = randf_range(0.5, 1.0)
					dur = randf_range(20.0, 240.0) if randf() < 0.8 else randf_range(3.0, 12.0)
					go("wheel")
			"wheel":                              # runs at the bottom of the wheel: stays in place, the wheel turns
				if fmod(st_t, 7.0) < dt:
					run_v = clampf(run_v + randf_range(-0.15, 0.15), 0.4, 1.05)
				var stride := 5.0 + run_v * 4.0   # strides per second (Schätzwert)
				var ph := st_t * stride * TAU
				var p := Vector3(w_c.x, 0, w_c.z + 0.005)
				ham.position = Vector3(p.x - 0.01, w_c.y - WR + 0.006 + absf(sin(ph * 0.5)) * 0.006, p.z)
				ham.rotation = Vector3(0, -PI / 2.0, 0.08)           # running towards -x: the wheel turns the other way
				for i in range(legs.size()):
					(legs[i] as Node3D).rotation.x = sin(ph + (PI if i >= 2 else 0.0)) * 0.9
				if st_t > dur:
					pos = Vector3(w_c.x - 0.17, 0, w_c.z + 0.05)
					_place(pos, PI / 2.0)
					dur = randf_range(2.0, 10.0)
					go("pause")
			"to_house":
				if _walk(dt, 0.2):
					go("sleep")
					ham.visible = false
		if st == "wheel":
			pass
		elif st != "sleep" and not active_time() and not st in ["to_house", "pause"]:
			tgt = house + Vector3(0.09, 0, 0)
			go("to_house")

	func info() -> Dictionary:
		var d := super.info()
		d["wheel_rps"] = snappedf(absf(w_om) / TAU, 0.01)
		d["run_mps"] = snappedf(run_v if st == "wheel" else 0.0, 0.01)
		return d


# ---- budgie in a cage on a stand ----------------------------------------------------------------------------------------------
# Wellensittich (Melopsittacus undulatus): 18 cm mit Schwanz, 30–40 g, tagaktiv; schläft nachts aufgeplustert auf einer
# hohen Stange, Kopf nach hinten ins Gefieder. Flügelschlag ~14 Hz (Tobalske B.W., Dial K.P. 1994, «Neuromuscular control
# and kinematics of intermittent flight in budgerigars», J. Exp. Biol. 187: 1–18). Hüpfer 10–25 cm (Schätzwert).
class Vogel extends Tier:
	var bird: Node3D
	var head: Node3D
	var wings: Array = []
	var bell: Node3D
	var bell_v := 0.0
	var bell_a := 0.0
	var perches: Array = []         # [x0, x1, y, z] in the cage
	var cur := 1                    # perch
	var px := 0.0
	var from_p := Vector3.ZERO
	var to_p := Vector3.ZERO
	var dur := 0.0
	var fluff := 1.0
	const W := 0.5
	const D := 0.32
	const H := 0.55

	func build() -> void:
		id = "vogel"
		var lite: bool = zt.lite
		var stand: Node3D = zt.node(vroot, Vector3(-2.42, 0.04, -4.4))
		zt.part(stand, zt.cylm(0.2, 0.22, 0.03, 12), Vector3(0, 0.015, 0), Color(0.2, 0.2, 0.22), "stone")
		zt.part(stand, zt.cylm(0.015, 0.015, 0.95, 6), Vector3(0, 0.49, 0), Color(0.2, 0.2, 0.22), "stone")
		zt.main.add_obstacle(Vector3(-2.42, 0, -4.4), 0.35)
		var cg: Node3D = zt.node(stand, Vector3(0, 0.97, 0))
		zt.part(cg, zt.boxm(W + 0.03, 0.06, D + 0.03), Vector3(0, 0.03, 0), Color(0.85, 0.85, 0.82), zt.room_t())   # plastic tray
		zt.part(cg, zt.boxm(W, 0.006, D), Vector3(0, 0.064, 0), Color(0.8, 0.72, 0.55), zt.room_t())               # sand
		var bl := []
		var step := 0.05 if lite else 0.025
		var x := -W / 2.0
		while x <= W / 2.0 + 0.001:
			for zz in [-D / 2.0, D / 2.0]:
				bl.append([Vector3(x, 0.06, zz), Vector3(x, H, zz)])
			x += step
		var z := -D / 2.0 + step
		while z < D / 2.0 - 0.001:
			for xx in [-W / 2.0, W / 2.0]:
				bl.append([Vector3(xx, 0.06, z), Vector3(xx, H, z)])
			z += step
		for yy in [0.06, H]:
			bl.append([Vector3(-W / 2.0, yy, -D / 2.0), Vector3(W / 2.0, yy, -D / 2.0)])
			bl.append([Vector3(-W / 2.0, yy, D / 2.0), Vector3(W / 2.0, yy, D / 2.0)])
			bl.append([Vector3(-W / 2.0, yy, -D / 2.0), Vector3(-W / 2.0, yy, D / 2.0)])
			bl.append([Vector3(W / 2.0, yy, -D / 2.0), Vector3(W / 2.0, yy, D / 2.0)])
		x = -W / 2.0
		while x <= W / 2.0 + 0.001:                          # roof
			bl.append([Vector3(x, H, -D / 2.0), Vector3(x, H, D / 2.0)])
			x += step * 2.0
		zt.bars(cg, bl, Color(0.92, 0.92, 0.9), 0.0012)
		# perches (wood, 1.2 cm): low left, middle right, high in the middle
		perches = [[-0.22, -0.02, 0.2, 0.0], [0.02, 0.22, 0.3, 0.02], [-0.12, 0.12, 0.43, -0.03]]
		for pr in perches:
			var l := float(pr[1]) - float(pr[0])
			zt.part(cg, zt.cylm(0.006, 0.006, l, 6), Vector3((float(pr[0]) + float(pr[1])) / 2.0, float(pr[2]), float(pr[3])), Color(0.6, 0.45, 0.3), zt.room_t(), Vector3(0, 0, PI / 2.0))
		zt.part(cg, zt.boxm(0.06, 0.04, 0.04), Vector3(-0.17, 0.09, 0.1), Color(0.95, 0.85, 0.3), zt.room_t())    # seed cup
		bell = zt.node(cg, Vector3(0.15, H - 0.005, -0.06))
		zt.part(bell, zt.cylm(0.001, 0.001, 0.06, 4), Vector3(0, -0.03, 0), Color(0.6, 0.6, 0.6), zt.room_t())
		zt.part(bell, zt.sphm(0.012, 0.018, 8), Vector3(0, -0.065, 0), Color(0.85, 0.75, 0.3), zt.room_t())
		# the budgie: green body, yellow head, long tail, wings on pivots
		bird = zt.node(cg, Vector3.ZERO)
		var body_t: float = Waerme.animal("budgie", zt.room_t(), "body")
		var head_t: float = Waerme.animal("budgie", zt.room_t(), "head")
		var green := Color(0.35, 0.72, 0.22)
		zt.part(bird, zt.sphm(0.024, 0.06, 8), Vector3(0, 0.03, 0), green, body_t, Vector3(0.35, 0, 0))
		head = zt.node(bird, Vector3(0, 0.065, -0.012))
		zt.part(head, zt.sphm(0.017), Vector3.ZERO, Color(0.95, 0.88, 0.25), head_t)
		zt.part(head, zt.cylm(0.0, 0.006, 0.012, 5), Vector3(0, -0.004, -0.017), Color(0.95, 0.75, 0.35), head_t, Vector3(-PI / 2.0 - 0.6, 0, 0))   # beak
		for sx in [-1, 1]:
			zt.part(head, zt.sphm(0.003), Vector3(0.012 * sx, 0.004, -0.01), Color(0.03, 0.03, 0.03), head_t)
		zt.part(bird, zt.boxm(0.012, 0.004, 0.09), Vector3(0, 0.01, 0.06), Color(0.15, 0.35, 0.6), body_t - 2.0, Vector3(-0.5, 0, 0))   # tail
		for sx in [-1, 1]:
			var wp: Node3D = zt.node(bird, Vector3(0.02 * sx, 0.05, 0.0))
			zt.part(wp, zt.boxm(0.05, 0.004, 0.065), Vector3(0.025 * sx, 0, 0.012), Color(0.3, 0.55, 0.2), body_t - 1.0)
			wp.rotation.z = -1.35 * sx            # folded along the body
			wings.append(wp)
		px = 0.1
		_sit()
		go("sit")
		dur = 3.0

	func _perch_p(i: int, x: float) -> Vector3:
		var pr: Array = perches[i]
		return Vector3(clampf(x, float(pr[0]) + 0.02, float(pr[1]) - 0.02), float(pr[2]) + 0.006, float(pr[3]))

	func _sit() -> void:
		bird.position = _perch_p(cur, px)
		bird.rotation.y = PI                          # looks into the room (the camera)

	func _wings(open: float, flap: float) -> void:
		for i in range(2):
			var sx := 1.0 if i == 0 else -1.0
			(wings[i] as Node3D).rotation.z = (-1.35 + open * (1.1 + 0.6 * sin(flap))) * sx

	func awake() -> bool:
		var h: float = zt.hour()
		return h >= 6.5 and h < 20.5 and not (zt.dark() and (h < 7.5 or h > 19.0))

	func tick(dt: float) -> void:
		# the bell swings on after a peck (pendulum 6 cm: ~2 Hz)
		bell_v += (-bell_a * 39.0 - bell_v * 1.5) * dt
		bell_a += bell_v * dt
		bell.rotation.z = bell_a
		match st:
			"sit":                                # looks around (quick head turns), small bobs
				_wings(0.0, 0.0)
				fluff = move_toward(fluff, 1.0, dt)
				bird.scale = Vector3.ONE * fluff
				if fmod(st_t, 1.3) < dt:
					head.rotation.y = randf_range(-1.0, 1.0)
				bird.position.y = _perch_p(cur, px).y + 0.002 * absf(sin(st_t * 5.0)) * (1.0 if fmod(st_t, 4.0) < 1.0 else 0.0)
				if st_t > dur:
					if not awake():
						_to_sleep()
						return
					var r := randf()
					if r < 0.45:
						_hop()
					elif r < 0.6:
						dur = randf_range(1.0, 3.0)
						go("flutter")
					elif r < 0.75:
						dur = randf_range(3.0, 8.0)
						go("preen")
					elif r < 0.85 and cur == 2:
						dur = 1.5
						go("peck")
					else:
						dur = randf_range(2.0, 9.0)
						go("sit")
			"hop", "fly":                         # an arc to the next place, wings open (flight: beating)
				var k := clampf(st_t / dur, 0.0, 1.0)
				var p := from_p.lerp(to_p, k) + Vector3(0, (0.05 if st == "hop" else 0.12) * sin(k * PI), 0)
				bird.position = p
				bird.rotation.y = 0.0 if to_p.x == from_p.x else (-PI / 2.0 if to_p.x > from_p.x else PI / 2.0)
				_wings(0.6 if st == "hop" else 1.0, t * TAU * 14.0)
				if k >= 1.0:
					_sit()
					dur = randf_range(2.0, 8.0)
					go("sit")
			"flutter":                            # holds on to the perch and beats its wings (exercise)
				_wings(1.0, t * TAU * 14.0)
				if st_t > dur:
					dur = randf_range(2.0, 6.0)
					go("sit")
			"preen":                              # head down to the wing, now and then
				_wings(0.0, 0.0)
				head.rotation = Vector3(0.9, 0.9 * sin(st_t * 1.7), 0.0)
				if st_t > dur:
					head.rotation = Vector3.ZERO
					dur = randf_range(2.0, 6.0)
					go("sit")
			"peck":                               # pecks at the bell (top perch) - the bell swings
				head.rotation = Vector3(0.5 if fmod(st_t, 0.5) < 0.2 else 0.0, -0.6, 0.0)
				if fmod(st_t, 0.5) < dt:
					bell_v += 1.5
				if st_t > dur:
					head.rotation = Vector3.ZERO
					dur = randf_range(2.0, 6.0)
					go("sit")
			"to_sleep":
				var k2 := clampf(st_t / 0.5, 0.0, 1.0)
				bird.position = from_p.lerp(to_p, k2) + Vector3(0, 0.06 * sin(k2 * PI), 0)
				_wings(0.6 if k2 < 1.0 else 0.0, t * TAU * 14.0)
				if k2 >= 1.0:
					go("sleep")
			"sleep":                              # fluffed up, head turned back into the feathers; only breathing
				_wings(0.0, 0.0)
				fluff = move_toward(fluff, 1.15, dt * 0.2)
				bird.scale = Vector3(fluff, fluff, fluff) * (1.0 + 0.01 * sin(st_t * 4.5))
				head.rotation = Vector3(0.2, PI * 0.8, 0.0)
				if awake() and st_t > 2.0:
					head.rotation = Vector3.ZERO
					dur = 4.0
					go("sit")

	func _hop() -> void:
		from_p = bird.position
		var nxt := cur
		if randf() < 0.6:
			nxt = (cur + 1 + randi() % 2) % perches.size()
		var pr: Array = perches[nxt]
		var nx := randf_range(float(pr[0]) + 0.03, float(pr[1]) - 0.03)
		to_p = _perch_p(nxt, nx)
		var far := from_p.distance_to(to_p) > 0.22
		cur = nxt
		px = nx
		dur = 0.35 if not far else 0.6
		go("fly" if far else "hop")

	func _to_sleep() -> void:
		from_p = bird.position
		cur = 2
		px = 0.0
		to_p = _perch_p(cur, px)
		go("to_sleep")

	func info() -> Dictionary:
		var d := super.info()
		d["perch"] = cur
		return d


# ---- house spider on walls and ceiling; now and then right in front of the lens -----------------------------------------------
# Hauswinkelspinne (Eratigena atrica): Körper ♀ bis 18.5 mm, ♂ 12–15 mm; Beinspanne ♀ ~45 mm, ♂ 25–75 mm; Sprints bis
# 0.53 m/s (Guinness-Rekord, Wikipedia «Giant house spider»). Meist aber langsam unterwegs: 1–3 cm/s mit Pausen
# (Schätzwert), nachtaktiv, im Herbst wandern die Männchen durch die Wohnungen. Abseilen am Sicherheitsfaden 3–8 cm/s,
# Hochklettern 1–2 cm/s (Schätzwerte). Pendel am Faden: T = 2π √(L/g) (≈ 2 s bei 1 m).
class Spinne extends Tier:
	var sp: Node3D                  # the 3D spider (park: room coordinates while on a wall)
	var vis_meshes: Array = []      # its visible meshes (layer 1 <-> HELPER_LAYER when it is right at a lens)
	var legs: Array = []            # [pivot, side, index]
	var sid := "front"              # front | left | ceil | thread | lens | away
	var p := Vector3.ZERO           # position (room) on a wall / the ceiling
	var tgt := Vector3.ZERO
	var heading := Vector3(1, 0, 0)
	var spd := 0.02
	var go_t := 0.0                 # stop and go
	var moving := true
	var leg_phase := 0.0
	var size_k := 1.0
	var near := false
	var lens_next := 0.0            # main.now() of the next visit to the lens
	var lens_want := false
	var lens_dist := 0.0
	var lens_hold := false
	var top := Vector3.ZERO         # thread: fixed under the ceiling (global)
	var L := 0.0                    # thread length now
	var L_end := 0.0
	var spin := 0.0
	var lp := Vector2.ZERO          # on the lens housing: position (camera x, y in m)
	var lv := Vector2.ZERO          # its way over the housing
	var l_d := 0.012                # distance housing front -> lens
	var dur := 0.0
	var other_sid := "ceil"

	func build() -> void:
		id = "spinne"
		size_k = randf_range(0.8, 1.0)                 # female 18 mm … a smaller one
		sp = zt.node(vroot, Vector3.ZERO)
		var tk: float = Waerme.animal("spider", zt.room_t())   # = room temperature
		var brown := Color(0.32, 0.24, 0.16)
		var s := size_k
		vis_meshes.append(zt.part(sp, zt.sphm(0.0034 * s, 0.003 * s, 6), Vector3(0, 0.002 * s, -0.0045 * s), brown, tk, Vector3.ZERO, Vector3(1, 1, 1.25)))
		vis_meshes.append(zt.part(sp, zt.sphm(0.0044 * s, 0.0045 * s, 6), Vector3(0, 0.0028 * s, 0.0058 * s), Color(0.28, 0.2, 0.13), tk, Vector3.ZERO, Vector3(1, 1, 1.35)))
		for k in range(8):
			var sd := 1.0 if k < 4 else -1.0
			var j := float(k % 4)
			var pv: Node3D = zt.node(sp, Vector3(sd * 0.0028 * s, 0.0025 * s, (-0.0055 + j * 0.0012) * s))
			var an := 0.5 + j * 0.62
			var a1 := Vector3(sd * sin(an), 0.6, -cos(an)).normalized() * (0.0085 + 0.0012 * j) * s
			var an2 := an + 0.35 * (-1.0 if j < 2.0 else 1.0)
			var a2 := a1 + Vector3(sd * sin(an2), -0.75, -cos(an2)).normalized() * (0.012 + 0.0015 * j) * s
			if zt.lite:
				vis_meshes.append(zt.stick(pv, Vector3.ZERO, Vector3(a2.x, 0.0, a2.z), 0.0005 * s, brown, tk))
			else:
				vis_meshes.append(zt.stick(pv, Vector3.ZERO, a1, 0.0006 * s, brown, tk))
				vis_meshes.append(zt.stick(pv, a1, a2, 0.0005 * s, Color(0.36, 0.27, 0.18), tk))
			legs.append([pv, sd, j])
		sid = "front"
		p = Vector3(1.6, 1.9, FZ)
		tgt = p
		_new_lens_time()
		go("rest")
		dur = randf_range(5.0, 30.0)

	# -- surfaces --------------------------------------------------------------------------------------------------------
	func normal(s_: String) -> Vector3:
		match s_:
			"front":
				return Vector3(0, 0, 1)
			"left":
				return Vector3(1, 0, 0)
		return Vector3(0, -1, 0)

	func clampp(s_: String, q: Vector3) -> Vector3:
		match s_:
			"front":                              # right of the door (no hole on the way)
				return Vector3(clampf(q.x, -0.9, 3.35), clampf(q.y, 0.15, CY), FZ)
			"left":                               # in front of the window
				return Vector3(LX, clampf(q.y, 0.15, CY), clampf(q.z, -4.85, -3.1))
		return Vector3(clampf(q.x, LX, 3.4), CY, clampf(q.z, FZ, 1.4))

	func rand_on(s_: String) -> Vector3:
		var c := p + Vector3(randf_range(-0.6, 0.6), randf_range(-0.5, 0.5), randf_range(-0.6, 0.6))
		if randf() < 0.3:                          # spiders like corners and edges
			match s_:
				"front":
					c.y = CY if randf() < 0.5 else 0.15
				"left":
					c.z = -4.85
				"ceil":
					c.z = FZ
		return clampp(s_, c)

	func edge(a: String, b: String) -> Vector3:
		"""the point on the edge between surface a and b nearest to p"""
		if (a == "front" and b == "ceil") or (a == "ceil" and b == "front"):
			return Vector3(clampf(p.x, -0.9, 3.35), CY, FZ)
		return Vector3(LX, CY, clampf(p.z, -4.85, -3.1))

	func gpos() -> Vector3:
		return sp.global_position

	func fwd_g() -> Vector3:
		return -sp.global_transform.basis.z.normalized()

	func up_g() -> Vector3:
		return sp.global_transform.basis.y.normalized()

	func visible_now() -> bool:
		return shown and sp.visible and sid != "away"

	func on_thread() -> bool:
		return sid == "thread"

	func set_near(on: bool) -> void:
		"""right at a lens: the 3D spider only for the operator's view (the lens shader draws it for MoveEye)"""
		if on == near:
			return
		near = on
		for mi in vis_meshes:
			if is_instance_valid(mi):
				(mi as MeshInstance3D).layers = zt.main.HELPER_LAYER if on else 1

	func _new_lens_time() -> void:
		# «manchmal»: at night every ~5–20 min, by day every ~20–60 min (real time)
		var night: bool = zt.dark()
		lens_next = zt.main.now() + (randf_range(300.0, 1200.0) if night else randf_range(1200.0, 3600.0))

	func start_lens(dist := 0.0, hold_ := false) -> Dictionary:
		lens_want = true
		lens_dist = dist
		lens_hold = hold_
		if sid in ["thread", "lens"]:
			return {"ok": true, "state": st}
		if dist > 0.0:                             # tests: straight to the thread in front of the lens (no long walk)
			sid = "ceil"
			_begin_drop(true)
			return {"ok": true, "state": st, "dist": dist}
		go("to_lens")
		return {"ok": true, "state": st}

	func _cam() -> Camera3D:
		return zt.main.cams[0] if zt.main.cams.size() > 0 else null

	func _drop_point() -> Vector3:
		"""a point a few cm in front of the head camera (global)"""
		var cam := _cam()
		if cam == null:
			return Vector3(0, 1.6, -0.05)
		var ct := cam.global_transform
		var f := -ct.basis.z
		f.y = 0.0
		f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
		var d := lens_dist if lens_dist > 0.0 else randf_range(0.025, 0.07)
		var side := ct.basis.x.normalized() * randf_range(-0.012, 0.012)
		return ct.origin + f * d + side + Vector3(0, randf_range(-0.012, 0.008), 0)

	func _begin_drop(jump := false) -> void:
		var dp := _drop_point()
		var top_y: float = zt.room.to_global(Vector3(0, CY, 0)).y
		top = Vector3(dp.x, top_y, dp.z)
		L_end = top_y - dp.y
		L = 0.0 if not jump else L_end
		sid = "thread"
		spin = randf_range(0.0, TAU)
		go("descend" if not jump else "dangle")
		dur = randf_range(8.0, 25.0)

	# -- moving -------------------------------------------------------------------------------------------------------
	func _orient_wall(dt: float) -> void:
		var n := normal(sid)
		var d := tgt - p
		d -= n * d.dot(n)
		if d.length() > 0.0005:
			heading = heading.slerp(d.normalized(), clampf(dt * 5.0, 0.0, 1.0)).normalized() if heading.dot(d.normalized()) > -0.95 else d.normalized()
		heading -= n * heading.dot(n)
		if heading.length() < 0.001:
			heading = Vector3(1, 0, 0) if absf(n.x) < 0.9 else Vector3(0, 0, -1)
		heading = heading.normalized()
		var lt := zt.room.global_transform
		var gp: Vector3 = lt * (p + n * 0.0005)
		var gb: Basis = lt.basis * Basis.looking_at(heading, n)
		sp.global_transform = Transform3D(gb, gp)

	func _walk(dt: float) -> bool:
		"""stop and go towards tgt on the current surface; true = there"""
		go_t -= dt
		if go_t <= 0.0:
			moving = not moving if spd < 0.2 else true
			go_t = randf_range(0.8, 4.0) if moving else randf_range(0.4, 3.0)
		var d := tgt - p
		var dl := d.length()
		if dl < 0.004:
			return true
		if moving:
			p += d / dl * minf(spd * dt, dl)
			leg_phase += dt * spd * 420.0               # 2 cm/s -> ~1.3 steps per second
			_legs(0.25)
		else:
			_legs(0.0)
		_orient_wall(dt)
		return false

	func _legs(amp: float) -> void:
		for lg in legs:
			var pv: Node3D = lg[0]
			var off := float(lg[2]) * 1.5708 + (0.0 if float(lg[1]) > 0.0 else PI)
			pv.rotation.y = sin(leg_phase + off) * amp * float(lg[1])

	func _pick() -> void:
		"""a new aim: on this surface, or over an edge to the next"""
		var night: bool = zt.dark()
		spd = randf_range(0.01, 0.03)
		if randf() < (0.06 if night else 0.02):
			spd = randf_range(0.3, 0.53)                # a short sprint
		if randf() < 0.25:
			var other := "ceil" if sid != "ceil" else ("front" if randf() < 0.65 else "left")
			tgt = edge(sid, other)
			other_sid = other
			go("to_edge")
		else:
			tgt = rand_on(sid)
			if spd > 0.2:
				tgt = clampp(sid, p + (tgt - p).normalized() * randf_range(0.1, 0.25))
			go("walk")

	func tick(dt: float) -> void:
		if not lens_want and zt.main.now() > lens_next and st in ["rest", "walk"]:
			lens_want = true
			lens_dist = 0.0
			lens_hold = false
			go("to_lens")
		match st:
			"rest":                               # sits still (by day mostly), legs spread
				_legs(0.0)
				_orient_wall(dt)
				if st_t > dur:
					_pick()
			"walk":
				if _walk(dt):
					var night: bool = zt.dark()
					if randf() < (0.35 if night else 0.7):
						dur = randf_range(5.0, 40.0) if night else randf_range(30.0, 240.0)
						go("rest")
					else:
						_pick()
			"to_edge":
				if _walk(dt):
					sid = other_sid
					p = clampp(sid, p)
					heading = (heading - normal(sid) * heading.dot(normal(sid)))
					if heading.length() < 0.01:
						heading = Vector3(1, 0, 0) if sid != "left" else Vector3(0, 0, -1)
					heading = heading.normalized()
					_pick()
			"to_lens":                            # to the ceiling, then right above the head camera
				spd = 0.03
				if sid != "ceil":
					tgt = edge(sid, "ceil")
					if _walk(dt):
						sid = "ceil"
						p = clampp(sid, p)
				else:
					var dp := _drop_point()
					tgt = clampp("ceil", zt.room.to_local(dp))
					if _walk(dt) or st_t > 120.0:
						_begin_drop()
			"descend":                            # down on the safety thread, slower near the end
				var v := 0.06 if L_end - L > 0.1 else 0.025
				L = minf(L + v * dt, L_end)
				_thread_pose(dt)
				if L >= L_end - 0.0005:
					go("dangle")
			"dangle":                             # hangs a few cm in front of the lens: turns and swings a little
				_thread_pose(dt)
				if fmod(st_t, 3.0) < dt:
					leg_phase += randf_range(-0.6, 0.6)
				if lens_hold:
					return
				if st_t > dur:
					if randf() < 0.5:
						go("climb")
					else:
						_onto_housing()
			"climb":                              # back up its thread
				L = maxf(L - 0.015 * dt, 0.0)
				leg_phase += dt * 6.0
				_thread_pose(dt)
				if L <= 0.002:
					_back_on_ceiling()
			"lens":                               # walks over the front of the housing, right over the lens
				var cam := _cam()
				if cam == null:
					_back_on_ceiling()
					return
				go_t -= dt
				if go_t <= 0.0:
					moving = not moving
					go_t = randf_range(0.6, 3.0) if moving else randf_range(0.5, 4.0)
				if moving and not lens_hold:
					lp += lv * dt
					leg_phase += dt * 5.0
				_legs(0.25 if moving else 0.0)
				var ct := cam.global_transform
				var fl := Vector3(lv.x, lv.y, 0.0).normalized()
				var gb := ct.basis * Basis.looking_at(fl if fl.length() > 0.1 else Vector3(0, 1, 0), Vector3(0, 0, 1))
				sp.global_transform = Transform3D(gb, ct * Vector3(lp.x, lp.y, -l_d))
				if lp.length() > 0.05 and not lens_hold:
					sid = "away"                   # on top of the housing / behind it: out of the picture
					sp.visible = false
					dur = randf_range(20.0, 60.0)
					go("away")
			"away":
				if st_t > dur:
					sp.visible = true
					_back_on_ceiling()

	func _thread_pose(dt: float) -> void:
		var g := 9.81
		var w := sqrt(g / maxf(L, 0.05))
		spin += dt * 0.25 * sin(t * 0.13)
		var sway := Vector3(sin(t * w) * 0.004, 0, cos(t * w * 0.93) * 0.003) * clampf(L, 0.0, 1.0)
		var gp := top + Vector3(0, -L, 0) + sway
		var n := Vector3(cos(spin), 0, sin(spin))
		var gb := Basis.looking_at(Vector3.DOWN, n)    # head down, back towards n
		sp.global_transform = Transform3D(gb, gp)
		_legs(0.05)

	func _onto_housing() -> void:
		var cam := _cam()
		if cam == null:
			go("climb")
			return
		var q: Vector3 = cam.global_transform.affine_inverse() * gpos()
		lp = Vector2(clampf(q.x, -0.02, 0.02), clampf(q.y, -0.015, 0.02))
		var a := randf_range(0.0, TAU)
		lv = Vector2(cos(a), sin(a)) * randf_range(0.006, 0.012)
		l_d = randf_range(0.01, 0.016)
		sid = "lens"
		moving = true
		go_t = 1.0
		go("lens")

	func _back_on_ceiling() -> void:
		sid = "ceil"
		p = clampp("ceil", zt.room.to_local(top if top != Vector3.ZERO else Vector3(0, CY, -0.3)))
		tgt = p
		lens_want = false
		lens_hold = false
		_new_lens_time()
		dur = randf_range(10.0, 60.0)
		sp.visible = true
		go("rest")

	func info() -> Dictionary:
		var d := super.info()
		d["on"] = sid
		d["near_lens"] = near
		var cam := _cam()
		if cam != null:
			d["d_lens_m"] = snappedf(-(cam.global_transform.affine_inverse() * gpos()).z, 0.001)
		d["next_lens_s"] = int(maxf(0.0, lens_next - float(zt.main.now())))
		return d


# =============================================================================================================================
# ---- the discovery book (entdecken.gd) and control ---------------------------------------------------------------------------
# =============================================================================================================================
func _register() -> void:
	var e = ent()
	if e == null:
		return
	e.register("zimmer.hamster_laufrad", {"scene": "schlafzimmer", "title": T.t("Hamster im Laufrad"),
			"short_text": T.t("Nachts rennt der Hamster im Laufrad – stundenlang kleine Bewegung. MoveEye soll deswegen keinen Alarm geben."),
			"hint": T.t("Auf der Kommode beim Eingang raschelt es nachts."), "icon": "🐹", "kind": "tier", "node": hamster.cage,
			"position": Vector3(0, 0.2, 0), "size": Vector3(0.8, 0.4, 0.4), "radius": 3.5, "when": "night",
			"active": func(): return hamster.st == "wheel" and hamster.shown})
	e.register("zimmer.wellensittich", {"scene": "schlafzimmer", "title": T.t("Wellensittich"),
			"short_text": T.t("Er hüpft von Stange zu Stange, flattert und pickt ans Glöckchen. Nachts schläft er aufgeplustert."),
			"hint": T.t("Im Käfig in der Ecke beim Eingang ist am Tag viel los."), "icon": "🐦", "kind": "tier", "node": vogel.bird,
			"position": Vector3(0, 0.03, 0), "size": Vector3(0.5, 0.5, 0.35), "radius": 3.5, "when": "day",
			"active": func(): return vogel.shown})
	e.register("zimmer.spinne_linse", {"scene": "schlafzimmer", "title": T.t("Spinne vor der Linse"),
			"short_text": T.t("Eine Hauswinkelspinne seilt sich direkt vor MoveEyes Kamera ab – unscharf und nachts im Infrarot hell: ein klassischer Fehlalarm."),
			"hint": T.t("Nachts kommt von der Decke manchmal jemand mit acht Beinen ganz nah an MoveEye."), "icon": "🕷", "kind": "tier",
			"node": spinne.sp, "position": Vector3.ZERO, "size": Vector3(0.05, 0.05, 0.05), "radius": 1.0, "los": false,
			"active": func(): return spinne.shown and spinne.near})


func control(d: Dictionary) -> Dictionary:
	match str(d.get("do", "info")):
		"lens":
			return lens_now(float(d.get("dist", 0.0)), bool(d.get("hold", false)))
		"set":
			set_on(bool(d.get("pets", pets_on)), bool(d.get("spider", spider_on)))
			return {"ok": true, "pets": pets_on, "spider": spider_on}
		"state":
			if not valid():
				return {"ok": false, "error": "nur in der Szene Schlafzimmer"}
			var who := {"hamster": hamster, "vogel": vogel, "spinne": spinne}
			var a = who.get(str(d.get("who", "")), null)
			if a == null:
				return {"ok": false, "error": "who: hamster | vogel | spinne"}
			if d.has("state"):
				a.go(str(d["state"]))
				if d.has("dur"):
					a.dur = float(d["dur"])
			a.hold = bool(d.get("hold", false))
			return {"ok": true}
	var out := []
	if valid():
		for a in [hamster, vogel, spinne]:
			out.append(a.info())
	return {"ok": true, "scene": str(main.scene), "pets": pets_on, "spider": spider_on, "lite": lite, "animals": out, "stats": stats}
