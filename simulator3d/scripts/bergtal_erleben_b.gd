extends Node3D
## 3D-4.x «Bergtal» – lustige und versteckte Ereignisse 18–34 (Daniel 31.10.2026, Stil «dezent», docs/Bergtal_Plan.md):
## kleine Abläufe an den reservierten Plätzen von bergtal.gd (VIGNETTES 30–46 = Daniels Nummern 18–34). Humor durch Timing
## und Bewegung, keine Sprechblasen, glaubwürdig – man muss genau hinschauen.
##   18 weisser Schneehase im braunen Herbst      · 19 Hermelin schaut aus jedem Mauerloch (am Schluss der Schwanz)
##   20 Salamander-Prozession nach Regen (einer falsch rum) · 21 nur Kuhglocken im Nebel, plötzlich eine Kuh vor MoveEye
##   22 Gämse auf dem Hospiz-Dach                · 23 Selfie-Wanderer an der Schluchtkante, die Kuh stupst ihn nach vorn
##   24 Trailrunner fragt den Wegweiser          · 25 Selbstversorger-Gast fegt die Veranda, der Wind weht alles zurück
##   26 Picknick: der Korkenzieher steckt am Hut · 27 Gleitschirm landet auf der Kuhweide
##   28 Postauto mit Dreiklang-Horn in den Kehren · 29 Schmugglerroute: Zeichen nur im Abendlicht, am Ende ein Versteck
##   30 Steinmann-Wald: einer hat Augen          · 31 verlassene Sennerei, im uralten Käselaib wohnt eine Maus
##   32 Holzski schmilzt aus dem Gletscher (Sommer) · 33 Nordlicht (nur seltene klare Winternächte)
##   34 geheimer Bergsee hinter dem Grat (Forellen springen, morgens trinkt eine Gämse)
## Gleiche Technik wie Teil A (bergtal_erleben_a.gd) und der Ferienpark (erlebniswelt.gd): jede Vignette eine kleine
## Zustandsmaschine (innere Klasse), läuft nur, wenn die Ansicht oder MoveEye näher als ACTIVE_R ist, Figuren erst beim ersten
## Zeigen gebaut, weiter weg als SHOW_R versteckt; bei Testlauf / Prüfstand / Messung ist alles weg (vergleichbare Ergebnisse).
## Die Hilfsfunktionen sind eine Kopie von Teil A (eigene Datei, damit die zwei Teile unabhängig sind; der Koordinator kann
## sie beim Zusammenführen in eine gemeinsame Basis legen).
## Entdeckungsbuch: main.entdecken.register() (Szene «bergtal», ids «berg.…»), nur wenn es das gibt (Zweig erlebniswelt/main).
## Steuerung: {"action": "bergtal", "do": "erleben_b", "what": "info | where | state | go | rain | nordlicht", "id": …}.
## Lite (Engine-Meta «lite» wie bib_berg.gd; der Koordinator verbindet es mit Quality.lite()): weniger Salamander, Blätter und
## Ringe, keine Leinen am Gleitschirm, Nordlicht mit 2 statt 4 Vorhängen, keine Zusatzlichter.


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
	name = "bergtal_erleben_b"
	lite = _lite() or str(m.quality) == "simple"
	_rain_end = float(Engine.get_meta("berg_rain_end", -1.0e9))
	process_priority = 100                      # after the figures: own heights (rock, bridge, desk) win over the ground
	s.root.add_child(self)
	holder = Node3D.new()
	holder.name = "erleben_b"
	bt.tal.add_child(holder)
	mb = Bib.new(m, s, holder, bt.tal.transform)
	for v in [Schneehase.new(self), Hermelin.new(self), Salamander.new(self), Glocken.new(self), Dachgemse.new(self), Selfie.new(self),
			Trailrunner.new(self), Fegen.new(self), Picknick.new(self), Gleitschirm.new(self), Postauto.new(self), Schmuggler.new(self),
			Augen.new(self), Sennerei.new(self), Holzski.new(self), Nordlicht.new(self), Geheimsee.new(self)]:
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
		a.set_meta("beb_y", wp.y)
	elif a.has_meta("beb_y"):
		a.remove_meta("beb_y")


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
		if a.has_meta("beb_y"):
			a.remove_meta("beb_y")
	else:
		var wp := W(Vector3(np.x, float(lift_y), np.z))
		a.global_position = wp
		a.set_meta("beb_y", wp.y)
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
		if a.has_meta("beb_y") and a.process_mode != Node.PROCESS_MODE_DISABLED:
			a.global_position.y = float(a.get_meta("beb_y"))
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



# ---- extra helpers of part B ------------------------------------------------------------------------------------------------
var _rain_end := -1.0e9        # m.now() when it rained the last time (salamanders: «nach Regen»; kept over rebuilds in an Engine meta)
var force_nordlicht := false   # tests / control: the northern lights tonight (else: rare, by date)


func arm(a, side: int, sx: float, ex: float, sz := 0.0) -> void:
	"""an arm pose set after the figure animated itself (side +1 = right): shoulder forward/up sx, elbow ex (radians)"""
	if a == null or not is_instance_valid(a):
		return
	for ar in a.arms:
		if int(ar[1]) == side:
			(ar[0] as Node3D).rotation.x = sx
			(ar[0] as Node3D).rotation.z = sz * side
			if ar.size() > 2 and ar[2] != null:
				(ar[2] as Node3D).rotation.x = ex


func forearm(a, side: int) -> Node3D:
	for ar in a.arms:
		if int(ar[1]) == side and ar.size() > 2 and ar[2] != null:
			return ar[2]
	return a.body_root


func rod(parent: Node3D, a: Vector3, b: Vector3, r: float, col: Color, tk) -> MeshInstance3D:
	"""a thin rod from a to b (lines of the paraglider, poles); its thermal twin follows"""
	var mi := part(parent, cylm(r, r, 1.0, 5), Vector3.ZERO, col, tk)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	set_rod(mi, a, b)
	return mi


func set_rod(mi: MeshInstance3D, a: Vector3, b: Vector3) -> void:
	var d := b - a
	var L := maxf(d.length(), 0.001)
	var y := d / L
	var x := y.cross(Vector3(0, 0, 1))
	if x.length() < 0.01:
		x = y.cross(Vector3(1, 0, 0))
	x = x.normalized()
	var z := x.cross(y)
	var tf := Transform3D(Basis(x, y * L, z), (a + b) * 0.5)
	mi.transform = tf
	var th := twin_of(mi)
	if th != null:
		th.transform = tf


func set_tf(mi: MeshInstance3D, tf: Transform3D) -> void:
	mi.transform = tf
	var th := twin_of(mi)
	if th != null:
		th.transform = tf


func wet_recent(mins := 45.0) -> bool:
	"""it rains now, or it rained in the last «mins» minutes of the simulator clock"""
	if weather() == "rain":
		return true
	return (float(m.now()) - _rain_end) * float(m.speed) / 60.0 < mins


func foggy() -> bool:
	"""fog: the weather «Nebel» or the fog that rolls in (bergtal.gd fog_roll)"""
	var fk = bt.get("_fog_k")
	return weather() == "fog" or (fk != null and float(fk) > 0.5)


func evening_light() -> float:
	"""0 … 1: low evening sun (sun 7° … 0° above the horizon, afternoon) - the raking light that shows scratches in the rock"""
	if not m.has_method("sun_pos") or hour() < 12.0 or weather() in ["fog", "rain", "snow"]:
		return 0.0
	var el: float = (m.sun_pos() as Vector2).x
	return clampf(1.0 - absf(el - 3.5) / 4.5, 0.0, 1.0)


func nordlicht_tonight() -> bool:
	"""rare: only in winter, only in clear dark nights, and then only on about one night in twelve (by date). In der Schweiz
	sieht man Polarlichter nur bei sehr starken Sonnenstürmen (zuletzt z. B. 10./11. Mai und 10. Oktober 2024), tief am
	Nordhorizont und meist rötlich (Sauerstoff-Leuchten in 200–400 km Höhe; das grüne Band liegt tiefer, unter dem Horizont)."""
	if season != "winter" or not dark():
		return false
	if force_nordlicht:
		return true
	if weather() != "clear":
		return false
	var d := Time.get_date_dict_from_system()
	var night := int(d["year"]) * 400 + int(m.day_of_year()) - (1 if hour() < 12.0 else 0)   # after midnight: still the same night
	return posmod(night * 7919 + 13, 97) < 8


func head_fwd() -> Vector3:
	"""where MoveEye's head camera looks (world, horizontal)"""
	if m.cams.is_empty() or m.cams[0] == null:
		return Vector3(0, 0, -1)
	var f: Vector3 = -(m.cams[0] as Node3D).global_transform.basis.z
	f.y = 0.0
	return f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)


# =============================================================================================================================
# ---- the vignettes 18–34 ----------------------------------------------------------------------------------------------------
# =============================================================================================================================

# ---- 18 · a white snow hare in the brown autumn: it sits still - always beside the only white thing around -------------------
class Schneehase extends Vig:
	var hare
	var spots: Array = []           # a last tiny snow patch, pale stones - it believes it is invisible there
	var at := 0

	func build() -> void:
		id = "schneehase_herbst"
		c = ew.G(-420.0, 385.0)
		for o in [Vector2(0, 0), Vector2(14, -6), Vector2(-9, 11), Vector2(6, 15)]:
			spots.append(ew.G(c.x + o.x, c.z + o.y))

	func when_ok() -> bool:
		return ew.season == "herbst"

	func live() -> void:
		for i in range(spots.size()):
			var p: Vector3 = spots[i]
			if i == 0:                                         # the snow patch: much too small for a hare
				ew.part(vroot, ew.cylm(0.24, 0.28, 0.03, 12), p + Vector3(0.08, 0.012, 0.1), Color(0.93, 0.94, 0.95), "snow")
			else:
				ew.part(vroot, ew.sphm(0.17, 0.2, 8), p + Vector3(0.38, 0.06, 0.0), Color(0.8, 0.79, 0.75), "stone")
		hare = ew.actor("hare", spots[0], spots[0] + Vector3(1, 0, 0), 1.0)
		# Schneehase (Lepus timidus varronis): wechselt im Oktober/November ins weisse Winterfell - ob Schnee liegt oder nicht.
		# Wärmebild: das dichte Winterfell isoliert, die Oberfläche bleibt weit unter den 39 °C im Körper (Schätzung 22 °C).
		ew.bt._recolor(hare, Color(0.95, 0.95, 0.93), 22.0)
		actors.append(hare)
		go("sit")

	func tick(dt: float) -> void:
		match st:
			"sit":                                             # pressed flat, ears down: «nobody sees me»
				ew.stop(hare, dt)
				ew.idle(hare, "sit")
				if st_t > 2.0 and ew.view_pos().distance_to(ew.W(spots[at])) < 7.0:
					at = (at + 1) % spots.size()
					ew.idle(hare, "")
					go("hop")
			"hop":                                             # a few long hops to the next pale thing - and sits still again
				if ew.walk(hare, spots[at], 3.4, dt, null, 10.0) or st_t > 12.0:
					ew.face(hare, Vector3(1, 0, 0.3))
					go("sit")

	func sitting() -> bool:
		return shown and st == "sit"


# ---- 19 · the stoat in the wall: out of every hole, faster and faster - at the end the head here and the tail there --------
class Hermelin extends Vig:
	var holes: Array = []           # [valley point of the hole face (side +), outward normal]
	var head: Node3D
	var tail: Node3D
	var order: Array = [0, 3, 1, 4, 2, 0, 3]
	var k := 0
	var side := 1.0
	var out := 0.0
	var rot := 0.6

	func build() -> void:
		id = "hermelin_mauer"
		c = ew.G(104.0, -34.0)

	func live() -> void:
		var L := 6.0
		var b := Basis(Vector3.UP, rot)
		for i in range(5):
			var lp := Vector3(-L * 0.4 + i * L * 0.2, 0.3 + 0.35 * (i % 2), 0.0)
			holes.append(c + b * lp)
		var winter: bool = ew.season == "winter"
		# Hermelin (Mustela erminea): Sommer braun mit weissem Bauch, Winter ganz weiss - die Schwanzspitze bleibt immer schwarz.
		# Wärmebild: kurzes Fell am Kopf, Oberfläche ~30 °C (Schätzung, wie die Maus im Ferienpark); Schwanz kühler.
		var back := Color(0.95, 0.94, 0.9) if winter else Color(0.5, 0.32, 0.16)
		head = ew.node(vroot, c)
		ew.part(head, ew.cylm(0.026, 0.03, 0.14, 8), Vector3(0, 0, 0.07), back, 30.0, Vector3(PI / 2, 0, 0))
		ew.part(head, ew.sphm(0.032, 0.05, 8), Vector3(0, 0.012, 0.15), back, 31.0)
		ew.part(head, ew.sphm(0.02, 0.03, 6), Vector3(0, -0.012, 0.15), Color(0.96, 0.95, 0.9), 31.0)    # white throat
		for sx in [-0.016, 0.016]:
			ew.part(head, ew.sphm(0.009), Vector3(sx, 0.036, 0.14), back, 29.0)                               # ears
			ew.part(head, ew.sphm(0.005), Vector3(sx * 0.9, 0.02, 0.178), Color(0.02, 0.02, 0.02), 31.0)       # eyes
		ew.part(head, ew.sphm(0.006), Vector3(0, 0.008, 0.185), Color(0.05, 0.03, 0.03), 31.0)               # nose
		tail = ew.node(vroot, c)
		ew.part(tail, ew.cylm(0.011, 0.013, 0.09, 6), Vector3(0, 0, 0.045), back, 26.0, Vector3(PI / 2, 0, 0))
		ew.part(tail, ew.cylm(0.004, 0.013, 0.06, 6), Vector3(0, 0, 0.115), Color(0.03, 0.03, 0.03), 25.0, Vector3(PI / 2, 0, 0))
		head.visible = false
		tail.visible = false
		go("pause")

	func _put(n: Node3D, hole: int, o: float, look := 0.0) -> void:
		var b := Basis(Vector3.UP, rot)
		var nrm: Vector3 = b * Vector3(0, 0, side)
		n.position = (holes[hole] as Vector3) + nrm * (0.17 + o)
		n.rotation = Vector3(0, rot + (0.0 if side > 0 else PI) + look, 0)
		n.visible = o > -0.15

	func _side_to_view() -> void:
		var v: Vector3 = ew.VL(ew.view_pos())
		var nrm: Vector3 = Basis(Vector3.UP, rot) * Vector3(0, 0, 1)
		side = 1.0 if (v - c).dot(nrm) >= 0.0 else -1.0

	func tick(dt: float) -> void:
		match st:
			"pause":
				head.visible = false
				tail.visible = false
				if st_t > 6.0:
					_side_to_view()
					k = 0
					go("peek")
			"peek":                                            # out - look left, right - and back in; every time a bit faster
				var dur: float = maxf(0.6, 3.0 * pow(0.72, k))
				var f: float = st_t / dur
				out = clampf(minf(f * 5.0, (1.0 - f) * 5.0), 0.0, 1.0)
				var look: float = 0.6 * sin(f * TAU) if dur > 1.0 else 0.0
				_put(head, order[k], -0.17 + 0.29 * out, look)
				if f >= 1.0:
					k += 1
					if k >= order.size():
						go("both")
					else:
						go("peek")
			"both":                                            # the head out of the middle hole - and the black tail tip out of the last one
				var o2: float = clampf(st_t * 3.0, 0.0, 1.0) * clampf((4.5 - st_t) * 3.0, 0.0, 1.0)
				_put(head, 2, -0.17 + 0.29 * o2, 0.25 * sin(st_t * 1.5))
				_put(tail, 4, -0.17 + 0.29 * o2, 0.0)
				tail.rotation.y += 0.35 * sin(st_t * 9.0)
				if st_t > 4.6:
					go("pause")

	func popping() -> bool:
		return shown and st in ["peek", "both"] and head.visible


# ---- 20 · alpine salamanders after the rain: a slow procession across the path - one walks the wrong way -------------------
class Salamander extends Vig:
	var sal: Array = []             # [node, u (m along the line), dir (+1 / -1), state]
	var a0 := Vector3.ZERO
	var a1 := Vector3.ZERO
	var L := 5.0
	var temp_t := 0.0

	func build() -> void:
		id = "salamander_prozession"
		c = ew.G(66.0, -40.0)
		var d := Vector2(10, -70).normalized()                # the Schluchtweg here (from the alp down to the gorge)
		var pr := Vector3(-d.y, 0, d.x) * -1.0
		a0 = c - pr * L * 0.5
		a1 = c + pr * L * 0.5

	func when_ok() -> bool:
		return ew.season != "winter" and ew.wet_recent()       # Winterruhe Oktober … April; draussen nur bei Regen und danach

	func live() -> void:
		var n := 4 if ew.lite else 7
		# Alpensalamander (Salamandra atra): ganz schwarz, glänzend, 11–15 cm; wechselwarm - im Wärmebild fast wie der Boden
		var temp: float = float(ew.m.ambient) + 0.5
		var col := Color(0.03, 0.03, 0.035)
		for i in range(n):
			var nd: Node3D = ew.node(vroot, a0)
			ew.part(nd, ew.sphm(0.013, 0.026, 6), Vector3(0, 0.012, 0), col, temp, Vector3.ZERO, Vector3(1.0, 0.75, 3.4))
			ew.part(nd, ew.sphm(0.011, 0.018, 6), Vector3(0, 0.013, -0.05), col, temp)
			ew.part(nd, ew.cylm(0.001, 0.008, 0.06, 5), Vector3(0, 0.01, 0.07), col, temp, Vector3(PI / 2, 0, 0))
			for lx in [-1.0, 1.0]:
				for lz in [-0.025, 0.022]:
					ew.part(nd, ew.boxm(0.018, 0.005, 0.006), Vector3(lx * 0.014, 0.005, lz), col, temp)
			var wrong := i == 3
			sal.append([nd, (L + 0.6) if wrong else -0.45 * i, -1.0 if wrong else 1.0, "walk", 0.0])
		go("walk")

	func tick(dt: float) -> void:
		var v := 0.05                                          # m/s - langsam (Alpensalamander kriechen gemächlich)
		var all_out := true
		for e in sal:
			var nd: Node3D = e[0]
			var u: float = e[1]
			match str(e[3]):
				"walk":
					u += v * float(e[2]) * dt
					if float(e[2]) < 0.0:                       # the wrong one meets the procession: nose to nose
						for o in sal:
							if o != e and float(o[2]) > 0.0 and absf(float(o[1]) - u) < 0.17 and float(o[1]) < u:
								e[3] = "meet"
								e[4] = 0.0
				"meet":
					e[4] = float(e[4]) + dt
					if float(e[4]) > 3.0:
						e[3] = "turn"
						e[4] = 0.0
				"turn":                                         # turns round and walks along behind the last one
					e[4] = float(e[4]) + dt
					if float(e[4]) > 1.6:
						e[2] = 1.0
						e[3] = "follow"
				"follow":
					var last := 1.0e9
					for o in sal:
						if o != e and float(o[2]) > 0.0:
							last = minf(last, float(o[1]))
					u += v * dt if u < last - 0.2 or u > last else 0.0
			e[1] = u
			if u < L + 0.5:
				all_out = false
			var k := clampf(u / L, -0.2, 1.2)
			var p: Vector3 = a0.lerp(a1, k)
			var dir: Vector3 = (a1 - a0).normalized() * float(e[2])
			var wig := sin(ew._clock * 5.0 + u * 30.0) * 0.006
			var side := Vector3(-dir.z, 0, dir.x)
			var gp: Vector3 = ew.G(p.x + side.x * wig, p.z + side.z * wig)
			nd.position = gp
			var yaw := atan2(-dir.x, -dir.z)
			if str(e[3]) == "turn":
				yaw += PI * (1.0 - float(e[4]) / 1.6)
			nd.rotation = Vector3(0, yaw + sin(ew._clock * 5.0 + u * 30.0) * 0.18, 0)
			nd.visible = u > -0.3 and u < L + 0.3
		if all_out and ew.unseen(ew.W(c), 30.0):              # all over: the next group (quietly, when nobody looks)
			for i in range(sal.size()):
				var w := i == 3
				sal[i][1] = (L + 0.6) if w else -0.45 * i - 2.0
				sal[i][2] = -1.0 if w else 1.0
				sal[i][3] = "walk"

	func crossing() -> bool:
		if not shown:
			return false
		for e in sal:
			if float(e[1]) > 0.0 and float(e[1]) < L:
				return true
		return false


# ---- 21 · only cow bells in the fog - then, suddenly, a cow right in front of MoveEye ---------------------------------------
class Glocken extends Vig:
	var cow
	var tgt := Vector3.ZERO         # where she stops (valley): in front of MoveEye's camera when MoveEye is near, else here
	var from := Vector3.ZERO
	var bell_t := 0.0
	var far_t := 0.0
	var ang := 0.0

	func build() -> void:
		id = "kuhglocken_nebel"
		c = ew.G(20.0, 70.0)

	func when_ok() -> bool:
		return ew.alp_season() and ew.foggy()

	func where() -> Vector3:
		var hp: Vector3 = ew.head_pos()
		return hp if hp.distance_to(ew.W(c)) < 150.0 else ew.W(c)

	func live() -> void:
		cow = ew.actor("cow", c, c + Vector3(0, 0, 1), 0.7)
		actors.append(cow)
		cow.visible = false
		ew.reg_glocken()
		go("bells")

	func _target() -> void:
		var hp: Vector3 = ew.head_pos()
		if hp.distance_to(ew.W(c)) < 150.0:
			var f: Vector3 = ew.head_fwd()
			var w: Vector3 = Vector3(hp.x, 0, hp.z) + f * 4.6
			var v: Vector3 = ew.VL(w)
			tgt = ew.G(v.x, v.z)
		else:
			tgt = c
		ang = randf() * TAU
		var d := Vector3(sin(ang), 0, cos(ang))
		from = ew.G(tgt.x + d.x * 9.0, tgt.z + d.z * 9.0)

	func _bell(p: Vector3, loud := 1.0) -> void:
		var f := randf_range(470.0, 560.0)
		ew.sound(p + Vector3(0, 0.8, 0), "bell", [[0.0, 0.9, f, f, loud], [0.42, 0.8, f * 1.01, f * 1.01, loud * 0.7]], -6.0, -16.0)   # Kuhglocke ≈ 80 dB in 1 m

	func tick(dt: float) -> void:
		bell_t -= dt
		match st:
			"bells":                                           # bells all round, coming nearer - nothing to see
				cow.visible = false
				if st_t < 0.1:
					_target()
				if bell_t <= 0.0:
					bell_t = randf_range(1.2, 2.6)
					var r: float = lerpf(40.0, 12.0, clampf(st_t / 25.0, 0.0, 1.0))
					var a: float = ang + sin(st_t * 0.3) * 0.8
					_bell(ew.G(tgt.x + sin(a) * r, tgt.z + cos(a) * r), 0.6 + 0.4 * clampf(st_t / 25.0, 0.0, 1.0))
				if st_t > 26.0:
					ew.place(cow, from)
					ew.face(cow, tgt - from)
					cow.visible = true
					go("come")
			"come":                                            # out of the fog: three steps and she stands there
				ew.idle(cow, "")
				if bell_t <= 0.0:
					bell_t = 0.7
					_bell(ew.ppos(cow) + Vector3(0, ew.bt.H(tgt.x, tgt.z), 0), 1.0)
				if ew.walk(cow, tgt, 0.9, dt, null, 3.0) or st_t > 15.0:
					go("stare")
			"stare":                                           # looks at MoveEye, chews; bells of the others far away
				ew.stop(cow, dt)
				ew.idle(cow, "stare")
				far_t -= dt
				if far_t <= 0.0:
					far_t = randf_range(3.0, 6.0)
					var a2 := randf() * TAU
					_bell(ew.G(tgt.x + sin(a2) * 30.0, tgt.z + cos(a2) * 30.0), 0.5)
				if st_t > 20.0:
					from = ew.G(tgt.x - sin(ang + 0.7) * 14.0, tgt.z - cos(ang + 0.7) * 14.0)
					ew.idle(cow, "")
					go("leave")
			"leave":
				if bell_t <= 0.0:
					bell_t = 0.8
					_bell(ew.ppos(cow) + Vector3(0, ew.bt.H(tgt.x, tgt.z), 0), 0.8)
				if ew.walk(cow, from, 0.8, dt, null, 2.0) or st_t > 25.0:
					cow.visible = false
					go("gone")
			"gone":
				cow.visible = false
				if st_t > 60.0:
					go("bells")

	func there() -> bool:
		return shown and st == "stare"


# ---- 22 · a chamois on the roof ridge of the hospice: quite at home up there --------------------------------------------------
class Dachgemse extends Vig:
	var g
	var ridge_y := 0.0
	var ends: Array = []
	var to := 0

	func build() -> void:
		id = "gemse_hospizdach"
		c = ew.G(18.0, 790.0)
		ridge_y = c.y + 13.5                                    # bib_berg.gd hospice: walls 10 m, roof 3.5 m (ridge along the valley x here)
		ends = [Vector3(12.8, ridge_y, 790.0), Vector3(23.2, ridge_y, 790.0)]

	func when_ok() -> bool:
		return not ew.dark()

	func where() -> Vector3:
		return ew.W(Vector3(c.x, ridge_y, c.z))

	func live() -> void:
		var p: Vector3 = ends[0]
		g = ew.actor("chamois", p, ends[1], 0.6)
		ew.place(g, p, true)
		actors.append(g)
		go("walk")

	func tick(dt: float) -> void:
		match st:
			"walk":                                            # sure-footed along the ridge, step by step
				ew.idle(g, "")
				if ew.walk(g, ends[to], 0.45, dt, ridge_y, 3.0):
					go("look")
			"look":                                            # at the end: looks down to the parking place (and to MoveEye)
				ew.stop(g, dt)
				ew.idle(g, "stare" if st_t < 7.0 else "look")
				if st_t > 12.0:
					to = 1 - to
					go("lie" if to == 1 and randf() < 0.5 else "walk")
			"lie":                                             # lies down on the ridge like on a ledge, chews
				ew.idle(g, "lie")
				if st_t > 30.0:
					ew.idle(g, "")
					go("walk")

	func up() -> bool:
		return shown


# ---- 23 · the selfie hiker steps back towards the edge of the gorge - a cow nudges him forward (nothing happens to him) -----
class Selfie extends Vig:
	var hk
	var cow
	var e := Vector3(-1, 0, 0)      # towards the gorge (downhill)
	var sd := Vector3(0, 0, 1)
	var start := Vector3.ZERO
	var trail := Vector3.ZERO
	var phone: MeshInstance3D
	var steps := 0

	func build() -> void:
		id = "selfie_kante"
		c = ew.G(64.0, -140.0)
		var gr: Vector2 = ew.bt.grad(c.x, c.z)
		if gr.length() > 0.001:
			e = Vector3(-gr.x, 0, -gr.y).normalized()
		sd = Vector3(-e.z, 0, e.x)
		start = ew.G(c.x - e.x * 2.0, c.z - e.z * 2.0)          # 2 m from the warning sign, never further than 0.8 m to it
		trail = ew.G(50.0, -130.0)

	func when_ok() -> bool:
		return ew.alp_season() and not ew.dark() and not ew.weather() in ["rain", "snow", "fog"]

	func live() -> void:
		hk = ew.actor("person", trail, start, 1.1, Color(0.85, 0.3, 0.12))
		ew.backpack(hk)
		phone = ew.part(ew.forearm(hk, 1), ew.boxm(0.07, 0.14, 0.01), Vector3(0, -0.33, -0.04), Color(0.08, 0.08, 0.1), 32.0)
		var cp: Vector3 = ew.G(c.x - e.x * 6.0 + sd.x * 16.0, c.z - e.z * 6.0 + sd.z * 16.0)
		cow = ew.actor("cow", cp, c, 0.7)
		actors.append(hk)
		actors.append(cow)
		go("arrive")

	func _selfie(on: bool) -> void:
		if on:
			ew.arm(hk, 1, 2.1, 0.25, 0.15)                     # the arm up and forward: the phone looks back at him
		phone.visible = on

	func tick(dt: float) -> void:
		match st:
			"arrive":
				_selfie(false)
				ew.idle(cow, "graze")
				if ew.walk(hk, start, 1.1, dt):
					ew.face(hk, -e)
					steps = 0
					go("selfie")
			"selfie":                                          # a photo, half a step back, another photo …
				ew.idle(hk, "")
				_selfie(true)
				var back: Vector3 = start + e * 0.3 * steps
				ew.walk(hk, back, 0.25, dt, null, 0.5)
				ew.face(hk, -e)
				if st_t > 2.5:
					steps += 1
					st_t = 0.0
					if steps > 4:                              # 1.2 m back - here the cow has seen enough
						go("cow")
				var cw: Vector3 = start + e * 1.2 + sd * 1.3 - e * 0.4
				if steps >= 2:
					ew.idle(cow, "")
					ew.walk(cow, cw, 0.8, dt)
			"cow":
				_selfie(true)
				var cw2: Vector3 = start + e * 1.2 + sd * 1.3 - e * 0.4
				ew.idle(cow, "")
				if ew.walk(cow, cw2, 0.8, dt) or st_t > 10.0:
					ew.face(cow, -sd)
					go("nudge")
			"nudge":                                           # a push with the head - he stumbles forward, away from the edge
				ew.idle(cow, "graze" if st_t < 0.4 else "")
				if st_t < 0.1:
					hk.startle_until = hk.now_s() + 0.9
				_selfie(false)
				ew.walk(hk, start - e * 0.6, 1.6, dt, null, 0.3)
				if st_t > 1.2:
					go("turn")
			"turn":
				ew.stop(hk, dt)
				ew.turn_to(hk, ew.ppos(cow) - ew.ppos(hk), dt, 2.0)
				ew.idle(cow, "stare")
				if st_t > 2.5:
					go("duo")
			"duo":                                             # then: a selfie with the cow (with his back to the meadow, not to the edge)
				ew.turn_to(hk, -e + sd * 0.6, dt, 2.0)
				_selfie(true)
				ew.idle(cow, "stare")
				if st_t > 7.0:
					_selfie(false)
					go("leave")
			"leave":
				ew.idle(cow, "graze")
				if ew.walk(hk, trail, 1.1, dt) or st_t > 30.0:
					go("done")
			"done":
				if st_t > 40.0 and ew.unseen(ew.W(c), 60.0):
					ew.place(hk, trail)
					ew.place(cow, ew.G(c.x - e.x * 6.0 + sd.x * 16.0, c.z - e.z * 6.0 + sd.z * 16.0))
					go("arrive")

	func happening() -> bool:
		return shown and st in ["cow", "nudge", "turn", "duo"]


# ---- 24 · the trail runner asks the signpost - waits for an answer, runs the wrong way, comes back ---------------------------
class Trailrunner extends Vig:
	var r
	var from := Vector3.ZERO
	var at := Vector3.ZERO
	var wrong := Vector3.ZERO
	var right := Vector3.ZERO

	func build() -> void:
		id = "trailrunner"
		c = ew.G(-200.0, -330.0)                                 # the signpost at the Gumpisee (Seeweg / Moorweg)
		from = ew.G(-150.0, -230.0)
		at = ew.G(-198.6, -328.4)
		wrong = ew.G(-216.0, -325.0)
		right = ew.G(-205.0, -380.0)

	func when_ok() -> bool:
		return not ew.dark() and ew.weather() != "snow"

	func live() -> void:
		r = ew.actor("jogger", from, c, 2.6, Color(0.1, 0.55, 0.75))
		actors.append(r)
		go("run")

	func _on_spot() -> void:
		r.cur_speed = 1.7                                       # running on the spot (the legs keep going)

	func tick(dt: float) -> void:
		match st:
			"run":
				if ew.walk(r, at, 2.8, dt):
					go("ask")
			"ask":                                             # looks up at the arms, points at one - and waits for the answer
				_on_spot()
				ew.turn_to(r, c - at, dt, 4.0)
				if st_t > 1.0 and st_t < 3.5:
					ew.arm(r, 1, 1.75, 0.15, 0.1)
				ew.idle(r, "look" if st_t > 4.0 else "")
				if st_t > 7.5:
					ew.idle(r, "")
					go("wrong")
			"wrong":                                           # off the wrong way …
				if ew.walk(r, wrong, 2.6, dt) or st_t > 12.0:
					go("doubt")
			"doubt":                                           # … stops, jogs on the spot, looks back at the sign
				_on_spot()
				ew.turn_to(r, c - ew.ppos(r), dt, 3.0)
				if st_t > 3.0:
					go("back")
			"back":
				if ew.walk(r, at, 2.6, dt):
					go("thanks")
			"thanks":                                          # a short nod to the signpost - and off the right way
				_on_spot()
				ew.turn_to(r, c - at, dt, 4.0)
				ew.arm(r, 1, 0.9 if st_t < 1.2 else 0.0, 1.6, 0.0)
				if st_t > 2.0:
					go("off")
			"off":
				if ew.walk(r, right, 2.8, dt) or st_t > 30.0:
					r.visible = false
					go("gone")
			"gone":
				r.visible = false
				if st_t > 50.0 and ew.unseen(ew.W(from), 80.0):
					ew.place(r, from)
					r.visible = true
					go("run")

	func asking() -> bool:
		return shown and st in ["ask", "thanks", "doubt"]


# ---- 25 · a guest of the self-catering hut sweeps the veranda - a gust blows it all back -------------------------------------
class Fegen extends Vig:
	var gst
	var bits: Array = []            # [mesh, start, now, from (gust), to (gust)]
	var broom: Node3D
	var edge := Vector3.ZERO
	var rounds := 0
	var with_wind := false

	func build() -> void:
		id = "huettenwart"
		c = ew.G(61.5, -5.2)                                     # in front of the door (bib alp_hut: the door is on the north side)

	func when_ok() -> bool:
		return not ew.dark() and not ew.weather() in ["rain", "snow"]

	func live() -> void:
		edge = ew.G(65.8, -5.4)
		var col := Color(0.82, 0.6, 0.16)                       # Herbst: Lärchennadeln
		var tk = "tree"
		match str(ew.season):
			"sommer":
				col = Color(0.72, 0.66, 0.36)                     # Heu
			"fruehling":
				col = Color(0.42, 0.32, 0.2)                      # dürres Laub vom Winter
			"winter":
				col = Color(0.95, 0.96, 0.98)                     # Schnee
				tk = "snow"
		for i in range(5 if ew.lite else 11):
			var p: Vector3 = ew.G(60.0 + randf() * 3.5, -4.6 - randf() * 1.6, 0.02)
			var mi: MeshInstance3D = ew.part(vroot, ew.boxm(0.06 + randf() * 0.05, 0.012, 0.03 + randf() * 0.03), p, col, tk, Vector3(0, randf() * TAU, 0))
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			bits.append([mi, p, p, p, p])
		gst = ew.actor("person", c, edge, 0.6, Color(0.3, 0.42, 0.25))
		broom = ew.node(ew.forearm(gst, 1), Vector3(0, -0.3, 0))
		ew.part(broom, ew.cylm(0.013, 0.013, 1.25, 6), Vector3(0, -0.45, -0.05), Color(0.55, 0.4, 0.22), "tree", Vector3(0.25, 0, 0))
		ew.part(broom, ew.boxm(0.34, 0.1, 0.1), Vector3(0, -1.05, -0.2), Color(0.62, 0.5, 0.25), "tree", Vector3(0.25, 0, 0))
		actors.append(gst)
		go("sweep")

	func _put_bit(b: Array, p: Vector3) -> void:
		b[2] = p
		ew.set_tf(b[0], Transform3D((b[0] as MeshInstance3D).transform.basis, p))

	func tick(dt: float) -> void:
		match st:
			"sweep":                                           # sweeps it all to the edge of the veranda
				ew.idle(gst, "bend")
				var tgt: Vector3 = ew.G(61.0 + minf(st_t * 0.35, 3.6), -5.2)
				ew.walk(gst, tgt, 0.4, dt, null, 3.0)
				ew.face(gst, edge - c)
				ew.arm(gst, 1, 0.55 + 0.3 * sin(st_t * 3.2), 0.35)
				ew.arm(gst, -1, 0.75 + 0.3 * sin(st_t * 3.2), 0.6)
				if fmod(st_t, 1.0) < dt:
					ew.sound(ew.ppos(gst) + Vector3(0, c.y, 0), "swish", [[0.0, 0.45, 300.0, 300.0, 0.6]], -14.0, -40.0)
				var gx: float = ew.ppos(gst).x + 0.9
				for b in bits:
					var p: Vector3 = b[2]
					if p.x < gx:
						var q: Vector3 = p.lerp(edge + Vector3(0, 0.02, randf_range(-0.3, 0.3)), minf(1.0, dt * 1.4))
						_put_bit(b, q)
				if st_t > 11.0:
					rounds += 1
					if with_wind:
						go("done")
					else:
						for b in bits:
							b[3] = b[2]
							b[4] = ew.G(60.0 + randf() * 3.6, -4.5 - randf() * 1.8, 0.02)
						ew.sound(edge + Vector3(0, 1.0, 0), "swish", [[0.0, 2.2, 200.0, 200.0, 1.0]], -8.0, -30.0)
						go("gust")
			"gust":                                            # the wind (west, up the valley) blows it back onto the boards
				ew.idle(gst, "")
				ew.stop(gst, dt)
				var k: float = clampf(st_t / 2.4, 0.0, 1.0)
				for b in bits:
					var a: Vector3 = b[3]
					var z: Vector3 = b[4]
					var q: Vector3 = a.lerp(z, k) + Vector3(0, sin(k * PI) * (0.6 + 0.4 * fmod(a.x * 13.0, 1.0)), 0)
					_put_bit(b, q)
					(b[0] as MeshInstance3D).rotation.y += dt * 6.0
				if st_t > 2.6:
					go("look")
			"look":                                            # looks at the boards, then into the wind
				ew.stop(gst, dt)
				ew.idle(gst, "look")
				if st_t > 1.5:
					ew.turn_to(gst, Vector3(1, 0, 0), dt, 1.5)
				if st_t > 5.0:
					ew.idle(gst, "")
					ew.place(gst, c)
					with_wind = rounds >= 2                         # the third time: he sweeps the other way, with the wind
					if with_wind:
						edge = ew.G(59.0, -5.6)
					go("sweep")
			"done":                                            # clean: leans on the broom
				ew.idle(gst, "look")
				ew.stop(gst, dt)
				ew.arm(gst, 1, 0.35, 0.2)
				if st_t > 25.0 and ew.unseen(ew.W(c), 40.0):
					rounds = 0
					with_wind = false
					edge = ew.G(65.8, -5.4)
					for b in bits:
						_put_bit(b, ew.G(60.0 + randf() * 3.5, -4.6 - randf() * 1.6, 0.02))
					ew.place(gst, c)
					go("sweep")

	func blown() -> bool:
		return shown and st in ["gust", "look"]


# ---- 26 · picnic: where is the corkscrew? (it is stuck in the band of his hat) -----------------------------------------------
class Picknick extends Vig:
	var man
	var wom
	var hat_on: Node3D
	var hat_hand: Node3D
	var screw: Node3D
	var bottle: MeshInstance3D
	var bs := Basis()
	var basket := Vector3.ZERO

	func build() -> void:
		id = "picknick"
		c = ew.G(-10.0, -296.0)
		bs = Basis(Vector3.UP, 0.4)                               # bergtal.gd: picnic_set at (-10, -296), turned 0.4
		basket = c + bs * Vector3(0.4, 0, 0.2)

	func when_ok() -> bool:
		return ew.season != "winter" and not ew.dark() and not ew.weather() in ["rain", "snow", "fog"]

	func _hat(parent: Node3D, p: Vector3, with_screw: bool) -> Node3D:
		var h: Node3D = ew.node(parent, p)
		var brown := Color(0.42, 0.33, 0.2)
		ew.part(h, ew.cylm(0.17, 0.17, 0.012, 16), Vector3.ZERO, brown, 27.0)
		ew.part(h, ew.cylm(0.105, 0.115, 0.09, 14), Vector3(0, 0.045, 0), brown, 27.0)
		ew.part(h, ew.cylm(0.117, 0.117, 0.022, 14), Vector3(0, 0.017, 0), Color(0.15, 0.1, 0.08), 27.0)
		if with_screw:                                         # Kellnermesser-Korkenzieher, im Hutband eingesteckt
			screw = ew.node(h, Vector3(0.112, 0.03, 0.03), 0.0)
			ew.part(screw, ew.boxm(0.012, 0.016, 0.1), Vector3(0, 0.0, 0), Color(0.55, 0.3, 0.15), "tree", Vector3(0.3, 0, 0))
			ew.part(screw, ew.cylm(0.004, 0.004, 0.05, 5), Vector3(0.006, -0.02, 0.03), Color(0.8, 0.8, 0.82), "metal", Vector3(0.5, 0, 0))
		return h

	func live() -> void:
		man = ew.actor("person", c + bs * Vector3(0.9, 0, -0.9), basket, 0.8, Color(0.55, 0.62, 0.7))
		wom = ew.actor("person", c + bs * Vector3(-0.35, 0, -0.25), basket, 0.8, Color(0.75, 0.25, 0.35))
		hat_on = _hat(man.head, Vector3(0, 0.22, 0), true)
		hat_hand = _hat(ew.forearm(man, 1), Vector3(0, -0.36, -0.08), false)
		hat_hand.rotation.x = PI / 2
		hat_hand.visible = false
		bottle = ew.part(ew.forearm(wom, 1), ew.cylm(0.035, 0.037, 0.3, 8), Vector3(0, -0.36, -0.02), Color(0.18, 0.35, 0.18), "stone")
		actors.append(man)
		actors.append(wom)
		go("search")

	func tick(dt: float) -> void:
		wom.crouch = 0.85                                       # she kneels on the blanket, the bottle in her hand
		ew.face(wom, ew.ppos(man) - ew.ppos(wom))
		ew.arm(wom, 1, 0.9 if st != "open" else 1.5, 0.9)
		ew.idle(wom, "")
		match st:
			"search":                                          # in the basket … the pockets … around … the basket again
				var ph: float = fmod(st_t, 20.0)
				if ph < 5.0:
					ew.idle(man, "bend")
					ew.turn_to(man, basket - ew.ppos(man), dt, 3.0)
				elif ph < 9.0:
					ew.idle(man, "")
					var pat: float = 0.35 if fmod(st_t, 0.8) < 0.4 else 0.1
					ew.arm(man, 1, pat, 1.5)
					ew.arm(man, -1, 0.45 - pat, 1.5)
				elif ph < 13.0:
					ew.idle(man, "look")
				elif ph < 16.0:
					ew.idle(man, "bend")
				else:
					ew.idle(man, "")
					ew.arm(man, 1, 2.6, 2.3)                     # scratches his head - right beside the hat …
				if st_t > 36.0:
					go("found")
			"found":                                           # … takes off the hat to wipe his forehead - there it is
				ew.idle(man, "")
				hat_on.visible = st_t < 0.8
				hat_hand.visible = st_t >= 0.8
				ew.arm(man, 1, 2.4 if st_t < 0.8 else 1.2, 2.2 if st_t < 0.8 else 1.4)
				if st_t > 1.0:
					ew.arm(man, -1, 1.1, 1.2)
				if st_t > 3.5:
					go("open")
			"open":                                            # opens the bottle; the hat goes back on
				hat_on.visible = st_t > 2.0
				hat_hand.visible = st_t <= 2.0
				screw.visible = st_t <= 0.5
				ew.turn_to(man, ew.ppos(wom) - ew.ppos(man), dt, 3.0)
				ew.arm(man, 1, 1.0, 1.0)
				ew.arm(man, -1, 1.0, 1.0)
				if fmod(st_t, 3.0) < dt and st_t < 4.0:
					ew.sound(ew.ppos(wom) + Vector3(0, c.y + 0.8, 0), "plop", [[0.0, 0.12, 900.0, 300.0, 1.0]], -10.0, -40.0)   # der Korken
				if st_t > 6.0:
					go("cheers")
			"cheers":
				ew.idle(man, "")
				if st_t > 30.0 and ew.unseen(ew.W(c), 50.0):
					screw.visible = true
					hat_on.visible = true
					hat_hand.visible = false
					go("search")

	func looking() -> bool:
		return shown and st in ["search", "found"]


# ---- 27 · a paraglider lands on the cow pasture - the cows come to look at the canopy -------------------------------------
class Gleitschirm extends Vig:
	var pilot
	var cows: Array = []
	var wing: Node3D
	var lines: Array = []
	var cells: Array = []
	var land := Vector3.ZERO
	var centre := Vector3.ZERO
	var ground_wing := Vector3.ZERO
	var alt := 0.0
	var a := 0.0
	var pos := Vector3.ZERO
	var road := Vector3.ZERO
	const SINK := 1.2               # m/s (Gleitschirm im Trimm: Sinken ≈ 1,1–1,3 m/s, ≈ 36 km/h - Herstellerangaben, z. B. EN-B-Schirme)
	const SPEED := 10.0

	func build() -> void:
		id = "gleitschirm"
		c = ew.G(135.0, 85.0)
		land = c
		centre = c + Vector3(30.0, 0, -20.0)
		ground_wing = ew.G(c.x + 7.0, c.z + 0.5)
		road = ew.G(176.0, 40.0)

	func when_ok() -> bool:
		return not ew.dark() and ew.weather() in ["clear", "cloudy"] and float(ew.m.wind) < 25.0

	func live() -> void:
		wing = ew.node(vroot, c)
		for i in range(9):                                     # the canopy: 9 cells in an arc, ≈ 10 m wide
			var aa := lerpf(-0.95, 0.95, i / 8.0)
			var col := Color(0.91, 0.35, 0.1) if i % 3 != 1 else Color(0.16, 0.35, 0.69)
			var mi: MeshInstance3D = ew.part(wing, ew.boxm(1.25, 0.2, 2.4 - absf(aa) * 0.5), Vector3(sin(aa) * 5.0, cos(aa) * 2.0 - 2.0, 0), col, "tent", Vector3(0, 0, -aa))
			cells.append([mi, Vector3(sin(aa) * 5.0, cos(aa) * 2.0 - 2.0, 0), aa])
		pilot = ew.actor("person", c, c + Vector3(-1, 0, 0), 1.0, Color(0.9, 0.85, 0.2))
		ew.backpack(pilot, Color(0.2, 0.2, 0.22))                 # the harness with the reserve
		actors.append(pilot)
		if not ew.lite:
			for sx in [-1.0, 1.0]:
				lines.append([ew.rod(vroot, c, c + Vector3(0, 1, 0), 0.006, Color(0.85, 0.85, 0.8), "tent"), sx])
		if ew.alp_season():
			for i in range(2):
				var cp: Vector3 = ew.G(c.x - 25.0 + i * 8.0, c.z + 22.0 - i * 6.0)
				var cw = ew.actor("cow", cp, c, 0.6)
				cows.append(cw)
				actors.append(cw)
		go("wait")

	func _fly_pose(p: Vector3, dir: Vector3, bank: float) -> void:
		var b := Basis.looking_at(Vector3(dir.x, 0, dir.z).normalized(), Vector3.UP) * Basis(Vector3(0, 0, 1), bank)
		wing.transform = Transform3D(b, p + Vector3(0, 7.5, 0))
		ew.place(pilot, p, true)
		ew.face(pilot, dir)
		pilot.cur_speed = 0.0
		for ln in lines:
			var tip: Vector3 = wing.transform * Vector3(float(ln[1]) * 3.2, -0.8, 0)
			ew.set_rod(ln[0], p + Vector3(float(ln[1]) * 0.2, 1.5, 0), tip)

	func tick(dt: float) -> void:
		for cw in cows:
			if st in ["wait", "fly", "final"]:
				ew.idle(cw, "graze")
		match st:
			"wait":                                            # high above the alp it starts circling down
				alt = 160.0
				a = 0.0
				wing.visible = false
				pilot.visible = false
				for ln in lines:
					(ln[0] as MeshInstance3D).visible = false
				if st_t > 5.0:
					wing.visible = true
					pilot.visible = true
					for ln in lines:
						(ln[0] as MeshInstance3D).visible = true
					go("fly")
			"fly":                                             # spirals down (sink ≈ 1,2 m/s), the circles get smaller
				alt -= SINK * dt
				var R: float = lerpf(25.0, 60.0, clampf(alt / 160.0, 0.0, 1.0))
				a += SPEED / R * dt
				pos = centre + Vector3(cos(a) * R, alt, sin(a) * R)
				_fly_pose(pos, Vector3(-sin(a), 0, cos(a)), -0.35)
				if alt < 30.0 and cos(a) > 0.9:
					go("final")
			"final":                                           # into the wind (west) onto the meadow, flare at the end
				var p0: Vector3 = Vector3(pos.x, 0, pos.z)
				var d := Vector3(land.x - p0.x, 0, land.z - p0.z)
				var L := d.length()
				var sp: float = SPEED * (0.4 if L < 12.0 else 1.0)
				alt = maxf(0.0, alt - (alt / maxf(L / sp, 0.5)) * dt)
				var np: Vector3 = p0 + d / maxf(L, 0.01) * minf(sp * dt, L)
				pos = Vector3(np.x, ew.bt.H(np.x, np.z) + alt, np.z)
				_fly_pose(pos, d, 0.0)
				if L < 0.3 or st_t > 30.0:
					ew.sound(land + Vector3(0, 0.3, 0), "thud", [[0.0, 0.15, 80.0, 60.0, 0.6]], -16.0, -50.0)
					ew.place(pilot, land)
					go("drop")
			"drop":                                            # the canopy falls down behind him and lies on the grass
				var k: float = clampf(st_t / 2.5, 0.0, 1.0)
				var b0 := Basis.looking_at(Vector3(-1, 0, 0), Vector3.UP)
				var b1 := b0 * Basis(Vector3(1, 0, 0), -PI / 2.0)
				var p1: Vector3 = ground_wing + Vector3(0, 0.15, 0)
				wing.transform = Transform3D(b0.slerp(b1, k), (land + Vector3(0, 7.5, 0)).lerp(p1, k))
				for ln in lines:
					ew.set_rod(ln[0], land + Vector3(0, 1.4 - k, 0), wing.transform * Vector3(float(ln[1]) * 3.2, -0.8, 0))
				ew.idle(pilot, "")
				ew.stop(pilot, dt)
				if st_t > 3.0:
					go("cows")
			"cows":                                            # the cows come over and sniff the strange big thing
				ew.idle(pilot, "look")
				for i in range(cows.size()):
					var tgt: Vector3 = ground_wing + Vector3(-1.5 + i * 3.0, 0, 3.2 - i * 6.4)
					if ew.walk(cows[i], tgt, 0.6, dt, null, 2.0):
						ew.idle(cows[i], "sniff")
				if st_t > (35.0 if not cows.is_empty() else 6.0):
					go("pack")
			"pack":                                            # he gathers the canopy into a bundle
				ew.idle(pilot, "bend")
				var k2: float = clampf(st_t / 12.0, 0.0, 1.0)
				var s3: float = lerpf(1.0, 0.1, k2)
				wing.transform = Transform3D(wing.transform.basis.orthonormalized() * Basis.from_scale(Vector3(s3, 1.0, s3)), ground_wing.lerp(land, k2) + Vector3(0, 0.15 + 0.25 * k2, 0))
				for ln in lines:
					(ln[0] as MeshInstance3D).visible = k2 < 0.5
				for cw in cows:
					ew.idle(cw, "graze")
				if st_t > 13.0:
					go("away")
			"away":
				ew.idle(pilot, "")
				pilot.carry = true
				wing.visible = false
				if ew.walk(pilot, road, 1.1, dt) or st_t > 60.0:
					pilot.visible = false
					go("gone")
			"gone":
				pilot.visible = false
				pilot.carry = false
				if st_t > 90.0 and ew.unseen(ew.W(c), 120.0):
					go("wait")

	func flying() -> bool:
		return shown and st in ["final", "drop", "cows"]


# ---- 28 · the Postauto in the hairpins of the pass road: the three-tone horn before the blind bend --------------------------
class Postauto extends Vig:
	var bus: Node3D
	var pts: Array = []             # [valley point on the road, cumulative distance]
	var total := 0.0
	var dist := 0.0
	var dirn := 1.0
	var horn_at := 0.0
	var horned := false
	var horn_clock := -100.0
	var prev_d := 0.0
	const V := 7.0                  # m/s ≈ 25 km/h in the hairpins

	func build() -> void:
		id = "postauto"
		c = ew.G(175.0, 300.0)
		var Bt = ew.bt.get_script()
		var rp: PackedVector2Array = Bt.road_pts
		var rh: PackedFloat32Array = Bt.road_h
		if rp.size() < 10:
			return
		var k: int = ew.bt._road_index_near(Vector2(175.0, 300.0))
		var i0 := maxi(0, k - 90)
		var i1 := mini(rp.size() - 1, k + 90)
		var acc := 0.0
		var prev := Vector3.ZERO
		for i in range(i0, i1 + 1):
			var y: float = rh[mini(i, rh.size() - 1)] if rh.size() > 0 else ew.bt.H(rp[i].x, rp[i].y)
			var q := Vector3(rp[i].x, y, rp[i].y)
			if i > i0:
				acc += q.distance_to(prev)
			if i == k:
				horn_at = acc
			pts.append([q, acc])
			prev = q
		total = acc
		c = Vector3(rp[k].x, prev.y, rp[k].y)
		c.y = (pts[k - i0][0] as Vector3).y

	func when_ok() -> bool:
		var h: float = ew.hour()
		return ew.season != "winter" and h > 6.5 and h < 21.0 and total > 50.0   # Pass im Winter gesperrt; Fahrplan tagsüber

	func live() -> void:
		# Postauto (gelber Reisebus 12 m) wie in bib_berg.gd - hier ein eigener, der fährt
		bus = ew.node(vroot, c)
		var Lb := 12.0
		ew.part(bus, ew.boxm(Lb, 2.6, 2.5), Vector3(0, 1.7, 0), Color(0.96, 0.77, 0.0), "car")
		ew.part(bus, ew.boxm(Lb - 0.6, 0.9, 2.52), Vector3(0.1, 2.3, 0), Color(0.16, 0.22, 0.29), "car")
		ew.part(bus, ew.boxm(0.08, 1.6, 2.3), Vector3(Lb / 2.0 + 0.02, 2.0, 0), Color(0.16, 0.22, 0.29), "car")
		ew.part(bus, ew.boxm(Lb, 0.35, 2.52), Vector3(0, 0.55, 0), Color(0.16, 0.16, 0.16), "car")
		ew.part(bus, ew.boxm(Lb, 0.12, 2.54), Vector3(0, 1.25, 0), Color(0.78, 0.06, 0.18), "car")
		ew.part(bus, ew.boxm(0.5, 0.4, 0.8), Vector3(-Lb / 2.0 + 0.3, 1.0, 0), Color(0.35, 0.35, 0.35), 60.0)   # Motor hinten: warm
		for x in [-Lb * 0.32, Lb * 0.32]:
			for z in [-1.15, 1.15]:
				ew.part(bus, ew.cylm(0.5, 0.5, 0.3, 12), Vector3(x, 0.5, z), Color(0.1, 0.1, 0.1), "car", Vector3(PI / 2, 0, 0))
		var gm = ew.glow_mat(Color(1.0, 0.96, 0.85), 3.0)
		for z in [-0.9, 0.9]:
			ew.light_part(bus, ew.sphm(0.12), Vector3(Lb / 2.0 + 0.06, 1.0, z), gm)
		go("pause")

	func _at(d: float) -> Array:
		"""[point, direction] at distance d along the road piece"""
		var lo := 0
		var hi := pts.size() - 1
		while hi - lo > 1:
			var mid := (lo + hi) / 2
			if float(pts[mid][1]) < d:
				lo = mid
			else:
				hi = mid
		var a: Vector3 = pts[lo][0]
		var b: Vector3 = pts[hi][0]
		var seg: float = maxf(float(pts[hi][1]) - float(pts[lo][1]), 0.001)
		return [a.lerp(b, clampf((d - float(pts[lo][1])) / seg, 0.0, 1.0)), (b - a).normalized()]

	func tick(dt: float) -> void:
		match st:
			"pause":
				bus.visible = false
				if st_t > 150.0 or (st_t > 8.0 and horn_clock < -50.0):
					dirn = -dirn
					dist = 0.0 if dirn > 0.0 else total
					horned = false
					bus.visible = true
					go("drive")
			"drive":
				prev_d = dist
				dist += V * dirn * dt
				var r := _at(dist)
				var p: Vector3 = r[0]
				var d: Vector3 = r[1] * dirn
				bus.position = p
				bus.rotation = Vector3(0, atan2(d.x, d.z) - PI / 2.0, atan2(d.y, Vector2(d.x, d.z).length()))
				# Dreiklang «Tü-ta-to» cis–e–a (aus Rossinis Wilhelm-Tell-Ouvertüre); auf Bergpoststrassen vor unübersichtlichen
				# Kurven - 25 m vor der Kehre. Laut: ≈ 105 dB in 1 m (wie bergtal.gd postauto_horn)
				var hp: float = horn_at - 25.0 * dirn
				if not horned and (prev_d - hp) * (dist - hp) <= 0.0:
					horned = true
					horn_clock = ew._clock
					ew.sound(p + Vector3(0, 2.0, 0), "horn", [[0.0, 0.42, 554.37, 554.37, 1.0], [0.47, 0.42, 659.26, 659.26, 1.0], [0.94, 0.75, 440.0, 440.0, 1.0]], 0.0, -1.0)
				if dist < -1.0 or dist > total + 1.0:
					bus.visible = false
					go("pause")

	func honked() -> bool:
		return shown and st == "drive" and ew._clock - horn_clock < 10.0


# ---- 29 · the smugglers' route: scratched marks on the stones - only to see in the low evening light - to a hiding place ----
class Schmuggler extends Vig:
	var marks: Array = []
	var start := Vector3.ZERO
	var k := 0.0

	func build() -> void:
		id = "schmuggler"
		c = ew.G(360.0, 720.0)
		start = ew.G(300.0, 668.0)

	func live() -> void:
		# Schmuggel über die Pässe nach Italien (Kaffee, Tabak, Zigaretten; «Spalloni», bis in die 1970er): die Wege waren mit
		# kleinen Kerben markiert. Hier: Kreuz-Kerben an 8 Steinen, die man nur im flachen Abendlicht sieht.
		for i in range(8):
			var t := (i + 0.5) / 8.0
			var q: Vector3 = start.lerp(c, t) + Vector3(sin(i * 2.1) * 2.5, 0, cos(i * 1.7) * 2.5)
			var g: Vector3 = ew.G(q.x, q.z)
			ew.part(vroot, ew.sphm(0.45, 0.6, 8), g + Vector3(0, 0.15, 0), Color(0.5, 0.48, 0.44), "stone")
			var face: Vector3 = (start - c).normalized()
			var n: Node3D = ew.node(vroot, g + Vector3(0, 0.3, 0) + face * 0.43, atan2(face.x, face.z))
			for rz in [0.7, -0.7]:
				var mi: MeshInstance3D = ew.part(n, ew.boxm(0.2, 0.025, 0.012), Vector3.ZERO, Color(0.86, 0.8, 0.66), "stone", Vector3(0, 0, rz))
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				marks.append(mi)
		# the hiding place: a slab leaning against a block - under it an old wooden box
		ew.part(vroot, ew.sphm(0.9, 1.3, 8), c + Vector3(0.8, 0.4, 0.3), Color(0.47, 0.46, 0.42), "stone")
		ew.part(vroot, ew.boxm(1.1, 0.08, 0.8), c + Vector3(-0.1, 0.45, 0.2), Color(0.52, 0.5, 0.46), "stone", Vector3(0, 0.3, 0.55))
		ew.part(vroot, ew.boxm(0.5, 0.3, 0.34), c + Vector3(-0.2, 0.15, 0.2), Color(0.36, 0.26, 0.16), "tree", Vector3(0, 0.3, 0))
		var lb := Label3D.new()
		lb.text = "CAFFÈ"
		lb.font_size = 40
		lb.pixel_size = 0.0018
		lb.modulate = Color(0.75, 0.68, 0.55)
		lb.outline_size = 0
		lb.position = c + Vector3(-0.2, 0.18, 0.2) + Basis(Vector3.UP, 0.3) * Vector3(0, 0, 0.175)
		lb.rotation.y = 0.3
		vroot.add_child(lb)
		_show(0.0)

	func _show(v: float) -> void:
		for mi in marks:
			ew.show_part(mi, v > 0.05)

	func tick(dt: float) -> void:
		var want: float = ew.evening_light()
		k = move_toward(k, want, dt * 0.2)
		_show(k)

	func visible_marks() -> bool:
		return shown and k > 0.3


# ---- 30 · the cairn forest: one of the cairns has eyes - they follow you, and close when you come too near ---------------------
class Augen extends Vig:
	var eyes: Node3D
	var lids: Array = []
	var blink_t := 4.0
	var shut := false
	var eye_c := Vector3.ZERO

	func build() -> void:
		id = "steinmann_wald"
		c = ew.G(-644.0, 426.0)

	func live() -> void:
		var h := 1.25                                            # a cairn like bib_berg.gd (5 stones) …
		var y := 0.0
		var r := 0.42 * h
		for i in range(5):
			ew.part(vroot, ew.sphm(r, r * 0.9, 9), c + Vector3(0.03 * sin(i * 2.0), y + r * 0.4, 0.03 * cos(i * 2.3)), [Color(0.49, 0.48, 0.45), Color(0.56, 0.54, 0.51), Color(0.42, 0.41, 0.38)][i % 3], "stone")
			if i == 3:
				eye_c = c + Vector3(0, y + r * 0.45, 0)
				eyes = ew.node(vroot, eye_c)
				for sx in [-1.0, 1.0]:                          # … with two eyes (stone-grey lids, a white pebble, a dark pupil)
					var e: Node3D = ew.node(eyes, Vector3(sx * r * 0.36, 0.0, -r * 0.82))
					ew.part(e, ew.sphm(0.04, 0.05, 8), Vector3.ZERO, Color(0.9, 0.89, 0.85), "stone")
					ew.part(e, ew.sphm(0.02, 0.025, 6), Vector3(0, 0, -0.03), Color(0.05, 0.05, 0.05), "stone")
					lids.append(e)
			y += r * 0.75
			r *= 0.72
		go("watch")

	func tick(dt: float) -> void:
		var v: Vector3 = ew.VL(ew.view_pos())
		var d := v - eye_c
		var near := Vector2(d.x, d.z).length()
		if near < 25.0:                                         # turn slowly to the one who looks
			var want := atan2(-d.x, -d.z)
			eyes.rotation.y = rotate_toward(eyes.rotation.y, want, dt * 0.8)
		blink_t -= dt
		shut = near < 3.5                                        # too near: shy - eyes shut, just a cairn
		var lid := 0.1 if shut or (blink_t < 0.14 and blink_t > 0.0) else 1.0
		if blink_t <= 0.0:
			blink_t = randf_range(3.5, 7.0)
		for e in lids:
			(e as Node3D).scale.y = move_toward((e as Node3D).scale.y, lid, dt * 12.0)

	func open() -> bool:
		return shown and not shut


# ---- 31 · the abandoned dairy: in the ancient cheese wheel lives a mouse --------------------------------------------------------
class Sennerei extends Vig:
	var mouse: Node3D
	var kid: Node3D
	var top := Vector3.ZERO
	var hole := Vector3.ZERO
	var nrm := Vector3.ZERO
	var phi := 0.0

	func build() -> void:
		id = "sennerei"
		c = ew.G(-698.5, -127.0)                                 # bergtal.gd: the cheese wheel in front of the old dairy

	func live() -> void:
		var base: Vector3 = c + Vector3(0, 0.02, 0)
		top = base + Vector3(0, 0.125, 0)
		var v: Vector3 = ew.G(-700.0, -150.0)                   # the hole looks towards the path
		phi = atan2(v.x - c.x, v.z - c.z)
		nrm = Vector3(sin(phi), 0, cos(phi))
		hole = base + Vector3(0, 0.055, 0) + nrm * 0.3
		ew.part(vroot, ew.cylm(0.026, 0.026, 0.012, 8), hole, Color(0.12, 0.09, 0.05), "tent", Vector3(PI / 2, phi, 0))
		ew.part(vroot, ew.cylm(0.018, 0.018, 0.012, 8), top + Vector3(0.1, 0.001, -0.06), Color(0.12, 0.09, 0.05), "tent")
		var lb := Label3D.new()                                 # the old brand on the rind
		lb.text = "1897"
		lb.font_size = 32
		lb.pixel_size = 0.0014
		lb.modulate = Color(0.45, 0.3, 0.12)
		lb.outline_size = 0
		var a2 := phi + 0.9
		lb.position = base + Vector3(0, 0.07, 0) + Vector3(sin(a2), 0, cos(a2)) * 0.302
		lb.rotation.y = a2
		vroot.add_child(lb)
		mouse = _mouse(vroot, 1.0)
		kid = _mouse(vroot, 0.7)
		mouse.visible = false
		kid.visible = false
		go("in")

	func _mouse(par: Node3D, sc: float) -> Node3D:
		# Maus (Apodemus / Mus): Fell-Oberfläche im Wärmebild ≈ 30 °C (wie die Maus im Ferienpark, erlebniswelt.gd)
		var n: Node3D = ew.node(par, c)
		var col := Color(0.45, 0.38, 0.3)
		ew.part(n, ew.sphm(0.025 * sc, 0.03 * sc, 8), Vector3(0, 0.014 * sc, 0.0), col, 30.0, Vector3.ZERO, Vector3(1, 1, 1.6))
		ew.part(n, ew.sphm(0.015 * sc, 0.02 * sc, 6), Vector3(0, 0.018 * sc, 0.04 * sc), col, 31.0)
		for sx in [-1.0, 1.0]:
			ew.part(n, ew.sphm(0.008 * sc), Vector3(sx * 0.009 * sc, 0.032 * sc, 0.034 * sc), Color(0.6, 0.45, 0.42), 29.0)
		ew.part(n, ew.cylm(0.002, 0.003, 0.07 * sc, 4), Vector3(0, 0.01, -0.07 * sc), Color(0.55, 0.45, 0.42), 26.0, Vector3(PI / 2, 0, 0))
		return n

	func tick(dt: float) -> void:
		var vd: float = ew.view_pos().distance_to(ew.W(c))
		match st:
			"in":
				mouse.visible = false
				kid.visible = st_t > 4.0 and st_t < 6.0 and vd > 2.5   # sometimes the young one looks out at the top
				if kid.visible:
					kid.position = top + Vector3(0.1, -0.02 + 0.02 * minf(1.0, (st_t - 4.0) * 4.0), -0.06)
					kid.rotation.y = phi + sin(st_t * 3.0)
				if st_t > 9.0 and vd > 2.5:
					go("peek")
			"peek":                                            # the nose first, looks left and right
				mouse.visible = true
				var o: float = clampf(st_t * 2.0, 0.0, 1.0) * 0.025
				mouse.position = hole + nrm * (o - 0.035) - Vector3(0, 0.014, 0)
				mouse.rotation.y = phi + 0.5 * sin(st_t * 2.5)
				if vd < 2.0:
					go("in")
				elif st_t > 3.0:
					go("out")
			"out":                                             # out on the board, sniffs, washes its face
				var o2: float = clampf(st_t * 1.5, 0.0, 1.0) * 0.1
				mouse.position = hole + nrm * (o2 - 0.01) - Vector3(0, 0.055, 0)
				mouse.rotation.y = phi + 0.3 * sin(st_t * 1.3)
				if vd < 2.0 or st_t > 7.0:
					go("in")

	func mouse_out() -> bool:
		return shown and st in ["peek", "out"]


# ---- 32 · an old wooden ski melts out of the glacier (summer): drops, a rivulet, a bamboo pole beside it -----------------------
class Holzski extends Vig:
	var ice: MeshInstance3D
	var drops: Array = []
	var tip := Vector3.ZERO

	func build() -> void:
		id = "holzski"
		c = ew.G(830.0, 485.0)

	func when_ok() -> bool:
		return ew.season == "sommer"

	func live() -> void:
		var b := Basis(Vector3.UP, 0.8)                           # bergtal.gd: wood_ski at (830, 485), turned 0.8, 0.25 m in the ice
		var im := StandardMaterial3D.new()
		im.albedo_color = Color(0.72, 0.84, 0.92, 0.6)
		im.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		im.roughness = 0.15
		ice = MeshInstance3D.new()
		ice.mesh = ew.boxm(0.55, 0.32, 1.1)
		ice.material_override = im
		ice.layers = 1
		ice.position = c + b * Vector3(0, -0.05, 0.4)
		ice.rotation.y = 0.8
		vroot.add_child(ice)
		ew.part(vroot, ew.boxm(0.5, 0.25, 1.0), c + b * Vector3(0, -0.08, 0.4), Color(0.7, 0.8, 0.88), "snow", Vector3(0, 0.8, 0)).visible = false
		var wet: MeshInstance3D = ew.part(vroot, ew.boxm(0.12, 0.01, 2.4), ew.G(c.x, c.z, 0.01) + b * Vector3(0.15, 0, 1.9), Color(0.25, 0.32, 0.36), "snow", Vector3(0, 0.8, 0))
		wet.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		# the bamboo pole with its leather basket (Skistock um 1930), half out of the ice
		ew.rod(vroot, c + b * Vector3(0.45, -0.1, 0.2), c + b * Vector3(0.6, 0.55, 0.0), 0.012, Color(0.78, 0.68, 0.42), "tree")
		ew.part(vroot, ew.cylm(0.07, 0.07, 0.01, 10), c + b * Vector3(0.48, 0.0, 0.17), Color(0.32, 0.2, 0.1), "tree")
		tip = c + b * Vector3(0, 0.36, -0.9)
		var dm: StandardMaterial3D = ew.glow_mat(Color(0.75, 0.88, 1.0), 0.3, 0.8)
		for i in range(1 if ew.lite else 3):
			drops.append([ew.light_part(vroot, ew.sphm(0.008, 0.014, 5), tip, dm), randf() * 1.5])
		go("melt")

	func tick(dt: float) -> void:
		# melts more in the afternoon: the ice is smaller (12–17 h)
		var h: float = ew.hour()
		var k: float = clampf((h - 10.0) / 6.0, 0.0, 1.0) if h < 18.0 else 0.6
		ice.scale = Vector3(1.0 - 0.15 * k, 1.0 - 0.3 * k, 1.0 - 0.1 * k)
		for d in drops:
			d[1] = float(d[1]) - dt
			var mi: MeshInstance3D = d[0]
			if float(d[1]) < 0.0:
				var f: float = -float(d[1])
				mi.position = Vector3(ice.position.x, ice.position.y + 0.16 - 4.9 * f * f, ice.position.z) + Basis(Vector3.UP, 0.8) * Vector3(0, 0, -0.55)
				if f > 0.2:
					d[1] = randf_range(0.8, 2.5)
					if not ew.lite and randf() < 0.3:
						ew.sound(mi.position, "plop", [[0.0, 0.05, 1800.0, 1200.0, 0.4]], -24.0, -60.0)
			else:
				mi.position = Vector3(ice.position.x, ice.position.y + 0.16, ice.position.z) + Basis(Vector3.UP, 0.8) * Vector3(0, 0, -0.55)


# ---- 33 · northern lights (only on rare clear winter nights): a faint red curtain low in the north, the green below it -------
class Nordlicht extends Vig:
	var sky: Node3D
	var curt: Array = []            # [MeshInstance3D, material, phase]
	var bench: Node3D
	var fade := 0.0

	func build() -> void:
		id = "nordlicht"
		c = ew.G(60.0, 850.0)
		anywhere = true
		bench = ew.node(ew.holder, c)                            # a flat stone bench, facing north (always there)
		ew.part(bench, ew.boxm(1.6, 0.12, 0.5), Vector3(0, 0.45, 0), Color(0.55, 0.53, 0.5), "stone")
		for x in [-0.6, 0.6]:
			ew.part(bench, ew.boxm(0.35, 0.42, 0.4), Vector3(x, 0.2, 0), Color(0.48, 0.46, 0.43), "stone")

	func when_ok() -> bool:
		return ew.nordlicht_tonight()

	func where() -> Vector3:
		return ew.W(c + Vector3(0, 12.0, -40.0))

	func live() -> void:
		sky = Node3D.new()
		vroot.add_child(sky)
		var n := 2 if ew.lite else 4
		for i in range(n):
			var mt := StandardMaterial3D.new()
			mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			mt.vertex_color_use_as_albedo = true
			mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			mt.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
			mt.cull_mode = BaseMaterial3D.CULL_DISABLED
			mt.no_depth_test = false
			if "disable_fog" in mt:
				mt.set("disable_fog", true)
			mt.albedo_color = Color(1, 1, 1, 0.0)
			var mi := MeshInstance3D.new()
			mi.mesh = _curtain(i)
			mi.material_override = mt
			mi.layers = 1                                       # not in the thermal picture (it is light, not heat)
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.extra_cull_margin = 3000.0
			sky.add_child(mi)
			curt.append([mi, mt, randf() * TAU])
		go("glow")

	func _curtain(i: int) -> ArrayMesh:
		var st_ := SurfaceTool.new()
		st_.begin(Mesh.PRIMITIVE_TRIANGLES)
		var cols := 28
		var w := 2600.0 - i * 300.0
		var x0 := -w / 2.0 + i * 180.0
		var z0 := -float(i) * 160.0
		var y0 := 260.0 + i * 40.0                                # at 2.6 km: 6° … 20° above the horizon
		var hgt := 620.0 - i * 80.0
		var rows := [0.0, 0.12, 0.35, 0.7, 1.0]
		# colours: low a faint green, above mostly red (seen from the Alps the red top of the aurora is what shows)
		var rc := [Color(0.25, 1.0, 0.5, 0.0), Color(0.3, 1.0, 0.55, 0.22), Color(0.85, 0.35, 0.4, 0.35), Color(0.95, 0.25, 0.35, 0.22), Color(0.9, 0.2, 0.4, 0.0)]
		for k in range(cols - 1):
			for r in range(rows.size() - 1):
				var quad := []
				for e in [[k, r], [k + 1, r], [k + 1, r + 1], [k, r + 1]]:
					var u: float = float(e[0]) / (cols - 1)
					var x: float = x0 + u * w
					var z: float = z0 + sin(u * 7.0 + i) * 220.0 + sin(u * 17.0 + i * 2.0) * 60.0
					var y: float = y0 + float(rows[e[1]]) * hgt * (0.8 + 0.3 * sin(u * 11.0 + i))
					var cc: Color = rc[e[1]]
					var edge: float = clampf(minf(u, 1.0 - u) * 6.0, 0.0, 1.0)
					quad.append([Vector3(x, y, z), Color(cc.r, cc.g, cc.b, cc.a * edge * (0.6 + 0.4 * sin(u * 23.0 + i * 3.0)))])
				for t in [0, 1, 2, 0, 2, 3]:
					st_.set_color(quad[t][1])
					st_.add_vertex(quad[t][0])
		return st_.commit()

	func tick(dt: float) -> void:
		var v: Vector3 = ew.VL(ew.view_pos())                     # always 2.6 km north of the one who looks (like the sky)
		sky.position = Vector3(v.x, c.y, v.z - 2600.0)
		fade = move_toward(fade, 1.0, dt / 40.0)                 # slowly brighter (a minute)
		for cu in curt:
			var ph: float = float(cu[2])
			var a: float = fade * (0.55 + 0.45 * sin(ew._clock * 0.11 + ph) * sin(ew._clock * 0.037 + ph * 2.0))
			(cu[1] as StandardMaterial3D).albedo_color = Color(1, 1, 1, clampf(a, 0.0, 1.0))
			(cu[0] as MeshInstance3D).position.x = sin(ew._clock * 0.01 + ph) * 120.0
			(cu[0] as MeshInstance3D).scale.y = 1.0 + 0.12 * sin(ew._clock * 0.05 + ph)

	func on_hide() -> void:
		fade = 0.0

	func glowing() -> bool:
		return shown and fade > 0.3


# ---- 34 · the secret lake behind the ridge: still water, trout rising, a stone bench - in the morning a chamois drinks ----------
class Geheimsee extends Vig:
	var rings: Array = []           # [mesh, material, age, life]
	var lvl := 0.0
	var next := 3.0
	var gms
	var shore := Vector3.ZERO
	var away := Vector3.ZERO
	var lk: Array = []

	func build() -> void:
		id = "geheimer_see"
		lk = ew.bt.get_script().LAKE4
		var cen: Vector2 = lk[0]
		lvl = ew.bt.level_of(lk)
		c = Vector3(cen.x, lvl, cen.y)
		var bp: Node3D = ew.node(ew.holder, ew.G(-857.0, 401.0))         # the stone bench at the end of the narrow path, facing the lake
		bp.rotation.y = atan2(-(cen.x + 857.0), -(cen.y - 401.0)) + PI
		ew.part(bp, ew.boxm(1.4, 0.1, 0.45), Vector3(0, 0.42, 0), Color(0.55, 0.53, 0.5), "stone")
		for x in [-0.5, 0.5]:
			ew.part(bp, ew.boxm(0.3, 0.4, 0.38), Vector3(x, 0.2, 0), Color(0.47, 0.45, 0.42), "stone")
		var a := 3.5
		var q: Vector2 = Vector2(cos(a) * float(lk[1]) * 1.06, sin(a) * float(lk[2]) * 1.06).rotated(float(lk[3])) + cen
		shore = ew.G(q.x, q.y)
		var q2: Vector2 = Vector2(cos(a) * float(lk[1]) * 1.7, sin(a) * float(lk[2]) * 1.7).rotated(float(lk[3])) + cen
		away = ew.G(q2.x, q2.y)

	func live() -> void:
		for i in range(1 if ew.lite else 3):
			var mt := StandardMaterial3D.new()
			mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			mt.albedo_color = Color(0.85, 0.9, 0.95, 0.0)
			var tm := TorusMesh.new()
			tm.inner_radius = 0.9
			tm.outer_radius = 1.0
			tm.rings = 24
			tm.ring_segments = 4
			var mi := MeshInstance3D.new()
			mi.mesh = tm
			mi.material_override = mt
			mi.layers = 1
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.scale = Vector3(0.1, 0.02, 0.1)
			mi.visible = false
			vroot.add_child(mi)
			rings.append([mi, mt, 0.0, 0.0])
		if ew.season != "winter":
			gms = ew.actor("chamois", away, shore, 0.6)
			actors.append(gms)
			gms.visible = false
		go("still")

	func _water_ok() -> bool:
		return ew.season in ["sommer", "herbst"]                 # winter / spring: the high lake is still frozen

	func tick(dt: float) -> void:
		var h: float = ew.hour()
		next -= dt
		if next <= 0.0 and _water_ok():                          # a trout rises after a fly: one ring that grows and fades
			var quiet := (h > 5.0 and h < 9.0) or (h > 18.0 and h < 21.5)
			next = randf_range(3.0, 7.0) if quiet else randf_range(10.0, 25.0)
			for r in rings:
				if not (r[0] as MeshInstance3D).visible:
					var u := Vector2(randf_range(-0.7, 0.7), randf_range(-0.7, 0.7))
					var q: Vector2 = Vector2(u.x * float(lk[1]), u.y * float(lk[2])).rotated(float(lk[3])) + (lk[0] as Vector2)
					(r[0] as MeshInstance3D).position = Vector3(q.x, lvl + 0.03, q.y)
					(r[0] as MeshInstance3D).visible = true
					r[2] = 0.0
					r[3] = randf_range(2.5, 3.5)
					ew.sound(Vector3(q.x, lvl, q.y), "plop", [[0.0, 0.08, 700.0, 250.0, 0.7]], -18.0, -50.0)
					break
		for r in rings:
			var mi: MeshInstance3D = r[0]
			if mi.visible:
				r[2] = float(r[2]) + dt
				var f: float = float(r[2]) / float(r[3])
				var s3: float = 0.1 + 1.6 * f
				mi.scale = Vector3(s3, 0.02, s3)
				(r[1] as StandardMaterial3D).albedo_color.a = 0.55 * (1.0 - f)
				if f >= 1.0:
					mi.visible = false
		if gms == null:
			return
		match st:
			"still":
				gms.visible = false
				if h > 5.5 and h < 9.5 and st_t > 20.0:
					ew.place(gms, away)
					gms.visible = true
					go("come")
			"come":
				ew.idle(gms, "")
				if ew.walk(gms, shore, 0.5, dt, null, 2.0) or st_t > 40.0:
					go("drink")
			"drink":                                           # drinks (head down), looks up, drinks again
				ew.stop(gms, dt)
				ew.idle(gms, "graze" if fmod(st_t, 9.0) < 6.5 else "look")
				if st_t > 30.0:
					go("leave")
			"leave":
				ew.idle(gms, "")
				if ew.walk(gms, away, 0.6, dt, null, 2.0) or st_t > 40.0:
					gms.visible = false
					go("still")


# =============================================================================================================================
# ---- the discovery book (entdecken.gd) -----------------------------------------------------------------------------------------
# =============================================================================================================================
func _reg(e, id: String, title: String, short: String, hint: String, icon: String, kind: String, pos: Vector3, size: Vector3, radius: float,
		when = "any", extra := {}) -> void:
	var inf := {"scene": SCENE, "title": title, "short_text": short, "hint": hint, "icon": icon, "kind": kind,
			"position": pos, "size": size, "radius": radius, "when": when}
	inf.merge(extra, true)
	e.register(id, inf)


func _register() -> void:
	var e = ent()
	if e == null:
		return
	var V: Dictionary = by_id
	var sh: Schneehase = V["schneehase_herbst"]
	_reg(e, "berg.schneehase_herbst", T.t("Der weisse Hase im braunen Herbst"),
			T.t("Der Schneehase hat schon sein Winterfell – nur liegt noch kein Schnee. Er sitzt ganz still und glaubt, man sehe ihn nicht. Immer neben dem einzigen weissen Ding weit und breit."),
			T.t("Im Herbst unter dem Grat beim Murmelboden: etwas Weisses sitzt da, wo noch gar kein Schnee liegt."), "🐇", "tier",
			W(sh.c) + Vector3(0, 0.3, 0), Vector3(0.6, 0.6, 0.6), 18.0, "day", {"active": func(): return sh.sitting()})
	var hm: Hermelin = V["hermelin_mauer"]
	_reg(e, "berg.hermelin_mauer", T.t("Das Hermelin in der Mauer"),
			T.t("Aus jedem Loch der alten Mauer schaut das Hermelin heraus, immer schneller – und am Schluss vorne der Kopf und hinten aus einem anderen Loch die schwarze Schwanzspitze."),
			T.t("Bei der Alp Tschuggen hat eine alte Trockenmauer fünf Löcher. Eine Weile still davor stehen bleiben."), "🦦", "tier",
			W(hm.c) + Vector3(0, 0.5, 0), Vector3(6.0, 1.0, 1.0), 14.0, "any", {"active": func(): return hm.popping()})
	var sa: Salamander = V["salamander_prozession"]
	_reg(e, "berg.salamander_prozession", T.t("Die Salamander-Prozession"),
			T.t("Nach dem Regen ziehen schwarze Alpensalamander im Gänsemarsch über den Weg. Einer kommt ihnen entgegen, stösst mit der Nase an – und kehrt um. Im Wärmebild sieht man sie kaum: sie sind so kalt wie der Boden."),
			T.t("Nach einem Regen auf dem Schluchtweg unterhalb der Alp auf den Boden schauen."), "🦎", "tier",
			W(sa.c) + Vector3(0, 0.1, 0), Vector3(5.0, 0.3, 1.0), 9.0, "any", {"active": func(): return sa.crossing()})
	reg_glocken()
	var dg: Dachgemse = V["gemse_hospizdach"]
	_reg(e, "berg.gemse_hospizdach", T.t("Die Gämse auf dem Hospiz"),
			T.t("Oben auf dem First des Hospizes geht eine Gämse spazieren, als wäre das Dach ein Grat. Am Ende legt sie sich hin und schaut auf den Parkplatz."),
			T.t("Auf dem Furggapass einmal nach oben schauen – auf das Dach des Hospizes."), "🐐", "tier",
			W(Vector3(dg.c.x, dg.ridge_y + 0.7, dg.c.z)), Vector3(12.0, 1.4, 1.5), 80.0, "day", {"active": func(): return dg.up()})
	var sf: Selfie = V["selfie_kante"]
	_reg(e, "berg.selfie_kante", T.t("Selfie mit Kuh"),
			T.t("Ein Wanderer macht Selfies und geht dabei rückwärts Richtung Schluchtkante. Eine Kuh stupst ihn von der Seite nach vorne – ihm passiert nichts, und das nächste Selfie ist mit der Kuh."),
			T.t("Am Schluchtweg beim Schild «Absturzgefahr» fotografiert sich jemand. Die Kühe schauen zu."), "🤳", "mensch",
			W(sf.c) + Vector3(0, 1.0, 0), Vector3(5.0, 2.0, 5.0), 30.0, "day", {"active": func(): return sf.happening()})
	var tr: Trailrunner = V["trailrunner"]
	_reg(e, "berg.trailrunner", T.t("Der Trailrunner fragt den Wegweiser"),
			T.t("Ein Läufer bleibt beim Wegweiser stehen, trippelt an Ort, zeigt auf eine Tafel und wartet auf eine Antwort. Er rennt los – falsch –, kommt zurück und nickt dem Wegweiser dankbar zu."),
			T.t("Beim Wegweiser am Gumpisee kommt ab und zu jemand angerannt, der es eilig hat."), "🏃", "mensch",
			W(tr.c) + Vector3(0, 1.2, 0), Vector3(3.0, 2.0, 3.0), 30.0, "day", {"active": func(): return tr.asking()})
	var fg: Fegen = V["huettenwart"]
	_reg(e, "berg.huettenwart", T.t("Fegen gegen den Wind"),
			T.t("Ein Gast der Selbstversorgerhütte fegt die Veranda – ein Windstoss, und alles liegt wieder da. Beim dritten Mal fegt er einfach in die andere Richtung."),
			T.t("Vor der Hütte Alp Tschuggen wird geputzt. Ob der Wind mithilft?"), "🧹", "mensch",
			W(fg.c) + Vector3(0, 0.6, 0), Vector3(5.0, 1.8, 2.5), 25.0, "day", {"active": func(): return fg.blown()})
	var pk: Picknick = V["picknick"]
	_reg(e, "berg.picknick", T.t("Wo ist der Korkenzieher?"),
			T.t("Beim Picknick am Gumpisee sucht er den Korkenzieher im Korb, in den Taschen, überall. Er steckt die ganze Zeit an seinem Hut."),
			T.t("Am Ufer des Gumpisees picknicken zwei. Schau genau auf den Hut."), "🍷", "mensch",
			W(pk.c) + Vector3(0, 0.8, 0), Vector3(2.5, 1.8, 2.5), 25.0, "day", {"active": func(): return pk.looking()})
	var gs: Gleitschirm = V["gleitschirm"]
	_reg(e, "berg.gleitschirm", T.t("Landung auf der Kuhweide"),
			T.t("Ein Gleitschirm kreist über der Alp herunter und landet mitten auf der Weide. Die Kühe kommen sofort und beschnuppern den grossen bunten Schirm."),
			T.t("An einem ruhigen Tag über der Alp Tschuggen in den Himmel schauen – da kommt jemand herunter."), "🪂", "szene",
			Vector3(0, 0, 0), Vector3(10.0, 2.0, 4.0), 90.0, "day",
			{"position": W(gs.c) + Vector3(0, 1.0, 0), "active": func(): return gs.flying()})
	var pa: Postauto = V["postauto"]
	_reg(e, "berg.postauto", T.t("Tü-ta-to in den Kehren"),
			T.t("Das Postauto fährt die Passstrasse hinauf und hupt vor der engen Kehre mit dem Dreiklang – das hört man im ganzen Tal."),
			T.t("Tagsüber bei den Kehren der Passstrasse warten und hinhören."), "🚌", "szene",
			W(pa.c) + Vector3(0, 2.0, 0), Vector3(12.0, 3.0, 3.0), 150.0, "day", {"los": false, "active": func(): return pa.honked()})
	var sm: Schmuggler = V["schmuggler"]
	_reg(e, "berg.schmugglerroute", T.t("Die Schmugglerroute"),
			T.t("Im flachen Abendlicht sieht man auf einmal Kreuze, in die Steine geritzt – eine alte Schmugglerroute über den Pass, zu einem Versteck."),
			T.t("Ob dem Furggapass, östlich vom Bunker: am Abend, wenn die Sonne tief steht, die Steine genau anschauen."), "✖", "ort",
			W(sm.start.lerp(sm.c, 0.2)) + Vector3(0, 0.4, 0), Vector3(3.0, 1.0, 3.0), 25.0, "day", {"active": func(): return sm.visible_marks(), "los": false})
	_reg(e, "berg.schmugglerversteck", T.t("Das Schmugglerversteck"),
			T.t("Unter einer schrägen Steinplatte steht eine alte Holzkiste, darauf verblasst: CAFFÈ. Leer – schon lange."),
			T.t("Die Kreuze in den Steinen führen hinauf zu einem grossen Block. Darunter nachschauen."), "📦", "ort",
			W(sm.c) + Vector3(-0.2, 0.2, 0.2), Vector3(0.6, 0.4, 0.5), 4.0, "any", {"active": func(): return e.is_found("berg.schmugglerroute")})
	var au: Augen = V["steinmann_wald"]
	_reg(e, "berg.steinmann_augen", T.t("Der Steinmann mit Augen"),
			T.t("Im Steinmann-Wald hat einer zwei Augen. Sie schauen dir nach – und wenn du zu nahe kommst, macht er sie zu und ist wieder nur ein Steinmann."),
			T.t("Im Steinmann-Wald beim Biwak: einer von über zweihundert schaut zurück."), "👀", "ort",
			W(au.c) + Vector3(0, 1.0, 0), Vector3(0.6, 0.4, 0.6), 9.0, "any", {"active": func(): return au.open()})
	var sn: Sennerei = V["sennerei"]
	_reg(e, "berg.sennerei_kaese", T.t("Der Käse von 1897"),
			T.t("Vor der verlassenen Sennerei liegt ein uralter Käselaib, auf der Rinde «1897». Er ist bewohnt: aus einem Loch schaut eine Maus, oben ab und zu eine junge."),
			T.t("Bei der alten Sennerei im Seitental West liegt ein Käse. Leise näher gehen."), "🧀", "tier",
			W(sn.c) + Vector3(0, 0.1, 0), Vector3(0.7, 0.3, 0.7), 5.0, "any", {"active": func(): return sn.mouse_out()})
	var hs: Holzski = V["holzski"]
	_reg(e, "berg.holzski", T.t("Der Holzski im Gletscher"),
			T.t("Im Sommer schmilzt am Wyssgletscher ein alter Holzski aus dem Eis, daneben ein Bambusstock mit Lederteller. Es tropft – das Eis gibt ihn langsam her."),
			T.t("Im Sommer am Rand des Wyssgletschers, beim Gletscherweg: etwas Braunes im Eis."), "🎿", "ort",
			W(hs.c) + Vector3(0, 0.2, 0), Vector3(1.2, 0.6, 2.0), 7.0, "any", {"active": func(): return hs.when_ok()})
	var nl: Nordlicht = V["nordlicht"]
	_reg(e, "berg.nordlicht", T.t("Nordlicht über dem Pass"),
			T.t("In einer seltenen, ganz klaren Winternacht steht tief im Norden ein schwacher roter Vorhang am Himmel, unten ein wenig grün. In der Schweiz sieht man das nur ein paar Mal in vielen Jahren."),
			T.t("In einer ganz klaren Winternacht auf dem Furggapass auf die Steinbank sitzen und nach Norden schauen. Es braucht Glück."), "🌌", "szene",
			nl.where(), Vector3(20.0, 10.0, 4.0), 60.0, "night", {"los": false, "active": func(): return nl.glowing()})
	var gse: Geheimsee = V["geheimer_see"]
	_reg(e, "berg.geheimer_see", T.t("Der geheime See"),
			T.t("Hinter dem Grat, nur über einen schmalen Pfad: ein kleiner stiller See. Am Morgen und am Abend springen Forellen, eine Steinbank wartet am Ufer."),
			T.t("Vom Gratspitz führt ein schmaler blau-weisser Pfad nach Westen hinter den Grat."), "🏞", "ort",
			W(gse.c) + Vector3(0, 1.0, 0), Vector3(20.0, 2.0, 14.0), 45.0)
	if not e.found.is_connected(_on_found):
		e.found.connect(_on_found)


func reg_glocken() -> void:
	"""21 needs a photo of the cow: registered again when the cow is there (the photo box follows her)"""
	var e = ent()
	if e == null:
		return
	var gl: Glocken = by_id["kuhglocken_nebel"]
	var ex := {"photo_required": true, "active": func(): return gl.there() and gl.cow != null and gl.cow.visible}
	if gl.cow != null:
		ex["node"] = gl.cow
	_reg(e, "berg.kuhglocken_nebel", T.t("Glocken im Nebel"),
			T.t("Im dichten Nebel hört man nur Kuhglocken, mal links, mal rechts, immer näher – und plötzlich steht eine Kuh direkt vor MoveEye und schaut in die Kamera. Fotografiert mit MoveEyes Kamera."),
			T.t("Bei Nebel bei der Alp Tschuggen übernachten und gut hinhören. Wenn sie vor MoveEye steht: ein Foto mit MoveEyes Kamera!"), "🔔", "tier",
			Vector3(0, 1.0, 0) if gl.cow != null else W(gl.c) + Vector3(0, 1.0, 0), Vector3(1.0, 1.6, 2.4), 25.0, ["fog"], ex)


func _on_found(id: String) -> void:
	if id == "berg.schmugglerroute" and is_inside_tree():
		var e = ent()
		if e != null:
			e.call_deferred("show_hint", "berg.schmugglerversteck")   # the marks lead up: Blinki tells where the hiding place is


func _exit_tree() -> void:
	var e = ent()
	if e != null and e.found.is_connected(_on_found):
		e.found.disconnect(_on_found)


# =============================================================================================================================
# ---- control {"action": "bergtal", "do": "erleben_b", "what": …} --------------------------------------------------------------
# =============================================================================================================================
func control(d: Dictionary) -> Dictionary:
	var id := str(d.get("id", ""))
	match str(d.get("what", "info")):
		"where":                                         # where a vignette is (world, valley), for tests and quick travel
			if not by_id.has(id):
				return {"ok": false, "error": "unknown", "ids": by_id.keys()}
			var v = by_id[id]
			var w: Vector3 = v.where()
			return {"ok": true, "pos": [snappedf(w.x, 0.01), snappedf(w.y, 0.01), snappedf(w.z, 0.01)], "tal": [snappedf(v.c.x, 0.1), snappedf(v.c.y, 0.1), snappedf(v.c.z, 0.1)],
					"when_ok": v.when_ok()}
		"state":                                         # tests: jump a vignette to a state (and hold it)
			if by_id.has(id):
				if d.has("state"):
					by_id[id].go(str(d.get("state", "")))
				if d.has("t"):
					by_id[id].st_t = float(d["t"])
				by_id[id].hold = bool(d.get("hold", false))
				return {"ok": true, "info": by_id[id].info()}
			return {"ok": false, "error": "unknown", "ids": by_id.keys()}
		"rain":                                          # tests: «it has just rained» (salamanders)
			_rain_end = float(m.now())
			Engine.set_meta("berg_rain_end", _rain_end)
			return {"ok": true, "wet": wet_recent()}
		"nordlicht":                                     # tests: the northern lights tonight (still only in a winter night)
			force_nordlicht = bool(d.get("value", true))
			return {"ok": true, "tonight": nordlicht_tonight(), "season": season, "dark": dark()}
	var out := []
	for v in vigs:
		var inf: Dictionary = v.info()
		inf["when_ok"] = v.when_ok()
		out.append(inf)
	return {"ok": true, "file": "b", "vignettes": out, "stats": stats, "lite": lite, "season": season, "wet": wet_recent(), "fog": foggy(),
			"nordlicht": nordlicht_tonight(), "evening_light": snappedf(evening_light(), 0.01)}
