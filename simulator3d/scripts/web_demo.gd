extends Node
## «Simulator im Browser» – Demo (Besitzer 14.11.2026; nur im Browser, web.gd legt den Knoten an, sonst gibt es ihn nicht):
##   * ein kleines eingebautes MoveEye: der Kopf bewacht selbst (über kopf_selbst.gd – wie die Pfeile, gleiche Grenzen und
##     Tempo), Rahmen um Personen und Tiere im Bild der Kopfkamera (aus der Welt des Simulators, kein echtes Erkennen),
##     die Status-LED (statusled.gd fragt led(), solange kein echtes MoveEye verbunden ist) und ein Alarm-Hinweis.
##     Die Tasten im Fenster «Gerät» gelten: «Schutz» kurz = Wachsam <-> Aus, «Alarm quittieren».
##   * Handy: die Oberfläche wird nach der Pixeldichte vergrössert (mindestens MIN_W Punkte breit, damit das Bedienfeld
##     passt), schmal = Bedienfeld am Anfang zu; grosse Knöpfe für Kopf und Bedienfeld bei Touch.
##   * PC-Karten weg (Verbindung, Simulator-PC, Tunnel, Start mit dem PC, Updates, «MoveEye auf diesem PC starten»).
##   * ein kurzer Hinweis beim Start: «Demo – ohne Verbindung zu MoveEye» (5 Sprachen).
## Gezeigt wird nur, was MoveEye sinngemäss täte – nichts davon geht an ein echtes MoveEye.

const T = preload("res://scripts/i18n.gd")
const Kopf = preload("res://scripts/kopf_selbst.gd")

const MIN_W := 600.0                    # so breit (Punkte) muss die Oberfläche mindestens sein: das Bedienfeld braucht ~560
const MIN_H := 420.0                    # … und so hoch (Handy quer)
const NARROW := 900.0                   # schmaler (oder niedriger als SHORT): Bedienfeld beim Start zu, die Kamera-Karte schwebt nicht
const SHORT := 520.0
const TOUCH_K := 1.15                   # Touch: etwas grösser als die Pixeldichte allein
const HIDE := ["Verbindung", "Simulator-PC", "Tunnel zu MoveEye (Firewall ohne Adminrechte)", "Start mit dem PC", "Updates"]
const ALARM_S := 1.5                    # so lange muss eine Person im Bild sein (Wachsam), bis Alarm kommt
const USER_S := 10.0                    # nach einem Tipp auf die Pfeile: so lange bewacht der Kopf nicht selbst
const TX := {
	"welcome": {"de": "Demo – ohne Verbindung zu MoveEye. Der Kopf bewacht selbst, Rahmen zeigen erkannte Personen und Tiere. Ziehen = umsehen, Pfeile = Kopf drehen.",
		"en": "Demo – not connected to MoveEye. The head guards by itself, boxes show detected people and animals. Drag = look around, arrows = turn the head.",
		"fr": "Démo – sans connexion à MoveEye. La tête surveille seule, des cadres montrent les personnes et animaux détectés. Glisser = regarder, flèches = tourner la tête.",
		"it": "Demo – senza collegamento a MoveEye. La testa sorveglia da sola, i riquadri mostrano persone e animali rilevati. Trascinare = guardarsi intorno, frecce = girare la testa.",
		"rm": "Demo – senza colliaziun cun MoveEye. Il chau surveglia sez, rams mussan persunas ed animals reconuschids. Trair = guardar enturn, flitschas = volver il chau."},
	"title": {"de": "MoveEye (Demo)", "en": "MoveEye (demo)", "fr": "MoveEye (démo)", "it": "MoveEye (demo)", "rm": "MoveEye (demo)"},
	"watch": {"de": "Wachsam", "en": "Watching", "fr": "Vigilant", "it": "Vigile", "rm": "Attent"},
	"off": {"de": "Schutz aus", "en": "Protection off", "fr": "Protection désactivée", "it": "Protezione spenta", "rm": "Protecziun deactivada"},
	"person": {"de": "Person", "en": "Person", "fr": "Personne", "it": "Persona", "rm": "Persuna"},
	"animal": {"de": "Tier", "en": "Animal", "fr": "Animal", "it": "Animale", "rm": "Animal"},
	"alarm": {"de": "ALARM – Person erkannt", "en": "ALARM – person detected", "fr": "ALARME – personne détectée", "it": "ALLARME – persona rilevata", "rm": "ALARM – persuna reconuschida"},
	"ack": {"de": "tippen = quittieren", "en": "tap = acknowledge", "fr": "toucher = acquitter", "it": "tocca = conferma", "rm": "tutgar = confermar"},
}

var main
var armed := true
var alarm := false
var alarm_t := -100.0
var dets: Array = []                    # [{"r": Rect2 (0..1 im Bild), "k": "person" | "animal", "d": Meter}]
var _person_s := 0.0                    # so lange ist eine Person ohne Pause im Bild
var _gone_s := 0.0
var _user_t := -100.0
var _my_goal := {"pan": INF, "tilt": INF}
var _seq := {"protect": -1, "ack": -1}
var _last_size := Vector2i.ZERO
var _last_phone := false
var _narrow := false
var _narrow_done := false
var _hidden: Array = []
var _hide_t := 0.0
var _det_t := 0.0
var _quiet_s := 0.0
var _spawn_i := 0
var _t := 0.0
var _built := false
var _layer: CanvasLayer
var _pip: PanelContainer
var _img: TextureRect
var _boxes: Control
var _status: Label
var _dot: Panel
var _dot_box: StyleBoxFlat
var _banner: Button
var _welcome: PanelContainer
var _pad: GridContainer


static func tx(k: String) -> String:
	var d: Dictionary = TX.get(k, {})
	return str(d.get(T.lang(), d.get("en", d.get("de", k))))


func still() -> bool:
	"""das Demo-MoveEye der Homepage ist verbunden (web_moveeye.gd): dann schweigt dieses kleine eingebaute MoveEye"""
	var wm = main.get_meta("web_moveeye") if main != null and main.has_meta("web_moveeye") else null
	return wm != null and wm.verbunden()


func led() -> Dictionary:
	"""für statusled.gd (solange kein echtes MoveEye verbunden ist): die LED wie MoveEye sie schicken würde"""
	if not _built or still():
		return {}
	if alarm:
		return {"on": true, "rgb": "#ff2a2a", "br": 1.0 if fmod(_t * 2.0, 1.0) < 0.5 else 0.05, "text": "LED: " + tx("alarm") + " (Demo)"}
	if not armed:
		return {"on": true, "rgb": "#9aa3ad", "br": 0.08, "text": "LED: " + tx("off") + " (Demo)"}
	for d in dets:
		if d["k"] == "person":
			return {"on": true, "rgb": "#ffd21f", "br": 0.8, "text": "LED: " + tx("person") + " (Demo)"}
	return {"on": true, "rgb": "#ff8a1f", "br": 0.4, "text": "LED: " + tx("watch") + " (Demo)"}


func _process(dt: float) -> void:
	_t += dt
	if not _built:
		if main.ui_root != null and main.ui_layer != null and main.vps.size() > 0 and main.cams.size() > 0 and main.head != null:
			_build()
		return
	_rescale()
	_hide_t -= dt
	if _hide_t <= 0.0:
		_hide_t = 1.0
		_hide_pc()
	var ruhig := still()
	_layer.visible = not ruhig                         # verbunden: Bild, Rahmen, Alarm und Kopf kommen vom echten Demo-MoveEye
	if ruhig:
		alarm = false
		dets = []
		return
	_det_t -= dt
	if _det_t <= 0.0:
		_det_t = 0.2
		_detect()
		_boxes.queue_redraw()
	_alarm_step(dt)
	_guard(dt)
	_buttons()
	_visitors(dt)
	_paint()


# ---- Oberfläche --------------------------------------------------------------------------------------------------------
func phone() -> bool:
	"""Handy-Modus (handy.gd) nach der Grösse in Punkten des Browsers (CSS-Pixel), nicht nach der vergrösserten Oberfläche"""
	var h = main.get("handy")
	if h == null:
		return false
	if h.mode != "auto":
		return h.mode == "phone"
	var dpr := DisplayServer.screen_get_scale()
	var css := Vector2(get_tree().root.size) / (dpr if dpr > 0.0 else 1.0)
	return minf(css.x, css.y) < h.SHORT


func _rescale() -> void:
	var w := get_tree().root
	var ph := phone()
	var k: float = main._mod("start").phone_scale()     # 3D-Ansicht: normale Auflösung (Besitzer 15.11.2026), nie unscharf
	if absf(main.get_viewport().scaling_3d_scale - k) > 0.01 or main.view_scale != k:
		main.set_view_scale(k)
	if w.size == _last_size and ph == _last_phone:
		return
	_last_size = w.size
	_last_phone = ph
	var dpr := DisplayServer.screen_get_scale()
	var f := (dpr if dpr > 0.0 else 1.0) * (TOUCH_K if DisplayServer.is_touchscreen_available() and not ph else 1.0)
	if not ph:                                         # Handy-Modus: die Oberfläche in Punkten des Handys (390 × 844)
		if w.size.x / f < MIN_W:
			f = w.size.x / MIN_W
		if w.size.y / f < MIN_H:
			f = w.size.y / MIN_H
	w.content_scale_factor = maxf(f, 0.5)
	var vs: Vector2 = main.get_viewport().get_visible_rect().size
	_narrow = vs.x < NARROW or vs.y < SHORT
	print("web: Fenster %d × %d, Pixeldichte %.2f -> Massstab %.2f (%d × %d Punkte)%s" % [w.size.x, w.size.y, dpr, w.content_scale_factor, vs.x, vs.y, " schmal" if _narrow else ""])
	if _narrow and not _narrow_done:
		_narrow_done = true
		main.show_panel(false)
		get_tree().create_timer(4.0).timeout.connect(func(): main.show_panel(false))   # nach dem Laden der Einstellungen noch einmal


func _style(bg: Color, border: Color, r := 10) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.border_color = border
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(r)
	sb.set_content_margin_all(8)
	return sb


func _build() -> void:
	_built = true
	var th: Theme = main.UI.theme()
	_layer = CanvasLayer.new()
	_layer.layer = 3                                     # über dem Fenster (1), unter dem TV-Modus (5)
	add_child(_layer)
	# das Bild von MoveEye (Kopfkamera) mit den Rahmen
	_pip = PanelContainer.new()
	_pip.theme = th
	_pip.add_theme_stylebox_override("panel", _style(Color(0.06, 0.08, 0.11, 0.92), Color(1.0, 0.55, 0.12, 0.8)))
	_layer.add_child(_pip)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	_pip.add_child(v)
	var hdr := HBoxContainer.new()
	hdr.add_theme_constant_override("separation", 8)
	v.add_child(hdr)
	_dot = Panel.new()
	_dot.custom_minimum_size = Vector2(14, 14)
	_dot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_dot_box = _style(Color(0.16, 0.19, 0.23), Color(0, 0, 0, 0), 7)
	_dot.add_theme_stylebox_override("panel", _dot_box)
	hdr.add_child(_dot)
	_status = Label.new()
	_status.add_theme_font_size_override("font_size", 14)
	_status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_status.clip_text = true
	hdr.add_child(_status)
	var fr := Control.new()
	fr.clip_contents = true
	v.add_child(fr)
	_img = TextureRect.new()
	_img.texture = main.vps[0].get_texture()
	_img.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_img.stretch_mode = TextureRect.STRETCH_SCALE
	_img.set_anchors_preset(Control.PRESET_FULL_RECT)
	fr.add_child(_img)
	_boxes = Control.new()
	_boxes.set_anchors_preset(Control.PRESET_FULL_RECT)
	_boxes.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_boxes.draw.connect(_draw_boxes)
	fr.add_child(_boxes)
	_pip.set_meta("frame", fr)
	_banner = Button.new()
	_banner.theme = th
	_banner.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_banner.add_theme_font_size_override("font_size", 16)
	_banner.add_theme_color_override("font_color", Color.WHITE)
	_banner.add_theme_color_override("font_hover_color", Color.WHITE)
	for st in ["normal", "hover", "pressed", "focus"]:
		_banner.add_theme_stylebox_override(st, _style(Color(0.78, 0.08, 0.08, 0.95), Color(1, 0.6, 0.6), 10))
	_banner.visible = false
	_banner.pressed.connect(func(): alarm = false)
	_layer.add_child(_banner)
	# grosse Knöpfe (Touch): Kopf drehen, Bedienfeld
	_pad = GridContainer.new()
	_pad.theme = th
	_pad.columns = 3
	_pad.add_theme_constant_override("h_separation", 8)
	_pad.add_theme_constant_override("v_separation", 8)
	_pad.visible = DisplayServer.is_touchscreen_available()
	_layer.add_child(_pad)
	for k in ["", "up", "panel", "left", "center", "right", "", "down", ""]:
		if k == "":
			var sp := Control.new()
			sp.custom_minimum_size = Vector2(60, 60)
			sp.mouse_filter = Control.MOUSE_FILTER_IGNORE
			_pad.add_child(sp)
			continue
		var b := Button.new()
		b.custom_minimum_size = Vector2(60, 60)
		var ic := Control.new()                          # gezeichnet: die Schrift des Simulators hat keine Pfeile
		ic.set_anchors_preset(Control.PRESET_FULL_RECT)
		ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
		ic.draw.connect(_draw_icon.bind(ic, k))
		if k == "panel":
			ic.set_meta("panel", true)
		b.add_child(ic)
		b.focus_mode = Control.FOCUS_NONE
		b.add_theme_stylebox_override("normal", _style(Color(0.08, 0.1, 0.14, 0.78), Color(1, 1, 1, 0.25), 30))
		b.add_theme_stylebox_override("hover", _style(Color(0.12, 0.15, 0.2, 0.85), Color(1, 1, 1, 0.4), 30))
		b.add_theme_stylebox_override("pressed", _style(Color(1.0, 0.55, 0.12, 0.85), Color(1, 1, 1, 0.5), 30))
		if k == "panel":
			b.pressed.connect(func(): main.show_panel(not main.ui_root.visible))
		else:
			b.pressed.connect(func(): main.mw_look(k, 6.0))
		_pad.add_child(b)
	# der Hinweis beim Start
	_welcome = PanelContainer.new()
	_welcome.theme = th
	_welcome.add_theme_stylebox_override("panel", _style(Color(0.06, 0.08, 0.11, 0.95), Color(1.0, 0.55, 0.12), 12))
	_layer.add_child(_welcome)
	var wv := VBoxContainer.new()
	wv.add_theme_constant_override("separation", 10)
	_welcome.add_child(wv)
	var wl := Label.new()
	wl.text = tx("welcome")
	wl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	wl.add_theme_font_size_override("font_size", 16)
	wv.add_child(wl)
	var ok := Button.new()
	ok.text = "OK"
	ok.custom_minimum_size = Vector2(110, 44)
	ok.size_flags_horizontal = Control.SIZE_SHRINK_END
	main.UI.primary(ok)
	ok.pressed.connect(func(): _welcome.visible = false)
	wv.add_child(ok)
	get_tree().create_timer(25.0).timeout.connect(func(): _welcome.visible = false)


func _draw_icon(c: Control, k: String) -> void:
	var m := c.size * 0.5
	var col := Color(1, 1, 1, 0.92)
	var r := 11.0
	match k:
		"panel":
			for i in range(3):
				c.draw_rect(Rect2(m.x - r, m.y - 8.0 + i * 7.0, r * 2.0, 3.0), col)
		"center":
			c.draw_arc(m, r, 0.0, TAU, 24, col, 3.0, true)
			c.draw_circle(m, 3.5, col)
		_:
			var a: float = {"up": -PI / 2.0, "down": PI / 2.0, "left": PI, "right": 0.0}[k]
			var d := Vector2.from_angle(a)
			var n := Vector2(-d.y, d.x)
			c.draw_colored_polygon(PackedVector2Array([m + d * r, m - d * r * 0.7 + n * r, m - d * r * 0.7 - n * r]), col)


func _paint() -> void:
	var vs: Vector2 = main.get_viewport().get_visible_rect().size
	var fr: Control = _pip.get_meta("frame")
	var isz := Vector2(main.vps[0].size)
	var asp := isz.y / maxf(isz.x, 1.0)
	var low := vs.y < SHORT
	var p0 := Vector2(224.0, 14.0) if low else Vector2(14.0, 222.0)   # links unter der Karte (minimap.gd), Handy quer: rechts neben ihr
	var pw := clampf(vs.x * (0.46 if _narrow else 0.24), 200.0, 340.0)
	pw = minf(pw, (vs.y - p0.y - 150.0) / asp)          # unten bleibt Platz für die Leiste
	var hon: bool = main.get("handy") != null and main.handy.on
	if not hon:                                         # Handy-Modus: das Bild hängt in «Kamera» gross (handy.gd) oder ist weg
		fr.custom_minimum_size = Vector2(pw, pw * asp)
		_pip.reset_size()
		_pip.position = p0
	var l := led()
	var c := Color.html(str(l.get("rgb", "#000000")))
	var br := float(l.get("br", 0.0))
	_dot_box.bg_color = c if br > 0.2 else c.lerp(Color(0.16, 0.19, 0.23), 0.6)
	var n := {"person": 0, "animal": 0}
	for d in dets:
		n[d["k"]] += 1
	var s := tx("title") + " · " + (tx("watch") if armed else tx("off"))
	if n["person"] > 0:
		s += " · %d %s" % [n["person"], tx("person")]
	if n["animal"] > 0:
		s += " · %d %s" % [n["animal"], tx("animal")]
	_status.text = s
	if hon:                                              # Handy-Modus: Leiste, Steuerkreuz und Hinweis oben macht handy.gd
		_pad.visible = false
		_banner.visible = false
		_pip.visible = false
		if _welcome.visible and (main.handy.cur != "" or main.handy.big_id != "" or _other_open()):
			_welcome.visible = false                    # ein Blatt / Fenster / Dialog ist offen: der Hinweis hat gedient
		_paint_welcome(vs)
		return
	_pad.visible = DisplayServer.is_touchscreen_available()
	var cover: bool = _narrow and main.ui_root.visible   # schmal und Bedienfeld offen: nur «≡» bleibt (zum Schliessen)
	_pip.visible = not cover
	for b in _pad.get_children():
		if b is Button:
			b.visible = not cover or b.get_child(0).has_meta("panel")
		else:
			b.visible = not cover
	_banner.visible = alarm and not cover
	if alarm:
		_banner.text = "%s · %s\n%s" % [tx("alarm"), Time.get_time_string_from_system().substr(0, 5), tx("ack")]
		_banner.custom_minimum_size.x = minf(vs.x - 28.0, 460.0)
		_banner.reset_size()
		var by := _pip.position.y + _pip.size.y + 10.0       # unter dem Bild von MoveEye; Handy quer: über der Leiste
		if low:
			by = vs.y - _banner.size.y - 84.0
		_banner.position = Vector2((vs.x - _banner.size.x) * 0.5, by)
	if _pad.visible:
		var bs := 46.0 if low else 60.0                      # Handy quer: kleiner und links unter der Karte (rechts ist «Gerät»)
		for b in _pad.get_children():
			b.custom_minimum_size = Vector2(bs, bs)
		_pad.reset_size()
		_pad.size = _pad.get_combined_minimum_size()
		_pad.position = Vector2(14.0, vs.y - _pad.size.y - 74.0) if low else Vector2(vs.x - _pad.size.x - 14.0, vs.y - _pad.size.y - 96.0)
	_paint_welcome(vs)
	if _narrow and main.cam_float != null and not main.ui_root.visible:
		main.cam_float.visible = false                   # schmal: das Bild oben links genügt (die Kamera-Karte bleibt im Bedienfeld)


func _other_open() -> bool:
	"""ein Fenster oder Dialog eines anderen Teils ist offen (vom Fenster-Wächter gefunden, nicht die eigenen der Demo)"""
	var f = main.get("waechter")
	if f == null:
		return false
	for c in f._track:
		if is_instance_valid(c) and (c as Node).get_parent() != _layer and (c as Control).is_visible_in_tree():
			return true
	return false


func _paint_welcome(vs: Vector2) -> void:
	if _welcome.visible:
		_welcome.custom_minimum_size.x = minf(vs.x - 28.0, 520.0)
		_welcome.reset_size()
		_welcome.position = Vector2((vs.x - _welcome.size.x) * 0.5, vs.y * 0.36)


func pip_frame() -> Control:
	"""das Bild der Kopfkamera mit den Rahmen (für «Kamera» gross im Handy-Modus, handy.gd)"""
	return _pip.get_meta("frame") if _built else null


func _draw_boxes() -> void:
	var sz := _boxes.size
	var f := ThemeDB.fallback_font
	for d in dets:
		var r: Rect2 = d["r"]
		var rr := Rect2(r.position * sz, r.size * sz)
		var col := Color(1.0, 0.25, 0.2) if d["k"] == "person" and alarm else (Color(1.0, 0.82, 0.12) if d["k"] == "person" else Color(0.3, 0.8, 1.0))
		_boxes.draw_rect(rr, col, false, 2.0)
		var txt := "%s %.0f m" % [tx(d["k"]), d["d"]]
		var y := rr.position.y - 3.0 if rr.position.y > 14.0 else rr.end.y + 12.0
		_boxes.draw_rect(Rect2(rr.position.x, y - 11.0, f.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x + 6.0, 14.0), Color(0, 0, 0, 0.55))
		_boxes.draw_string(f, Vector2(rr.position.x + 3.0, y), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, col)


func _hide_pc() -> void:
	"""die Karten und Teile, die es nur am PC gibt (Verbindung zu MoveEye, Simulator-PC, Start mit dem PC, Updates)"""
	var ok := not _hidden.is_empty()
	for c in _hidden:
		if not is_instance_valid(c):
			ok = false
	if not ok or fmod(_t, 10.0) < 1.0:                   # neu suchen: am Anfang, nach einem Neubau, alle 10 s
		_hidden.clear()
		for n in main.ui_root.find_children("*", "VBoxContainer", true, false):
			if n.has_meta("title") and str(n.get_meta("title")) in HIDE:
				var c = n.get_meta("card") if n.has_meta("card") else n.get_meta("wrap", null)
				if c is Control:
					_hidden.append(c)
	for c in _hidden:
		if c.visible:
			c.visible = false
	for c in [main.mwpc_btn, main.mwpc_label]:
		if c != null and c.visible:
			c.visible = false


# ---- das kleine MoveEye --------------------------------------------------------------------------------------------------
func _detect() -> void:
	"""Personen und Tiere im Bild der Kopfkamera: die Hülle ihrer Teile durch die Kamera aufs Bild gelegt"""
	dets.clear()
	var cam: Camera3D = main.cams[0]
	var isz := Vector2(main.vps[0].size)
	if isz.x <= 0.0 or isz.y <= 0.0 or main.visitors == null:
		return
	for v in main.visitors.get_children():
		if not (v is Node3D) or not v.is_visible_in_tree() or bool(v.get("done")):
			continue
		var kind := str(v.get("kind"))
		if kind == "car" or kind == "":
			continue
		var d: float = cam.global_position.distance_to(v.global_position)
		if d > 35.0 or d < 0.4:
			continue
		var meshes: Array = v.get_meta("web_meshes") if v.has_meta("web_meshes") else []
		if meshes.is_empty():
			meshes = v.find_children("*", "MeshInstance3D", true, false)
			v.set_meta("web_meshes", meshes)
		var lo := Vector2(INF, INF)
		var hi := Vector2(-INF, -INF)
		var any := false
		for mi in meshes:
			if not is_instance_valid(mi) or not mi.is_visible_in_tree() or (mi.layers & cam.cull_mask) == 0:
				continue
			var bb: AABB = mi.global_transform * mi.get_aabb()
			for i in range(8):
				var p := bb.get_endpoint(i)
				if cam.is_position_behind(p):
					continue
				var s := cam.unproject_position(p)
				lo = lo.min(s)
				hi = hi.max(s)
				any = true
		if not any:
			continue
		var r := Rect2(lo, hi - lo).intersection(Rect2(Vector2.ZERO, isz))
		if r.size.y < 10.0 or r.size.x < 4.0:                # zu klein (weit weg) oder ausserhalb des Bildes
			continue
		dets.append({"r": Rect2(r.position / isz, r.size / isz), "k": "animal" if (v.has_method("is_animal") and v.call("is_animal")) else "person", "d": d,
				"pos": v.global_position})


func _alarm_step(dt: float) -> void:
	var person := false
	for d in dets:
		person = person or d["k"] == "person"
	_person_s = _person_s + dt if person else 0.0
	_gone_s = 0.0 if person else _gone_s + dt
	if armed and _person_s >= ALARM_S and not alarm:
		alarm = true
		alarm_t = _t
	if alarm and _gone_s > 30.0:
		alarm = false                                    # niemand mehr da: nach 30 s von selbst wieder ruhig


func _buttons() -> void:
	"""die Tasten im Fenster «Gerät» (statusled.gd zählt sie wie ein GPIO)"""
	var sl = main.statusled
	if sl == null:
		return
	for k in ["protect", "ack"]:
		var b: Dictionary = sl.btn[k]
		var s := int(b["seq"])
		if _seq[k] < 0:
			_seq[k] = s
			continue
		if s == _seq[k]:
			continue
		_seq[k] = s
		if k == "ack":
			alarm = false
		elif int(b["last_ms"]) >= 1500:
			armed = true                                 # lang = «Voll» – hier gleich wie Wachsam
		else:
			armed = not armed
			if not armed:
				alarm = false


func _guard(_dt: float) -> void:
	"""der Kopf bewacht selbst: zur nächsten Person (sonst zum nächsten Tier), sonst langsam hin und her"""
	var ks = main.kopf_selbst
	if ks == null or not ks.allowed():
		return
	if ks.active and (absf(float(ks.goal["pan"]) - float(_my_goal["pan"])) > 0.05 or absf(float(ks.goal["tilt"]) - float(_my_goal["tilt"])) > 0.05):
		_user_t = _t                                     # jemand hat die Pfeile benutzt: der Kopf gehört eine Weile ihm
	if _t - _user_t < USER_S:
		_my_goal = ks.goal.duplicate()
		return
	var best = null
	for d in dets:
		if best == null or (d["k"] == "person" and best["k"] != "person") or (d["k"] == best["k"] and d["d"] < best["d"]):
			best = d
	var pan := 55.0 * sin(_t * 0.18)
	var tilt := -4.0
	if best != null:
		var par: Node3D = main.head.get_parent()
		var lp: Vector3 = par.to_local(best["pos"]) - main.head.position
		pan = -rad_to_deg(atan2(-lp.x, -lp.z))
		tilt = clampf(rad_to_deg(atan2(lp.y + 0.8, Vector2(lp.x, lp.z).length())) + 6.0, -30.0, 20.0)
	if not ks.active:
		ks._take()
	ks.goal["pan"] = clampf(pan, -Kopf.LIMIT["pan"], Kopf.LIMIT["pan"])
	ks.goal["tilt"] = clampf(tilt, -Kopf.LIMIT["tilt"], Kopf.LIMIT["tilt"])
	ks.active = true
	_my_goal = ks.goal.duplicate()


func _visitors(dt: float) -> void:
	"""damit es in der Demo etwas zu sehen gibt: ist eine Weile niemand da, kommt jemand (abwechselnd Person und Tier)"""
	_quiet_s = _quiet_s + dt if main.visitors.get_child_count() == 0 else 0.0
	if _quiet_s > (6.0 if _spawn_i == 0 else 20.0):
		_quiet_s = 0.0
		main.spawn(["person", "fox", "person", "deer", "person", "cat"][_spawn_i % 6])
		_spawn_i += 1
