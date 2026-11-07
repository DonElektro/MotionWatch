extends Node
## Gehäuse v5.1 am Gerät (Paket «real-gehaeuse», 01.11.2026): statt des dunklen Kastens zeigt der Simulator die
## vereinfachten echten Druckteile aus hardware/gehaeuse/ (Modell des Besitzers: v5.py / pantilt.py, vereinfacht mit decimate.py
## von werkzeuge/gehaeuse_bauen.py): res://inhalte/gehaeuse/gehaeuse.glb (Lite: gehaeuse_lite.glb, gröber, nur die äusseren
## Teile) + modelle.json (Gruppe, Farbe, Explosion, Prüfsumme der Quelle).
##   base  Unterteil, Deckel, Füsse, Buchsen – dreht nicht (eigener Knoten im rig auf der Höhe von main.head)
##   pan   Drehteller, Gabel, Arm 2, Lampen – hängen an main.head (Pan)
##   tilt  Kamerakopf, Seitendeckel, Kameras – hängen an main.head_pitch (Tilt)
## Ursprung der Modelle = Kippachse auf der Pan-Achse = main.head / main.head_pitch: die Kameras (cams[0], Wärmebild) und
## die Erkennung bleiben genau wo sie waren – nur das Bild des Geräts ändert sich. Der alte Kasten (main.head_box) bleibt im
## Code und erscheint wieder, wenn «Echtes Gehäuse» aus ist (Werkstatt, /control {"action": "werkstatt", "do": "real_case"}).
## Der Mast endet unter den Füssen; die Status-LED sitzt auf dem echten Kopfdach (Lage aus Gehäuse v5.2).
## Variante v5.2 (real-gehaeuse-v52, 01.11.2026): ist die Weitwinkel-Kamera «Im Gehäuse (v5.2)» oder «Unterteil vorne»
## montiert, zeigt die Szene das echte Unterteil v5.2 (Fenster, IR-Modul, Linse – modelle.json «variante» 5.2) statt v5.1;
## die Teile mit «ersetzt» blenden ihr Teil von v5.1 aus.
## real-abgleich-v52 (Wunsch des Besitzers 01.11.2026): v5.2 bleibt v5.2 – die Szene zeigt immer das Unterteil v5.2. Ist die
## Weitwinkel-Kamera am Kopf, am Mast (Szene) oder gar nicht montiert, sitzt der Blindstopfen 12 im Fenster (modelle.json
## «ohne»: "wide") und der Stopfen 19 im IR-Modul-Loch («ohne»: "irled"); Weitwinkel-Linse und IR-Modul sind dann nicht zu sehen. Farben aus bau.json «farben» (modelle.json):
## Kopfteil orange, Unterteil, Deckel, Zwischenboden, Füsse und Stopfen grau («grau», «grau_teile»).
## real-gehaeuse-v53 (02.11.2026): ist in «Bauen» das Gehäuse v5.3 gewählt (user://bau_mein.json), zeigt die Szene die Teile mit
## «variante» 5.3 (Unterteil, Deckel, Füsse in den Ecken, Akkuklappe) und blendet die ersetzten Teile aus; sonst bleibt es v5.2.
## sim-echte-kamera (Idee 4, 07.11.2026): die Linse des Weisslichts leuchtet, wenn es an ist; die IR-Lampe und das IR-Modul im
## Unterteil glimmen schwach dunkelrot (850 nm, fürs Auge kaum sichtbar). Sichtweiten: Normal = feine Teile bis LOD_M (ohne
## eigenen Schatten), dahinter die groben; den Schatten werfen immer die groben (nur Schatten); ab FAR_M nichts. Lite = nur grob.
## Weitwinkel «Kopf vorne / hinten»: ein kleines Modul auf dem Kopfdach (weitwinkel.gd setzt die Kamera dorthin, solange das
## echte Gehäuse zu sehen ist). Gerät 2 (device.gd) bekommt dasselbe Gehäuse (grob) über build_copy().

const Quality := preload("res://scripts/quality.gd")
const DIR := "res://inhalte/gehaeuse/"
const FILE := "user://gehaeuse.json"
const PETG := Color("#9a9ea3")                 # PETG-Grau (bau.json «farben.grau») – nur falls modelle.json «farben.grau» fehlt
const GRAU_ALT := ["tub", "tub52", "lid", "plug", "feet"]   # graue Teile, falls modelle.json «farben.grau_teile» fehlt
const MIT_WEIT := ["wide", "irled"]            # nur sichtbar, wenn die Weitwinkel-Kamera im Gehäuse sitzt
const LED_POS := Vector3(-0.008, 0.0305, -0.003)   # v5.2: Status-LED auf dem Kopfdach (Kipp-Koordinaten x 3, y 8, Dach z 29 mm)
const LED_SCALE := 0.2                         # Diffusor Ø 14 mm statt des grossen Auges auf dem Kasten
# sim-echte-kamera (Idee 4, 07.11.2026): Sichtweiten und Leuchten
const LOD_M := 6.0                             # Normal: die feinen Teile bis 6 m, dahinter die groben (gehaeuse_lite.glb)
const FAR_M := 150.0                           # weiter weg ist das Gerät kleiner als ein Bildpunkt: nicht zeichnen
# leuchtende Teile: [Grundfarbe aus, Farbe des Leuchtens]
const GLOW := {"lens_w": [Color("#e9e4c8"), Color(1.0, 0.95, 0.82)], "lens_ir": [Color("#3a1010"), Color(0.6, 0.03, 0.02)],
		"irled": [Color("#3a1010"), Color(0.6, 0.03, 0.02)]}
const GLOW_WHITE := 8.0                        # Weisslicht nachts (die Linse ist das Hellste im Bild)
const GLOW_WHITE_DAY := 2.5                    # am Tag
const GLOW_IR := 0.35                          # 850 nm: das Auge sieht nur ein schwaches dunkelrotes Glimmen
# Weitwinkel-Modul (Camera Module 3 Wide, 25 × 24 mm) auf dem Kopfdach, wenn es «Kopf vorne / hinten» montiert ist
const WMOD_FRONT := Vector3(0.0, 0.0445, -0.030)
const WMOD_REAR := Vector3(0.0, 0.0445, 0.016)

var main
var on := true                                 # gespeichert (user://gehaeuse.json)
var ok := false                                # Modelle geladen
var why := ""                                  # warum nicht (Diagnose)
var man := {}
var lite := false
var tris := 0
var _base: Node3D
var _nodes: Array = []                         # [Node3D-Gruppenknoten] base / pan / tilt
var _led_keep = null                           # [position, scale] der Status-LED vorher
var v52 := true                                # zeigt die Szene v5.2? (immer, real-abgleich-v52)
var weit := false                              # Weitwinkel-Kamera im Gehäuse (sonst Blindstopfen 12 im Fenster)
var v53 := false                               # zeigt die Szene v5.3? (Wahl «Gehäuse» in Bauen / Werkstatt, sonst v5.2)
var lists := {}                                # sim-echte-kamera: die Teile nach Rolle (place_parts), alle Sätze (fein, grob, Schatten)
var mats := {}
var lod := false                               # Normal: feine Teile in der Nähe, grobe dahinter (LOD_M)
var tris_lod := 0
var glow_on := {"white": false, "ir": false, "ir_wide": false}
var wmod: Node3D                               # sim-echte-kamera: Weitwinkel-Modul am Kopf (Halterung «Kopf vorne / hinten»)


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY and d.has("on"):
		on = bool(d["on"])
	call_deferred("build")


static func manifest() -> Dictionary:
	var p := DIR + "modelle.json"
	if not FileAccess.file_exists(p):
		return {}
	var d = JSON.parse_string(FileAccess.get_file_as_string(p))
	return d if typeof(d) == TYPE_DICTIONARY else {}


static func load_parts(file: String) -> Dictionary:
	"""GLB zur Laufzeit lesen (GLTFDocument, ohne Import): {Teil-id: MeshInstance3D} (noch ohne Eltern)"""
	var out := {}
	var path := DIR + file
	if not FileAccess.file_exists(path):
		return out
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_file(path, st) != OK:
		return out
	var root: Node = doc.generate_scene(st)
	if root == null:
		return out
	var stack: Array = [root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		for c in n.get_children():
			stack.append(c)
		if n is MeshInstance3D:
			var mi := n as MeshInstance3D
			var key := str(mi.name)
			if mi.get_parent() != null and mi.mesh == null:
				continue
			out[key] = mi
	for k in out:
		var mi: MeshInstance3D = out[k]
		var t := mi.global_transform if mi.is_inside_tree() else mi.transform
		mi.get_parent().remove_child(mi)
		mi.transform = t
	root.free()
	return out


func build() -> void:
	if main == null or main.head == null or main.head_pitch == null:
		why = "no_head"
		return
	man = manifest()
	if man.is_empty():
		why = "no_manifest"
		return
	lite = Quality.lite()
	var ms := load_parts("gehaeuse_lite.glb" if lite else "gehaeuse.glb")
	if ms.is_empty():
		why = "glb_unreadable"
		return
	_base = Node3D.new()
	_base.name = "GehaeuseUnterteil"
	main.rig.add_child(_base)
	var pan := Node3D.new()
	pan.name = "GehaeusePan"
	main.head.add_child(pan)
	var tilt := Node3D.new()
	tilt.name = "GehaeuseTilt"
	main.head_pitch.add_child(tilt)
	_nodes = [_base, pan, tilt]
	mats = materials(man)
	# sim-echte-kamera: Lite = nur die groben Teile (mit Schatten); Normal = die feinen Teile bis LOD_M (ohne eigene Schatten),
	# dahinter die groben, und die groben werfen auch in der Nähe den Schatten (nur Schatten) – der Schatten-Durchgang zeichnet
	# so nie die 140'000 Dreiecke der feinen Teile.
	var L: Dictionary
	if lite:
		L = place_parts(man, ms, _base, pan, tilt, mats, true, 0.0, FAR_M, GeometryInstance3D.SHADOW_CASTING_SETTING_ON)
	else:
		L = place_parts(man, ms, _base, pan, tilt, mats, false, 0.0, LOD_M, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
		var ml := load_parts("gehaeuse_lite.glb")
		if not ml.is_empty():
			var far := place_parts(man, ml, _base, pan, tilt, mats, true, LOD_M, FAR_M, GeometryInstance3D.SHADOW_CASTING_SETTING_ON)
			var sh := place_parts(man, ml, _base, pan, tilt, mats, true, 0.0, LOD_M, GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY, true)
			lod = true
			for k in far:
				if far[k] is Array:
					(L[k] as Array).append_array(far[k])
					(L[k] as Array).append_array(sh[k])
			tris_lod = int(far["tris"])
		else:
			for mi in L["alle"]:                         # no lite parts: the fine parts cast the shadow themselves
				(mi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	lists = L
	tris = int(L["tris"])
	ok = true
	apply()


static func materials(m: Dictionary) -> Dictionary:
	"""die Materialien des Geräts: PETG-Grau, Kopf-Orange (bau.json «farben» über modelle.json) und die leuchtenden Teile
	(sim-echte-kamera): Linse Weisslicht, Linse IR-Lampe, IR-Modul im Unterteil – je ein eigenes Material, das leuchtet"""
	var fb: Dictionary = m.get("farben", {})                 # Wunsch des Besitzers 01.11.2026: Kopfteil in MoveEye-Orange, Rest grau
	var petg := StandardMaterial3D.new()
	petg.albedo_color = Color.from_string(str(fb.get("grau", "")), PETG) if str(fb.get("grau", "")) != "" else PETG
	petg.roughness = 0.55
	petg.cull_mode = BaseMaterial3D.CULL_DISABLED
	var orange := StandardMaterial3D.new()
	orange.albedo_color = Color.from_string(str(fb.get("kopf", "#f59a4a")), Color("#f59a4a"))
	orange.roughness = 0.55
	orange.cull_mode = BaseMaterial3D.CULL_DISABLED
	var glow := {}
	for id in GLOW:
		var g: Array = GLOW[id]
		var gm := StandardMaterial3D.new()
		gm.albedo_color = g[0]
		gm.roughness = 0.25
		gm.emission_enabled = true
		gm.emission = g[1]
		gm.emission_energy_multiplier = 0.0
		glow[id] = gm
	return {"petg": petg, "orange": orange, "glow": glow, "kopf": fb.get("kopf_teile", []), "grau": fb.get("grau_teile", GRAU_ALT)}


static func place_parts(m: Dictionary, ms: Dictionary, base: Node3D, pan: Node3D, tilt: Node3D, mt: Dictionary, coarse: bool,
		r0: float, r1: float, shadow: int, copy := false) -> Dictionary:
	"""die äusseren Teile aus ms an base / pan / tilt hängen (Farben, Sichtweite r0..r1 m, Schatten); copy = die Meshes
	stammen aus einem anderen Satz, der schon hängt (nur neue Knoten, gleiche Meshes). Antwort: die Listen für show_variant()"""
	var L := {"alle": [], "mit_weit": [], "ohne_weit": [], "v53": [], "v52": [], "v51": [], "ers53": [], "glow": {}, "tris": 0}
	var repl := {}                                 # ersetztes Teil -> Variante des ersetzenden Teils ("5.2" / "5.3")
	for e in m.get("teile", []):
		if str(e.get("ersetzt", "")) != "":
			repl[str(e["ersetzt"])] = str(e.get("variante", "5.2"))
	var kopf: Array = mt.get("kopf", [])
	var grau: Array = mt.get("grau", GRAU_ALT)
	var glow: Dictionary = mt.get("glow", {})
	for e in m.get("teile", []):
		var id := str(e.get("id", ""))
		if not bool(e.get("aussen", false)) or not ms.has(id):
			continue
		var mi: MeshInstance3D = ms[id]
		if copy:
			var c := MeshInstance3D.new()
			c.mesh = mi.mesh
			c.transform = mi.transform
			mi = c
		mi.name = ("geh_" + id) + ("_lod" if coarse and r0 > 0.0 else ("_schatten" if copy else ""))
		mi.layers = 1
		if glow.has(id):
			mi.material_override = glow[id]
			if not copy:
				L["glow"][id] = glow[id]
		elif id in kopf:
			mi.material_override = mt["orange"]
		elif id in grau:
			mi.material_override = mt["petg"]
		mi.cast_shadow = shadow
		mi.visibility_range_begin = r0
		mi.visibility_range_end = r1
		var grp := str(e.get("gruppe", "base"))
		var par: Node3D = pan if grp == "pan" else (tilt if grp == "tilt" else base)
		par.add_child(mi)
		L["alle"].append(mi)
		if id in MIT_WEIT:
			L["mit_weit"].append(mi)
		elif str(e.get("ohne", "")) in MIT_WEIT:     # 12 Blindstopfen (ohne Weitwinkel), 19 Stopfen (ohne IR-Modul)
			L["ohne_weit"].append(mi)
		elif str(e.get("variante", "")) == "5.3":
			L["v53"].append(mi)
		elif str(e.get("variante", "")) == "5.2":
			L["v52"].append(mi)
		elif repl.has(id) and repl[id] != "5.3":
			L["v51"].append(mi)
		if repl.get(id, "") == "5.3":
			L["ers53"].append(mi)
		L["tris"] = int(L["tris"]) + int(e.get("dreiecke_lite" if coarse else "dreiecke", 0))
	if not copy:
		for k in ms:                                    # what was not used
			if (ms[k] as MeshInstance3D).get_parent() == null:
				(ms[k] as MeshInstance3D).free()
	return L


static func show_variant(L: Dictionary, with_wide: bool, show52: bool, show53: bool) -> void:
	"""welche Teile zu sehen sind: Weitwinkel-Linse + IR-Modul oder Stopfen, v5.1 / v5.2 / v5.3"""
	for mi in L.get("mit_weit", []):
		if is_instance_valid(mi):
			(mi as Node3D).visible = with_wide
	for mi in L.get("ohne_weit", []):
		if is_instance_valid(mi):
			(mi as Node3D).visible = not with_wide
	for mi in L.get("v52", []):
		if is_instance_valid(mi):
			(mi as Node3D).visible = show52
	for mi in L.get("v51", []):
		if is_instance_valid(mi):
			(mi as Node3D).visible = not show52
	for mi in L.get("v53", []):
		if is_instance_valid(mi):
			(mi as Node3D).visible = show53
	for mi in L.get("ers53", []):
		if is_instance_valid(mi) and show53:
			(mi as Node3D).visible = false


static func set_glow(L: Dictionary, white: bool, ir: bool, ir_wide: bool, dark: bool) -> void:
	"""sim-echte-kamera: Weisslicht = die Linse leuchtet hell; IR (850 nm) = fürs Auge nur ein schwaches dunkelrotes Glimmen"""
	var g: Dictionary = L.get("glow", {})
	var want := {"lens_w": (GLOW_WHITE if dark else GLOW_WHITE_DAY) if white else 0.0,
			"lens_ir": GLOW_IR if ir else 0.0, "irled": GLOW_IR if ir_wide else 0.0}
	for id in g:
		var gm: StandardMaterial3D = g[id]
		var e := float(want.get(id, 0.0))
		if gm.emission_energy_multiplier != e:
			gm.emission_energy_multiplier = e


static func build_copy(rig: Node3D, head: Node3D, pitch: Node3D) -> Dictionary:
	"""sim-echte-kamera: das echte Gehäuse (grobe Teile) an einem weiteren Gerät (device.gd, Gerät 2): {ok, base, nodes, lists, tris}"""
	var m := manifest()
	if m.is_empty():
		return {"ok": false, "why": "no_manifest"}
	var ms := load_parts("gehaeuse_lite.glb")
	if ms.is_empty():
		return {"ok": false, "why": "glb_unreadable"}
	var b := Node3D.new()
	b.name = "GehaeuseUnterteil"
	rig.add_child(b)
	var pan := Node3D.new()
	pan.name = "GehaeusePan"
	head.add_child(pan)
	var tilt := Node3D.new()
	tilt.name = "GehaeuseTilt"
	pitch.add_child(tilt)
	var L := place_parts(m, ms, b, pan, tilt, materials(m), true, 0.0, FAR_M, GeometryInstance3D.SHADOW_CASTING_SETTING_ON)
	show_variant(L, false, true, gewaehlt_v53())       # Gerät 2: ohne Weitwinkel im Gehäuse (Blindstopfen 12)
	return {"ok": true, "base": b, "nodes": [b, pan, tilt], "lists": L, "tris": int(L["tris"]),
			"drop": float(m.get("kippachse_ueber_boden_m", 0.1258)) + float(m.get("fuesse_m", 0.006))}


func set_on(v: bool) -> void:
	on = v
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"on": on}))
	apply()


func drop() -> float:
	"""Kippachse über der Unterseite der Füsse (m) – so weit unter main.head endet der Mast"""
	return float(man.get("kippachse_ueber_boden_m", 0.1258)) + float(man.get("fuesse_m", 0.006))


static func wide_in_case(m) -> bool:
	"""zeigt die Szene das Unterteil v5.2? – Weitwinkel «Im Gehäuse (v5.2)» oder «Unterteil vorne» (weitwinkel.gd)"""
	var w = m.get("weit") if m != null else null
	return w != null and str(w.get("mount")) in ["case", "base"]


static func gewaehlt_v53() -> bool:
	"""real-gehaeuse-v53: zeigt die Szene v5.3? Die Wahl in «Bauen» (Werkstatt, user://bau_mein.json), sonst der Standard aus bau.json."""
	var p := "user://bau_mein.json"
	var d = JSON.parse_string(FileAccess.get_file_as_string(p)) if FileAccess.file_exists(p) else null
	if d is Dictionary and d.get("var") is Dictionary and str((d["var"] as Dictionary).get("gehaeuse", "")) != "":
		return str((d["var"] as Dictionary)["gehaeuse"]) == "v53"     # die eigene Wahl bleibt
	var std: Dictionary = (load("res://scripts/werkstatt_daten.gd").BAU as Dictionary).get("variante_standard", {})
	return str(std.get("gehaeuse", "")) == "v53"                       # Standard (bau.json, ab 02.11.2026 v5.3)


func apply() -> void:
	var real := on and ok
	for n in _nodes:
		if is_instance_valid(n):
			(n as Node3D).visible = real
	v52 = true                                      # real-abgleich-v52: v5.2 bleibt v5.2
	weit = wide_in_case(main)
	v53 = gewaehlt_v53()
	show_variant(lists, weit, v52, v53)
	if main.get("head_box") != null:
		main.head_box.visible = not real
	if wmod != null and not real:
		wmod.visible = false
	if not real:
		main.set_mast(main.mast_h)
	var sl = main.get("statusled")
	if sl != null and sl.get("_rig") != null and is_instance_valid(sl._rig):
		var rg: Node3D = sl._rig
		if real:
			if _led_keep == null:
				_led_keep = [rg.position, rg.scale]
			rg.position = LED_POS
			rg.scale = Vector3.ONE * LED_SCALE
		elif _led_keep != null:
			rg.position = _led_keep[0]
			rg.scale = _led_keep[1]
			_led_keep = null


func _process(_dt: float) -> void:
	if not (on and ok) or main.head == null:
		return
	if is_instance_valid(_base):
		_base.position = main.head.position             # the lower part does not pan: in the rig, at the height of the head
	var pole: MeshInstance3D = main.mast_pole
	if pole != null:
		var L := maxf(0.01, main.mast_h - drop())
		pole.scale = Vector3(1, L, 1)
		pole.position = Vector3(0, -drop() - L / 2.0, 0)
	var sl = main.get("statusled")
	if _led_keep == null and sl != null and sl.get("_rig") != null and is_instance_valid(sl._rig):
		apply()                                       # the LED is built later than the case
	elif wide_in_case(main) != weit:
		apply()                                       # v5.2: the mount of the wide camera changed (lens or plug 12)
	_glow_tick()
	_wmod_tick()


func _glow_tick() -> void:
	"""sim-echte-kamera: die Lampen am Kopf leuchten, wenn sie an sind (Weisslicht: das echte Licht der Szene; IR: ir_on())"""
	var w: bool = main.white_light != null and main.white_light.light_energy > 0.0
	var ir: bool = main.ir_on()
	var iw: bool = main.weit != null and main.weit.has_method("ir_wide_on") and main.weit.ir_wide_on() and weit
	glow_on = {"white": w, "ir": ir, "ir_wide": iw}
	set_glow(lists, w, ir, iw, main.is_dark())


static func head_mount_pos(rear: bool) -> Vector3:
	return WMOD_REAR if rear else WMOD_FRONT


func _wmod_tick() -> void:
	"""das Weitwinkel-Modul am Kopf: dort, wo cams[1] ist (weitwinkel.gd), nur bei «Kopf vorne / hinten»"""
	var wt = main.weit
	var want: bool = wt != null and wt.has_method("on_head") and wt.on_head()
	if not want:
		if wmod != null:
			wmod.visible = false
		return
	if wmod == null:
		wmod = Node3D.new()
		wmod.name = "WeitwinkelModul"
		wmod.top_level = true
		add_child(wmod)
		var pcb := MeshInstance3D.new()
		pcb.mesh = BoxMesh.new()
		(pcb.mesh as BoxMesh).size = Vector3(0.025, 0.024, 0.004)
		pcb.position = Vector3(0, 0, 0.009)
		var pm := StandardMaterial3D.new()
		pm.albedo_color = Color("#b33333")            # wie «wide» in modelle.json
		pcb.material_override = pm
		pcb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		wmod.add_child(pcb)
		var hold := MeshInstance3D.new()              # Halterung (Kopf-Orange)
		hold.mesh = BoxMesh.new()
		(hold.mesh as BoxMesh).size = Vector3(0.029, 0.028, 0.008)
		hold.position = Vector3(0, 0, 0.015)
		hold.material_override = mats.get("orange", main.mat(Color("#f59a4a")))
		hold.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		wmod.add_child(hold)
		var lens := MeshInstance3D.new()
		var cy := CylinderMesh.new()
		cy.top_radius = 0.0045
		cy.bottom_radius = 0.0055
		cy.height = 0.007
		cy.radial_segments = 12
		cy.rings = 1
		lens.mesh = cy
		lens.rotation.x = PI / 2.0
		lens.position = Vector3(0, 0, 0.004)
		lens.material_override = main.mat(Color(0.05, 0.05, 0.06))
		lens.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		wmod.add_child(lens)
		for c in wmod.get_children():
			(c as GeometryInstance3D).visibility_range_end = 40.0
	wmod.visible = on and ok
	wmod.global_transform = main.cams[1].global_transform


func info() -> Dictionary:
	var hp: Vector3 = main.head.global_position if main.head != null and main.head.is_inside_tree() else Vector3.ZERO
	return {"on": on, "ok": ok, "why": why, "lite": lite, "tris": tris, "version": str(man.get("version", "")), "v52": v52, "v53": v53, "weit": weit,
			"lod": lod, "tris_lod": tris_lod, "glow": glow_on, "wmod": wmod != null and wmod.visible,
			"head_pos": [snappedf(hp.x, 0.001), snappedf(hp.y, 0.001), snappedf(hp.z, 0.001)],
			"quelle_sha256": str(man.get("quelle_sha256", "")).substr(0, 12)}
