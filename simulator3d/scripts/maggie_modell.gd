extends Node
## Maggie mit Skelett (Daniel 01.11.2026, «Maggie realistischer»), ab Grafik «mittel» (nicht Lite / «einfach»):
## ein freies Hundemodell mit Knochen (Quaternius «Ultimate Animated Animals», ShibaInu, CC0 – LIZENZEN.md), mit
## werkzeuge/maggie_modell.py auf Jack-Russell-Proportionen gebracht (hochbeinig, schlank, Kippohren, Schwanz nach oben
## gebogen) und mit Maggies Muster als Vertex-Farben. Datei: modelle/maggie_hund_glb.bin (ein GLB, roh im Export).
##
## Bewegt wird sie wie bisher von actor.gd / anim_tier.gd / maggie_hund.gd: die bekannten Gelenke (legs[i][0] Hüfte /
## Schulter, legs[i][2] Hand- / Sprunggelenk, head, tail, body_root) bleiben als unsichtbare Knoten an den Stellen der
## Knochen; dieser Knoten (Kind von «maggie_koerper», läuft nach allen anderen) überträgt jedes Bild ihre Drehung auf die
## Knochen – Gehen, Rennen, Sitzen, Liegen, Graben, Schnüffeln, Freuen, Wedeln, Knurren, Schütteln wirken ohne Änderung.
## Dazu: der Kopf biegt den Hals mit (Drehung auf Hals und Kopf verteilt), der Schwanz biegt sich beim Wedeln nach,
## die Kippohren wippen beim Laufen und Schütteln.
## Fell: shaders/maggie_fell.gdshader (kurze Haarstruktur als Rauschen über die Normale, leichtes Randlicht).
## Wärmebild: ein Zwilling auf Ebene 2 mit derselben Haut (wie figur.gd).

const DATEI := "res://modelle/maggie_hund_glb.bin"
const RUECKEN := 2.3424             # Modell-Einheiten: höchster Punkt des Rückens (werkzeuge/maggie_modell.py gibt ihn aus)
const RUECKEN_M := 0.31             # m: Maggies Rückenhöhe (Schulterhöhe ≈ 31 cm, wie die Grundformen)
const PFOTE_H := 0.0112             # m: wie maggie_hund.gd (die Marken der Pfoten liegen so hoch über der Sohle)

static var _bytes := PackedByteArray()
static var _versucht := false
static var fehler := ""

var a                                # actor.gd (Maggie)
var sk: Skeleton3D
var mi: MeshInstance3D
var holder: Node3D
var _ord: Array = []                 # Knochen-Indizes, Eltern zuerst
var _par: PackedInt32Array
var _rest_lok: Array = []            # Basis jedes Knochens in Ruhe (lokal)
var _rest_gl: Array = []             # Basis jedes Knochens in Ruhe (Modell-Raum)
var _map := {}                       # Knochen -> [Steuerknoten, Anteil]
var _ctl_rest := {}                  # Steuerknoten -> seine Basis in Ruhe (Raum maggie_koerper)
var _k: Node3D
var _hr := Basis()                   # Drehung des Modells im Raum maggie_koerper
var _ohren: Array = []               # [Knochen, Seite]
var _knick := {}                     # Knochen -> Hüft-Steuerknoten: Hinterlauf beim Sitzen / Liegen unter dem Knie zurück
var _t := 0.0


static func verfuegbar() -> bool:
	if not _versucht:
		_versucht = true
		if FileAccess.file_exists(DATEI):
			_bytes = FileAccess.get_file_as_bytes(DATEI)
		if _bytes.is_empty():
			fehler = "Modell fehlt: " + DATEI
	return not _bytes.is_empty()


static func _szene() -> Node3D:
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_buffer(_bytes, "", st) != OK:
		fehler = "Modell nicht lesbar"
		return null
	return doc.generate_scene(st) as Node3D


static func bauen(h, act, k: Node3D) -> Node:
	"""Maggie mit Skelett in «maggie_koerper» (Raum in Metern, Boden y = 0, vorne = -z) bauen. h = maggie_hund.gd.
	Gibt den Knoten zurück oder null (dann baut maggie_hund.gd die Grundformen)."""
	if not verfuegbar():
		return null
	var sc := _szene()
	if sc == null:
		return null
	var r = load("res://scripts/maggie_modell.gd").new()
	r.name = "maggie_modell"
	if not r._aufbauen(h, act, k, sc):
		r.free()
		sc.free()
		return null
	return r


func _aufbauen(h, act, k: Node3D, sc: Node3D) -> bool:
	a = act
	_k = k
	var sks := sc.find_children("*", "Skeleton3D", true, false)
	var mis := sc.find_children("*", "MeshInstance3D", true, false)
	if sks.is_empty() or mis.is_empty():
		fehler = "Modell ohne Skelett"
		return false
	sk = sks[0]
	mi = mis[0]
	holder = Node3D.new()
	holder.name = "modell"
	var s := RUECKEN_M / RUECKEN
	holder.basis = Basis(Vector3.UP, PI).scaled(Vector3.ONE * s)   # das Modell schaut nach +z, actor.gd nach -z
	k.add_child(holder)
	holder.add_child(sc)
	_hr = Basis(Vector3.UP, PI)
	# ---- Materialien: Fell (eigener Shader), Nase, Augen (leuchten nachts wie bei den anderen Tieren: a.lights) ----
	var fm := ShaderMaterial.new()
	fm.shader = load("res://shaders/maggie_fell.gdshader")
	fm.set_shader_parameter("fein", 0.0 if bool(h.lite) else 1.0)
	mi.set_surface_override_material(0, fm)
	var nm := StandardMaterial3D.new()
	nm.vertex_color_use_as_albedo = true
	nm.roughness = 0.32
	mi.set_surface_override_material(1, nm)
	var em := StandardMaterial3D.new()
	em.vertex_color_use_as_albedo = true
	em.roughness = 0.12
	em.emission_enabled = true
	em.emission = Color(0.9, 0.95, 0.8)
	em.emission_energy_multiplier = 0.0
	mi.set_surface_override_material(2, em)
	a.lights.append(em)
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if bool(h.lite) else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	var th := MeshInstance3D.new()                           # Wärmebild: dieselbe Haut, Fell ≈ 30 °C
	th.name = "waerme"
	th.mesh = mi.mesh
	th.skin = mi.skin
	mi.get_parent().add_child(th)
	th.skeleton = th.get_path_to(sk)
	th.transform = mi.transform
	th.material_override = h.m.tmat_fixed(h.FELL_C)
	th.layers = 2
	th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# ---- Knochen in Ruhe ----
	var n := sk.get_bone_count()
	_par = PackedInt32Array()
	_par.resize(n)
	_rest_lok.resize(n)
	_rest_gl.resize(n)
	for i in range(n):
		_par[i] = sk.get_bone_parent(i)
		_rest_lok[i] = sk.get_bone_rest(i).basis.orthonormalized()
	var tiefe := func(i: int) -> int:
		var d := 0
		var p := _par[i]
		while p >= 0:
			d += 1
			p = _par[p]
		return d
	_ord = range(n)
	_ord.sort_custom(func(x, y): return tiefe.call(x) < tiefe.call(y))
	for i in _ord:
		_rest_gl[i] = (_rest_gl[_par[i]] * _rest_lok[i]) if _par[i] >= 0 else _rest_lok[i]
	# ---- Steuerknoten an den Stellen der Knochen (Schnittstelle von actor.gd) ----
	var pfoten := []
	var beine := [["FrontUpperLeg.R", "FrontLowerLeg.R", "FF.R", true], ["FrontUpperLeg.L", "FrontLowerLeg.L", "FF.L", true],
			["BackLeg.R", "BackLowerLeg.R", "FFB.R", false], ["BackLeg.L", "BackLowerLeg.L", "FFB.L", false]]
	for i in range(4):
		var b: Array = beine[i]
		var hp := _knoten(k, _kpos(str(b[0])))
		var kn := _knoten(hp, _kpos(str(b[1])) - hp.position)
		if bool(b[3]):
			kn.rotation.y = PI                           # wie die Grundformen: + beugt die Vorderpfote nach hinten
		var fuss := _kpos(str(b[2]))
		var pf := Node3D.new()                            # Marke der Pfote (maggie_hund._schwanz: Pfoten bleiben am Boden)
		pf.name = "pfote"
		kn.add_child(pf)
		pf.global_position = k.to_global(Vector3(fuss.x, PFOTE_H, fuss.z))
		pfoten.append(pf)
		a.legs.append([hp, 1 if i in [0, 3] else -1, kn])
		_map[sk.find_bone(str(b[0]))] = [hp, 1.0]
		_map[sk.find_bone(str(b[1]))] = [kn, 1.0]
		if not bool(b[3]):
			var sx := "R" if i == 2 else "L"
			_knick[sk.find_bone("BackUpperLeg." + sx)] = hp
			_knick[sk.find_bone("BackLowerLeg." + sx)] = hp
	k.set_meta("pfoten", pfoten)
	var hd := _knoten(k, _kpos("Neck1"))                 # Kopf-Gelenk am Halsansatz (wie die Grundformen)
	a.head = hd
	for bn in [["Neck1", 0.35], ["Neck2", 0.6], ["Neck3", 0.8], ["Head", 1.0]]:
		_map[sk.find_bone(str(bn[0]))] = [hd, float(bn[1])]
	var tw := _knoten(k, _kpos("Tail1"))
	a.tail = tw
	for bn in [["Tail1", 0.55], ["Tail2", 0.85], ["Tail3", 1.15]]:
		_map[sk.find_bone(str(bn[0]))] = [tw, float(bn[1])]
	for c in [hd, tw] + a.legs.map(func(l): return l[0]) + a.legs.map(func(l): return l[2]):
		_ctl_rest[c] = _kbasis(c)
	for e in ["Ear2.L", "Ear2.R", "Ear3.L", "Ear3.R"]:
		_ohren.append([sk.find_bone(e), 1.0 if e.ends_with(".L") else -1.0])
	process_priority = 200                                # nach actor.gd (-1), anim_tier.gd und maggie_hund.gd
	k.add_child(self)
	_sync(0.0)
	return true


func _knoten(parent: Node3D, p: Vector3) -> Node3D:
	var n := Node3D.new()
	n.position = p
	parent.add_child(n)
	return n


func _kpos(bone: String) -> Vector3:
	"""Ruhelage eines Knochens im Raum von maggie_koerper (Meter)"""
	var i := sk.find_bone(bone)
	var g := Transform3D()
	while i >= 0:
		g = sk.get_bone_rest(i) * g
		i = sk.get_bone_parent(i)
	return _k.to_local(sk.global_transform * g.origin)


func _kbasis(c: Node3D) -> Basis:
	"""Drehung eines Steuerknotens im Raum von maggie_koerper"""
	var b := c.basis
	var p := c.get_parent()
	while p != null and p != _k:
		b = (p as Node3D).basis * b
		p = p.get_parent()
	return b.orthonormalized()


func _process(dt: float) -> void:
	_sync(dt)


func _sync(dt: float) -> void:
	_t += dt
	if sk == null or not is_instance_valid(sk):
		return
	var dq := {}                                          # Steuerknoten -> Drehung gegenüber der Ruhe (Modell-Raum)
	for c in _ctl_rest:
		if is_instance_valid(c):
			var q: Basis = _kbasis(c) * (_ctl_rest[c] as Basis).inverse()
			dq[c] = (_hr.inverse() * q * _hr).get_rotation_quaternion()
	# Ohren: wippen mit den Schritten, schlackern beim Schütteln
	var v := clampf(float(a.cur_speed) / 3.0, 0.0, 1.0)
	var wipp := sin(float(a.phase) * 2.0) * 0.22 * v
	var sch := 0.0
	if str(a.idle_kind) == "schuetteln":
		sch = 0.5 * sin(_t * 30.0)
	var gl := []
	gl.resize(_par.size())
	for i in _ord:
		var pg: Basis = gl[_par[i]] if _par[i] >= 0 else Basis()
		var g: Basis = pg * (_rest_lok[i] as Basis)
		if _map.has(i):
			var m: Array = _map[i]
			if dq.has(m[0]):
				var q: Quaternion = dq[m[0]]
				var f: float = m[1]
				var qf := Quaternion().slerp(q, f) if f <= 1.0 else q * Quaternion().slerp(q, f - 1.0)
				g = Basis(qf) * (_rest_gl[i] as Basis)
		if _knick.has(i):
			# Sitzen / Liegen: der Oberschenkel geht weit nach vorne, Unterschenkel und Pfote klappen unter dem Knie zurück
			var w: float = (_knick[i] as Node3D).rotation.x
			var zu := signf(w) * maxf(0.0, absf(w) - 0.55) * 1.35
			if zu != 0.0:
				g = Basis(Vector3.RIGHT, zu) * g           # um die Querachse; das Modell ist gedreht (x gespiegelt): + = nach hinten
		gl[i] = g
		var lok: Basis = pg.inverse() * g
		sk.set_bone_pose_rotation(i, lok.get_rotation_quaternion())
	for o in _ohren:
		var bi: int = o[0]
		if bi < 0:
			continue
		var ax := Vector3(1, 0, 0)
		var extra := Quaternion(ax, (wipp + sch) * float(o[1]) * 0.6 + wipp * 0.4)
		sk.set_bone_pose_rotation(bi, sk.get_bone_pose_rotation(bi) * extra)
