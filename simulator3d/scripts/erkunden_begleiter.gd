extends Node
## «Frei erkunden mit eigener Figur», Etappe 2 (Besitzer 21.11.2026): Begleiter und «MoveEye sieht dich». Ein Kind von
## explore_person.gd («person»), läuft nach den Figuren (process_priority 96).
##   * Maggie (main.ex_maggie, ab Werk aus): der Familienhund folgt der Figur in jeder Welt - ein Hund von actor.gd mit
##     «leader» (geht mit seiner Person) und Maggies Körper aus maggie_hund.gd (Modell mit Skelett, in Lite Grundformen).
##     Zu weit weg (Schnelllauf, Klettern, Schwimmen) kommt sie hinter der Figur wieder dazu. MoveEye sieht sie wie ein Tier.
##   * Blinki (main.ex_blinki, ab Werk an): klein in der Ecke (gezeichnet, tour.gd BlinkiView), sagt ab und zu etwas zur
##     Haltung, zum Wasser und ob MoveEye dich sieht.
##   * MoveEye sieht die Figur (main.ex_mw_sieht, ab Werk an = wie bisher): aus = die Figur ist für die Kameras von MoveEye
##     unsichtbar (Ebene der Hilfsmarken, kein Wärmebild, kein Schatten) - kein Bild, kein Alarm; man selbst sieht sie.
##   * Auge-Symbol «MoveEye sieht dich» (main.ex_auge, ab Werk an - Besitzer 21.11.2026): offen und hell, solange die Figur im
##     Bild einer Kamera von MoveEye ist (Sichtfeld, Sichtlinie frei, bis 80 m), sonst zu; durchgestrichen, wenn MoveEye die
##     Figur gar nicht sieht (Schalter aus). Das ist «im Bild», nicht «erkannt» (das entscheidet MoveEye selbst).

const T = preload("res://scripts/i18n.gd")
const Tour = preload("res://scripts/tour.gd")
const ActorS = preload("res://scripts/actor.gd")
const HELPER := 128                  # main.HELPER_LAYER: only the operator's view sees it
const WEIT := 14.0                   # m: further away Maggie comes back behind the figure

var person
var main
var hund: Node3D = null
var _mh = null                       # maggie_hund.gd (only to build Maggie's body)
var sieht := false                   # the figure is in a picture of MoveEye now
var _t := 0.0
var _layer: CanvasLayer
var auge: Control
var blinki: Control
var _bl_box: PanelContainer
var _bl_txt: Label
var _bl_bis := 0.0
var _bl_alt := {}
var _mw_an := true                   # the layers of the figure: as for MoveEye now
var _mw_von: Node = null


class Auge extends Control:
	var zustand := "shut"                # open | shut | off (MoveEye sees nothing)

	func _draw() -> void:
		var c := Vector2(size.y * 0.5 + 4.0, size.y * 0.5)
		var r := size.y * 0.32
		var col := Color(0.3, 0.95, 0.55) if zustand == "open" else Color(0.75, 0.78, 0.82)
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.05, 0.07, 0.09, 0.78))
		draw_rect(Rect2(Vector2.ZERO, size), Color(col.r, col.g, col.b, 0.9), false, 1.5)
		var pts := PackedVector2Array()
		for i in range(17):
			var a := PI * float(i) / 16.0
			pts.append(c + Vector2(-cos(a) * r * 1.5, -sin(a) * r * (0.9 if zustand == "open" else 0.15)))
		for i in range(17):
			var a2 := PI * float(i) / 16.0
			pts.append(c + Vector2(cos(a2) * r * 1.5, sin(a2) * r * (0.9 if zustand == "open" else 0.15)))
		draw_polyline(pts, col, 2.0, true)
		if zustand == "open":
			draw_circle(c, r * 0.5, col)
		if zustand == "off":
			draw_line(c + Vector2(-r * 1.4, r * 1.1), c + Vector2(r * 1.4, -r * 1.1), Color(0.95, 0.4, 0.35), 2.5, true)


func _ready() -> void:
	process_priority = 96
	_layer = CanvasLayer.new()
	_layer.layer = 6
	add_child(_layer)
	auge = Auge.new()
	auge.mouse_filter = Control.MOUSE_FILTER_IGNORE
	auge.visible = false
	var al := Label.new()
	al.name = "text"
	al.add_theme_font_size_override("font_size", 14)
	al.add_theme_color_override("font_color", Color(1, 1, 1))
	al.position = Vector2(44, 6)
	auge.add_child(al)
	_layer.add_child(auge)
	blinki = Tour.BlinkiView.new()
	blinki.custom_minimum_size = Vector2(46, 52)
	blinki.size = Vector2(46, 52)
	blinki.mouse_filter = Control.MOUSE_FILTER_IGNORE
	blinki.visible = false
	_layer.add_child(blinki)
	_bl_box = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.07, 0.09, 0.85)
	sb.set_corner_radius_all(8)
	sb.set_content_margin_all(6)
	_bl_box.add_theme_stylebox_override("panel", sb)
	_bl_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bl_txt = Label.new()
	_bl_txt.add_theme_font_size_override("font_size", 13)
	_bl_txt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_bl_txt.custom_minimum_size = Vector2(220, 0)
	_bl_box.add_child(_bl_txt)
	_bl_box.visible = false
	_layer.add_child(_bl_box)


func _an() -> bool:
	return person != null and person.ok() and bool(person.active) and person.ex != null and bool(person.ex.on)


# ---- MoveEye sees the figure (layers) ---------------------------------------------------------------------------------
func mw_anwenden(force := false) -> void:
	"""the figure for the cameras of MoveEye: visible (layer 1 + thermal 2) or only for the operator (switch off)"""
	if not person.ok():
		return
	var an := bool(main.get("ex_mw_sieht"))
	if not force and an == _mw_an and _mw_von == person.actor:
		return
	_mw_an = an
	_mw_von = person.actor
	for n in person.actor.find_children("*", "GeometryInstance3D", true, false):
		var g := n as GeometryInstance3D
		if not g.has_meta("ew_layers"):
			g.set_meta("ew_layers", g.layers)
			g.set_meta("ew_shadow", g.cast_shadow)
		var l0: int = int(g.get_meta("ew_layers"))
		if an:
			g.layers = l0
			g.cast_shadow = int(g.get_meta("ew_shadow"))
		else:
			g.layers = (HELPER if (l0 & 1) != 0 else 0)
			g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for n2 in person.actor.find_children("*", "Light3D", true, false):  # a headlamp: MoveEye would see what it lights
		var li := n2 as Light3D
		if not li.has_meta("ew_cull"):
			li.set_meta("ew_cull", li.light_cull_mask)
		li.light_cull_mask = int(li.get_meta("ew_cull")) if an else HELPER


func im_bild() -> bool:
	"""is the figure in a picture of MoveEye now (field of view, free line of sight, up to 80 m)?"""
	if not person.ok() or not bool(main.get("ex_mw_sieht")):
		return false
	var top: Vector3 = person.actor.global_position + Vector3(0, maxf(0.3, person.hoehe() * 0.7), 0)
	for i in range(mini(2, main.cams.size())):
		var cam: Camera3D = main.cams[i]
		if cam == null or not cam.is_inside_tree():
			continue
		if cam.global_position.distance_to(top) > 80.0 or not cam.is_position_in_frustum(top):
			continue
		if main.line_free(cam.global_position, top):
			return true
	return false


# ---- Maggie -------------------------------------------------------------------------------------------------------------
func _hund_da() -> bool:
	return hund != null and is_instance_valid(hund)


func hund_weg() -> void:
	if _hund_da():
		hund.queue_free()
	hund = null


func _hund_bauen() -> void:
	var a: Node3D = person.actor
	var back: Vector3 = a.global_transform.basis.z
	var at: Vector3 = a.global_position + back * 1.2 + a.global_transform.basis.x * 0.6
	var q: Vector2 = main.keep_out(Vector2(at.x, at.z), 0.3, false)
	var d = ActorS.new()
	d.name = "erkunden_maggie"
	main.add_child(d)
	d.setup(main, "dog", Vector3(q.x, main.ground_y(q.x, q.y), q.y), a.global_position, 1.6)
	if _mh == null:
		_mh = load("res://scripts/maggie_hund.gd").new()
		_mh.m = main
		_mh.lite = load("res://scripts/quality.gd").lite() or str(main.quality) == "simple"
	_mh._maggie_koerper(d)                                  # Maggie's own body (model with skeleton, else soft shapes)
	d.leader = a
	d.follow_off = Vector3(0.8, 0, 1.3)
	d.speed = 1.6
	hund = d


func _hund_tick() -> void:
	var soll: bool = _an() and bool(main.get("ex_maggie"))
	if not soll:
		if _hund_da() and not (person.ok() and bool(main.get("ex_maggie"))):
			hund_weg()
		return
	if not _hund_da() or hund.get("leader") != person.actor:
		hund_weg()
		_hund_bauen()
		return
	var a: Node3D = person.actor
	hund.speed = clampf(float(a.cur_speed) * 1.15, 1.4, 9.0)    # keeps up with a run, not with a fast run (then: back behind)
	var d: float = Vector2(hund.global_position.x - a.global_position.x, hund.global_position.z - a.global_position.z).length()
	if d > WEIT or absf(hund.global_position.y - a.global_position.y) > 4.0:
		var back: Vector3 = a.global_transform.basis.z
		var w: Vector3 = a.global_position + back * 1.5
		var q: Vector2 = main.keep_out(Vector2(w.x, w.z), 0.3, false)
		hund.position = Vector3(q.x, main.ground_y(q.x, q.y), q.y)
		hund.cur_speed = 0.0


# ---- Blinki ------------------------------------------------------------------------------------------------------------
func sag(text: String, secs := 5.0) -> void:
	if not bool(main.get("ex_blinki")):
		return
	_bl_txt.text = text
	_bl_bis = main.now() + secs
	blinki.talk()
	blinki.hop()


func _blinki_tick() -> void:
	var p = person
	var key := {"h": str(p.haltung), "w": str(p.wasser), "s": sieht}
	if _bl_alt.is_empty():
		_bl_alt = key
		sag(T.t("Hallo! Ich komme mit. Duck dich (C), dann sieht MoveEye dich schlechter."), 6.0)
		return
	if key["w"] != _bl_alt["w"] and key["w"] == "schwimmen":
		sag(T.t("Schwimmen! Tauchen geht nicht – zum Ufer kommst du einfach zurück."))
	elif key["h"] != _bl_alt["h"] and key["h"] == "kriechen":
		sag(T.t("Kriechend bist du ganz klein im Bild von MoveEye."))
	elif key["s"] != _bl_alt["s"] and bool(key["s"]) and bool(main.get("ex_auge")):
		sag(T.t("Achtung, MoveEye sieht dich!"), 3.0)
	_bl_alt = key


func _layout() -> void:
	var s: Vector2 = get_viewport().get_visible_rect().size
	var ex = person.ex
	var unten: float = 150.0
	if ex != null and is_instance_valid(ex):
		var r: Rect2 = ex.get_global_rect()
		unten = r.position.y + r.size.y + 8.0                    # (the global rect is already scaled)
	auge.size = Vector2(minf(250.0, s.x - 80.0), 34)
	auge.position = Vector2(clampf(s.x * 0.5 - auge.size.x * 0.5, 66.0, s.x - auge.size.x - 4.0), unten)
	if s.x >= 768.0:                                          # wide: under the small map at the left (the cameras are right)
		blinki.position = Vector2(16.0, 214.0)
		_bl_box.position = Vector2(66.0, 222.0)
	else:
		blinki.position = Vector2(s.x - 58.0, unten + 2.0)
		_bl_box.position = Vector2(maxf(66.0, s.x - 58.0 - 232.0), unten + 44.0)
	_bl_txt.custom_minimum_size = Vector2(minf(220.0, s.x - 140.0), 0)


func _process(dt: float) -> void:
	if person == null:
		return
	_t -= dt
	if person.ok():
		mw_anwenden()
	_hund_tick()
	var an := _an()
	if not an:
		auge.visible = false
		blinki.visible = false
		_bl_box.visible = false
		_bl_alt = {}
		return
	if _t <= 0.0:
		_t = 0.25
		sieht = im_bild()
		_blinki_tick()
	_layout()
	var ruhig: bool = (person.sachen != null and person.sachen.fernglas) or (person.extras != null and person.extras.foto_an) \
			or (person.gestalten != null and person.gestalten.offen)
	auge.visible = bool(main.get("ex_auge")) and not ruhig
	var z := "off" if not bool(main.get("ex_mw_sieht")) else ("open" if sieht else "shut")
	if auge.zustand != z or auge.get_node("text").text == "":
		auge.zustand = z
		auge.get_node("text").text = T.t("MoveEye sieht dich") if z == "open" else (T.t("MoveEye sieht dich nicht (aus)") if z == "off" else T.t("Nicht im Bild von MoveEye"))
		auge.queue_redraw()
	blinki.visible = bool(main.get("ex_blinki"))
	_bl_box.visible = blinki.visible and main.now() < _bl_bis
	blinki.mood = "point" if sieht else "normal"


func info() -> Dictionary:
	return {"maggie": _hund_da(), "maggie_d": snappedf(Vector2(hund.global_position.x - person.actor.global_position.x,
				hund.global_position.z - person.actor.global_position.z).length(), 0.1) if _hund_da() and person.ok() else -1.0,
			"blinki": blinki.visible, "blinki_sagt": _bl_txt.text if _bl_box.visible else "", "sieht": sieht,
			"auge": auge.visible, "auge_zustand": auge.zustand, "mw_sieht": bool(main.get("ex_mw_sieht"))}


func _exit_tree() -> void:
	if _mh != null and is_instance_valid(_mh):
		_mh.free()
