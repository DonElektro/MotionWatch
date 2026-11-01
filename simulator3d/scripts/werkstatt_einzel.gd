extends RefCounted
## «Bauen» → Einzelteil-Vorschau und «Druckplatten» (Paket real-einzelteil-vorschau, 01.11.2026; gleich wie MoveEye /build,
## Teil 639wc): ein angetipptes Teil allein zeigen (drehen, zoomen, zentriert), Grösse, Druck-Infos bzw. Zukauf-Infos, Download
## der 3MF genau dieses Teils, «Liegend wie gedruckt» auf einer Druckplatte 256 × 256 mm, «Wo es hingehört» (kleines Bild unten
## rechts mit dem ganzen Modell, das Teil leuchtet, und dem Montageschritt – antippen springt zum Schritt). «Druckplatten»: Platte
## A / B der Variante mit allen Teilen wie in der 3MF; Teile ohne eigenes Netz (kleine Stopfen, die 4 Füsse) als Quader.
## Die Lage kommt aus res://inhalte/gehaeuse/druck_lage.json (werkzeuge/druck_lage.py, dieselben Daten wie MoveEye 639wb): das
## Modell der Werkstatt wird nur gedreht und verschoben, es kommen keine Netze dazu. Downloads: über MoveEye, wenn verbunden
## (/build/datei/…, /build/platten.zip), sonst direkt von GitHub (Einzelteil, Platte) bzw. das Bausatz-Paket (alle Platten).
## «In Bambu Studio öffnen» bewusst nicht: das Link-Schema ist nicht offiziell beschrieben (siehe 639wc).

const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
const DATA = preload("res://scripts/werkstatt_daten.gd")
const FH = preload("res://scripts/fehler_hilfe.gd")
const Icons = preload("res://scripts/mehr_icons.gd")
const PFAD := "res://inhalte/gehaeuse/druck_lage.json"
const RAW := "https://github.com/DonElektro/MotionWatch/raw/main/hardware/gehaeuse/Druckdateien/"
const BAUSATZ := "https://github.com/DonElektro/MotionWatch/releases/latest/download/MoveEye_Bausatz.zip"
const FARBE := {"orange": "orange", "grau": "grau", "natur": "natur / weiss", "schwarz": "schwarz"}
const COL := {"orange": "#f59a4a", "grau": "#6d7074", "natur": "#e9e5d9", "schwarz": "#222222"}

var w                               # werkstatt.gd
var dl := {}                        # druck_lage.json
var mode := ""                      # "" | "teil" | "platten"
var solo := ""
var flat := false
var plate := 0
var pdatei := ""                    # Platte: ein Teil ohne eigenes Netz (nur Infos)
var last_url := ""                  # Tests: was zuletzt geöffnet wurde
var _plate_root: Node3D = null
var _boxes: Node3D = null
var _box_key := ""
var _ui := {}
var _inset_vpc: SubViewportContainer = null
var _inset_vp: SubViewport = null
var _inset_world: Node3D = null
var _inset_mis := {}
var _inset_key := ""
var _ghost: StandardMaterial3D
var _lit: StandardMaterial3D


func _init(werkstatt) -> void:
	w = werkstatt
	if FileAccess.file_exists(PFAD):
		var d = JSON.parse_string(FileAccess.get_file_as_string(PFAD))
		if d is Dictionary:
			dl = d
	_ghost = StandardMaterial3D.new()
	_ghost.albedo_color = Color(0.75, 0.8, 0.88, 0.2)
	_ghost.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_ghost.cull_mode = BaseMaterial3D.CULL_DISABLED
	_lit = StandardMaterial3D.new()
	_lit.albedo_color = Color("#f59a4a")
	_lit.emission_enabled = true
	_lit.emission = Color("#f59a4a")
	_lit.emission_energy_multiplier = 0.6


func lage(id: String) -> Dictionary:
	return (dl.get("lage", {}) as Dictionary).get(id, {})


func plates() -> Array:
	return (dl.get("platten", {}) as Dictionary).get("v52" if w.v52 else "v51", [])


# ---- the card of the part, below the 3D picture (like MoveEye: under the picture, not in the side panel) --------------------
func build_ui(col: VBoxContainer) -> void:
	"""real-einzelteil-2: under the picture – left the infos, right the buttons (MoveEye #v3d-info)"""
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sc.visible = false
	col.add_child(sc)
	_ui["card"] = sc
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", UI.box(UI.FIELD, UI.ACC, 12, 10, 1))
	pc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(pc)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 14)
	pc.add_child(hb)
	var iv := VBoxContainer.new()
	iv.add_theme_constant_override("separation", 4)
	iv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hb.add_child(iv)
	_ui["box"] = iv
	var bv := VBoxContainer.new()
	bv.add_theme_constant_override("separation", 6)
	bv.custom_minimum_size = Vector2(300, 0)
	hb.add_child(bv)
	_ui["btns"] = bv


static func icon_button(text: String, kind: String) -> Button:
	"""a button with a drawn symbol on the left (🔍 📍 🖨 of MoveEye – the font of Godot has no emoji)"""
	var b := Button.new()
	b.text = "      " + text
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	var ic := Icons.icon(kind, UI.TXT, 18.0)
	ic.set_anchors_preset(Control.PRESET_CENTER_LEFT)
	ic.offset_left = 9.0
	ic.offset_top = -9.0
	ic.offset_right = 27.0
	ic.offset_bottom = 9.0
	b.add_child(ic)
	b.set_meta("icon", kind)
	return b


func build_view(holder: Control) -> void:
	"""the inset «Wo es hingehört» bottom right over the 3D picture (own little world: the same meshes, the part lit)"""
	_inset_vpc = SubViewportContainer.new()
	_inset_vpc.stretch = true
	_inset_vpc.custom_minimum_size = Vector2(230, 184)
	_inset_vpc.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_inset_vpc.offset_left = -238.0
	_inset_vpc.offset_top = -192.0
	_inset_vpc.offset_right = -8.0
	_inset_vpc.offset_bottom = -8.0
	_inset_vpc.visible = false
	_inset_vpc.mouse_filter = Control.MOUSE_FILTER_STOP
	_inset_vpc.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			where())
	holder.add_child(_inset_vpc)
	_inset_vp = SubViewport.new()
	_inset_vp.own_world_3d = true
	_inset_vp.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
	_inset_vpc.add_child(_inset_vp)
	var cap := Label.new()
	cap.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cap.add_theme_font_size_override("font_size", 11)
	cap.add_theme_color_override("font_color", Color("#e6edf5"))
	cap.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	cap.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	cap.offset_top = -22.0
	cap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("#1b2430", 0.8)
	cap.add_theme_stylebox_override("normal", sb)
	_inset_vpc.add_child(cap)
	var pin := Icons.icon("pin", Color("#e6edf5"), 14.0)   # 📍 like MoveEye
	pin.set_anchors_preset(Control.PRESET_CENTER_LEFT)
	pin.offset_left = 6.0
	pin.offset_top = -7.0
	pin.offset_right = 20.0
	pin.offset_bottom = 7.0
	cap.add_child(pin)
	_ui["cap"] = cap


func build_world() -> void:
	"""the plate 256 × 256 mm (hidden until needed)"""
	var P := float(dl.get("platte_mm", 256)) / 1000.0
	_plate_root = Node3D.new()
	_plate_root.visible = false
	w.world.add_child(_plate_root)
	var top := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(P, 0.002, P)
	top.mesh = bm
	var m := StandardMaterial3D.new()
	m.albedo_color = Color("#39424f")
	m.roughness = 0.85
	top.material_override = m
	top.position = Vector3(0, -0.0011, 0)
	_plate_root.add_child(top)
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color("#6b7a8c")
	gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for i in range(9):
		var k := -P / 2 + P * i / 8.0
		for along in [0, 1]:
			var ln := MeshInstance3D.new()
			var lb := BoxMesh.new()
			lb.size = Vector3(P, 0.0002, 0.0006) if along == 0 else Vector3(0.0006, 0.0002, P)
			ln.mesh = lb
			ln.material_override = gm
			ln.position = Vector3(0, 0.0001, k) if along == 0 else Vector3(k, 0.0001, 0)
			_plate_root.add_child(ln)
	var fr := MeshInstance3D.new()                   # the front edge (y = 0 of the 3MF) orange
	var fb := BoxMesh.new()
	fb.size = Vector3(P, 0.0025, 0.004)
	fr.mesh = fb
	var fm := StandardMaterial3D.new()
	fm.albedo_color = Color("#f59a4a")
	fr.material_override = fm
	fr.position = Vector3(0, -0.001, P / 2 + 0.002)
	_plate_root.add_child(fr)
	_boxes = Node3D.new()
	_plate_root.add_child(_boxes)


# ---- modes --------------------------------------------------------------------------------------------------------------
func set_mode(m: String, id := "", fl := false, n := 0) -> void:
	mode = m if m in ["", "teil", "platten"] else ""
	if mode == "teil":
		if not w.parts.has(id):
			mode = ""
		else:
			solo = id
			flat = fl and not lage(id).is_empty()
			w.sel = id
	elif mode == "platten":
		plate = clampi(n, 0, maxi(0, plates().size() - 1))
	if mode == "":
		pdatei = ""
		for pid in w.parts:
			(w.parts[pid]["mi"] as MeshInstance3D).transform = Transform3D.IDENTITY
		w.min_dist = 0.12
		w.cam.near = 0.01
		w.set_view(145.0, 24.0, 0.62)
	w._paint()
	if mode != "":
		frame()


func _xf(id: String, dx := 0.0, dz := 0.0) -> Transform3D:
	var L := lage(id)
	if L.is_empty():
		return Transform3D.IDENTITY
	var r: Array = L["r"]
	var t: Array = L["t"]
	var b := Basis(Vector3(float(r[0]), float(r[3]), float(r[6])), Vector3(float(r[1]), float(r[4]), float(r[7])), Vector3(float(r[2]), float(r[5]), float(r[8])))
	return Transform3D(b, Vector3(float(t[0]) + dx, float(t[1]), float(t[2]) + dz))


func paint() -> void:
	"""called at the end of werkstatt._paint() while a mode is on: only the part / the plate, as printed"""
	var P := float(dl.get("platte_mm", 256)) / 1000.0
	var bench = w._w.get("bench")
	if bench != null:
		(bench as Node3D).visible = mode == ""
	var fl := mode == "platten" or (mode == "teil" and flat)
	if _plate_root != null:
		_plate_root.visible = fl
	var pl: Dictionary = plates()[plate] if mode == "platten" and plate < plates().size() else {}
	_make_boxes(pl)
	if _boxes != null:
		_boxes.visible = not pl.is_empty()
	var on := {}
	for it in pl.get("teile", []):
		if str(it.get("id", "")) != "" and w.parts.has(str(it["id"])):
			on[str(it["id"])] = it
	for id in w.parts:
		var p: Dictionary = w.parts[id]
		var mi: MeshInstance3D = p["mi"]
		var m: StandardMaterial3D = p["mat"]
		m.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
		m.albedo_color = Color(p["base"], 1.0)
		m.emission_enabled = false
		if mode == "teil":
			mi.visible = id == solo
			mi.transform = _xf(id) if (mi.visible and fl) else Transform3D.IDENTITY
		else:
			mi.visible = on.has(id)
			if mi.visible:
				mi.transform = _xf(id, float(on[id]["x"]) / 1000.0 - P / 2, P / 2 - float(on[id]["y"]) / 1000.0)
			else:
				mi.transform = Transform3D.IDENTITY
	_inset()
	_side()


func _make_boxes(pl: Dictionary) -> void:
	if _boxes == null:
		return
	var key := ("v52" if w.v52 else "v51") + ":" + str(pl.get("name", ""))
	if key == _box_key:
		return
	_box_key = key
	for c in _boxes.get_children():
		c.free()
	var P := float(dl.get("platte_mm", 256)) / 1000.0
	for it in pl.get("teile", []):
		if str(it.get("id", "")) != "" and w.parts.has(str(it["id"])):
			continue
		var g: Array = it["g"]
		var bx := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(maxf(float(g[0]), 0.5), maxf(float(g[2]), 0.5), maxf(float(g[1]), 0.5)) / 1000.0
		bx.mesh = bm
		var mt := StandardMaterial3D.new()
		mt.albedo_color = Color(str(COL.get(str((dl.get("dateien", {}) as Dictionary).get(str(it["datei"]), {}).get("farbe", "grau")), "#6d7074")))
		mt.roughness = 0.6
		bx.material_override = mt
		bx.position = Vector3(float(it["x"]) / 1000.0 - P / 2, float(g[2]) / 2000.0, P / 2 - float(it["y"]) / 1000.0)
		bx.set_meta("it", it)
		_boxes.add_child(bx)


func frame() -> void:
	"""the camera on the part / the plate"""
	var aabb := AABB()
	if mode == "platten":
		var P := float(dl.get("platte_mm", 256)) / 1000.0
		aabb = AABB(Vector3(-P / 2, 0, -P / 2), Vector3(P, 0.04, P))
	elif w.parts.has(solo):
		var mi: MeshInstance3D = w.parts[solo]["mi"]
		aabb = mi.transform * mi.mesh.get_aabb()
	else:
		return
	var r := maxf(0.006, aabb.size.length() / 2.0)
	w.min_dist = maxf(0.008, r * 0.5)
	w.cam.near = maxf(0.0005, r / 60.0)
	w.target = aabb.get_center()
	w.yaw = 0.0 if mode == "platten" else 145.0
	w.pitch = 58.0 if mode == "platten" else (32.0 if flat else 24.0)
	w.dist = clampf(r / sin(deg_to_rad(w.cam.fov / 2.0)) * (1.25 if mode == "teil" else 1.02), w.min_dist, 2.0)
	w._place_cam()


func tap(pos: Vector2) -> void:
	"""a click in the 3D picture: on a plate the part -> single part view (a box: only its infos)"""
	if mode != "platten":
		return
	var id: String = w.pick_at(pos)
	if id != "":
		plate_tap(id, str(lage(id).get("datei", "")))
		return
	var o: Vector3 = w.cam.project_ray_origin(pos)
	var d: Vector3 = w.cam.project_ray_normal(pos)
	var best = null
	var bt := INF
	for bx in _boxes.get_children():
		var inv := (bx as Node3D).global_transform.affine_inverse()
		var hit = ((bx as MeshInstance3D).mesh.get_aabb().grow(0.001)).intersects_ray(inv * o, (inv.basis * d).normalized())
		if hit != null and (hit as Vector3).distance_to(inv * o) < bt:
			bt = (hit as Vector3).distance_to(inv * o)
			best = bx
	if best != null:
		var it: Dictionary = best.get_meta("it")
		plate_tap(str(it.get("teil", "")), str(it.get("datei", "")))


func plate_tap(id: String, datei: String) -> void:
	if id != "" and not lage(id).is_empty() and w.parts.has(id):
		set_mode("teil", id, true)
		return
	pdatei = datei
	_side()


func where() -> void:
	"""«Wo es hingehört»: back to the whole model, the assembly step of the part"""
	var r = w.rows.get(solo)
	if r == null or int(r[4]) <= 0:
		return
	set_mode("")
	w.set_tab("montage")
	w.set_step(int(r[4]))


func _step_text() -> String:
	var r = w.rows.get(solo)
	if r == null or int(r[4]) <= 0:
		return ""
	return T.t("Wo es hingehört") + " · " + T.t("Schritt %d – %s") % [int(r[4]), T.t(str(w._schritt(int(r[4]))[0]))]


func _inset() -> void:
	if _inset_vpc == null:
		return
	var on: bool = mode == "teil" and w.parts.has(solo)
	_inset_vpc.visible = on
	if not on:
		return
	if _inset_world == null:
		_inset_world = Node3D.new()
		_inset_vp.add_child(_inset_world)
		var env := Environment.new()
		env.background_mode = Environment.BG_COLOR
		env.background_color = Color("#243142")
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.ambient_light_color = Color(0.62, 0.66, 0.72)
		env.ambient_light_energy = 0.7
		var we := WorldEnvironment.new()
		we.environment = env
		_inset_world.add_child(we)
		var sun := DirectionalLight3D.new()
		sun.rotation_degrees = Vector3(-50, -30, 0)
		_inset_world.add_child(sun)
		var c := Camera3D.new()
		c.fov = 40.0
		c.near = 0.01
		var b := Basis.from_euler(Vector3(deg_to_rad(-24.0), deg_to_rad(145.0), 0))
		var tg := Vector3(0, -0.06, 0.04)
		c.position = tg + b * Vector3(0, 0, 0.6)
		_inset_world.add_child(c)
		c.look_at(tg, Vector3.UP)
		for id in w.parts:
			var mi := MeshInstance3D.new()
			mi.mesh = (w.parts[id]["mi"] as MeshInstance3D).mesh
			_inset_world.add_child(mi)
			_inset_mis[id] = mi
	var key := solo + ":" + str(w.v52) + str(w.inner)
	if key != _inset_key:
		_inset_key = key
		var s0: int = w.step
		w.step = 0
		for id in _inset_mis:
			var mi: MeshInstance3D = _inset_mis[id]
			mi.visible = id == solo or w._shown(id)
			mi.material_override = _lit if id == solo else _ghost
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		w.step = s0
	var r = w.rows.get(solo)                         # short like MoveEye: «📍 Schritt 10 von 14»
	(_ui["cap"] as Label).text = ("       " + T.t("Schritt %d von %d") % [int(r[4]), DATA.SCHRITTE.size()]) if r != null and int(r[4]) > 0 else ""


# ---- the side card ------------------------------------------------------------------------------------------------------
func _druck(datei: String) -> Dictionary:
	var any := {}
	for p in DATA.BAU.get("druck", {}).get("teile", []):
		if str(p.get("datei", "")) == datei:
			if w._ok(p.get("wenn")):
				return p
			any = p
	return any


func pfile(datei: String) -> String:
	"""the 3MF of a print part: v5.2 -> Druckdateien/v5-2/ (also parts that exist only there), else v5.1 (like MoveEye pfile)"""
	var all: Array = DATA.BAU.get("druckdateien_einzeln", [])
	var f1 := "MoveEye_v5-1_" + datei + ".3mf"
	var f2 := "v5-2/MoveEye_v5-2_" + datei + ".3mf"
	return f2 if f2 in all and (w.v52 or not (f1 in all)) else f1


func _pname(datei: String) -> String:
	for r in DATA.TEILE:
		if str(r[5]) == datei and str(r[2]) != "":
			return T.t(str(r[2]))
	return datei.replace("_", " ")


func _n1(v: float) -> String:
	return str(int(round(v))) if v >= 20.0 else str(snappedf(v, 0.1)).replace(".", ",")


func dims(id: String) -> String:
	"""Bounding Box in Einbaulage (mm: Länge × Breite × Höhe), aus druck_lage.json «masse» – dieselben Zahlen wie MoveEye"""
	var g: Array = (dl.get("masse", {}) as Dictionary).get(id, [])
	if g.size() < 3:
		return ""
	return "%s × %s × %s" % [_n1(float(g[0])), _n1(float(g[1])), _n1(float(g[2]))]


func print_lines(datei: String) -> Array:
	var d := _druck(datei)
	var de: Dictionary = (dl.get("dateien", {}) as Dictionary).get(datei, {})
	var out := [T.t("Material") + ": PETG", T.t("Farbe") + ": " + T.t(str(FARBE.get(str(de.get("farbe", "grau")), "grau")))]
	if d.has("liegt"):
		out.append(T.t("Ausrichtung") + ": " + T.t(str(d["liegt"])))
	if not d.is_empty():
		out.append(T.t("Stützen") + ": " + ("✓" if bool(d.get("stuetzen", false)) else T.t("keine")) + "  ·  Brim: " + (("%d mm" % int(d["brim"])) if int(d.get("brim", 0)) > 0 else T.t("keine")))
		out.append("%s %d %%  ·  %s %d  ·  %s %s mm  ·  × %d" % [T.t("Füllung"), int(d.get("fuellung", 0)), T.t("Wände"), int(d.get("waende", 0)), T.t("Schicht"), str(d.get("schicht", "")), int(d.get("stueck", 1))])
		out.append(T.t("Druckzeit") + ": " + T.t("ca. %s h (geschätzt)") % str(d.get("zeit_h", "")))
	if de.has("gramm"):
		out.append(T.t("Gewicht") + ": " + T.t("ca. %s g (geschätzt)") % str(de["gramm"]))
	return out


func _btn(parent: Control, text: String, cb: Callable, primary := false, kind := "") -> Button:
	var b: Button = icon_button(text, kind) if kind != "" else Button.new()
	if kind == "":
		b.text = text
	b.clip_text = true                               # one line (autowrap made the first button very tall in a fresh column)
	b.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	b.tooltip_text = text
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if primary:
		UI.primary(b)
	b.pressed.connect(cb)
	parent.add_child(b)
	return b


func _lbl(parent: Control, text: String, col := UI.TXT, big := false) -> void:
	var l := Label.new()
	l.text = text
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(300, 0)
	l.add_theme_color_override("font_color", col)
	if big:
		l.add_theme_font_override("font", UI.heading_font())
		l.add_theme_font_size_override("font_size", 15)
	parent.add_child(l)


func _title(text: String, kind := "search") -> Control:
	"""the heading of the card with its symbol (🔍 / 🖨 in MoveEye)"""
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 6)
	var ic := Icons.icon(kind, UI.TXT, 18.0)
	ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hb.add_child(ic)
	var l := Label.new()
	l.text = text
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.add_theme_font_override("font", UI.heading_font())
	l.add_theme_font_size_override("font_size", 15)
	hb.add_child(l)
	return hb


func open_url(path: String, raw_name := "") -> void:
	"""a download: through MoveEye when it is connected, else GitHub (the single file) or the kit (all plates)"""
	var b: String = FH.mw_base(w.main) if w.main != null else ""
	if b != "":
		last_url = b + path
	elif raw_name != "":
		last_url = RAW + raw_name
	else:
		last_url = BAUSATZ
	if not w.has_meta("no_shell"):
		OS.shell_open(last_url)


func _side() -> void:
	var card = _ui.get("card")
	if card == null or not is_instance_valid(card):
		return
	(card as Control).visible = mode != ""
	var sb = w._w.get("solo_btn")
	if sb != null and is_instance_valid(sb):
		(sb as Button).visible = mode == "" and w.sel != "" and w.rows.has(w.sel)
	for k in ["explode", "xray", "inner"]:
		var c = w._w.get(k)
		if c != null and is_instance_valid(c):
			if c is HSlider:
				(c as HSlider).editable = mode == ""
			else:
				(c as BaseButton).disabled = mode != ""
	var pb = w._w.get("plates_btn")
	if pb != null and is_instance_valid(pb):
		(pb as Button).button_pressed = mode == "platten"
	if mode == "":
		return
	var v: VBoxContainer = _ui["box"]
	var bv: VBoxContainer = _ui["btns"]
	for c in v.get_children() + bv.get_children():
		c.queue_free()
	if mode == "teil":
		var r = w.rows.get(solo, [solo, "", solo, "", 0, ""])
		var b = DATA.BOM.get(str(r[3]))
		v.add_child(_title(T.t("Einzelteil") + ": " + T.t(str(r[2]) if str(r[2]) != "" else (str(b[1]) if b != null else solo))))
		var sz := dims(solo)
		var L := lage(solo)
		if sz != "":
			sz = T.t("Grösse (Bounding Box): %s mm") % sz
		if flat and not L.is_empty():
			sz += "  ·  " + T.t("auf der Platte %s mm") % ("%s × %s × %s" % [_n1(float(L["g"][0])), _n1(float(L["g"][1])), _n1(float(L["g"][2]))])
		if sz != "":
			_lbl(v, sz)
		var datei := str(r[5]) if r.size() > 5 else ""
		if datei != "":
			_lbl(v, T.t("Druckteil"), UI.MUT)
			for ln in print_lines(datei):
				_lbl(v, ln, UI.MUT)
			var f := pfile(datei)
			_btn(bv, "⬇ " + T.t("Druckdatei 3MF (dieses Teil)"), func(): open_url("/build/datei/" + f.uri_encode().replace("%2F", "/"), f))
			if not L.is_empty():
				var ck := CheckButton.new()
				ck.text = T.t("Liegend wie gedruckt (Druckplatte 256 × 256 mm)")
				ck.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				ck.custom_minimum_size = Vector2(300, 0)
				ck.button_pressed = flat
				ck.toggled.connect(func(on): set_mode("teil", solo, on))
				bv.add_child(ck)
				if bool(L.get("unsicher", false)) and flat:
					_lbl(v, T.t("wie eingebaut (Lage geschätzt)"), UI.MUT)
		elif b != null:
			_lbl(v, T.t("Zukaufteil"), UI.MUT)
			var ex: Dictionary = DATA.BAU.get("bom_extra", {}).get(str(r[3]), {})
			_lbl(v, "%s  %s" % [T.t(str(b[0])), T.t(str(b[1]))])
			if str(b[2]) != "":
				_lbl(v, T.t("Bestellnummer") + ": " + T.t(str(b[2])), UI.MUT)
			_lbl(v, T.t("Gruppe") + ": " + T.t(str(b[3])), UI.MUT)
			var H: Dictionary = DATA.BAU.get("haendler", {})
			var hk := str(ex.get("haendler", ""))
			if H.has(hk):
				var u := str(H[hk]["suche"]).replace("{q}", str(ex.get("suche", "")).uri_encode())
				var lb := LinkButton.new()
				lb.text = T.t("Suchen bei") + " " + T.t(str(H[hk]["name"]))
				lb.pressed.connect(func():
					last_url = u
					if not w.has_meta("no_shell"):
						OS.shell_open(u))
				bv.add_child(lb)
		else:
			_lbl(v, T.t("nicht in der Materialliste"), UI.MUT)
		var st := _step_text()
		if st != "":                                 # the button short (one line with its symbol), the full step as a line on the left
			var rr = w.rows.get(solo)
			_lbl(v, st, UI.MUT)
			_btn(bv, T.t("Wo es hingehört") + " · " + T.t("Schritt %d von %d") % [int(rr[4]), DATA.SCHRITTE.size()], where, false, "pin")
		_btn(bv, "↩ " + T.t("Zurück zum ganzen Modell"), func(): set_mode(""), true)
	else:
		v.add_child(_title(T.t("Druckplatten") + " · " + T.t("Gehäuse") + " v" + ("5.2" if w.v52 else "5.1"), "printer"))
		var hb := HBoxContainer.new()
		hb.add_theme_constant_override("separation", 6)
		v.add_child(hb)
		var ps := plates()
		for i in range(ps.size()):
			var bt := Button.new()
			bt.text = T.t("Platte %s") % str(ps[i]["name"])
			bt.toggle_mode = true
			bt.button_pressed = i == plate
			var st_ := UI.box(UI.ACC if i == plate else UI.BTN2, UI.ACC if i == plate else UI.LINE, 8, 6, 1)
			for s_ in ["normal", "hover", "pressed", "focus"]:
				bt.add_theme_stylebox_override(s_, st_)
			var ii := i
			bt.pressed.connect(func(): set_mode("platten", "", false, ii))
			hb.add_child(bt)
		if plate >= ps.size():
			return
		var pl: Dictionary = ps[plate]
		_lbl(v, T.t("%d Teile auf dieser Platte") % (pl["teile"] as Array).size() + " · 256 × 256 mm · " + T.t("Teil auf der Platte antippen: Einzelteil-Vorschau."), UI.MUT)
		if pdatei != "":
			_lbl(v, _pname(pdatei), UI.TXT, true)
			_lbl(v, T.t("als Quader gezeigt (kein eigenes 3D-Modell)"), UI.MUT)
			for ln in print_lines(pdatei):
				_lbl(v, ln, UI.MUT)
			var f2 := pfile(pdatei)
			_btn(bv, "⬇ " + T.t("Druckdatei 3MF (dieses Teil)"), func(): open_url("/build/datei/" + f2.uri_encode().replace("%2F", "/"), f2))
		var seen := []
		for it in pl["teile"]:
			var dt := str(it["datei"])
			if dt in seen:
				continue
			seen.append(dt)
			var n := 0
			for x in pl["teile"]:
				if str(x["datei"]) == dt:
					n += 1
			var lb2 := LinkButton.new()
			lb2.text = _pname(dt) + ((" × %d" % n) if n > 1 else "")
			var iid := str(it.get("id", it.get("teil", "")))
			lb2.pressed.connect(func(): plate_tap(iid, dt))
			v.add_child(lb2)
		var pf := str(pl["datei"])
		_btn(bv, "⬇ " + T.t("Platte herunterladen (3MF)"), func(): open_url("/build/datei/" + pf.uri_encode().replace("%2F", "/"), pf))
		_btn(bv, "⬇ " + T.t("Alle Platten (ZIP mit Kurzanleitung)"), func(): open_url("/build/platten.zip?v=" + ("v52" if w.v52 else "v51") + "&lang=" + T.lang()))
		_lbl(v, T.t("3MF in Bambu Studio öffnen (Datei → Öffnen): die Teile liegen schon richtig, ohne Stützen."), UI.MUT)
		_btn(bv, "↩ " + T.t("Zurück zum ganzen Modell"), func(): set_mode(""), true)


func after_paint() -> void:
	"""end of werkstatt._paint(): in a mode only the part / the plate; else just the button «Nur dieses Teil zeigen»"""
	if mode != "":
		paint()
	else:
		_side()


func closed() -> void:
	"""the window is closed: its nodes are gone"""
	mode = ""
	pdatei = ""
	_plate_root = null
	_boxes = null
	_box_key = ""
	_inset_vpc = null
	_inset_vp = null
	_inset_world = null
	_inset_mis = {}
	_inset_key = ""
	_ui = {}


func info() -> Dictionary:
	var vis := []
	for id in w.parts:
		if (w.parts[id]["mi"] as MeshInstance3D).visible:
			vis.append(id)
	return {"mode": mode, "solo": solo, "flat": flat, "plate": plate, "plates": plates().size(), "visible": vis,
			"boxes": _boxes.get_child_count() if _boxes != null and _boxes.visible else 0, "inset": _inset_vpc != null and _inset_vpc.visible,
			"where": _step_text() if mode == "teil" else "", "pdatei": pdatei, "url": last_url, "data": not dl.is_empty()}
