extends Node
## «Werkstatt» (Mehr → Werkstatt; MoveEye: Mehr → «Gehäuse & Bau» → «Im Simulator ansehen»; Paket «real-gehaeuse»,
## 01.11.2026): das Gehäuse v5.1 mit dem Innenleben in einer eigenen kleinen 3D-Welt.
##   · ziehen = drehen, rechts / mittlere Taste ziehen = verschieben, Rad = zoomen, Teil anklicken = Name, Eintrag aus der
##     Materialliste (Menge, Bezeichnung, Teilenummer) und der passende Montageschritt
##   · Regler «Explosion», «Durchsichtig» (Druckteile fast durchsichtig, Klicks treffen zuerst das Innenleben),
##     «Innenleben», «Variante v5.2» (real-gehaeuse-v52: das echte Unterteil v5.2 mit Fenster, Weitwinkel-Kamera, IR-Modul
##     120°, Kabelkamm, Tasten, Status-LED – aus hardware/gehaeuse/Quellcode/v52.py; ersetzte Teile von v5.1 werden ausgeblendet)
##   · «Montage Schritt für Schritt»: die 14 Schritte der Montageanleitung v5.1 (LIESMICH_Montage_v5-1.md + v4.1 Kopf), die
##     Teile des Schritts fliegen an ihren Platz, Weiter / Zurück
## Modelle: res://inhalte/gehaeuse/gehaeuse.glb (alle Teile, gehaeuse.gd lädt es), Texte: werkstatt_daten.gd (erzeugt aus
## hardware/gehaeuse/bau.json). Die Welt rechnet nur, solange das Fenster offen ist.
## /control {"action": "werkstatt", "do": open | close | info | explode (value) | xray (on) | inner (on) | v52 (on) |
##           pick (id) | step (n, 0 = frei) | next | prev | view (yaw, pitch, dist) | real_case (on)}

const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
const DATA = preload("res://scripts/werkstatt_daten.gd")
const GH = preload("res://scripts/gehaeuse.gd")
const DRUCK_ALPHA := 0.16

var main
var mehr
var layer: CanvasLayer
var win: PanelContainer = null
var vpc: SubViewportContainer
var vp: SubViewport
var cam: Camera3D
var world: Node3D
var parts := {}                    # id -> {mi, e (modelle.json), mat, row (TEILE)}
var rows := {}                     # id -> [id, art, name, bom, schritt, datei, ersetzt]
var repl := {}                     # v5.2: Teil von v5.1 -> das Teil der Variante, das es ersetzt
var yaw := 145.0                  # from the front (PIR side), a little from the left
var pitch := 24.0
var dist := 0.62
var target := Vector3(0, -0.06, 0.04)
var explode := 0.0
var xray := false
var inner := true
var v52 := false
var sel := ""
var step := 0                      # 0 = frei, 1..N = Montage
var _anim := 1.0                   # 0 -> 1: the parts of the step fly in
var _drag := Vector2.ZERO
var _down := Vector2.ZERO
var _btn := 0
var _w := {}                       # widgets


func _ready() -> void:
	layer = CanvasLayer.new()
	layer.layer = 61
	add_child(layer)
	for r in DATA.TEILE:
		rows[str(r[0])] = r
		if r.size() > 6 and str(r[6]) != "":
			repl[str(r[6])] = str(r[0])


func is_open() -> bool:
	return win != null and is_instance_valid(win)


func open() -> void:
	if is_open():
		return
	if mehr != null:
		mehr.close_window()
		mehr.close_menu()
	_build_ui()
	_build_world()
	_paint()


func close() -> void:
	if is_open():
		win.queue_free()
	win = null
	parts = {}
	sel = ""


# ---- the window ----------------------------------------------------------------------------------------------------------
func _build_ui() -> void:
	win = PanelContainer.new()
	win.theme = main.ui_root.theme if main.ui_root != null else UI.theme()
	win.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.99), UI.LINE, 16, 12, 1))
	win.set_anchors_preset(Control.PRESET_FULL_RECT)
	for s in ["left", "top", "right", "bottom"]:
		win.set("offset_" + s, 16.0 if s in ["left", "top"] else -16.0)
	layer.add_child(win)
	if mehr != null and mehr.farben != null:
		mehr.farben.register(win, "all")
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 12)
	win.add_child(h)
	vpc = SubViewportContainer.new()
	vpc.stretch = true
	vpc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vpc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	vpc.custom_minimum_size = Vector2(320, 240)
	vpc.gui_input.connect(_on_input)
	h.add_child(vpc)
	vp = SubViewport.new()
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_2X if not GH.Quality.lite() else Viewport.MSAA_DISABLED
	vp.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
	vpc.add_child(vp)
	var side := ScrollContainer.new()
	side.custom_minimum_size = Vector2(350, 0)
	side.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	h.add_child(side)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 8)
	side.add_child(v)
	var hd := HBoxContainer.new()
	v.add_child(hd)
	var tl := Label.new()
	tl.text = T.t("Werkstatt – Gehäuse v%s") % DATA.VERSION
	tl.add_theme_font_override("font", UI.heading_font())
	tl.add_theme_font_size_override("font_size", 17)
	tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(tl)
	var x := Button.new()
	x.text = "✕"
	x.flat = true
	x.tooltip_text = T.t("Schliessen (Esc)")
	x.pressed.connect(close)
	hd.add_child(x)
	var ms := UI.small(T.t(DATA.MASSE))
	ms.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(ms)
	var hint := UI.small(T.t("Ziehen = drehen · rechts ziehen = verschieben · Rad = zoomen · Teil anklicken = was ist das?"))
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(hint)
	# view
	v.add_child(UI.heading(T.t("Ansicht")))
	var er := HBoxContainer.new()
	v.add_child(er)
	var el := Label.new()
	el.text = T.t("Explosion")
	el.custom_minimum_size = Vector2(92, 0)
	er.add_child(el)
	var sl := HSlider.new()
	sl.min_value = 0.0
	sl.max_value = 1.0
	sl.step = 0.01
	sl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sl.value_changed.connect(func(val): set_explode(val))
	er.add_child(sl)
	_w["explode"] = sl
	_w["xray"] = _check(v, T.t("Gehäuse durchsichtig"), func(on): set_xray(on))
	_w["inner"] = _check(v, T.t("Innenleben zeigen"), func(on): set_inner(on))
	_w["v52"] = _check(v, T.t("Variante v5.2 zeigen (Weitwinkel, IR-LED, Tasten, Status-LED)"), func(on): set_v52(on))
	_w["real"] = _check(v, T.t("Echtes Gehäuse am Gerät in der Szene"), func(on): set_real_case(on))
	var rb := Button.new()
	rb.text = T.t("Ansicht zurücksetzen")
	rb.pressed.connect(func(): set_view(145.0, 24.0, 0.62))
	v.add_child(rb)
	# the part
	v.add_child(UI.heading(T.t("Teil")))
	var ip := PanelContainer.new()
	ip.add_theme_stylebox_override("panel", UI.box(UI.FIELD, UI.LINE, 12, 10, 1))
	v.add_child(ip)
	var iv := VBoxContainer.new()
	iv.add_theme_constant_override("separation", 4)
	ip.add_child(iv)
	var nm := Label.new()
	nm.add_theme_font_override("font", UI.heading_font())
	nm.add_theme_font_size_override("font_size", 15)
	nm.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	iv.add_child(nm)
	_w["name"] = nm
	var bo := UI.small("", UI.TXT)
	bo.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	iv.add_child(bo)
	_w["bom"] = bo
	var stl := UI.small("")
	stl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	iv.add_child(stl)
	_w["pstep"] = stl
	var gs := Button.new()
	gs.text = T.t("Zu diesem Schritt")
	gs.pressed.connect(func():
		var r = rows.get(sel)
		if r != null and int(r[4]) > 0:
			set_step(int(r[4])))
	iv.add_child(gs)
	_w["gostep"] = gs
	# assembly
	v.add_child(UI.heading(T.t("Montage Schritt für Schritt")))
	var mp := PanelContainer.new()
	mp.add_theme_stylebox_override("panel", UI.box(UI.FIELD, UI.LINE, 12, 10, 1))
	v.add_child(mp)
	var mv := VBoxContainer.new()
	mv.add_theme_constant_override("separation", 6)
	mp.add_child(mv)
	var sn := UI.small("")
	mv.add_child(sn)
	_w["snr"] = sn
	var stt := Label.new()
	stt.add_theme_font_override("font", UI.heading_font())
	stt.add_theme_font_size_override("font_size", 15)
	stt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	mv.add_child(stt)
	_w["stitle"] = stt
	var stx := UI.small("", UI.TXT)
	stx.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stx.custom_minimum_size = Vector2(300, 0)
	mv.add_child(stx)
	_w["stext"] = stx
	var br := HBoxContainer.new()
	br.add_theme_constant_override("separation", 6)
	mv.add_child(br)
	var bp := Button.new()
	bp.text = "◀ " + T.t("Zurück")
	bp.pressed.connect(prev_step)
	br.add_child(bp)
	_w["prev"] = bp
	var bn := Button.new()
	bn.text = T.t("Weiter") + " ▶"
	bn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	UI.primary(bn)
	bn.pressed.connect(next_step)
	br.add_child(bn)
	_w["next"] = bn
	var be := Button.new()
	be.text = T.t("Ende")
	be.tooltip_text = T.t("Montage beenden – alle Teile zeigen")
	be.pressed.connect(func(): set_step(0))
	br.add_child(be)
	_w["end"] = be
	v.add_child(UI.small(T.t("Anleitung, Materialliste und Druckdateien: MoveEye → Mehr → «Gehäuse & Bau» (hardware/gehaeuse/ im Repository).")))
	for k in ["name", "bom", "pstep"]:
		(_w[k] as Label).text = ""


func _check(parent: Control, text: String, cb: Callable) -> CheckButton:
	var c := CheckButton.new()
	c.text = text
	c.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	c.custom_minimum_size = Vector2(300, 0)
	c.toggled.connect(cb)
	parent.add_child(c)
	return c


# ---- the little world ----------------------------------------------------------------------------------------------------
func _build_world() -> void:
	world = Node3D.new()
	vp.add_child(world)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("#1b2430")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.62, 0.66, 0.72)
	env.ambient_light_energy = 0.55
	var we := WorldEnvironment.new()
	we.environment = env
	world.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, -30, 0)
	sun.light_energy = 1.1
	world.add_child(sun)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-20, 150, 0)
	fill.light_energy = 0.45
	world.add_child(fill)
	var grid := MeshInstance3D.new()                    # a work bench under the case
	var pm := PlaneMesh.new()
	pm.size = Vector2(0.9, 0.7)
	grid.mesh = pm
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color("#2a3442")
	gm.roughness = 0.9
	grid.material_override = gm
	var mf := GH.manifest()
	grid.position = Vector3(0, -(float(mf.get("kippachse_ueber_boden_m", 0.1258)) + float(mf.get("fuesse_m", 0.006))) - 0.0005, 0.045)
	world.add_child(grid)
	_w["bench"] = grid
	cam = Camera3D.new()
	cam.fov = 40.0
	cam.near = 0.01
	cam.far = 10.0
	world.add_child(cam)
	var man := GH.manifest()
	var ms := GH.load_parts("gehaeuse.glb")
	for e in man.get("teile", []):
		var id := str(e.get("id", ""))
		if not ms.has(id):
			continue
		var mi: MeshInstance3D = ms[id]
		var src: Material = mi.mesh.surface_get_material(0) if mi.mesh != null and mi.mesh.get_surface_count() > 0 else null
		var m := StandardMaterial3D.new()
		m.albedo_color = src.albedo_color if src is BaseMaterial3D else Color.from_string(str(e.get("farbe", "#888888")), Color.GRAY)
		m.roughness = 0.6
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		mi.material_override = m
		world.add_child(mi)
		parts[id] = {"mi": mi, "e": e, "mat": m, "base": m.albedo_color}
	for k in ms:
		if (ms[k] as MeshInstance3D).get_parent() == null:
			(ms[k] as MeshInstance3D).free()
	if parts.is_empty():
		var l := UI.small(T.t("Die Modelle fehlen (inhalte/gehaeuse/) – werkzeuge/gehaeuse_bauen.py --sim"), UI.ORG)
		l.position = Vector2(20, 20)
		vpc.add_child(l)
	_place_cam()


func _place_cam() -> void:
	if cam == null:
		return
	var b := Basis.from_euler(Vector3(deg_to_rad(-pitch), deg_to_rad(yaw), 0))
	cam.position = target + b * Vector3(0, 0, dist)
	cam.look_at(target, Vector3.UP)


func set_view(y: float, p: float, d: float) -> void:
	yaw = y
	pitch = clampf(p, -80.0, 85.0)
	dist = clampf(d, 0.12, 2.0)
	target = Vector3(0, -0.06, 0.04)
	_place_cam()


func _on_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton:
		var mb := ev as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			dist = clampf(dist * 0.9, 0.12, 2.0)
			_place_cam()
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			dist = clampf(dist / 0.9, 0.12, 2.0)
			_place_cam()
		elif mb.pressed:
			_btn = mb.button_index
			_down = mb.position
			_drag = mb.position
		else:
			if _btn == MOUSE_BUTTON_LEFT and mb.position.distance_to(_down) < 5.0:
				var id := pick_at(mb.position)
				select(id)
			_btn = 0
	elif ev is InputEventMouseMotion and _btn != 0:
		var mm := ev as InputEventMouseMotion
		var dd: Vector2 = mm.position - _drag
		_drag = mm.position
		if _btn == MOUSE_BUTTON_LEFT:
			yaw -= dd.x * 0.4
			pitch = clampf(pitch + dd.y * 0.3, -80.0, 85.0)
		else:
			var b := cam.global_transform.basis
			target += (-b.x * dd.x + b.y * dd.y) * dist * 0.0016
		_place_cam()
	elif ev is InputEventMagnifyGesture:
		dist = clampf(dist / (ev as InputEventMagnifyGesture).factor, 0.12, 2.0)
		_place_cam()


func _unhandled_key_input(e: InputEvent) -> void:
	if is_open() and e is InputEventKey and e.pressed and (e as InputEventKey).keycode == KEY_ESCAPE:
		close()
		get_viewport().set_input_as_handled()


# ---- picking -------------------------------------------------------------------------------------------------------------
func pick_at(pos: Vector2) -> String:
	"""the part under the mouse (SubViewport coordinates); with «durchsichtig» the inner parts first"""
	if cam == null:
		return ""
	var o := cam.project_ray_origin(pos)
	var d := cam.project_ray_normal(pos)
	var best := ""
	var best_t := INF
	for pass_ in [0, 1]:
		for id in parts:
			var p: Dictionary = parts[id]
			var mi: MeshInstance3D = p["mi"]
			if not mi.visible:
				continue
			var druck := _is_print(id)
			if xray and pass_ == 0 and druck:
				continue
			var inv := mi.global_transform.affine_inverse()
			var lo: Vector3 = inv * o
			var ld: Vector3 = (inv.basis * d).normalized()
			var aabb: AABB = mi.mesh.get_aabb().grow(0.002)
			if aabb.intersects_ray(lo, ld) == null:
				continue
			if not p.has("faces"):
				p["faces"] = mi.mesh.get_faces()
			var fs: PackedVector3Array = p["faces"]
			for i in range(0, fs.size(), 3):
				var hit = Geometry3D.ray_intersects_triangle(lo, ld, fs[i], fs[i + 1], fs[i + 2])
				if hit != null:
					var tt := (hit as Vector3).distance_to(lo)
					if tt < best_t:
						best_t = tt
						best = id
		if best != "" or not xray:
			break
	return best


func select(id: String) -> void:
	sel = id if parts.has(id) else ""
	_paint()


func part_info(id: String) -> Dictionary:
	var r = rows.get(id)
	if r == null:
		return {}
	var out := {"id": id, "name": T.t(str(r[2])), "art": str(r[1]), "file": str(r[5])}
	var b = DATA.BOM.get(str(r[3]))
	if b != null:
		out["bom"] = {"id": str(r[3]), "qty": str(b[0]), "name": T.t(str(b[1])), "nr": str(b[2]), "group": T.t(str(b[3]))}
	var s := int(r[4])
	if s > 0:
		out["step"] = s
		out["step_title"] = T.t(str(DATA.SCHRITTE[s - 1][0]))
	return out


# ---- what is shown -------------------------------------------------------------------------------------------------------
func set_explode(v: float) -> void:
	explode = clampf(v, 0.0, 1.0)
	target = Vector3(0, -0.06 + 0.17 * explode, 0.04)    # the exploded case is higher: keep it in the picture
	dist = maxf(dist, 0.62 + 0.5 * explode)
	_place_cam()
	_paint()


func set_xray(on: bool) -> void:
	xray = on
	_paint()


func set_inner(on: bool) -> void:
	inner = on
	_paint()


func set_v52(on: bool) -> void:
	v52 = on
	_paint()


func set_real_case(on: bool) -> void:
	if main.gehaeuse != null:
		main.gehaeuse.set_on(on)
	_paint()


func set_step(n: int) -> void:
	step = clampi(n, 0, DATA.SCHRITTE.size())
	_anim = 0.0 if step > 1 else 1.0
	if step > 0:
		sel = ""
		_focus_step()
	_paint()


func next_step() -> void:
	set_step(mini(step + 1, DATA.SCHRITTE.size()) if step > 0 else 1)


func prev_step() -> void:
	set_step(maxi(step - 1, 1))


func _focus_step() -> void:
	"""look at the parts of the step"""
	var c := Vector3.ZERO
	var n := 0
	for id in parts:
		if int(rows.get(id, [0, 0, 0, 0, 0])[4]) == step:
			c += Vector3(parts[id]["e"]["mitte"][0], parts[id]["e"]["mitte"][1], parts[id]["e"]["mitte"][2])
			n += 1
	if n > 0 and step > 1:
		target = target.lerp(c / n, 0.6)
	else:
		target = Vector3(0, -0.06, 0.04)
	_place_cam()


func _is_print(id: String) -> bool:
	"""a printed part (v5.1 «druck» or a part of a variant with its own print file, e.g. 01_Unterteil_v52)"""
	var r = rows.get(id)
	return r != null and (str(r[1]) == "druck" or (r.size() > 5 and str(r[5]) != ""))


func _shown(id: String) -> bool:
	var r = rows.get(id)
	if r == null:
		return false
	var art := str(r[1])
	if art == "v52":
		return v52 and step == 0 and (inner or _is_print(id) or bool(parts[id]["e"].get("aussen", false)))
	if v52 and step == 0 and repl.has(id) and parts.has(repl[id]):
		return false                                  # v5.2: replaced by the real part of the variant (lower part, ...)
	if step == 1:
		return art == "druck"
	if step > 1 and int(r[4]) > step:
		return false
	if not inner and art != "druck" and not bool(parts[id]["e"].get("aussen", false)):
		return false
	return true


func _paint() -> void:
	if not is_open():
		return
	for id in parts:
		var p: Dictionary = parts[id]
		var mi: MeshInstance3D = p["mi"]
		mi.visible = _shown(id)
		var r: Array = rows.get(id, ["", "", "", "", 0])
		var k := explode
		if step == 1:
			k = 1.0
		elif step > 1 and int(r[4]) == step:
			k = maxf(explode, 1.0 - _ease(_anim)) + 0.0
		var ev: Array = p["e"].get("explosion", [0, 0, 0])
		var off := Vector3(float(ev[0]), float(ev[1]), float(ev[2])) * k
		if step > 1 and int(r[4]) == step:
			off += Vector3(0, 0.06, 0) * (1.0 - _ease(_anim))
		mi.position = off
		var m: StandardMaterial3D = p["mat"]
		var col: Color = p["base"]
		var see := xray and _is_print(id)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if see else BaseMaterial3D.TRANSPARENCY_DISABLED
		m.albedo_color = Color(col, DRUCK_ALPHA if see else 1.0)
		m.no_depth_test = false
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if see else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		var hi: bool = id == sel or (step > 1 and int(r[4]) == step)
		m.emission_enabled = hi
		if hi:
			m.emission = UI.ACC if id == sel else Color("#f59a4a")
			m.emission_energy_multiplier = 0.55 if id == sel else 0.35
	(_w["explode"] as HSlider).set_value_no_signal(explode)
	(_w["xray"] as CheckButton).set_pressed_no_signal(xray)
	(_w["inner"] as CheckButton).set_pressed_no_signal(inner)
	(_w["v52"] as CheckButton).set_pressed_no_signal(v52)
	(_w["real"] as CheckButton).set_pressed_no_signal(main.gehaeuse != null and main.gehaeuse.on)
	var inf := part_info(sel)
	(_w["name"] as Label).text = str(inf.get("name", T.t("Teil anklicken – oder einen Schritt der Montage wählen.")))
	var bt := ""
	if inf.has("bom"):
		bt = T.t("Materialliste: %s %s") % [inf["bom"]["qty"], inf["bom"]["name"]]
		if str(inf["bom"]["nr"]) != "":
			bt += " · " + str(inf["bom"]["nr"])
		bt += "  (" + str(inf["bom"]["group"]) + ")"
	elif sel != "":
		bt = T.t("nicht in der Materialliste")
	if str(inf.get("file", "")) != "":
		bt += ("\n" if bt != "" else "") + T.t("Druckdatei: %s") % str(inf["file"])
	(_w["bom"] as Label).text = bt
	(_w["pstep"] as Label).text = (T.t("Montage: Schritt %d – %s") % [int(inf["step"]), str(inf["step_title"])]) if inf.has("step") else (T.t("Variante v5.2 – noch nicht in der Montage v5.1") if str(inf.get("art", "")) == "v52" else "")
	(_w["gostep"] as Button).visible = inf.has("step") and int(inf.get("step", 0)) != step
	var n: int = DATA.SCHRITTE.size()
	if step == 0:
		(_w["snr"] as Label).text = T.t("%d Schritte") % n
		(_w["stitle"] as Label).text = T.t("Montage starten")
		(_w["stext"] as Label).text = T.t("«Weiter» zeigt Schritt 1. Die Teile jedes Schritts fliegen an ihren Platz.")
		(_w["next"] as Button).text = T.t("Montage starten") + " ▶"
	else:
		var s: Array = DATA.SCHRITTE[step - 1]
		(_w["snr"] as Label).text = T.t("Schritt %d von %d") % [step, n]
		(_w["stitle"] as Label).text = T.t(str(s[0]))
		(_w["stext"] as Label).text = T.t(str(s[1]))
		(_w["next"] as Button).text = T.t("Weiter") + " ▶"
	(_w["prev"] as Button).disabled = step <= 1
	(_w["next"] as Button).disabled = step >= n
	(_w["end"] as Button).visible = step > 0


static func _ease(t: float) -> float:
	var x := clampf(t, 0.0, 1.0)
	return 1.0 - pow(1.0 - x, 3.0)


func _process(dt: float) -> void:
	if is_open() and _anim < 1.0:
		_anim = minf(1.0, _anim + dt / 1.1)
		_paint()


# ---- /control ------------------------------------------------------------------------------------------------------------
func control(d: Dictionary) -> Dictionary:
	var dd := str(d.get("do", "info"))
	if dd != "info" and dd != "close" and dd != "real_case" and not is_open():
		open()
	match dd:
		"open":
			pass
		"close":
			close()
		"explode":
			set_explode(float(d.get("value", 1.0)))
		"xray":
			set_xray(bool(d.get("on", true)))
		"inner":
			set_inner(bool(d.get("on", true)))
		"v52":
			set_v52(bool(d.get("on", true)))
		"pick":
			select(str(d.get("id", "")))
		"click":                                      # tests: a click at x / y (0..1 of the 3D picture) - like the mouse
			var sz: Vector2 = Vector2(vp.size) if vp != null else Vector2.ONE
			select(pick_at(Vector2(float(d.get("x", 0.5)) * sz.x, float(d.get("y", 0.5)) * sz.y)))
		"step":
			set_step(int(d.get("n", 1)))
			if bool(d.get("done", false)):
				_anim = 1.0
				_paint()
		"next":
			next_step()
		"prev":
			prev_step()
		"view":
			set_view(float(d.get("yaw", yaw)), float(d.get("pitch", pitch)), float(d.get("dist", dist)))
		"real_case":
			if main.gehaeuse != null:
				main.gehaeuse.set_on(bool(d.get("on", true)))
			_paint()
	return info()


func info() -> Dictionary:
	var vis := 0
	for id in parts:
		if (parts[id]["mi"] as MeshInstance3D).visible:
			vis += 1
	return {"ok": true, "open": is_open(), "version": DATA.VERSION, "step": step, "steps": DATA.SCHRITTE.size(),
			"step_title": T.t(str(DATA.SCHRITTE[step - 1][0])) if step > 0 else "", "sel": sel, "part": part_info(sel),
			"explode": explode, "xray": xray, "inner": inner, "v52": v52, "parts": parts.size(), "visible": vis,
			"real_case": main.gehaeuse.info() if main.gehaeuse != null else {}, "source_sha": DATA.QUELLE_SHA.substr(0, 12)}
