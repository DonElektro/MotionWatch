extends Node
## «Die Karte des Grossvaters», Kapitel 3 «Der Seeblock»: die neuen Teile in einer eigenen Datei (kit_abenteuer.gd hängt sie
## nur ein: bauen, tick, Aktionen, Film-Einträge, Schritte mit «duft» / «floss»):
##   * Duftspur: Duftwolken, eine nach der anderen; jede verblasst in «fade» s, solange man trödelt oder falsch geht (wer
##     näher kommt, hat fast unbegrenzt Zeit). Ist sie weg, auf Aktion neu
##     (Abzeichen «Spürnase», wenn die Spur nie verloren ging).
##   * Floss: aus drei Stämmen Treibholz; man stakt mit dem Stick in Blickrichtung über den See, an Bojen entlang. Windböen
##     schieben quer: kommt die Warnung, im richtigen Moment Aktion (Stange einstemmen). Wer den Kurs verliert, beginnt an der
##     letzten Boje (Abzeichen «Kapitän»: nie vom Kurs, jede Böe gehalten).
##   * Zahlenschloss: drei Rädchen mit Zeichen; die Lösung steht an drei Stellen im Fels (I, II, III), unter Moos.
##   * das Set am See: der Seeblock mit Steg, Riss (das Zeichen aus Kapitel 2), Marken und Kiste; das Floss; das Feuer;
##     Lias Fussspuren beim Zelt; Bojen.
## Tasten im Schloss: ←/→ Rädchen, ↑/↓ Zeichen, Enter/E öffnen, Esc zurück (dazu Knöpfe für Maus und Touch).

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Bt = preload("res://scripts/bergtal.gd")

var kit
var par
var main
var daten
var wl := 0.0                          # the lake level (valley y)
var _rng := RandomNumberGenerator.new()

# the set
var _riss_mat: StandardMaterial3D
var _marken := {}                      # id -> {moos, schrift}
var gelesen := {}
var _deckel: Node3D
var _kiste_glanz: Node3D
var _floss_node: Node3D
var _feuer_an := false
var _kugeln: Array = []                # [valley point, radius]: the camera keeps out of the block

# the scent trail
var duft := {}
var _puff: Node3D
var _puff_mat: StandardMaterial3D

# the raft
var floss := {}
var _floss_deck: Array = []

# the lock
var _layer: CanvasLayer
var _schloss: PanelContainer
var _schloss_lab: Array = []
var _schloss_rahmen: Array = []
var schloss_wahl := [0, 0, 0]
var schloss_sel := 0
var schloss_falsch := 0
var schloss_auf := false
var _tasten := {}
var _boe_box: PanelContainer
var _boe_lab: Label
var _boe_bar: ProgressBar

var _ziel = null                       # world point for the compass / the marker (null = the step's own)


func _init(k) -> void:
	kit = k
	par = k.par
	main = k.main
	daten = k.daten
	name = "kit_k3"
	_rng.seed = 1974
	wl = Bt.level_of(Bt.LAKE1)


# =======================================================================================================================
# the set
# =======================================================================================================================
func bauen() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 118
	add_child(_layer)
	_seeblock()
	_spuren()
	_feuerstelle()
	_bojen()
	_floss_bauen_node()
	_ui_boe()
	_see_hindernisse(true)


var _see_alt: Array = []                 # [obstacle, r] of the lake obstacles switched off around the Seeblock


func _see_hindernisse(weg: bool) -> void:
	"""bergtal keeps people out of the lake with low round obstacles (height 0.1); on the landing of the Seeblock and on the
	raft the figure stands in the lake: around the block they are switched off while the chapter runs (back at the end)"""
	if not weg:
		for e in _see_alt:
			(e[0] as Dictionary)["r"] = e[1]
		_see_alt.clear()
		return
	var sb: Dictionary = daten.SEEBLOCK
	var mitte: Vector3 = par.welt_abs(float(sb["c"][0]), float(sb["c"][1]) - 3.0, wl)
	for o in main.obstacles:
		if not (o as Dictionary).has("r") or float(o.get("ht", 3.0)) > 0.2:
			continue
		if (o["c"] as Vector2).distance_to(Vector2(mitte.x, mitte.z)) < 14.0 + float(o["r"]):
			_see_alt.append([o, float(o["r"])])
			o["r"] = 0.0


func _sqw(sv: float, qv: float, y_tal: float) -> Vector3:
	"""[s, q] + valley height -> valley point (the holder of the course lives in valley space)"""
	var t: Vector2 = par.tal(sv, qv)
	return Vector3(t.x, y_tal, t.y)


func _seeblock() -> void:
	var sb: Dictionary = daten.SEEBLOCK
	var c: Vector2 = par.tal(float(sb["c"][0]), float(sb["c"][1]))
	var rs := float(sb["rs"])
	var rq := float(sb["rq"])
	var top := wl + float(sb["top_see"])
	var fels: Color = par.FELS
	par._box(c, rq, rs, top, fels, "stone", 10.0)         # the block: steep sides, a rounded top
	par._deck(c, rq, rs, top)
	var n: Node3D = par.node(par.holder, Vector3(c.x, top, c.y), -par.rot)
	for lump in [[Vector3(rq * 0.7, -1.6, rs * 0.55), Vector3(2.0, 2.6, 2.2)], [Vector3(-rq * 0.8, -2.4, -rs * 0.4), Vector3(2.2, 2.4, 2.6)],
			[Vector3(rq * 0.2, -0.2, -rs * 0.9), Vector3(1.6, 1.2, 1.8)], [Vector3(-rq * 0.5, -3.8, rs * 0.85), Vector3(2.4, 2.0, 2.0)]]:
		par.fels(par.part(n, par.sphm(1.0, -1.0, 12), lump[0], fels.lerp(Color(0.42, 0.44, 0.4), 0.25), "stone", Vector3.ZERO, lump[1]))
	for sv in [-rs * 0.55, 0.0, rs * 0.55]:                # the camera keeps out (two layers of spheres along the block)
		for hy in [1.2, 3.6]:
			var kp: Vector2 = par.tal(float(sb["c"][0]) + sv, float(sb["c"][1]))
			_kugeln.append([Vector3(kp.x, wl + hy, kp.y), minf(rq, rs) * 0.82])
	# the landing at the water (the raft lands here; a dry deck - around it the lake is water)
	var st: Dictionary = sb["steg"]
	var sc: Vector2 = par.tal(float(st["c"][0]), float(st["c"][1]))
	par._box(sc, float(st["lq"]), float(st["ls"]), wl + float(st["top_see"]), par.FELS2, "stone", 10.0)
	par._deck(sc, float(st["lq"]), float(st["ls"]), wl + float(st["top_see"]))
	var steg_y := wl + float(st["top_see"])
	# the crack: two lines and a cross (the sign of chapter 2), dark - it glows warm when compared
	var r: Array = sb["riss"]
	_riss_mat = StandardMaterial3D.new()
	_riss_mat.albedo_color = Color(0.1, 0.09, 0.08)
	_riss_mat.emission_enabled = true
	_riss_mat.emission = Color(1.0, 0.7, 0.3)
	_riss_mat.emission_energy_multiplier = 0.0
	var rn: Node3D = par.node(par.holder, _sqw(float(r[0]), float(r[1]), steg_y + float(r[2])), -par.rot)
	for z in [-0.22, 0.22]:
		par.light_part(rn, par.boxm(0.05, 0.95, 0.07), Vector3(0, 0, z), _riss_mat)
	for a in [PI * 0.25, -PI * 0.25]:
		par.light_part(rn, par.boxm(0.05, 0.5, 0.07), Vector3(0, 0, 0.75), _riss_mat).rotation = Vector3(a, 0, 0)
	# the marks: under moss on the face, a numeral and a sign scratched in
	for m in sb["marken"]:
		var mp := _sqw(float(m[1]), float(r[1]), steg_y + 1.15)
		var mn: Node3D = par.node(par.holder, mp, -par.rot)
		var moos: MeshInstance3D = par.part(mn, par.boxm(0.08, 0.5, 0.55), Vector3(-0.02, 0, 0), Color(0.3, 0.42, 0.2), "stone")
		var lab := Label3D.new()
		lab.text = "%s\n%s" % [str(m[2]), str(m[3])]
		lab.font_size = 96
		lab.pixel_size = 0.0028
		lab.modulate = Color(0.95, 0.92, 0.82)
		lab.outline_modulate = Color(0.12, 0.1, 0.08)
		lab.outline_size = 10
		lab.visible = false
		par.holder.add_child(lab)
		var aussen: Vector3 = par.W(mp)
		var innen: Vector3 = par.W(_sqw(float(m[1]), float(r[1]) + 1.0, steg_y + 1.15))
		lab.global_position = aussen + (aussen - innen).normalized() * 0.03
		lab.look_at(lab.global_position + (innen - aussen).normalized(), Vector3.UP)
		_marken[str(m[0])] = {"moos": moos, "schrift": lab, "nr": str(m[2]), "zeichen": str(m[3])}
	# the box in a niche at the landing: wood, three brass wheels, a lid on a hinge
	var kp2: Array = sb["kiste"]
	var kn: Node3D = par.node(par.holder, _sqw(float(kp2[0]), float(kp2[1]), steg_y), -par.rot)
	par.part(kn, par.boxm(0.36, 0.3, 0.52), Vector3(0, 0.15, 0), Color(0.36, 0.24, 0.14), "tree")
	for i in range(3):
		par.part(kn, par.cylm(0.045, 0.045, 0.04, 10), Vector3(-0.19, 0.16, -0.14 + i * 0.14), Color(0.72, 0.58, 0.28), 12.0, Vector3(0, 0, PI * 0.5))
	_deckel = par.node(kn, Vector3(0.18, 0.3, 0), 0.0)
	par.part(_deckel, par.boxm(0.38, 0.05, 0.54), Vector3(-0.19, 0.025, 0), Color(0.3, 0.2, 0.12), "tree")
	_kiste_glanz = par.node(kn, Vector3(0, 0.26, 0), 0.0)
	par.light_part(_kiste_glanz, par.boxm(0.26, 0.01, 0.34), Vector3.ZERO, par.glow_mat(Color(0.95, 0.88, 0.7), 0.6))
	_kiste_glanz.visible = false


func kugeln_welt() -> Array:
	var out := []
	for k in _kugeln:
		out.append([par.W(k[0]), float(k[1])])
	return out


func _spuren() -> void:
	"""scene 1: Lia's boot prints from her tent to the north"""
	var mt: Material = par.m.mat(Color(0.2, 0.17, 0.13))
	var z := -18.6
	var i := 0
	while z > -31.0:
		var x := -9.9 + 0.04 * i + (0.13 if i % 2 == 0 else -0.13)
		var p: Vector3 = par.G(x, z, 0.015)
		par.light_part(par.node(par.holder, p, 0.05), par.boxm(0.11, 0.01, 0.27), Vector3.ZERO, mt)
		z -= 0.72
		i += 1


func _feuerstelle() -> void:
	var f: Array = daten.FEUER
	var c: Vector2 = par.tal(float(f[0]), float(f[1]))
	var n: Node3D = par.node(par.holder, par.G(c.x, c.y), 0.0)
	for i in range(9):
		var a := TAU * i / 9.0
		par.part(n, par.sphm(0.13, 0.16, 8), Vector3(cos(a) * 0.45, 0.04, sin(a) * 0.45), Color(0.45, 0.44, 0.42), "stone")
	for a2 in [0.3, 1.4, 2.5]:
		par.part(n, par.cylm(0.05, 0.06, 0.7, 6), Vector3(0, 0.1, 0), Color(0.3, 0.2, 0.12), "tree", Vector3(PI * 0.5, a2, 0.25))


func _bojen() -> void:
	var fl: Dictionary = daten.FLOSS
	for k in fl["kurs"].slice(0, (fl["kurs"] as Array).size() - 1):
		var n: Node3D = par.node(par.holder, _sqw(float(k[0]), float(k[1]), wl), 0.0)
		par.part(n, par.sphm(0.22, 0.3, 10), Vector3(0, 0.06, 0), Color(0.86, 0.22, 0.16), "tent")
		par.part(n, par.cylm(0.03, 0.03, 0.7, 6), Vector3(0, 0.4, 0), Color(0.92, 0.92, 0.9), "tent")


func _floss_bauen_node() -> void:
	_floss_node = Node3D.new()
	_floss_node.name = "kit_floss"
	par.holder.add_child(_floss_node)
	var holz := Color(0.42, 0.32, 0.2)
	for i in range(4):
		par.part(_floss_node, par.cylm(0.17, 0.17, 2.5, 10), Vector3(-0.54 + i * 0.36, 0.0, 0), holz.darkened(0.06 * (i % 2)), "tree", Vector3(PI * 0.5, 0, 0))
	for z in [-0.9, 0.9]:
		par.part(_floss_node, par.boxm(1.5, 0.08, 0.14), Vector3(0, 0.18, z), holz.darkened(0.25), "tree")
		for x in [-0.54, -0.18, 0.18, 0.54]:
			par.part(_floss_node, par.boxm(0.36, 0.09, 0.05), Vector3(x, 0.19, z + 0.09), Color(0.78, 0.7, 0.5), 14.0)
	par.part(_floss_node, par.cylm(0.025, 0.025, 2.8, 6), Vector3(0.45, 0.26, 0.1), Color(0.55, 0.42, 0.26), "tree", Vector3(PI * 0.5, 0, 0.1))
	_floss_node.visible = false


func _floss_an(p: Vector2, h: float) -> void:
	_floss_node.visible = true
	_floss_node.position = Vector3(p.x, wl + 0.06, p.y)
	_floss_node.rotation.y = h
	if _floss_deck.is_empty():
		_floss_deck = par._deck(p, 1.0, 1.2, wl + 0.26)
	_floss_deck[0] = p


# =======================================================================================================================
# hooks from kit_abenteuer.gd
# =======================================================================================================================
func schritt_start(st: Dictionary) -> void:
	if st.has("duft"):
		duft_start(str(st["duft"]))
	elif bool(st.get("floss", false)):
		floss_start()


func ziel():
	return _ziel


func tick(dt: float, ein: Dictionary) -> Dictionary:
	"""before the figure: the scent trail, the raft, the lock - may take the action / the stick for itself"""
	if not kit.running or kit.phase in ["pause", "laden"]:
		return ein
	if not duft.is_empty():
		ein = _duft_tick(dt, ein)
	if not floss.is_empty() and bool(floss.get("an", false)):
		ein = _floss_tick(dt, ein)
	if _schloss != null:
		ein = _schloss_tick(ein)
	if not kit.erledigt.has("staemme") and kit.funde.has("stamm1") and kit.funde.has("stamm2") and kit.funde.has("stamm3"):
		kit.aktion_fertig("staemme")
		kit.sag(kit.tx("Drei Stämme. Genug für ein kleines Floss."), "figur")
	return ein


func aktion(art: String, ak: Dictionary) -> void:
	"""an action of chapter 3 (kit_abenteuer._aktion_effekt): it is marked done already"""
	var id := str(ak.get("id", ""))
	match art:
		"floss_bauen":
			if not kit.erledigt.has("staemme"):
				kit.erledigt.erase(id)
				par.erledigt.erase(id)
				kit.sag(kit.tx("Dafür brauche ich noch mehr Holz."), "figur")
		"marke":
			_marke_lesen(id)
		"schloss":
			if schloss_auf:                              # (aktion_fertig on opening comes here again)
				return
			kit.erledigt.erase(id)                       # done only when it opens
			par.erledigt.erase(id)
			schloss_oeffnen()
		"zeichen":
			pass


func film(e: Dictionary, sprung: bool) -> void:
	match str(e.get("k", "")):
		"floss_zeigen":
			var fl: Dictionary = daten.FLOSS
			_floss_an(par.tal(float(fl["start"][0]), float(fl["start"][1])), par.yaw_achse())
		"riss_leuchtet":
			if sprung:
				_riss_mat.emission_energy_multiplier = 2.2
			else:
				create_tween().tween_property(_riss_mat, "emission_energy_multiplier", 2.2, 1.2)
		"kiste_auf":
			_kiste_glanz.visible = true
			if sprung:
				_deckel.rotation.z = 1.9
			else:
				create_tween().tween_property(_deckel, "rotation:z", 1.9, 1.0).set_trans(Tween.TRANS_BACK)
		"feuer":
			if not _feuer_an:
				_feuer_an = true
				var f: Array = daten.FEUER
				par.ofen_an(par.tal(float(f[0]), float(f[1])), 0.35)
		"fund":
			kit.fund(str(e["id"]))


func control(d: Dictionary) -> Dictionary:
	match str(d.get("was", "info")):
		"schloss":
			if _schloss == null:
				schloss_oeffnen()
			var z: Array = d.get("zeichen", [])
			var sy: Array = daten.SCHLOSS["symbole"]
			for i in range(mini(3, z.size())):
				schloss_wahl[i] = maxi(0, sy.find(str(z[i])))
			_schloss_zeigen()
			if bool(d.get("oeffnen", true)):
				_schloss_pruefen()
			return {"ok": true, "info": info()}
		"schloss_zu":
			_schloss_schliessen()
	return {"ok": true, "info": info()}


func info() -> Dictionary:
	var o := {"gelesen": gelesen.keys(), "schloss_offen": _schloss != null, "schloss": schloss_wahl.duplicate(), "falsch": schloss_falsch}
	if not duft.is_empty():
		o["duft"] = {"i": int(duft["i"]), "n": (duft["pts"] as Array).size(), "t": snappedf(float(duft["t"]), 0.1),
			"weg": bool(duft["weg"]), "verloren": int(duft["verloren"])}
	if not floss.is_empty():
		var p: Vector2 = floss["p"]
		o["floss"] = {"an": bool(floss["an"]), "sq": [snappedf(par.sq(p).x, 0.01), snappedf(par.sq(p).y, 0.01)],
			"v": snappedf((floss["v"] as Vector2).length(), 0.01), "boje": int(floss["i"]), "boeen": int(floss["boeen"]),
			"gehalten": int(floss["gehalten"]), "zurueck": int(floss["zurueck"]), "boe": str(floss["boe"]["phase"])}
	return o


func aufraeumen() -> void:
	_see_hindernisse(false)
	if _layer != null and is_instance_valid(_layer):
		_layer.queue_free()
	if not _floss_deck.is_empty() and kit.bt != null:
		kit.bt.decks.erase(_floss_deck)


# =======================================================================================================================
# the scent trail
# =======================================================================================================================
func duft_start(id: String) -> void:
	var dd: Dictionary = daten.DUFT[id]
	var pts := []
	for p in dd["punkte"]:
		pts.append(par.welt(float(p[0]), float(p[1])))
	duft = {"id": id, "pts": pts, "i": 0, "t": 0.0, "fade0": float(dd.get("fade", 4.0)), "fade": 10.0, "r": float(dd.get("r", 2.0)),
		"weg": false, "verloren": 0}
	_puff_neu()


func _puff_neu() -> void:
	if _puff != null and is_instance_valid(_puff):
		_puff.queue_free()
	var w: Vector3 = duft["pts"][int(duft["i"])]
	_puff = Node3D.new()
	_puff.name = "kit_duft"
	par.holder.add_child(_puff)
	_puff.global_position = w + Vector3(0, 0.35, 0)
	_puff_mat = par.glow_mat(Color(0.9, 1.0, 0.55), 1.6, 0.55)
	_puff_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	for k in range(6):
		var a := TAU * k / 6.0
		par.light_part(_puff, par.sphm(0.16 + 0.05 * (k % 3), -1.0, 8), Vector3(cos(a) * 0.28, 0.12 * (k % 2) + 0.05 * k, sin(a) * 0.28), _puff_mat)
	var pt := CPUParticles3D.new()
	pt.amount = 10
	pt.lifetime = 1.8
	pt.direction = Vector3(0, 1, 0)
	pt.spread = 30.0
	pt.gravity = Vector3(0, 0.15, 0)
	pt.initial_velocity_min = 0.15
	pt.initial_velocity_max = 0.35
	pt.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	pt.emission_sphere_radius = 0.35
	var pm: SphereMesh = par.sphm(0.03, -1.0, 4)
	pm.material = _puff_mat
	pt.mesh = pm
	_puff.add_child(pt)
	duft["t"] = 0.0
	duft["weg"] = false
	duft["fade"] = float(duft["fade0"]) * (1.6 if kit.kinder else 1.0)
	duft["abst"] = INF
	duft["fort"] = kit.uhr
	_ziel = w + Vector3(0, 1.0, 0)
	if kit.hund != null:                                    # Maggie leads: to the cloud, a sniff
		var q: Vector3 = kit.hund.VL(w)
		kit.hund.modus = "folgen"
		kit.hund._aktion([{"t": "walk", "p": Vector3(q.x, 0, q.z), "spd": 2.6}, {"t": "idle", "k": "sniff", "s": 1.2}])


func _duft_tick(dt: float, ein: Dictionary) -> Dictionary:
	if kit.phase != "spiel":
		return ein
	# the cloud fades while one dawdles or goes the wrong way - hardly while one comes closer (fair at any frame rate)
	var w0: Vector3 = duft["pts"][int(duft["i"])]
	var ab: float = Vector2(kit.figur.pos().x - w0.x, kit.figur.pos().z - w0.z).length()
	if ab < float(duft.get("abst", INF)) - 0.05:            # a new closest point: progress (the figure moves on physics frames)
		duft["abst"] = ab
		duft["fort"] = kit.uhr
	var naeher: bool = kit.uhr - float(duft.get("fort", -10.0)) < 1.0
	duft["t"] = float(duft["t"]) + dt * (0.12 if naeher and not bool(duft["weg"]) else 1.0)
	var k := clampf(1.0 - float(duft["t"]) / float(duft["fade"]), 0.0, 1.0)
	if _puff != null and is_instance_valid(_puff):
		_puff.rotation.y += dt * 0.6
		_puff.position.y += sin(kit.uhr * 2.0) * 0.002
		_puff_mat.albedo_color.a = 0.6 * k
		_puff_mat.emission_energy_multiplier = 1.6 * k
		_puff.visible = k > 0.02
	if bool(duft["weg"]):
		if bool(ein.get("aktion", false)):                  # Maggie sniffs the trail again
			ein = ein.duplicate()
			ein["aktion"] = false
			if kit.hund != null:
				kit.hund.bellen(kit.hund.ppos(kit.hund.hund), 1)
			kit.sag(kit.tx("Such, Maggie! … Da lang!"), "figur")
			_puff_neu()
		return ein
	var w: Vector3 = duft["pts"][int(duft["i"])]
	var me: Vector3 = kit.figur.pos()
	if Vector2(me.x - w.x, me.z - w.z).length() < float(duft["r"]):
		duft["i"] = int(duft["i"]) + 1
		kit.ton("fund")
		if int(duft["i"]) >= (duft["pts"] as Array).size():
			if _puff != null and is_instance_valid(_puff):
				_puff.queue_free()
			_puff = null
			duft = {}
			_ziel = null
			kit.aktion_fertig("duft")
			return ein
		_puff_neu()
		return ein
	if k <= 0.0:                                            # gone: the trail is lost until Maggie sniffs again
		duft["weg"] = true
		duft["verloren"] = int(duft["verloren"]) + 1
		kit.merke("duft_verloren")
		_ziel = null
		kit.sag(kit.tx("Spur verloren! Drück die Aktion – Maggie schnüffelt neu."), "blinki")
	return ein


# =======================================================================================================================
# the raft
# =======================================================================================================================
func floss_start() -> void:
	var fl: Dictionary = daten.FLOSS
	var p0: Vector2 = par.tal(float(fl["start"][0]), float(fl["start"][1]))
	var kurs := [p0]
	for k in fl["kurs"]:
		kurs.append(par.tal(float(k[0]), float(k[1])))
	floss = {"an": true, "p": p0, "v": Vector2.ZERO, "h": par.yaw_achse(), "kurs": kurs, "i": 1, "letzte": p0,
		"breite": float(fl.get("breite", 7.0)), "boeen": 0, "gehalten": 0, "zurueck": 0,
		"boe": {"phase": "ruhe", "t": 0.0, "next": 3.5, "seite": 1.0, "gehalten": false, "frueh": false}}
	_floss_an(p0, par.yaw_achse())
	kit.figur.geh_zu("steuern")
	if kit.hund != null:
		kit.hund.modus = "warten"
	_floss_setzen(0.0)


func _floss_setzen(dt: float) -> void:
	var p: Vector2 = floss["p"]
	var v: Vector2 = floss["v"]
	if v.length() > 0.25:                                   # the raft turns slowly into its way
		var wh := atan2(-v.x, -v.y)
		floss["h"] = lerp_angle(float(floss["h"]), wh, clampf(dt * 1.4, 0.0, 1.0))
	var bob := sin(kit.uhr * 1.7) * 0.03
	_floss_node.position = Vector3(p.x, wl + 0.06 + bob, p.y)
	_floss_node.rotation = Vector3(sin(kit.uhr * 1.3) * 0.02, float(floss["h"]), sin(kit.uhr * 1.1) * 0.025)
	_floss_deck[0] = p
	var fw: Vector3 = par.W(Vector3(p.x, wl + 0.26, p.y))
	var a = kit.figur.a
	a.position.x = fw.x
	a.position.z = fw.z
	var hw: Vector3 = par.W(Vector3(p.x - sin(float(floss["h"])), wl, p.y - cos(float(floss["h"])))) - par.W(Vector3(p.x, wl, p.y))
	a.heading = atan2(-hw.x, -hw.z)
	a.rotation.y = a.heading
	if kit.hund != null and kit.hund.hund != null:
		var hp := Vector2(p.x, p.y) + Vector2(sin(float(floss["h"])), cos(float(floss["h"]))) * 0.75
		kit.hund.place(kit.hund.hund, Vector3(hp.x, wl + 0.27, hp.y), true)


func _seg_abstand(p: Vector2) -> float:
	var K: Array = floss["kurs"]
	var best := 1.0e9
	for i in range(K.size() - 1):
		var q := Geometry2D.get_closest_point_to_segment(p, K[i], K[i + 1])
		best = minf(best, p.distance_to(q))
	return best


func _floss_tick(dt: float, ein: Dictionary) -> Dictionary:
	if kit.phase != "spiel":
		_floss_setzen(dt)
		return ein
	dt = clampf(dt, 0.0, 0.1)
	var mv: Vector2 = ein.get("mv", Vector2.ZERO)
	var akt := bool(ein.get("aktion", false))
	ein = ein.duplicate()
	ein["mv"] = Vector2.ZERO
	ein["aktion"] = false
	ein["sprung"] = false
	var tal_d: Vector3 = kit.bt.tal.transform.basis.inverse() * Vector3(mv.x, 0, mv.y)
	var a := Vector2(tal_d.x, tal_d.z)
	var v: Vector2 = floss["v"]
	v += a * 1.7 * dt
	v *= exp(-0.6 * dt)
	var vmax := 2.5 if kit.kinder else 2.1
	if v.length() > vmax:
		v = v.normalized() * vmax
	# the gusts (only out on the lake, after the first buoy)
	var K: Array = floss["kurs"]
	var i := int(floss["i"])
	var b: Dictionary = floss["boe"]
	var seg: Vector2 = ((K[mini(i, K.size() - 1)] as Vector2) - (K[maxi(0, i - 1)] as Vector2)).normalized()
	var quer := Vector2(-seg.y, seg.x)
	if i >= 2:
		b["t"] = float(b["t"]) + dt
		match str(b["phase"]):
			"ruhe":
				if float(b["t"]) > float(b["next"]):
					b["phase"] = "warn"
					b["t"] = 0.0
					b["seite"] = -1.0 if _rng.randf() < 0.5 else 1.0
					b["gehalten"] = false
					b["frueh"] = false
					kit.ton("wind")
			"warn":
				if akt:
					if float(b["t"]) > 0.7:
						b["gehalten"] = true
						kit.figur.a.aktion("heben", 0.8)
					elif not bool(b["frueh"]):
						b["frueh"] = true
						kit.hud.toast(T.t("Zu früh! Warte, bis der Balken fast voll ist."), 1.6)
				if float(b["t"]) > 1.6:
					b["phase"] = "boe"
					b["t"] = 0.0
			"boe":
				if akt and float(b["t"]) < 0.5 and not bool(b["frueh"]):
					b["gehalten"] = true
				var f := (1.1 if kit.kinder else 2.3) * (0.12 if bool(b["gehalten"]) else 1.0)
				v += quer * float(b["seite"]) * f * dt
				if float(b["t"]) > 1.4:
					floss["boeen"] = int(floss["boeen"]) + 1
					if bool(b["gehalten"]):
						floss["gehalten"] = int(floss["gehalten"]) + 1
					else:
						kit.merke("boe_verpasst")
					b["phase"] = "ruhe"
					b["t"] = 0.0
					b["next"] = _rng.randf_range(3.2, 5.0)
	_ui_boe_zeigen(b, i >= 2)
	var p: Vector2 = floss["p"]
	p += v * dt
	floss["v"] = v
	floss["p"] = p
	# off the course: back to the last buoy (nobody drowns)
	if _seg_abstand(p) > float(floss["breite"]):
		floss["zurueck"] = int(floss["zurueck"]) + 1
		kit.merke("kurs_verloren")
		floss["p"] = floss["letzte"]
		floss["v"] = Vector2.ZERO
		b["phase"] = "ruhe"
		b["t"] = 0.0
		kit.hud.blende(0.8)
		kit.sag(kit.tx("Vom Kurs abgekommen – zurück zur letzten Boje."), "blinki")
	elif p.distance_to(K[i]) < (2.2 if i == K.size() - 1 else 3.2):
		floss["letzte"] = K[i]
		floss["i"] = i + 1
		if i + 1 >= K.size():
			_floss_angelegt()
			return ein
		kit.ton("fund")
	_floss_setzen(dt)
	var ni := mini(int(floss["i"]), K.size() - 1)
	var nz: Vector2 = K[ni]
	_ziel = par.W(Vector3(nz.x, wl + 1.0, nz.y))
	return ein


func _floss_angelegt() -> void:
	"""at the landing of the Seeblock: off the raft"""
	floss["an"] = false
	floss["v"] = Vector2.ZERO
	_ui_boe_zeigen({}, false)
	_floss_setzen(0.0)
	var st: Dictionary = daten.SEEBLOCK["steg"]
	kit.figur.setzen(par.welt_abs(float(st["c"][0]), float(st["c"][1]), wl + float(st["top_see"])), kit.figur.a.heading)
	kit.figur.geh_zu("boden")
	if kit.hund != null:
		kit.hund.setzen_welt(par.welt_abs(float(st["c"][0]) - 1.2, float(st["c"][1]), wl + float(st["top_see"])))
		kit.hund.place(kit.hund.hund, _sqw(float(st["c"][0]) - 1.2, float(st["c"][1]), wl + float(st["top_see"])), true)
		kit.hund.modus = "folgen"
	_ziel = null
	if not kit.merker.has("kurs_verloren") and not kit.merker.has("boe_verpasst") and int(floss["boeen"]) >= 2:
		kit.merke("kapitaen")
	kit.aktion_fertig("floss")


func _ui_boe() -> void:
	_boe_box = PanelContainer.new()
	_boe_box.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.1, 0.86), Color(0.55, 0.85, 1.0, 0.7), 12, 10, 1))
	_boe_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var v := VBoxContainer.new()
	_boe_box.add_child(v)
	_boe_lab = Label.new()
	_boe_lab.add_theme_font_size_override("font_size", 20)
	_boe_lab.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(_boe_lab)
	_boe_bar = ProgressBar.new()
	_boe_bar.min_value = 0.0
	_boe_bar.max_value = 1.0
	_boe_bar.show_percentage = false
	_boe_bar.custom_minimum_size = Vector2(320, 14)
	v.add_child(_boe_bar)
	var c := Control.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.theme = UI.theme()
	_layer.add_child(c)
	c.add_child(_boe_box)
	_boe_box.visible = false


func _ui_boe_zeigen(b: Dictionary, an: bool) -> void:
	if _boe_box == null:
		return
	var ph := str(b.get("phase", "ruhe"))
	_boe_box.visible = an and ph in ["warn", "boe"]
	if not _boe_box.visible:
		return
	var links := float(b.get("seite", 1.0)) > 0.0
	if ph == "warn":
		_boe_lab.text = (T.t("Böe von links!") if links else T.t("Böe von rechts!")) + "  " + T.t("Gleich: Aktion – Stange einstemmen")
		_boe_bar.value = clampf(float(b["t"]) / 1.6, 0.0, 1.0)
		_boe_bar.modulate = Color(0.55, 1.0, 0.55) if float(b["t"]) > 0.7 else Color(1.0, 0.85, 0.4)
	else:
		_boe_lab.text = T.t("Gehalten!") if bool(b.get("gehalten", false)) else T.t("Die Böe schiebt das Floss!")
		_boe_bar.value = 1.0
		_boe_bar.modulate = Color(0.55, 1.0, 0.55) if bool(b.get("gehalten", false)) else Color(1.0, 0.45, 0.35)
	var vs: Vector2 = _boe_box.get_viewport().get_visible_rect().size
	_boe_box.reset_size()
	_boe_box.position = Vector2((vs.x - _boe_box.size.x) * 0.5, vs.y * 0.16)


# =======================================================================================================================
# the marks and the lock
# =======================================================================================================================
func _marke_lesen(id: String) -> void:
	if not _marken.has(id) or gelesen.has(id):
		return
	gelesen[id] = true
	var mk: Dictionary = _marken[id]
	(mk["moos"] as Node3D).visible = false
	(mk["schrift"] as Node3D).visible = true
	kit.figur.a.aktion("aufheben", 1.0)
	kit.sag(T.t("Unter dem Moos: «%s» – und daneben «%s».") % [str(mk["nr"]), str(mk["zeichen"])], "figur")
	if gelesen.size() >= _marken.size():
		kit.aktion_fertig("marken")


func schloss_oeffnen() -> void:
	if _schloss != null:
		return
	kit.figur.geh_zu("steuern")
	_schloss = PanelContainer.new()
	_schloss.add_theme_stylebox_override("panel", UI.box(Color(0.06, 0.05, 0.04, 0.95), Color(0.9, 0.7, 0.35, 0.8), 16, 18, 1))
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = UI.theme()
	root.name = "kit_schloss"
	_layer.add_child(root)
	root.add_child(_schloss)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	_schloss.add_child(v)
	var t := Label.new()
	t.text = T.t("Die Kiste: drei Rädchen")
	t.add_theme_font_size_override("font_size", 22)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 14)
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(h)
	_schloss_lab.clear()
	_schloss_rahmen.clear()
	for i in range(3):
		var rahmen := PanelContainer.new()
		h.add_child(rahmen)
		var col := VBoxContainer.new()
		col.add_theme_constant_override("separation", 6)
		rahmen.add_child(col)
		var hoch := Button.new()
		hoch.text = "▲"
		hoch.custom_minimum_size = Vector2(78, 44)
		var idx := i
		hoch.pressed.connect(func(): _rad(idx, -1))
		col.add_child(hoch)
		var lab := Label.new()
		lab.add_theme_font_size_override("font_size", 46)
		lab.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lab.custom_minimum_size = Vector2(78, 64)
		col.add_child(lab)
		var runter := Button.new()
		runter.text = "▼"
		runter.custom_minimum_size = Vector2(78, 44)
		runter.pressed.connect(func(): _rad(idx, 1))
		col.add_child(runter)
		_schloss_lab.append(lab)
		_schloss_rahmen.append(rahmen)
	var hk := Label.new()
	hk.text = T.t("←/→ Rädchen · ↑/↓ Zeichen · Enter öffnen · Esc zurück")
	hk.add_theme_font_size_override("font_size", 14)
	hk.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(hk)
	var knoepfe := HBoxContainer.new()
	knoepfe.alignment = BoxContainer.ALIGNMENT_CENTER
	knoepfe.add_theme_constant_override("separation", 12)
	v.add_child(knoepfe)
	var zu := Button.new()
	zu.text = T.t("Zurück")
	zu.custom_minimum_size = Vector2(140, 46)
	zu.pressed.connect(func(): _schloss_schliessen())
	knoepfe.add_child(zu)
	var ok := Button.new()
	ok.text = T.t("Öffnen")
	ok.custom_minimum_size = Vector2(160, 46)
	UI.primary(ok)
	ok.pressed.connect(func(): _schloss_pruefen())
	knoepfe.add_child(ok)
	_tasten = {}
	_schloss_zeigen()


func _rad(i: int, d: int) -> void:
	var n: int = (daten.SCHLOSS["symbole"] as Array).size()
	schloss_sel = i
	schloss_wahl[i] = posmod(int(schloss_wahl[i]) + d, n)
	kit.ton("klick")
	_schloss_zeigen()


func _schloss_zeigen() -> void:
	if _schloss == null:
		return
	var sy: Array = daten.SCHLOSS["symbole"]
	for i in range(3):
		(_schloss_lab[i] as Label).text = str(sy[int(schloss_wahl[i])])
		var sel := i == schloss_sel
		(_schloss_rahmen[i] as PanelContainer).add_theme_stylebox_override("panel",
				UI.box(Color(0.16, 0.12, 0.07, 0.9) if sel else Color(0.1, 0.08, 0.06, 0.8), Color(1.0, 0.8, 0.4, 0.95) if sel else Color(0.5, 0.4, 0.25, 0.5), 10, 6, 2 if sel else 1))
	_schloss.reset_size()
	var vs: Vector2 = _schloss.get_viewport().get_visible_rect().size if _schloss.is_inside_tree() else Vector2(1280, 720)
	_schloss.position = (vs - _schloss.get_combined_minimum_size()) * 0.5


func _taste_neu(k: int) -> bool:
	var on := Input.is_key_pressed(k)
	var alt := bool(_tasten.get(k, false))
	_tasten[k] = on
	return on and not alt


func _schloss_tick(ein: Dictionary) -> Dictionary:
	if _taste_neu(KEY_LEFT) or _taste_neu(KEY_A):
		schloss_sel = posmod(schloss_sel - 1, 3)
		_schloss_zeigen()
	if _taste_neu(KEY_RIGHT) or _taste_neu(KEY_D):
		schloss_sel = posmod(schloss_sel + 1, 3)
		_schloss_zeigen()
	if _taste_neu(KEY_UP) or _taste_neu(KEY_W):
		_rad(schloss_sel, -1)
	if _taste_neu(KEY_DOWN) or _taste_neu(KEY_S):
		_rad(schloss_sel, 1)
	if _taste_neu(KEY_ENTER) or _taste_neu(KEY_KP_ENTER) or _taste_neu(KEY_E):
		_schloss_pruefen()
	elif _taste_neu(KEY_ESCAPE):
		_schloss_schliessen()
	ein = ein.duplicate()
	ein["mv"] = Vector2.ZERO
	ein["aktion"] = false
	ein["sprung"] = false
	return ein


func _schloss_pruefen() -> void:
	if _schloss == null:
		return
	var sy: Array = daten.SCHLOSS["symbole"]
	var los: Array = daten.SCHLOSS["loesung"]
	var ok := true
	for i in range(3):
		ok = ok and str(sy[int(schloss_wahl[i])]) == str(los[i])
	if ok:
		schloss_auf = true
		_schloss_schliessen()
		kit.ton("fund")
		kit.aktion_fertig("schloss")
		return
	schloss_falsch += 1
	var tw := create_tween()
	var x0: float = _schloss.position.x
	for k in range(3):
		tw.tween_property(_schloss, "position:x", x0 + 10.0, 0.04)
		tw.tween_property(_schloss, "position:x", x0 - 10.0, 0.04)
	tw.tween_property(_schloss, "position:x", x0, 0.04)
	if schloss_falsch == 1:
		kit.sag(kit.tx("Klick. Nichts. Die Zeichen am Fels haben Nummern."), "blinki")
	elif schloss_falsch >= 2 and kit.kinder:
		kit.sag(kit.tx("Zuerst I, dann II, dann III."), "blinki")


func _schloss_schliessen() -> void:
	if _schloss == null:
		return
	var r := _schloss.get_parent()
	_schloss = null
	if r != null:
		r.queue_free()
	if kit.figur != null and kit.figur.zustand == "steuern" and (floss.is_empty() or not bool(floss.get("an", false))):
		kit.figur.geh_zu("boden")
