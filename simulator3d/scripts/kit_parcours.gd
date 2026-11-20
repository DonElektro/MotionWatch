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
		aktionen.append({"id": str(a["id"]), "art": str(a["art"]), "p": tal(float(a["s"]), float(a["q"])), "r": float(a.get("r", 1.2)), "d": a})


func _deck(c: Vector2, hq: float, hs: float, top_abs: float) -> Array:
	var dk := [c, Vector2(hq, hs), rot, top_abs]
	bt.decks.append(dk)
	_decks.append(dk)
	return dk


func _box(c: Vector2, hq: float, hs: float, top_abs: float, col: Color, tk = "stone", tief := 3.0) -> MeshInstance3D:
	var h := tief + (top_abs - _H(c.x, c.y))
	var n := node(holder, Vector3(c.x, top_abs - h * 0.5, c.y), -rot)
	return part(n, boxm(hq * 2.0, h, hs * 2.0), Vector3.ZERO, col, tk)


func _ding(d: Dictionary) -> void:
	var id := str(d["id"])
	var sv := float(d.get("s", 0.0))
	var qv := float(d.get("q", 0.0))
	var c := tal(sv, qv)
	var ls := float(d.get("ls", 0.5))
	var lq := float(d.get("lq", 0.5))
	var vorn := tal(sv - ls, qv)
	var top := _H(vorn.x, vorn.y) + float(d.get("top", 0.0))
	var e := {"d": d, "c": c, "top": top, "decks": [], "node": null}
	match str(d["art"]):
		"stein":
			e["decks"].append(_deck(c, lq, ls, top))
			var n := node(holder, Vector3(c.x, top - 0.35, c.y), -rot)
			part(n, sphm(1.0, -1.0, 10), Vector3.ZERO, FELS.lerp(Color(0.3, 0.36, 0.3), 0.3), "stone", Vector3.ZERO, Vector3(lq * 1.15, 0.45, ls * 1.15))
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
			var base := _H(c.x, c.y)
			var h2 := float(d.get("top", 4.0))
			var n4 := node(holder, Vector3(c.x, base, c.y), -rot)
			for sx in [-0.25, 0.25]:
				part(n4, boxm(0.06, h2 + 0.6, 0.06), Vector3(sx, (h2 + 0.6) * 0.5, 0), HOLZ, "tree")
			var k := 0.3
			while k < h2 + 0.5:
				part(n4, boxm(0.5, 0.04, 0.05), Vector3(0, k, 0), HOLZ.lightened(0.1), "tree")
				k += 0.32
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
				var wm := StandardMaterial3D.new()
				wm.albedo_color = Color(WASSER, 0.9)
				wm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
				wm.roughness = 0.08
				wm.metallic = 0.2
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
		"fund":
			var n7 := node(holder, Vector3(c.x, top + 0.12, c.y), 0.0)
			light_part(n7, sphm(0.09, -1.0, 8), Vector3.ZERO, glow_mat(Color(1.0, 0.9, 0.6), 2.5))
			part(n7, cylm(0.035, 0.035, 0.12, 6), Vector3(0, 0.02, 0), Color(0.6, 0.62, 0.66), 10.0, Vector3(0, 0, 0.5))
			e["node"] = n7
			_glanz.append([n7, n7.position.y])
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
			part(n, boxm(hq * 2.0, t - sims_top - 0.6, ls * 2.0), Vector3.ZERO, FELS, "stone")
	e["top"] = top


const FALL_SHADER := """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform float speed = 2.2;
void fragment() {
	float st = fract(UV.y * 3.0 - TIME * speed + sin(UV.x * 23.0) * 0.15);
	float n = smoothstep(0.0, 0.5, st) * (1.0 - smoothstep(0.55, 1.0, st));
	float edge = smoothstep(0.0, 0.18, UV.x) * smoothstep(1.0, 0.82, UV.x);
	ALBEDO = mix(vec3(0.72, 0.82, 0.86), vec3(1.0), n);
	ALPHA = (0.45 + 0.45 * n) * edge;
}
"""


const BACH_SHADER := """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;
void fragment() {
	float st = fract(UV.y * 0.6 - TIME * 0.9 + sin(UV.x * 9.0 + UV.y * 2.0) * 0.12);
	float n = smoothstep(0.0, 0.4, st) * (1.0 - smoothstep(0.45, 1.0, st));
	float edge = smoothstep(0.0, 0.25, UV.x) * smoothstep(1.0, 0.75, UV.x);
	ALBEDO = mix(vec3(0.24, 0.42, 0.46), vec3(0.78, 0.88, 0.9), n * 0.6);
	ALPHA = (0.55 + 0.3 * n) * edge;
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
	if not lite:                                           # spray at the foot
		var sp := glow_mat(Color(0.9, 0.95, 1.0), 0.4, 0.35)
		for i in range(5):
			light_part(n, sphm(0.35 + 0.1 * i, -1.0, 8), Vector3(randf_range(-w * 0.4, w * 0.4), -(h + 0.6) * 0.5 + 0.35, randf_range(-0.3, 0.3)), sp)
	e["node"] = n


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
		if float(a["r"]) <= 0.0 or (nur_offen and erledigt.has(a["id"]) and str(a["art"]) in ["maggie_heben", "fund"]):
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


func weg_punkte() -> PackedVector2Array:
	var out := PackedVector2Array()
	for p in daten.WEG:
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
	return {"dinge": dinge.size(), "decks": _decks.size(), "aktionen": aktionen.size(), "gefahren": gefahren.size(), "erledigt": erledigt.keys()}
