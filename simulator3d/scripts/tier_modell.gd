extends Node
## «Flora und Fauna»: Tiere als echte Modelle mit Skelett und eigenen Bewegungen (Phase 1: der Fuchs; Paket 3 «Tiere echt»:
## Reh, Hund in mehreren Rassen / Farbschlägen, Katze in vier Farbschlägen, Igel).
## Modelle: Quaternius «Ultimate Animated Animals» (CC0, wie Maggie), mit werkzeuge/tier_modelle.py zu EINEM Netz mit
## Fell-Farben gemacht (Katze und Igel aus dem Fuchs umgeformt); Dateien modelle/<art>_glb.bin, Kennzahlen im GLB
## (scenes[0].extras.moveeye: Rückenhöhe, Augen, Bereiche für das Wärmebild). Fell: shaders/maggie_fell.gdshader
## (Haarstruktur, Randlicht; Farbschlag aus der Helligkeit).
##
## Was gleich bleibt (Wahrheit der Erkennung):
##   - actor.gd bewegt das Tier wie bisher (Weg, Tempo, Flucht, Verhalten aus tiere.gd); das Modell hängt an body_root,
##     Rückenhöhe wie die Grundformen (Hunde: je nach Rasse etwas kleiner / grösser, siehe VARIANTEN).
##   - Das Wärmebild: bis Paket 2 blieben die Zwillinge der Grundformen; jetzt hat das Modell einen eigenen Zwilling
##     (dasselbe Netz, dieselbe Haut, shaders/thermal_tier.gdshader) mit DENSELBEN Temperaturen wie die Grundformen
##     (Rumpf, Kopf, Beine, Augen, kühle Teile - aus ihren Wärme-Materialien gelesen) - die Form passt jetzt zum Bild.
##     WAERME_MODELL = false: wie bisher (Zwillinge der Grundformen).
##   - Der Rahmen der Trainingsbilder (dataset.gd: sichtbare Netze der Ebene 1) kommt aus «pose_aabb», jede 0.2 s aus den
##     Knochen der Pose gerechnet (wie figur.gd).
##   - Die Augen leuchten nachts wie bisher (a.lights, Infrarot-Reflex), jetzt am Kopf-Knochen des Modells.
## Bewegungen: Gehen / Traben (Walk, Tempo nach der Geschwindigkeit), Galopp auf der Flucht, Mäusesprung (Gallop_Jump),
## Schnüffeln (Idle_2_HeadLow), Fressen / Äsen / Graben (Eating), Stehen und Sichern (Idle / Idle_2), weich überblendet;
## Katze: Schleichen tief und langsam; Igel: rollt sich ein (Kopf und Beine verschwinden unter den Stacheln).
## Leistung: die Bewegung wird von Hand weitergerechnet - nah jedes Bild, ab 30 m jedes 3., ab 70 m jedes 6. Bild.
## Nur ab Stufe «normal» (scripts/flora.gd), nicht in Lite und nicht im Prüfstand (--quality): dort die Grundformen wie bisher.
## Schalter für Tests: MW_TIERE=modell | alt (siehe an()).

const WAERME_MODELL := true

# Art -> Rückenhöhe (m, wie die Grundformen von actor.gd: hb × 1.32), Augen-Radius (m), Fellhaare (pro m), Varianten
const ARTEN := {
	"fox": {"ruecken_m": 0.4092, "auge_m": 0.009},
	"deer": {"ruecken_m": 0.726, "auge_m": 0.013},
	"dog": {"ruecken_m": 0.66, "auge_m": 0.01},
	"cat": {"ruecken_m": 0.2904, "auge_m": 0.008},
	"hedgehog": {"ruecken_m": 0.16, "auge_m": 0.004},
}
# Farbschläge: [dunkel, mittel, hell, Helligkeit «hell» im Original] (lineare Farben, maggie_fell.gdshader)
const VARIANTEN := {
	"fox": [{"datei": "fuchs"}],
	"deer": [{"datei": "reh"}],
	# Hund: nach der Farbe der Grundform (actor.gd: braun, schwarz, creme, grau)
	"dog": [{"datei": "hund_shiba", "groesse": 0.8},
			{"datei": "hund_husky", "groesse": 1.0, "farbe": [Color(0.006, 0.006, 0.006), Color(0.014, 0.013, 0.012), Color(0.05, 0.045, 0.04), 0.7]},
			{"datei": "hund_shiba", "groesse": 1.0, "farbe": [Color(0.16, 0.09, 0.03), Color(0.56, 0.38, 0.15), Color(0.84, 0.70, 0.46), 0.7]},
			{"datei": "hund_husky", "groesse": 0.95}],
	# Katze: getigert grau, rot, schwarz, weiss (actor.gd: dieselbe Reihenfolge)
	"cat": [{"datei": "katze"},
			{"datei": "katze", "farbe": [Color(0.30, 0.11, 0.03), Color(0.66, 0.32, 0.10), Color(0.88, 0.68, 0.42), 0.52]},
			{"datei": "katze", "farbe": [Color(0.005, 0.005, 0.005), Color(0.011, 0.010, 0.010), Color(0.03, 0.028, 0.027), 0.52]},
			{"datei": "katze", "farbe": [Color(0.40, 0.38, 0.35), Color(0.66, 0.64, 0.60), Color(0.78, 0.76, 0.72), 0.52]}],
	"hedgehog": [{"datei": "igel"}],
}
const FARBE_ALT := {   # actor.gd _build_animal: die Grundfarben vor dem Aufhellen (Index = Variante)
	"dog": [Color(0.45, 0.35, 0.22), Color(0.1, 0.1, 0.1), Color(0.85, 0.75, 0.55), Color(0.6, 0.55, 0.5)],
	"cat": [Color(0.35, 0.33, 0.3), Color(0.85, 0.5, 0.2), Color(0.1, 0.1, 0.1), Color(0.9, 0.88, 0.85)],
}
const REH_WINTER := [Color(0.025, 0.02, 0.016), Color(0.24, 0.19, 0.14), Color(0.62, 0.59, 0.54), 0.36]   # Okt. - April
const SCHRITT := [0.75, 3.2]      # m/s beim Fuchs (Rücken 0.41 m), bei denen Walk / Gallop mit Tempo 1 ohne Rutschen laufen
# (die alte Liste DATEI bleibt der Schalter für actor.gd: welche Arten ein Modell bekommen)
const DATEI := {"fox": "fuchs", "deer": "reh", "dog": "hund", "cat": "katze", "hedgehog": "igel"}

static var _cache := {}           # datei -> {"bytes", "meta"}
static var fehler := ""

var a
var kind := ""
var meta := {}
var sk: Skeleton3D
var mi: MeshInstance3D
var th: MeshInstance3D
var ap: AnimationPlayer
var holder: Node3D
var einheit := 0.17               # m pro Modell-Einheit
var _cur := ""
var _box_t := 0.0
var _lod_t := 0.0
var _lod_n := 1
var _frame := 0
var _acc := 0.0
var _stp := [0.75, 3.2]
var _igel_bones: Array = []


static func an(stufe: String) -> bool:
	"""Modelle ab Stufe normal / hoch (flora.gd). Für Tests: Umgebung MW_TIERE=modell (immer, auch im Prüfstand mit
	--quality, z. B. Erkennungstest mit den neuen Tieren, ohne die Pflanzen zu ändern) bzw. MW_TIERE=alt (nie)"""
	var e := OS.get_environment("MW_TIERE")
	if e == "modell":
		return true
	if e == "alt":
		return false
	return stufe in ["normal", "hoch"]


static func _datei_laden(datei: String) -> Dictionary:
	if _cache.has(datei):
		return _cache[datei]
	var p := "res://modelle/%s_glb.bin" % datei
	var b := FileAccess.get_file_as_bytes(p) if FileAccess.file_exists(p) else PackedByteArray()
	var e := {"bytes": b, "meta": {}}
	if b.is_empty():
		fehler = "Modell fehlt: " + p
	_cache[datei] = e
	return e


static func verfuegbar(k: String) -> bool:
	if not VARIANTEN.has(k):
		return false
	return not (_datei_laden(str(VARIANTEN[k][0]["datei"]))["bytes"] as PackedByteArray).is_empty()


static func _variante(act, k: String) -> int:
	"""Farbschlag / Rasse aus der Farbe der Grundform (actor.gd würfelt sie schon - kein neuer Zufall)"""
	var vs: Array = VARIANTEN[k]
	if vs.size() < 2:
		return 0
	var c := Color(-1, -1, -1)
	for n in act.body_root.get_children():
		if n is MeshInstance3D and (n as MeshInstance3D).layers == 1 and (n as MeshInstance3D).material_override is StandardMaterial3D:
			c = ((n as MeshInstance3D).material_override as StandardMaterial3D).albedo_color
			break
	if c.r < 0.0 or not FARBE_ALT.has(k):
		return act.get_instance_id() % vs.size()
	var best := 0
	var bd := INF
	var pal: Array = FARBE_ALT[k]
	for i in range(pal.size()):
		var p: Color = pal[i]
		# die Grundfarbe ist bis zu 15 % aufgehellt (col.lerp(col.lightened(0.15), randf())): mit beiden Enden vergleichen
		var dd: float = minf(Vector3(c.r - p.r, c.g - p.g, c.b - p.b).length(),
				Vector3(c.r - p.lightened(0.15).r, c.g - p.lightened(0.15).g, c.b - p.lightened(0.15).b).length())
		if dd < bd:
			bd = dd
			best = i
	return best


static func bauen(act) -> Node:
	"""das Modell an actor.gd (Tier) hängen; null = nicht möglich (dann bleiben die Grundformen)"""
	var k: String = act.kind
	if not verfuegbar(k):
		return null
	var vi := _variante(act, k)
	var v: Dictionary = VARIANTEN[k][vi]
	var e := _datei_laden(str(v["datei"]))
	if (e["bytes"] as PackedByteArray).is_empty():
		return null
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_buffer(e["bytes"], "", st) != OK:
		fehler = "Modell nicht lesbar"
		return null
	if (e["meta"] as Dictionary).is_empty():
		var js = st.json
		if typeof(js) == TYPE_DICTIONARY and js.has("scenes"):
			var sc0 = js["scenes"][0]
			if typeof(sc0) == TYPE_DICTIONARY and sc0.has("extras"):
				e["meta"] = sc0["extras"].get("moveeye", {})
	var sc := doc.generate_scene(st) as Node3D
	if sc == null:
		return null
	var r = load("res://scripts/tier_modell.gd").new()
	r.name = "tier_modell"
	if not r._aufbauen(act, k, sc, v, e["meta"]):
		r.free()
		sc.free()
		return null
	return r


func _twin_temps() -> Dictionary:
	"""die Temperaturen der Grundformen (ihre Wärme-Zwillinge, Ebene 2): Rumpf, Kopf, Beine, Augen, kühlste Teile"""
	var all: Array = []
	var body := NAN
	for n in a.body_root.find_children("*", "MeshInstance3D", true, false):
		var m := n as MeshInstance3D
		if m.layers != 2 or not (m.material_override is ShaderMaterial):
			continue
		var t = (m.material_override as ShaderMaterial).get_shader_parameter("temp")
		if t == null:
			continue
		all.append(float(t))
		if is_nan(body) and m.get_parent() == a.body_root:
			body = float(t)
	if all.is_empty():
		return {}
	var head_t: Array = []
	if a.head != null:
		for n in a.head.get_children():
			if n is MeshInstance3D and (n as MeshInstance3D).layers == 2 and (n as MeshInstance3D).material_override is ShaderMaterial:
				var t2 = ((n as MeshInstance3D).material_override as ShaderMaterial).get_shader_parameter("temp")
				if t2 != null:
					head_t.append(float(t2))
	var leg_t: Array = []
	if not a.legs.is_empty() and is_instance_valid(a.legs[0][0]):
		for n in (a.legs[0][0] as Node).find_children("*", "MeshInstance3D", true, false):
			if (n as MeshInstance3D).layers == 2 and (n as MeshInstance3D).material_override is ShaderMaterial:
				var t3 = ((n as MeshInstance3D).material_override as ShaderMaterial).get_shader_parameter("temp")
				if t3 != null:
					leg_t.append(float(t3))
	all.sort()
	var eye: float = all[all.size() - 1]
	var hd := body
	var hs: Array = head_t.filter(func(x): return x < eye - 0.01)
	if not hs.is_empty():
		hs.sort()
		hd = hs[hs.size() - 1]
	var lg := body
	if not leg_t.is_empty():
		leg_t.sort()
		lg = leg_t[leg_t.size() / 2]
	return {"rumpf": body, "kopf": hd, "beine": lg, "auge": eye, "kuehl": all[0]}


func _aufbauen(act, k: String, sc: Node3D, v: Dictionary, m: Dictionary) -> bool:
	a = act
	kind = k
	meta = m
	var sks := sc.find_children("*", "Skeleton3D", true, false)
	var mis := sc.find_children("*", "MeshInstance3D", true, false)
	var aps := sc.find_children("*", "AnimationPlayer", true, false)
	if sks.is_empty() or mis.is_empty() or aps.is_empty() or meta.is_empty():
		fehler = "Modell ohne Skelett / Bewegungen / Kennzahlen"
		return false
	sk = sks[0]
	mi = mis[0]
	ap = aps[0]
	var art: Dictionary = ARTEN[k]
	var groesse: float = float(v.get("groesse", 1.0))
	einheit = float(art["ruecken_m"]) * groesse / float(meta["ruecken"])
	var temps := _twin_temps() if WAERME_MODELL else {}
	# the visible basic shapes go (layer 1); their thermal twins (layer 2) too when the model has its own twin
	for n in a.body_root.find_children("*", "MeshInstance3D", true, false):
		var bm := n as MeshInstance3D
		if bm.layers == 1 or (bm.layers == 2 and not temps.is_empty()):
			bm.visible = false
	holder = Node3D.new()
	holder.name = "modell"
	holder.basis = Basis(Vector3.UP, PI).scaled(Vector3.ONE * einheit)   # the model looks to +z
	a.body_root.add_child(holder)
	holder.add_child(sc)
	var lite := Engine.has_meta("lite") and bool(Engine.get_meta("lite"))
	var fm := ShaderMaterial.new()
	fm.shader = load("res://shaders/maggie_fell.gdshader")
	fm.set_shader_parameter("fein", 0.0 if lite else 1.0)
	fm.set_shader_parameter("haar", 370.0 * einheit)          # gleich dicht wie beim Fuchs (63 pro Einheit)
	fm.set_shader_parameter("rand", 0.45)
	fm.set_shader_parameter("bein_y", float(meta.get("bein_y", 1.35)))
	var farbe = v.get("farbe", null)
	if k == "deer" and _winterfell():
		farbe = REH_WINTER
	if farbe != null:
		var f: Array = farbe
		fm.set_shader_parameter("umfaerben", 1.0)
		fm.set_shader_parameter("f_dunkel", Vector3(f[0].r, f[0].g, f[0].b))
		fm.set_shader_parameter("f_mittel", Vector3(f[1].r, f[1].g, f[1].b))
		fm.set_shader_parameter("f_hell", Vector3(f[2].r, f[2].g, f[2].b))
		fm.set_shader_parameter("hell_ref", float(f[3]))
	mi.set_surface_override_material(0, fm)
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if lite else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	mi.extra_cull_margin = 1.0
	if not temps.is_empty():
		_waerme_zwilling(temps)
	_augen()
	if k == "deer" and _bock():
		_geweih(temps)
	if k == "hedgehog":
		for bn in ["Head", "Neck3", "FrontUpperLeg.L", "FrontUpperLeg.R", "BackUpperLeg.L", "BackUpperLeg.R", "Tail1"]:
			var bi := sk.find_bone(bn)
			if bi >= 0:
				_igel_bones.append(bi)
	for an in ap.get_animation_list():
		var anim := ap.get_animation(an)
		if anim != null:
			anim.loop_mode = Animation.LOOP_NONE if an == "Gallop_Jump" else Animation.LOOP_LINEAR
	ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var gr: float = float(art["ruecken_m"]) * groesse / 0.4092
	_stp = [SCHRITT[0] * gr, SCHRITT[1] * gr]
	_play("Idle_2", 0.0)
	ap.seek(float(a.get_instance_id() % 997) / 997.0 * 2.0, true)   # (no randf(): the global random numbers stay the same)
	process_priority = 120                                   # after actor.gd and tiere.gd
	a.add_child(self)
	_update_box()
	return true


func _winterfell() -> bool:
	var d := 196
	if a.main != null and a.main.has_method("day_of_year"):
		d = int(a.main.day_of_year())
	return d >= 285 or d < 115                               # Reh: graues Winterhaar etwa Mitte Oktober bis April


func _bock() -> bool:
	"""actor.gd hat dem Reh (zu 40 %) ein Geweih gegeben: zwei schmale Zylinder am Kopf - dann ist es ein Bock"""
	if a.head == null:
		return false
	for n in a.head.get_children():
		if n is MeshInstance3D and (n as MeshInstance3D).mesh is CylinderMesh:
			return true
	return false


func _waerme_zwilling(t: Dictionary) -> void:
	var tm := ShaderMaterial.new()
	tm.shader = load("res://shaders/thermal_tier.gdshader")
	tm.set_shader_parameter("spread", 0.6)
	tm.set_shader_parameter("t_rumpf", float(t["rumpf"]))
	tm.set_shader_parameter("t_kopf", float(t["kopf"]))
	tm.set_shader_parameter("t_beine", float(t["beine"]))
	tm.set_shader_parameter("t_auge", float(t["auge"]))
	tm.set_shader_parameter("t_kuehl", float(t["kuehl"]))
	for key in ["kopf_z", "kopf_y", "bein_y", "schwanz_z"]:
		tm.set_shader_parameter(key, float(meta.get(key, 0.0)))
	tm.set_shader_parameter("einheit", einheit)
	if a.main != null and a.main.has_method("th_reg"):
		a.main.th_reg(tm)
	th = MeshInstance3D.new()
	th.name = "waerme"
	th.mesh = mi.mesh
	th.skin = mi.skin
	th.material_override = tm
	th.layers = 2
	th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	th.extra_cull_margin = 1.0
	mi.get_parent().add_child(th)
	th.transform = mi.transform
	th.skeleton = mi.skeleton


func _augen() -> void:
	"""eyes: they shine in the light at night (like _eyes in actor.gd) - on the head bone of the model"""
	var hi := sk.find_bone("Head")
	if hi < 0:
		return
	var ba := BoneAttachment3D.new()
	ba.bone_name = "Head"
	sk.add_child(ba)
	var inv := sk.get_bone_global_rest(hi).affine_inverse()
	var em := StandardMaterial3D.new()
	em.albedo_color = Color(0.03, 0.025, 0.02)
	em.roughness = 0.1
	em.emission_enabled = true
	em.emission = Color(0.9, 0.95, 0.8)
	em.emission_energy_multiplier = 0.0
	a.lights.append(em)
	var r: float = float(ARTEN[kind]["auge_m"]) / einheit
	var eye := SphereMesh.new()
	eye.radius = r
	eye.height = r * 1.5
	eye.radial_segments = 8
	eye.rings = 4
	var p0: Array = meta.get("augen", [0.2, 2.0, 2.0])
	for s in [-1.0, 1.0]:
		var e := MeshInstance3D.new()
		e.mesh = eye
		e.material_override = em
		e.layers = 1
		e.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		e.position = inv * Vector3(float(p0[0]) * s, float(p0[1]), float(p0[2]) + r * 0.4)
		ba.add_child(e)


static var _geweih_mesh: ArrayMesh = null


func _geweih(t: Dictionary) -> void:
	"""Rehbock: kurzes Gehörn (Sechser, ~20 cm) mit Rosen, rau und dunkel, Enden hell - am Kopf-Knochen"""
	var hi := sk.find_bone("Head")
	if hi < 0:
		return
	if _geweih_mesh == null:
		var stt := SurfaceTool.new()
		stt.begin(Mesh.PRIMITIVE_TRIANGLES)
		var parts: Array = []
		for s in [-1.0, 1.0]:
			# [Start (m, vom Scheitel), Richtung, Länge, Radius unten, oben, Farbe]
			var base := Vector3(0.035 * s, 0.0, 0.0)
			var up := Vector3(0.18 * s, 1.0, 0.12).normalized()
			parts.append([base, up, 0.025, 0.017, 0.016, Color(0.30, 0.25, 0.20)])                  # Rose
			parts.append([base + up * 0.02, up, 0.2, 0.011, 0.005, Color(0.22, 0.17, 0.12)])        # Stange
			parts.append([base + up * 0.09, Vector3(0.1 * s, 0.6, 1.0).normalized(), 0.055, 0.006, 0.0025, Color(0.30, 0.24, 0.17)])   # Vordersprosse
			parts.append([base + up * 0.15, Vector3(0.05 * s, 0.4, -1.0).normalized(), 0.045, 0.005, 0.002, Color(0.30, 0.24, 0.17)])  # Hintersprosse
		for p in parts:
			var cm := CylinderMesh.new()
			cm.top_radius = p[4]
			cm.bottom_radius = p[3]
			cm.height = p[2]
			cm.radial_segments = 6
			cm.rings = 1
			var dirv: Vector3 = p[1]
			var b := Basis()
			var ax := Vector3.UP.cross(dirv)
			if ax.length() > 1e-4:
				b = Basis(ax.normalized(), Vector3.UP.angle_to(dirv))
			var tf := Transform3D(b, (p[0] as Vector3) + dirv * float(p[2]) * 0.5)
			var mt := StandardMaterial3D.new()
			mt.albedo_color = p[5]
			stt.set_color(p[5])
			var arr := cm.get_mesh_arrays()
			var cols := PackedColorArray()
			cols.resize((arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size())
			cols.fill(p[5])
			arr[Mesh.ARRAY_COLOR] = cols
			var tmp := ArrayMesh.new()
			tmp.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
			stt.append_from(tmp, 0, tf)
		_geweih_mesh = stt.commit()
	var ba := BoneAttachment3D.new()
	ba.bone_name = "Head"
	sk.add_child(ba)
	var inv := sk.get_bone_global_rest(hi).affine_inverse()
	var top: Array = meta.get("kopf_oben", [0.0, 4.0, 2.0])
	var g := MeshInstance3D.new()
	g.mesh = _geweih_mesh
	var gm := StandardMaterial3D.new()
	gm.vertex_color_use_as_albedo = true
	gm.roughness = 0.9
	g.material_override = gm
	g.layers = 1
	# in model units: the mesh is in metres
	g.transform = inv * Transform3D(Basis().scaled(Vector3.ONE / einheit), Vector3(float(top[0]), float(top[1]) - 0.01 / einheit, float(top[2])))
	ba.add_child(g)
	if not t.is_empty() and a.main != null:
		var gt := MeshInstance3D.new()
		gt.mesh = _geweih_mesh
		gt.material_override = a.main.tmat_fixed(float(t["kuehl"]))
		gt.layers = 2
		gt.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		gt.transform = g.transform
		ba.add_child(gt)


func _play(n: String, blend := 0.3, spd := 1.0) -> void:
	if not ap.has_animation(n):
		return
	if n != _cur:
		ap.play(n, blend)
		_cur = n
	ap.speed_scale = spd


func _process(dt: float) -> void:
	if a == null or not is_instance_valid(a):
		return
	var spd: float = float(a.cur_speed)
	var st := ""
	var curl := 0.0
	if a.main != null and a.main.get("tiere") != null:
		var s = a.main.tiere._st.get(a.get_instance_id(), null)
		if typeof(s) == TYPE_DICTIONARY:
			st = str(s.get("st", ""))
			curl = float(s.get("k", 0.0)) if kind == "hedgehog" else 0.0
	var leap: bool = kind == "deer" and bool(a.fled) and spd > 2.0
	if st == "pounce":
		_play("Gallop_Jump", 0.15)
	elif curl > 0.5:
		_play("Idle_2_HeadLow", 0.3, 0.3)
	elif spd > _stp[1] * 0.8 or (bool(a.fled) and spd > 1.0 * _stp[0] / SCHRITT[0]):
		_play("Gallop", 0.25, clampf(spd / float(_stp[1]), 0.6, 2.2))
	elif spd > 0.04:
		var sneak: bool = kind == "cat" and spd < 0.9
		_play("Walk", 0.3, clampf(spd / float(_stp[0]) * (1.25 if sneak else 1.0), 0.35, 2.6))
	else:
		var idle: String = str(a.idle_kind) if a.now_s() < float(a.idle_until) else ""
		match idle:
			"sniff", "halt", "lie":
				_play("Idle_2_HeadLow", 0.4)
			"graze", "root", "dig":
				_play("Eating", 0.4)
			"look", "sit_up":
				_play("Idle", 0.4)
			_:
				_play("Idle_2", 0.5)
	# the basic shapes move body_root up / down (paws on the ground, lying, sitting): the model has its own legs - only
	# the leap of the deer stays; a stalking cat goes low (shorter legs: the body a little squashed)
	var br: Node3D = a.body_root
	var sy: float = maxf(0.01, br.scale.y)
	if not leap:
		holder.position.y = -br.position.y / sy
		holder.rotation.x = -br.rotation.x
	else:
		holder.position.y = 0.0
		holder.rotation.x = 0.0
	var low: float = 0.86 if kind == "cat" and spd > 0.04 and spd < 0.9 else 1.0
	holder.scale = Vector3(einheit, einheit * lerpf(holder.scale.y / einheit, low, clampf(dt * 4.0, 0.0, 1.0)), einheit)
	# LOD: far away the pose is computed less often
	_lod_t -= dt
	if _lod_t <= 0.0:
		_lod_t = 0.5
		var d := 0.0
		if a.main != null and a.main.get("head") != null:
			d = (a.main.head.global_position as Vector3).distance_to(a.global_position)
			var vc = a.main.get("view_cam")
			if vc != null and (vc as Camera3D).current:
				d = minf(d, (vc as Camera3D).global_position.distance_to(a.global_position))
		_lod_n = 1 if d < 30.0 else (3 if d < 70.0 else 6)
	_acc += dt
	_frame += 1
	if _frame % _lod_n == 0:
		ap.advance(_acc)
		_acc = 0.0
		if kind == "hedgehog":
			_igel_einrollen(curl)
	_box_t -= dt
	if _box_t <= 0.0:
		_box_t = 0.2
		_update_box()


func _igel_einrollen(k: float) -> void:
	"""0 = läuft … 1 = Stachelkugel: Kopf, Beine und Schwanz unter die Stacheln (Knochen klein)"""
	var s := Vector3.ONE * maxf(0.05, 1.0 - 0.95 * k)
	for bi in _igel_bones:
		sk.set_bone_pose_scale(bi, s)


func _update_box() -> void:
	"""«pose_aabb» (dataset.gd, vielfalt.gd): the box of the pose from the bones (space of the mesh), with a margin for fur,
	ears, snout and tail tip"""
	if sk == null:
		return
	var lo := Vector3(INF, INF, INF)
	var hi := -lo
	var to_mi := mi.transform.affine_inverse() if mi.get_parent() == sk else Transform3D()
	for i in range(sk.get_bone_count()):
		var n := sk.get_bone_name(i)
		if n.begins_with("IK") or n.begins_with("Pole") or n.begins_with("FF"):
			continue
		if not _igel_bones.is_empty() and i in _igel_bones and sk.get_bone_pose_scale(i).x < 0.5:
			continue
		var p: Vector3 = to_mi * sk.get_bone_global_pose(i).origin
		lo = lo.min(p)
		hi = hi.max(p)
	if lo.x == INF:
		return
	var m := 0.065 / einheit                                 # ≈ 6.5 cm for fur, ears, snout, tail tip
	if kind == "hedgehog":
		m = 0.05 / einheit
	var box := AABB(lo - Vector3(m, m, m), hi - lo + Vector3(2 * m, 2 * m, 2 * m))
	box = box.merge(AABB(Vector3(box.position.x, minf(box.position.y, 0.0), box.position.z), Vector3(box.size.x, 0.01, box.size.z)))   # down to the paws
	mi.set_meta("pose_aabb", box)
