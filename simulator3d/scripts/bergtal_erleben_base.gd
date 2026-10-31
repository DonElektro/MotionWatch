extends Node3D
## 3D-4.37: gemeinsame Basis der Bergtal-Erlebnisse (bergtal_erleben_a.gd 1–17, bergtal_erleben_b.gd 18–34):
## Hilfsfunktionen (Tal ↔ Welt, Figuren, kleine Netze, Töne), Nähe-/Sichtbarkeitsprüfung, _process und die Klasse Vig.
## Jeder Teil: extends dieser Datei, _part(), _make_vigs(), _register() und seine Vignetten (class X extends Vig).

const T = preload("res://scripts/i18n.gd")
const Bib = preload("res://scripts/bib_berg.gd")

const ACTIVE_R := 60.0         # m: closer than this (window camera or MoveEye) the vignette moves
const SHOW_R := 220.0          # m: farther than this from both, its figures are hidden
const SCENE := "bergtal"

var m                          # main.gd
var bt                         # bergtal.gd (valley transform, ground, season, spot)
var s                          # scenes.gd
var holder: Node3D             # valley-space node (child of the valley node «bergtal»)
var mb                         # own library instance (bib_berg.gd) for the fixed pieces of these vignettes
var lite := false
var season := "sommer"
var vigs: Array = []
var by_id := {}
var _tick := 0.0
var _clock := 0.0
var _pending: Array = []       # sounds to play later: [clock, valley pos, kind, notes, vol_db, db1m]
var stats := {"active": 0, "shown": 0, "actors": 0, "us": 0.0}
static var _snd_cache := {}


static func _lite() -> bool:
	return Bib.lite()


func setup(bt_) -> void:
	bt = bt_
	m = bt.m
	s = bt.s
	season = str(bt.season)
	name = "bergtal_erleben_" + _part()
	lite = _lite() or str(m.quality) == "simple"
	_rain_end = float(Engine.get_meta("berg_rain_end", -1.0e9))
	process_priority = 100                      # after the figures: own heights (rock, bridge, desk) win over the ground
	s.root.add_child(self)
	holder = Node3D.new()
	holder.name = "erleben_" + _part()
	bt.tal.add_child(holder)
	mb = Bib.new(m, s, holder, bt.tal.transform)
	for v in _make_vigs():
		v.build()
		vigs.append(v)
		by_id[v.id] = v
	mb.finish()
	_register()
	_update_shown(true)


# ---- helpers: valley <-> world, figures, small meshes, sounds ------------------------------------------------------------
func G(x: float, z: float, dy := 0.0) -> Vector3:
	"""a valley point on the ground"""
	return Vector3(x, bt.H(x, z) + dy, z)


func W(p: Vector3) -> Vector3:
	var w: Vector3 = bt.W(p)
	return w


func VL(w: Vector3) -> Vector3:
	var p: Vector3 = bt.V(w)
	return p


func head_pos() -> Vector3:
	return (m.head as Node3D).global_position if m.head != null else Vector3.ZERO


func view_cam() -> Camera3D:
	return get_viewport().get_camera_3d() if is_inside_tree() else null


func view_pos() -> Vector3:
	var c := view_cam()
	return c.global_position if c != null else Vector3(0, 1000, 0)


func unseen(w: Vector3, far := 70.0) -> bool:
	"""the window camera does not look at this world point now (or is far) - for quiet resets"""
	var c := view_cam()
	if c == null:
		return true
	var d := w - c.global_position
	if d.length() > far:
		return true
	return (-c.global_transform.basis.z).dot(d.normalized()) < 0.35


func actor(kind: String, p: Vector3, look: Vector3, spd := 1.2, jacket = null) -> Node3D:
	"""a figure of actor.gd as a puppet at the valley point p, facing the valley point look"""
	var a = m.Actor.new()
	if jacket != null:
		a.player_color = jacket
	add_child(a)
	a.setup(m, kind, W(p), W(look), spd)
	a.puppet = true
	a.set_meta("nachbar", true)                                   # never part of a test (like the neighbours of szenenplus.gd)
	a.set_meta("erleben", true)
	a.add_to_group("erleben_fig")                                 # overlay3d.gd: MoveEye's boxes on these count as «erkannt»
	if a.lamp != null:                                            # no torch / phone light
		a.lamp.light_energy = 0.0
		a.lamp_mat.emission_energy_multiplier = 0.0
		a.lamp = null
		a.phone_out = false
	face(a, look - p)
	return a


func marmot(p: Vector3, look: Vector3, sc := 1.0) -> Node3D:
	# Murmeltier (Marmota marmota): 50–60 cm, braungrau; Fell-Oberfläche im Wärmebild um 31 °C (wie bergtal.gd _marmot)
	var a := actor("badger", p, look, 0.6)
	a.body_root.scale *= 0.85 * sc
	bt._recolor(a, Color(0.56, 0.44, 0.3), 31.0)
	return a


func backpack(a, col := Color(0.2, 0.32, 0.5)) -> void:
	"""a hiker's backpack on the back of a person (with its thermal twin, about the air)"""
	if a.body_root == null:
		return
	part(a.body_root, boxm(0.34, 0.5, 0.2), Vector3(0, 1.22, 0.2), col, "tent")


func face(a, d: Vector3) -> void:
	"""turn a figure towards the valley direction d (at once)"""
	var wd: Vector3 = bt.tal.transform.basis * Vector3(d.x, 0, d.z)
	if wd.length() < 0.001:
		return
	a.heading = atan2(-wd.x, -wd.z)
	a.rotation.y = a.heading
	a.dir = wd.normalized()


func turn_to(a, d: Vector3, dt: float, rate := 4.0) -> bool:
	var wd: Vector3 = bt.tal.transform.basis * Vector3(d.x, 0, d.z)
	if wd.length() < 0.001:
		return true
	var want := atan2(-wd.x, -wd.z)
	a.heading = rotate_toward(float(a.heading), want, rate * dt)
	a.rotation.y = a.heading
	return absf(wrapf(want - float(a.heading), -PI, PI)) < 0.05


func ppos(a) -> Vector3:
	"""where a figure is (valley x, z; y = 0)"""
	var q := VL((a as Node3D).global_position)
	return Vector3(q.x, 0, q.z)


func place(a, p: Vector3, lift := false) -> void:
	"""a figure at the valley point p; lift = keep this height (rock, desk), else on the ground"""
	var wp := W(p)
	a.global_position = wp
	if lift:
		a.set_meta("be_y", wp.y)
	elif a.has_meta("be_y"):
		a.remove_meta("be_y")


func walk(a, to: Vector3, spd: float, dt: float, lift_y = null, turn := 6.0) -> bool:
	"""a few steps towards the valley point «to» (x, z); true = arrived. lift_y: walk at this valley height (a ledge)"""
	var p := ppos(a)
	var d := Vector3(to.x - p.x, 0, to.z - p.z)
	var L := d.length()
	if L < 0.08:
		a.cur_speed = move_toward(float(a.cur_speed), 0.0, dt * 4.0)
		return true
	turn_to(a, d, dt, turn)
	a.cur_speed = move_toward(float(a.cur_speed), spd, dt * 3.0 * maxf(1.0, spd))
	var stp: float = minf(float(a.cur_speed) * dt, L)
	var np := p + d / L * stp
	if lift_y == null:
		var gp := W(G(np.x, np.z))
		a.global_position = gp
		if a.has_meta("be_y"):
			a.remove_meta("be_y")
	else:
		var wp := W(Vector3(np.x, float(lift_y), np.z))
		a.global_position = wp
		a.set_meta("be_y", wp.y)
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
	"""a visible part + its twin for the thermal camera (tk: °C or a surface key like "stone", "tree", "tent", "snow")"""
	var mi: MeshInstance3D = m.add_mesh(parent, mesh, p, m.mat(col), tk, rot, scl)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if lite else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	return mi


func twin_of(mi: MeshInstance3D) -> MeshInstance3D:
	var par := mi.get_parent()
	var i := mi.get_index() + 1
	return par.get_child(i) as MeshInstance3D if i < par.get_child_count() else null


func show_part(mi: MeshInstance3D, on: bool) -> void:
	"""a part and its thermal twin on / off together"""
	mi.visible = on
	var th := twin_of(mi)
	if th != null:
		th.visible = on


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


func glow_mat(c: Color, e := 2.0, alpha := 1.0) -> StandardMaterial3D:
	var gm := StandardMaterial3D.new()
	gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	gm.albedo_color = Color(c.r, c.g, c.b, alpha)
	gm.emission_enabled = true
	gm.emission = c
	gm.emission_energy_multiplier = e
	if alpha < 1.0:
		gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return gm


func light_part(parent: Node3D, mesh: Mesh, p: Vector3, mt: Material) -> MeshInstance3D:
	"""a part only for the normal cameras (light, sky) - the thermal camera does not see it"""
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = p
	mi.material_override = mt
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


func lamp(parent: Node3D, p: Vector3, col: Color, energy: float, rng_m: float) -> OmniLight3D:
	"""a small light (not in Lite - there only the glowing part)"""
	if lite:
		return null
	var l := OmniLight3D.new()
	l.position = p
	l.light_color = col
	l.light_energy = energy
	l.omni_range = rng_m
	l.shadow_enabled = false
	parent.add_child(l)
	return l


func hour() -> float:
	var h: float = m.hour()
	return h


func dark() -> bool:
	return bool(m.is_dark())


func weather() -> String:
	return str(m.weather)


func alp_season() -> bool:
	"""the cows and sheep are up on the alp (Alpaufzug June … Alpabzug end of September)"""
	return season in ["sommer", "herbst"]


func ent():
	var e = m.get("entdecken")
	return e if e != null and e.has_method("register") else null


func sound(p: Vector3, kind: String, notes: Array, vol_db := 0.0, db1m := -12.0, delay := 0.0) -> void:
	"""a small generated sound at the valley point p (notes: [[start s, length s, f0 Hz, f1 Hz, amp]]); MoveEye's
	microphone gets the level (main.add_sound), the PC speakers the sound itself (only if «Geräusche» are on)"""
	_pending.append([_clock + delay, p, kind, notes, vol_db, db1m])


func _play(p: Vector3, kind: String, notes: Array, vol_db: float, db1m: float) -> void:
	var dur := 0.0
	for n in notes:
		dur = maxf(dur, float(n[0]) + float(n[1]))
	var wp := W(p)
	m.add_sound(db1m, wp, dur)
	if not bool(m.sound_on) or DisplayServer.get_name() == "headless":
		return
	var key := kind + str(notes)
	if not _snd_cache.has(key):
		_snd_cache[key] = _synth(kind, notes, dur)
	var pl := AudioStreamPlayer3D.new()
	pl.stream = _snd_cache[key]
	pl.volume_db = vol_db
	pl.unit_size = 8.0
	pl.max_distance = 700.0
	add_child(pl)
	pl.global_position = wp
	pl.finished.connect(pl.queue_free)
	pl.play()


func _synth(kind: String, notes: Array, dur: float) -> AudioStreamWAV:
	var rate := 16000
	var ns := int((dur + 0.2) * rate)
	var buf := PackedFloat32Array()
	buf.resize(ns)
	var att: float = {"horn": 0.15, "voice": 0.06, "moo": 0.12, "whistle": 0.015, "honk": 0.01, "thud": 0.002, "creak": 0.05, "bell": 0.003, "swish": 0.08, "plop": 0.004}.get(kind, 0.05)
	var rel: float = {"horn": 0.3, "voice": 0.22, "moo": 0.3, "whistle": 0.08, "honk": 0.04, "thud": 0.05, "creak": 0.1, "bell": 0.25, "swish": 0.15, "plop": 0.05}.get(kind, 0.1)
	for n in notes:
		var t0 := float(n[0])
		var ln := float(n[1])
		var f0 := float(n[2])
		var f1 := float(n[3])
		var amp := float(n[4]) if n.size() > 4 else 1.0
		var i0 := int(t0 * rate)
		var cnt := mini(int(ln * rate), ns - i0)
		var ph := 0.0
		for i in range(cnt):
			var t := float(i) / rate
			var f := lerpf(f0, f1, t / ln)
			if kind in ["horn", "voice"]:
				f *= 1.0 + 0.004 * sin(t * TAU * 5.2)
			ph += TAU * f / rate
			var env := minf(1.0, t / att) * clampf((ln - t) / rel, 0.0, 1.0)
			var v := 0.0
			match kind:
				"horn":
					v = sin(ph) + 0.45 * sin(2.0 * ph) + 0.25 * sin(3.0 * ph) + 0.1 * sin(4.0 * ph)
				"voice":
					v = sin(ph) + 0.7 * sin(2.0 * ph) + 0.5 * sin(3.0 * ph) + 0.25 * sin(5.0 * ph)
				"moo":
					v = (sin(ph) + 0.6 * sin(2.0 * ph) + 0.45 * sin(3.0 * ph) + 0.3 * sin(4.0 * ph) + 0.2 * sin(5.0 * ph)) * (0.75 + 0.25 * sin(t * TAU * 3.0))
				"whistle":
					v = sin(ph) * 1.6
				"honk":
					v = 0.5 * signf(sin(ph)) + 0.5 * signf(sin(ph * 1.26))
				"thud":
					v = (randf() * 2.0 - 1.0) * exp(-t * 28.0) * 2.0
				"creak":
					v = (randf() * 2.0 - 1.0) * 0.5 * (0.5 + 0.5 * sin(ph))
				"bell":                                       # Kuhglocke (Treichel/Schelle): unharmonische Teiltöne, klingt aus
					v = (sin(ph) + 0.6 * sin(2.76 * ph) + 0.35 * sin(5.4 * ph)) * exp(-t * 4.0) * 1.4
				"swish":                                      # Besen: Rauschen, das an- und abschwillt
					v = (randf() * 2.0 - 1.0) * 0.6 * sin(PI * clampf(t / ln, 0.0, 1.0))
				"plop":                                       # eine Forelle springt nach einer Fliege
					v = sin(ph) * exp(-t * 30.0) * 1.5
			buf[i0 + i] += v * env * amp * 0.22
	var pcm := PackedByteArray()
	pcm.resize(ns * 2)
	for i in range(ns):
		pcm.encode_s16(i * 2, int(clampf(buf[i], -1.0, 1.0) * 30000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = rate
	w.data = pcm
	return w


# ---- running: only what is near, nothing during tests --------------------------------------------------------------------
func _is_quiet() -> bool:
	var e = ent()
	if e != null and e.has_method("_quiet"):
		return bool(e._quiet())
	return bool(m.measuring()) or bool(m.get("spectate"))


func _update_shown(force := false) -> void:
	var q := _is_quiet()
	var vp := view_pos()
	var hp := head_pos()
	var na := 0
	var ns := 0
	var nact := 0
	var show_r := SHOW_R * (0.6 if lite else 1.0)
	for v in vigs:
		var w: Vector3 = v.where()
		var d := 0.0 if v.anywhere else minf(vp.distance_to(w), hp.distance_to(w))
		var sh: bool = not q and v.when_ok() and d < show_r
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


func _process(dt: float) -> void:
	if m == null or not is_inside_tree() or bt.tal == null or not is_instance_valid(bt.tal):
		return
	dt = minf(dt, 0.25)
	_clock += dt
	_tick -= dt
	if _tick <= 0.0:
		_tick = 0.6 if lite else 0.3
		if weather() == "rain":                                   # salamanders: «nach Regen» (kept over rebuilds of the scene)
			_rain_end = float(m.now())
			Engine.set_meta("berg_rain_end", _rain_end)
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
		if a.has_meta("be_y") and a.process_mode != Node.PROCESS_MODE_DISABLED:
			a.global_position.y = float(a.get_meta("be_y"))
	for i in range(_pending.size() - 1, -1, -1):
		var pd: Array = _pending[i]
		if _clock >= float(pd[0]):
			_pending.remove_at(i)
			_play(pd[1], pd[2], pd[3], pd[4], pd[5])
	stats["us"] = lerpf(float(stats["us"]), float(Time.get_ticks_usec() - t0), 0.1)


# =============================================================================================================================
# ---- the vignettes ------------------------------------------------------------------------------------------------------------
# =============================================================================================================================
class Vig:
	var ew
	var id := ""
	var c := Vector3.ZERO           # valley centre (on the ground)
	var actors: Array = []
	var t := 0.0
	var st := ""
	var st_t := 0.0
	var active := false
	var shown := false
	var hold := false
	var always := false
	var anywhere := false           # shown wherever the view is (the sky: northern lights)
	var built := false
	var vroot: Node3D               # valley-space node of its things (shown / hidden as a whole)

	func _init(e) -> void:
		ew = e
		vroot = Node3D.new()
		e.holder.add_child(vroot)
		vroot.visible = false

	func build() -> void:           # fixed pieces (at the scene start)
		pass

	func live() -> void:            # figures and moving things (the first time it is shown)
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
		if on and not built:
			built = true
			live()
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
		return {"id": id, "state": st, "active": active, "shown": shown, "built": built, "t": snappedf(t, 0.1)}


# ---- what each part fills in -----------------------------------------------------------------------------------------------
func _part() -> String:
	"""«a» or «b» (node names)"""
	return "x"


func _make_vigs() -> Array:
	"""the vignettes of this part (instances of inner classes extending Vig)"""
	return []


func _register() -> void:
	pass


# ---- shared state ----------------------------------------------------------------------------------------------------------
var _rain_end := -1.0e9        # m.now() when it rained the last time (salamanders: «nach Regen»; kept over rebuilds in an Engine meta)
