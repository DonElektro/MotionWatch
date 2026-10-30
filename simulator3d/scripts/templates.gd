extends PanelContainer
## 3D-3.82: «Vorlagen» - every way to get a ready-made world into the simulator, in one window with four tabs:
##   Fertige Szenen  - all built-in scenes (one click)
##   Ganze Orte      - a real place: the map of Switzerland (swisstopo), or a whole area as a 3D file (Blender + Blosm, OSM)
##   Bausätze        - free 3D models (Kenney, Quaternius, Poly Pizza, Poly Haven, KayKit, Sketchfab ...) with link and licence
##   Eigene Datei    - load a .glb / .gltf (button or drag & drop into the window): kept in user://vorlagen/, shown in the
##                     scene «Meine Vorlage» (scenes.gd _vorlage). Size and middle are found by themselves; the meshes become
##                     obstacles (people and animals walk round them, the game's line of sight). Move / turn / size per file.

var main
var tabs: TabContainer
var _list: VBoxContainer           # tab 4: the loaded files
var _msg: Label
var _scene_box: GridContainer
var _search: LineEdit
var _fd: FileDialog
var placed: Array = []             # [{file, name, x, z, rot, scale, auto}]

const UI = preload("res://scripts/ui_style.gd")
const DIR := "user://vorlagen"
const MAX_OBST := 250

const NEW_SCENES := ["bauernhof", "seeufer", "baustelle", "stellplatz", "vorlage", "parcours"]
const SCENE_INFO := {
	"camping": "Zelt, Wohnwagen, Feuer – der Klassiker", "wald": "Dichter Wald, viele Wildtiere", "parkplatz": "Autos, Leute, Lieferwagen",
	"garten": "Haus mit Garten, Katzen und Igel", "lustig": "Bunter Platz zum Ausprobieren", "wild": "Hochsitz, Wildwechsel",
	"verstecken": "Viele Verstecke – fürs Spiel", "ort": "Ein echter Ort aus der Karte", "zuhause": "Selbst gebaut im Haus-Editor",
	"bauernhof": "Scheune, Heuballen, Weide mit Zaun", "seeufer": "Wasser, Steg mit Boot, Schilf, Zelt",
	"baustelle": "Bauzaun, Container, Bagger, Werkzeugkiste", "stellplatz": "Wohnmobile, Stromsäulen, Hecken",
	"vorlage": "Deine eigene 3D-Datei (Reiter «Eigene Datei»)", "parcours": "Wiese mit Distanzmarken, Busch, Zelt, Auto, Baum – Verfolgen üben"}

# [name, what, licence, link]
const KITS := [
	["Kenney", "Tausende einfache Modelle: Häuser, Autos, Möbel, Natur, Zäune. Ideal für den Simulator.", "CC0 – frei, auch für Verkauf", "https://kenney.nl/assets/category:3D"],
	["Quaternius", "Low-Poly-Pakete: Natur, Stadt, Bauernhof, Camping, Tiere und Figuren.", "CC0 – frei", "https://quaternius.com/"],
	["Poly Pizza", "Suche über viele Low-Poly-Modelle (u. a. Google Poly-Archiv), direkt als .glb.", "meist CC0 / CC-BY (steht beim Modell)", "https://poly.pizza/"],
	["KayKit", "Fertige Bausätze (Stadt, Wald, Abenteuer) in einheitlichem Stil.", "CC0 – frei", "https://kaylousberg.itch.io/"],
	["Poly Haven", "Fotorealistische Modelle, Oberflächen und Himmel (HDRI).", "CC0 – frei", "https://polyhaven.com/models"],
	["ambientCG", "Oberflächen (Holz, Kies, Rasen, Beton) für eigene Modelle in Blender.", "CC0 – frei", "https://ambientcg.com/"],
	["Sketchfab", "Riesige Auswahl, auch echte Gebäude und 3D-Scans. Filter «Downloadable», Format glTF wählen.", "je Modell verschieden – Lizenz prüfen!", "https://sketchfab.com/search?features=downloadable&type=models"],
	["OpenGameArt", "Gemeinschafts-Archiv, gemischte Qualität.", "verschieden (CC0, CC-BY, GPL)", "https://opengameart.org/art-search-advanced?field_art_type_tid%5B%5D=10"],
	["Smithsonian 3D", "3D-Scans aus Museen (Objekte, kein Gelände).", "viele CC0", "https://3d.si.edu/"],
]

# [name, what, link]
const PLACES := [
	["Karte der Schweiz (eingebaut)", "Ort anklicken – Gelände, Luftbild, Häuser von swisstopo / OpenStreetMap werden geladen.", ""],
	["Blender + Blosm (OpenStreetMap, weltweit)", "1. Blender installieren (gratis).  2. Erweiterung «Blosm» installieren.  3. Gebiet auf der Karte wählen → «Import».  4. «Datei → Export → glTF 2.0 (.glb)».  5. Die .glb hier in «Eigene Datei» ziehen.", "https://prochitecture.gumroad.com/l/blender-osm"],
	["Blender herunterladen", "Freies 3D-Programm, auch zum Verkleinern und Anpassen von Modellen.", "https://www.blender.org/download/"],
	["swissBUILDINGS3D (swisstopo)", "Alle Gebäude der Schweiz in 3D. Kachel herunterladen, in Blender öffnen, als .glb exportieren.", "https://www.swisstopo.admin.ch/de/landschaftsmodell-swissbuildings3d-3-0-beta"],
	["swissALTI3D / swissSURFACE3D", "Gelände und Oberfläche (Bäume, Dächer) als Höhenmodell – für eigene Gelände in Blender.", "https://www.swisstopo.admin.ch/de/hoehenmodell-swissalti3d"],
	["Google Earth-Gebäude (Blender «Maps Models Importer»)", "Fotorealistische Städte – nur für den eigenen Gebrauch (Nutzungsbedingungen von Google).", "https://github.com/eliemichel/MapsModelsImporter"],
]


func _ready() -> void:
	visible = false
	add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.97), UI.ACC, 14, 12, 1))
	custom_minimum_size = Vector2(620, 470)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	add_child(v)
	var hd := HBoxContainer.new()
	v.add_child(hd)
	var t := UI.heading("Vorlagen – fertige Welten und 3D-Modelle")
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(t)
	var x := Button.new()
	x.text = "✕"
	x.pressed.connect(func(): visible = false)
	hd.add_child(x)
	tabs = TabContainer.new()
	tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(tabs)
	_tab_scenes()
	_tab_places()
	_tab_kits()
	_tab_own()                      # 3D-4.x: «Dein Platz» (photo of the place) is now the first tab of the window «Dein Platz» (inventar.gd)
	_msg = UI.small("")
	_msg.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_msg.custom_minimum_size = Vector2(580, 0)
	v.add_child(_msg)
	DirAccess.make_dir_recursive_absolute(DIR)
	_load_placed()
	_paint_list()
	get_window().files_dropped.connect(_on_drop)


func toggle(tab := -1) -> void:
	visible = not visible if tab < 0 else true
	if tab >= 0:
		tabs.current_tab = tab
	if visible:
		get_parent().move_child(self, -1)
		_paint_scenes()


func _process(_dt: float) -> void:
	if visible:
		var vs := get_viewport_rect().size
		size = Vector2(minf(680, vs.x - 30), minf(560, vs.y - 60))
		position = ((vs - size) / 2.0).floor()


func _page(title: String, intro: String) -> VBoxContainer:
	var sc := ScrollContainer.new()
	sc.name = title
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	tabs.add_child(sc)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 8)
	sc.add_child(v)
	var l := UI.small(intro)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(560, 0)
	v.add_child(l)
	return v


func _entry(parent: Control, title: String, text: String, extra: String, btn: String, cb: Callable, mark := false) -> void:
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", UI.box(UI.PANEL2 if not mark else UI.PANEL2.lerp(UI.GRN, 0.12), UI.LINE, 10, 8))
	parent.add_child(pc)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 10)
	pc.add_child(h)
	var vv := VBoxContainer.new()
	vv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(vv)
	var a := Label.new()
	a.text = title
	a.add_theme_font_size_override("font_size", 15)
	vv.add_child(a)
	for s in [text, extra]:
		if s != "":
			var b := UI.small(s, UI.MUT if s == text else UI.GRN)
			b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			b.custom_minimum_size = Vector2(400, 0)
			vv.add_child(b)
	if btn != "":
		var bb := Button.new()
		bb.text = btn
		bb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		bb.pressed.connect(cb)
		h.add_child(bb)


# ---- tab 1: the scenes ------------------------------------------------------------------------------------------------
func _tab_scenes() -> void:
	var v := _page("Fertige Szenen", "Alle eingebauten Szenen. Klick = Szene laden (Besucher kommen von selbst). Grün = neu.")
	_search = UI.search_field("Szene suchen …")
	_search.text_changed.connect(func(_s): _paint_scenes())
	v.add_child(_search)
	_scene_box = GridContainer.new()
	_scene_box.columns = 2
	_scene_box.add_theme_constant_override("h_separation", 8)
	_scene_box.add_theme_constant_override("v_separation", 8)
	v.add_child(_scene_box)


func _paint_scenes() -> void:
	for c in _scene_box.get_children():
		c.queue_free()
	var q := _search.text.strip_edges().to_lower()
	for s in main.Scenes.LIST:
		var id: String = s[0]
		var info: String = SCENE_INFO.get(id, "")
		if q != "" and not (s[1].to_lower().contains(q) or info.to_lower().contains(q)):
			continue
		var b := Button.new()
		b.text = ("● " if id == main.scene else "") + s[1] + "\n" + info
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(285, 54)
		b.add_theme_font_size_override("font_size", 12)
		if id in NEW_SCENES:
			b.add_theme_color_override("font_color", Color(0.55, 0.95, 0.6))
		b.pressed.connect(func(): _open_scene(id))
		_scene_box.add_child(b)


func _open_scene(id: String) -> void:
	if id == "ort":
		visible = false
		main.open_map()
		return
	main.set_scene(id)
	_say("Szene «%s» geladen." % id)
	_paint_scenes()


# ---- tab 2: whole places ----------------------------------------------------------------------------------------------
func _tab_places() -> void:
	var v := _page("Ganze Orte", "Einen echten Ort nachbauen. In der Schweiz geht es direkt mit der Karte; weltweit über Blender (gratis) und OpenStreetMap – das Ergebnis als .glb hier laden.")
	for p in PLACES:
		var link: String = p[2]
		if link == "":
			_entry(v, p[0], p[1], "", "Karte öffnen", func(): visible = false; main.open_map(), true)
		else:
			_entry(v, p[0], p[1], "", "Seite öffnen", func(): OS.shell_open(link))


# ---- tab 3: kits ------------------------------------------------------------------------------------------------------
func _tab_kits() -> void:
	var v := _page("Bausätze", "Freie 3D-Modelle zum Herunterladen. Format .glb (oder .gltf) wählen, dann in «Eigene Datei» laden oder ins Fenster ziehen. CC0 = ohne Bedingungen; CC-BY = Urheber nennen.")
	for k in KITS:
		var link: String = k[3]
		_entry(v, k[0], k[1], "Lizenz: " + k[2], "Seite öffnen", func(): OS.shell_open(link))


# ---- tab 4: own file --------------------------------------------------------------------------------------------------
func _tab_own() -> void:
	var v := _page("Eigene Datei", "3D-Datei (.glb oder .gltf) laden – mit dem Knopf oder einfach ins Simulator-Fenster ziehen. Sie erscheint in der Szene «Meine Vorlage»; Grösse und Mitte stellt der Simulator selbst ein, Wände und Gegenstände werden zu Hindernissen.")
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	v.add_child(h)
	var b := Button.new()
	b.text = "📂 Datei wählen …"
	UI.primary(b)
	b.pressed.connect(_pick_file)
	h.add_child(b)
	var o := Button.new()
	o.text = "Szene «Meine Vorlage» zeigen"
	o.pressed.connect(func(): main.set_scene("vorlage"); _say("Szene «Meine Vorlage» geladen."))
	h.add_child(o)
	var f := Button.new()
	f.text = "Ordner öffnen"
	f.tooltip_text = "Hier liegen die geladenen Dateien"
	f.pressed.connect(func(): OS.shell_open(ProjectSettings.globalize_path(DIR)))
	h.add_child(f)
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 6)
	v.add_child(_list)
	_fd = FileDialog.new()
	_fd.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	_fd.access = FileDialog.ACCESS_FILESYSTEM
	_fd.filters = PackedStringArray(["*.glb, *.gltf ; 3D-Modell (glTF)"])
	_fd.title = "3D-Datei wählen"
	_fd.size = Vector2i(760, 480)
	_fd.file_selected.connect(func(p): import_file(p))
	add_child(_fd)


func _pick_file() -> void:
	_fd.popup_centered()


func _on_drop(files: PackedStringArray) -> void:
	var n := 0
	for p in files:
		if p.get_extension().to_lower() in ["jpg", "jpeg", "png", "webp"] and main.zwilling != null:   # 3D-4.4: a photo of the place
			if main.zwilling.import_image(p) and main.inventar != null:
				main.inventar.open(0)                    # 3D-4.x: shown in the window «Dein Platz»
			return
		if p.get_extension().to_lower() in ["glb", "gltf"]:
			if import_file(p, false):
				n += 1
	if n > 0:
		main.set_scene("vorlage")
		visible = true
		tabs.current_tab = 3
		get_parent().move_child(self, -1)
	elif files.size() > 0:
		_say("Nur .glb- und .gltf-Dateien gehen (andere Formate in Blender öffnen und als glTF 2.0 exportieren).")


func import_file(path: String, show := true) -> bool:
	"""copy the file to user://vorlagen as .glb (a .gltf with its parts becomes one .glb) and place it"""
	var ext := path.get_extension().to_lower()
	var base := path.get_file().get_basename().validate_filename()
	var dst := DIR + "/" + base + ".glb"
	var i := 2
	while FileAccess.file_exists(dst):
		dst = DIR + "/%s_%d.glb" % [base, i]
		i += 1
	if ext == "glb":
		var bytes := FileAccess.get_file_as_bytes(path)
		if bytes.size() < 20 or bytes.slice(0, 4).get_string_from_ascii() != "glTF":
			_say("Datei nicht lesbar: " + path.get_file())
			return false
		var fw := FileAccess.open(dst, FileAccess.WRITE)
		if fw == null:
			_say("Kann nicht speichern: " + dst)
			return false
		fw.store_buffer(bytes)
		fw.close()
	else:
		var doc := GLTFDocument.new()
		var st := GLTFState.new()
		if doc.append_from_file(path, st) != OK:
			_say("Datei nicht lesbar: " + path.get_file())
			return false
		var sc = doc.generate_scene(st)
		var doc2 := GLTFDocument.new()
		var st2 := GLTFState.new()
		var ok: bool = sc != null and doc2.append_from_scene(sc, st2) == OK and doc2.write_to_filesystem(st2, dst) == OK
		if sc != null:
			sc.free()
		if not ok:
			_say("Umwandeln ging nicht: " + path.get_file())
			return false
	var test = _load_scene(dst)
	if test == null:
		DirAccess.remove_absolute(dst)
		_say("Datei enthält kein 3D-Modell: " + path.get_file())
		return false
	var info := _measure(test)
	test.free()
	var e := {"file": dst.get_file(), "name": path.get_file(), "x": 0.0, "z": -16.0 if placed.is_empty() else -16.0 - 10.0 * placed.size(),
			"rot": 0.0, "scale": 1.0, "auto": float(info["auto"]), "size": info["size"]}
	if float(info["size"].x) * float(info["auto"]) > 60.0:
		e["z"] = 0.0                                       # a whole area: MoveEye stands in its middle
	placed.append(e)
	_save_placed()
	_paint_list()
	_say("«%s» geladen (%s)." % [path.get_file(), _size_txt(e)])
	if show:
		main.set_scene("vorlage")
	elif main.scene == "vorlage":
		main.set_scene("vorlage")
	return true


func _load_scene(p: String) -> Node3D:
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_file(ProjectSettings.globalize_path(p) if p.begins_with("user://") else p, st) != OK:
		return null
	var sc = doc.generate_scene(st)
	return sc as Node3D


func _meshes(n: Node, xf: Transform3D, out: Array) -> void:
	var t := xf
	if n is Node3D:
		t = xf * (n as Node3D).transform
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		out.append([n, t])
	for c in n.get_children():
		_meshes(c, t, out)


func _aabb_of(ms: Array) -> AABB:
	var box := AABB()
	var first := true
	for it in ms:
		var a: AABB = it[1] * (it[0] as MeshInstance3D).mesh.get_aabb()
		box = a if first else box.merge(a)
		first = false
	return box


func _measure(sc: Node3D) -> Dictionary:
	"""the size and a guess of the unit: a model of 300 m or more is mostly in cm, of 3 km or more in mm"""
	var ms := []
	_meshes(sc, Transform3D(), ms)
	var box := _aabb_of(ms)
	var big := maxf(box.size.x, maxf(box.size.y, box.size.z))
	var auto := 1.0
	if big > 3000.0:
		auto = 0.001
	elif big > 300.0:
		auto = 0.01
	elif big < 0.05 and big > 0.0:
		auto = 100.0
	return {"auto": auto, "size": box.size, "meshes": ms.size()}


func _size_txt(e: Dictionary) -> String:
	var s: Vector3 = e.get("size", Vector3.ZERO) if typeof(e.get("size")) == TYPE_VECTOR3 else Vector3.ZERO
	var k := float(e.get("auto", 1.0)) * float(e.get("scale", 1.0))
	return "%.1f × %.1f × %.1f m" % [s.x * k, s.z * k, s.y * k]


func place_into(root: Node3D) -> void:
	"""called by scenes.gd _vorlage: every loaded file into the scene, standing on the ground, with obstacles"""
	var nob := 0
	for e in placed:
		var sc := _load_scene(DIR + "/" + str(e["file"]))
		if sc == null:
			continue
		var holder := Node3D.new()
		holder.name = "vorlage_" + str(e["file"]).get_basename()
		root.add_child(holder)
		holder.add_child(sc)
		var ms := []
		_meshes(sc, Transform3D(), ms)
		var box := _aabb_of(ms)
		var k := float(e.get("auto", 1.0)) * float(e.get("scale", 1.0))
		# the middle of the model on (x, z), the lowest point on the ground
		sc.position = -Vector3(box.position.x + box.size.x / 2.0, box.position.y, box.position.z + box.size.z / 2.0)
		holder.scale = Vector3.ONE * k
		holder.rotation.y = deg_to_rad(float(e.get("rot", 0.0)))
		holder.position = Vector3(float(e.get("x", 0.0)), 0.0, float(e.get("z", 0.0)))
		e["size"] = box.size
		for it in ms:
			var mi: MeshInstance3D = it[0]
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		# obstacles: each mesh (in the scene frame) that is a thing people walk round - not the ground, not tiny bits
		var hx := Transform3D(holder.basis, holder.position) * Transform3D(Basis(), sc.position)
		for it in ms:
			if nob >= MAX_OBST:
				break
			var a: AABB = (hx * it[1]) * (it[0] as MeshInstance3D).mesh.get_aabb()
			if a.size.y < 0.35 or a.position.y > 1.6:          # flat (ground, road) or high up (roof, lamp)
				continue
			if a.size.x > 40.0 or a.size.z > 40.0 or a.size.x * a.size.z < 0.04:
				continue
			var c := a.get_center()
			if Vector2(c.x, c.z).length() < 1.5:               # never right at MoveEye
				continue
			main.add_obstacle_box(Vector3(c.x, 0, c.z), a.size.x, a.size.z, 0.0)
			main.set_obstacle_height(a.position.y + a.size.y)
			nob += 1
	if placed.is_empty():
		_say("Noch keine 3D-Datei – «Vorlagen» → «Eigene Datei» oder eine .glb ins Fenster ziehen.")   # (was main._say: wrong arguments)


func _paint_list() -> void:
	if _list == null:
		return
	for c in _list.get_children():
		c.queue_free()
	if placed.is_empty():
		var l := UI.small("Noch keine Datei geladen. Tipp: in «Bausätze» z. B. bei Kenney ein Haus herunterladen und hier hineinziehen.")
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size = Vector2(560, 0)
		_list.add_child(l)
		return
	for i in range(placed.size()):
		var e: Dictionary = placed[i]
		var pc := PanelContainer.new()
		pc.add_theme_stylebox_override("panel", UI.box(UI.PANEL2, UI.LINE, 10, 8))
		_list.add_child(pc)
		var vv := VBoxContainer.new()
		pc.add_child(vv)
		var t := Label.new()
		t.text = "%s   ·   %s" % [e["name"], _size_txt(e)]
		vv.add_child(t)
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 4)
		vv.add_child(h)
		for d in [["◀", "x", -2.0], ["▶", "x", 2.0], ["▲", "z", -2.0], ["▼", "z", 2.0], ["⟲", "rot", -15.0], ["⟳", "rot", 15.0], ["−", "scale", 0.8], ["+", "scale", 1.25]]:
			var b := Button.new()
			b.text = d[0]
			b.custom_minimum_size = Vector2(38, 30)
			b.tooltip_text = {"x": "verschieben (links / rechts, 2 m)", "z": "verschieben (weg / her, 2 m)", "rot": "drehen (15°)", "scale": "kleiner / grösser"}[d[1]]
			b.pressed.connect(_adjust.bind(i, d[1], d[2]))
			h.add_child(b)
		var r := Button.new()
		r.text = "Mitte"
		r.tooltip_text = "Wieder in die Mitte, Originalgrösse"
		r.pressed.connect(func(): e["x"] = 0.0; e["z"] = -16.0; e["rot"] = 0.0; e["scale"] = 1.0; _changed())
		h.add_child(r)
		var x := Button.new()
		x.text = "Weg"
		x.tooltip_text = "Entfernen"
		x.pressed.connect(func(): remove(i))
		h.add_child(x)


func _adjust(i: int, key: String, d: float) -> void:
	if i >= placed.size():
		return
	var e: Dictionary = placed[i]
	if key == "scale":
		e["scale"] = clampf(float(e["scale"]) * d, 0.05, 50.0)
	else:
		e[key] = float(e[key]) + d
	_changed()


func _changed() -> void:
	_save_placed()
	_paint_list()
	if main.scene == "vorlage":
		main.set_scene("vorlage")


func remove(i: int) -> void:
	if i >= placed.size():
		return
	var e: Dictionary = placed[i]
	placed.remove_at(i)
	var still := false
	for o in placed:
		still = still or o["file"] == e["file"]
	if not still:
		DirAccess.remove_absolute(DIR + "/" + str(e["file"]))
	_changed()


func _say(s: String) -> void:
	if _msg != null:
		_msg.text = s


func _save_placed() -> void:
	var out := []
	for e in placed:
		var d: Dictionary = e.duplicate()
		var s = d.get("size", Vector3.ZERO)
		d["size"] = [s.x, s.y, s.z] if typeof(s) == TYPE_VECTOR3 else [0, 0, 0]
		out.append(d)
	var f := FileAccess.open(DIR + "/vorlagen.json", FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(out))


func _load_placed() -> void:
	placed = []
	if not FileAccess.file_exists(DIR + "/vorlagen.json"):
		return
	var js = JSON.parse_string(FileAccess.get_file_as_string(DIR + "/vorlagen.json"))
	if typeof(js) != TYPE_ARRAY:
		return
	for d in js:
		if typeof(d) == TYPE_DICTIONARY and FileAccess.file_exists(DIR + "/" + str(d.get("file", ""))):
			var s = d.get("size", [0, 0, 0])
			d["size"] = Vector3(float(s[0]), float(s[1]), float(s[2])) if typeof(s) == TYPE_ARRAY and s.size() == 3 else Vector3.ZERO
			placed.append(d)


func info() -> Dictionary:
	var out := []
	for e in placed:
		out.append({"name": e["name"], "file": e["file"], "x": e["x"], "z": e["z"], "rot": e["rot"], "scale": e["scale"], "auto": e["auto"], "size": _size_txt(e)})
	return {"placed": out, "visible": visible, "tab": tabs.current_tab}
