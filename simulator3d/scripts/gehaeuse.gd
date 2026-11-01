extends Node
## Gehäuse v5.1 am Gerät (Paket «real-gehaeuse», 01.11.2026): statt des dunklen Kastens zeigt der Simulator die
## vereinfachten echten Druckteile aus hardware/gehaeuse/ (Daniels Modell v5.py / pantilt.py, vereinfacht mit decimate.py
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
## real-abgleich-v52 (Wunsch Daniel 01.11.2026): v5.2 bleibt v5.2 – die Szene zeigt immer das Unterteil v5.2. Ist die
## Weitwinkel-Kamera am Kopf, am Mast (Szene) oder gar nicht montiert, sitzt der Blindstopfen 12 im Fenster (modelle.json
## «ohne»: "wide"), Weitwinkel-Linse und IR-Modul sind dann nicht zu sehen. Farben aus bau.json «farben» (modelle.json):
## Kopfteil orange, Unterteil, Deckel, Zwischenboden, Füsse und Stopfen grau («grau», «grau_teile»).

const Quality := preload("res://scripts/quality.gd")
const DIR := "res://inhalte/gehaeuse/"
const FILE := "user://gehaeuse.json"
const PETG := Color("#6d7074")                 # eSun PETG Grau (Bestellliste) – nur falls modelle.json «farben.grau» fehlt
const GRAU_ALT := ["tub", "tub52", "lid", "plug", "feet"]   # graue Teile, falls modelle.json «farben.grau_teile» fehlt
const MIT_WEIT := ["wide", "irled"]            # nur sichtbar, wenn die Weitwinkel-Kamera im Gehäuse sitzt
const LED_POS := Vector3(-0.008, 0.0305, -0.003)   # v5.2: Status-LED auf dem Kopfdach (Kipp-Koordinaten x 3, y 8, Dach z 29 mm)
const LED_SCALE := 0.2                         # Diffusor Ø 14 mm statt des grossen Auges auf dem Kasten

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
var _v52: Array = []                           # Teile der Variante v5.2 (nur sichtbar, wenn v5.2 gewählt ist)
var _v51: Array = []                           # Teile von v5.1, die v5.2 ersetzt
var v52 := true                                # zeigt die Szene v5.2? (immer, real-abgleich-v52)
var weit := false                              # Weitwinkel-Kamera im Gehäuse (sonst Blindstopfen 12 im Fenster)
var _mit_weit: Array = []                      # Linse + IR-Modul
var _ohne_weit: Array = []                     # Blindstopfen 12


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
	var fb: Dictionary = man.get("farben", {})                 # Wunsch Daniel 01.11.2026: Kopfteil in MoveEye-Orange, Rest grau
	var petg := StandardMaterial3D.new()
	petg.albedo_color = Color.from_string(str(fb.get("grau", "")), PETG) if str(fb.get("grau", "")) != "" else PETG
	petg.roughness = 0.55
	petg.cull_mode = BaseMaterial3D.CULL_DISABLED
	var kopf: Array = fb.get("kopf_teile", [])
	var grau: Array = fb.get("grau_teile", GRAU_ALT)
	var orange := StandardMaterial3D.new()
	orange.albedo_color = Color.from_string(str(fb.get("kopf", "#f59a4a")), Color("#f59a4a"))
	orange.roughness = 0.55
	orange.cull_mode = BaseMaterial3D.CULL_DISABLED
	tris = 0
	_v52 = []
	_v51 = []
	_mit_weit = []
	_ohne_weit = []
	var repl := {}
	for e in man.get("teile", []):
		if str(e.get("ersetzt", "")) != "":
			repl[str(e["ersetzt"])] = true
	for e in man.get("teile", []):
		var id := str(e.get("id", ""))
		if not bool(e.get("aussen", false)) or not ms.has(id):
			continue
		var mi: MeshInstance3D = ms[id]
		mi.name = "geh_" + id
		mi.layers = 1
		if id in kopf:
			mi.material_override = orange
		elif id in grau:
			mi.material_override = petg
		var grp := str(e.get("gruppe", "base"))
		var par: Node3D = pan if grp == "pan" else (tilt if grp == "tilt" else _base)
		par.add_child(mi)
		if id in MIT_WEIT:
			_mit_weit.append(mi)
		elif str(e.get("ohne", "")) == "wide":
			_ohne_weit.append(mi)
		elif str(e.get("variante", "")) == "5.2":
			_v52.append(mi)
		elif repl.has(id):
			_v51.append(mi)
		tris += int(e.get("dreiecke_lite" if lite else "dreiecke", 0))
	for k in ms:                                    # what was not used
		if (ms[k] as MeshInstance3D).get_parent() == null:
			(ms[k] as MeshInstance3D).free()
	ok = true
	apply()


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


func apply() -> void:
	var real := on and ok
	for n in _nodes:
		if is_instance_valid(n):
			(n as Node3D).visible = real
	v52 = true                                      # real-abgleich-v52: v5.2 bleibt v5.2
	weit = wide_in_case(main)
	for mi in _mit_weit:
		if is_instance_valid(mi):
			(mi as Node3D).visible = weit
	for mi in _ohne_weit:
		if is_instance_valid(mi):
			(mi as Node3D).visible = not weit
	for mi in _v52:
		if is_instance_valid(mi):
			(mi as Node3D).visible = v52
	for mi in _v51:
		if is_instance_valid(mi):
			(mi as Node3D).visible = not v52
	if main.get("head_box") != null:
		main.head_box.visible = not real
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


func info() -> Dictionary:
	var hp: Vector3 = main.head.global_position if main.head != null and main.head.is_inside_tree() else Vector3.ZERO
	return {"on": on, "ok": ok, "why": why, "lite": lite, "tris": tris, "version": str(man.get("version", "")), "v52": v52, "weit": weit,
			"head_pos": [snappedf(hp.x, 0.001), snappedf(hp.y, 0.001), snappedf(hp.z, 0.001)],
			"quelle_sha256": str(man.get("quelle_sha256", "")).substr(0, 12)}
