extends Node
## «Frei erkunden mit eigener Figur», Etappe 3 (Besitzer 21.11.2026): was die Sachen im Rucksack tun, und die Kraft.
## Ein Kind von explore_person.gd («person»); der Rucksack selbst: erkunden_rucksack.gd (main.ex_rucksack).
##   * Stirnlampe (L): ein / aus (das Licht der Figur - MoveEye sieht es nachts).
##   * Feldstecher (B): Blick durch den Feldstecher, Zoom 2–10× (Rad, + / −, Knöpfe), Tiere und Menschen im Bild mit Name und
##     Distanz, Foto (Leertaste / Knopf, user://erkunden_fotos/), Nachtsicht (N / Knopf). B / Esc = zurück.
##   * Kompass: Leiste oben mit der Richtung; O merkt den Ort hier - die Nadel zeigt dorthin, mit Distanz.
##   * Taschenuhr: die Zeit oben; , / . = eine halbe Stunde zurück / vor (Knöpfe im Rucksack-Menü).
##   * Seil: an einer Kante (1–40 m tief) mit E abseilen - sanft hinunter statt umzukehren.
##   * Pickel: auf Schnee und Eis kein Tempoverlust, Kanten bis 3,5 m hoch (ohne: 2,2 m).
##   * Wanderstöcke: weniger müde («Echt»).
##   * Mini-Stativ + Powerbank: MoveEye hier aufstellen (schaut, wohin die Figur schaut) - weggehen und anschleichen.
##   * Dach (Zelt / Tarp / Biwaksack) + Schlafsack: hier übernachten - das Lager steht, die Figur schläft, weiter am Morgen
##     (7 Uhr), Kraft wieder voll. Ohne Isomatte / im Winter ohne Winterschlafsack: kalt (nur «Echt»).
##   * Kocher + Essen: warm essen (mehr Kraft und Wärme); Essen; Wasser trinken, am Bach / See auffüllen.
##   * Jacke: weniger Kälte; Erste Hilfe: nach einem harten Sturz wieder normal gehen; Hut, Karabiner: nur zum Aussehen.
##   * Kraft (main.ex_kraft_echt): «Entspannt» (ab Werk) = nie müde, kein Hunger, kein Durst; «Echt» = Kraft, Hunger, Durst und
##     Wärme sinken (Tempo, Steigung, Gewicht über «bequem», Rennen, Schwimmen, Nacht / Kälte), Ausruhen (stehen, sitzen,
##     liegen), Essen, Trinken und Schlafen geben sie zurück. Wenig davon = langsamer, ohne Kraft kein Rennen. Niemand stirbt.
## Menü «Rucksack» (R / Knopf am Rand): alles, was man gerade tun kann (oder warum nicht).

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const RS = preload("res://scripts/erkunden_rucksack.gd")
const Welt = preload("res://scripts/erkunden_welt.gd")

const ZOOM_MIN := 2.0
const ZOOM_MAX := 10.0
const FOTO_DIR := "user://erkunden_fotos"
const MASKE_SH := """
shader_type canvas_item;
uniform float aspect = 1.78;
void fragment() {
	vec2 p = (UV - 0.5) * vec2(aspect, 1.0);
	float r = min(0.44, aspect * 0.27);
	float d = min(length(p - vec2(-r * 0.72, 0.0)), length(p - vec2(r * 0.72, 0.0)));
	COLOR = vec4(0.0, 0.0, 0.0, 0.94 * smoothstep(r - 0.012, r + 0.012, d));
}
"""
const NACHT_SH := """
shader_type canvas_item;
uniform sampler2D scr : hint_screen_texture, filter_linear_mipmap;
void fragment() {
	vec3 c = texture(scr, SCREEN_UV).rgb;
	float l = clamp(dot(c, vec3(0.3, 0.59, 0.11)) * 4.0 + 0.04, 0.0, 1.0);
	float n = fract(sin(dot(SCREEN_UV * 640.0 + TIME, vec2(12.9898, 78.233))) * 43758.5453) - 0.5;
	vec2 d = SCREEN_UV - 0.5;
	float v = 1.0 - dot(d, d) * 1.6;
	COLOR = vec4(vec3(l * 0.55, l, l * 0.5) * v + n * 0.06, 1.0);
}
"""

var person
var main
var kraft := 100.0
var hunger := 100.0                  # 100 = satt
var durst := 100.0                   # 100 = nicht durstig
var waerme := 100.0
var verletzt := false
var fernglas := false
var zoom := 4.0
var nacht := false
var ziel = null                      # Vector3: the place marked with O (the compass needle)
var lager: Node3D = null             # the camp of the night
var _y_hoch := 0.0                   # the highest point of the last jump (a hard fall)
var _layer: CanvasLayer
var _hud: Control
var _kompass: Control
var _uhr: Label
var _bars: Control
var _menu: PanelContainer
var _menu_box: VBoxContainer
var _fg: Control                     # binocular overlay
var _fg_nacht: ColorRect
var _fg_maske: ColorRect
var _fg_text: Label
var _fg_labels: Control
var _fg_knoepfe: HFlowContainer
var _msg: Label
var _msg_bis := 0.0
var _fotos := 0


func _ready() -> void:
	process_priority = 97
	_layer = CanvasLayer.new()
	_layer.layer = 8
	add_child(_layer)
	_hud = Control.new()
	_hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layer.add_child(_hud)
	_kompass = Control.new()
	_kompass.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_kompass.draw.connect(_kompass_draw)
	_hud.add_child(_kompass)
	_uhr = Label.new()
	_uhr.add_theme_font_size_override("font_size", 15)
	_uhr.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_uhr.add_theme_constant_override("outline_size", 5)
	_uhr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.add_child(_uhr)
	_bars = Control.new()
	_bars.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bars.draw.connect(_bars_draw)
	_hud.add_child(_bars)
	_msg = Label.new()
	_msg.add_theme_font_size_override("font_size", 16)
	_msg.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_msg.add_theme_constant_override("outline_size", 6)
	_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_msg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_msg.visible = false
	_hud.add_child(_msg)
	# the binoculars
	_fg = Control.new()
	_fg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fg.visible = false
	_layer.add_child(_fg)
	_fg_nacht = ColorRect.new()
	_fg_nacht.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fg_nacht.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sm := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = NACHT_SH
	sm.shader = sh
	_fg_nacht.material = sm
	_fg_nacht.visible = false
	_fg.add_child(_fg_nacht)
	_fg_maske = ColorRect.new()                                   # the two round lenses, dark round them
	_fg_maske.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fg_maske.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mm := ShaderMaterial.new()
	var msh := Shader.new()
	msh.code = MASKE_SH
	mm.shader = msh
	_fg_maske.material = mm
	_fg.add_child(_fg_maske)
	_fg_text = Label.new()
	_fg_text.add_theme_font_size_override("font_size", 18)
	_fg_text.add_theme_color_override("font_color", Color(0.85, 1.0, 0.85))
	_fg_text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fg.add_child(_fg_text)
	_fg_labels = Control.new()
	_fg_labels.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fg_labels.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fg_labels.draw.connect(_fg_labels_draw)
	_fg.add_child(_fg_labels)
	_fg_knoepfe = HFlowContainer.new()                           # two rows on the phone
	_fg_knoepfe.add_theme_constant_override("h_separation", 8)
	_fg_knoepfe.add_theme_constant_override("v_separation", 8)
	_fg_knoepfe.alignment = FlowContainer.ALIGNMENT_CENTER
	_fg.add_child(_fg_knoepfe)
	for e in [["minus", "−"], ["plus", "+"], ["foto", "Foto"], ["nacht", "Nachtsicht"], ["zurueck", "Zurück"]]:
		var b := Button.new()
		b.name = str(e[0])
		b.set_meta("t", str(e[1]))
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(64, 48)
		var id := str(e[0])
		b.pressed.connect(func(): _fg_knopf(id))
		_fg_knoepfe.add_child(b)
	# the menu «Rucksack»
	_menu = PanelContainer.new()
	_menu.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL.r, UI.PANEL.g, UI.PANEL.b, 0.95), UI.LINE, 12, 10, 1))
	_menu.visible = false
	_layer.add_child(_menu)
	_menu_box = VBoxContainer.new()
	_menu_box.add_theme_constant_override("separation", 6)
	_menu.add_child(_menu_box)


func rs() -> Dictionary:
	return RS.norm(main.get("ex_rucksack"))


func hat(id: String) -> bool:
	"""in the pack - the equipment of the figure (Etappe 2) counts too"""
	var r := rs()
	if RS.hat(r, id):
		return true
	var fd: Dictionary = person.figur_wahl()
	return id in ["stirnlampe", "stoecke", "feldstecher"] and bool(fd.get(id, false))


func echt() -> bool:
	return bool(main.get("ex_kraft_echt"))


func sag(text: String, secs := 3.0) -> void:
	_msg.text = text
	_msg.visible = true
	_msg_bis = main.now() + secs


func _an() -> bool:
	return person != null and person.ok() and bool(person.active) and person.ex != null and bool(person.ex.on)


func _nimm(id: String) -> bool:
	"""uses up one (food, water, first aid)"""
	var r := rs()
	if not RS.hat(r, id):
		return false
	main.ex_rucksack = RS.dazu(r, id, -1)["d"]
	main._settings_dirty = true
	return true


# ---- the actions -----------------------------------------------------------------------------------------------------------
func lampe() -> void:
	if not hat("stirnlampe"):
		sag(T.t("Keine Stirnlampe im Rucksack"))
		return
	var a: Node3D = person.actor
	if a.get("lamp") == null:
		a.add_lamp("head")
		person.begleiter.mw_anwenden(true)
	var l: SpotLight3D = a.lamp
	var an: bool = not bool(a.get_meta("ew_lampe", false))
	a.set_meta("ew_lampe", an)
	l.visible = an
	l.light_energy = 3.0 if an else 0.0
	if a.get("lamp_mat") != null:
		(a.lamp_mat as StandardMaterial3D).emission_energy_multiplier = 3.0 if an else 0.0
	sag(T.t("Stirnlampe an") if an else T.t("Stirnlampe aus"), 1.5)


func lampe_an() -> bool:
	return person.ok() and bool(person.actor.get_meta("ew_lampe", false))


func feldstecher(v: bool) -> void:
	if v and not hat("feldstecher"):
		sag(T.t("Kein Feldstecher im Rucksack"))
		return
	fernglas = v
	_fg.visible = v
	if not v:
		nacht = false
		_fg_nacht.visible = false
		main.view_cam.fov = 62.0
	person._eye_yaw = float(person.actor.heading)


func tu_fernglas(id: String) -> void:
	_fg_knopf(id)


func _fg_knopf(id: String) -> void:
	match id:
		"minus":
			set_zoom(zoom - 1.0)
		"plus":
			set_zoom(zoom + 1.0)
		"foto":
			foto()
		"nacht":
			nacht = not nacht
			_fg_nacht.visible = nacht
		"zurueck":
			feldstecher(false)


func set_zoom(z: float) -> void:
	zoom = clampf(z, ZOOM_MIN, ZOOM_MAX)


func foto() -> String:
	"""the picture as it is on the screen now - saved in user://erkunden_fotos/"""
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FOTO_DIR))
	_fotos += 1
	var nm := "%s/erkunden_%s_%d.png" % [FOTO_DIR, Time.get_datetime_string_from_system().replace(":", "-"), _fotos]
	var img: Image = get_viewport().get_texture().get_image() if DisplayServer.get_name() != "headless" else null
	if img == null:
		return ""                                         # (no picture without a renderer - tests)
	img.save_png(nm)
	sag(T.t("Foto gespeichert"), 2.0)
	return nm


func ort_merken() -> void:
	ziel = person.figur.pos()
	sag(T.t("Ort gemerkt – der Kompass zeigt hierher") if hat("kompass") else T.t("Ort gemerkt"), 2.5)


func uhr(stunden: float) -> void:
	if not hat("taschenuhr"):
		sag(T.t("Keine Taschenuhr im Rucksack"))
		return
	main.set_hour(fposmod(float(main.hour()) + stunden, 24.0))
	sag(_zeit(), 1.5)


func _zeit() -> String:
	var h: float = fposmod(float(main.hour()), 24.0)
	return "%02d:%02d" % [int(h), int(fmod(h, 1.0) * 60.0)]


func essen() -> void:
	if not _nimm("essen"):
		sag(T.t("Kein Proviant mehr"))
		return
	hunger = minf(100.0, hunger + 45.0)
	kraft = minf(100.0, kraft + 15.0)
	sag(T.t("Gegessen"), 1.5)


func trinken() -> void:
	if not _nimm("wasser"):
		sag(T.t("Kein Wasser mehr – am Bach oder See auffüllen"))
		return
	durst = minf(100.0, durst + 50.0)
	sag(T.t("Getrunken"), 1.5)


func am_wasser() -> bool:
	if not person.ok():
		return false
	var p: Vector3 = person.figur.pos()
	var fw: Vector3 = person.figur.vorne()
	for d in [0.0, 1.0, 2.0]:
		if not Welt.wasser(main, p + fw * float(d)).is_empty():
			return true
	return false


func auffuellen() -> void:
	if not am_wasser():
		sag(T.t("Hier ist kein Wasser"))
		return
	var r := rs()
	var n := 0
	while RS.anzahl(r, "wasser") < int(RS.item("wasser")[5]):
		var e := RS.dazu(r, "wasser", 1)
		if not bool(e["ok"]):
			break
		r = e["d"]
		n += 1
	main.ex_rucksack = r
	main._settings_dirty = true
	durst = 100.0
	sag(T.t("Getrunken und %d Liter aufgefüllt") % n, 2.0)


func kochen() -> void:
	if not hat("kocher"):
		sag(T.t("Kein Kocher im Rucksack"))
		return
	if not _nimm("essen"):
		sag(T.t("Kein Proviant mehr"))
		return
	hunger = 100.0
	kraft = minf(100.0, kraft + 35.0)
	waerme = minf(100.0, waerme + 35.0)
	sag(T.t("Warm gegessen – das tut gut"), 2.0)


func erste_hilfe() -> void:
	if not _nimm("apotheke"):
		sag(T.t("Keine Erste Hilfe im Rucksack"))
		return
	verletzt = false
	kraft = minf(100.0, kraft + 10.0)
	sag(T.t("Verbunden – es geht wieder"), 2.0)


func moveeye_aufstellen() -> void:
	if not hat("ministativ"):
		sag(T.t("Dafür braucht es das Mini-Stativ"))
		return
	if not hat("powerbank"):
		sag(T.t("Ohne Powerbank hält MoveEye nicht lange – nimm sie mit"))
		return
	var p: Vector3 = person.figur.pos() + person.figur.vorne() * 0.6
	var q: Vector2 = main.keep_out(Vector2(p.x, p.z), 0.4, false)
	main.rig.position = Vector3(q.x, main.ground_y(q.x, q.y), q.y)
	main.rig.rotation.y = float(person.actor.heading)
	sag(T.t("MoveEye steht hier – jetzt weggehen und anschleichen!"), 3.0)


func kann_uebernachten() -> String:
	"""'' = it works here, else why not"""
	var r := rs()
	if not RS.hat_eins(r, RS.DACH):
		return T.t("Dafür braucht es ein Zelt, ein Tarp oder einen Biwaksack")
	if not RS.hat_eins(r, RS.SCHLAF):
		return T.t("Dafür braucht es einen Schlafsack")
	if person.wasser != "":
		return T.t("Nicht im Wasser")
	return ""


func uebernachten() -> void:
	var w := kann_uebernachten()
	if w != "":
		sag(w)
		return
	var r := rs()
	if lager != null and is_instance_valid(lager):
		lager.queue_free()
	lager = _lager_bauen(r)
	person.set_haltung("liegen")
	var kalt: bool = not RS.hat(r, "isomatte") or (_winter() and not RS.hat(r, "winterschlafsack"))
	var h: float = float(main.hour())
	main.set_hour(7.0)                                       # (the next morning)
	kraft = 100.0
	hunger = maxf(30.0, hunger - 25.0)
	durst = maxf(30.0, durst - 25.0)
	waerme = 55.0 if kalt and echt() else 100.0
	sag(T.t("Gut geschlafen – guten Morgen!") if not (kalt and echt()) else T.t("Kalt geschlafen – mit Isomatte / Winterschlafsack wäre es wärmer"), 4.0)
	person.begleiter.sag(T.t("Guten Morgen! Das Lager bleibt stehen, bis du weitergehst."), 5.0)
	set_meta("geschlafen_ab", h)


func _lager_bauen(r: Dictionary) -> Node3D:
	"""a simple tent / tarp / bivy where the figure lies (MoveEye sees it, warm in the thermal picture)"""
	var n := Node3D.new()
	n.name = "erkunden_lager"
	main.add_child(n)
	var p: Vector3 = person.figur.pos()
	n.position = Vector3(p.x, main.ground_y(p.x, p.z), p.z)
	n.rotation.y = float(person.actor.heading)
	var col := Color(0.85, 0.45, 0.15)
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	if RS.hat_eins(r, ["einmannzelt", "kuppelzelt"]):
		var gross := RS.hat(r, "kuppelzelt")
		var pm := PrismMesh.new()
		pm.size = Vector3(1.6 if gross else 1.1, 1.2 if gross else 0.9, 2.3)
		main.add_mesh(n, pm, Vector3(0, pm.size.y * 0.5, -0.4), m, "tent")
	elif RS.hat(r, "tarp"):
		m.albedo_color = Color(0.25, 0.4, 0.3)
		main.add_mesh(n, main.box(2.0, 0.03, 2.4), Vector3(0, 1.0, -0.4), m, "tent", Vector3(0.0, 0.0, 0.25))
	else:
		m.albedo_color = Color(0.2, 0.3, 0.55)
		main.add_mesh(n, main.box(0.8, 0.25, 2.1), Vector3(0, 0.12, -0.5), m, "tent")
	return n


func lager_weg() -> void:
	if lager != null and is_instance_valid(lager):
		lager.queue_free()
	lager = null


func _winter() -> bool:
	return str(main.get("season")) == "winter" or str(main.weather) == "snow"


func auf_schnee() -> bool:
	"""snow or ice under the figure: winter, snowfall, a glacier / frozen lake of the Bergtal"""
	if _winter():
		return true
	if str(main.scene) == "bergtal" and main.scenes != null:
		var b = main.scenes.data.get("bergtal", null)
		if b != null and b.has_method("zone"):
			var v: Vector3 = b.V(person.figur.pos())
			return str(b.zone(v.x, v.z)) in ["glacier", "snow"]
	return false


# ---- rappelling --------------------------------------------------------------------------------------------------------------
func abgrund() -> Dictionary:
	"""a drop ahead of the figure (1–40 m): {von, kante, nach, h} or {}"""
	if not person.ok():
		return {}
	var p: Vector3 = person.figur.pos()
	var fw: Vector3 = person.figur.vorne()
	for dd in [0.6, 0.9, 1.3]:
		var q: Vector3 = p + fw * float(dd)
		var g: float = main.ground_y(q.x, q.z)
		var h := p.y - g
		if h > 1.0 and h < 40.0:
			var q2: Vector3 = p + fw * (float(dd) + 0.5)
			return {"kante": Vector3(q.x, p.y, q.z), "nach": Vector3(q2.x, main.ground_y(q2.x, q2.z), q2.z), "h": h}
	return {}


# ---- strength («Echt») ------------------------------------------------------------------------------------------------------
func tempo_faktor() -> float:
	"""× the speed of the figure (actor.gear_speed)"""
	var f := 1.0
	if auf_schnee() and not hat("pickel"):
		f *= 0.75
	if not echt():
		return f
	f *= lerpf(0.55, 1.0, clampf(kraft / 60.0, 0.0, 1.0))
	if hunger < 15.0:
		f *= 0.85
	if durst < 15.0:
		f *= 0.85
	if waerme < 20.0:
		f *= 0.85
	if verletzt:
		f *= 0.6
	return f


func darf_rennen() -> bool:
	return not echt() or (kraft > 15.0 and not verletzt)


func _kraft_tick(dt: float) -> void:
	var a: Node3D = person.actor
	var spd: float = float(a.cur_speed)
	var h: String = str(person.haltung)
	if not echt():
		kraft = 100.0
		hunger = 100.0
		durst = 100.0
		waerme = 100.0
		verletzt = false
		return
	var r := rs()
	var last: float = 1.0 + maxf(0.0, RS.gewicht(r) - RS.bequem(r)) / maxf(1.0, RS.bequem(r))
	var hoch: float = maxf(0.0, (person.figur.pos().y - float(get_meta("y_alt", person.figur.pos().y))) / maxf(dt, 0.001))
	set_meta("y_alt", person.figur.pos().y)
	var zehr: float = (0.12 * spd + (0.25 * maxf(0.0, spd - 2.0)) + 0.6 * minf(hoch, 1.5)) * last
	if person.wasser == "schwimmen":
		zehr += 0.6
	if hat("stoecke") and spd > 0.2:
		zehr *= 0.8
	var ruhe: float = 0.0
	if spd < 0.15:
		ruhe = {"sitzen": 1.4, "liegen": 1.8}.get(h, 0.6)
		if hunger < 10.0 or durst < 10.0:
			ruhe *= 0.3
	kraft = clampf(kraft - zehr * dt + ruhe * dt, 0.0, 100.0)
	hunger = clampf(hunger - dt * (0.05 + 0.02 * spd), 0.0, 100.0)
	durst = clampf(durst - dt * (0.07 + 0.03 * spd + (0.05 if spd > 2.5 else 0.0)), 0.0, 100.0)
	var kalt: float = 0.0
	if main.is_dark():
		kalt += 0.08
	if _winter():
		kalt += 0.15
	if str(main.weather) in ["rain", "snow"]:
		kalt += 0.1
	if person.wasser != "":
		kalt += 0.25
	if hat("jacke"):
		kalt *= 0.4
	waerme = clampf(waerme - kalt * dt + (0.2 if kalt < 0.05 else 0.0) * dt + (0.1 * dt if spd > 1.0 else 0.0), 0.0, 100.0)


func gelandet(fall: float) -> void:
	"""explore_person: the figure landed after a fall of fall metres"""
	if echt() and fall > 2.5 and not verletzt:
		verletzt = true
		kraft = maxf(0.0, kraft - 15.0)
		sag(T.t("Autsch! Hart gelandet – Erste Hilfe hilft") if hat("apotheke") else T.t("Autsch! Hart gelandet – langsam weiter"), 3.0)


# ---- the menu «Rucksack» ----------------------------------------------------------------------------------------------------
func menu(v: bool) -> void:
	if v and not _an():
		return
	_menu.visible = v
	if v:
		_menu_bauen()


func menu_offen() -> bool:
	return _menu.visible


func aktionen() -> Array:
	"""[id, text, possible, why not] - what the menu offers now"""
	var r := rs()
	var out := []
	out.append(["lampe", T.t("Stirnlampe aus") if lampe_an() else T.t("Stirnlampe an"), hat("stirnlampe"), T.t("Keine Stirnlampe im Rucksack")])
	out.append(["feldstecher", T.t("Feldstecher"), hat("feldstecher"), T.t("Kein Feldstecher im Rucksack")])
	out.append(["essen", T.t("Essen (%d)") % RS.anzahl(r, "essen"), RS.hat(r, "essen"), T.t("Kein Proviant mehr")])
	out.append(["kochen", T.t("Warm kochen"), RS.hat(r, "kocher") and RS.hat(r, "essen"), T.t("Braucht Kocher und Proviant")])
	out.append(["trinken", T.t("Trinken (%d L)") % RS.anzahl(r, "wasser"), RS.hat(r, "wasser"), T.t("Kein Wasser mehr")])
	out.append(["auffuellen", T.t("Wasser auffüllen"), am_wasser(), T.t("Nur am Bach oder See")])
	out.append(["erste_hilfe", T.t("Erste Hilfe"), RS.hat(r, "apotheke"), T.t("Keine Erste Hilfe im Rucksack")])
	var ab := abgrund()
	out.append(["abseilen", T.t("Abseilen (%d m)") % int(ab.get("h", 0.0)) if not ab.is_empty() else T.t("Abseilen"),
			RS.hat(r, "seil") and not ab.is_empty(), T.t("Braucht ein Seil und eine Kante vor dir") if ab.is_empty() or not RS.hat(r, "seil") else ""])
	var wu := kann_uebernachten()
	out.append(["uebernachten", T.t("Hier übernachten"), wu == "", wu])
	out.append(["moveeye", T.t("MoveEye hier aufstellen"), hat("ministativ") and hat("powerbank"), T.t("Braucht Mini-Stativ und Powerbank")])
	out.append(["ort", T.t("Ort merken (Kompass)"), true, ""])
	out.append(["uhr_zurueck", T.t("Uhr: ½ Stunde zurück"), hat("taschenuhr"), T.t("Keine Taschenuhr im Rucksack")])
	out.append(["uhr_vor", T.t("Uhr: ½ Stunde vor"), hat("taschenuhr"), T.t("Keine Taschenuhr im Rucksack")])
	out.append(["fotomodus", T.t("Fotomodus (P)"), true, ""])
	return out


func tu(id: String) -> void:
	match id:
		"lampe":
			lampe()
		"feldstecher":
			feldstecher(not fernglas)
		"essen":
			essen()
		"kochen":
			kochen()
		"trinken":
			trinken()
		"auffuellen":
			auffuellen()
		"erste_hilfe":
			erste_hilfe()
		"abseilen":
			person.abseilen()
		"uebernachten":
			uebernachten()
		"moveeye":
			moveeye_aufstellen()
		"ort":
			ort_merken()
		"uhr_zurueck":
			uhr(-0.5)
		"uhr_vor":
			uhr(0.5)
		"fotomodus":
			_menu.visible = false
			person.extras.fotomodus(true)
	if _menu.visible:
		_menu_bauen()


func _menu_bauen() -> void:
	for c in _menu_box.get_children():
		c.queue_free()
	var kopf := HBoxContainer.new()
	_menu_box.add_child(kopf)
	var ti := Label.new()
	ti.text = T.t("Rucksack")
	ti.add_theme_font_override("font", UI.heading_font())
	ti.add_theme_font_size_override("font_size", 16)
	ti.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	kopf.add_child(ti)
	var zu := Button.new()
	zu.text = T.t("Zu")
	zu.focus_mode = Control.FOCUS_NONE
	zu.pressed.connect(func(): menu(false))
	kopf.add_child(zu)
	var r := rs()
	_menu_box.add_child(UI.small(T.t("%.1f kg · %d von %d L") % [RS.gewicht(r), int(RS.volumen(r)), int(RS.platz(r))], UI.MUT))
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 6)
	g.add_theme_constant_override("v_separation", 6)
	_menu_box.add_child(g)
	for e in aktionen():
		var b := Button.new()
		b.name = str(e[0])
		b.text = str(e[1])
		b.focus_mode = Control.FOCUS_NONE
		b.disabled = not bool(e[2])
		b.tooltip_text = str(e[3]) if not bool(e[2]) else ""
		b.custom_minimum_size = Vector2(170, 40)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var id := str(e[0])
		b.pressed.connect(func(): tu(id))
		g.add_child(b)
	_menu_box.add_child(UI.small(T.t("PC: L Lampe · B Feldstecher · O Ort merken · , . Uhr · E abseilen · R dieses Menü"), UI.MUT))


# ---- every frame --------------------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if person == null:
		return
	var an := _an()
	if not an:
		_hud.visible = false
		_menu.visible = false
		if fernglas:
			feldstecher(false)
		return
	_hud.visible = not ((person.gestalten != null and person.gestalten.offen) or (person.extras != null and person.extras.foto_an))
	_kraft_tick(dt)
	var s: Vector2 = get_viewport().get_visible_rect().size
	var oben: float = 160.0
	if person.begleiter != null and person.begleiter.auge != null:
		var ar: Rect2 = person.begleiter.auge.get_global_rect()
		oben = ar.position.y + ar.size.y + 6.0 if person.begleiter.auge.visible else ar.position.y
	var kw := minf(360.0, s.x - 90.0)
	_kompass.visible = hat("kompass") and not fernglas
	_kompass.position = Vector2((s.x - kw) * 0.5 + (20.0 if s.x < 768.0 else 0.0), oben)
	_kompass.size = Vector2(kw, 30)
	_kompass.queue_redraw()
	_uhr.visible = hat("taschenuhr") and not fernglas
	_uhr.text = "◷ " + _zeit()
	_uhr.position = Vector2(_kompass.position.x + kw - 64.0, oben + (34.0 if _kompass.visible else 0.0))
	_bars.visible = echt() and not fernglas
	_bars.position = Vector2(_kompass.position.x, oben + (34.0 if _kompass.visible else 0.0))
	_bars.size = Vector2(minf(220.0, kw - 80.0), 40)
	_bars.queue_redraw()
	_msg.position = Vector2(0, s.y * 0.3)
	_msg.size = Vector2(s.x, 30)
	if _msg.visible and main.now() > _msg_bis:
		_msg.visible = false
	if _menu.visible:
		var mw := minf(440.0, s.x - 16.0)
		_menu.position = Vector2((s.x - mw) * 0.5, maxf(oben + 40.0, s.y * 0.3))
		_menu.size = Vector2(mw, 0)
		_menu.custom_minimum_size = Vector2(mw, 0)
	if fernglas:
		(_fg_maske.material as ShaderMaterial).set_shader_parameter("aspect", s.x / maxf(1.0, s.y))
		_fg_text.text = str(int(round(zoom))) + "×" + (("  " + T.t("Nachtsicht")) if nacht else "")
		_fg_text.position = Vector2(16, s.y - (280.0 if s.x < 600.0 else 200.0))
		var bw := minf(s.x - 16.0, 520.0)
		_fg_knoepfe.size = Vector2(bw, 0)
		_fg_knoepfe.position = Vector2((s.x - bw) * 0.5, s.y - (230.0 if s.x < 600.0 else 150.0))
		for b in _fg_knoepfe.get_children():
			(b as Button).text = T.t(str(b.get_meta("t")))
		_fg_labels.queue_redraw()
	# lying in the camp: getting up = the camp stays where it is (packed away when exploring ends)


func _kompass_draw() -> void:
	if person == null or not person.ok():
		return
	var c := _kompass
	var w: float = c.size.x
	c.draw_rect(Rect2(Vector2.ZERO, c.size), Color(0.05, 0.07, 0.09, 0.75))
	var yaw: float = float(person.actor.heading) if not fernglas else person._eye_yaw
	var cam: Camera3D = main.view_cam
	var f := -cam.global_transform.basis.z
	if Vector2(f.x, f.z).length() > 0.1:
		yaw = atan2(-f.x, -f.z)
	var dir_deg := fposmod(rad_to_deg(-yaw), 360.0)                    # 0 = north (-z), 90 = east (+x)
	var span := 120.0
	for k in range(0, 360, 15):
		var dd := wrapf(float(k) - dir_deg, -180.0, 180.0)
		if absf(dd) > span * 0.5:
			continue
		var x := w * 0.5 + dd / span * w
		var lab: String = {0: "N", 90: "O", 180: "S", 270: "W"}.get(k, "")
		c.draw_line(Vector2(x, 2), Vector2(x, 8 if lab == "" else 12), Color(1, 1, 1, 0.8), 1.5)
		if lab != "":
			c.draw_string(ThemeDB.fallback_font, Vector2(x - 5, 26), lab, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(1, 0.85, 0.4) if lab == "N" else Color.WHITE)
	c.draw_line(Vector2(w * 0.5, 0), Vector2(w * 0.5, 30), Color(0.35, 0.75, 1.0), 2.0)
	if ziel is Vector3:
		var to: Vector3 = (ziel as Vector3) - person.figur.pos()
		var tdeg := fposmod(rad_to_deg(atan2(to.x, -to.z)), 360.0)
		var dd2 := clampf(wrapf(tdeg - dir_deg, -180.0, 180.0), -span * 0.5, span * 0.5)
		var x2 := w * 0.5 + dd2 / span * w
		c.draw_colored_polygon(PackedVector2Array([Vector2(x2 - 6, 30), Vector2(x2 + 6, 30), Vector2(x2, 18)]), Color(1.0, 0.35, 0.3))
		c.draw_string(ThemeDB.fallback_font, Vector2(clampf(x2 + 8, 0, w - 50), 28), "%d m" % int(Vector2(to.x, to.z).length()),
				HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1.0, 0.6, 0.55))


func _bars_draw() -> void:
	var c := _bars
	var vals := [[T.t("Kraft"), kraft, Color(0.3, 0.85, 0.45)], [T.t("Hunger"), hunger, Color(0.95, 0.7, 0.3)],
			[T.t("Durst"), durst, Color(0.35, 0.7, 1.0)], [T.t("Wärme"), waerme, Color(1.0, 0.45, 0.35)]]
	var bw: float = (c.size.x - 6.0) / 4.0
	for i in range(4):
		var x := float(i) * (bw + 2.0)
		c.draw_rect(Rect2(x, 0, bw, 8), Color(0.05, 0.07, 0.09, 0.8))
		c.draw_rect(Rect2(x, 0, bw * clampf(float(vals[i][1]) / 100.0, 0.0, 1.0), 8), vals[i][2])
		c.draw_string(ThemeDB.fallback_font, Vector2(x, 22), str(vals[i][0]), HORIZONTAL_ALIGNMENT_LEFT, bw, 11, Color(1, 1, 1, 0.9))
	if verletzt:
		c.draw_string(ThemeDB.fallback_font, Vector2(0, 36), T.t("verletzt"), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1.0, 0.45, 0.4))


# ---- the binoculars -----------------------------------------------------------------------------------------------------------
func sichtbare() -> Array:
	"""animals and people in the binoculars now: [[name, distance, screen position]]"""
	var out := []
	var cam: Camera3D = main.view_cam
	var listen: Array = []
	if main.visitors != null:
		listen.append_array(main.visitors.get_children())
	if person.begleiter != null and person.begleiter.hund != null and is_instance_valid(person.begleiter.hund):
		listen.append(person.begleiter.hund)
	for v in listen:
		if not (v is Node3D) or v.get("kind") == null or v == person.actor or not (v as Node3D).is_visible_in_tree():
			continue
		var p: Vector3 = (v as Node3D).global_position + Vector3(0, maxf(0.4, float(v.get("body_h")) if v.get("body_h") != null else 0.8), 0)
		var d := cam.global_position.distance_to(p)
		if d > 400.0 or cam.is_position_behind(p) or not cam.is_position_in_frustum(p):
			continue
		if not main.line_free(cam.global_position, p):
			continue
		var k: String = str(v.get("kind"))
		var nm: String = T.t("Maggie") if v == person.begleiter.hund else (T.t(main._animal_name(k)) if k != "person" else T.t("Mensch"))
		out.append([nm, d, cam.unproject_position(p)])
	return out


func _fg_labels_draw() -> void:
	if person == null or not person.ok():
		return
	for e in sichtbare():
		var q: Vector2 = e[2]
		var t := "%s · %d m" % [str(e[0]), int(e[1])]
		_fg_labels.draw_rect(Rect2(q + Vector2(-4, -36), Vector2(t.length() * 8.0 + 8.0, 22)), Color(0, 0, 0, 0.6))
		_fg_labels.draw_string(ThemeDB.fallback_font, q + Vector2(0, -20), t, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(1.0, 0.95, 0.5))
		_fg_labels.draw_arc(q, 10.0, 0.0, TAU, 16, Color(1.0, 0.95, 0.5), 1.5, true)


func kamera(cam: Camera3D, dt: float) -> void:
	"""looking through the binoculars: at the eyes, along the view yaw, zoomed"""
	var fw := Vector3(-sin(person._eye_yaw), 0, -cos(person._eye_yaw))
	var at: Vector3 = person.augen_punkt() + fw * 0.15
	cam.global_position = at
	cam.fov = 62.0 / zoom
	cam.look_at(at + fw * 10.0 + Vector3(0, (0.38 - float(person.ex.pitch)) * 4.0, 0), Vector3.UP)


func info() -> Dictionary:
	var r := rs()
	return {"kraft": snappedf(kraft, 0.1), "hunger": snappedf(hunger, 0.1), "durst": snappedf(durst, 0.1), "waerme": snappedf(waerme, 0.1),
			"verletzt": verletzt, "echt": echt(), "fernglas": fernglas, "zoom": zoom, "nacht": nacht, "lampe": lampe_an() if person.ok() else false,
			"ziel": [snappedf((ziel as Vector3).x, 0.1), snappedf((ziel as Vector3).z, 0.1)] if ziel is Vector3 else [],
			"lager": lager != null and is_instance_valid(lager), "kg": snappedf(RS.gewicht(r), 0.01), "liter": snappedf(RS.volumen(r), 0.1),
			"pack": str(r["pack"]), "n": r["n"], "menu": _menu.visible, "sichtbar": sichtbare().map(func(e): return [e[0], snappedf(e[1], 0.1)]) if fernglas else [],
			"tempo": snappedf(tempo_faktor(), 0.01), "schnee": auf_schnee() if person.ok() else false}
