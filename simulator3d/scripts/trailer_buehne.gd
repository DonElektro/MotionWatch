extends "res://scripts/bergtal_erleben_base.gd"
## Trailer-Bühne (Daniel 31.10.2026, Regie: trailer.gd): die Szenen der beiden Trailer im echten Bergtal – Orte aus bergtal.gd
## (Konstanten, ziehen bei einer neuen Landschaft mit), Figuren aus actor.gd, Maggie aus maggie_hund.gd (ihr Aussehen kommt von
## dort: ändert es sich, sieht der Trailer es auch), Kristall / Lichtsäule / Teilchen aus maggie_welt.gd.
## Alles ist an die Zeit der Einstellung gebunden (Wege nach Zeit, nicht Schritt für Schritt): jede Einstellung kann direkt
## angesprungen werden (Standbilder, --trailer-ab) und sieht im Film genauso aus wie beim Sprung.
## Spoiler (Daniel): nur Anfang und Andeutungen. Grossvater: keine Steinmännchen, kein Seeli, kein Ziel der Karte (nur das
##   erste Kartenstück). Maggie: kein Finale (keine Bergkapelle), nichts Brutales – Augen, Knurren, Nebel, die mutige Maggie.
## Einstellung (Dictionary): t0, d, art (welt | tafel | papier | titel | ende | schwarz), text / sub (Tafeln), zeit, wetter,
##   donner, nebel (zusätzliche Dichte), tint (Farbe über dem Bild), auf / tick (Methoden hier), cam, say [[t, Text]],
##   ton [[t, Befehl …]], blitz [t …]. Kamera: k = fahrt (a → b, Blick la → lb) | folge (fig, off, look) | kreis (c, r, h, a0, a1);
##   Punkte als Vector3(x, Höhe über Boden, z) in Tal-Koordinaten (x = Osten, z = Süden).

const Welt = preload("res://scripts/maggie_welt.gd")
const Bt = preload("res://scripts/bergtal.gd")
const Orte = preload("res://scripts/bergtal_orte.gd")
const FD = preload("res://scripts/abenteuer_figuren_daten.gd")
const Figur = preload("res://scripts/figur.gd")

const KRISTALL := Color(0.62, 0.85, 1.0)
const AUGE := Color(0.95, 0.85, 0.35)

var regie                              # trailer.gd
var trailer := "grossvater"
var figs := {}                         # name -> actor
var hund_mod = null                    # maggie_hund.gd (nur Maggie)
var _hstub = null
var dinge := {}                        # name -> Node3D (Kristall, Lichtsäule, Augen, Fackel, Krähen, Viper …)
var _shot := {}
var _held_look := {}
var _held_col := Color(0.75, 0.16, 0.12)


func _part() -> String:
	return "trailer"


func binden(m_) -> bool:
	"""an das Bergtal hängen, das gerade gebaut ist (wie maggie_hund.gd _binden)"""
	m = m_
	var b = m.scenes.data.get("bergtal", null) if m.scenes != null else null
	if b == null or b.tal == null or not is_instance_valid(b.tal):
		return false
	bt = b
	s = bt.s
	season = str(bt.season)
	lite = _lite() or str(m.quality) == "simple"
	process_priority = 100
	name = "trailer_buehne"
	holder = Node3D.new()
	holder.name = "trailer_dinge"
	bt.tal.add_child(holder)
	return true


func aufraeumen() -> void:
	if hund_mod != null and is_instance_valid(hund_mod):
		hund_mod._on_schluss()
		hund_mod.queue_free()
	hund_mod = null
	for k in figs:
		if is_instance_valid(figs[k]):
			figs[k].queue_free()
	figs = {}
	if holder != null and is_instance_valid(holder):
		holder.queue_free()
	holder = null
	dinge = {}


# =======================================================================================================================
# helpers
# =======================================================================================================================
func P(v: Vector3) -> Vector3:
	"""Vector3(x, Höhe über Boden, z) im Tal -> Welt"""
	return W(G(v.x, v.z, v.y))


func ein(t: float, a: float, b: float) -> float:
	"""0 … 1 zwischen a und b (weich)"""
	return smoothstep(a, b, t)


func setze_held(look: Dictionary, col: Color) -> void:
	_held_look = look.duplicate()
	_held_col = col


func fig(nm: String, kind: String, opt := {}) -> Node3D:
	"""eine Figur (einmal gebaut, danach nur gezeigt): opt jacke (Color), look (Dictionary), pack, scale, farbe (Tiere)"""
	if figs.has(nm) and is_instance_valid(figs[nm]):
		(figs[nm] as Node3D).visible = true
		return figs[nm]
	var a = m.Actor.new()
	if opt.has("jacke"):
		a.player_color = opt["jacke"]
	if opt.has("look"):
		a.look = (opt["look"] as Dictionary).duplicate()
	add_child(a)
	var p := G(0, 0)
	a.setup(m, kind, W(p), W(p + Vector3(0, 0, -1)), 1.2)
	a.puppet = true
	a.set_meta("nachbar", true)
	a.set_meta("trailer", true)
	if a.lamp != null:
		a.lamp.light_energy = 0.0
		a.lamp_mat.emission_energy_multiplier = 0.0
		a.lamp = null
		a.phone_out = false
	if bool(opt.get("pack", false)):
		backpack(a, opt.get("pack_col", Color(0.2, 0.32, 0.5)))
	if opt.has("scale"):
		a.body_root.scale *= float(opt["scale"])
	if opt.has("farbe"):
		bt._recolor(a, opt["farbe"], float(opt.get("temp", 30.0)))
	figs[nm] = a
	return a


func nur(names: Array) -> void:
	"""nur diese Figuren sind im Bild (die anderen versteckt und still)"""
	for k in figs:
		var a = figs[k]
		if not is_instance_valid(a):
			continue
		var on: bool = k in names
		a.visible = on
		a.process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED
	var h = hund()
	if h != null:
		h.visible = "maggie" in names
		h.process_mode = Node.PROCESS_MODE_INHERIT if "maggie" in names else Node.PROCESS_MODE_DISABLED


func stell(a, x: float, z: float, lx: float, lz: float, lift = null) -> void:
	if a == null:
		return
	place(a, G(x, z) if lift == null else Vector3(x, float(lift), z), lift != null)
	face(a, Vector3(lx - x, 0, lz - z))
	a.cur_speed = 0.0
	idle(a, "")


func pfad(a, pts: Array, spd: float, t: float, lift = null) -> bool:
	"""die Figur steht dort, wo sie nach t Sekunden mit spd auf dem Weg pts (Vector2 Tal) ist; true = am Ende"""
	if a == null or pts.size() < 2:
		return true
	var rest := maxf(0.0, spd * t)
	for i in range(pts.size() - 1):
		var p0: Vector2 = pts[i]
		var p1: Vector2 = pts[i + 1]
		var L := p0.distance_to(p1)
		if rest <= L or i == pts.size() - 2:
			var k := clampf(rest / maxf(L, 0.001), 0.0, 1.0)
			var q := p0.lerp(p1, k)
			var y = lift
			place(a, G(q.x, q.y) if y == null else Vector3(q.x, float(y), q.y), y != null)
			face(a, Vector3(p1.x - p0.x, 0, p1.y - p0.y))
			a.cur_speed = spd if k < 1.0 else 0.0
			idle(a, "")
			return k >= 1.0
		rest -= L
	return true


func _saeule() -> Node3D:
	var b := Welt.beam(KRISTALL)
	b.layers = 1                                       # (the window camera of the film hides the helper layer)
	return _add("saeule", b)


func licht(n: Node3D, e: float) -> void:
	var l := n.get_node_or_null("light") as OmniLight3D
	if l != null:
		l.light_energy = e


func ding(nm: String) -> Node3D:
	return dinge.get(nm, null) if dinge.has(nm) and is_instance_valid(dinge[nm]) else null


func dinge_aus(ausser: Array = []) -> void:
	for k in dinge:
		if is_instance_valid(dinge[k]) and not k in ausser:
			(dinge[k] as Node3D).visible = false


func zeig(nm: String) -> Node3D:
	var n := ding(nm)
	if n != null:
		n.visible = true
	return n


func _add(nm: String, n: Node3D) -> Node3D:
	holder.add_child(n)
	dinge[nm] = n
	return n


# ---- Maggie (maggie_hund.gd baut sie: gleiches Aussehen wie im Spiel) -------------------------------------------------------
class HundStub:
	## die kleine Story für maggie_hund.gd: keine Region (keine Stationen), die Figur ist der Wanderer des Trailers;
	## fuehrt_hund() = true: der Trailer führt Maggie selbst (nach Zeit, nicht «folgen»)
	var b
	func _init(b_) -> void:
		b = b_
	func region_aktiv() -> String:
		return ""
	func spieler_pos() -> Vector3:
		var a = b.figs.get("held", null)
		return (a as Node3D).global_position if a != null and is_instance_valid(a) else b.view_pos()
	func region_mitte(_id: String) -> Vector3:
		return b.view_pos()
	func kristall_bei_spieler() -> bool:
		return true
	func fuehrt_hund() -> bool:
		return true
	func tipp(_t: String) -> void:
		pass
	func moveeye_sagt(_t: String) -> void:
		pass


func hund() -> Node3D:
	if hund_mod != null and is_instance_valid(hund_mod) and hund_mod.hund != null and is_instance_valid(hund_mod.hund):
		return hund_mod.hund
	return null


func maggie_bauen() -> void:
	if hund() != null or not ResourceLoader.exists("res://scripts/maggie_hund.gd"):
		return
	var h = load("res://scripts/maggie_hund.gd").new()
	h.main = m
	h.m = m
	_hstub = HundStub.new(self)
	h.story = _hstub
	h.zwei = _hstub
	add_child(h)
	if not h._binden():
		h.queue_free()
		return
	h._hund_bauen()
	hund_mod = h


func graben(on: bool) -> void:
	if hund_mod != null and is_instance_valid(hund_mod):
		hund_mod._graben_hier(on)


# ---- things ------------------------------------------------------------------------------------------------------------------
func kristall(nm: String, sc: float) -> Node3D:
	var n := ding(nm)
	if n == null:
		n = _add(nm, Node3D.new())
		var c := Welt.crystal(sc)
		c.name = "c"
		n.add_child(c)
		if not lite:
			var sp := Welt.sparkles(KRISTALL)
			sp.name = "sp"
			n.add_child(sp)
			sp.emitting = true
	n.visible = true
	return n


func augen(nm: String, pts: Array, col := AUGE) -> Node3D:
	"""Augenpaare im Dunkeln (nur leuchtende Punkte): pts = [Vector3(x, Höhe, z) Tal, …]"""
	var n := ding(nm)
	if n != null:
		n.visible = true
		return n
	n = _add(nm, Node3D.new())
	var mt := glow_mat(col, 6.0)
	for i in range(pts.size()):
		var p: Vector3 = pts[i]
		var pair := Node3D.new()
		pair.name = "p%d" % i
		pair.position = G(p.x, p.z, p.y)
		n.add_child(pair)
		for sd in [-1.0, 1.0]:
			var e := light_part(pair, sphm(0.055, -1.0, 8), Vector3(sd * 0.1, 0, 0), mt)
			e.name = "e%d" % int(sd + 1.0)
	return n


func augen_tick(nm: String, t: float, start: float, step: float) -> void:
	"""die Augen gehen nacheinander auf (alle step s eines), blinzeln ab und zu und schauen zur Kamera"""
	var n := ding(nm)
	if n == null:
		return
	var cam := view_cam()
	for i in range(n.get_child_count()):
		var pair := n.get_child(i) as Node3D
		var on := t >= start + i * step
		pair.visible = on
		if not on:
			continue
		var bl := fmod(t * (0.9 + 0.13 * i) + i * 1.7, 4.0)
		pair.scale = Vector3(1.0, 0.12 if bl < 0.12 else minf(1.0, (t - start - i * step) * 3.0), 1.0)
		if cam != null:
			var to := cam.global_position - pair.global_position
			to.y = 0.0
			if to.length() > 0.1:
				pair.global_rotation = Vector3(0, atan2(to.x, to.z), 0)


func tier_augen(a, e: float) -> void:
	"""die Augen eines Tiers von actor.gd leuchten (nach seinem _process – wir laufen später)"""
	if a == null or not is_instance_valid(a):
		return
	for l in a.lights:
		if l is StandardMaterial3D:
			(l as StandardMaterial3D).emission = AUGE
			(l as StandardMaterial3D).emission_energy_multiplier = e


func fackel(a, on: bool) -> void:
	var n := ding("fackel")
	if n == null:
		n = _add("fackel", Node3D.new())
		part(n, cylm(0.025, 0.03, 0.6), Vector3(0, 0, 0), Color(0.35, 0.22, 0.12), "tent")
		var fl := light_part(n, sphm(0.07, 0.22, 8), Vector3(0, 0.38, 0), glow_mat(Color(1.0, 0.6, 0.2), 4.0, 0.9))
		fl.name = "flamme"
		var l := OmniLight3D.new()
		l.name = "light"
		l.light_color = Color(1.0, 0.62, 0.3)
		l.light_energy = 2.2
		l.omni_range = 9.0
		l.shadow_enabled = false
		l.position = Vector3(0, 0.45, 0)
		n.add_child(l)
	n.visible = on
	if on and a != null:
		var at: Vector3 = (a as Node3D).global_position + (a as Node3D).global_transform.basis * Vector3(0.32, 1.25, -0.25)
		n.global_position = at
		var fl2 := n.get_node("flamme") as Node3D
		fl2.scale = Vector3.ONE * (0.9 + 0.15 * sin(_clock * 23.0) + 0.1 * sin(_clock * 37.0))
		licht(n, 2.0 + 0.4 * sin(_clock * 17.0))


func schneefall(on: bool, cam_pos: Vector3) -> void:
	"""falling snow around the camera (own particles: the weather «snow» of the simulator would stay on the ground)"""
	var n := ding("schneefall")
	if n == null:
		if not on:
			return
		n = _add("schneefall", Node3D.new())
		var p := CPUParticles3D.new()
		p.name = "p"
		p.amount = 260 if not lite else 120
		p.lifetime = 4.0
		p.preprocess = 4.0
		p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
		p.emission_box_extents = Vector3(14, 1, 14)
		p.direction = Vector3(0.2, -1, 0)
		p.spread = 15.0
		p.gravity = Vector3(0, -0.6, 0)
		p.initial_velocity_min = 1.2
		p.initial_velocity_max = 2.0
		p.local_coords = false
		var qm := QuadMesh.new()
		qm.size = Vector2(0.06, 0.06)
		p.mesh = qm
		var mt := glow_mat(Color(0.92, 0.95, 1.0), 0.6, 0.9)
		mt.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		p.material_override = mt
		n.add_child(p)
	n.visible = on
	if on:
		n.global_position = cam_pos + Vector3(0, 7, 0)


func steine(nm: String, x: float, z: float) -> Node3D:
	"""a few warm flat stones in the evening sun (for the viper)"""
	var n := ding(nm)
	if n != null:
		n.visible = true
		return n
	n = _add(nm, Node3D.new())
	n.position = G(x, z)
	var r := [[Vector3(0.0, 0.05, 0.0), 0.45], [Vector3(0.75, 0.04, 0.35), 0.32], [Vector3(-0.6, 0.04, 0.5), 0.36], [Vector3(0.3, 0.03, -0.7), 0.3],
			[Vector3(-0.4, 0.03, -0.45), 0.22]]
	for e in r:
		var mi := MeshInstance3D.new()
		mi.mesh = sphm(float(e[1]), float(e[1]) * 0.7, 10)
		mi.position = e[0]
		mi.material_override = m.mat(Color(0.42, 0.4, 0.37))
		n.add_child(mi)
	return n


func kraehen(nm: String, n_: int) -> Node3D:
	var n := ding(nm)
	if n != null:
		n.visible = true
		return n
	n = _add(nm, Node3D.new())
	var mt: Material = m.mat(Color(0.05, 0.05, 0.06))
	for i in range(n_):
		var b := Node3D.new()
		b.name = "b%d" % i
		n.add_child(b)
		var body := MeshInstance3D.new()
		body.mesh = sphm(0.12, 0.36, 8)
		body.rotation.x = PI / 2.0
		body.material_override = mt
		b.add_child(body)
		for sd in [-1.0, 1.0]:
			var w := MeshInstance3D.new()
			var bm := BoxMesh.new()
			bm.size = Vector3(0.42, 0.02, 0.18)
			w.mesh = bm
			w.position = Vector3(sd * 0.22, 0, 0)
			w.material_override = mt
			w.name = "w%d" % int(sd + 1.0)
			b.add_child(w)
	return n


func kraehen_tick(nm: String, t: float, von: Vector3, nach: Vector3, dauer: float) -> void:
	var n := ding(nm)
	if n == null:
		return
	for i in range(n.get_child_count()):
		var b := n.get_child(i) as Node3D
		var k := clampf((t - i * 0.12) / dauer, 0.0, 1.0)
		var off := Vector3(sin(i * 2.3) * 4.0, sin(i * 1.7) * 2.0 + k * 3.0 * sin(i * 0.9), cos(i * 3.1) * 4.0)
		var p := von.lerp(nach, k) + off * (0.3 + k)
		b.position = G(p.x, p.z, p.y)
		var d := nach - von
		b.rotation.y = atan2(-d.x, -d.z)
		var fl := sin((t + i * 0.37) * 16.0) * 0.7
		(b.get_node("w0") as Node3D).rotation.z = fl
		(b.get_node("w2") as Node3D).rotation.z = -fl
		b.visible = t >= i * 0.12


func viper(nm: String) -> Node3D:
	var n := ding(nm)
	if n != null:
		n.visible = true
		return n
	n = _add(nm, Node3D.new())
	for i in range(12):
		var mi := MeshInstance3D.new()
		mi.mesh = sphm(0.05 - i * 0.002 if i > 1 else 0.055, -1.0, 8)
		mi.material_override = m.mat(Color(0.62, 0.52, 0.36) if i % 2 == 0 else Color(0.1, 0.08, 0.06))
		mi.name = "s%d" % i
		n.add_child(mi)
	return n


func viper_tick(nm: String, t: float, start: Vector3, dir_: float) -> void:
	var n := ding(nm)
	if n == null:
		return
	var fw := Vector3(sin(dir_), 0, cos(dir_))
	var sd := Vector3(fw.z, 0, -fw.x)
	var head := start + fw * t * 0.18
	for i in range(n.get_child_count()):
		var b := n.get_child(i) as Node3D
		var q := head - fw * (i * 0.08) + sd * sin(t * 5.0 - i * 0.7) * 0.08
		b.position = G(q.x, q.z, q.y + 0.03)


# =======================================================================================================================
# the camera
# =======================================================================================================================
func kamera(cam: Dictionary, u: float, rel: float) -> Array:
	"""[Position, Blickpunkt, fov] (Welt) der Einstellung beim Anteil u (0 … 1, schon weich) und rel Sekunden"""
	var fov := float(cam.get("fov", 60.0))
	var at := Vector3.ZERO
	var lk := Vector3.ZERO
	match str(cam.get("k", "fahrt")):
		"fahrt":
			var a: Vector3 = cam["a"]
			var b: Vector3 = cam.get("b", a)
			var la: Vector3 = cam["la"]
			var lb: Vector3 = cam.get("lb", la)
			at = P(a.lerp(b, u))
			lk = P(la.lerp(lb, u))
		"folge":
			var f = figs.get(str(cam["fig"]), null) if str(cam["fig"]) != "maggie" else hund()
			if f == null or not is_instance_valid(f):
				return []
			var fp: Vector3 = (f as Node3D).global_position
			var hd := float(f.heading)
			var fw := Vector3(-sin(hd), 0, -cos(hd))
			var rt := fw.cross(Vector3.UP)
			var o: Vector3 = cam.get("off", Vector3(0, 2.0, 5.0))
			var ob: Vector3 = cam.get("off_b", o)
			o = o.lerp(ob, u)
			at = fp + rt * o.x + Vector3(0, o.y, 0) - fw * o.z
			var l: Vector3 = cam.get("look", Vector3(0, 1.0, 0))
			lk = fp + rt * l.x + Vector3(0, l.y, 0) + fw * l.z
		"ziel":
			var zr: Array = _ziel_cam(cam)
			var tg: Vector3 = zr[0]
			var ang := deg_to_rad(float(zr[1]) + float(cam.get("dreh", 0.0)) * u)
			var dist := float(cam.get("dist", 20.0)) * (1.0 - float(cam.get("naeher", 0.0)) * u)
			var cp := Vector3(tg.x + sin(ang) * dist, 0, tg.z + cos(ang) * dist)
			cp.y = maxf(Bt.H(cp.x, cp.z) + float(cam.get("h", 2.0)), tg.y + float(cam.get("h_min", -1000.0)))
			at = W(cp)
			lk = W(tg + Vector3(0, float(cam.get("lh", 0.0)), 0))
		"kreis":
			var c: Vector3
			if cam.has("fig"):
				var f2 = figs.get(str(cam["fig"]), null) if str(cam["fig"]) != "maggie" else hund()
				if f2 == null or not is_instance_valid(f2):
					return []
				c = (f2 as Node3D).global_position
			elif cam.has("welt"):
				c = cam["welt"]
			elif cam.has("ding") and ding(str(cam["ding"])) != null:
				c = ding(str(cam["ding"])).global_position
			else:
				c = P(cam["c"])
			var ang := deg_to_rad(lerpf(float(cam.get("a0", 0.0)), float(cam.get("a1", 40.0)), u))
			var r := lerpf(float(cam.get("r", 6.0)), float(cam.get("r1", cam.get("r", 6.0))), u)
			at = c + Vector3(sin(ang) * r, float(cam.get("h", 2.0)), cos(ang) * r)
			lk = c + Vector3(0, float(cam.get("lh", 1.0)), 0)
	var gy: float = m.ground_y(at.x, at.z)
	at.y = maxf(at.y, gy + 0.35)
	var wk := float(cam.get("wackel", 0.0))
	if wk > 0.0:
		lk += Vector3(sin(rel * 2.3) + 0.5 * sin(rel * 5.1), 0.6 * sin(rel * 3.7), cos(rel * 1.9)) * wk
	return [at, lk, fov]


var _zc := {}


func _ziel_punkt(cam: Dictionary) -> Vector3:
	var z: Vector3 = cam["z"]
	if bool(cam.get("bruecke", false)):                  # the deck of the rope bridge (height from the gorge rims)
		return Vector3(z.x, _brueckenhoehe() + z.y, z.z)
	return Vector3(z.x, z.y if bool(cam.get("abs", false)) else Bt.H(z.x, z.z) + z.y, z.z)


func _frei(a: Vector3, b: Vector3) -> bool:
	"""line of sight over the height map (valley, absolute heights)"""
	for i in range(1, 24):
		var q := a.lerp(b, float(i) / 24.0)
		if Bt.H(q.x, q.z) + 0.6 > q.y:
			return false
	return true


func _ziel_cam(cam: Dictionary) -> Array:
	"""the camera looks at a place from a direction with a free view (searched once per shot: works with a new landscape too)"""
	var key := str(cam.get("z")) + str(cam.get("ang", 0.0)) + str(cam.get("dist", 20.0)) + str(cam.get("h", 2.0))
	if _zc.has(key):
		return _zc[key]
	var tg := _ziel_punkt(cam)
	var pref := float(cam.get("ang", 0.0))
	var dist := float(cam.get("dist", 20.0))
	var best := pref
	for k in range(25):
		var a: float = pref + (1.0 if k % 2 == 1 else -1.0) * ceil(k / 2.0) * 15.0
		var r := deg_to_rad(a)
		var cp := Vector3(tg.x + sin(r) * dist, 0, tg.z + cos(r) * dist)
		cp.y = maxf(Bt.H(cp.x, cp.z) + float(cam.get("h", 2.0)), tg.y + float(cam.get("h_min", -1000.0)))
		if _frei(cp, tg + Vector3(0, float(cam.get("lh", 0.0)), 0)):
			best = a
			break
	_zc[key] = [tg, best]
	return _zc[key]


# =======================================================================================================================
# the two trailers: the list of shots
# =======================================================================================================================
func einstellungen(id: String) -> Array:
	trailer = id
	var out: Array = grossvater() if id == "grossvater" else maggie()
	var t := 0.0
	for sh in out:
		sh["t0"] = t
		t += float(sh["d"])
	return out


func _brueckenhoehe() -> float:
	var br := Bt.GORGE_BRIDGE
	return minf(Bt.H(br.x - 13.0, br.y), Bt.H(br.x + 13.0, br.y)) - 0.6


func _w(d: float, auf: String, cam: Dictionary, more := {}) -> Dictionary:
	var sh := {"d": d, "art": "welt", "auf": auf, "cam": cam}
	sh.merge(more, true)
	return sh


func _tafel(d: float, text: String, more := {}) -> Dictionary:
	var sh := {"d": d, "art": "tafel", "text": text}
	sh.merge(more, true)
	return sh


# ---- «Die Karte des Grossvaters» (≈ 3 Min.) ----------------------------------------------------------------------------------
func grossvater() -> Array:
	var ch := Bt.CHAPEL
	var hut := Vector2(float(Orte.B_HUT[0]), float(Orte.B_HUT[1]))
	var wf := Bt.GORGE_HEAD
	var br := Bt.GORGE_BRIDGE
	var cp: Array = Bt.SPOTS["huette"]
	var camp := Vector2(float(cp[1]), float(cp[2]))
	var kz: Array = Bt.VIEWPOINTS[2]                       # Chanzle über dem Gumpisee
	var kp := Vector2(float(kz[3]), float(kz[4]))
	var L := []
	L.append(_tafel(4.0, T.t("MoveEye Sim zeigt"), {"klein": true, "ton": [[0.0, "loop", "wind", -16.0, 3.0]]}))
	L.append(_w(12.0, "g_tal", {"k": "ziel", "z": Vector3(hut.x, 0.0, hut.y + 120), "dist": 620.0, "h": 140.0, "ang": 185.0, "dreh": 6.0,
			"naeher": 0.22, "fov": 55.0},
			{"zeit": 8.2, "wetter": "clear", "fade_in": 2.0, "say": [[2.0, T.t("Jedes Tal hat seine Geschichten.")]],
			"ton": [[0.0, "loop", "pad_ruhig", -10.0, 4.0], [5.0, "one", "kuhglocke", -24.0]]}))
	L.append(_w(10.0, "g_kapelle", {"k": "fahrt", "a": Vector3(ch.x + 9, 1.7, ch.y - 24), "b": Vector3(ch.x + 4, 1.6, ch.y - 15),
			"la": Vector3(ch.x - 4, 1.4, ch.y + 6), "fov": 52.0},
			{"zeit": 8.0, "say": [[1.0, T.t("Diese hier beginnt mit einem Brief.")]]}))
	L.append({"d": 12.0, "art": "papier", "say": [[1.5, T.t("«Die Karte gehört jetzt dir – lies sie mit der Sonne.»")]],
			"ton": [[0.2, "one", "papier", -8.0], [6.0, "one", "papier", -12.0]]})
	L.append(_tafel(5.0, T.t("Fünf Stücke einer alten Karte."), {"ton": [[0.0, "one", "pauke", -6.0]]}))
	L.append(_w(10.0, "g_weg", {"k": "folge", "fig": "held", "off": Vector3(0.8, 2.3, 5.5), "off_b": Vector3(2.6, 1.9, 3.6),
			"look": Vector3(0, 1.4, 6.0), "fov": 52.0},
			{"zeit": 10.0, "ton": [[0.0, "loop", "schritte", -14.0, 1.0], [0.0, "loop", "pulse", -16.0, 6.0]]}))
	L.append(_w(9.0, "g_alp", {"k": "ziel", "z": Vector3(hut.x + 10.0, 1.4, hut.y + 7.0), "dist": 24.0, "h": 2.6, "ang": 290.0, "dreh": 12.0,
			"naeher": 0.25, "h_min": 0.5, "fov": 50.0},
			{"zeit": 11.0, "say": [[0.6, T.t("Menschen, die das Tal kennen.")]],
			"ton": [[0.0, "stop", "schritte", 0.5], [0.5, "one", "kuhglocke", -14.0], [4.0, "one", "kuhglocke", -18.0]]}))
	L.append(_w(8.0, "g_wasserfall", {"k": "ziel", "z": Vector3(wf.x, 3.0, wf.y), "dist": 34.0, "h": 2.0, "ang": 190.0, "dreh": -8.0,
			"naeher": 0.2, "lh": 2.0, "h_min": -4.0, "fov": 60.0},
			{"zeit": 12.5, "say": [[0.6, T.t("Wege, die sich gabeln.")]],
			"ton": [[0.0, "loop", "wasser", -8.0, 1.0], [7.5, "stop", "wasser", 0.8]]}))
	L.append(_w(8.0, "g_bruecke", {"k": "ziel", "z": Vector3(br.x, -1.0, br.y), "bruecke": true, "dist": 28.0, "h": 1.6, "ang": 10.0,
			"dreh": 10.0, "h_min": -14.0, "fov": 50.0},
			{"zeit": 13.0, "say": [[0.8, T.t("Brücken, die schwanken.")]],
			"ton": [[0.0, "loop", "wind", -10.0, 1.0], [2.0, "one", "knacken", -14.0], [5.0, "one", "knacken", -16.0]]}))
	L.append(_tafel(5.0, T.t("Fünf Kapitel. Ein Tal voller Rätsel."), {"ton": [[0.0, "one", "pauke", -5.0]]}))
	L.append(_w(8.0, "g_ruedi", {"k": "ziel", "z": Vector3(-82.0, 1.2, 178.0), "dist": 7.0, "h": 1.6, "ang": 200.0, "dreh": 14.0,
			"naeher": 0.15, "h_min": 0.3, "fov": 48.0},
			{"zeit": 9.5, "say": [[0.5, T.t("Wer genau hinschaut, findet die Zeichen.")]],
			"ton": [[1.5, "one", "pfiff", -16.0], [5.0, "one", "pfiff", -20.0]]}))
	L.append(_w(8.0, "g_wolken", {"k": "folge", "fig": "held", "off": Vector3(-1.0, 1.3, 3.5), "look": Vector3(0, 5.0, 20.0), "fov": 60.0},
			{"zeit": 15.5, "wetter": "cloudy", "say": [[0.5, T.t("Doch das Wetter am Berg wartet auf niemanden.")]],
			"ton": [[0.0, "loop", "wind", -6.0, 3.0], [0.0, "loop", "pad_dunkel", -12.0, 4.0], [0.0, "stop", "pad_ruhig", 4.0]]}))
	L.append(_w(3.5, "g_rennen", {"k": "folge", "fig": "held", "off": Vector3(1.5, 1.4, -4.0), "look": Vector3(0, 1.3, 0.0), "fov": 62.0,
			"wackel": 0.25}, {"zeit": 16.0, "wetter": "rain", "donner": true, "nebel_max": 0.002,
			"ton": [[0.0, "loop", "regen", -8.0, 0.4], [0.0, "loop", "rennen", -10.0, 0.2], [0.0, "loop", "ostinato", -14.0, 0.5],
				[0.0, "stop", "pulse", 0.5]]}))
	L.append(_w(3.5, "g_blitz", {"k": "ziel", "z": Vector3(hut.x + 40, 120.0, hut.y + 400), "dist": 420.0, "h": 6.0, "ang": 185.0, "dreh": 3.0,
			"fov": 64.0},
			{"zeit": 20.6, "wetter": "rain", "donner": true, "blitz": [0.6, 0.75], "nebel_max": 0.0006,
			"ton": [[0.0, "stop", "rennen", 0.3], [0.65, "one", "donner", -2.0]]}))
	L.append(_w(11.0, "g_lager", {"k": "kreis", "kopf": true, "r": 7.5, "r1": 5.0, "h": 2.4, "a0": 200.0, "a1": 245.0,
			"lh": 1.3, "fov": 55.0},
			{"zeit": 21.9, "wetter": "clear", "fade_in": 1.0, "nachtlicht": 0.32,
			"say": [[0.8, T.t("Und wenn es Nacht wird …")], [5.5, T.t("… wacht MoveEye.")]],
			"ton": [[0.0, "stop", "regen", 1.5], [0.0, "stop", "ostinato", 1.0], [0.0, "loop", "wind", -18.0, 2.0],
				[0.0, "loop", "pulse", -16.0, 3.0]]}))
	# night montage: quick cuts
	var nacht := [["g_augen", {"k": "fahrt", "a": Vector3(camp.x - 6, 1.4, camp.y + 2), "b": Vector3(camp.x - 8, 1.4, camp.y + 4),
					"la": Vector3(camp.x - 40, 1.0, camp.y + 30), "fov": 42.0}, "pauke"],
			["g_kopf", {"k": "kreis", "kopf": true, "r": 1.6, "h": 1.7, "a0": 160.0, "a1": 140.0, "lh": 1.4, "fov": 50.0}, "whoosh"],
			["g_fuchs", {"k": "fahrt", "a": Vector3(camp.x + 7, 0.8, camp.y + 6), "la": Vector3(camp.x - 4, 0.5, camp.y + 9), "fov": 50.0}, "rascheln"],
			["g_zelt", {"k": "fahrt", "a": Vector3(camp.x + 3, 1.0, camp.y - 7), "b": Vector3(camp.x + 2, 1.0, camp.y - 5.5),
					"la": Vector3(camp.x - 3, 0.8, camp.y + 1), "fov": 48.0}, "pauke"],
			["g_augen2", {"k": "fahrt", "a": Vector3(camp.x - 9, 1.2, camp.y + 5), "b": Vector3(camp.x - 12, 1.2, camp.y + 9),
					"la": Vector3(camp.x - 30, 1.0, camp.y + 25), "fov": 38.0}, "knacken"],
			["g_kopf2", {"k": "kreis", "kopf": true, "r": 1.3, "h": 1.5, "a0": 230.0, "a1": 260.0, "lh": 1.4, "fov": 46.0}, "pauke"]]
	for i in range(nacht.size()):
		var n: Array = nacht[i]
		var more := {"zeit": 22.6, "wetter": "clear", "nachtlicht": 0.36, "ton": [[0.0, "one", n[2], -6.0 if n[2] == "pauke" else -10.0]]}
		if i == 0:
			more["ton"].append([0.0, "loop", "ostinato", -16.0, 0.5])
			more["ton"].append([0.0, "stop", "pulse", 0.5])
		L.append(_w(2.3, str(n[0]), n[1], more))
	# flash montage (white flashes between the shots), a riser into the silence
	var blitz := [["g_bruecke", {"k": "ziel", "z": Vector3(br.x, -1.0, br.y), "bruecke": true, "dist": 18.0, "h": 1.6, "ang": 30.0,
					"h_min": -10.0, "fov": 50.0}, 13.0],
			["g_wasserfall", {"k": "ziel", "z": Vector3(wf.x, 3.0, wf.y), "dist": 26.0, "h": 2.0, "ang": 200.0, "lh": 2.0, "h_min": -4.0, "fov": 55.0}, 12.5],
			["g_alp", {"k": "ziel", "z": Vector3(hut.x + 10.0, 1.2, hut.y + 7.0), "dist": 14.0, "h": 1.6, "ang": 300.0, "h_min": 0.5, "fov": 45.0}, 11.0],
			["g_augen", {"k": "fahrt", "a": Vector3(camp.x - 10, 1.3, camp.y + 6), "la": Vector3(camp.x - 40, 1.0, camp.y + 30), "fov": 34.0}, 22.2],
			["g_blitz", {"k": "ziel", "z": Vector3(hut.x + 40, 120.0, hut.y + 400), "dist": 380.0, "h": 6.0, "ang": 175.0, "fov": 70.0,
					"nebel_max": 0.0006}, 20.6],
			["g_kapelle", {"k": "fahrt", "a": Vector3(ch.x + 3, 1.2, ch.y - 12), "la": Vector3(ch.x, 4.0, ch.y), "fov": 50.0}, 8.0],
			["g_rennen", {"k": "folge", "fig": "held", "off": Vector3(-1.2, 1.0, 2.5), "look": Vector3(0, 1.2, 4.0), "fov": 64.0}, 16.0],
			["g_kopf", {"k": "kreis", "kopf": true, "r": 1.1, "h": 1.6, "a0": 190.0, "a1": 200.0, "lh": 1.4, "fov": 44.0}, 22.6]]
	for i in range(blitz.size()):
		var b: Array = blitz[i]
		var more2 := {"zeit": float(b[2]), "wetter": "rain" if str(b[0]) == "g_blitz" else "clear", "blitz": [0.0],
				"nebel_max": float((b[1] as Dictionary).get("nebel_max", 0.0)),
				"ton": [[0.0, "one", "whoosh", -14.0]]}
		if i == 0:
			more2["ton"] = [[0.0, "one", "whoosh", -14.0], [0.0, "one", "riser", -6.0, 3.2]]
		if float(b[2]) > 21.0:
			more2["nachtlicht"] = 0.16
		L.append(_w(0.9, str(b[0]), b[1], more2))
	L.append({"d": 2.8, "art": "schwarz", "ton": [[0.0, "stille", 0.12]]})
	L.append(_tafel(5.0, T.t("Wer war es?"), {"klein": true, "ton": [[0.6, "one", "rascheln", -12.0], [3.2, "one", "knacken", -10.0]]}))
	L.append({"d": 9.0, "art": "titel", "text": T.t("Die Karte des Grossvaters"), "sub": T.t("5 Kapitel, je 30–45 Min.") + "  ·  " + T.t("ab %d Jahren", [8]),
			"ton": [[0.0, "one", "boom", -2.0], [0.0, "loop", "pad_dunkel", -12.0, 0.2], [5.5, "loop", "pad_hell", -12.0, 3.0],
				[5.5, "stop", "pad_dunkel", 3.0]]})
	L.append(_w(14.0, "g_morgen", {"k": "ziel", "z": Vector3(kp.x + 1.0, 1.3, kp.y - 1.0), "dist": 7.0, "h": 1.9, "ang": 70.0, "dreh": 30.0,
			"h_min": 0.6, "fov": 55.0},
			{"zeit": 7.6, "wetter": "clear", "fade_in": 1.5,
			"say": [[1.0, T.t("Fünf Kapitel. Ein Geheimnis. Deine Karte.")], [7.5, T.t("Lies sie mit der Sonne.")]],
			"ton": [[0.0, "loop", "wind", -20.0, 2.0]]}))
	L.append({"d": 10.0, "art": "ende", "text": T.t("Die Karte des Grossvaters"),
			"say": [[0.8, T.t("Jetzt spielen.")]], "ton": [[0.0, "one", "chime", -14.0], [7.0, "stille", 3.0]]})
	return L


# ---- «Maggie und der Bergkristall» (≈ 3 Min.) --------------------------------------------------------------------------------
func maggie() -> Array:
	var sp := Welt.INTRO_SPOT
	var dg := Welt.INTRO_DIG
	var mo := Bt.MOOR
	var uh := Bt.UPPER_HUT
	var L := []
	L.append(_tafel(4.0, T.t("MoveEye Sim zeigt"), {"klein": true, "ton": [[0.0, "loop", "wind", -18.0, 3.0], [1.8, "one", "bellen", -26.0]]}))
	L.append(_w(12.0, "m_alp", {"k": "fahrt", "a": Vector3(sp.x + 70, 45, sp.y + 90), "b": Vector3(sp.x + 14, 6.0, sp.y + 16),
			"la": Vector3(sp.x - 10, 0.5, sp.y + 10), "lb": Vector3(sp.x - 14, 1.0, sp.y + 12), "fov": 55.0},
			{"zeit": 16.3, "wetter": "clear", "fade_in": 2.0, "say": [[2.0, T.t("Ein ruhiger Herbstabend auf der Alp.")]],
			"ton": [[0.0, "loop", "pad_ruhig", -10.0, 4.0]]}))
	L.append(_w(8.0, "m_spaziergang", {"k": "folge", "fig": "maggie", "off": Vector3(2.2, 1.2, -2.2), "off_b": Vector3(2.6, 1.3, 0.4),
			"look": Vector3(0, 0.4, 0.0), "fov": 50.0},
			{"zeit": 16.4, "say": [[0.6, T.t("Du und Maggie, euer kleiner Hund.")]], "ton": [[0.0, "loop", "schritte", -16.0, 1.0]]}))
	L.append(_w(8.0, "m_riechen", {"k": "folge", "fig": "maggie", "off": Vector3(-0.8, 1.1, 2.6), "look": Vector3(0, 0.3, 3.0), "fov": 55.0},
			{"zeit": 16.5, "say": [[0.5, T.t("Bis Maggie plötzlich etwas riecht …")]],
			"ton": [[0.0, "stop", "schritte", 0.6], [3.4, "one", "bellen", -12.0], [4.0, "loop", "pulse", -18.0, 3.0]]}))
	L.append(_w(11.0, "m_graben", {"k": "kreis", "c": Vector3(dg.x, 0, dg.y), "r": 2.8, "r1": 2.2, "h": 0.9, "a0": 130.0, "a1": 165.0,
			"lh": 0.5, "fov": 50.0},
			{"zeit": 16.6, "say": [[6.0, T.t("Ein Bergkristall. Er leuchtet ganz von selbst.")]],
			"ton": [[0.0, "one", "rascheln", -14.0], [5.0, "one", "chime", -6.0], [5.0, "loop", "pad_hell", -12.0, 2.0], [5.0, "stop", "pad_ruhig", 2.0],
				[5.0, "stop", "pulse", 2.0]]}))
	L.append(_w(4.0, "m_zukunft", {"k": "fahrt", "a": Vector3(-300, 160, -40), "b": Vector3(-420, 140, -120),
			"la": Vector3(-620, 0, -220), "fov": 60.0},
			{"zeit": 16.8, "tint": Color(0.55, 0.8, 1.0, 0.28), "say": [[0.4, T.t("In seinem Licht: Bilder der Zukunft.")]],
			"ton": [[0.0, "one", "whoosh", -12.0]]}))
	L.append(_w(4.0, "m_zukunft", {"k": "fahrt", "a": Vector3(330, 120, 160), "b": Vector3(420, 110, 230),
			"la": Vector3(600, 20, 380), "fov": 60.0},
			{"zeit": 16.0, "tint": Color(0.55, 0.8, 1.0, 0.28), "ton": [[0.0, "one", "whoosh", -12.0]]}))
	L.append(_tafel(5.0, T.t("Doch der Kristall darf nicht in falsche Hände geraten."),
			{"ton": [[0.0, "one", "pauke", -5.0], [0.0, "stop", "pad_hell", 1.5], [0.0, "loop", "pad_dunkel", -11.0, 2.0]]}))
	L.append(_w(10.0, "m_moor", {"k": "ziel", "z": Vector3(mo.x - 8.0, 0.7, mo.y), "dist": 18.0, "h": 1.6, "ang": 90.0, "naeher": 0.35,
			"fov": 50.0},
			{"zeit": 18.6, "wetter": "cloudy", "nebel": 0.016, "say": [[1.0, T.t("Böse Tiere wollen ihn haben.")]],
			"ton": [[0.0, "loop", "wind", -12.0, 2.0], [2.0, "one", "grunzen", -10.0], [6.5, "one", "grunzen", -8.0]]}))
	L.append(_w(5.0, "m_augen", {"k": "fahrt", "a": Vector3(sp.x - 18, 1.3, sp.y + 30), "b": Vector3(sp.x - 20, 1.3, sp.y + 32),
			"la": Vector3(sp.x - 30, 0.8, sp.y + 41), "fov": 40.0},
			{"zeit": 21.8, "nebel": 0.012, "nachtlicht": 0.32, "ton": [[1.0, "one", "knurren", -10.0], [3.5, "one", "knacken", -12.0]]}))
	L.append(_w(4.0, "m_knurren", {"k": "folge", "fig": "maggie", "off": Vector3(0.9, 1.0, -1.6), "look": Vector3(0, 0.35, 0.0), "fov": 46.0},
			{"zeit": 21.8, "nebel": 0.012, "nachtlicht": 0.34, "ton": [[0.2, "one", "knurren", -6.0]]}))
	L.append(_tafel(5.0, T.t("Vier Jahreszeiten. Vier Täler."), {"ton": [[0.0, "one", "pauke", -5.0]]}))
	L.append(_w(10.0, "m_woelfe", {"k": "ziel", "z": Vector3(uh.x + 6.0, 0.9, uh.y + 8.0), "dist": 28.0, "h": 1.8, "ang": 240.0, "naeher": 0.2,
			"dreh": 8.0, "fov": 48.0},
			{"zeit": 20.4, "wetter": "clear", "schnee": true, "nachtlicht": 0.36, "say": [[1.2, T.t("Wölfe im Schnee …")]],
			"ton": [[0.0, "loop", "wind", -8.0, 1.0], [0.5, "one", "heulen", -8.0], [5.0, "one", "heulen", -13.0]]}))
	L.append(_w(6.0, "m_fackel", {"k": "folge", "fig": "held", "off": Vector3(2.0, 1.6, -3.0), "off_b": Vector3(2.6, 1.7, -2.6),
			"look": Vector3(0, 1.3, 0.0), "fov": 55.0},
			{"zeit": 20.6, "wetter": "clear", "schnee": true, "nachtlicht": 0.34, "ton": [[0.0, "one", "whoosh", -8.0], [2.0, "one", "knurren", -12.0]]}))
	L.append(_w(5.0, "m_kraehen", {"k": "ziel", "z": Vector3(-40.0, 14.0, -625.0), "dist": 45.0, "h": 2.0, "ang": 150.0, "lh": 4.0,
			"fov": 62.0},
			{"zeit": 13.5, "wetter": "cloudy", "nebel_max": 0.002, "say": [[0.4, T.t("Krähen über dem Wald …")]],
			"ton": [[0.0, "stop", "wind", 1.0], [0.3, "one", "kraehen", -6.0], [1.6, "one", "kraehen", -10.0], [3.0, "one", "kraehen", -12.0]]}))
	L.append(_w(5.0, "m_viper", {"k": "ziel", "z": Vector3(_viper_ort().x, 0.15, _viper_ort().y), "dist": 1.6, "h": 0.75, "ang": 35.0, "naeher": 0.2,
			"dreh": 12.0, "fov": 45.0},
			{"zeit": 15.4, "wetter": "clear", "say": [[0.4, T.t("… und Vipern zwischen warmen Steinen.")]],
			"ton": [[1.2, "one", "zischen", -10.0]]}))
	L.append(_w(8.0, "m_mutig", {"k": "folge", "fig": "maggie", "off": Vector3(-0.5, 0.9, -1.9), "off_b": Vector3(-0.3, 0.8, -1.4),
			"look": Vector3(0, 0.4, 0.0), "fov": 48.0},
			{"zeit": 21.5, "nebel": 0.01, "nachtlicht": 0.34, "say": [[0.6, T.t("Aber Maggie hat eine sehr gute Nase.")], [4.6, T.t("Und sie hat keine Angst.")]],
			"ton": [[0.0, "loop", "pulse", -14.0, 1.0], [3.0, "one", "bellen", -6.0]]}))
	# the montage: faster and faster
	var mont := [["m_rennen", {"k": "folge", "fig": "maggie", "off": Vector3(1.0, 1.0, -2.6), "look": Vector3(0, 0.3, 0.0), "fov": 60.0, "wackel": 0.08}, 16.5, "whoosh"],
			["m_augen", {"k": "fahrt", "a": Vector3(sp.x - 22, 1.3, sp.y + 34), "la": Vector3(sp.x - 30, 0.8, sp.y + 41), "fov": 34.0}, 21.8, "pauke"],
			["m_moor", {"k": "ziel", "z": Vector3(mo.x - 6.0, 0.6, mo.y), "dist": 12.0, "h": 0.9, "ang": 80.0, "naeher": 0.3, "fov": 44.0, "wackel": 0.12}, 18.6, "grunzen"],
			["m_fackel", {"k": "folge", "fig": "held", "off": Vector3(-1.4, 1.5, 2.6), "look": Vector3(0, 1.2, 6.0), "fov": 56.0}, 20.6, "whoosh"],
			["m_kristall", {"k": "folge", "fig": "held", "off": Vector3(1.3, 1.45, -1.5), "off_b": Vector3(0.9, 1.4, -1.6), "look": Vector3(0.38, 1.25, 0.0),
					"fov": 40.0}, 21.0, "chime"],
			["m_woelfe", {"k": "ziel", "z": Vector3(uh.x + 6.0, 0.9, uh.y + 8.0), "dist": 16.0, "h": 1.3, "ang": 250.0, "fov": 40.0}, 20.4, "heulen"],
			["m_nebellauf", {"k": "folge", "fig": "held", "off": Vector3(1.0, 1.4, -3.2), "look": Vector3(0, 1.3, 0.0), "fov": 62.0, "wackel": 0.2}, 18.6, "pauke"],
			["m_bellen", {"k": "folge", "fig": "maggie", "off": Vector3(0.7, 0.9, -1.4), "look": Vector3(0, 0.35, 0.0), "fov": 44.0}, 21.5, "bellen"],
			["m_rennen", {"k": "folge", "fig": "maggie", "off": Vector3(-1.2, 1.1, 2.2), "look": Vector3(0, 0.3, 3.0), "fov": 60.0}, 16.5, "whoosh"],
			["m_augen", {"k": "fahrt", "a": Vector3(sp.x - 24, 1.3, sp.y + 36), "la": Vector3(sp.x - 30, 0.8, sp.y + 41), "fov": 30.0}, 21.8, "pauke"]]
	for i in range(mont.size()):
		var e: Array = mont[i]
		var d := 2.2 if i < 6 else 1.6
		var more := {"zeit": float(e[2]), "wetter": "cloudy" if str(e[0]) in ["m_moor", "m_nebellauf"] else "clear",
				"schnee": str(e[0]) in ["m_woelfe", "m_fackel"],
				"nebel": 0.016 if str(e[0]) in ["m_moor", "m_nebellauf"] else 0.01, "nachtlicht": 0.34 if float(e[2]) > 20.0 else 0.0,
				"ton": [[0.0, "one", e[3], -6.0 if e[3] == "pauke" else -10.0]]}
		if i == 0:
			more["say"] = [[0.2, T.t("Durch Nebel. Durch Schnee. Durch die Nacht.")]]
			more["ton"].append([0.0, "loop", "ostinato", -14.0, 0.5])
			more["ton"].append([0.0, "stop", "pulse", 0.5])
		L.append(_w(d, str(e[0]), e[1], more))
	for i in range(5):
		L.append(_w(1.0, "m_kristall", {"k": "folge", "fig": "held", "off": Vector3(1.6 - 0.25 * i, 1.35 + 0.05 * i, -1.2 - 0.15 * i),
				"look": Vector3(0.38, 1.25, 0.0), "fov": 40.0 - 3.0 * i}, {"zeit": 21.0, "blitz": [0.0], "nachtlicht": 0.3, "ton": [[0.0, "one", "riser", -6.0, 1.0]] if i == 0 else []}))
	L.append({"d": 3.0, "art": "schwarz", "ton": [[0.0, "stille", 0.12]]})
	L.append(_w(6.0, "m_dunkel", {"k": "folge", "fig": "maggie", "off": Vector3(0.6, 0.8, -1.4), "look": Vector3(0, 0.38, 0.0), "fov": 44.0},
			{"zeit": 22.4, "nebel": 0.02, "nachtlicht": 0.16, "ton": [[1.2, "one", "knurren", -16.0], [4.0, "one", "chime", -4.0]], "blitz": [4.0]}))
	L.append({"d": 9.0, "art": "titel", "text": T.t("Maggie und der Bergkristall"), "sub": T.t("etwa 2 Stunden") + "  ·  " + T.t("ab %d Jahren", [10]),
			"kristall": true,
			"ton": [[0.0, "one", "boom", -2.0], [0.0, "loop", "pad_hell", -12.0, 1.0], [0.0, "stop", "pad_dunkel", 2.0], [0.0, "stop", "ostinato", 0.3]]})
	L.append(_w(14.0, "m_sterne", {"k": "ziel", "z": Vector3(sp.x + 0.4, 0.6, sp.y - 0.4), "dist": 4.0, "h": 1.1, "ang": 205.0, "dreh": 35.0,
			"naeher": -0.9, "fov": 52.0},
			{"zeit": 22.3, "fade_in": 1.5, "nachtlicht": 0.32,
			"say": [[1.0, T.t("Vier Jahreszeiten. Ein Kristall. Und Maggie.")], [7.0, T.t("Bring ihn sicher hinauf.")]],
			"ton": [[0.0, "loop", "wind", -22.0, 2.0]]}))
	L.append({"d": 10.0, "art": "ende", "text": T.t("Maggie und der Bergkristall"), "kristall": true,
			"say": [[0.8, T.t("Jetzt spielen.")]], "ton": [[0.0, "one", "chime", -12.0], [7.0, "stille", 3.0]]})
	return L


# =======================================================================================================================
# set-up and tick of the shots (auf = einmal beim Schnitt, tick = jedes Bild mit rel = Sekunden seit dem Schnitt)
# =======================================================================================================================
func aufbau(sh: Dictionary) -> void:
	_shot = sh
	dinge_aus()
	var fn := str(sh.get("auf", ""))
	if fn != "" and has_method(fn):
		call(fn)


func tick(sh: Dictionary, rel: float, dt: float) -> void:
	var fn := str(sh.get("auf", "")) + "_tick"
	if has_method(fn):
		call(fn, rel, dt)


func _held() -> Node3D:
	return fig("held", "person", {"jacke": _held_col, "look": _held_look, "pack": true})


# ---- Grossvater ----------------------------------------------------------------------------------------------------------
func g_tal() -> void:
	nur([])


func g_kapelle() -> void:
	var a := _held()
	nur(["held"])
	var ch := Bt.CHAPEL
	stell(a, ch.x - 2.0, ch.y + 4.0, ch.x - 6.0, ch.y + 30.0)
	idle(a, "look", 1.0e4)


func g_weg() -> void:
	_held()
	nur(["held"])


func g_weg_tick(rel: float, _dt: float) -> void:
	pfad(figs["held"], [Vector2(172, -60), Vector2(160, -45), Vector2(130, -28), Vector2(110, -20)], 1.35, rel + 2.0)


func g_alp() -> void:
	var hut := Vector2(float(Orte.B_HUT[0]), float(Orte.B_HUT[1]))
	var fs: Dictionary = FD.FIG["aelpler"]
	var sepp := fig("sepp", "person", {"jacke": fs["jacke"], "look": {"hat": "cap" if bool(fs.get("cap", false)) else ""}})
	stell(sepp, hut.x + 9.0, hut.y + 8.0, hut.x + 22.0, hut.y + 18.0)
	idle(sepp, "talk", 1.0e4)
	var names := ["sepp"]
	for i in range(4):
		var k := "kuh%d" % i
		var c := fig(k, "cow")
		var a := float(i) * 1.7
		stell(c, hut.x + 14.0 + cos(a) * (6.0 + i), hut.y + 2.0 + sin(a) * (5.0 + i), hut.x + 30.0, hut.y + 30.0 * cos(a))
		idle(c, "graze", 1.0e4)
		names.append(k)
	nur(names)


func g_wasserfall() -> void:
	nur([])


func g_bruecke() -> void:
	_held()
	nur(["held"])


func g_bruecke_tick(rel: float, _dt: float) -> void:
	var br := Bt.GORGE_BRIDGE
	var rim := minf(Bt.H(br.x - 13.0, br.y), Bt.H(br.x + 13.0, br.y))
	var a: Node3D = figs["held"]
	var k := clampf((rel + 1.0) * 1.05 / 26.0, 0.0, 1.0)
	var sag := 1.4 * sin(PI * k)
	pfad(a, [Vector2(br.x + 13.0, br.y), Vector2(br.x - 13.0, br.y)], 1.05, rel + 1.0, rim - 0.6 - sag + 0.05)


func g_ruedi() -> void:
	var fr: Dictionary = FD.FIG["wildhueter"]
	var r := fig("ruedi", "person", {"jacke": fr["jacke"], "look": {"hat": "cap"}, "pack": true, "pack_col": Color(0.25, 0.27, 0.18)})
	stell(r, -84.0, 180.0, -60.0, 150.0)
	idle(r, "photo", 1.0e4)
	if not figs.has("murmel"):
		figs["murmel"] = marmot(Vector3(-70, 0, 168), Vector3(-84, 0, 180))
	stell(figs["murmel"], -70.0, 168.0, -84.0, 180.0)
	nur(["ruedi", "murmel"])


func g_wolken() -> void:
	var a := _held()
	nur(["held"])
	stell(a, 120.0, -24.0, 60.0, 100.0)
	idle(a, "look", 1.0e4)


func g_rennen() -> void:
	_held()
	nur(["held"])


func g_rennen_tick(rel: float, _dt: float) -> void:
	pfad(figs["held"], [Vector2(96, -14), Vector2(76, -6), Vector2(62, 2)], 3.3, rel + 1.0)


func g_blitz() -> void:
	nur([])


func g_lager() -> void:
	nur([])


func g_augen() -> void:
	nur(["hirsch"])
	var cp: Array = Bt.SPOTS["huette"]
	var c := Vector2(float(cp[1]), float(cp[2]))
	var h := fig("hirsch", "deer")
	stell(h, c.x - 22.0, c.y + 15.0, c.x, c.y)
	idle(h, "stare", 1.0e4)
	augen("waldaugen", [Vector3(c.x - 18, 0.9, c.y + 15), Vector3(c.x - 15, 0.6, c.y + 17), Vector3(c.x - 21, 1.0, c.y + 12)])


func g_augen_tick(rel: float, _dt: float) -> void:
	tier_augen(figs.get("hirsch", null), 5.0)
	augen_tick("waldaugen", rel + 0.3, 0.0, 0.5)


func g_augen2() -> void:
	g_augen()


func g_augen2_tick(rel: float, dt: float) -> void:
	g_augen_tick(rel + 2.0, dt)


func g_kopf() -> void:
	nur([])


func g_kopf2() -> void:
	nur([])


func g_fuchs() -> void:
	nur(["fuchs"])
	fig("fuchs", "fox")


func g_fuchs_tick(rel: float, _dt: float) -> void:
	var cp: Array = Bt.SPOTS["huette"]
	var c := Vector2(float(cp[1]), float(cp[2]))
	var f: Node3D = figs["fuchs"]
	pfad(f, [Vector2(c.x + 6, c.y + 12), Vector2(c.x - 2, c.y + 9), Vector2(c.x - 10, c.y + 7)], 2.4, rel)
	tier_augen(f, 3.0)


func g_zelt() -> void:
	nur([])
	var cp: Array = Bt.SPOTS["huette"]
	var c := Vector2(float(cp[1]), float(cp[2]))
	var n := ding("zeltlicht")
	if n == null:
		n = _add("zeltlicht", Node3D.new())
		var l := OmniLight3D.new()
		l.name = "light"
		l.light_color = Color(1.0, 0.8, 0.5)
		l.light_energy = 1.4
		l.omni_range = 3.0
		l.shadow_enabled = false
		n.add_child(l)
	n.visible = true
	n.position = G(c.x - 1.5, c.y + 1.5, 0.6)


func g_morgen() -> void:
	var a := _held()
	nur(["held"])
	var kz: Array = Bt.VIEWPOINTS[2]
	stell(a, float(kz[3]) + 1.0, float(kz[4]) - 1.0, float(kz[3]) - 40.0, float(kz[4]) + 20.0)
	idle(a, "look", 1.0e4)


# ---- Maggie --------------------------------------------------------------------------------------------------------------
func _mag() -> Node3D:
	maggie_bauen()
	return hund()


func m_alp() -> void:
	_held()
	_mag()
	nur(["held", "maggie"])


func m_alp_tick(rel: float, _dt: float) -> void:
	var sp := Welt.INTRO_SPOT
	var w := [Vector2(sp.x + 8, sp.y - 4), Vector2(sp.x - 2, sp.y + 4), Vector2(sp.x - 10, sp.y + 10)]
	pfad(figs["held"], w, 1.1, rel)
	var h := hund()
	if h != null:
		pfad(h, [w[0] + Vector2(1.2, 1.0), w[1] + Vector2(1.2, 1.0), w[2] + Vector2(1.2, 1.0)], 1.1, rel + 1.4)


func m_spaziergang() -> void:
	m_alp()


func m_spaziergang_tick(rel: float, dt: float) -> void:
	m_alp_tick(rel + 12.0, dt)


func m_riechen() -> void:
	m_alp()


func m_riechen_tick(rel: float, _dt: float) -> void:
	var sp := Welt.INTRO_SPOT
	var dg := Welt.INTRO_DIG
	var a: Node3D = figs["held"]
	stell(a, sp.x - 6.0, sp.y + 7.0, dg.x, dg.y)
	var h := hund()
	if h == null:
		return
	var p0 := Vector2(sp.x - 4.6, sp.y + 8.4)
	if rel < 3.2:
		stell(h, p0.x, p0.y, dg.x, dg.y)
		idle(h, "sniff", 10.0)
	else:
		pfad(h, [p0, Vector2(dg.x + 0.4, dg.y - 0.6)], 4.2, rel - 3.4)
	var b := ding("saeule")
	if b == null:
		b = _saeule()
	b.visible = true
	b.position = G(dg.x, dg.y, 35.0)


func m_graben() -> void:
	m_alp()
	var dg := Welt.INTRO_DIG
	stell(figs["held"], dg.x + 2.4, dg.y - 2.6, dg.x, dg.y)
	idle(figs["held"], "look", 1.0e4)
	var h := hund()
	if h != null:
		stell(h, dg.x + 0.3, dg.y - 0.5, dg.x, dg.y)
	var d := ding("erde")
	if d == null:
		d = _add("erde", Node3D.new())
		var p := Welt.dirt()
		p.name = "p"
		d.add_child(p)
	d.visible = true
	d.position = G(dg.x, dg.y, 0.1)


func m_graben_tick(rel: float, _dt: float) -> void:
	var dg := Welt.INTRO_DIG
	var h := hund()
	if h != null:
		idle(h, "root" if rel < 5.0 else "sit", 10.0)
	var d := ding("erde")
	if d != null:
		(d.get_node("p") as CPUParticles3D).emitting = rel < 5.0
	if rel >= 4.6:
		var k := kristall("kristall_gross", 1.6)
		k.position = G(dg.x, dg.y, -0.3 + 1.4 * ein(rel, 4.6, 7.0))
		k.rotation.y = rel * 0.8
		licht(k.get_node("c"), 0.8 + 1.6 * ein(rel, 4.6, 6.0))
	var b := ding("saeule")
	if b == null:
		b = _saeule()
	b.visible = rel < 4.6
	b.position = G(dg.x, dg.y, 35.0)


func m_zukunft() -> void:
	nur([])


func m_moor() -> void:
	nur(["sau0", "sau1", "sau2"])
	var mo := Bt.MOOR
	for i in range(3):
		var s_ := fig("sau%d" % i, "boar")
		stell(s_, mo.x - 4.0 - i * 3.5, mo.y + 2.0 - i * 2.2, mo.x + 10.0, mo.y)
		idle(s_, "root", 1.0e4)


func m_moor_tick(rel: float, _dt: float) -> void:
	var mo := Bt.MOOR
	var s0: Node3D = figs["sau0"]
	if rel > 4.0:
		pfad(s0, [Vector2(mo.x - 4.0, mo.y + 2.0), Vector2(mo.x + 6.0, mo.y + 1.5)], 1.4, rel - 4.0)
	for i in range(3):
		tier_augen(figs["sau%d" % i], 1.2)


func m_augen() -> void:
	var sp := Welt.INTRO_SPOT
	nur([])
	augen("waldaugen_m", [Vector3(sp.x - 29, 0.6, sp.y + 41), Vector3(sp.x - 33, 0.9, sp.y + 40), Vector3(sp.x - 27, 0.5, sp.y + 45),
			Vector3(sp.x - 36, 0.7, sp.y + 44), Vector3(sp.x - 31, 1.1, sp.y + 47)])


func m_augen_tick(rel: float, _dt: float) -> void:
	augen_tick("waldaugen_m", rel, 0.2, 0.55)


func m_knurren() -> void:
	m_alp()
	var sp := Welt.INTRO_SPOT
	stell(figs["held"], sp.x - 15.0, sp.y + 27.0, sp.x - 50.0, sp.y + 56.0)
	var h := hund()
	if h != null:
		stell(h, sp.x - 16.2, sp.y + 28.2, sp.x - 50.0, sp.y + 56.0)
		idle(h, "alert", 1.0e4)
	var k := kristall("kristall_hand", 1.0)
	k.global_position = (figs["held"] as Node3D).global_position + (figs["held"] as Node3D).global_transform.basis * Vector3(0.38, 1.25, 0)


func m_woelfe() -> void:
	var uh := Bt.UPPER_HUT
	var names := []
	for i in range(3):
		var w := fig("wolf%d" % i, "wolf")
		stell(w, uh.x + 4.0 + i * 3.0, uh.y + 8.0 + i * 1.5, uh.x + 30.0, uh.y + 20.0)
		names.append("wolf%d" % i)
	nur(names)


func m_woelfe_tick(rel: float, _dt: float) -> void:
	var uh := Bt.UPPER_HUT
	for i in range(3):
		var w: Node3D = figs["wolf%d" % i]
		var o := Vector2(i * 3.0, i * 1.5)
		pfad(w, [Vector2(uh.x - 2.0, uh.y + 4.0) + o, Vector2(uh.x + 14.0, uh.y + 12.0) + o], 1.3, rel + i * 0.6)
		tier_augen(w, 6.0)


func m_fackel() -> void:
	m_alp()
	var uh := Bt.UPPER_HUT
	stell(figs["held"], uh.x - 12.0, uh.y + 2.0, uh.x + 4.0, uh.y + 8.0)
	var h := hund()
	if h != null:
		stell(h, uh.x - 11.0, uh.y + 3.2, uh.x + 4.0, uh.y + 8.0)
		idle(h, "alert", 1.0e4)
	var names := ["held", "maggie"]
	for i in range(2):
		fig("wolf%d" % i, "wolf")
		names.append("wolf%d" % i)
	nur(names)


func m_fackel_tick(rel: float, _dt: float) -> void:
	var uh := Bt.UPPER_HUT
	var c := Vector2(uh.x - 12.0, uh.y + 2.0)
	for i in range(2):
		var w: Node3D = figs["wolf%d" % i]
		var a := rel * 0.22 + i * 2.4
		place(w, G(c.x + sin(a) * 10.0, c.y + cos(a) * 10.0))
		face(w, Vector3(cos(a), 0, -sin(a)))
		w.cur_speed = 1.2
		tier_augen(w, 6.0)
	fackel(figs["held"], true)


func m_kraehen() -> void:
	nur([])
	kraehen("schwarm", 14 if not lite else 7)


func m_kraehen_tick(rel: float, _dt: float) -> void:
	kraehen_tick("schwarm", rel, Vector3(-62, 8.0, -655), Vector3(-10, 30.0, -590), 4.5)


func _viper_ort() -> Vector2:
	return Welt.INTRO_SPOT + Vector2(16.0, -12.0)


func m_viper() -> void:
	nur([])
	var v := _viper_ort()
	steine("steine", v.x, v.y)
	viper("viper")


func m_viper_tick(rel: float, _dt: float) -> void:
	var v := _viper_ort()
	viper_tick("viper", rel, Vector3(v.x - 0.6, 0.0, v.y + 0.1), 1.1)


func m_mutig() -> void:
	m_knurren()


func m_mutig_tick(rel: float, _dt: float) -> void:
	var h := hund()
	if h != null:
		idle(h, "alert" if rel < 3.0 or rel > 4.5 else "", 10.0)


func m_rennen() -> void:
	m_alp()


func m_rennen_tick(rel: float, _dt: float) -> void:
	var sp := Welt.INTRO_SPOT
	var h := hund()
	if h != null:
		pfad(h, [Vector2(sp.x - 2.0, sp.y + 2.0), Vector2(sp.x - 14.0, sp.y + 10.0)], 4.4, rel)
	pfad(figs["held"], [Vector2(sp.x + 2.0, sp.y), Vector2(sp.x - 12.0, sp.y + 9.0)], 3.2, rel)


func m_kristall() -> void:
	m_knurren()
	nur(["held"])


func m_nebellauf() -> void:
	_held()
	nur(["held"])


func m_nebellauf_tick(rel: float, _dt: float) -> void:
	var mo := Bt.MOOR
	pfad(figs["held"], [Vector2(mo.x + 16, mo.y + 6), Vector2(mo.x + 30, mo.y + 8)], 3.3, rel)


func m_bellen() -> void:
	m_knurren()


func m_bellen_tick(rel: float, _dt: float) -> void:
	var h := hund()
	if h != null:
		idle(h, "" if fmod(rel, 0.6) < 0.3 else "alert", 1.0)


func m_dunkel() -> void:
	m_knurren()
	var k := ding("kristall_hand")
	if k != null:
		licht(k.get_node("c"), 0.15)


func m_dunkel_tick(rel: float, _dt: float) -> void:
	var k := ding("kristall_hand")
	if k != null:
		licht(k.get_node("c"), 0.15 if rel < 4.0 else 0.15 + 3.0 * ein(rel, 4.0, 4.4))


func m_sterne() -> void:
	m_alp()
	var sp := Welt.INTRO_SPOT
	stell(figs["held"], sp.x, sp.y, sp.x - 6.0, sp.y - 8.0)
	idle(figs["held"], "sit", 1.0e4)
	var h := hund()
	if h != null:
		stell(h, sp.x + 0.9, sp.y + 0.3, sp.x - 6.0, sp.y - 8.0)
		idle(h, "sit", 1.0e4)
	var k := kristall("kristall_boden", 1.2)
	k.position = G(sp.x + 0.4, sp.y - 0.9, 0.05)


func m_sterne_tick(rel: float, _dt: float) -> void:
	var k := ding("kristall_boden")
	if k != null:
		k.rotation.y = rel * 0.3
