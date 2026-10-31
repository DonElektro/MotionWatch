extends Node3D
## 3D-4.x «Erlebniswelt Ferienpark am See» (Daniel 31.10.2026, Vignetten 1–19 + Schnecken-Rennen aus 22, Stil «dezent»):
## kleine Abläufe an den reservierten Orten von ferienpark.gd (ERLEBNIS) - Humor durch Timing und Bewegung, keine
## Sprechblasen, man muss genau hinschauen.
##   A Tiere:   1 Katze vor den Mauslöchern · 2 Eichhörnchen klaut Nüsse · 3 Entenfamilie · 4 Igel · 5 Hund mit Ball ·
##              6 Fuchs am Abfall (nachts) · 7 Möwe klaut Pommes
##   B Menschen: 8 Zeltaufbau-Chaos · 9 Grillmeister · 10 Angler (Stiefel; einmal am Tag der Riesenfisch) ·
##              11 Schlafwandler (nachts, winkt MoveEye) · 12 Kinder spielen Verstecken (auch mit MoveEye) · 13 Yoga (morgens)
##   C Orte:    Glühwürmchen in der Höhle (nachts), Igel-Bibliothek im alten Wohnwagen, Wanderzwerg (jeden Tag woanders),
##              Flaschenpost -> Schatzkiste; Schnecken-Rennen (nur bei Regen)
## Jede Vignette ist eine kleine Zustandsmaschine (innere Klasse). Sie läuft nur, wenn die Ansicht (Fenster-Kamera) oder
## MoveEye näher als ACTIVE_R ist - sonst steht sie still (Figuren ohne _process). Bei Testlauf / Prüfstand / Messung sind
## alle Vignetten weg (vergleichbare Ergebnisse). Menschen und Tiere sind Figuren von actor.gd im «puppet»-Modus (Haltung und
## Ort setzt dieses Skript; Wärmebild wie alle Figuren), kleine Tiere und Dinge aus Grundformen mit Wärme-Zwilling.
## Entdeckungen: main.entdecken.register() (Szene «ferienpark», ids «see.…»). Steuerung: {"action": "ferienpark", "do": "erleben"}.
## Lite: _lite() (Engine-Meta «lite», wie bib_objekte.gd) - weniger Küken, keine Tropfen, ein Rauch statt drei.

const T = preload("res://scripts/i18n.gd")
const Bib = preload("res://scripts/bib_objekte.gd")

const ACTIVE_R := 60.0         # m: closer than this (window camera or MoveEye) the vignette moves
const SHOW_R := 180.0          # m: farther than this from both, its figures are hidden (fewer draw calls)
const WATER_Y := 0.0           # the lake surface (park coordinates)

var m                          # main.gd
var fp                         # ferienpark.gd (park transform, ground)
var s                          # scenes.gd
var park: Node3D
var holder: Node3D             # park-space node for the things of the vignettes
var lite := false
var vigs: Array = []
var by_id := {}
var _tick := 0.0
var _quiet := false
var stats := {"active": 0, "shown": 0, "actors": 0, "us": 0.0}
var today := ""                # the date (the gnome walks, the giant fish bites once a day)
var day_seed := 0


static func _lite() -> bool:
	"""Lite graphics (Raspberry Pi) - the coordinator joins it with Quality.lite()"""
	return Engine.has_meta("lite") and bool(Engine.get_meta("lite"))


func setup(fp_) -> void:
	fp = fp_
	m = fp.m
	s = fp.s
	park = fp.park
	name = "erlebniswelt"
	lite = _lite() or str(m.quality) == "simple"
	process_priority = 100                      # after the figures: own heights (jetty, table, water) win over the ground
	s.root.add_child(self)
	holder = Node3D.new()
	holder.name = "erleben"
	park.add_child(holder)
	today = Time.get_date_string_from_system()
	day_seed = absi(hash(today))
	for v in [Katze.new(self), Eichhorn.new(self), Enten.new(self), Igel.new(self), Hund.new(self), Fuchs.new(self), Moewe.new(self),
			Zelt.new(self), Grill.new(self), Angler.new(self), Schlafwandler.new(self), Verstecken.new(self), Yoga.new(self)]:
		v.build()
		vigs.append(v)
		by_id[v.id] = v
	_register()
	_update_shown(true)


# ---- helpers: park <-> world, ground, figures, small meshes ------------------------------------------------------------------
func W(p: Vector3) -> Vector3:
	return park.transform * p


func Pg(x: float, z: float, dy := 0.0) -> Vector3:
	var h: float = fp.H(x, z)
	return Vector3(x, h + dy, z)


func toP(w: Vector3) -> Vector3:
	return park.transform.affine_inverse() * w


func zs(x: float) -> float:
	var z: float = fp.zs(x)
	return z


func head_pos() -> Vector3:
	return (m.head as Node3D).global_position if m.head != null else Vector3.ZERO


func view_pos() -> Vector3:
	var c := get_viewport().get_camera_3d()
	return c.global_position if c != null else Vector3(0, 1000, 0)


func actor(kind: String, p: Vector3, look: Vector3, spd := 1.2, jacket = null) -> Node3D:
	"""a figure of actor.gd as a puppet at p (park), facing look (park point)"""
	var a = m.Actor.new()
	if jacket != null:
		a.player_color = jacket                                   # actor.gd takes it as the jacket colour
	add_child(a)
	var wp := W(p)
	a.setup(m, kind, wp, W(look), spd)
	a.puppet = true
	a.set_meta("nachbar", true)                                   # like the neighbours of szenenplus.gd: never part of a test
	a.set_meta("erleben", true)
	a.add_to_group("erleben_fig")                                 # overlay3d.gd: MoveEye's boxes on these count as «erkannt», not as false alarm
	if a.lamp != null:                                            # no torch / phone light (set_night would switch it on)
		a.lamp.light_energy = 0.0
		a.lamp_mat.emission_energy_multiplier = 0.0
		a.lamp = null
		a.phone_out = false
	face(a, look - p)
	return a


func face(a, d: Vector3) -> void:
	"""turn a figure towards the park direction d (at once)"""
	var wd: Vector3 = park.transform.basis * Vector3(d.x, 0, d.z)
	if wd.length() < 0.001:
		return
	a.heading = atan2(-wd.x, -wd.z)
	a.rotation.y = a.heading
	a.dir = wd.normalized()


func turn_to(a, d: Vector3, dt: float, rate := 4.0) -> bool:
	"""turn smoothly; true when done"""
	var wd: Vector3 = park.transform.basis * Vector3(d.x, 0, d.z)
	if wd.length() < 0.001:
		return true
	var want := atan2(-wd.x, -wd.z)
	a.heading = rotate_toward(float(a.heading), want, rate * dt)
	a.rotation.y = a.heading
	return absf(wrapf(want - float(a.heading), -PI, PI)) < 0.05


func ppos(a) -> Vector3:
	"""where a figure is (park coordinates, on the ground)"""
	var q := toP((a as Node3D).global_position)
	return Vector3(q.x, 0, q.z)


func place(a, p: Vector3, lift := false) -> void:
	"""a figure at the park point p; lift = keep its own height (jetty, table, water - not the ground)"""
	var wp := W(p)
	a.position = wp
	if lift:
		a.set_meta("ew_y", wp.y)
	elif a.has_meta("ew_y"):
		a.remove_meta("ew_y")


func walk(a, to: Vector3, spd: float, dt: float, lift_y = null, turn := 6.0) -> bool:
	"""a few steps towards the park point «to» (x, z) at spd m/s; true = arrived (and stands)"""
	var p := ppos(a)
	var d := Vector3(to.x - p.x, 0, to.z - p.z)
	var L := d.length()
	if L < 0.08:
		a.cur_speed = move_toward(float(a.cur_speed), 0.0, dt * 4.0)
		return true
	turn_to(a, d, dt, turn)
	a.cur_speed = move_toward(float(a.cur_speed), spd, dt * 3.0 * maxf(1.0, spd))
	var st: float = minf(float(a.cur_speed) * dt, L)
	var np := p + d / L * st
	if lift_y == null:
		var wp := W(Pg(np.x, np.z))
		a.position = Vector3(wp.x, a.position.y, wp.z)
		if a.has_meta("ew_y"):
			a.remove_meta("ew_y")
	else:
		var wp2 := W(Vector3(np.x, float(lift_y), np.z))
		a.position = wp2
		a.set_meta("ew_y", wp2.y)
	return false


func stop(a, dt: float) -> void:
	a.cur_speed = move_toward(float(a.cur_speed), 0.0, dt * 4.0)


func idle(a, k: String, secs := 1.0e5) -> void:
	a.idle_kind = k
	a.idle_until = a.now_s() + secs if k != "" else 0.0


func node(parent: Node3D, p: Vector3, ry := 0.0) -> Node3D:
	var n := Node3D.new()
	n.position = p
	n.rotation.y = ry
	parent.add_child(n)
	return n


func part(parent: Node3D, mesh: Mesh, p: Vector3, col: Color, tk, rot := Vector3.ZERO, scl := Vector3.ONE) -> MeshInstance3D:
	"""a visible part + its twin for the thermal camera (tk: °C or a surface key like "stone", "tree", "tent")"""
	var mi: MeshInstance3D = m.add_mesh(parent, mesh, p, m.mat(col), tk, rot, scl)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if lite else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	return mi


func twin_of(mi: MeshInstance3D) -> MeshInstance3D:
	"""the thermal twin made right after mi by main.add_mesh"""
	var par := mi.get_parent()
	var i := mi.get_index() + 1
	return par.get_child(i) as MeshInstance3D if i < par.get_child_count() else null


func set_heat(mi: MeshInstance3D, temp: float) -> void:
	var th := twin_of(mi)
	if th != null:
		th.material_override = m.tmat_fixed(temp)


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
	c.radial_segments = seg if not lite else maxi(5, seg / 2)
	c.rings = 1
	return c


func glow_mat(c: Color, e := 2.0) -> StandardMaterial3D:
	var gm := StandardMaterial3D.new()
	gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	gm.albedo_color = c
	gm.emission_enabled = true
	gm.emission = c
	gm.emission_energy_multiplier = e
	return gm


func light_part(parent: Node3D, mesh: Mesh, p: Vector3, mt: Material) -> MeshInstance3D:
	"""a part only for the normal cameras (cold light: glow-worms - the thermal camera does not see it)"""
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = p
	mi.material_override = mt
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


func hour() -> float:
	var h: float = m.hour()
	return h


func dark() -> bool:
	return bool(m.is_dark())


func rain() -> bool:
	return str(m.weather) == "rain"


func ent():
	var e = m.get("entdecken")
	return e if e != null and e.has_method("register") else null


# ---- running: only what is near, nothing during tests --------------------------------------------------------------------
func _is_quiet() -> bool:
	var e = ent()
	if e != null and e.has_method("_quiet"):
		return bool(e._quiet())
	return bool(m.measuring())


func _update_shown(force := false) -> void:
	var q := _is_quiet()
	var vp := view_pos()
	var hp := head_pos()
	var na := 0
	var ns := 0
	var nact := 0
	for v in vigs:
		var w: Vector3 = v.where()
		var d := minf(vp.distance_to(w), hp.distance_to(w))
		var sh: bool = not q and v.when_ok() and d < SHOW_R
		var ac: bool = sh and (d < ACTIVE_R or v.always)
		if sh != v.shown or force:
			v.set_shown(sh)
		if ac != v.active or force:
			v.active = ac
			for a in v.actors:
				if is_instance_valid(a):
					a.process_mode = Node.PROCESS_MODE_INHERIT if ac else Node.PROCESS_MODE_DISABLED
		na += 1 if ac else 0
		ns += 1 if sh else 0
		nact += v.actors.size()
	stats["active"] = na
	stats["shown"] = ns
	stats["actors"] = nact
	_quiet = q


func _process(dt: float) -> void:
	if m == null or not is_inside_tree():
		return
	dt = minf(dt, 0.25)
	_tick -= dt
	if _tick <= 0.0:
		_tick = 0.6 if lite else 0.3
		_update_shown()
	var t0 := Time.get_ticks_usec()
	for v in vigs:
		if v.active:
			if v.hold:                                               # tests: a state held still (screenshots)
				v.tick(0.0)
				continue
			v.t += dt
			v.st_t += dt
			v.tick(dt)
	for a in get_children():                                         # own heights (after the figures put themselves on the ground)
		if a.has_meta("ew_y") and a.process_mode != Node.PROCESS_MODE_DISABLED:
			a.position.y = float(a.get_meta("ew_y"))
	stats["us"] = lerpf(float(stats["us"]), float(Time.get_ticks_usec() - t0), 0.1)


# =============================================================================================================================
# ---- the vignettes ------------------------------------------------------------------------------------------------------------
# =============================================================================================================================
class Vig:
	var ew
	var id := ""
	var c := Vector3.ZERO           # park centre
	var actors: Array = []
	var nodes: Array = []           # park-space nodes shown / hidden with the vignette
	var t := 0.0                    # own clock (only runs while active)
	var st := ""
	var st_t := 0.0
	var active := false
	var shown := true
	var hold := false               # tests: keep the state (control «state» with hold)
	var always := false             # moves even when nobody is near (the sleepwalker walks to MoveEye)
	var vroot: Node3D               # park-space node of all its things (shown / hidden as a whole)

	func _init(e) -> void:
		ew = e
		vroot = Node3D.new()
		e.holder.add_child(vroot)

	func build() -> void:
		pass

	func when_ok() -> bool:
		return true

	func where() -> Vector3:
		return ew.W(c)

	func go(s_: String) -> void:
		st = s_
		st_t = 0.0

	func tick(_dt: float) -> void:
		pass

	func set_shown(on: bool) -> void:
		shown = on
		vroot.visible = on
		for a in actors:
			if is_instance_valid(a):
				a.visible = on
		if not on:
			on_hide()

	func on_hide() -> void:
		pass

	func info() -> Dictionary:
		return {"id": id, "state": st, "active": active, "shown": shown, "t": snappedf(t, 0.1)}


# ---- 1 · cat in front of two mouse holes -------------------------------------------------------------------------------------
class Katze extends Vig:
	var cat
	var mouse: Node3D
	var holes: Array = []
	var watch := 0                  # the hole the cat looks at
	var yaw := 0.0
	var n := 0                      # rounds (every 4th: the mouse sits behind the cat)
	var m_from := Vector3.ZERO
	var m_to := Vector3.ZERO

	func build() -> void:
		id = "katze"
		c = ew.Pg(-118.0, -102.0)
		holes = [ew.Pg(-118.9, -102.74), ew.Pg(-117.1, -102.74)]
		cat = ew.actor("cat", ew.Pg(-118.0, -101.75), ew.Pg(-118.0, -103.0), 1.0)
		ew.idle(cat, "sit")
		actors.append(cat)
		mouse = ew.node(vroot, holes[0])
		var mc := Color(0.42, 0.39, 0.36)
		# house mouse: fur surface ~30 °C (small mammal, thin fur; IR thermography of rodents 28–34 °C)
		ew.part(mouse, ew.sphm(0.03, 0.05), Vector3(0, 0.025, 0), mc, 30.0, Vector3.ZERO, Vector3(1, 1, 1.5))
		ew.part(mouse, ew.sphm(0.018), Vector3(0, 0.03, -0.05), mc, 31.0)
		for sx in [-1, 1]:
			ew.part(mouse, ew.sphm(0.009), Vector3(0.012 * sx, 0.05, -0.045), Color(0.75, 0.6, 0.58), 30.0)
		ew.part(mouse, ew.cylm(0.003, 0.004, 0.08, 4), Vector3(0, 0.01, 0.07), Color(0.7, 0.55, 0.52), 26.0, Vector3(PI / 2.2, 0, 0))
		mouse.visible = false
		nodes.append(mouse)
		go("watch")

	func tick(dt: float) -> void:
		var hole: Vector3 = holes[watch]
		var other: Vector3 = holes[1 - watch]
		match st:
			"watch":                                  # the cat stares at one hole
				if st_t > 2.5 + fmod(t * 0.37, 2.5):
					n += 1
					if n % 4 == 0:
						m_from = other
						m_to = ew.Pg(-118.0 + 0.18, -101.2)        # right behind the cat
						go("sneak")
					else:
						go("peek")
			"peek":                                   # the mouse looks out of the OTHER hole
				mouse.visible = true
				var k := clampf(st_t / 0.4, 0.0, 1.0)
				mouse.position = other + Vector3(0, 0, 0.05 * k)
				mouse.rotation.y = PI
				if st_t > 1.1:                         # the cat turns its head - just too late
					watch = 1 - watch
					go("turn")
			"turn":
				var k2 := clampf(1.0 - st_t / 0.25, 0.0, 1.0)
				mouse.position = hole + Vector3(0, 0, 0.05 * k2)
				if st_t > 0.25:
					mouse.visible = false
				if st_t > 0.8:
					go("watch")
			"sneak":                                  # out of the other hole, round to behind the cat
				mouse.visible = true
				var k3 := clampf(st_t / 1.6, 0.0, 1.0)
				var mid: Vector3 = m_from.lerp(m_to, k3) + Vector3(0.25 * sin(k3 * PI), 0, 0)
				mouse.position = ew.Pg(mid.x, mid.z)
				mouse.rotation.y = atan2(-(m_to.x - m_from.x), -(m_to.z - m_from.z))
				if k3 >= 1.0:
					go("behind")
			"behind":                                 # sits behind the cat, cleans its whiskers; the cat stares on
				mouse.position = ew.Pg(m_to.x, m_to.z) + Vector3(0, 0.006 * absf(sin(st_t * 9.0)), 0)
				mouse.rotation.y = PI * 0.15
				if st_t > 3.5:
					m_from = m_to
					m_to = holes[1 - watch]
					go("back")
			"back":
				var k4 := clampf(st_t / 0.9, 0.0, 1.0)
				var q: Vector3 = m_from.lerp(m_to, k4)
				mouse.position = ew.Pg(q.x, q.z)
				mouse.rotation.y = atan2(-(m_to.x - m_from.x), -(m_to.z - m_from.z))
				if k4 >= 1.0:
					mouse.visible = false
					go("late")
			"late":                                   # only now the cat turns round - nothing there
				yaw = lerpf(yaw, 1.4, clampf(dt * 5.0, 0.0, 1.0))
				if st_t > 1.4:
					go("watch")
		var want: float = (0.72 if watch == 0 else -0.72)
		if st != "late":
			yaw = lerpf(yaw, want, clampf(dt * (9.0 if st == "turn" else 3.0), 0.0, 1.0))
		if cat.head != null:
			cat.head.rotation.y = yaw
			cat.head.rotation.x = -0.2

	func info() -> Dictionary:
		var d := super.info()
		d["mouse_behind"] = st == "behind"
		return d


# ---- 2 · squirrel takes nuts from the picnic table while the camper looks away -------------------------------------------------
class Eichhorn extends Vig:
	var sq
	var camper
	var bowl := Vector3.ZERO
	var nuts_t: Array = []          # nut meshes in the bowl
	var nuts_h: Array = []          # nuts stuck in the knot hole (the pile grows)
	var nuts_g: Array = []          # ... and fallen under the tree
	var left := 8
	var stash := 0
	var nut_mouth: Node3D
	var tree := Vector3.ZERO
	var hole := Vector3.ZERO
	var leg := Vector3.ZERO
	var top_y := 0.0
	var away := false
	var cam_t := 0.0

	func build() -> void:
		id = "eichhorn"
		c = ew.Pg(8.0, -78.5)
		var txf := Transform3D(Basis(Vector3.UP, 0.2), ew.Pg(6.0, -77.0))
		bowl = txf * Vector3(0.55, 0.79, 0.05)
		leg = txf * Vector3(0.9, 0, -0.45)
		top_y = bowl.y
		tree = ew.Pg(10.0, -80.5)
		hole = Vector3(10.0, tree.y + 2.2, -80.5 - 0.2)
		var n0: Node3D = ew.node(vroot, Vector3.ZERO)
		nodes.append(n0)
		ew.part(n0, ew.cylm(0.11, 0.08, 0.05, 10), bowl + Vector3(0, -0.005, 0), Color(0.82, 0.8, 0.76), "stone")
		for i in range(8):
			var a := TAU * i / 8.0
			nuts_t.append(ew.part(n0, ew.sphm(0.018), bowl + Vector3(cos(a) * 0.05, 0.03 + (i % 3) * 0.008, sin(a) * 0.05), Color(0.55, 0.36, 0.18), "tree"))
		for i in range(12):
			var a2 := (i - 5.5) * 0.25
			nuts_h.append(ew.part(n0, ew.sphm(0.017), hole + Vector3(sin(a2) * 0.07, -0.06 + (i / 4) * 0.025, 0.02 - absf(a2) * 0.02), Color(0.55, 0.36, 0.18), "tree"))
		for i in range(6):
			nuts_g.append(ew.part(n0, ew.sphm(0.018), Vector3(tree.x + 0.18 + 0.06 * (i % 3), tree.y + 0.015, tree.z - 0.25 - 0.05 * (i / 3)), Color(0.5, 0.33, 0.16), "tree"))
		for nn in nuts_h + nuts_g:
			nn.visible = false
		camper = ew.actor("person", txf * Vector3(-1.4, 0, 0.5), bowl, 1.2)
		actors.append(camper)
		sq = ew.actor("squirrel", tree + Vector3(0.3, 0, 0.1), bowl, 2.0)
		actors.append(sq)
		nut_mouth = ew.node(sq.head if sq.head != null else sq, Vector3(0, 0.0, -0.07))
		ew.part(nut_mouth, ew.sphm(0.018), Vector3.ZERO, Color(0.55, 0.36, 0.18), "tree")
		nut_mouth.visible = false
		go("wait")

	func when_ok() -> bool:
		var h: float = ew.hour()
		return h > 7.0 and h < 20.0

	func _show() -> void:
		for i in range(nuts_t.size()):
			nuts_t[i].visible = i < left
		for i in range(nuts_h.size()):
			nuts_h[i].visible = i < mini(stash, 12)
		for i in range(nuts_g.size()):
			nuts_g[i].visible = i < clampi(stash - 12, 0, 6)

	func _camper(dt: float) -> void:
		cam_t -= dt
		if cam_t <= 0.0:
			away = not away
			cam_t = randf_range(9.0, 15.0) if away else randf_range(5.0, 8.0)
		var look: Vector3 = Vector3(0.3, 0, -1.0) if away else (bowl - ew.ppos(camper))
		ew.turn_to(camper, look, dt, 2.5)
		ew.idle(camper, "phone" if away else "")
		ew.stop(camper, dt)

	func tick(dt: float) -> void:
		_camper(dt)
		_show()
		sq.rotation.x = 0.0
		match st:
			"wait":
				ew.idle(sq, "sit_up")
				ew.place(sq, tree + Vector3(0.3, 0, 0.1))
				if away and cam_t > 6.0 and st_t > 2.0:
					ew.idle(sq, "")
					go("to_table")
			"to_table":
				if ew.walk(sq, leg, 2.6, dt):
					go("up")
			"up":
				var k := clampf(st_t / 0.45, 0.0, 1.0)
				ew.place(sq, Vector3(leg.x, lerpf(leg.y, top_y, k), leg.z), true)
				sq.rotation.x = 1.3 * sin(k * PI)
				if k >= 1.0:
					go("on_table")
			"on_table":
				if not away:                           # caught? - sit very still until he looks away again
					ew.idle(sq, "sit_up")
					sq.cur_speed = 0.0
					st_t = minf(st_t, 0.2)
					return
				ew.idle(sq, "")
				if ew.walk(sq, bowl + Vector3(0.12, 0, 0.08), 0.9, dt, top_y):
					if left > 0:
						left -= 1
					nut_mouth.visible = true
					go("off")
			"off":
				if ew.walk(sq, leg, 1.2, dt, top_y):
					go("down")
			"down":
				var k2 := clampf(st_t / 0.4, 0.0, 1.0)
				ew.place(sq, Vector3(leg.x, lerpf(top_y, leg.y, k2), leg.z), k2 < 1.0)
				if k2 >= 1.0:
					go("to_tree")
			"to_tree":
				if ew.walk(sq, Vector3(tree.x, 0, tree.z + 0.16), 2.8, dt):
					go("climb")
			"climb":                                  # up the trunk to the knot hole
				var k3 := clampf(st_t / 1.6, 0.0, 1.0)
				ew.face(sq, Vector3(0, 0, -1))
				sq.rotation.x = PI / 2.0
				ew.place(sq, Vector3(tree.x, lerpf(tree.y + 0.1, hole.y - 0.2, k3), tree.z - 0.16), true)
				sq.cur_speed = 1.2 if k3 < 1.0 else 0.0
				if k3 >= 1.0:
					go("stash")
			"stash":
				sq.rotation.x = PI / 2.0
				if st_t > 0.8:
					nut_mouth.visible = false
					stash += 1
					go("climb_down")
			"climb_down":
				var k4 := clampf(st_t / 1.3, 0.0, 1.0)
				sq.rotation.x = -PI / 2.0
				ew.face(sq, Vector3(0, 0, 1))
				ew.place(sq, Vector3(tree.x, lerpf(hole.y - 0.2, tree.y + 0.1, k4), tree.z - 0.16), true)
				sq.cur_speed = 1.2 if k4 < 1.0 else 0.0
				if k4 >= 1.0:
					sq.rotation.x = 0.0
					ew.place(sq, tree + Vector3(0.3, 0, 0.1))
					if left == 0:
						go("empty")
					else:
						go("wait")
			"empty":                                  # the bowl is empty: the camper looks, looks again, refills
				ew.idle(sq, "sit_up")
				away = false
				cam_t = 2.0
				if st_t > 1.5 and st_t < 4.0:
					ew.idle(camper, "look", 2.0)
				if st_t > 4.0:
					ew.idle(camper, "bend", 2.0)
				if st_t > 6.0:
					left = 8
					if stash >= 18:
						stash = 0
					go("wait")

	func info() -> Dictionary:
		var d := super.info()
		d["bowl"] = left
		d["pile"] = stash
		d["camper_away"] = away
		return d


# ---- 3 · the duck family crosses the path, the last duckling dawdles and tumbles ----------------------------------------------
class Enten extends Vig:
	var ducks: Array = []           # [node, size]
	var trail: Array = []           # the mother's way (park points), newest first
	var path: Array = []
	var pi_ := 0
	var lag := 0.0                  # the last duckling: extra distance
	var dawdle := 0.0
	var roll := -1.0
	var rest := 0.0
	var dpos := Vector3.ZERO

	func build() -> void:
		id = "enten"
		c = ew.Pg(-165.0, -140.0)
		var shore: float = ew.zs(-166.0)
		path = [Vector3(-161.0, 0, -124.0), Vector3(-163.0, 0, -136.0), Vector3(-165.0, 0, -150.0), Vector3(-166.0, 0, shore + 0.5),
				Vector3(-167.0, 0, shore - 5.0), Vector3(-158.0, 0, shore - 7.0), Vector3(-157.0, 0, shore - 0.5), Vector3(-160.0, 0, -150.0),
				Vector3(-162.0, 0, -136.0), Vector3(-161.0, 0, -124.0)]
		var n: int = 3 if ew.lite else 5
		ducks.append([_duck(true), 1.0])
		for i in range(n):
			ducks.append([_duck(false), 0.3])
		dpos = path[0]
		for i in range(200):
			trail.append(dpos)
		go("walk")

	func _duck(mother: bool) -> Node3D:
		var nd: Node3D = ew.node(vroot, Vector3.ZERO)
		nodes.append(nd)
		var b := Node3D.new()
		b.name = "b"
		nd.add_child(b)
		# mallard: feather surface 25–30 °C, the head and bill warmer (bird thermography, e.g. McCafferty 2013, Ibis)
		if mother:
			ew.part(b, ew.sphm(0.13, 0.22), Vector3(0, 0.17, 0), Color(0.55, 0.42, 0.3), 27.0, Vector3.ZERO, Vector3(1.0, 0.9, 1.8))
			ew.part(b, ew.sphm(0.065), Vector3(0, 0.32, -0.2), Color(0.5, 0.38, 0.27), 33.0)
			ew.part(b, ew.boxm(0.04, 0.02, 0.07), Vector3(0, 0.31, -0.28), Color(0.85, 0.6, 0.2), 30.0)
			ew.part(b, ew.boxm(0.02, 0.1, 0.02), Vector3(0, 0.26, -0.16), Color(0.5, 0.38, 0.27), 31.0)
			ew.part(b, ew.boxm(0.08, 0.03, 0.08), Vector3(0, 0.2, 0.22), Color(0.35, 0.27, 0.2), 25.0, Vector3(-0.4, 0, 0))
			for sx in [-1, 1]:
				ew.part(b, ew.boxm(0.02, 0.09, 0.02), Vector3(0.05 * sx, 0.045, 0), Color(0.9, 0.55, 0.15), 22.0)
		else:
			ew.part(b, ew.sphm(0.05, 0.08), Vector3(0, 0.06, 0), Color(0.62, 0.52, 0.28), 30.0, Vector3.ZERO, Vector3(1, 1, 1.3))
			ew.part(b, ew.sphm(0.03), Vector3(0, 0.11, -0.05), Color(0.7, 0.6, 0.3), 32.0)
			ew.part(b, ew.boxm(0.018, 0.01, 0.025), Vector3(0, 0.105, -0.085), Color(0.3, 0.25, 0.2), 30.0)
			for sx in [-1, 1]:
				ew.part(b, ew.boxm(0.012, 0.035, 0.012), Vector3(0.02 * sx, 0.017, 0), Color(0.75, 0.5, 0.2), 25.0)
		return nd

	func where() -> Vector3:
		return ew.W(dpos)

	func tick(dt: float) -> void:
		var goal: Vector3 = path[pi_]
		var wet: bool = dpos.z < ew.zs(dpos.x) - 0.3
		var spd := 0.55 if not wet else 0.4
		if rest > 0.0:
			rest -= dt
			spd = 0.0
		var d := Vector3(goal.x - dpos.x, 0, goal.z - dpos.z)
		if spd > 0.0:
			if d.length() < 0.3:
				pi_ = (pi_ + 1) % path.size()
				if pi_ == 0 or pi_ == 5:
					rest = randf_range(12.0, 25.0)       # a rest in the grass / on the water
			else:
				dpos += d.normalized() * minf(spd * dt, d.length())
				if dpos.distance_to(trail[0]) > 0.04:
					trail.push_front(dpos)
					trail.resize(200)
		# the last one: stops now and then to peck, then runs after the others and tumbles once
		if spd > 0.0 and dawdle <= 0.0 and roll < 0.0 and not wet and fmod(t, 40.0) < dt * 1.5:
			dawdle = 4.0
		if dawdle > 0.0:
			dawdle -= dt
			lag += spd * dt
			if dawdle <= 0.0:
				roll = 0.0
		elif lag > 0.0:
			lag = maxf(0.0, lag - dt * 1.4)
		var n := ducks.size()
		for i in range(n):
			var nd: Node3D = ducks[i][0]
			var gap := 0.0 if i == 0 else 0.55 + (i - 1) * 0.32
			if i == n - 1:
				gap += lag
			var ti := clampi(int(gap / 0.04), 0, trail.size() - 2)
			var p: Vector3 = trail[ti]
			var ahead: Vector3 = trail[maxi(ti - 3, 0)]
			var onw: bool = p.z < ew.zs(p.x) - 0.3
			var y: float = (WATER_Y - (0.07 if i == 0 else 0.025)) if onw else ew.Pg(p.x, p.z).y
			nd.position = Vector3(p.x, y, p.z)
			if ahead.distance_to(p) > 0.01:
				nd.rotation.y = atan2(-(ahead.x - p.x), -(ahead.z - p.z))
			var b: Node3D = nd.get_node("b")
			var moving := spd > 0.0 or (i == n - 1 and lag > 0.0 and dawdle <= 0.0)
			b.rotation.z = (sin(t * (9.0 if i > 0 else 6.0) + i) * 0.12) if moving and not onw else 0.0
			b.rotation.x = 0.0
			b.position.y = 0.0
			if i == n - 1:
				if dawdle > 0.0:
					b.rotation.x = -0.5 * absf(sin(t * 6.0))          # pecks
					b.rotation.z = 0.0
				if roll >= 0.0:
					roll += dt
					var k := clampf(roll / 0.45, 0.0, 1.0)
					b.rotation.x = -TAU * k                            # head over heels
					b.position.y = 0.05 * sin(k * PI)
					if roll > 0.7:
						roll = -1.0

	func info() -> Dictionary:
		var d := super.info()
		d["at"] = [snappedf(dpos.x, 0.1), snappedf(dpos.z, 0.1)]
		d["dawdle"] = dawdle > 0.0
		d["tumble"] = roll >= 0.0
		return d


# ---- 4 · hedgehog at the bungalow hedge: rolls up when you come close, sneaks on when you wait ---------------------------------
class Igel extends Vig:
	var hh
	var a_ := Vector3.ZERO
	var b_ := Vector3.ZERO
	var dirn := 1.0
	var curl := 0.0
	var calm := 0.0
	var last_cam := Vector3.ZERO

	func build() -> void:
		id = "igel"
		c = ew.Pg(-60.8, 13.5)
		a_ = Vector3(-60.75, 0, 10.6)
		b_ = Vector3(-60.75, 0, 16.6)
		hh = ew.actor("hedgehog", ew.Pg(-60.75, 12.0), ew.Pg(-60.75, 16.0), 0.25)
		actors.append(hh)
		go("walk")

	func tick(dt: float) -> void:
		var cp: Vector3 = ew.view_pos()
		var hp: Vector3 = (hh as Node3D).global_position
		var dist := Vector2(cp.x - hp.x, cp.z - hp.z).length()
		var cam_v := cp.distance_to(last_cam) / maxf(dt, 0.001)
		last_cam = cp
		var close := dist < 4.5 and absf(cp.y - hp.y) < 5.0
		if close and (cam_v > 0.25 or dist < 2.0) and st != "curl":
			go("curl")
			calm = 0.0
		match st:
			"walk":
				curl = move_toward(curl, 0.0, dt * 0.6)
				if curl > 0.05:
					ew.stop(hh, dt)
				else:
					var goal: Vector3 = b_ if dirn > 0.0 else a_
					if fmod(t, 7.0) < 1.6:
						ew.idle(hh, "sniff", 0.5)
						ew.stop(hh, dt)
					elif ew.walk(hh, goal, 0.14, dt):
						dirn = -dirn
			"curl":
				ew.stop(hh, dt)
				curl = move_toward(curl, 1.0, dt * 3.0)
				if close and cam_v > 0.25:
					calm = 0.0
				else:
					calm += dt
				if calm > (6.0 if close else 2.5):
					go("walk")
		ew.idle(hh, "lie" if curl > 0.3 else ("" if hh.idle_kind == "lie" else hh.idle_kind), 0.5)
		hh.body_root.scale = Vector3(1.0, 1.0 + 0.35 * curl, 1.0 - 0.3 * curl)
		if hh.head != null:
			hh.head.rotation.x = -1.1 * curl
			hh.head.position.y = 0.08 - 0.05 * curl

	func info() -> Dictionary:
		var d := super.info()
		d["curl"] = snappedf(curl, 0.01)
		return d


# ---- 5 · dog brings the ball to everyone who passes, swims after it, shakes himself next to a camper ---------------------------
class Hund extends Vig:
	var dog
	var sun                          # the camper on the towel
	var ball: Node3D
	var ball_p := Vector3.ZERO       # park
	var ball_v := Vector3.ZERO
	var carried := true
	var target: Node3D = null        # a figure (visitor, camper) or null
	var tkind := ""                  # "view" (the window camera) · "visitor" · "camper"
	var tgt_p := Vector3.ZERO
	var tries := 0
	var drops: Array = []
	var sun_p := Vector3.ZERO

	func build() -> void:
		id = "hund"
		c = ew.Pg(-95.0, -160.0)
		var shore: float = ew.zs(-93.0)
		sun_p = ew.Pg(-93.0, shore + 9.0)
		var tw: Node3D = ew.node(vroot, sun_p + Vector3(0, 0.005, 0), 0.0)
		ew.part(tw, ew.boxm(0.9, 0.01, 1.9), Vector3(0, 0, -0.5), Color(0.85, 0.3, 0.3), "tent")
		nodes.append(tw)
		sun = ew.actor("person", sun_p, sun_p + Vector3(0, 0, -2), 1.0)
		sun.prone = 1.0
		actors.append(sun)
		dog = ew.actor("dog", sun_p + Vector3(2.0, 0, 0.5), sun_p, 3.0)
		actors.append(dog)
		ball = Node3D.new()
		ew.add_child(ball)
		ew.part(ball, ew.sphm(0.034, -1.0, 8), Vector3.ZERO, Color(0.8, 0.9, 0.2), "tent")
		if not ew.lite:
			var dm := StandardMaterial3D.new()
			dm.albedo_color = Color(0.8, 0.9, 1.0, 0.6)
			dm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			dm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			for i in range(10):
				var dr: MeshInstance3D = ew.light_part(vroot, ew.sphm(0.012, -1.0, 4), Vector3.ZERO, dm)
				dr.visible = false
				drops.append([dr, Vector3.ZERO])
		go("rest")

	func when_ok() -> bool:
		var h: float = ew.hour()
		return h > 8.0 and h < 20.0 and not ew.rain()

	func where() -> Vector3:
		return (dog as Node3D).global_position if is_instance_valid(dog) else ew.W(c)

	func set_shown(on: bool) -> void:
		super.set_shown(on)
		ball.visible = on

	func _mouth() -> Vector3:
		if dog.head != null:
			return (dog.head as Node3D).global_transform * Vector3(0, -0.03, -0.3)
		return (dog as Node3D).global_position + Vector3(0, 0.45, 0)

	func _pick() -> void:
		"""who gets the ball: the window camera if it is near and low (a passer-by), a visitor, else the camper"""
		target = null
		tkind = ""
		var cp: Vector3 = ew.view_pos()
		var cpp: Vector3 = ew.toP(cp)
		var dp: Vector3 = ew.ppos(dog)
		if tries == 0 and Vector2(cpp.x - dp.x, cpp.z - dp.z).length() < 16.0 and cpp.y - ew.Pg(cpp.x, cpp.z).y < 4.0:
			tkind = "view"
			tgt_p = Vector3(cpp.x, 0, cpp.z)
			return
		for v in ew.m.visitors.get_children():
			if v is Node3D and str(v.get("kind")) == "person":
				var vp: Vector3 = ew.toP((v as Node3D).global_position)
				if Vector2(vp.x - dp.x, vp.z - dp.z).length() < 22.0 and tries == 0:
					target = v
					tkind = "visitor"
					tgt_p = Vector3(vp.x, 0, vp.z)
					return
		target = sun
		tkind = "camper"
		tgt_p = sun_p

	func _wet(p: Vector3) -> bool:
		return p.z < ew.zs(p.x) - 0.4

	func tick(dt: float) -> void:
		var dp: Vector3 = ew.ppos(dog)
		var swim := _wet(dp)
		dog.body_root.rotation.z = 0.0
		if swim:
			ew.place(dog, Vector3(dp.x, WATER_Y - 0.36, dp.z), true)
		elif dog.has_meta("ew_y"):
			dog.remove_meta("ew_y")
		match st:
			"rest":
				ew.idle(dog, "lie", 1.0)
				ew.stop(dog, dt)
				if st_t > 8.0:
					ew.idle(dog, "", 0.0)
					_pick()
					go("bring")
			"bring":
				if tkind != "view" and target != null and is_instance_valid(target):
					var tp: Vector3 = ew.toP((target as Node3D).global_position)
					tgt_p = Vector3(tp.x, 0, tp.z)
				elif tkind == "view":
					var cpp: Vector3 = ew.toP(ew.view_pos())
					tgt_p = Vector3(cpp.x, 0, cpp.z)
				var to := tgt_p - dp
				to.y = 0
				var stand := tgt_p - to.normalized() * 1.1 if to.length() > 0.01 else tgt_p
				if tkind == "camper":
					stand = sun_p + Vector3(0.9, 0, -1.3)
				if ew.walk(dog, stand, 1.0 if swim else 3.2, dt) or st_t > 25.0:
					carried = false
					ball_p = ew.toP(_mouth())
					ball_p.y = ew.Pg(ball_p.x, ball_p.z).y + 0.034
					go("offer")
			"offer":                                    # sits, wags, waits
				ew.idle(dog, "sit", 1.0)
				ew.stop(dog, dt)
				ew.turn_to(dog, tgt_p - dp, dt, 3.0)
				if tkind == "camper":
					if st_t > 2.5:
						sun.prone = move_toward(float(sun.prone), 0.0, dt * 1.5)
						sun.crouch = move_toward(float(sun.crouch), 1.0, dt * 2.0)
					if st_t > 4.0 and st_t - dt <= 4.0:
						sun.play_emote("throw", 0.6)
					if st_t > 4.3:
						carried = false
						var far := randf() < 0.6
						var aim: Vector3 = sun_p + Vector3(randf_range(-6.0, 6.0), 0, -(randf_range(12.0, 18.0) if far else randf_range(4.0, 7.0)))
						ball_p = ew.toP((sun as Node3D).global_position) + Vector3(0.2, 1.4, -0.3)
						ball_v = Vector3((aim.x - ball_p.x) / 1.6, 7.0, (aim.z - ball_p.z) / 1.6)
						go("fly")
				elif st_t > 7.0:                     # nobody plays: pick it up again, nudge it closer once, then off to the camper
					carried = true
					tries += 1
					if tries >= 2:
						tries = 0
						target = sun
						tkind = "camper"
						tgt_p = sun_p
					go("bring")
			"fly":
				ew.idle(dog, "", 0.0)
				sun.crouch = move_toward(float(sun.crouch), 0.0, dt)
				sun.prone = move_toward(float(sun.prone), 1.0, dt * 0.8)
				ball_v.y -= 9.81 * dt
				ball_p += ball_v * dt
				var gy: float = WATER_Y if _wet(ball_p) else ew.Pg(ball_p.x, ball_p.z).y + 0.034
				if ball_p.y <= gy:
					ball_p.y = gy
					ball_v = Vector3.ZERO
				if st_t > 0.5:
					if ew.walk(dog, ball_p, 1.0 if swim else 4.0, dt) and ball_v == Vector3.ZERO:
						carried = true
						go("back")
				else:
					ew.stop(dog, dt)
			"back":
				var side: Vector3 = sun_p + Vector3(1.0, 0, -0.4)
				if ew.walk(dog, side, 1.0 if swim else 3.0, dt):
					go("shake" if bool(dog.get_meta("was_wet", false)) else "offer2")
				if swim:
					dog.set_meta("was_wet", true)
			"shake":                                    # right next to the camper - who jumps up
				ew.stop(dog, dt)
				dog.body_root.rotation.z = 0.5 * sin(st_t * 70.0) * clampf(1.2 - st_t, 0.0, 1.0)
				if st_t < 0.1:
					sun.startle_until = sun.now_s() + 1.2
					_spray()
				if st_t > 1.4:
					dog.set_meta("was_wet", false)
					carried = false
					ball_p = ew.toP(_mouth())
					ball_p.y = ew.Pg(ball_p.x, ball_p.z).y + 0.034
					go("rest")
			"offer2":
				carried = false
				ball_p = ew.toP(_mouth())
				ball_p.y = ew.Pg(ball_p.x, ball_p.z).y + 0.034
				go("rest")
		if st == "rest" or st == "bring":
			sun.prone = move_toward(float(sun.prone), 1.0, dt)
			sun.crouch = move_toward(float(sun.crouch), 0.0, dt)
		if st == "bring" and not carried:
			carried = true
		ball.global_position = _mouth() if carried else ew.W(ball_p)
		for d in drops:
			var dr: MeshInstance3D = d[0]
			if dr.visible:
				d[1] = (d[1] as Vector3) + Vector3(0, -9.81 * dt, 0)
				dr.position += (d[1] as Vector3) * dt
				if dr.position.y < ew.Pg(dr.position.x, dr.position.z).y:
					dr.visible = false

	func _spray() -> void:
		var o: Vector3 = ew.toP((dog as Node3D).global_position) + Vector3(0, 0.45, 0)
		for d in drops:
			(d[0] as MeshInstance3D).position = o
			(d[0] as MeshInstance3D).visible = true
			d[1] = Vector3(randf_range(-2.0, 2.0), randf_range(0.5, 2.0), randf_range(-2.0, 2.0))

	func info() -> Dictionary:
		var d := super.info()
		d["target"] = tkind
		d["swim"] = _wet(ew.ppos(dog))
		return d


# ---- 6 · fox at the bin at night: the lid falls, in the tent next to it a lamp goes on --------------------------------------------
class Fuchs extends Vig:
	var fox
	var lid: Node3D
	var bin := Vector3.ZERO
	var tent_m: StandardMaterial3D
	var tent_l: OmniLight3D
	var wrap: Node3D
	var light_t := -1.0
	var from := Vector3.ZERO
	var off := Vector3.ZERO

	func build() -> void:
		id = "fuchs"
		bin = ew.Pg(-101.6, -62.0)
		c = bin
		from = Vector3(-113.0, 0, -60.6)
		off = Vector3(-84.0, 0, -59.5)
		var bn: Node3D = ew.node(vroot, bin)
		nodes.append(bn)
		ew.part(bn, ew.cylm(0.24, 0.22, 0.8, 12), Vector3(0, 0.4, 0), Color(0.24, 0.42, 0.26), "caravan")
		lid = ew.node(bn, Vector3(0, 0.82, 0))
		ew.part(lid, ew.cylm(0.26, 0.26, 0.04, 12), Vector3.ZERO, Color(0.2, 0.35, 0.22), "caravan")
		ew.part(lid, ew.boxm(0.12, 0.03, 0.03), Vector3(0, 0.035, 0), Color(0.15, 0.15, 0.15), "caravan")
		# the small tent next to it (a lamp goes on inside: the fabric glows)
		var tp: Vector3 = ew.Pg(-108.6, -66.6)
		var tn: Node3D = ew.node(vroot, tp, 0.4)
		nodes.append(tn)
		tent_m = StandardMaterial3D.new()
		tent_m.albedo_color = Color(0.25, 0.42, 0.58)
		tent_m.emission_enabled = true
		tent_m.emission = Color(1.0, 0.78, 0.45)
		tent_m.emission_energy_multiplier = 0.0
		tent_m.roughness = 0.9
		var dome := SphereMesh.new()
		dome.radius = 1.05
		dome.height = 1.05
		dome.is_hemisphere = true
		dome.radial_segments = 14 if not ew.lite else 8
		dome.rings = 5
		var dm: MeshInstance3D = ew.m.add_mesh(tn, dome, Vector3.ZERO, tent_m, "tent", Vector3.ZERO, Vector3(1.0, 1.0, 1.25))
		dm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		ew.m.add_obstacle(ew.W(tp), 1.2)
		ew.m.set_obstacle_height(1.1)
		tent_l = OmniLight3D.new()
		tent_l.position = Vector3(0, 0.5, 0)
		tent_l.light_color = Color(1.0, 0.8, 0.5)
		tent_l.omni_range = 4.0
		tent_l.light_energy = 0.0
		tent_l.shadow_enabled = false
		tn.add_child(tent_l)
		fox = ew.actor("fox", ew.Pg(from.x, from.z), bin, 1.4)
		actors.append(fox)
		wrap = ew.node(fox.head if fox.head != null else fox, Vector3(0, -0.04, -0.28))
		ew.part(wrap, ew.boxm(0.1, 0.02, 0.08), Vector3.ZERO, Color(0.9, 0.88, 0.8), "tent")
		wrap.visible = false
		go("away")

	func when_ok() -> bool:
		return ew.dark()

	func on_hide() -> void:
		_light(false)

	func _light(on: bool) -> void:
		tent_m.emission_energy_multiplier = 0.9 if on else 0.0
		tent_l.light_energy = 0.8 if on else 0.0

	func at_bin() -> bool:
		return st in ["come", "rear", "lid", "jump", "wait", "rummage", "light", "freeze"]

	func tick(dt: float) -> void:
		if light_t >= 0.0:
			light_t += dt
			if light_t > 28.0:
				light_t = -1.0
				_light(false)
		var fb := bin + Vector3(-0.55, 0, 0.0)
		match st:
			"away":
				ew.place(fox, ew.Pg(from.x, from.z))
				fox.visible = false
				if st_t > 18.0:
					fox.visible = true
					lid.position = Vector3(0, 0.82, 0)
					lid.rotation = Vector3.ZERO
					go("come")
			"come":
				fox.visible = shown
				if fmod(t, 6.0) < 1.2:
					ew.idle(fox, "sniff", 0.4)
					ew.stop(fox, dt)
				elif ew.walk(fox, fb, 0.9, dt):
					go("rear")
			"rear":                                     # up on the hind legs, nose at the lid
				ew.turn_to(fox, bin - ew.ppos(fox), dt)
				ew.idle(fox, "sit_up", 0.5)
				if st_t > 1.3:
					go("lid")
			"lid":                                      # the lid slides off and clatters down
				var k := clampf(st_t / 0.6, 0.0, 1.0)
				lid.position = Vector3(0.35 * k, 0.82 - 0.8 * k * k, 0.1 * k)
				lid.rotation = Vector3(0, 0, -1.4 * k)
				if k >= 1.0:
					go("jump")
			"jump":                                     # startled: quickly back
				ew.idle(fox, "", 0.0)
				var away: Vector3 = ew.ppos(fox) + (ew.ppos(fox) - bin).normalized() * 0.9
				ew.walk(fox, away, 3.0, dt)
				if st_t > 0.35:
					go("wait")
			"wait":
				ew.stop(fox, dt)
				ew.idle(fox, "look", 0.5)
				if st_t > 2.2:
					go("rummage")
			"rummage":
				if ew.walk(fox, fb, 0.6, dt):
					ew.idle(fox, "sit_up", 0.5)
					if fox.head != null:
						fox.head.rotation.x = -0.6 + 0.15 * sin(st_t * 12.0)
				if st_t > 4.0:
					wrap.visible = true
					light_t = 0.0
					_light(true)
					go("freeze")
			"freeze":                                   # the light went on - the fox stands very still, then trots off
				ew.idle(fox, "stare", 0.5)
				ew.stop(fox, dt)
				if st_t > 3.0:
					go("off")
			"off":
				ew.idle(fox, "", 0.0)
				if ew.walk(fox, off, 1.6, dt):
					wrap.visible = false
					go("away")

	func info() -> Dictionary:
		var d := super.info()
		d["at_bin"] = at_bin()
		d["tent_light"] = light_t >= 0.0
		return d


# ---- 7 · seagull steals French fries from the restaurant terrace ---------------------------------------------------------------
class Moewe extends Vig:
	var gull: Node3D
	var wings: Array = []
	var guest
	var plate := Vector3.ZERO
	var seat := Vector3.ZERO
	var rail := Vector3.ZERO
	var fries: Array = []
	var left := 10
	var fry: Node3D
	var p0 := Vector3.ZERO
	var p1 := Vector3.ZERO
	var flap := 0.0

	func build() -> void:
		id = "moewe"
		var tz := -121.5 - 1.75
		var y: float = ew.fp.H(-30.0, -121.5 + 3.5) + 0.25
		plate = Vector3(-30.0, y + 0.775, tz)
		seat = Vector3(-30.0, y, tz + 0.95)
		rail = Vector3(-31.2, y, -124.6)
		c = plate
		var pn: Node3D = ew.node(vroot, plate)
		nodes.append(pn)
		ew.part(pn, ew.cylm(0.13, 0.12, 0.015, 14), Vector3.ZERO, Color(0.95, 0.95, 0.93), "stone")
		for i in range(10):
			var a := TAU * i / 10.0 + 0.3
			fries.append(ew.part(pn, ew.boxm(0.012, 0.012, 0.075), Vector3(cos(a) * 0.05, 0.015 + (i % 3) * 0.008, sin(a) * 0.05), Color(0.95, 0.78, 0.35), 40.0, Vector3(0, a * 1.7, 0.1)))
		guest = ew.actor("person", seat, plate, 1.1)
		guest.set_meta("ew_y", ew.W(seat).y)
		actors.append(guest)
		gull = ew.node(vroot, Vector3.ZERO)
		nodes.append(gull)
		# herring gull: plumage surface ~ 25–32 °C (feathered body), legs cool
		ew.part(gull, ew.sphm(0.11, 0.18), Vector3(0, 0.2, 0), Color(0.95, 0.95, 0.95), 30.0, Vector3.ZERO, Vector3(1, 1, 2.2))
		ew.part(gull, ew.sphm(0.065), Vector3(0, 0.3, -0.2), Color(0.97, 0.97, 0.97), 33.0)
		ew.part(gull, ew.boxm(0.025, 0.025, 0.08), Vector3(0, 0.29, -0.29), Color(0.95, 0.8, 0.2), 28.0)
		ew.part(gull, ew.boxm(0.08, 0.02, 0.14), Vector3(0, 0.22, 0.24), Color(0.2, 0.2, 0.22), 24.0)
		for sx in [-1, 1]:
			ew.part(gull, ew.boxm(0.012, 0.13, 0.012), Vector3(0.04 * sx, 0.065, 0), Color(0.85, 0.75, 0.5), 20.0)
			var w: Node3D = ew.node(gull, Vector3(0.09 * sx, 0.24, 0.02))
			ew.part(w, ew.boxm(0.55, 0.02, 0.2), Vector3(0.27 * sx, 0, 0), Color(0.62, 0.65, 0.7), 26.0)
			ew.part(w, ew.boxm(0.14, 0.021, 0.12), Vector3(0.5 * sx, 0, 0.03), Color(0.12, 0.12, 0.13), 24.0)
			wings.append([w, sx])
		fry = ew.node(gull, Vector3(0, 0.29, -0.33))
		ew.part(fry, ew.boxm(0.012, 0.012, 0.075), Vector3(0.03, 0, 0), Color(0.95, 0.78, 0.35), 35.0, Vector3(0, 1.4, 0))
		fry.visible = false
		gull.visible = false
		go("eat")

	func when_ok() -> bool:
		var h: float = ew.hour()
		return h > 10.0 and h < 21.0 and not ew.rain()

	func _wings(open: float, beat: bool, dt: float) -> void:
		flap += dt * 11.0
		for w in wings:
			var nd: Node3D = w[0]
			var a := (0.6 * sin(flap)) if beat else 0.0
			nd.rotation.z = (a + (1.0 - open) * 1.3) * float(w[1]) * -1.0
			nd.scale.x = lerpf(0.35, 1.0, open)

	func _fly(a: Vector3, b: Vector3, k: float, hgt: float) -> void:
		var p := a.lerp(b, k) + Vector3(0, hgt * sin(k * PI), 0)
		gull.position = p
		var d := b - a
		gull.rotation.y = atan2(-d.x, -d.z)

	func tick(dt: float) -> void:
		for i in range(fries.size()):
			fries[i].visible = i < left
		match st:
			"eat":                                      # the guest eats, then gets up for a photo of the lake
				ew.idle(guest, "bend" if fmod(st_t, 5.0) < 1.0 else "", 0.3)
				ew.turn_to(guest, plate - seat, dt)
				if st_t > 7.0:
					go("to_rail")
			"to_rail":
				ew.idle(guest, "", 0.0)
				if ew.walk(guest, rail, 1.0, dt, rail.y):
					p0 = Vector3(-46.0, plate.y + 9.0, -160.0)
					p1 = plate + Vector3(0.35, 0.0, 0.05)
					gull.visible = true
					go("photo")
			"photo":                                    # back to the table - in comes the gull
				ew.turn_to(guest, Vector3(0.2, 0, -1), dt)
				ew.idle(guest, "phone", 0.5)
				var k := clampf(st_t / 4.5, 0.0, 1.0)
				_fly(p0, p1, k, 1.5)
				gull.position.y = lerpf(p0.y, p1.y, 1.0 - pow(1.0 - k, 2.0))
				_wings(1.0, k < 0.2 or k > 0.85, dt)
				if k >= 1.0:
					go("hop")
			"hop":                                      # two small hops to the plate, grabs a fry
				_wings(0.0, false, dt)
				var k2 := clampf(st_t / 0.8, 0.0, 1.0)
				gull.position = p1.lerp(plate + Vector3(0.12, 0.01, 0.02), k2) + Vector3(0, 0.06 * absf(sin(k2 * TAU)), 0)
				gull.rotation.y = atan2(0.35, 0.05)
				if st_t > 1.3:
					if left > 0:
						left -= 1
					fry.visible = true
					p0 = gull.position
					p1 = Vector3(-18.0, plate.y + 8.0, -165.0)
					go("off")
			"off":
				var k3 := clampf(st_t / 3.5, 0.0, 1.0)
				_fly(p0, p1, k3, 1.0)
				gull.position.y = lerpf(p0.y, p1.y, k3 * k3)
				_wings(1.0, true, dt)
				if st_t > 1.8 and st_t - dt <= 1.8:
					guest.startle_until = guest.now_s() + 0.8
				if k3 >= 1.0:
					gull.visible = false
					fry.visible = false
					go("back")
			"back":
				ew.idle(guest, "", 0.0)
				if ew.walk(guest, seat, 1.0, dt, seat.y):
					go("look")
			"look":                                     # counts the fries - looks round - looks at the lake
				ew.turn_to(guest, plate - seat, dt)
				if st_t > 1.0 and st_t < 4.5:
					ew.idle(guest, "look", 0.5)
				else:
					ew.idle(guest, "bend", 0.3)
				if st_t > 6.0:
					if left <= 2:
						left = 10
					go("eat")

	func gull_near() -> bool:
		return st in ["photo", "hop", "off"] and gull.visible

	func info() -> Dictionary:
		var d := super.info()
		d["fries"] = left
		d["gull"] = gull_near()
		return d


# ---- 8 · the tent falls down again and again - in the end the camper sleeps in the car ---------------------------------------
class Zelt extends Vig:
	var camper
	var tent: Node3D
	var tc := Vector3.ZERO
	var car_p := Vector3.ZERO
	var falls := 0
	var lean := 0.0
	var hgt := 0.08

	func build() -> void:
		id = "zelt"
		tc = ew.Pg(-145.5, -69.5)
		c = tc
		car_p = ew.Pg(-141.6, -66.0)
		var b2 = Bib.new(ew.m, ew.s, vroot, ew.park.transform)
		b2.add("car", car_p, PI / 2.0, {"col": "6a6a6a", "style": "sedan"})
		b2.add("picnic_table", ew.Pg(-148.0, -64.8), 0.1, {"len": 1.6})
		b2.finish()
		tent = ew.node(vroot, tc, 0.3)
		nodes.append(tent)
		var dome := SphereMesh.new()
		dome.radius = 1.3
		dome.height = 1.25
		dome.is_hemisphere = true
		dome.radial_segments = 14 if not ew.lite else 8
		dome.rings = 5
		ew.part(tent, dome, Vector3.ZERO, Color(0.86, 0.45, 0.16), "tent", Vector3.ZERO, Vector3(1.0, 1.0, 1.15))
		ew.part(tent, ew.boxm(0.7, 0.8, 0.02), Vector3(0, 0.4, 1.32), Color(0.55, 0.28, 0.1), "tent")
		for k in range(2):                              # the two poles (arches)
			var tor := TorusMesh.new()
			tor.inner_radius = 1.27
			tor.outer_radius = 1.3
			tor.rings = 16 if not ew.lite else 8
			tor.ring_segments = 4
			ew.part(tent, tor, Vector3.ZERO, Color(0.2, 0.2, 0.22), "tent", Vector3(PI / 2.0, PI / 4.0 + k * PI / 2.0, 0), Vector3(1.0, 1.0, 0.97))
		var bag: Node3D = ew.node(vroot, ew.Pg(-147.4, -67.4))
		nodes.append(bag)
		ew.part(bag, ew.cylm(0.13, 0.13, 0.55, 8), Vector3(0, 0.13, 0), Color(0.2, 0.3, 0.2), "tent", Vector3(0, 0, PI / 2.0))
		camper = ew.actor("person", ew.Pg(-145.5, -67.6), tc, 1.2)
		actors.append(camper)
		go("flat")

	func when_ok() -> bool:
		var h: float = ew.hour()
		return h > 7.0 and h < 22.0

	func _tent(dt: float, want_h: float, want_lean: float, spd := 1.5) -> void:
		hgt = move_toward(hgt, want_h, dt * spd)
		lean = move_toward(lean, want_lean, dt * 0.5)
		var wob := 0.03 * sin(t * 13.0) * clampf(absf(want_h - hgt) * 4.0, 0.0, 1.0)
		tent.scale = Vector3(1.0 + (1.0 - hgt) * 0.25, maxf(0.06, hgt + wob), 1.0 + (1.0 - hgt) * 0.25)
		tent.rotation.z = lean
		tent.position = tc + Vector3(-lean * 0.6, 0, 0)

	func tick(dt: float) -> void:
		var front := tc + Vector3(0, 0, 2.0)
		match st:
			"flat":                                     # kneels at the flat tent, fiddles with the poles
				_tent(dt, 0.08, 0.0)
				ew.place(camper, ew.Pg(front.x, front.z))
				camper.visible = true
				camper.crouch = move_toward(float(camper.crouch), 1.0, dt * 2.0)
				camper.prone = 0.0
				ew.face(camper, tc - front)
				if st_t > 4.0:
					go("rise")
			"rise":
				camper.crouch = move_toward(float(camper.crouch), 0.0, dt * 1.5)
				_tent(dt, 1.0, 0.0, 0.8)
				if st_t > 3.0:
					go("pegs")
			"pegs":                                     # round to the back, bends to the pegs
				var back := tc + Vector3(-1.9, 0, -0.4)
				if ew.walk(camper, back, 1.0, dt):
					ew.turn_to(camper, tc - back, dt)
					ew.idle(camper, "bend", 0.5)
				_tent(dt, 1.0, 0.0)
				if st_t > 5.5:
					go("lean")
			"lean":                                     # ... and the tent quietly leans away from him
				if st_t < 1.2:
					ew.idle(camper, "bend", 0.3)
				else:
					ew.idle(camper, "", 0.0)
				_tent(dt, 0.95, 0.38 if falls % 2 == 0 else -0.38)
				if st_t > 2.2:
					go("fall")
			"fall":
				_tent(dt, 0.08, 0.0, 3.5)
				if st_t < 0.2:
					camper.startle_until = camper.now_s() + 1.5    # hands up
				if st_t > 2.5:
					falls += 1
					go("stare")
			"stare":
				ew.idle(camper, "look", 0.5)
				_tent(dt, 0.08, 0.0)
				if st_t > 2.5:
					if falls >= 3:
						go("to_car")
					else:
						go("back_front")
			"back_front":
				ew.idle(camper, "", 0.0)
				if ew.walk(camper, front, 1.0, dt):
					go("flat")
			"to_car":                                   # gives up: the car
				_tent(dt, 0.08, 0.0)
				if ew.walk(camper, car_p + Vector3(0.0, 0, 1.3), 0.9, dt):
					go("in_car")
			"in_car":                                   # sleeps in the car - only his feet stick out at the back
				ew.face(camper, Vector3(-1, 0, 0))
				ew.place(camper, car_p + Vector3(2.35, 0.72, 0.0), true)
				camper.crouch = 0.0
				camper.prone = 1.0
				camper.cur_speed = 0.0
				if st_t > 70.0:
					falls = 0
					camper.prone = 0.0
					ew.place(camper, car_p + Vector3(0.0, 0, 1.3))
					go("back_front")

	func info() -> Dictionary:
		var d := super.info()
		d["falls"] = falls
		d["tent_h"] = snappedf(hgt, 0.01)
		return d


# ---- 9 · the barbecue smokes more and more - the neighbour comes with a bucket ------------------------------------------------
class Grill extends Vig:
	var cook
	var nb
	var coal: MeshInstance3D
	var coal_m: StandardMaterial3D
	var heat := 15.0
	var smokes: Array = []
	var steam: CPUParticles3D
	var sausages: Array = []
	var bucket: Node3D
	var g := Vector3.ZERO
	var nb_home := Vector3.ZERO
	var level := 0

	func build() -> void:
		id = "grill"
		g = ew.Pg(-125.0, -64.0)
		c = g
		nb_home = ew.Pg(-133.5, -63.4)
		var gn: Node3D = ew.node(vroot, g)
		nodes.append(gn)
		coal_m = StandardMaterial3D.new()
		coal_m.albedo_color = Color(0.12, 0.1, 0.09)
		coal_m.emission_enabled = true
		coal_m.emission = Color(1.0, 0.35, 0.1)
		coal_m.emission_energy_multiplier = 0.0
		coal = ew.m.add_mesh(gn, ew.boxm(0.82, 0.03, 0.52), Vector3(0, 0.9, 0), coal_m, 15.0)
		for i in range(4):
			sausages.append(ew.part(gn, ew.cylm(0.018, 0.018, 0.16, 6), Vector3(-0.24 + i * 0.16, 0.965, 0.05), Color(0.75, 0.45, 0.35), 60.0, Vector3(PI / 2.0, 0, 0)))
		for i in range(1 if ew.lite else 3):
			var p := CPUParticles3D.new()
			p.amount = [10, 18, 28][i]
			p.lifetime = 6.0
			p.position = g + Vector3(0, 1.0, 0)
			p.direction = Vector3(0, 1, 0)
			p.spread = 18.0
			p.initial_velocity_min = 0.35
			p.initial_velocity_max = 0.7
			p.gravity = Vector3(0.2 + float(ew.m.wind) * 0.02, 0.06, 0.05)
			var cv := Curve.new()
			cv.add_point(Vector2(0, 0.25))
			cv.add_point(Vector2(1, 2.4))
			p.scale_amount_curve = cv
			var sm: SphereMesh = ew.sphm(0.35, -1.0, 6)
			var mt := StandardMaterial3D.new()
			mt.albedo_color = Color(0.55 - i * 0.1, 0.55 - i * 0.1, 0.56 - i * 0.1, 0.35 + i * 0.1)
			mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			sm.material = mt
			p.mesh = sm
			p.emitting = false
			vroot.add_child(p)
			smokes.append(p)
			nodes.append(p)
		steam = CPUParticles3D.new()
		steam.amount = 24
		steam.lifetime = 2.5
		steam.one_shot = true
		steam.explosiveness = 0.85
		steam.position = g + Vector3(0, 1.0, 0)
		steam.direction = Vector3(0, 1, 0)
		steam.spread = 35.0
		steam.initial_velocity_min = 1.0
		steam.initial_velocity_max = 2.2
		steam.gravity = Vector3(0, 0.3, 0)
		var sm2: SphereMesh = ew.sphm(0.3, -1.0, 6)
		var mt2 := StandardMaterial3D.new()
		mt2.albedo_color = Color(0.95, 0.95, 0.97, 0.45)
		mt2.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mt2.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		sm2.material = mt2
		steam.mesh = sm2
		steam.emitting = false
		vroot.add_child(steam)
		cook = ew.actor("person", g + Vector3(0, 0, 0.95), g, 1.2)
		actors.append(cook)
		nb = ew.actor("person", nb_home, g, 1.2)
		actors.append(nb)
		var arm: Node3D = nb.arms[1][2] if nb.arms.size() > 1 and nb.arms[1].size() > 2 else nb
		bucket = ew.node(arm, Vector3(0, -0.52, 0))
		ew.part(bucket, ew.cylm(0.15, 0.12, 0.26, 10), Vector3.ZERO, Color(0.35, 0.5, 0.7), "caravan")
		ew.part(bucket, ew.cylm(0.135, 0.135, 0.01, 10), Vector3(0, 0.1, 0), Color(0.3, 0.45, 0.6), "pond")
		go("light")

	func when_ok() -> bool:
		var h: float = ew.hour()
		return h > 10.0 and h < 22.5 and not ew.rain()

	func on_hide() -> void:
		for p in smokes:
			p.emitting = false

	func _heat(v: float) -> void:
		heat = v
		# glowing charcoal under a layer of ash: 300–600 °C at the surface (thermography of BBQ charcoal); a cooled grill ~40 °C
		ew.set_heat(coal, snappedf(v, 10.0))
		coal_m.emission_energy_multiplier = clampf((v - 150.0) / 300.0, 0.0, 1.0) * (1.5 if ew.dark() else 0.6)

	func _smoke(lv: int) -> void:
		level = lv
		for i in range(smokes.size()):
			var on := lv > i if smokes.size() > 1 else lv > 0
			if smokes[i].emitting != on:
				smokes[i].emitting = on

	func tick(dt: float) -> void:
		var front := g + Vector3(0, 0, 0.95)
		ew.place(cook, ew.Pg(front.x, front.z))
		match st:
			"light":                                    # new sausages, lights the coal
				for sg in sausages:
					(sg as MeshInstance3D).material_override = ew.m.mat(Color(0.75, 0.45, 0.35))
				ew.face(cook, g - front)
				ew.idle(cook, "bend", 0.5)
				_heat(minf(heat + dt * 40.0, 350.0))
				_smoke(1)
				if st_t > 8.0:
					go("grill")
			"grill":
				_heat(minf(heat + dt * 10.0, 450.0))
				var k := snappedf(clampf(st_t / 40.0, 0.0, 1.0), 0.125)
				for sg in sausages:
					(sg as MeshInstance3D).material_override = ew.m.mat(Color(0.75, 0.45, 0.35).lerp(Color(0.12, 0.08, 0.06), k))
				_smoke(1 if st_t < 14.0 else (2 if st_t < 26.0 else 3))
				if st_t > 26.0 and fmod(st_t, 2.0) < dt:
					cook.play_emote("throw", 0.6)            # fans the smoke away
				elif fmod(st_t, 9.0) < 1.5:
					ew.idle(cook, "bend", 0.3)               # turns the sausages (and coughs)
				if st_t > 30.0:
					go("bucket")
			"bucket":                                   # the neighbour comes over with a bucket of water
				_smoke(3)
				var to := g + Vector3(-1.05, 0, 0.35)
				if ew.walk(nb, to, 1.25, dt):
					ew.turn_to(nb, g - to, dt)
					if st_t > 1.0:
						nb.play_emote("throw", 0.7)
						go("splash")
			"splash":
				if st_t > 0.35 and not bucket.has_meta("empty"):
					bucket.set_meta("empty", true)
					steam.restart()
					steam.emitting = true
					_smoke(0)
					cook.startle_until = cook.now_s() + 1.4
				if bucket.has_meta("empty"):
					_heat(maxf(heat - dt * 220.0, 45.0))
				if st_t > 2.5:
					ew.idle(cook, "look", 2.0)
					ew.idle(nb, "look", 2.0)
				if st_t > 5.0:
					go("home")
			"home":
				ew.idle(nb, "", 0.0)
				_heat(maxf(heat - dt * 3.0, 35.0))
				if ew.walk(nb, nb_home, 1.1, dt):
					ew.turn_to(nb, g - nb_home, dt)
					bucket.remove_meta("empty")
				if st_t > 40.0:
					go("light")

	func smoky() -> bool:
		return level >= 2 or st in ["bucket", "splash"]

	func info() -> Dictionary:
		var d := super.info()
		d["smoke"] = level
		d["coal_c"] = roundi(heat)
		return d


# ---- 10 · the angler on the jetty catches only a boot - once a day a giant fish (and he falls in) -----------------------------
class Angler extends Vig:
	var man
	var rod: Node3D
	var rod_seg: Array = []
	var line: Node3D
	var bob: Node3D
	var catch_boot: Node3D
	var fish: Node3D
	var pile: Array = []
	var boots := 0
	var stand := Vector3.ZERO
	var deck := 0.8
	var bob_p := Vector3.ZERO
	var pitch := 0.55
	var bend := 0.0
	var fish_hour := 12.0
	var fish_day := ""
	var force := false
	var wait_s := 20.0
	var splash: CPUParticles3D

	func build() -> void:
		id = "angler"
		stand = Vector3(80.25, deck, -197.6)
		c = stand
		bob_p = Vector3(80.4, WATER_Y + 0.02, -202.6)
		fish_hour = 9.0 + float(ew.day_seed % 900) / 100.0           # once a day, between 9 and 18 o'clock (seeded by the date)
		man = ew.actor("person", stand, stand + Vector3(0, 0, -2), 1.1)
		man.set_meta("ew_y", ew.W(stand).y)
		actors.append(man)
		rod = ew.node(vroot, Vector3.ZERO)
		nodes.append(rod)
		var prev: Node3D = rod
		for i in range(4):                              # the rod in four pieces: it can bend
			var sg: Node3D = ew.node(prev, Vector3(0, 0, -0.65) if i > 0 else Vector3.ZERO)
			ew.part(sg, ew.boxm(0.025 - i * 0.004, 0.025 - i * 0.004, 0.66), Vector3(0, 0, -0.33), Color(0.15, 0.15, 0.16), "stone")
			rod_seg.append(sg)
			prev = sg
		line = ew.node(vroot, Vector3.ZERO)
		nodes.append(line)
		ew.light_part(line, ew.boxm(0.004, 0.004, 1.0), Vector3(0, 0, -0.5), ew.m.mat(Color(0.85, 0.85, 0.85)))
		bob = ew.node(vroot, bob_p)
		nodes.append(bob)
		ew.part(bob, ew.sphm(0.03, -1.0, 8), Vector3.ZERO, Color(0.9, 0.15, 0.1), "pond")
		ew.part(bob, ew.cylm(0.004, 0.004, 0.08, 4), Vector3(0, 0.05, 0), Color(0.95, 0.95, 0.95), "pond")
		catch_boot = ew.node(vroot, Vector3.ZERO)
		nodes.append(catch_boot)
		_boot(catch_boot, Vector3.ZERO, Vector3(0.3, 0, 0))
		catch_boot.visible = false
		for i in range(4):
			var bp: Node3D = ew.node(vroot, Vector3(79.2 - 0.22 * (i % 2), deck, -197.0 + 0.25 * (i / 2)), i * 1.3)
			_boot(bp, Vector3.ZERO, Vector3(0, 0, PI / 2.0 if i % 2 == 0 else 0.0))
			bp.visible = false
			pile.append(bp)
			nodes.append(bp)
		fish = ew.node(vroot, Vector3.ZERO)
		nodes.append(fish)
		# a big pike / catfish: body = water temperature (fish are ectotherms - the thermal camera hardly sees them)
		ew.part(fish, ew.sphm(0.16, 0.3), Vector3.ZERO, Color(0.45, 0.48, 0.4), "pond", Vector3.ZERO, Vector3(1.0, 1.0, 4.0))
		ew.part(fish, ew.boxm(0.03, 0.32, 0.22), Vector3(0, 0, 0.7), Color(0.4, 0.42, 0.35), "pond")
		ew.part(fish, ew.boxm(0.02, 0.15, 0.25), Vector3(0, 0.16, 0.05), Color(0.38, 0.4, 0.33), "pond")
		fish.visible = false
		splash = CPUParticles3D.new()
		splash.amount = 18 if not ew.lite else 8
		splash.lifetime = 1.2
		splash.one_shot = true
		splash.explosiveness = 0.9
		splash.direction = Vector3(0, 1, 0)
		splash.spread = 40.0
		splash.initial_velocity_min = 1.5
		splash.initial_velocity_max = 3.5
		splash.gravity = Vector3(0, -9.8, 0)
		var smm: SphereMesh = ew.sphm(0.05, -1.0, 4)
		var mt := StandardMaterial3D.new()
		mt.albedo_color = Color(0.85, 0.92, 1.0, 0.6)
		mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		smm.material = mt
		splash.mesh = smm
		splash.emitting = false
		vroot.add_child(splash)
		go("wait")

	func _boot(n: Node3D, p: Vector3, r: Vector3) -> void:
		var b: Node3D = ew.node(n, p)
		b.rotation = r
		ew.part(b, ew.cylm(0.06, 0.07, 0.28, 8), Vector3(0, 0.14, 0), Color(0.18, 0.3, 0.18), "pond")
		ew.part(b, ew.boxm(0.12, 0.08, 0.24), Vector3(0, 0.04, -0.06), Color(0.18, 0.3, 0.18), "pond")

	func when_ok() -> bool:
		var h: float = ew.hour()
		return h > 6.0 and h < 21.0

	func fish_now() -> bool:
		return st in ["fight", "jump", "fall", "swim", "climb"]

	func _rod(dt: float, man_p: Vector3) -> Vector3:
		"""rod in the hands; returns the tip (park)"""
		var hb: Basis = ew.park.transform.basis.inverse() * (man as Node3D).global_transform.basis
		var yaw := hb.get_euler().y
		rod.position = man_p + Basis(Vector3.UP, yaw) * Vector3(0.22, 1.05, -0.3)
		rod.rotation = Vector3(pitch, yaw, 0)
		for i in range(1, rod_seg.size()):
			(rod_seg[i] as Node3D).rotation.x = -bend * 0.3 * i
		var tipn: Node3D = rod_seg[rod_seg.size() - 1]
		return ew.toP(tipn.global_transform * Vector3(0, 0, -0.66))

	func _line(a: Vector3, b: Vector3) -> void:
		var d := b - a
		var L := d.length()
		line.position = a
		if L > 0.01:
			var up := Vector3.UP if absf(d.normalized().y) < 0.95 else Vector3.FORWARD
			line.basis = Basis.looking_at(d / L, up)
			line.scale = Vector3(1, 1, L)

	func tick(dt: float) -> void:
		var mp: Vector3 = ew.ppos(man)
		mp.y = deck
		var tip := _rod(dt, mp)
		var hook := bob_p
		ew.idle(man, "", 0.0)
		match st:
			"wait":                                     # the float bobs gently; he waits
				ew.place(man, stand, true)
				ew.face(man, Vector3(0, 0, -1))
				pitch = lerpf(pitch, 0.55, dt * 2.0)
				bend = lerpf(bend, 0.0, dt * 3.0)
				bob.position = bob_p + Vector3(0, 0.008 * sin(t * 2.3), 0)
				var due: bool = force or (ew.hour() >= fish_hour and fish_day != ew.today)
				if st_t > wait_s:
					if due:
						force = false
						fish_day = ew.today
						go("fight")
					else:
						go("bite")
			"bite":                                     # it bites - dip, dip, under
				bob.position = bob_p + Vector3(0, -0.04 * absf(sin(st_t * 9.0)) - (0.08 if st_t > 1.2 else 0.0), 0)
				if st_t > 1.6:
					go("reel")
			"reel":                                     # up with the rod - a boot hangs on the hook
				pitch = lerpf(pitch, 1.15, dt * 2.5)
				bend = 0.25
				var k := clampf(st_t / 2.5, 0.0, 1.0)
				hook = bob_p.lerp(tip + Vector3(0, -0.9, 0), k)
				catch_boot.visible = k > 0.15
				catch_boot.position = hook + Vector3(0, -0.28, 0)
				bob.position = hook
				if k >= 1.0:
					go("look")
			"look":                                     # looks at it ... and puts it on the pile
				hook = tip + Vector3(0, -0.9, 0)
				catch_boot.position = hook + Vector3(0, -0.28, 0) + Vector3(0.02 * sin(t * 3.0), 0, 0)
				bob.position = hook
				ew.idle(man, "look", 0.5)
				if st_t > 2.5:
					catch_boot.visible = false
					boots = (boots + 1) % 5
					for i in range(pile.size()):
						pile[i].visible = i < boots
					wait_s = randf_range(18.0, 35.0)
					go("cast")
			"cast":
				ew.idle(man, "", 0.0)
				if st_t < 0.1:
					man.play_emote("throw", 0.6)
				pitch = lerpf(pitch, 0.55, dt * 3.0)
				bend = 0.0
				var k2 := clampf(st_t / 1.2, 0.0, 1.0)
				hook = tip.lerp(bob_p, k2) + Vector3(0, 1.2 * sin(k2 * PI), 0)
				bob.position = hook
				if k2 >= 1.0:
					go("wait")
			"fight":                                    # something BIG: the rod bends, he is pulled step by step to the edge
				bend = 0.9 + 0.15 * sin(st_t * 7.0)
				pitch = 0.9 + 0.1 * sin(st_t * 5.0)
				bob.position = bob_p + Vector3(0.3 * sin(st_t * 2.0), -0.3, -0.2 * st_t)
				man.crouch = 0.35
				var edge := Vector3(stand.x, deck, -198.85)
				var step: float = 0.18 * dt if fmod(st_t, 1.5) < 0.6 else 0.0
				var p: Vector3 = ew.ppos(man)
				ew.place(man, Vector3(p.x, deck, maxf(edge.z, p.z - step)), true)
				hook = bob.position
				if st_t > 7.0:
					fish.visible = true
					go("jump")
			"jump":                                     # the fish jumps out of the water
				var k3 := clampf(st_t / 1.1, 0.0, 1.0)
				fish.position = Vector3(80.8, WATER_Y - 0.2 + 1.6 * sin(k3 * PI), -202.0 - k3 * 1.5)
				fish.rotation = Vector3(-1.2 + 2.4 * k3, 0.3, 0.4 * sin(k3 * 6.0))
				hook = fish.position + Vector3(0, 0, -0.5)
				bob.position = hook
				if k3 >= 1.0:
					fish.visible = false
					splash.position = fish.position
					splash.restart()
					splash.emitting = true
					man.startle_until = man.now_s() + 1.0
					go("fall")
			"fall":                                     # ... and pulls him in
				var k4 := clampf(st_t / 0.9, 0.0, 1.0)
				man.crouch = 0.0
				var p2 := Vector3(stand.x, lerpf(deck, WATER_Y - 1.15, k4 * k4), lerpf(-198.85, -200.0, k4))
				ew.place(man, p2, true)
				pitch = lerpf(pitch, 1.4, dt * 3.0)
				if k4 >= 1.0:
					splash.position = Vector3(stand.x, WATER_Y, -200.0)
					splash.restart()
					splash.emitting = true
					rod.visible = false
					line.visible = false
					go("swim")
			"swim":                                     # treads water, swims to the side of the jetty
				var p3: Vector3 = ew.ppos(man)
				var to := Vector3(81.7, 0, -197.5)
				ew.walk(man, to, 0.5, dt, WATER_Y - 1.15 + 0.04 * sin(t * 3.0))
				if st_t > 7.0:
					go("climb")
			"climb":
				var k5 := clampf(st_t / 2.0, 0.0, 1.0)
				man.crouch = 0.6 * sin(k5 * PI)
				ew.face(man, Vector3(-1, 0, 0))
				ew.place(man, Vector3(lerpf(81.7, 80.6, k5), lerpf(WATER_Y - 1.15, deck, k5), -197.5), true)
				if k5 >= 1.0:
					go("drip")
			"drip":                                     # stands there dripping, looks at the water
				man.crouch = 0.0
				ew.idle(man, "look", 0.5)
				if st_t > 6.0:
					rod.visible = true
					line.visible = true
					wait_s = 30.0
					go("cast")
		if st in ["wait", "bite"]:
			hook = bob.position
		_line(tip, hook + Vector3(0, 0.05, 0))

	func info() -> Dictionary:
		var d := super.info()
		d["boots"] = boots
		d["fish_hour"] = snappedf(fish_hour, 0.01)
		d["fish_today"] = fish_day == ew.today
		d["fish_now"] = fish_now()
		return d


# ---- 11 · sleepwalker in pyjamas at night: stops in front of MoveEye and waves ------------------------------------------------
class Schlafwandler extends Vig:
	var man
	var home := Vector3.ZERO
	var goal := Vector3.ZERO
	var way: Array = []
	var wi := 0

	func build() -> void:
		id = "schlafwandler"
		home = Vector3(-101.5, 0, -61.6)
		c = ew.Pg(-100.0, -58.0)
		always = true
		man = ew.actor("person", ew.Pg(home.x, home.z), ew.Pg(-100.0, -58.0), 0.55, Color(0.62, 0.72, 0.88))
		if man.fig != null:
			man.fig.recolour(Color(0.62, 0.72, 0.88), Color(0.58, 0.68, 0.84))     # light blue pyjamas
		man.carry = true                                # arms straight ahead
		actors.append(man)
		man.visible = false
		go("sleep")

	func when_ok() -> bool:
		return ew.dark()

	func where() -> Vector3:
		return (man as Node3D).global_position if is_instance_valid(man) else ew.W(c)

	func _plan() -> void:
		"""to MoveEye if it is not too far (along the path of the tent meadow), else to the lantern at the sanitary building"""
		var hp: Vector3 = ew.head_pos()
		var cam: Camera3D = ew.m.cams[0]
		var fw := -cam.global_transform.basis.z
		fw.y = 0
		fw = fw.normalized() if fw.length() > 0.01 else Vector3(0, 0, -1)
		var front: Vector3 = ew.toP(hp + fw * 5.0)          # 5 m: whole in the picture of the head camera (photo)
		way = [Vector3(-100.5, 0, -58.2)]
		if Vector2(front.x + 100.0, front.z + 58.0).length() < 95.0:
			way.append(Vector3(front.x, 0, -58.2))
			goal = Vector3(front.x, 0, front.z)
		else:
			goal = Vector3(-90.0, 0, -59.0)
		way.append(goal)
		wi = 0

	func waving() -> bool:
		return st == "wave"

	func tick(dt: float) -> void:
		man.carry = st in ["walk", "back"]
		match st:
			"sleep":
				man.visible = false
				ew.place(man, ew.Pg(home.x, home.z))
				if st_t > 25.0:
					_plan()
					man.visible = shown
					go("walk")
			"walk":
				man.visible = shown
				man.body_root.rotation.z = 0.04 * sin(t * 1.3)
				if ew.walk(man, way[wi], 0.55, dt, null, 1.5):
					wi += 1
					if wi >= way.size():
						go("turn")
			"turn":
				var hp: Vector3 = ew.toP(ew.head_pos())
				if ew.turn_to(man, hp - ew.ppos(man), dt, 1.2) or st_t > 3.0:
					go("wave")
			"wave":                                     # stands still, waves at MoveEye (eyes closed - you do not see that)
				man.play_emote("wave", 0.3)
				ew.stop(man, dt)
				if st_t > 7.0:
					go("stand")
			"stand":
				if st_t > 2.5:
					way = [Vector3(goal.x, 0, -58.2), Vector3(-100.5, 0, -58.2), home]
					wi = 0
					go("back")
			"back":
				if ew.walk(man, way[wi], 0.55, dt, null, 1.5):
					wi += 1
					if wi >= way.size():
						man.visible = false
						go("sleep")

	func info() -> Dictionary:
		var d := super.info()
		d["goal"] = [snappedf(goal.x, 0.1), snappedf(goal.z, 0.1)]
		var p: Vector3 = ew.ppos(man)
		d["at"] = [snappedf(p.x, 0.1), snappedf(p.z, 0.1)]
		d["to_moveeye_m"] = snappedf((man as Node3D).global_position.distance_to(ew.head_pos()), 0.1)
		return d


# ---- 12 · children play hide-and-seek - and MoveEye can play along and find them ----------------------------------------------
class Verstecken extends Vig:
	var kids: Array = []
	var hides: Array = []           # park points behind hedges, motorhomes, cars
	var base := Vector3.ZERO
	var seeker := 0
	var order: Array = []
	var found: Array = []
	var spot_of: Array = []
	# the round with MoveEye
	var mw := false
	var mw_hides: Array = []        # park points near MoveEye
	var mw_found: Array = []
	var mw_t := 0.0
	var mw_next: Array = []
	var result := {}

	func build() -> void:
		id = "verstecken"
		c = ew.Pg(-128.0, -32.0)
		base = Vector3(-134.0, 0, -38.6)
		hides = [Vector3(-133.4, 0, -34.0), Vector3(-127.5, 0, -27.6), Vector3(-121.3, 0, -33.8), Vector3(-126.0, 0, -23.2), Vector3(-138.6, 0, -34.2)]
		var jackets := [Color(0.9, 0.3, 0.3), Color(0.25, 0.55, 0.9), Color(0.95, 0.8, 0.2), Color(0.3, 0.7, 0.35)]
		for i in range(4):
			var k = ew.actor("child", ew.Pg(base.x + i * 0.8, base.z + 0.8), ew.Pg(base.x, base.z - 2.0), 2.2, jackets[i])
			kids.append(k)
			actors.append(k)
			found.append(false)
			spot_of.append(Vector3.ZERO)
			mw_found.append(false)
			mw_next.append(0.0)
		go("count")

	func when_ok() -> bool:
		var h: float = ew.hour()
		return (h > 8.5 and h < 20.0 and not ew.rain()) or mw

	func where() -> Vector3:
		if mw and not kids.is_empty():
			return (kids[0] as Node3D).global_position
		return ew.W(c)

	# ---- normal play: one counts at the hedge, the others hide, the seeker finds them one by one ----
	func tick(dt: float) -> void:
		if mw:
			_mw_tick(dt)
			return
		var sk = kids[seeker]
		match st:
			"count":
				if st_t < dt * 1.5:
					var hs := hides.duplicate()
					hs.shuffle()
					for i in range(kids.size()):
						spot_of[i] = hs[i % hs.size()]
						found[i] = i == seeker
				ew.place(sk, ew.Pg(base.x, base.z))
				ew.face(sk, Vector3(-1, 0, 0))
				ew.idle(sk, "bend", 0.5)                 # face in the arms at the hedge
				for i in range(kids.size()):
					if i == seeker:
						continue
					var k = kids[i]
					if ew.walk(k, spot_of[i], 2.6, dt):
						k.crouch = move_toward(float(k.crouch), 1.0, dt * 3.0)
				if st_t > 12.0:
					order = []
					for i in range(kids.size()):
						if i != seeker:
							order.append(i)
					order.shuffle()
					ew.idle(sk, "", 0.0)
					go("seek")
			"seek":
				if order.is_empty():
					go("play")
					return
				var who: int = order[0]
				var at: Vector3 = spot_of[who] + (base - spot_of[who]).normalized() * 0.9
				if fmod(st_t, 6.0) < 1.2:
					ew.idle(sk, "look", 0.5)
					ew.stop(sk, dt)
				elif ew.walk(sk, at, 1.3, dt):
					found[who] = true
					kids[who].crouch = 0.0
					kids[who].play_emote("goal", 1.2)
					sk.play_emote("goal", 1.2)
					order.pop_front()
					st_t = 0.0
				for i in range(kids.size()):
					if found[i] and i != seeker:
						var k2 = kids[i]
						if k2.emote_until < k2.now_s():
							if ew.walk(k2, base + Vector3(0.7 * i, 0, 0.6), 1.8, dt):
								ew.face(k2, Vector3(1, 0, 0))
			"play":                                     # a short chase round the hedge, then the next one counts
				for i in range(kids.size()):
					var k3 = kids[i]
					var p := base + Vector3(2.0 + 2.5 * sin(t * 0.8 + i * 1.6), 0, 2.0 + 1.5 * cos(t * 0.8 + i * 1.6))
					ew.walk(k3, p, 2.4, dt)
				if st_t > 8.0:
					seeker = (seeker + 1) % kids.size()
					go("count")

	# ---- with MoveEye: the children hide near MoveEye; MoveEye has to report them ----
	func start_mw() -> Dictionary:
		var hp: Vector3 = ew.head_pos()
		var cam: Camera3D = ew.m.cams[0]
		var fw := -cam.global_transform.basis.z
		var cand: Array = []
		for w in ew.s.data.get("fp_verstecke", []):
			var wp: Vector3 = w
			var d := Vector2(wp.x - hp.x, wp.z - hp.z).length()
			if d > 7.0 and d < 32.0:
				var away := Vector3(wp.x - hp.x, 0, wp.z - hp.z).normalized()
				var ang := absf(Vector2(fw.x, fw.z).angle_to(Vector2(away.x, away.z)))
				cand.append([d + (0.0 if ang < 1.1 else 40.0), ew.toP(wp + away * 1.0)])   # behind the thing; in front of MoveEye first
		cand.sort_custom(func(a, b): return a[0] < b[0])
		if cand.is_empty():                                    # no hiding things here: behind MoveEye, at the sides
			for a in [140.0, -140.0, 100.0, -100.0]:
				cand.append([12.0, ew.toP(ew.m.pos_of(a, 12.0))])
		mw_hides = []
		for i in range(kids.size()):
			mw_hides.append(cand[i % cand.size()][1])
		var start: Vector3 = ew.toP(hp + Vector3(0, 0, 0)) + Vector3(0, 0, 0)
		var road = ew.s.data.get("road_line", null)
		if road is PackedVector2Array and (road as PackedVector2Array).size() > 0:
			var best := Vector2(9999, 9999)
			for v in road:
				var vv: Vector2 = v
				var dd := vv.length()
				if dd > 28.0 and dd < 45.0 and dd < best.length():
					best = vv
			if best.x < 9000.0:
				start = ew.toP(Vector3(best.x, 0, best.y))
		for i in range(kids.size()):
			var k = kids[i]
			k.crouch = 0.0
			k.visible = true
			ew.place(k, ew.Pg(start.x + i * 0.9, start.z + 0.5))
			mw_found[i] = false
			mw_next[i] = randf_range(12.0, 24.0)
		mw = true
		mw_t = 0.0
		result = {"state": "verstecken", "found": 0, "total": kids.size(), "moveeye": ew.m.now() - float(ew.m.mw_det_t) < 3.0}
		go("mw_hide")
		return result

	func stop_mw() -> void:
		mw = false
		go("count")
		for i in range(kids.size()):
			ew.place(kids[i], ew.Pg(base.x + i * 0.8, base.z + 0.8))
			kids[i].crouch = 0.0

	func _rect(k) -> Rect2:
		"""where a child is in the picture of the head camera (0..1), or empty"""
		var cam: Camera3D = ew.m.cams[0]
		var p: Vector3 = (k as Node3D).global_position
		var h := 1.25 * (1.0 - 0.45 * float(k.crouch))
		if cam.is_position_behind(p) or cam.global_position.distance_to(p) > 45.0:
			return Rect2()
		var vs := Vector2(ew.m.CAM_W[0], ew.m.CAM_H[0])
		var a := cam.unproject_position(p) / vs
		var b := cam.unproject_position(p + Vector3(0, h, 0)) / vs
		var w := absf(a.y - b.y) * 0.4
		var r := Rect2(minf(a.x, b.x) - w / 2.0, minf(a.y, b.y), w + absf(a.x - b.x), absf(a.y - b.y))
		if r.end.x < 0.0 or r.position.x > 1.0 or r.end.y < 0.0 or r.position.y > 1.0:
			return Rect2()
		if not ew.ent() or not ew.ent()._los(cam.global_position, p + Vector3(0, h * 0.8, 0)):
			return Rect2()
		return r

	func _reported(k) -> bool:
		if ew.m.now() - float(ew.m.mw_det_t) > 1.5:
			return false
		var r := _rect(k)
		if r.size.x <= 0.0:
			return false
		var bx = ew.m.mw_det.get("boxes", null)
		if typeof(bx) == TYPE_ARRAY:
			for b in bx:
				if typeof(b) == TYPE_ARRAY and (b as Array).size() == 4:
					var br := Rect2(float(b[0]), float(b[1]), float(b[2]), float(b[3]))
					if br.grow(0.02).intersects(r):
						return true
			return false
		return int(ew.m.mw_det.get("persons", 0)) > 0          # an older MoveEye without boxes: any person


	func _mw_tick(dt: float) -> void:
		mw_t += dt
		var hp: Vector3 = ew.toP(ew.head_pos())
		var side := Vector3(2.2, 0, 1.0)
		var n_found := 0
		for i in range(kids.size()):
			var k = kids[i]
			var hide: Vector3 = mw_hides[i]
			if mw_found[i]:
				n_found += 1
				if k.emote_until < k.now_s():
					if ew.walk(k, hp + side + Vector3(0.8 * i, 0, 0), 1.6, dt):
						ew.turn_to(k, hp - ew.ppos(k), dt)
				continue
			match st:
				"mw_hide":                               # run to the hiding places (MoveEye «counts»)
					if ew.walk(k, hide, 2.8, dt):
						k.crouch = move_toward(float(k.crouch), 1.0, dt * 3.0)
						ew.turn_to(k, hp - hide, dt)
				"mw_seek":
					mw_next[i] -= dt
					var peek: bool = mw_next[i] < 0.0 and mw_next[i] > -4.0      # stands up for a moment and looks
					if mw_next[i] < -4.0:
						mw_next[i] = randf_range(10.0, 25.0)
					if ew.walk(k, hide, 2.8, dt):
						k.crouch = move_toward(float(k.crouch), 0.0 if peek else 1.0, dt * 3.0)
						ew.turn_to(k, hp - hide, dt)
					if _reported(k):
						mw_found[i] = true
						k.crouch = 0.0
						k.play_emote("goal", 1.5)
						n_found += 1
		result["found"] = n_found
		result["moveeye"] = ew.m.now() - float(ew.m.mw_det_t) < 3.0
		result["t"] = snappedf(mw_t, 0.1)
		match st:
			"mw_hide":
				result["state"] = "verstecken"
				if mw_t > 15.0:
					go("mw_seek")
			"mw_seek":
				result["state"] = "suchen"
				if n_found >= kids.size():
					result["state"] = "alle gefunden"
					var e = ew.ent()
					if e != null:
						e.mark_found("see.verstecken_moveeye", "api")
					go("mw_end")
				elif mw_t > 15.0 + 180.0:
					result["state"] = "Zeit um"
					go("mw_end")
			"mw_end":                                   # the ones not found come out and cheer
				for i in range(kids.size()):
					if not mw_found[i]:
						kids[i].crouch = 0.0
						if st_t < dt * 1.5:
							kids[i].play_emote("goal", 2.0)
				if st_t > 12.0:
					stop_mw()

	func info() -> Dictionary:
		var d := super.info()
		d["moveeye_round"] = mw
		d["result"] = result
		return d


# ---- 13 · yoga on the beach at sunrise - one of them does it the wrong way round ----------------------------------------------
class Yoga extends Vig:
	var people: Array = []          # [actor, delay, facing]
	const POSES := [[0.0, "stand"], [4.0, "up"], [7.5, "fold"], [11.5, "lie"], [17.0, "crouch"], [20.0, "stand"]]
	const PERIOD := 26.0

	func build() -> void:
		id = "yoga"
		c = ew.Pg(-118.0, -155.0)
		var mats := [Color(0.5, 0.3, 0.6), Color(0.2, 0.6, 0.6), Color(0.85, 0.45, 0.3), Color(0.3, 0.5, 0.8), Color(0.6, 0.7, 0.3), Color(0.8, 0.3, 0.45)]
		var spots := [[-118.0, -158.6, 1.0, 0.0], [-120.2, -154.2, -1.0, 0.0], [-118.0, -154.2, -1.0, 0.0], [-115.8, -154.2, -1.0, 0.0],
				[-119.1, -151.6, -1.0, 0.0], [-116.9, -151.6, 1.0, 1.4]]      # x, z, facing (-1 = to the lake), delay; the last one: wrong way round
		for i in range(spots.size()):
			var sp: Array = spots[i]
			var p: Vector3 = ew.Pg(float(sp[0]), float(sp[1]))
			var fz := float(sp[2])
			var mn: Node3D = ew.node(vroot, p + Vector3(0, 0.006, 0))
			ew.part(mn, ew.boxm(0.62, 0.008, 1.85), Vector3(0, 0, fz * 0.35), mats[i % mats.size()], "tent")
			nodes.append(mn)
			var jk: Color = [Color(0.95, 0.95, 0.95), Color(0.2, 0.2, 0.25), Color(0.5, 0.6, 0.75), Color(0.75, 0.4, 0.45)][i % 4]
			var a = ew.actor("person", p, p + Vector3(0, 0, fz * 2.0), 1.0, jk)
			actors.append(a)
			people.append([a, float(sp[3]), fz])

	func when_ok() -> bool:
		var h: float = ew.hour()
		return h >= 5.0 and h < 10.0 and not ew.rain()

	func pose_at(tt: float) -> String:
		var k := fposmod(tt, PERIOD)
		var p := "stand"
		for q in POSES:
			if k >= float(q[0]):
				p = str(q[1])
		return p

	func tick(dt: float) -> void:
		for e in people:
			var a = e[0]
			var ps := pose_at(t - float(e[1]))
			a.cur_speed = 0.0
			ew.face(a, Vector3(0, 0, float(e[2])))
			var want_c := 0.0
			var want_p := 0.0
			match ps:
				"up":                                   # arms up (salute to the sun)
					a.startle_until = a.now_s() + 0.3
					ew.idle(a, "", 0.0)
				"fold":
					ew.idle(a, "bend", 0.3)
				"lie":
					want_p = 1.0
					ew.idle(a, "", 0.0)
				"crouch":
					want_c = 1.0
					ew.idle(a, "", 0.0)
				_:
					ew.idle(a, "", 0.0)
			a.crouch = move_toward(float(a.crouch), want_c if float(a.prone) < 0.3 else 1.0, dt * 1.5)
			a.prone = move_toward(float(a.prone), want_p, dt * 0.8)

	func info() -> Dictionary:
		var d := super.info()
		d["pose"] = pose_at(t)
		d["late_one"] = pose_at(t - 1.4)
		return d


# =============================================================================================================================
# ---- the discovery book (entdecken.gd) -----------------------------------------------------------------------------------------
# =============================================================================================================================
func _reg(e, id: String, title: String, short: String, hint: String, icon: String, kind: String, pos: Vector3, size: Vector3, radius: float,
		when = "any", extra := {}) -> void:
	var inf := {"scene": "ferienpark", "title": T.t(title), "short_text": T.t(short), "hint": hint, "icon": icon, "kind": kind,
			"position": pos, "size": size, "radius": radius, "when": when}
	inf.merge(extra, true)
	e.register(id, inf)


func _register() -> void:
	var e = ent()
	if e == null:
		return
	var V: Dictionary = by_id
	# A · Tiere
	_reg(e, "see.katze_mausloecher", "Katze vor den Mauslöchern", "Sie starrt geduldig auf ein Loch – und die Maus schaut immer beim anderen heraus. Ab und zu sitzt sie sogar hinter der Katze.",
			T.t("Beim Schuppen am Schwimmbad sitzt jemand ganz geduldig vor einer Mauer …"), "🐈", "tier", W(V["katze"].c) + Vector3(0, 0.3, 0), Vector3(2.2, 0.8, 1.2), 7.0)
	_reg(e, "see.eichhoernchen", "Der Nussdieb", "Immer wenn der Camper aufs Handy schaut, holt das Eichhörnchen eine Nuss vom Tisch und versteckt sie im Astloch. Der Haufen dort wächst.",
			T.t("Beim Picknicktisch unter dem grossen Baum verschwinden Nüsse …"), "🐿", "tier", W(Pg(8.0, -78.5, 1.0)), Vector3(4, 3, 4), 9.0, "day")
	_reg(e, "see.entenfamilie", "Entenfamilie auf dem Weg", "Die Mutter vorne, die Küken hinterher – und das letzte trödelt, rennt hinterher und purzelt.",
			T.t("Westlich vom Strand hat es eine kleine Familie gar nicht eilig über den Weg …"), "🦆", "tier", Vector3.ZERO, Vector3(3, 0.6, 3), 10.0, "day",
			{"node": V["enten"].ducks[0][0], "position": Vector3(0, 0.2, 0)})
	_reg(e, "see.igel", "Der schüchterne Igel", "Kommt man näher, rollt er sich zusammen. Wartet man still, schleicht er weiter der Hecke entlang.",
			T.t("An der Hecke bei den Bungalows raschelt es – ganz leise näher gehen."), "🦔", "tier", Vector3.ZERO, Vector3(0.5, 0.4, 0.5), 5.0, "any",
			{"node": V["igel"].hh, "position": Vector3(0, 0.15, 0)})
	_reg(e, "see.hund_ball", "Hund mit Ball", "Er bringt jedem den Ball, der vorbeikommt – auch dir. Schwimmt hinterher und schüttelt sich genau neben dem Camper.",
			T.t("Am Strand sucht jemand mit einem Ball eine Mitspielerin oder einen Mitspieler."), "🐕", "tier", Vector3.ZERO, Vector3(1, 0.8, 1), 9.0, "day",
			{"node": V["hund"].dog, "position": Vector3(0, 0.35, 0)})
	var fx: Fuchs = V["fuchs"]
	_reg(e, "see.fuchs_abfall", "Fuchs am Abfalleimer", "Er stösst den Deckel um – und im Zelt daneben geht das Licht an. Auch ein Fehlalarm-Test für MoveEye: Tier, Licht, Bewegung.",
			T.t("Nachts klappert es beim Abfall an der Zeltwiese …"), "🦊", "tier", Vector3.ZERO, Vector3(1, 0.8, 1), 12.0, "night",
			{"node": fx.fox, "position": Vector3(0, 0.35, 0), "active": func(): return fx.at_bin() and fx.shown})
	var gu: Moewe = V["moewe"]
	_reg(e, "see.moewe_pommes", "Die Pommes-Möwe", "Kaum dreht sich der Gast zum See, holt sich die Möwe eine Pommes vom Teller.",
			T.t("Auf der Restaurant-Terrasse sollte man die Pommes nicht allein lassen."), "🍟", "tier", Vector3.ZERO, Vector3(1, 0.6, 1), 14.0, "day",
			{"node": gu.gull, "position": Vector3(0, 0.2, 0), "active": func(): return gu.gull_near()})
	# B · Menschen
	_reg(e, "see.zelt_chaos", "Zeltaufbau-Chaos", "Das Zelt steht – und fällt um. Und nochmals. Am Ende schläft der Camper im Auto.",
			T.t("Ganz im Westen der Zeltwiese baut jemand ein Zelt auf – oder versucht es."), "⛺", "mensch", W(V["zelt"].c) + Vector3(0, 0.8, 0), Vector3(4, 2, 4), 14.0, "day")
	var gr: Grill = V["grill"]
	_reg(e, "see.grillmeister", "Der Grillmeister", "Es raucht immer mehr – bis der Nachbar mit dem Wassereimer kommt. Im Wärmebild ist die Glut sehr heiss.",
			T.t("Bei der Zeltwiese riecht es nach Grillwurst – und immer mehr nach Rauch."), "🍖", "mensch", W(gr.g) + Vector3(0, 1.2, 0), Vector3(3, 2.5, 3), 16.0, "any",
			{"active": func(): return gr.smoky() and gr.shown})
	var an: Angler = V["angler"]
	_reg(e, "see.angler_stiefel", "Petri Heil?", "Der Angler am Steg fängt – einen Stiefel. Er legt ihn ordentlich zu den anderen.",
			T.t("Am Ende des Bootsstegs wartet jemand geduldig auf einen Fang."), "🎣", "mensch", W(an.stand) + Vector3(0, 0.6, 0), Vector3(2, 2, 2), 14.0, "day",
			{"active": func(): return an.st in ["reel", "look"] and an.shown})
	_reg(e, "see.angler_riesenfisch", "Der Riesenfisch", "Einmal am Tag beisst etwas Grosses an – und zieht den Angler ins Wasser. Fotografiert mit MoveEyes Kamera.",
			T.t("Heute gegen %d Uhr beisst beim Angler etwas Grosses an. Vom Bootssteg aus mit MoveEyes Kamera ein Foto machen.", [int(an.fish_hour)]), "🐟", "mensch",
			Vector3.ZERO, Vector3(3.0, 2.6, 3.0), 45.0, "day", {"node": an.man, "position": Vector3(0, 0.6, -1.2), "photo_required": true,
			"active": func(): return an.fish_now() and an.shown})
	var sw: Schlafwandler = V["schlafwandler"]
	_reg(e, "see.schlafwandler", "Der Schlafwandler", "Nachts im Pyjama unterwegs, die Arme vorgestreckt – vor MoveEye bleibt er stehen und winkt. Fotografiert mit MoveEyes Kamera.",
			T.t("Nachts, wenn MoveEye beim Zelt steht, kommt jemand im Pyjama vorbei. Ein Foto mit MoveEyes Kamera, wenn er winkt!"), "😴", "mensch",
			Vector3.ZERO, Vector3(0.8, 1.85, 0.5), 25.0, "night", {"node": sw.man, "position": Vector3(0, 0.95, 0), "photo_required": true,
			"active": func(): return sw.waving() and sw.shown})
	var vk: Verstecken = V["verstecken"]
	_reg(e, "see.verstecken", "Verstecken hinter den Hecken", "Eines zählt an der Hecke, die anderen verstecken sich hinter Hecken, Wohnmobilen und Autos.",
			T.t("Auf der Wohnmobil-Terrasse kichert es hinter den Hecken."), "🙈", "mensch", W(vk.c) + Vector3(0, 0.8, 0), Vector3(6, 2, 6), 16.0, "day",
			{"active": func(): return not vk.mw and vk.shown})
	_reg(e, "see.verstecken_moveeye", "MoveEye spielt mit", "MoveEye hat beim Verstecken alle vier Kinder gefunden.",
			T.t("Die Kinder spielen auch mit MoveEye Verstecken: Spiel → Entdecken → «Verstecken mit MoveEye»."), "👀", "mensch",
			Vector3(0, -50, 0), Vector3.ONE, 0.5, "day", {"active": func(): return false, "los": false})
	var yg: Yoga = V["yoga"]
	_reg(e, "see.yoga", "Yoga bei Sonnenaufgang", "Alle schauen zum See – nur eine Person macht alles falsch herum und etwas zu spät.",
			T.t("Früh am Morgen ist am Strand Yoga – schau genau, wer wohin schaut."), "🧘", "mensch", W(yg.c) + Vector3(0, 0.8, 0), Vector3(7, 2, 7), 18.0, "morning")
	if not e.found.is_connected(_on_found):
		e.found.connect(_on_found)


func _on_found(id: String) -> void:
	if id == "see.flaschenpost" and is_inside_tree():
		var e = ent()
		if e != null:
			e.call_deferred("show_hint", "see.schatzkiste")       # the map: Blinki tells where the cross is


func _exit_tree() -> void:
	var e = ent()
	if e != null and e.found.is_connected(_on_found):
		e.found.disconnect(_on_found)


# =============================================================================================================================
# ---- control {"action": "ferienpark", "do": "erleben", …} ---------------------------------------------------------------------
# =============================================================================================================================
func start_seek() -> Dictionary:
	var v: Verstecken = by_id["verstecken"]
	var r := v.start_mw()
	_update_shown(true)
	return r


func control(d: Dictionary) -> Dictionary:
	match str(d.get("what", "info")):
		"verstecken":
			return {"ok": true, "result": start_seek()}
		"verstecken_stop":
			(by_id["verstecken"] as Verstecken).stop_mw()
			return {"ok": true}
		"fish":                                          # tests: the giant fish now (next time the float is in the water)
			var a: Angler = by_id["angler"]
			a.force = true
			a.wait_s = 2.0
			return {"ok": true}
		"where":                                         # where a vignette is (world), for tests
			var id := str(d.get("id", ""))
			if not by_id.has(id):
				return {"ok": false, "error": "unknown", "ids": by_id.keys()}
			var w: Vector3 = by_id[id].where()
			return {"ok": true, "pos": [snappedf(w.x, 0.01), snappedf(w.y, 0.01), snappedf(w.z, 0.01)]}
		"state":                                         # tests: jump a vignette to a state
			var id2 := str(d.get("id", ""))
			if by_id.has(id2):
				if d.has("state"):
					by_id[id2].go(str(d.get("state", "")))
				if d.has("t"):
					by_id[id2].st_t = float(d["t"])
				by_id[id2].hold = bool(d.get("hold", false))
				return {"ok": true}
			return {"ok": false}
	var out := []
	for v in vigs:
		out.append(v.info())
	return {"ok": true, "vignettes": out, "stats": stats, "lite": lite, "today": today}
