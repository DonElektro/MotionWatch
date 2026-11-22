extends CanvasLayer
## «Frei erkunden mit eigener Figur», Etappe 2 (Besitzer 21.11.2026): das Fenster «Figur gestalten». Knopf «🎨 Figur» in der
## Erkunden-Leiste (als Figur), Taste I, Steuerbefehl {"action": "explore", "gestalten": true | false, "figur": {…}}.
##   * Reiter Person · Kopf · Kleider · Ausrüstung · Unterwegs (Begleiter Maggie / Blinki, MoveEye sieht die Figur, Auge-Symbol)
##   * jede Wahl gilt sofort: die Figur wird neu gebaut (explore_person.figur_setzen) und steht als Vorschau vor der Kamera
##     (Porträt von vorn, lebend in der Welt - so wie MoveEye sie sieht), gespeichert in main.ex_figur
##   * PC / iPad quer: das Fenster rechts, die Figur links daneben; Handy hochkant: das Fenster unten, die Figur oben
##   * «Zufall», «Zurücksetzen», «Fertig» (Esc)
## Farben als Felder, alles andere als Knöpfe (Daumen-gross auf dem Handy). Texte in 5 Sprachen (T.t).

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const EF = preload("res://scripts/erkunden_figur.gd")
const RS = preload("res://scripts/erkunden_rucksack.gd")
const AbD = preload("res://scripts/bergtal_abenteuer_daten.gd")

const REITER := [["person", "Person"], ["kopf", "Kopf"], ["kleider", "Kleider"], ["ausruestung", "Ausrüstung"], ["rucksack", "Rucksack"], ["unterwegs", "Unterwegs"], ["welt", "Welt"]]
const INHALT := {"person": [["sex", "Geschlecht"], ["alter", "Alter"], ["groesse", "Grösse"], ["bau", "Statur"]],
		"kopf": [["haar", "Frisur"], ["haarfarbe", "Haarfarbe"], ["haut", "Hautfarbe"], ["bart", "Bart"]],
		"kleider": [["jacke", "Jacke"], ["hose", "Hose"], ["hut", "Kopfbedeckung"], ["rucksack", "Rucksack"]],
		"ausruestung": [["stirnlampe", "Stirnlampe (leuchtet nachts)"], ["stoecke", "Wanderstöcke"], ["feldstecher", "Feldstecher"]],
		"rucksack": [],
		"welt": [],
		"unterwegs": [["ex_kraft_echt", "Kraft, Hunger, Durst, Kälte: «Echt» (aus = «Entspannt»)"], ["ex_maggie", "Maggie kommt mit"], ["ex_blinki", "Blinki kommt mit"],
				["ex_mw_sieht", "MoveEye sieht die Figur (Bild und Alarm)"], ["ex_auge", "Auge-Symbol «MoveEye sieht dich»"]]}

var person
var main
var offen := false
var reiter := "person"
var panel: PanelContainer
var _tabs: HFlowContainer
var _body: VBoxContainer
var _scroll: ScrollContainer
var _knoepfe := {}                   # id -> Button (tests)


func _ready() -> void:
	layer = 20                                                   # above the green stick and the edge buttons
	panel = PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL.r, UI.PANEL.g, UI.PANEL.b, 0.94), UI.LINE, 12, 10, 1))
	panel.visible = false
	add_child(panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	panel.add_child(v)
	var kopf := HBoxContainer.new()
	v.add_child(kopf)
	var ti := Label.new()
	ti.name = "titel"
	ti.add_theme_font_override("font", UI.heading_font())
	ti.add_theme_font_size_override("font_size", 17)
	ti.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	kopf.add_child(ti)
	var fertig := Button.new()
	fertig.name = "fertig"
	fertig.focus_mode = Control.FOCUS_NONE
	fertig.pressed.connect(func(): zeigen(false))
	UI.primary(fertig)
	kopf.add_child(fertig)
	_tabs = HFlowContainer.new()                                  # wraps on the phone (no cut words)
	_tabs.add_theme_constant_override("h_separation", 4)
	_tabs.add_theme_constant_override("v_separation", 4)
	v.add_child(_tabs)
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(_scroll)
	_body = VBoxContainer.new()
	_body.add_theme_constant_override("separation", 10)
	_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.add_child(_body)
	var unten := HBoxContainer.new()
	unten.add_theme_constant_override("separation", 8)
	v.add_child(unten)
	for e in [["zufall", "Zufällige Figur"], ["zurueck", "Zurücksetzen"]]:
		var b := Button.new()
		b.name = str(e[0])
		b.focus_mode = Control.FOCUS_NONE
		b.set_meta("t", str(e[1]))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var id := str(e[0])
		b.pressed.connect(func(): _wahl(EF.zufall() if id == "zufall" else EF.DEFAULT.duplicate()))
		unten.add_child(b)
	get_viewport().size_changed.connect(_layout)


func zeigen(on: bool) -> void:
	if on and (person == null or not person.ok() or not bool(person.active)):
		return
	var war := offen
	offen = on
	panel.visible = on
	if on:
		person.portrait_start()
		_bauen()
		_layout()
	elif war and person != null and person.ok():
		person.portrait_ende()


func _handy() -> bool:
	var s: Vector2 = get_viewport().get_visible_rect().size
	return s.y > s.x


func _layout() -> void:
	if not offen:
		return
	var s: Vector2 = get_viewport().get_visible_rect().size
	if _handy():                                             # upright: the window below, the figure above
		panel.position = Vector2(6, s.y * 0.46)
		panel.size = Vector2(s.x - 12.0, s.y * 0.54 - 70.0)
	else:
		var w := clampf(s.x * 0.36, 340.0, 460.0)
		panel.position = Vector2(s.x - w - 10.0, 60.0)
		panel.size = Vector2(w, s.y - 130.0)
	panel.custom_minimum_size = panel.size


func _wahl(d: Dictionary) -> void:
	person.figur_setzen(d)
	person.portrait_start()
	_bauen()


func setze(feld: String, wert) -> void:
	"""one choice (a button, a colour, a switch) - fields of the figure or the switches of «Unterwegs» (main.ex_*)"""
	if feld.begins_with("ex_"):
		main.set(feld, bool(wert))
		main._settings_dirty = true
		_bauen()
		return
	_wahl(EF.setzen(person.figur_wahl(), feld, wert))


func _bauen() -> void:
	var ti: Label = panel.find_child("titel", true, false)
	ti.text = T.t("Figur gestalten")
	(panel.find_child("fertig", true, false) as Button).text = T.t("Fertig")
	for b in [panel.find_child("zufall", true, false), panel.find_child("zurueck", true, false)]:
		(b as Button).text = T.t(str(b.get_meta("t")))
	for c in _tabs.get_children():
		c.queue_free()
	var gross := _handy()
	for r in REITER:
		var tb := Button.new()
		tb.text = T.t(str(r[1]))
		tb.toggle_mode = true
		tb.button_pressed = str(r[0]) == reiter
		tb.focus_mode = Control.FOCUS_NONE
		tb.custom_minimum_size = Vector2(0, 40 if gross else 32)
		tb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		tb.add_theme_font_size_override("font_size", 13)
		var rid := str(r[0])
		tb.pressed.connect(func(): reiter = rid; _bauen())
		if rid == reiter:
			UI.primary(tb)
		_tabs.add_child(tb)
	for c in _body.get_children():
		c.queue_free()
	_knoepfe = {}
	if reiter == "rucksack":
		_rucksack_bauen(gross)
		return
	if reiter == "welt":
		_welt_bauen(gross)
		return
	var fd: Dictionary = person.figur_wahl()
	for zeile in INHALT[reiter]:
		var feld := str(zeile[0])
		var lb := UI.small(T.t(str(zeile[1])), UI.TXT)
		_body.add_child(lb)
		var fl := HFlowContainer.new()
		fl.add_theme_constant_override("h_separation", 6)
		fl.add_theme_constant_override("v_separation", 6)
		_body.add_child(fl)
		if feld.begins_with("ex_") or feld in EF.SCHALTER:
			var an: bool = bool(main.get(feld)) if feld.begins_with("ex_") else bool(fd[feld])
			var gesperrt: bool = feld == "bart" and (str(fd["sex"]) != "m" or str(fd["alter"]) != "erw")
			for e in [[true, "an"], [false, "aus"]]:
				var b := _chip(T.t(str(e[1])), an == bool(e[0]), gross)
				b.disabled = gesperrt
				var w = bool(e[0])
				b.pressed.connect(func(): setze(feld, w))
				fl.add_child(b)
				_knoepfe["%s=%s" % [feld, str(e[0]).to_lower()]] = b
			if gesperrt:
				_body.add_child(UI.small(T.t("Nur für erwachsene Männer"), UI.MUT))
		elif EF.OPT.has(feld):
			for o in EF.OPT[feld]:
				var b2 := _chip(T.t(str(o[1])), str(fd[feld]) == str(o[0]), gross)
				var w2 := str(o[0])
				b2.pressed.connect(func(): setze(feld, w2))
				fl.add_child(b2)
				_knoepfe["%s=%s" % [feld, w2]] = b2
		else:
			for hx in EF._werte(feld):
				var b3 := _farbe(str(hx), str(fd[feld]) == str(hx), gross)
				var w3 := str(hx)
				b3.pressed.connect(func(): setze(feld, w3))
				fl.add_child(b3)
				_knoepfe["%s=%s" % [feld, w3]] = b3


const ZEITEN := [[7.0, "Morgen"], [12.0, "Mittag"], [19.5, "Abend"], [23.0, "Nacht"]]
const WETTER := [["clear", "klar"], ["cloudy", "bewölkt"], ["rain", "Regen"], ["fog", "Nebel"], ["snow", "Schnee"]]


func _welt_bauen(gross: bool) -> void:
	"""Etappe 4: time of day, weather, remember the place, the photo mode"""
	_body.add_child(UI.small(T.t("Tageszeit") + "  (" + person.sachen._zeit() + ")", UI.TXT))
	var fl := HFlowContainer.new()
	fl.add_theme_constant_override("h_separation", 6)
	_body.add_child(fl)
	var h: float = float(main.hour())
	for z in ZEITEN:
		var b := _chip(T.t(str(z[1])), absf(h - float(z[0])) < 0.3, gross)
		var w := float(z[0])
		b.pressed.connect(func(): main.set_hour(w); _bauen())
		fl.add_child(b)
		_knoepfe["zeit=" + str(z[1])] = b
	_body.add_child(UI.small(T.t("Wetter"), UI.TXT))
	var fl2 := HFlowContainer.new()
	fl2.add_theme_constant_override("h_separation", 6)
	_body.add_child(fl2)
	for wt in WETTER:
		var b2 := _chip(T.t(str(wt[1])), str(main.weather) == str(wt[0]), gross)
		var w2 := str(wt[0])
		b2.pressed.connect(func(): main.weather = w2; main._settings_dirty = true; _bauen())
		fl2.add_child(b2)
		_knoepfe["wetter=" + w2] = b2
	_body.add_child(UI.small(T.t("Ort"), UI.TXT))
	var o: Dictionary = person.extras.ort()
	_body.add_child(UI.small(T.t("Gemerkt: %s") % str(o.get("name", "")) if not o.is_empty() else T.t("Noch kein Ort gemerkt"), UI.MUT))
	var b3 := _chip(T.t("Ort hier merken (nächstes Mal weiter hier)"), false, gross)
	b3.pressed.connect(func(): person.extras.ort_merken(); _bauen())
	_body.add_child(b3)
	_knoepfe["ort_merken"] = b3
	var b4 := _chip(T.t("Fotomodus (P)"), false, gross)
	b4.pressed.connect(func(): zeigen(false); person.extras.fotomodus(true))
	_body.add_child(b4)
	_knoepfe["fotomodus"] = b4


func _rucksack_bauen(gross: bool) -> void:
	"""Etappe 3: pack like in the adventure - 30 / 50 / 70 L, every thing with − / +, weight and volume"""
	var r: Dictionary = RS.norm(main.get("ex_rucksack"))
	_body.add_child(UI.small(T.t("Rucksack"), UI.TXT))
	var fl := HFlowContainer.new()
	fl.add_theme_constant_override("h_separation", 6)
	_body.add_child(fl)
	for pk in ["30", "50", "70"]:
		var b := _chip(T.t(str(AbD.PACKS[pk][0])), str(r["pack"]) == pk, gross)
		var w: String = pk
		b.pressed.connect(func(): main.ex_rucksack = RS.pack_setzen(RS.norm(main.get("ex_rucksack")), w); main._settings_dirty = true; _bauen())
		fl.add_child(b)
		_knoepfe["pack=" + pk] = b
	var kg := RS.gewicht(r)
	var zu_schwer := kg > RS.bequem(r)
	var sum := UI.small(T.t("%.1f kg (bequem bis %d kg) · %d von %d Liter") % [kg, int(RS.bequem(r)), int(RS.volumen(r)), int(RS.platz(r))],
			UI.ORG if zu_schwer else UI.MUT)
	sum.name = "summe"
	_body.add_child(sum)
	for id in RS.ORDER:
		var e: Array = RS.item(id)
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 6)
		_body.add_child(row)
		var lb := Label.new()
		var n := RS.anzahl(r, id)
		lb.text = "%s%s" % [T.t(str(e[0])), (" × %d" % n) if n > 1 else ""]
		lb.tooltip_text = T.t(str(e[4]))
		lb.mouse_filter = Control.MOUSE_FILTER_PASS
		lb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		lb.clip_text = true
		lb.add_theme_color_override("font_color", UI.TXT if n > 0 else UI.MUT)
		row.add_child(lb)
		var kgl := UI.small("%.1f kg" % float(e[1]), UI.MUT)
		kgl.custom_minimum_size = Vector2(54, 0)
		row.add_child(kgl)
		for k in [-1, 1]:
			var b2 := Button.new()
			b2.text = "−" if k < 0 else "+"
			b2.focus_mode = Control.FOCUS_NONE
			b2.custom_minimum_size = Vector2(44 if gross else 34, 40 if gross else 30)
			b2.disabled = (k < 0 and n == 0) or (k > 0 and n >= int(e[5]))
			var iid := str(id)
			var kk := int(k)
			b2.pressed.connect(func():
				var res: Dictionary = RS.dazu(RS.norm(main.get("ex_rucksack")), iid, kk)
				if bool(res["ok"]):
					main.ex_rucksack = res["d"]
					main._settings_dirty = true
				elif person.sachen != null:
					person.sachen.sag(T.t(str(res["grund"])))
				_bauen())
			row.add_child(b2)
			_knoepfe["%s%s" % [id, "+" if k > 0 else "-"]] = b2


func _chip(text: String, an: bool, gross: bool) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(64, 44 if gross else 34)
	if an:
		UI.primary(b)
	return b


func _farbe(hx: String, an: bool, gross: bool) -> Button:
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	var d := 44 if gross else 34
	b.custom_minimum_size = Vector2(d, d)
	b.tooltip_text = "#" + hx
	for st in ["normal", "hover", "pressed"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color.html(hx)
		sb.set_corner_radius_all(int(d / 2.0))
		sb.border_color = UI.ACC if an else Color(1, 1, 1, 0.35)
		sb.set_border_width_all(4 if an else 1)
		b.add_theme_stylebox_override(st, sb)
	return b


func _unhandled_key_input(ev: InputEvent) -> void:
	if offen and ev is InputEventKey and ev.pressed and (ev as InputEventKey).keycode == KEY_ESCAPE:
		zeigen(false)
		get_viewport().set_input_as_handled()


func _process(_dt: float) -> void:
	if offen and (person == null or not person.ok() or not bool(person.active) or not bool(person.ex.on)):
		zeigen(false)


func druecke(id: String) -> bool:
	"""tests: press a button of the window («feld=wert», «zufall», «zurueck», «fertig», a tab «reiter:kopf»)"""
	if id.begins_with("reiter:"):
		reiter = id.substr(7)
		_bauen()
		return true
	var b: Button = _knoepfe.get(id, panel.find_child(id, true, false))
	if b == null or b.disabled:
		return false
	b.pressed.emit()
	return true


func info() -> Dictionary:
	return {"offen": offen, "reiter": reiter, "knoepfe": _knoepfe.keys().size(),
			"rect": [int(panel.position.x), int(panel.position.y), int(panel.size.x), int(panel.size.y)]}
