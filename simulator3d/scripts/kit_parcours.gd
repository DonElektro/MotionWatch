extends "res://scripts/bergtal_erleben_base.gd"
## Abenteuer-Kit (Grossvater-Neubau, Besitzer 20.11.2026): der Parcours eines Kapitels aus seinen DATEN (kit_k2_daten.gd …) im
## echten Bergtal – Steine, Felsstufen, Wände mit Tor und Fenster, Leiter, Seil, Baumstamm, Wasser (Gumpe), Spalt,
## Wasserfall, Funde. Gebaut im Tal-Raum (Kind des Tal-Knotens, wie die Bergtal-Erlebnisse); begehbare Oberkanten kommen als
## «decks» in bergtal.gd (gy(): Menschen stehen darauf, main.ground_y kennt sie), beim Aufräumen wieder weg.
## Gelände: alles steht relativ zum Boden (bergtal.H) und über die Achse der Schlucht [s, q] (siehe kit_k2_daten.gd).
## Lite: keine Lichter, kein Gischt-Schimmer, weniger Teile.

const Bt = preload("res://scripts/bergtal.gd")

const FELS := Color(0.64, 0.53, 0.42)               # warm rock like the walls of the gorge (kit_schlucht.gd)
const FELS2 := Color(0.56, 0.46, 0.37)
const HOLZ := Color(0.45, 0.31, 0.19)
const WASSER := Color(0.12, 0.28, 0.32)
const Schlucht = preload("res://scripts/kit_schlucht.gd")

var daten                            # the chapter data (script with ACHSE, DINGE, AKTIONEN, WEG …)
var ax0 := Vector2.ZERO
var ax_d := Vector2(0, -1)
var ax_q := Vector2(1, 0)
var rot := 0.0                       # deck rotation (local x = across)
var dinge := {}                      # id -> {d, node, decks: [deck arrays], c: Vector2, top: abs valley height}
var aktionen: Array = []             # [{id, art, p: Vector2 valley, r, d}]
var gefahren: Array = []             # [{id, art, c, hs, hq}] wasser / spalt
var erledigt := {}                   # action id -> true
var _decks: Array = []               # what we added to bt.decks
var _wf: Array = []                  # waterfall materials (time)
var _glanz: Array = []               # [node, base y] of finds
var schlucht = null                  # kit_schlucht.gd: the own gorge (its ground wins over bergtal.H)
var _nur_ir: Array = []              # things only seen with the IR light
var nur_lampe: Array = []            # Kapitel 1: things only seen in the cone of the headlamp
var ebenen_decks := {}               # Kapitel 1: level -> its decks (in bt.decks only while it is on)
var ebene_an := {}


func boden_tal(c: Vector2) -> float:
	"""the floor at a valley point as main.ground_y sees it (the deck of a building), as valley height"""
	var w := W(Vector3(c.x, _H(c.x, c.y), c.y))
	return float(m.ground_y(w.x, w.z)) + float(bt.h0)


func ebene(id: String, on: bool) -> void:
	"""a level (the attic): its floors count only while one is up there - a deck counts everywhere under it"""
	if bool(ebene_an.get(id, false)) == on:
		return
	ebene_an[id] = on
	for dk in ebenen_decks.get(id, []):
		if on:
			bt.decks.append(dk)
			_decks.append(dk)
		else:
			bt.decks.erase(dk)
			_decks.erase(dk)


var _ofen_licht: OmniLight3D = null


func ofen_an(c: Vector2, h: float) -> void:
	"""Kapitel 1: the stove burns - warm flickering light in the room, smoke out of the chimney"""
	if _ofen_licht != null:
		return
	var y := boden_tal(c) + h
	_ofen_licht = OmniLight3D.new()
	_ofen_licht.light_color = Color(1.0, 0.62, 0.3)
	_ofen_licht.light_energy = 1.6
	_ofen_licht.omni_range = 6.5
	_ofen_licht.shadow_enabled = false
	_ofen_licht.position = Vector3(c.x, y, c.y)
	holder.add_child(_ofen_licht)
	var tw := _ofen_licht.create_tween().set_loops()
	tw.tween_property(_ofen_licht, "light_energy", 1.25, 0.23)
	tw.tween_property(_ofen_licht, "light_energy", 1.7, 0.31)
	light_part(holder, sphm(0.12, -1.0, 8), Vector3(c.x, y - 0.25, c.y), glow_mat(Color(1.0, 0.5, 0.15), 3.0))
	var rauch := CPUParticles3D.new()
	rauch.amount = 14 if lite else 26
	rauch.lifetime = 4.0
	rauch.direction = Vector3(0.2, 1, 0)
	rauch.spread = 12.0
	rauch.initial_velocity_min = 0.5
	rauch.initial_velocity_max = 0.9
	rauch.gravity = Vector3(0.25, 0.15, 0)
	rauch.scale_amount_min = 0.8
	rauch.scale_amount_max = 2.0
	var pm := QuadMesh.new()
	pm.size = Vector2(0.6, 0.6)
	var mt := StandardMaterial3D.new()
	mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mt.albedo_texture = _weich_tex()
	mt.albedo_color = Color(0.75, 0.75, 0.78, 0.45)
	mt.vertex_color_use_as_albedo = true
	mt.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	pm.material = mt
	rauch.mesh = pm
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0.6))
	fade.set_color(1, Color(1, 1, 1, 0.0))
	rauch.color_ramp = fade
	var kam: Vector2 = tal(0.0, 2.7)                       # the chimney of the hut (local x 2.7, z 0)
	rauch.position = Vector3(kam.x, boden_tal(c) + 6.9, kam.y)
	holder.add_child(rauch)
var _planken: Array = []             # the bridge: [q, node, deck]


func ir_sichtbar(on: bool) -> void:
	for n in _nur_ir:
		if is_instance_valid(n):
			(n as Node3D).visible = on


func _bruecke(e: Dictionary, d: Dictionary, c: Vector2, sv: float, qv: float, ls: float, lq: float, top: float) -> void:
	"""an old suspension bridge: planks across the cleft (each one a deck), two hand ropes, posts at both ends"""
	var q := qv - lq + 0.25
	while q <= qv + lq - 0.2:
		var pc := tal(sv, q)
		var dk := _deck(pc, 0.27, ls, top)                # (a little overlap: no gap to fall through between two planks)
		e["decks"].append(dk)
		var n := node(holder, Vector3(pc.x, top - 0.04, pc.y), -rot)
		part(n, boxm(0.44, 0.06, ls * 2.0), Vector3.ZERO, HOLZ.darkened(randf() * 0.15), "tree", Vector3(0, 0, randf_range(-0.03, 0.03)))
		_planken.append([q, n, dk])
		q += 0.5
	for side in [-1.0, 1.0]:
		var a := tal(sv + side * ls, qv - lq - 0.3)
		var b := tal(sv + side * ls, qv + lq + 0.3)
		for p in [a, b]:
			part(holder, cylm(0.06, 0.07, 1.4, 6), Vector3(p.x, top + 0.55, p.y), HOLZ.darkened(0.2), "tree")
		var mid := (a + b) * 0.5
		var seil := part(holder, cylm(0.02, 0.02, a.distance_to(b), 5), Vector3(mid.x, top + 0.95, mid.y), Color(0.75, 0.66, 0.45), "tree",
				Vector3(PI * 0.5, 0, 0))
		seil.get_parent().remove_child(seil)
		var hn := node(holder, Vector3(mid.x, top + 0.95, mid.y), -rot + PI * 0.5)
		hn.add_child(seil)
		seil.position = Vector3.ZERO
		_planken.append([999.0, hn, null])
	_brueckenkopf(e, sv, qv, lq, top)


func _brueckenkopf(e: Dictionary, sv: float, qv: float, lq: float, top: float) -> void:
	"""the way onto the bridge (owner stuck 21.11.): a wide wooden landing at the head (q > the cleft), flat stones from the
	terrace to it, two lanterns on the head posts - the head lies RIGHT of the waterfall cleft, not straight ahead"""
	var q0 := qv + lq - 0.4                                # the landing overlaps the last planks
	var q1 := qv + lq + 1.7
	var lc := tal(sv, (q0 + q1) * 0.5)
	var dk := _deck(lc, (q1 - q0) * 0.5, 1.0, top)
	e["decks"].append(dk)
	var ln := node(holder, Vector3(lc.x, top - 0.07, lc.y), -rot)
	part(ln, boxm(q1 - q0, 0.12, 2.0), Vector3.ZERO, HOLZ.lightened(0.08), "tree")
	for zz in [-0.98, 0.98]:                               # edge beams
		part(ln, boxm(q1 - q0, 0.1, 0.1), Vector3(0, 0.08, zz), HOLZ.darkened(0.25), "tree")
	# flat stones from the terrace (the end of the rope swing / the carabiner) to the landing
	var von := Vector2(47.6, 5.6)
	var bis := Vector2(sv - 1.2, qv + lq + 0.6)
	var n := int(von.distance_to(bis) / 0.75)
	for i in range(n + 1):
		var f := float(i) / maxf(1.0, float(n))
		var pq := von.lerp(bis, f) + Vector2(0, 0.18 * sin(i * 1.7))
		var pt := tal(pq.x, pq.y)
		var g := _H(pt.x, pt.y)
		part(holder, cylm(0.32, 0.36, 0.08, 7), Vector3(pt.x, g + 0.01, pt.y), Color(0.62, 0.6, 0.56).darkened(randf() * 0.12), "stone",
				Vector3(0, randf() * 3.0, 0), Vector3(1.0, 1.0, 0.75))
	# lanterns on the two posts at the head
	for side in [-1.0, 1.0]:
		var lp := tal(sv + side * 0.9, q1 - 0.3)
		part(holder, cylm(0.06, 0.07, 1.7, 6), Vector3(lp.x, top + 0.8, lp.y), HOLZ.darkened(0.2), "tree")
		light_part(holder, sphm(0.11, -1.0, 8), Vector3(lp.x, top + 1.72, lp.y), glow_mat(Color(1.0, 0.72, 0.32), 3.0))
		lamp(holder, Vector3(lp.x, top + 1.75, lp.y), Color(1.0, 0.75, 0.4), 0.9, 4.5)


func bruecke_einsturz(ab_q: float) -> void:
	"""the planks behind (q > ab_q) and the ropes fall into the cleft"""
	for pl in _planken:
		if float(pl[0]) <= ab_q:
			continue
		if pl[2] != null:
			bt.decks.erase(pl[2])
			_decks.erase(pl[2])
			for id in dinge:
				(dinge[id]["decks"] as Array).erase(pl[2])
		var n: Node3D = pl[1]
		if not is_instance_valid(n):
			continue
		var tw := n.create_tween().set_parallel(true)
		var delay := clampf((float(pl[0]) - ab_q) * 0.05, 0.0, 0.4) if float(pl[0]) < 900.0 else 0.15
		tw.tween_property(n, "position:y", n.position.y - 9.0, 1.3).set_delay(delay).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		tw.tween_property(n, "rotation:x", randf_range(-1.5, 1.5), 1.3).set_delay(delay)


func _H(x: float, z: float) -> float:
	"""the ground (valley y): the own gorge, else the valley"""
	if schlucht != null:
		var h = schlucht.boden(x, z)
		if h != null:
			return float(h)
	return Bt.H(x, z)


func G(x: float, z: float, dy := 0.0) -> Vector3:
	return Vector3(x, _H(x, z) + dy, z)


func _part() -> String:
	return "kit"


func binden(m_, daten_) -> bool:
	m = m_
	daten = daten_
	var b = m.scenes.data.get("bergtal", null) if m.scenes != null else null
	if b == null or b.tal == null or not is_instance_valid(b.tal):
		return false
	bt = b
	s = bt.s
	season = str(bt.season)
	lite = _lite() or str(m.quality) == "simple"
	process_priority = 100
	name = "kit_parcours"
	holder = Node3D.new()
	holder.name = "kit_dinge"
	bt.tal.add_child(holder)
	ax0 = daten.ACHSE[0]
	ax_d = (daten.ACHSE[1] as Vector2).normalized()
	ax_q = Vector2(-ax_d.y, ax_d.x)
	rot = atan2(ax_q.y, ax_q.x)
	return true


func aufraeumen() -> void:
	if schlucht != null:
		schlucht.aufraeumen()
		if bt != null and bt.get("boden_fn") != null:
			bt.boden_fn = Callable()
	schlucht = null
	if bt != null:
		for d in _decks:
			bt.decks.erase(d)
	_decks.clear()
	if holder != null and is_instance_valid(holder):
		holder.queue_free()
	holder = null
	dinge.clear()
	aktionen.clear()
	gefahren.clear()


# ---- coordinates -------------------------------------------------------------------------------------------------------
func tal(sv: float, qv: float) -> Vector2:
	"""[s, q] of the gorge axis -> valley (x, z)"""
	return ax0 + ax_d * sv + ax_q * qv


func sq(v: Vector2) -> Vector2:
	"""valley (x, z) -> [s, q]"""
	var o := v - ax0
	return Vector2(o.dot(ax_d), o.dot(ax_q))


func welt(sv: float, qv: float, dy := 0.0) -> Vector3:
	"""[s, q] -> world point on the ground (+ dy)"""
	var t := tal(sv, qv)
	return W(G(t.x, t.y, dy))


func welt_abs(sv: float, qv: float, y_tal: float) -> Vector3:
	var t := tal(sv, qv)
	return W(Vector3(t.x, y_tal, t.y))


func tal_von(w: Vector3) -> Vector2:
	var q := VL(w)
	return Vector2(q.x, q.z)


func sq_von(w: Vector3) -> Vector2:
	return sq(tal_von(w))


func y_welt(y_tal: float) -> float:
	"""a valley height -> world height (the valley is only turned around y and moved)"""
	return W(Vector3(0, y_tal, 0)).y


func top_welt(id: String) -> float:
	return y_welt(float(dinge[id]["top"])) if dinge.has(id) else 0.0


func yaw_achse() -> float:
	"""world heading (actor.heading) for «downstream»"""
	var a := W(Vector3(ax0.x, 0, ax0.y))
	var b := W(Vector3(ax0.x + ax_d.x, 0, ax0.y + ax_d.y))
	var d := b - a
	return atan2(-d.x, -d.z)


# ---- building ------------------------------------------------------------------------------------------------------------
func bauen() -> void:
	if daten.get_script_constant_map().has("SCHLUCHT"):
		schlucht = Schlucht.new(bt, daten.SCHLUCHT)
		schlucht.bauen(holder, m, lite)
		bt.boden_fn = func(x: float, z: float): return schlucht.boden(x, z)
	for d in daten.DINGE:
		_ding(d)
	for a in daten.AKTIONEN:
		var ap := Vector2(float(a["tal"][0]), float(a["tal"][1])) if a.has("tal") else tal(float(a["s"]), float(a["q"]))
		aktionen.append({"id": str(a["id"]), "art": str(a["art"]), "p": ap, "r": float(a.get("r", 1.2)), "d": a})


func _deck(c: Vector2, hq: float, hs: float, top_abs: float) -> Array:
	var dk := [c, Vector2(hq, hs), rot, top_abs]
	bt.decks.append(dk)
	_decks.append(dk)
	return dk


var _fels_mt: Material = null


func fels(mi: MeshInstance3D) -> MeshInstance3D:
	"""the rock look of the gorge (kit_schlucht.gd shader) on a piece of the course - moss on its flat top"""
	if _fels_mt == null:
		_fels_mt = Schlucht.fels_material(true)
	mi.material_override = _fels_mt
	return mi


func _box(c: Vector2, hq: float, hs: float, top_abs: float, col: Color, tk = "stone", tief := 3.0) -> MeshInstance3D:
	var h := tief + (top_abs - _H(c.x, c.y))
	var n := node(holder, Vector3(c.x, top_abs - h * 0.5, c.y), -rot)
	var mi := part(n, boxm(hq * 2.0, h, hs * 2.0), Vector3.ZERO, col, tk)
	if not lite:                                           # a softer edge: a slightly smaller, rounded cap on the box
		var cap := part(n, cylm(1.0, 1.0, 0.3, 12), Vector3(0, h * 0.5 - 0.06, 0), col, tk, Vector3.ZERO, Vector3(hq * 0.98, 1.0, hs * 0.98))
		fels(cap)
	return fels(mi)


func _ding(d: Dictionary) -> void:
	var id := str(d["id"])
	var sv := float(d.get("s", 0.0))
	var qv := float(d.get("q", 0.0))
	if d.has("tal"):                                       # placed in valley coordinates (at the camp on the rim)
		var sqt := sq(Vector2(float(d["tal"][0]), float(d["tal"][1])))
		sv = sqt.x
		qv = sqt.y
	var c := tal(sv, qv)
	var ls := float(d.get("ls", 0.5))
	var lq := float(d.get("lq", 0.5))
	var vorn := tal(sv - ls, qv)
	if d.has("boden_bei"):
		vorn = tal(float(d["boden_bei"][0]), float(d["boden_bei"][1]))
	var top := _H(vorn.x, vorn.y) + float(d.get("top", 0.0))
	if bool(d.get("boden_deck", false)) or d.has("ebene"):   # Kapitel 1: over the floor of the hut (its deck), not the terrain
		top = boden_tal(c) + float(d.get("top", 0.0))
	var e := {"d": d, "c": c, "top": top, "decks": [], "node": null}
	match str(d["art"]):
		"stein":
			e["decks"].append(_deck(c, lq, ls, top))
			var n := node(holder, Vector3(c.x, top - 0.35, c.y), -rot)
			fels(part(n, sphm(1.0, -1.0, 10), Vector3.ZERO, FELS.lerp(Color(0.3, 0.36, 0.3), 0.3), "stone", Vector3.ZERO, Vector3(lq * 1.15, 0.45, ls * 1.15)))
			e["node"] = n
		"block":
			e["decks"].append(_deck(c, lq, ls, top))
			e["node"] = _box(c, lq, ls, top, FELS2 if bool(d.get("kante", false)) else FELS)
			if bool(d.get("kante", false)):                # a lighter band at the edge you can grab
				var n2 := node(holder, Vector3(c.x, top - 0.04, c.y), -rot)
				part(n2, boxm(lq * 2.0 + 0.02, 0.08, ls * 2.0 + 0.02), Vector3.ZERO, Color(0.66, 0.62, 0.55), "stone")
		"wand":
			_wand(e, c, lq, ls, top)
		"tor":
			e["decks"].append(_deck(c, lq, ls, top))
			var piv := node(holder, Vector3(0, 0, 0), 0.0)
			var a0 := c - ax_q * lq
			piv.position = Vector3(a0.x, _H(c.x, c.y), a0.y)
			piv.rotation.y = -rot
			for i in range(5):
				part(piv, boxm(lq * 2.0 / 5.0 - 0.04, float(d.get("top", 2.0)), 0.08), Vector3(lq * 2.0 * (i + 0.5) / 5.0, float(d.get("top", 2.0)) * 0.5, 0), HOLZ.darkened(0.08 * (i % 2)), "tree")
			for yy in [0.5, 1.5]:
				part(piv, boxm(lq * 2.0, 0.14, 0.12), Vector3(lq, yy, 0.06), HOLZ.darkened(0.2), "tree")
			var riegel := part(piv, boxm(0.5, 0.08, 0.08), Vector3(lq * 2.0 - 0.1, 1.2, 0.2), Color(0.35, 0.35, 0.38), 12.0)
			e["node"] = piv
			e["riegel"] = riegel
		"balken":
			e["decks"].append(_deck(c, lq, ls, top))
			var n3 := node(holder, Vector3(c.x, top - 0.2, c.y), -rot)
			part(n3, cylm(0.2, 0.24, ls * 2.0 + 0.4, 10), Vector3.ZERO, Color(0.36, 0.27, 0.18), "tree", Vector3(PI * 0.5, 0, 0))
			e["node"] = n3
		"leiter":
			var base := boden_tal(c) if bool(d.get("boden_deck", false)) else _H(c.x, c.y)
			var h2 := float(d.get("top", 4.0))
			if bool(d.get("unsichtbar", false)):           # Kapitel 1: the ladder of the hut is there already
				e["top"] = base + h2
				dinge[id] = e
				return
			var n4 := node(holder, Vector3(c.x, base, c.y), -rot)
			var eisen := Color(0.36, 0.36, 0.38)
			var k := 0.35                                  # Klettersteig: iron rungs (bügel) in the rock and a steel cable beside
			var st := SurfaceTool.new()                    # all rungs and anchors in ONE mesh (one draw call; web Lite)
			st.begin(Mesh.PRIMITIVE_TRIANGLES)
			while k < h2 + 0.3:
				st.append_from(boxm(0.42, 0.035, 0.035), 0, Transform3D(Basis.IDENTITY, Vector3(0, k, -0.14)))
				for sx in [-0.2, 0.2]:
					st.append_from(boxm(0.035, 0.035, 0.16), 0, Transform3D(Basis.IDENTITY, Vector3(sx, k, -0.07)))
				k += 0.34
			for yy in [0.2, h2 * 0.5, h2 + 1.0]:
				st.append_from(boxm(0.05, 0.05, 0.12), 0, Transform3D(Basis.IDENTITY, Vector3(0.42, yy, -0.04)))
			light_part(n4, st.commit(), Vector3.ZERO, m.mat(eisen))
			light_part(n4, cylm(0.012, 0.012, h2 + 1.2, 6), Vector3(0.42, (h2 + 1.2) * 0.5, -0.05), m.mat(Color(0.7, 0.72, 0.74)))
			e["node"] = n4
			e["top"] = base + h2
		"seil":
			var vt := tal(float(d["von"][0]), float(d["von"][1]))
			top = _H(vt.x, vt.y)
			e["top"] = top
			var anker := Vector3(c.x, top + 4.0, c.y)
			var n5 := node(holder, anker, 0.0)
			part(holder, boxm(0.25, 0.25, 4.6), Vector3(c.x, top + 4.1, c.y), HOLZ.darkened(0.25), "tree", Vector3(0, -rot, 0))
			var seil := MeshInstance3D.new()
			seil.mesh = cylm(0.025, 0.025, 1.0, 6)
			seil.material_override = m.mat(Color(0.75, 0.66, 0.45))
			holder.add_child(seil)
			e["node"] = n5
			e["seil"] = seil
			e["anker"] = anker
			seil_zu(id, tal(float(d["von"][0]), float(d["von"][1])), top + 1.6)
		"wasser", "spalt":
			gefahren.append({"id": id, "art": str(d["art"]), "c": c, "hs": ls, "hq": lq})
			if str(d["art"]) == "wasser":
				var n6 := node(holder, Vector3(c.x, _H(c.x, c.y) + 0.06, c.y), -rot)
				var wm := ShaderMaterial.new()
				var psh := Shader.new()
				psh.code = POOL_SHADER
				wm.shader = psh
				wm.set_shader_parameter("ring", _ring_uv(sv, qv, ls, lq))
				var pm := PlaneMesh.new()
				pm.size = Vector2(lq * 2.0, ls * 2.0)
				var mi := MeshInstance3D.new()
				mi.mesh = pm
				mi.material_override = wm
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				n6.add_child(mi)
				e["node"] = n6
		"fall":
			_fall(e, c, float(d.get("top", 4.0)), float(d.get("breite", 1.2)))
		"bach":
			_bach(e, d)
		"bruecke":
			_bruecke(e, d, c, sv, qv, ls, lq, top)
		"steinmann":
			var n8 := node(holder, Vector3(c.x, top, c.y), 0.0)
			var yy := 0.0
			for i in range(6):
				var r := 0.42 - i * 0.055
				fels(part(n8, sphm(1.0, -1.0, 8), Vector3(randf_range(-0.04, 0.04), yy + r * 0.32, randf_range(-0.04, 0.04)), FELS, "stone",
						Vector3(0, randf() * 3.0, 0), Vector3(r, r * 0.62, r * 0.9)))
				yy += r * 0.6
			e["node"] = n8
		"findling":
			var n9 := node(holder, Vector3(c.x, top, c.y), 0.0)
			fels(part(n9, sphm(1.0, -1.0, 10), Vector3(0, 0.45, 0), FELS, "stone", Vector3(0, 0.6, 0), Vector3(float(d.get("r", 0.9)), 0.75, float(d.get("r", 0.9)) * 0.8)))
			e["node"] = n9
		"zelt":
			var n10 := node(holder, Vector3(c.x, top, c.y), deg_to_rad(float(d.get("dreh", 0.0))))
			var zc := Color(0.86, 0.4, 0.22)
			for sd in [-1.0, 1.0]:
				part(n10, boxm(1.25, 0.04, 2.1), Vector3(sd * 0.42, 0.5, 0), zc, "tent", Vector3(0, 0, sd * 0.86))
			part(n10, boxm(0.06, 1.1, 0.06), Vector3(0, 0.55, 1.0), Color(0.3, 0.3, 0.32), 8.0)
			e["node"] = n10
		"buch":
			var n11 := node(holder, Vector3(c.x, top + 0.03, c.y), 0.4)
			light_part(n11, sphm(0.035, -1.0, 8), Vector3(0.6, 0.1, 0.35), glow_mat(Color(1.0, 0.75, 0.4), 1.6))   # Lia's lantern
			lamp(n11, Vector3(0.45, 0.3, 0.2), Color(1.0, 0.72, 0.4), 0.9, 4.0)
			part(n11, boxm(0.34, 0.035, 0.24), Vector3.ZERO, Color(0.36, 0.22, 0.14), 14.0)
			part(n11, boxm(0.32, 0.012, 0.22), Vector3(0, 0.024, 0), Color(0.93, 0.9, 0.8), 14.0, Vector3(0, 0, 0.05))
			e["node"] = n11
		"fund":
			var n7 := node(holder, Vector3(c.x, top + 0.12, c.y), 0.0)
			light_part(n7, sphm(0.09, -1.0, 8), Vector3.ZERO, glow_mat(Color(1.0, 0.9, 0.6), 2.5))
			match str(d.get("form", "")):                  # Kapitel 1: what lies there
				"dose":
					part(n7, cylm(0.11, 0.11, 0.09, 12), Vector3(0, -0.06, 0), Color(0.55, 0.5, 0.42), 10.0)
				"schuh":
					part(n7, boxm(0.12, 0.14, 0.3), Vector3(0, -0.04, 0), Color(0.36, 0.22, 0.12), 10.0)
				"nest":
					part(n7, sphm(0.13, 0.12, 8), Vector3(0, -0.06, 0), Color(0.78, 0.74, 0.62), 12.0)
				_:
					part(n7, cylm(0.035, 0.035, 0.12, 6), Vector3(0, 0.02, 0), Color(0.6, 0.62, 0.66), 10.0, Vector3(0, 0, 0.5))
			e["node"] = n7
			if str(d.get("form", "")) == "":
				_glanz.append([n7, n7.position.y])
			if bool(d.get("nur_ir", false)):                # only seen in MoveEye's infrared light
				n7.visible = false
				_nur_ir.append(n7)
			if bool(d.get("nur_lampe", false)):             # Kapitel 1: only in the cone of the headlamp
				n7.visible = false
				nur_lampe.append(n7)
			if bool(d.get("versteckt", false)):             # shown by the story (Maggie brings it)
				n7.visible = false
		"deck":                                            # Kapitel 1: an invisible floor of a level (the attic) - off at first
			var dk := [c, Vector2(lq, ls), rot, top]
			e["decks"].append(dk)
			ebenen_decks[str(d.get("ebene", ""))] = ebenen_decks.get(str(d.get("ebene", "")), []) + [dk]
		"holz":                                            # Kapitel 1: the wood pile beside the hut
			var nh := node(holder, Vector3(c.x, _H(c.x, c.y), c.y), -rot)
			for r in range(3):
				for k2 in range(5 - r):
					part(nh, cylm(0.11, 0.11, 1.0, 8), Vector3(0, 0.12 + r * 0.2, (k2 - (4 - r) * 0.5) * 0.23),
							Color(0.5, 0.36, 0.22).darkened(randf() * 0.2), "tree", Vector3(0, 0, PI * 0.5))
			e["decks"].append(_deck(c, 0.55, 0.65, _H(c.x, c.y) + 0.75))
			e["node"] = nh
	dinge[id] = e


func _wand(e: Dictionary, c: Vector2, lq: float, ls: float, top: float) -> void:
	"""a wall across the gorge; a gate («tor» at the same s) leaves a gap, «fenster» [q, half width] a hole for Maggie"""
	var d: Dictionary = e["d"]
	var sv := float(d["s"])
	var cuts: Array = []
	for o in daten.DINGE:
		if str(o["art"]) == "tor" and absf(float(o["s"]) - sv) < 0.5:
			cuts.append([float(o["q"]) - float(o["lq"]), float(o["q"]) + float(o["lq"]), "tor"])
	var fe = d.get("fenster", null)
	if fe is Array:
		cuts.append([float(fe[0]) - float(fe[1]), float(fe[0]) + float(fe[1]), "fenster"])
	cuts.sort_custom(func(a, b): return float(a[0]) < float(b[0]))
	var q0 := float(d["q"]) - lq
	var parts := []
	for ct in cuts:
		if float(ct[0]) > q0:
			parts.append([q0, float(ct[0]), "voll"])
		if str(ct[2]) == "fenster":
			parts.append([float(ct[0]), float(ct[1]), "fenster"])
		q0 = float(ct[1])
	if q0 < float(d["q"]) + lq:
		parts.append([q0, float(d["q"]) + lq, "voll"])
	var hoch := float(d.get("top", 2.5))
	for p in parts:
		var qm := (float(p[0]) + float(p[1])) * 0.5
		var hq := (float(p[1]) - float(p[0])) * 0.5
		var cc := tal(sv, qm)
		var t := _H(cc.x, cc.y) + hoch
		e["decks"].append(_deck(cc, hq, ls, t))
		if str(p[2]) == "voll":
			_box(cc, hq, ls, t, FELS)
		else:                                             # the window: rock below and above the hole
			var sims_top := _H(cc.x, cc.y) + 1.5
			_box(cc, hq, ls, sims_top, FELS)
			var n := node(holder, Vector3(cc.x, sims_top + 0.6 + (t - sims_top - 0.6) * 0.5, cc.y), -rot)
			fels(part(n, boxm(hq * 2.0, t - sims_top - 0.6, ls * 2.0), Vector3.ZERO, FELS, "stone"))
			# the hole made obvious (21.11.): a dark frame round it and warm light coming through from the other side
			var hn := node(holder, Vector3(cc.x, sims_top + 0.3, cc.y), -rot)
			var dunkel: Material = m.mat(Color(0.12, 0.09, 0.07))
			for sx in [-1.0, 1.0]:
				light_part(hn, boxm(0.12, 0.72, ls * 2.0 + 0.04), Vector3(sx * (hq + 0.02), 0, 0), dunkel)
			light_part(hn, boxm(hq * 2.0 + 0.2, 0.12, ls * 2.0 + 0.04), Vector3(0, 0.36, 0), dunkel)
			var licht := glow_mat(Color(1.0, 0.85, 0.55), 1.4, 0.55)
			licht.cull_mode = BaseMaterial3D.CULL_DISABLED
			var lq_m := QuadMesh.new()
			lq_m.size = Vector2(hq * 1.7, 0.5)
			light_part(hn, lq_m, Vector3(0, 0, -ls - 0.03), licht)
			lamp(hn, Vector3(0, 0, -ls - 0.6), Color(1.0, 0.8, 0.5), 1.2, 3.0)
	e["top"] = top


# ---- water (Besitzer 21.11.: «besserer Shader»): the fall streams down faster towards the foot, with layered streaks, a
# white foam band at the bottom and a translucent tint; the stream flows DOWN the gorge (towards smaller s); the pools are
# lit with moving ripples, a fresnel sheen and rings where the fall hits them. All in one pass, no screen texture (web Lite).
const FALL_SHADER := """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform float speed = 2.2;
float h1(float x) { return fract(sin(x * 127.1) * 43758.5453); }
void fragment() {
	float y = pow(UV.y, 1.35);                                   // faster towards the foot (falling)
	float col = floor(UV.x * 18.0);                              // vertical strands of different brightness and phase
	float col2 = floor(UV.x * 31.0);
	float wob = h1(col) * 0.9 + sin(UV.x * 5.0 + TIME * 0.5) * 0.04;
	float st = fract(y * 3.0 - TIME * speed * (0.85 + 0.3 * h1(col + 3.0)) + wob);
	float n = smoothstep(0.0, 0.5, st) * (1.0 - smoothstep(0.55, 1.0, st));
	float st2 = fract(y * 7.0 - TIME * speed * 1.7 + h1(col2 + 9.0));
	float n2 = smoothstep(0.0, 0.3, st2) * (1.0 - smoothstep(0.35, 1.0, st2));
	float strand = 0.65 + 0.35 * h1(col);
	float edge = smoothstep(0.0, 0.16 + 0.05 * sin(UV.y * 9.0 + TIME), UV.x) * smoothstep(1.0, 0.84 - 0.05 * sin(UV.y * 7.0 - TIME), UV.x);
	float foam = smoothstep(0.78, 1.0, UV.y);                     // the white foot
	float top = smoothstep(0.0, 0.06, UV.y);
	vec3 deep = vec3(0.32, 0.5, 0.55);
	vec3 c = mix(deep, vec3(0.92, 0.97, 1.0), clamp((n * 0.6 + n2 * 0.45) * strand + foam * 0.8, 0.0, 1.0));
	ALBEDO = c;
	ALPHA = clamp((0.42 + 0.35 * n * strand + 0.2 * n2 + foam * 0.4) * edge * top, 0.0, 0.95);
}
"""


const BACH_SHADER := """
shader_type spatial;
render_mode blend_mix, cull_disabled, depth_draw_never, shadows_disabled, specular_schlick_ggx;
void fragment() {
	// UV.y = s along the gorge (it grows upstream): the water moves towards smaller s
	float t = TIME * 0.9;
	float st = fract(UV.y * 0.6 + t + sin(UV.x * 9.0 + UV.y * 2.0) * 0.12);
	float n = smoothstep(0.0, 0.4, st) * (1.0 - smoothstep(0.45, 1.0, st));
	float st2 = fract(UV.y * 1.7 + t * 1.6 + sin(UV.x * 17.0 - UV.y * 3.0) * 0.2);
	float n2 = smoothstep(0.0, 0.25, st2) * (1.0 - smoothstep(0.3, 1.0, st2));
	float edge = smoothstep(0.0, 0.25, UV.x) * smoothstep(1.0, 0.75, UV.x);
	float bank = 1.0 - smoothstep(0.08, 0.3, min(UV.x, 1.0 - UV.x));   // foam along the banks
	ALBEDO = mix(vec3(0.11, 0.21, 0.23), vec3(0.55, 0.66, 0.68), clamp(n * 0.3 + n2 * 0.2 + bank * 0.25, 0.0, 1.0));
	ROUGHNESS = 0.12;
	SPECULAR = 0.6;
	NORMAL_MAP = normalize(vec3(0.5 + 0.18 * sin(UV.y * 9.0 + t * 6.0 + UV.x * 5.0), 0.5 + 0.18 * cos(UV.x * 13.0 + t * 4.0), 1.0));
	ALPHA = (0.66 + 0.18 * n) * edge;
}
"""


const POOL_SHADER := """
shader_type spatial;
render_mode blend_mix, cull_disabled, depth_draw_never, shadows_disabled, specular_schlick_ggx;
uniform vec2 ring = vec2(0.5, 0.05);                            // where the fall hits (UV), -1 = none
uniform vec3 tief = vec3(0.07, 0.2, 0.23);
uniform vec3 flach = vec3(0.2, 0.36, 0.36);
void fragment() {
	vec2 p = UV * vec2(6.0, 6.0);
	float t = TIME;
	float w = sin(p.x * 3.1 + t * 1.3) * 0.5 + sin(p.y * 2.3 - t * 1.1 + p.x * 0.7) * 0.5 + sin((p.x + p.y) * 4.7 + t * 2.1) * 0.25;
	float r = 0.0;
	if (ring.x >= 0.0) {
		float d = distance(UV, ring);
		r = sin(d * 60.0 - t * 4.0) * (1.0 - smoothstep(0.0, 0.45, d)) * 0.8;
	}
	float edge = min(min(UV.x, 1.0 - UV.x), min(UV.y, 1.0 - UV.y));
	float rand = 1.0 - smoothstep(0.0, 0.12, edge);              // lighter and a little foam at the rim
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	ALBEDO = mix(mix(tief, flach, rand * 0.7), vec3(0.6, 0.7, 0.74), clamp(fres * 0.25 + max(r, 0.0) * 0.25, 0.0, 1.0));
	NORMAL_MAP = normalize(vec3(0.5 + 0.12 * w + 0.2 * r, 0.5 + 0.12 * cos(w * 2.0 + t), 1.0));
	ROUGHNESS = 0.14;
	SPECULAR = 0.45;
	ALPHA = 0.86 + 0.1 * fres;
}
"""


func _bach(e: Dictionary, d: Dictionary) -> void:
	"""the stream: a flowing strip along the floor (one draw call per part)"""
	var sh := Shader.new()
	sh.code = BACH_SHADER
	var sm := ShaderMaterial.new()
	sm.shader = sh
	var qv := float(d.get("q", 0.0))
	var w := float(d.get("breite", 1.6)) * 0.5
	for t in d["teile"]:
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
		var sv := float(t[0])
		while sv <= float(t[1]) + 0.01:
			for side in [-1.0, 1.0]:
				var p := tal(sv, qv + side * w)
				var pc := tal(sv, qv)
				st.set_uv(Vector2(0.5 + side * 0.5, sv))
				st.add_vertex(Vector3(p.x, _H(pc.x, pc.y) + 0.05, p.y))
			sv += 1.0
		var mi := MeshInstance3D.new()
		mi.mesh = st.commit()
		mi.material_override = sm
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		holder.add_child(mi)


func _fall(e: Dictionary, c: Vector2, h: float, w: float) -> void:
	var g := _H(c.x, c.y)
	var sh := Shader.new()
	sh.code = FALL_SHADER
	var sm := ShaderMaterial.new()
	sm.shader = sh
	var qm := QuadMesh.new()
	qm.size = Vector2(w, h + 0.6)
	var mi := MeshInstance3D.new()
	mi.mesh = qm
	mi.material_override = sm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var n := node(holder, Vector3(c.x, g + (h + 0.6) * 0.5 - 0.3, c.y), -rot)
	n.add_child(mi)
	var fuss := Vector3(0, -(h + 0.6) * 0.5 + 0.3, 0.35)
	_nebel(n, fuss, w, h)
	if lite:                                               # the owner saw flat white squares: no spray in Lite (foam ring stays)
		_schaum(n, fuss, w)
		e["node"] = n
		return
	var spray := CPUParticles3D.new()                    # spray: soft round billboards, fading out (CPU particles work on the web too)
	spray.amount = 30
	spray.lifetime = 1.2
	spray.position = fuss
	spray.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	spray.emission_box_extents = Vector3(w * 0.5, 0.1, 0.2)
	spray.direction = Vector3(0, 1, 1)
	spray.spread = 40.0
	spray.initial_velocity_min = 0.6
	spray.initial_velocity_max = 1.6
	spray.gravity = Vector3(0, -1.5, 0)
	spray.scale_amount_min = 0.5
	spray.scale_amount_max = 1.2
	var pm := QuadMesh.new()
	pm.size = Vector2(0.35, 0.35)
	var pmat := StandardMaterial3D.new()
	pmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	pmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	pmat.albedo_texture = _weich_tex()
	pmat.albedo_color = Color(0.95, 0.97, 1.0, 0.5)
	pmat.vertex_color_use_as_albedo = true
	pmat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	pm.material = pmat
	spray.mesh = pm
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0.7))
	fade.set_color(1, Color(1, 1, 1, 0.0))
	spray.color_ramp = fade
	n.add_child(spray)
	_schaum(n, fuss, w)
	e["node"] = n


func _ring_uv(sv: float, qv: float, ls: float, lq: float) -> Vector2:
	"""the UV of the plane where a waterfall of the data hits this pool (or -1)"""
	for o in daten.DINGE:
		if str(o["art"]) != "fall":
			continue
		var fs := float(o["s"])
		var fq := float(o["q"])
		if absf(fs - sv) < ls + 1.5 and absf(fq - qv) < lq:
			# PlaneMesh: x across (lq), z along (ls); UV.x = across, UV.y = along (towards -s at UV 1)
			return Vector2(clampf(0.5 + (fq - qv) / (2.0 * lq), 0.0, 1.0), clampf(0.5 - (fs - sv) / (2.0 * ls), 0.02, 0.98))
	return Vector2(-1.0, -1.0)


func _nebel(n: Node3D, fuss: Vector3, w: float, h: float) -> void:
	"""a soft layer of mist in front of the foot of the fall (two crossed soft quads - cheap, also in Lite)"""
	var mm := StandardMaterial3D.new()
	mm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mm.albedo_texture = _weich_tex()
	mm.albedo_color = Color(0.95, 0.97, 1.0, 0.35)
	mm.cull_mode = BaseMaterial3D.CULL_DISABLED
	mm.disable_receive_shadows = true
	for k in range(2):
		var q := MeshInstance3D.new()
		var qm := QuadMesh.new()
		qm.size = Vector2(w * 2.6, minf(2.2, h * 0.5 + 0.8))
		q.mesh = qm
		q.material_override = mm
		q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		q.position = fuss + Vector3(0, qm.size.y * 0.35, 0.45)
		q.rotation.y = 0.0 if k == 0 else PI * 0.5
		n.add_child(q)
		var tw := q.create_tween().set_loops()
		tw.tween_property(q, "scale", Vector3(1.12, 1.08, 1.0), 2.6 + k).set_trans(Tween.TRANS_SINE)
		tw.tween_property(q, "scale", Vector3(0.94, 0.95, 1.0), 2.6 + k).set_trans(Tween.TRANS_SINE)


static var _weich: ImageTexture = null


static func _weich_tex() -> ImageTexture:
	"""a soft round dot (radial falloff) for the spray"""
	if _weich == null:
		var img := Image.create(32, 32, false, Image.FORMAT_RGBA8)
		for y in range(32):
			for x in range(32):
				var r := Vector2(x - 15.5, y - 15.5).length() / 15.5
				img.set_pixel(x, y, Color(1, 1, 1, clampf(1.0 - r, 0.0, 1.0) * clampf(1.0 - r, 0.0, 1.0)))
		_weich = ImageTexture.create_from_image(img)
	return _weich


func _schaum(n: Node3D, fuss: Vector3, w: float) -> void:
	var ring := MeshInstance3D.new()                      # the foam ring in the pool under the fall
	var tm := TorusMesh.new()
	tm.inner_radius = w * 0.35
	tm.outer_radius = w * 0.85
	tm.rings = 16 if not lite else 10
	tm.ring_segments = 6
	ring.mesh = tm
	ring.scale = Vector3(1, 0.08, 1)
	ring.position = fuss + Vector3(0, -0.25, 0.3)
	ring.material_override = glow_mat(Color(0.9, 0.95, 0.97), 0.25, 0.6)
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	n.add_child(ring)


# ---- what the figure / the kit asks ----------------------------------------------------------------------------------------
func _in(dk: Array, v: Vector2, pad := 0.0) -> bool:
	var q := (v - (dk[0] as Vector2)).rotated(-float(dk[2]))
	return absf(q.x) < (dk[1] as Vector2).x + pad and absf(q.y) < (dk[1] as Vector2).y + pad


func gefahr_bei(w: Vector3) -> Dictionary:
	"""the water / gap under a world point (or {})"""
	var v := tal_von(w)
	for g in gefahren:
		var q := (v - (g["c"] as Vector2)).rotated(-rot)
		if absf(q.x) < float(g["hq"]) and absf(q.y) < float(g["hs"]):
			for dk in _decks:                            # a stone in the water is not water
				if _in(dk, v):
					return {}
			return g
	return {}


func ding_bei(w: Vector3, pad := 0.0) -> String:
	"""the thing whose top is under a world point ('' = the ground)"""
	var v := tal_von(w)
	for id in dinge:
		for dk in dinge[id]["decks"]:
			if _in(dk, v, pad):
				return str(id)
	return ""


func aktion_bei(w: Vector3, nur_offen := true) -> Dictionary:
	"""the nearest context action in reach of a world point"""
	var v := tal_von(w)
	var best := {}
	var bd := 1.0e9
	for a in aktionen:
		if float(a["r"]) <= 0.0 or (nur_offen and erledigt.has(a["id"]) and str(a["art"]) in ["maggie_heben", "fund", "karte", "ofen", "moveeye", "maggie_such"]):
			continue
		if (a["d"] as Dictionary).has("ebene") and not bool(ebene_an.get(str(a["d"]["ebene"]), false)):
			continue                                       # Kapitel 1: an action of the attic only up there
		if str(a["art"]) == "leiter" and bool(ebene_an.get("dach", false)) and str(a["d"].get("ding", "")) == "dachleiter":
			continue                                       # (up there: down by «runter», not the ladder from below)
		if str(a["art"]) == "fund" and dinge.has(str(a["d"].get("ding", ""))) and not (dinge[str(a["d"]["ding"])]["node"] as Node3D).is_visible_in_tree():
			continue
		var dd: float = v.distance_to(a["p"])
		if dd < float(a["r"]) and dd < bd:
			bd = dd
			best = a
	return best


func aktion(id: String) -> Dictionary:
	for a in aktionen:
		if str(a["id"]) == id:
			return a
	return {}


func deck_weg(id: String) -> void:
	if not dinge.has(id):
		return
	for dk in dinge[id]["decks"]:
		bt.decks.erase(dk)
		_decks.erase(dk)
	dinge[id]["decks"] = []


func tor_auf(id: String) -> void:
	deck_weg(id)
	if dinge.has(id) and dinge[id]["node"] != null:
		var n: Node3D = dinge[id]["node"]
		var tw := n.create_tween()
		tw.tween_property(n, "rotation:y", n.rotation.y + 1.75, 1.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)


func fund_weg(id: String) -> void:
	if dinge.has(id) and dinge[id]["node"] != null:
		(dinge[id]["node"] as Node3D).visible = false


func seil_zu(id: String, griff: Vector2, y_tal: float) -> void:
	"""the rope from its anchor to the grip (valley x, z, height)"""
	if not dinge.has(id):
		return
	var e: Dictionary = dinge[id]
	var a: Vector3 = e["anker"]
	var b := Vector3(griff.x, y_tal, griff.y)
	var seil: MeshInstance3D = e["seil"]
	var L := a.distance_to(b)
	var up := (a - b).normalized()
	var side := up.cross(Vector3.FORWARD if absf(up.z) < 0.9 else Vector3.RIGHT).normalized()
	seil.transform = Transform3D(Basis(side, up * L, side.cross(up)), (a + b) * 0.5)


func weg_punkte(L = null) -> PackedVector2Array:
	var out := PackedVector2Array()
	for p in (daten.WEG if L == null else L):
		out.append(tal(float(p[0]), float(p[1])))
	return out


func _process(dt: float) -> void:
	if holder == null or not is_instance_valid(holder):
		return
	_clock += dt
	for g in _glanz:
		if is_instance_valid(g[0]):
			(g[0] as Node3D).position.y = float(g[1]) + 0.04 * sin(_clock * 3.0)
			(g[0] as Node3D).rotation.y = _clock * 1.5


func info() -> Dictionary:
	var teile := holder.find_children("*", "MeshInstance3D", true, false).size() if holder != null and is_instance_valid(holder) else 0
	return {"dinge": dinge.size(), "decks": _decks.size(), "aktionen": aktionen.size(), "gefahren": gefahren.size(), "erledigt": erledigt.keys(),
		"netze": teile, "schlucht": schlucht.info() if schlucht != null else {}}
