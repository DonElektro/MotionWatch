extends Node
## «Bauen» (Mehr → Bauen, früher «Werkstatt»; MoveEye: Mehr → «Bauen» /build; Pakete «real-gehaeuse» und «real-bauen»,
## 01.11.2026): das Gehäuse v5.1 mit dem Innenleben in einer eigenen kleinen 3D-Welt, dazu dieselben Reiter wie in MoveEye:
## Übersicht · Teile · Einkauf · Drucken · Montage · Verkabeln · Software · Inbetriebnahme · Fehlersuche · Wartung (Daten aus
## werkstatt_daten.gd BAU, erzeugt aus hardware/gehaeuse/bau.json – dieselbe Quelle wie MoveEye). «Mein Bau» (Variante und
## Checkliste) liegt lokal in user://bau_mein.json.
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
##           pick (id) | step (n, 0 = frei) | next | prev | view (yaw, pitch, dist) | real_case (on) | tab (name) |
##           variant (gehaeuse | akku | mover, value) | done (id, on) | fertig (pkg) | order (pkg)}
## «Fertig kaufen» (Besitzer 01.11.2026): ein schmaler Hinweis oben im Fenster (wie MoveEye /build, Teil 639zj; Texte und
## Pakete aus ui_gemeinsam.json «fertig»): Paket Basis / Komplett / Autark wählen, «Fertig bestellen (Anfrage)» schliesst
## «Bauen» und öffnet die Rückmeldung (feedback.gd open_order) mit Art «Bestellung fertiges Gerät» und dem Paket.

const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
const DATA = preload("res://scripts/werkstatt_daten.gd")
const GH = preload("res://scripts/gehaeuse.gd")
const DRUCK_ALPHA := 0.16
const FH = preload("res://scripts/fehler_hilfe.gd")
const EINZEL = preload("res://scripts/werkstatt_einzel.gd")   # Einzelteil-Vorschau, Druckplatten (real-einzelteil-vorschau)
const TABS := [["uebersicht", "Übersicht"], ["teile", "Teile"], ["einkauf", "Einkauf"], ["drucken", "Drucken"], ["montage", "Montage"],
		["verkabeln", "Verkabeln"], ["software", "Software"], ["inbetrieb", "Inbetriebnahme"], ["fehler", "Fehlersuche"], ["wartung", "Wartung"]]
const MEIN_PFAD := "user://bau_mein.json"
const UG = preload("res://scripts/ui_gemeinsam.gd")
const Icons = preload("res://scripts/mehr_icons.gd")
const ART_COL := {"i2c": Color("#3b82f6"), "pwm": Color("#f59e0b"), "gpio": Color("#10b981"), "strom": Color("#ef4444"),
		"usb": Color("#8b5cf6"), "csi": Color("#ec4899"), "spi": Color("#14b8a6"), "audio": Color("#a3a3a3")}

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
var tab := "uebersicht"            # real-bauen: the tab (the same ids as MoveEye /build)
var mein := {"var": {}, "done": []}  # «Mein Bau»: variant + checklist (user://bau_mein.json)
var node_sel := ""                 # Verkabeln: the module that is lit
var fertig_pkg := ""               # «Fertig kaufen»: the package chosen in the hint ("" = the standard one)
var last_order := {}               # tests: what «Fertig bestellen (Anfrage)» handed to the feedback
var einzel = null                  # werkstatt_einzel.gd: single part view, print plates
var min_dist := 0.12               # zoom limit (smaller for a single small part)


func _ready() -> void:
	layer = CanvasLayer.new()
	layer.layer = 61
	add_child(layer)
	for r in DATA.TEILE:
		rows[str(r[0])] = r
		if r.size() > 6 and str(r[6]) != "":
			repl[str(r[6])] = str(r[0])
	_mein_load()
	einzel = EINZEL.new(self)


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
	set_v52(str(_vars().get("gehaeuse", "")) == "v52")
	set_tab(tab)


func close() -> void:
	if is_open():
		win.queue_free()
	win = null
	parts = {}
	sel = ""
	if einzel != null:
		einzel.closed()
	min_dist = 0.12


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
	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 8)
	win.add_child(root)
	var hd := HBoxContainer.new()
	hd.add_theme_constant_override("separation", 10)
	root.add_child(hd)
	var tl := Label.new()
	tl.text = _title_text()
	_w["title"] = tl
	tl.add_theme_font_override("font", UI.heading_font())
	tl.add_theme_font_size_override("font_size", 17)
	hd.add_child(tl)
	var pr := UI.small("")
	pr.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(pr)
	_w["prog"] = pr
	var x := Button.new()
	x.text = "✕"
	x.flat = true
	x.tooltip_text = T.t("Schliessen (Esc)")
	x.pressed.connect(close)
	hd.add_child(x)
	_fertig_bar(root)
	var tsc := ScrollContainer.new()
	tsc.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	tsc.custom_minimum_size = Vector2(0, 42)
	root.add_child(tsc)
	var tb := HBoxContainer.new()
	tb.add_theme_constant_override("separation", 6)
	tsc.add_child(tb)
	for td in TABS:
		var b := Button.new()
		b.text = T.t(str(td[1]))
		b.toggle_mode = true
		var tid := str(td[0])
		b.pressed.connect(func(): set_tab(tid))
		tb.add_child(b)
		_w["tab_" + tid] = b
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 12)
	h.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(h)
	_w["body3d"] = h
	var pg := ScrollContainer.new()
	pg.size_flags_vertical = Control.SIZE_EXPAND_FILL
	pg.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	pg.visible = false
	root.add_child(pg)
	_w["page"] = pg
	var pv := VBoxContainer.new()
	pv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pv.add_theme_constant_override("separation", 6)
	pg.add_child(pv)
	_w["pv"] = pv
	vpc = SubViewportContainer.new()
	vpc.stretch = true
	vpc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vpc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	vpc.custom_minimum_size = Vector2(320, 240)
	vpc.gui_input.connect(_on_input)
	vpc.set_meta("rad_zoom", "werkstatt")              # tasten.gd: + / − = the wheel of the 3D view
	var holder := Control.new()                         # real-einzelteil-vorschau: 3D picture + «Wo es hingehört» bottom right
	holder.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	holder.size_flags_vertical = Control.SIZE_EXPAND_FILL
	holder.custom_minimum_size = Vector2(320, 240)
	h.add_child(holder)
	vpc.set_anchors_preset(Control.PRESET_FULL_RECT)
	holder.add_child(vpc)
	vp = SubViewport.new()
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_2X if not GH.Quality.lite() else Viewport.MSAA_DISABLED
	vp.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
	vpc.add_child(vp)
	einzel.build_view(holder)
	var side := ScrollContainer.new()
	side.custom_minimum_size = Vector2(350, 0)
	side.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	h.add_child(side)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 8)
	side.add_child(v)
	# real-bauen: the variant (the same choice as MoveEye «Deine Variante»)
	v.add_child(UI.heading(T.t("Deine Variante")))
	for vg in DATA.BAU.get("varianten", []):
		var vr := HBoxContainer.new()
		v.add_child(vr)
		var vl := Label.new()
		vl.text = T.t(str(vg["titel"]))
		vl.custom_minimum_size = Vector2(70, 0)
		vr.add_child(vl)
		var ob := OptionButton.new()
		ob.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		ob.clip_text = true
		for o in vg["werte"]:
			ob.add_item(T.t(str(o["name"])))
		var gid := str(vg["id"])
		ob.item_selected.connect(func(i): set_variant(gid, str(vg["werte"][i]["id"])))
		vr.add_child(ob)
		_w["var_" + gid] = ob
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
	rb.pressed.connect(func():
		if einzel.mode != "":
			einzel.frame()
		else:
			set_view(145.0, 24.0, 0.62))
	v.add_child(rb)
	var plb := Button.new()                              # real-einzelteil-vorschau: the plates of the variant as in the 3MF
	plb.text = T.t("Druckplatten")
	plb.toggle_mode = true
	plb.pressed.connect(func(): einzel.set_mode("platten" if einzel.mode != "platten" else "", "", false, einzel.plate))
	v.add_child(plb)
	_w["plates_btn"] = plb
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
	var so := Button.new()                               # real-einzelteil-vorschau
	so.text = T.t("Nur dieses Teil zeigen")
	so.visible = false
	so.pressed.connect(func(): einzel.set_mode("teil", sel))
	iv.add_child(so)
	_w["solo_btn"] = so
	einzel.build_ui(v)
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
	var sd := CheckBox.new()
	sd.text = T.t("erledigt")
	sd.toggled.connect(func(on):
		if step > 0:
			set_done("m:%d" % step, on))
	mv.add_child(sd)
	_w["sdone"] = sd
	var be := Button.new()
	be.text = T.t("Ende")
	be.tooltip_text = T.t("Montage beenden – alle Teile zeigen")
	be.pressed.connect(func(): set_step(0))
	br.add_child(be)
	_w["end"] = be
	var mo := Button.new()
	mo.text = "↗ " + T.t("In MoveEye öffnen")
	mo.pressed.connect(func(): _open_mw("/build#" + tab))
	v.add_child(mo)
	for k in ["name", "bom", "pstep"]:
		(_w[k] as Label).text = ""


# ---- «Fertig kaufen»: the hint at the top (the same as MoveEye /build) ---------------------------------------------------------
func _fertig_bar(parent: Control) -> void:
	if UG.fertig().is_empty():
		return
	var L := T.lang()
	if fertig_pkg == "":
		fertig_pkg = str(UG.fertig_paket("", L).get("id", ""))
	var pc := PanelContainer.new()
	var st := UI.box(Color(UI.ACC, 0.08), Color(UI.ACC, 0.45), 10, 8, 1)
	st.border_width_left = 4
	st.border_color = Color(UI.ACC, 0.45)
	pc.add_theme_stylebox_override("panel", st)
	parent.add_child(pc)
	_w["fertig"] = pc
	var h := HFlowContainer.new()
	h.add_theme_constant_override("h_separation", 8)
	h.add_theme_constant_override("v_separation", 6)
	pc.add_child(h)
	var ic := Icons.icon("cart", UI.ACC, 18.0)
	ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(ic)
	var tx := Label.new()
	tx.text = UG.fertig_text("hint", L)
	tx.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tx.custom_minimum_size = Vector2(320, 0)
	tx.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tx.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(tx)
	_w["fertig_text"] = tx
	var seg := HBoxContainer.new()
	seg.add_theme_constant_override("separation", 0)
	seg.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(seg)
	for p in UG.fertig_pakete():
		var pid := str(p.get("id", ""))
		var pk := UG.fertig_paket(pid, L)
		var b := Button.new()
		b.text = str(pk.get("name", pid))
		b.tooltip_text = str(pk.get("desc", "")) + " · " + UG.fertig_text("price", L)
		b.toggle_mode = true
		b.focus_mode = Control.FOCUS_NONE
		b.add_theme_font_size_override("font_size", 13)
		b.pressed.connect(func(): set_fertig(pid))
		seg.add_child(b)
		_w["fertig_" + pid] = b
	var pr := UI.small("")
	pr.autowrap_mode = TextServer.AUTOWRAP_OFF
	pr.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(pr)
	_w["fertig_desc"] = pr
	var ob := Button.new()
	ob.text = UG.fertig_text("button", L)
	ob.size_flags_vertical = Control.SIZE_SHRINK_CENTER         # a normal button (dezent), like MoveEye class «sec»
	ob.pressed.connect(func(): order())
	h.add_child(ob)
	_w["fertig_btn"] = ob
	_paint_fertig()


func _paint_fertig() -> void:
	"""the chosen package blue (like MoveEye .seg .on), next to it its short description · «Preise auf Anfrage»"""
	var L := T.lang()
	var dl = _w.get("fertig_desc")
	if dl != null and is_instance_valid(dl):
		(dl as Label).text = str(UG.fertig_paket(fertig_pkg, L).get("desc", "")) + " · " + UG.fertig_text("price", L)
	for p in UG.fertig_pakete():
		var b = _w.get("fertig_" + str(p.get("id", "")))
		if b != null and is_instance_valid(b):
			var on: bool = str(p.get("id", "")) == fertig_pkg
			(b as Button).button_pressed = on
			var st := UI.box(UI.ACC if on else UI.BTN2, UI.ACC if on else UI.LINE, 8, 6, 1)
			for s_ in ["normal", "hover", "pressed", "focus"]:
				(b as Button).add_theme_stylebox_override(s_, st)


func set_fertig(pid: String) -> void:
	fertig_pkg = str(UG.fertig_paket(pid, T.lang()).get("id", fertig_pkg))
	if is_open():
		_paint_fertig()


func order(pid := "") -> Dictionary:
	"""«Fertig bestellen (Anfrage)»: close «Bauen», open the feedback with kind «order» and the package (feedback.gd)"""
	if pid != "":
		set_fertig(pid)
	var fb = mehr.feedback if mehr != null and "feedback" in mehr else (main.feedback_dlg if "feedback_dlg" in main else null)
	last_order = {"pkg": fertig_pkg, "kind": str(UG.fertig().get("kind", "order")), "dialog": fb != null}
	if fb == null or not fb.has_method("open_order"):
		return {"ok": false, "error": "no feedback dialog", "pkg": fertig_pkg}
	close()
	fb.open_order(fertig_pkg, "Bauen")
	return {"ok": true, "pkg": fertig_pkg, "kind": last_order["kind"]}


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
	einzel.build_world()


func _place_cam() -> void:
	if cam == null:
		return
	var b := Basis.from_euler(Vector3(deg_to_rad(-pitch), deg_to_rad(yaw), 0))
	cam.position = target + b * Vector3(0, 0, dist)
	cam.look_at(target, Vector3.UP)


func set_view(y: float, p: float, d: float) -> void:
	yaw = y
	pitch = clampf(p, -80.0, 85.0)
	dist = clampf(d, min_dist, 2.0)
	target = Vector3(0, -0.06, 0.04)
	_place_cam()


func _on_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton:
		var mb := ev as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			dist = clampf(dist * 0.9, min_dist, 2.0)
			_place_cam()
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			dist = clampf(dist / 0.9, min_dist, 2.0)
			_place_cam()
		elif mb.pressed:
			_btn = mb.button_index
			_down = mb.position
			_drag = mb.position
		else:
			if _btn == MOUSE_BUTTON_LEFT and mb.position.distance_to(_down) < 5.0:
				if einzel.mode == "platten":
					einzel.tap(mb.position)
				elif einzel.mode == "":
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
		dist = clampf(dist / (ev as InputEventMagnifyGesture).factor, min_dist, 2.0)
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
	if einzel != null and einzel.mode != "":
		einzel.set_mode("")
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
		out["step_title"] = T.t(str(_schritt(s)[0]))
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
	if _w.has("title") and is_instance_valid(_w["title"]):
		(_w["title"] as Label).text = _title_text()
	_paint()


func _title_text() -> String:
	"""Modellname (v5.1 / v5.2) und automatisch «Stand MoveEye X.Y.Z» aus der laufenden Version (main.VERSION, Wunsch des Besitzers)"""
	var t := T.t("Bauen – Gehäuse v%s") % ("5.2" if v52 else DATA.VERSION)
	var ver := str(main.get("VERSION")) if main != null and main.get("VERSION") != null else ""
	return t + ("  ·  " + T.t("Stand MoveEye %s") % ver if ver != "" else "")


func _schritt(n: int) -> Array:
	"""[Titel, Text] von Schritt n (1…): v5.2 (Standard) oder die Texte von v5.1, wenn v5.1 gewählt ist (bau.json «v51»)"""
	var s: Array = DATA.SCHRITTE[n - 1]
	return [s[0], s[1]] if v52 or s.size() < 4 else [s[2], s[3]]


func set_real_case(on: bool) -> void:
	if main.gehaeuse != null:
		main.gehaeuse.set_on(on)
	_paint()


func set_step(n: int) -> void:
	if einzel != null and einzel.mode != "" and is_open():
		einzel.set_mode("")
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


func _dev() -> bool:
	return str(_vars().get("akku", "")) == "entwicklung"


func _is_print(id: String) -> bool:
	"""a printed part (v5.1 «druck» or a part of a variant with its own print file, e.g. 01_Unterteil_v52)"""
	var r = rows.get(id)
	return r != null and (str(r[1]) == "druck" or (r.size() > 5 and str(r[5]) != ""))


func _shown(id: String) -> bool:
	var r = rows.get(id)
	if r == null:
		return false
	var art := str(r[1])
	# real-v52-standard (01.11.2026): v5.2 is the standard - its parts are in the assembly steps too (bau.json «schritt»)
	if art == "v52" and not v52:
		return false
	if art == "dev" and not _dev():                   # Entwicklungs-Variante ohne Akku (Sockel 13 statt UPS HAT + Akkus)
		return false
	if parts.has(id) and str(parts[id]["e"].get("ohne", "")) != "":
		return false                                  # 12 Blindstopfen: nur in der Szene (Gerät ohne Weitwinkel), der Bau zeigt die Kamera
	if repl.has(id) and parts.has(repl[id]):
		var ra := str((rows.get(repl[id], ["", ""]) as Array)[1])
		if (ra == "v52" and v52) or (ra == "dev" and _dev()):
			return false                              # replaced by the part of the variant (lower part v5.2, socket ...)
	if step == 1:
		return _is_print(id)
	if step > 1 and int(r[4]) > step:
		return false
	if not inner and not _is_print(id) and not bool(parts[id]["e"].get("aussen", false)):
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
		var s: Array = _schritt(step)
		(_w["snr"] as Label).text = T.t("Schritt %d von %d") % [step, n]
		(_w["stitle"] as Label).text = T.t(str(s[0]))
		(_w["stext"] as Label).text = T.t(str(s[1]))
		(_w["next"] as Button).text = T.t("Weiter") + " ▶"
	(_w["prev"] as Button).disabled = step <= 1
	(_w["next"] as Button).disabled = step >= n
	(_w["end"] as Button).visible = step > 0
	(_w["sdone"] as CheckBox).visible = step > 0
	(_w["sdone"] as CheckBox).set_pressed_no_signal(step > 0 and ("m:%d" % step) in mein["done"])
	var vv := _vars()
	for vg in DATA.BAU.get("varianten", []):
		var ob: OptionButton = _w.get("var_" + str(vg["id"]))
		for i in range((vg["werte"] as Array).size()):
			if str(vg["werte"][i]["id"]) == str(vv.get(vg["id"], "")):
				ob.select(i)
	for td in TABS:
		(_w["tab_" + str(td[0])] as Button).set_pressed_no_signal(str(td[0]) == tab)
	_prog()
	einzel.after_paint()


static func _ease(t: float) -> float:
	var x := clampf(t, 0.0, 1.0)
	return 1.0 - pow(1.0 - x, 3.0)


func _process(dt: float) -> void:
	if is_open() and _anim < 1.0:
		_anim = minf(1.0, _anim + dt / 1.1)
		_paint()


# ---- real-bauen: the tabs, «Mein Bau» ------------------------------------------------------------------------------------
func _mein_load() -> void:
	if FileAccess.file_exists(MEIN_PFAD):
		var d = JSON.parse_string(FileAccess.get_file_as_string(MEIN_PFAD))
		if d is Dictionary:
			mein["var"] = d.get("var", {}) if d.get("var", {}) is Dictionary else {}
			mein["done"] = d.get("done", []) if d.get("done", []) is Array else []


func _mein_save() -> void:
	var f := FileAccess.open(MEIN_PFAD, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(mein))


func _vars() -> Dictionary:
	var v: Dictionary = (DATA.BAU.get("variante_standard", {}) as Dictionary).duplicate()
	for k in mein["var"]:
		v[k] = mein["var"][k]
	return v


func _ok(w) -> bool:
	var s := str(w) if w != null else ""
	return s == "" or s in _vars().values()


func all_ids() -> Array:
	"""the points of the checklist in this variant (the same ids as MoveEye /build)"""
	var ids := []
	var ex: Dictionary = DATA.BAU.get("bom_extra", {})
	for id in DATA.BOM:
		var e: Dictionary = ex.get(id, {})
		if _ok(e.get("wenn")) and not bool(e.get("optional", false)):
			ids.append("e:" + str(id))
	for p in DATA.BAU.get("druck", {}).get("teile", []):
		if _ok(p.get("wenn")):
			ids.append("d:" + str(p["datei"]))
	for i in range(DATA.SCHRITTE.size()):
		ids.append("m:%d" % (i + 1))
	var xs: Array = DATA.BAU.get("extra_schritte", [])
	for i in range(xs.size()):
		if _ok(xs[i].get("wenn")):
			ids.append("x:%d" % i)
	for c in DATA.BAU.get("verkabelung", {}).get("verbindungen", []):
		if _ok(c.get("wenn")):
			ids.append("k:" + str(c["id"]))
	for i in range((DATA.BAU.get("software", []) as Array).size()):
		ids.append("s:%d" % i)
	for i in range((DATA.BAU.get("inbetriebnahme", []) as Array).size()):
		ids.append("i:%d" % i)
	return ids


func _prog() -> void:
	if not is_open() or not _w.has("prog"):
		return
	var ids := all_ids()
	var n := 0
	for i in ids:
		if i in mein["done"]:
			n += 1
	(_w["prog"] as Label).text = T.t("Mein Bau") + ": " + T.t("%d von %d erledigt") % [n, ids.size()] + "  ·  " + T.t("Im Simulator gespeichert (auf diesem Rechner).")


func set_done(id: String, on: bool) -> void:
	var d: Array = mein["done"]
	if on and not (id in d):
		d.append(id)
	elif not on:
		d.erase(id)
	_mein_save()
	_prog()


func set_variant(g: String, v: String) -> void:
	(mein["var"] as Dictionary)[g] = v
	_mein_save()
	if g == "gehaeuse":
		set_v52(v == "v52")
	elif g == "akku":
		_paint()
	if is_open():
		set_tab(tab)


func set_tab(id: String) -> void:
	var ok := false
	for td in TABS:
		if str(td[0]) == id:
			ok = true
	tab = id if ok else "uebersicht"
	if not is_open():
		return
	var three := tab == "uebersicht" or tab == "montage"
	(_w["body3d"] as Control).visible = three
	(_w["page"] as Control).visible = not three
	if tab == "montage" and step == 0:
		set_step(1)
	if not three:
		_page()
	_paint()


func _open_mw(path: String) -> void:
	var b := FH.mw_base(main)
	if b == "":
		if mehr != null and mehr.has_method("toast"):
			mehr.toast(T.t("MoveEye nicht verbunden – die Seite öffnet sich, sobald MoveEye verbunden ist."))
		return
	OS.shell_open(b + path)


func _lbl(parent: Control, text: String, col := UI.TXT, big := false) -> Label:
	var l := Label.new()
	l.text = text
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_color_override("font_color", col)
	if big:
		l.add_theme_font_override("font", UI.heading_font())
		l.add_theme_font_size_override("font_size", 15)
	parent.add_child(l)
	return l


func _chk(parent: Control, id: String, text: String) -> CheckBox:
	var c := CheckBox.new()
	c.text = text
	c.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	c.custom_minimum_size = Vector2(300, 0)
	c.button_pressed = id in mein["done"]
	c.toggled.connect(func(on): set_done(id, on))
	parent.add_child(c)
	return c


func _card(parent: Control) -> VBoxContainer:
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", UI.box(UI.FIELD, UI.LINE, 10, 8, 1))
	parent.add_child(pc)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	pc.add_child(v)
	return v


func _marks(parent: Control, o: Dictionary) -> void:
	var t := ""
	if str(o.get("wenn", "")) != "" and o.get("wenn") != null:
		t += "⚑ " + _vname(str(o["wenn"])) + "  "
	if bool(o.get("optional", false)):
		t += T.t("optional") + "  "
	if t != "":
		_lbl(parent, t, UI.MUT)
	if o.get("unklar") != null and str(o.get("unklar", "")) != "":
		_lbl(parent, "⚠ " + T.t("unklar") + ": " + T.t(str(o["unklar"])), UI.ORG)


func _vname(w: String) -> String:
	for vg in DATA.BAU.get("varianten", []):
		for o in vg["werte"]:
			if str(o["id"]) == w:
				return T.t(str(o["name"]))
	return w


func _page() -> void:
	var pv: VBoxContainer = _w["pv"]
	for c in pv.get_children():
		c.queue_free()
	var mo := Button.new()
	mo.text = "↗ " + T.t("In MoveEye öffnen")
	mo.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	mo.pressed.connect(func(): _open_mw("/build#" + tab))
	match tab:
		"teile":
			pv.add_child(UI.heading(T.t("Teile")))
			var grp := ""
			for id in DATA.BOM:
				var b: Array = DATA.BOM[id]
				var e: Dictionary = DATA.BAU["bom_extra"].get(id, {})
				if not _ok(e.get("wenn")):
					continue
				if str(b[3]) != grp:
					grp = str(b[3])
					_lbl(pv, T.t(grp), UI.ACC, true)
				var r := HBoxContainer.new()
				pv.add_child(r)
				var l := _lbl(r, "%s  %s%s" % [T.t(str(b[0])), T.t(str(b[1])), ("  · " + T.t(str(b[2]))) if str(b[2]) != "" else ""])
				l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				for tr_ in DATA.TEILE:
					if str(tr_[3]) == str(id):
						var tid := str(tr_[0])
						var sb := Button.new()
						sb.text = T.t("Teil im 3D zeigen")
						sb.pressed.connect(func():
							set_tab("uebersicht")
							select(tid))
						r.add_child(sb)
						break
		"einkauf":
			pv.add_child(UI.heading(T.t("Einkauf")))
			_lbl(pv, T.t("Preise sind Schätzungen in CHF ohne Versand – beim Händler nachsehen."), UI.MUT)
			var br := HBoxContainer.new()
			pv.add_child(br)
			var cb := Button.new()
			cb.text = T.t("CSV in die Zwischenablage")
			cb.pressed.connect(func(): _csv())
			br.add_child(cb)
			br.add_child(mo)
			var sum := 0.0
			var H: Dictionary = DATA.BAU.get("haendler", {})
			for id in DATA.BOM:
				var b: Array = DATA.BOM[id]
				var e: Dictionary = DATA.BAU["bom_extra"].get(id, {})
				if not _ok(e.get("wenn")):
					continue
				if not bool(e.get("optional", false)):
					sum += float(e.get("preis", 0.0))
				var v := _card(pv)
				_chk(v, "e:" + str(id), "%s  %s  –  %.2f" % [T.t(str(b[0])), T.t(str(b[1])), float(e.get("preis", 0.0))])
				if str(b[2]) != "":
					_lbl(v, T.t(str(b[2])), UI.MUT)
				if str(e.get("alt", "")) != "":
					_lbl(v, T.t("Alternative") + ": " + T.t(str(e["alt"])), UI.MUT)
				_marks(v, e)
				var lr := HBoxContainer.new()
				v.add_child(lr)
				var hks := [str(e.get("haendler", ""))]
				if not ("galaxus" in hks):
					hks.append("galaxus")
				for hk in hks:
					if H.has(hk):
						var u := str(H[hk]["suche"]).replace("{q}", str(e.get("suche", "")).uri_encode())
						var lb := LinkButton.new()
						lb.text = T.t("Suchen bei") + " " + T.t(str(H[hk]["name"]))
						lb.pressed.connect(func(): OS.shell_open(u))
						lr.add_child(lb)
			_lbl(pv, T.t("Gesamt (Schätzung)") + ": %.2f" % sum, UI.TXT, true)
		"drucken":
			pv.add_child(UI.heading(T.t("Drucken")))
			pv.add_child(mo)
			var D: Dictionary = DATA.BAU.get("druck", {})
			var hrs := 0.0
			for p in D.get("teile", []):
				if not _ok(p.get("wenn")):
					continue
				hrs += float(p["zeit_h"])
				var v := _card(pv)
				var nm := str(p["datei"])
				for tr_ in DATA.TEILE:
					if str(tr_[5]) == nm:
						nm = T.t(str(tr_[2]))
						break
				_chk(v, "d:" + str(p["datei"]), "%s  × %d" % [nm, int(p["stueck"])])
				_lbl(v, "%s %d %%  ·  %s %d  ·  %s %s  ·  %s %s mm  ·  %s %s  ·  %s %s" % [T.t("Füllung"), int(p["fuellung"]), T.t("Wände"), int(p["waende"]),
						T.t("Stützen"), "✓" if bool(p["stuetzen"]) else T.t("keine"), T.t("Schicht"), str(p["schicht"]), T.t("liegt auf"), T.t(str(p["liegt"])),
						T.t("Druckzeit"), T.t("ca. %s h") % str(p["zeit_h"])], UI.MUT)
			_lbl(pv, T.t("Druckzeit") + ": " + T.t("ca. %s h") % str(snappedf(hrs, 0.1)) + "  ·  " + T.t(str(D.get("zeit_hinweis", ""))), UI.TXT, true)
			pv.add_child(UI.heading(T.t("Hinweise für den Bambu-Drucker")))
			for hh in D.get("hinweise", []):
				_lbl(pv, "•  " + T.t(str(hh)))
		"verkabeln":
			pv.add_child(UI.heading(T.t("Verkabeln")))
			_lbl(pv, T.t("Pins und Kanäle stammen aus dem Code von MoveEye und aus der Doku. Unklares ist markiert."), UI.MUT)
			_lbl(pv, T.t("Tippe ein Modul an: seine Verbindungen leuchten."), UI.MUT)
			pv.add_child(_plan())
			var ab := Button.new()
			ab.text = T.t("Alle Verbindungen")
			ab.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
			ab.pressed.connect(func():
				node_sel = ""
				_page())
			pv.add_child(ab)
			var K: Dictionary = DATA.BAU["verkabelung"]["knoten"]
			for c in DATA.BAU["verkabelung"]["verbindungen"]:
				if not _ok(c.get("wenn")) or (node_sel != "" and str(c["von"]) != node_sel and str(c["nach"]) != node_sel):
					continue
				var v := _card(pv)
				var cc := _chk(v, "k:" + str(c["id"]), T.t(str(K[c["von"]]["name"])) + "  →  " + T.t(str(K[c["nach"]]["name"])))
				cc.add_theme_color_override("font_color", ART_COL.get(str(c["art"]), UI.TXT))
				_lbl(v, T.t(str(c["pins"])), UI.MUT)
				_marks(v, c)
		"software":
			pv.add_child(UI.heading(T.t("Software")))
			var sw: Array = DATA.BAU.get("software", [])
			for i in range(sw.size()):
				var s: Dictionary = sw[i]
				var v := _card(pv)
				_chk(v, "s:%d" % i, "%d.  %s" % [i + 1, T.t(str(s["titel"]))])
				_lbl(v, T.t(str(s["text"])), UI.MUT)
				if s.has("befehl"):
					var te := TextEdit.new()
					te.text = str(s["befehl"])
					te.editable = false
					te.custom_minimum_size = Vector2(300, 22 * (str(s["befehl"]).count("\n") + 1) + 12)
					v.add_child(te)
					var cp := Button.new()
					cp.text = T.t("Kopieren")
					cp.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
					var bf := str(s["befehl"])
					cp.pressed.connect(func(): DisplayServer.clipboard_set(bf))
					v.add_child(cp)
			var b := FH.mw_base(main)
			if b != "":
				_lbl(pv, T.t("QR-Code zu dieser MoveEye-Seite"), UI.TXT, true)
				pv.add_child(FH.qr_view(b + "/"))
				_lbl(pv, b + "/", UI.MUT)
		"inbetrieb":
			pv.add_child(UI.heading(T.t("Inbetriebnahme")))
			var ib: Array = DATA.BAU.get("inbetriebnahme", [])
			for i in range(ib.size()):
				var s: Dictionary = ib[i]
				var v := _card(pv)
				_chk(v, "i:%d" % i, "%d.  %s" % [i + 1, T.t(str(s["titel"]))])
				_lbl(v, T.t(str(s["text"])), UI.MUT)
				if s.has("link"):
					var ob := Button.new()
					ob.text = "↗ " + T.t("In MoveEye öffnen")
					ob.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
					var lk := str(s["link"])
					ob.pressed.connect(func(): _open_mw(lk))
					v.add_child(ob)
		"fehler":
			pv.add_child(UI.heading(T.t("Fehlersuche")))
			for fid in DATA.BAU.get("fehlersuche", []):
				var e: Dictionary = FH.entry(str(fid))
				if e.is_empty():
					continue
				var v := _card(pv)
				_lbl(v, ("⛔ " if str(e.get("stufe", "")) == "bad" else "⚠ ") + str(FH.tx(e.get("titel", {}))), UI.TXT, true)
				_lbl(v, str(FH.tx(e.get("text", {}))), UI.MUT)
				var st = FH.tx(e.get("schritte", {}))
				if st is Array:
					for i in range((st as Array).size()):
						_lbl(v, "%d. %s" % [i + 1, str(st[i])])
				var hb := Button.new()
				hb.text = "↗ " + T.t("Hilfe öffnen")
				hb.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
				var fpath := "/hilfe/fehler/" + str(fid)
				hb.pressed.connect(func(): _open_mw(fpath))
				v.add_child(hb)
		"wartung":
			pv.add_child(UI.heading(T.t("Was verschleisst und wann prüfen")))
			for w in DATA.BAU.get("wartung", []):
				if not _ok(w.get("wenn")):
					continue
				var v := _card(pv)
				_lbl(v, T.t(str(w["teil"])) + "  ·  " + T.t(str(w["wann"])), UI.TXT, true)
				_lbl(v, T.t(str(w["was"])), UI.MUT)
	if tab in ["teile", "verkabeln", "fehler", "wartung"]:
		pv.add_child(mo)
	else:
		if mo.get_parent() == null:
			mo.queue_free()
	if tab == "drucken" or tab == "einkauf":
		pv.add_child(UI.heading(T.t("Sicherheit")))
		for sf in DATA.BAU.get("sicherheit", []):
			if _ok(sf.get("wenn")):
				_lbl(pv, "⚠  " + T.t(str(sf["text"])), UI.MUT)


func _csv() -> String:
	"""the shopping list as CSV (also to the clipboard and into user://MoveEye_Einkauf.csv)"""
	var H: Dictionary = DATA.BAU.get("haendler", {})
	var q := func(s): return "\"" + str(s).replace("\"", "\"\"") + "\""
	var lines := [q.call(_title_text()), ";".join([q.call(T.t("erledigt")), q.call(T.t("Menge")), q.call(T.t("Bezeichnung")), q.call(T.t("Teilenummer")), q.call(T.t("Preis")), q.call(T.t("Alternative")), q.call(T.t("Händler")), q.call(T.t("Suchlink")), q.call(T.t("optional"))])]
	for id in DATA.BOM:
		var b: Array = DATA.BOM[id]
		var e: Dictionary = DATA.BAU["bom_extra"].get(id, {})
		if not _ok(e.get("wenn")):
			continue
		var h: Dictionary = H.get(str(e.get("haendler", "")), {})
		lines.append(";".join([q.call("x" if ("e:" + str(id)) in mein["done"] else ""), q.call(T.t(str(b[0]))), q.call(T.t(str(b[1]))), q.call(T.t(str(b[2]))),
				q.call("%.2f" % float(e.get("preis", 0.0))), q.call(T.t(str(e.get("alt", "")))), q.call(T.t(str(h.get("name", "")))),
				q.call(str(h.get("suche", "")).replace("{q}", str(e.get("suche", "")).uri_encode())), q.call("x" if bool(e.get("optional", false)) else "")]))
	var csv := "\r\n".join(lines)
	DisplayServer.clipboard_set(csv)
	var f := FileAccess.open("user://MoveEye_Einkauf.csv", FileAccess.WRITE)
	if f != null:
		f.store_string(csv)
		f = null
		if mehr != null and mehr.has_method("toast"):
			mehr.toast(T.t("CSV gespeichert: %s") % ProjectSettings.globalize_path("user://MoveEye_Einkauf.csv"))
	return csv


func _plan() -> Control:
	"""the wiring plan: modules as boxes, the connections as coloured lines; a click lights one module"""
	var V: Dictionary = DATA.BAU["verkabelung"]
	var K: Dictionary = V["knoten"]
	var c := Control.new()
	c.custom_minimum_size = Vector2(960, 470)
	c.mouse_filter = Control.MOUSE_FILTER_STOP
	var W := 8.2
	var Hh := 4.4
	var font := ThemeDB.fallback_font
	var pos := func(k) -> Vector2:
		return Vector2(float(K[k]["x"]) * W + 4, float(K[k]["y"]) * Hh + 12)
	c.draw.connect(func():
		c.draw_rect(Rect2(Vector2.ZERO, c.size), UI.FIELD)
		for cn in V["verbindungen"]:
			if not _ok(cn.get("wenn")) or not _ok(K[cn["von"]].get("wenn")) or not _ok(K[cn["nach"]].get("wenn")):
				continue
			var on: bool = node_sel == "" or str(cn["von"]) == node_sel or str(cn["nach"]) == node_sel
			var col: Color = ART_COL.get(str(cn["art"]), UI.MUT)
			col.a = 0.9 if on else 0.15
			c.draw_line(pos.call(cn["von"]) + Vector2(63, 13), pos.call(cn["nach"]) + Vector2(63, 13), col, 3.0 if on and node_sel != "" else 1.6, true)
		for k in K:
			if not _ok(K[k].get("wenn")):
				continue
			var p: Vector2 = pos.call(k)
			c.draw_rect(Rect2(p, Vector2(126, 26)), UI.PANEL)
			c.draw_rect(Rect2(p, Vector2(126, 26)), UI.ACC if k == node_sel else UI.LINE, false, 2.0 if k == node_sel else 1.0)
			c.draw_string(font, p + Vector2(5, 17), T.t(str(K[k]["name"])), HORIZONTAL_ALIGNMENT_LEFT, 118, 12, UI.TXT))
	c.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			var hit := ""
			for k in K:
				if hit == "" and _ok(K[k].get("wenn")) and Rect2(pos.call(k), Vector2(126, 26)).has_point(ev.position):
					hit = str(k)
			if hit != "":
				node_sel = "" if node_sel == hit else hit
				_page())
	return c


# ---- /control ------------------------------------------------------------------------------------------------------------
func control(d: Dictionary) -> Dictionary:
	var dd := str(d.get("do", "info"))
	if dd == "order":                              # «Fertig bestellen (Anfrage)» (tests and the phone page)
		return order(str(d.get("pkg", "")))
	if dd != "info" and dd != "close" and dd != "real_case" and dd != "done" and dd != "variant" and dd != "fertig" and not is_open():
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
		"solo":                                      # real-einzelteil-vorschau: only this part (flat = as printed)
			einzel.set_mode("teil", str(d.get("id", sel)), bool(d.get("flat", false)))
		"plates":                                    # the print plates of the variant (n = 0, 1 …)
			einzel.set_mode("platten", "", false, int(d.get("n", 0)))
		"whole":
			einzel.set_mode("")
		"plate_tap":                                 # tests: a part of the plate (id or only the print file)
			einzel.plate_tap(str(d.get("id", "")), str(d.get("datei", "")))
		"where":
			einzel.where()
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
		"tab":                                        # real-bauen: one of the tabs (uebersicht … wartung)
			set_tab(str(d.get("name", "uebersicht")))
		"variant":
			set_variant(str(d.get("group", "gehaeuse")), str(d.get("value", "")))
		"fertig":
			set_fertig(str(d.get("pkg", "")))
		"done":
			set_done(str(d.get("id", "")), bool(d.get("on", true)))
			if is_open() and not (tab == "uebersicht" or tab == "montage"):
				_page()
	return info()


func info() -> Dictionary:
	var vis := 0
	for id in parts:
		if (parts[id]["mi"] as MeshInstance3D).visible:
			vis += 1
	return {"ok": true, "open": is_open(), "version": DATA.VERSION, "step": step, "steps": DATA.SCHRITTE.size(),
			"step_title": T.t(str(_schritt(step)[0])) if step > 0 else "", "sel": sel, "part": part_info(sel),
			"explode": explode, "xray": xray, "inner": inner, "v52": v52, "parts": parts.size(), "visible": vis,
			"real_case": main.gehaeuse.info() if main.gehaeuse != null else {}, "source_sha": DATA.QUELLE_SHA.substr(0, 12),
			"tab": tab, "variant": _vars(), "done": (mein["done"] as Array).size(), "todo": all_ids().size(),
			"fertig": {"shown": is_open() and _w.has("fertig") and is_instance_valid(_w["fertig"]), "pkg": fertig_pkg,
				"text": str((_w["fertig_text"] as Label).text) if is_open() and _w.has("fertig_text") and is_instance_valid(_w["fertig_text"]) else "",
				"button": str((_w["fertig_btn"] as Button).text) if is_open() and _w.has("fertig_btn") and is_instance_valid(_w["fertig_btn"]) else ""},
			"last_order": last_order, "einzel": einzel.info() if einzel != null else {}}
