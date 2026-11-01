extends PanelContainer
## 3D-3.82 (Wunsch Daniel, während dem grossen Makeover): nach jedem Update erscheint einmal eine kurze Info «Neu in dieser
## Version» - alle Versionen seit der zuletzt gesehenen (aus neu_data.gd, erzeugt aus «Lies mich.txt») und «Als Nächstes im
## Makeover» (NEXT_ALL ohne DONE, bei jeder Makeover-Version nachführen). main.news_seen / main.news_popup sind in KEEP.
## Links zu Neuerungen (Daniel 01.11.2026, wie MoveEye Teil 137 / 639zc): bei jeder Neuerung ein kleiner Link zur Funktion -
## Ziele aus res://ui_gemeinsam.json «neu_ziele» (sim_einstellung: Karte aufklappen und hervorheben, sim_menue «Gruppe/Teil»,
## sim_aktion: eine Aktion von main_steuerung). Nur in MoveEye: Hinweis «in MoveEye» (verbunden: öffnet die Seite im Browser).
## Schalter main.news_links (auto | on | off, Entwickler-Fenster, mit MoveEye geteilt); auto = Projektschalter
## «projekt_veroeffentlicht» (false: an, true: aus).

var main
var _box: VBoxContainer

const UI = preload("res://scripts/ui_style.gd")
const Data = preload("res://scripts/neu_data.gd")
const UG = preload("res://scripts/ui_gemeinsam.gd")
const AB = preload("res://scripts/abgleich.gd")
const SIM_KEYS := ["sim_einstellung", "sim_menue", "sim_aktion"]
const MW_KEYS := ["seite", "anker", "einstellung"]

const NEXT_ALL := [
	[1, "Ein gemeinsames Erscheinungsbild (Web, Fenster, Simulator)"], [2, "Simulations-Modus sichtbar (oranger Streifen «SIMULATION»)"],
	[3, "Startseite mit Simulator-Kachel"], [4, "Kachel-Steuerung des Simulators auf dem Handy"], [5, "Kino-Modus (Vollbild für TV / Beamer)"],
	[6, "Einheitliche Ereignis-Symbole"], [7, "Simulator-Zentrale in MoveEye"], [8, "«Was wäre wenn …?» bei echten Alarmen"],
	[9, "Dein Platz (Ort, Winkel, Zonen, Patrouille)"], [10, "Zonen im Simulator sehen"], [11, "Erkennung live in der 3D-Ansicht"],
	[12, "Automatische Trainings-Nacht"], [13, "Einstellungs-Vergleich A/B"], [14, "Benachrichtigungen testen (Test-Kanal)"],
	[15, "Akku-, Wetter- und WLAN-Ausfall üben"], [16, "Mehrere MoveEye-Geräte im Simulator"], [17, "Rover voll integriert"],
	[18, "Tagebuch-Statistik aus dem Simulator"], [19, "Versionen vergleichen (Kurve)"], [20, "Ein-Klick-Demo"],
	[21, "Fehlalarm-Lernen"], [22, "Karte der blinden Flecken"], [23, "Nacht-Generalprobe vor dem Scharfschalten"],
	[24, "Schwellen automatisch einstellen"], [25, "Erkennungs-Check jede Woche"]]
const DONE := [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]                       # numbers already delivered (nachführen)


static func _vt(v: String) -> Array:
	"""Versionierung 3.0.0: «3D-4.82» and «3.0.0» in one order (versionen.gd) - the last seen may still be «3D-4.8x»"""
	return preload("res://scripts/versionen.gd").key(v)


static func _newer(a: String, b: String) -> bool:
	"""a > b"""
	return preload("res://scripts/versionen.gd").newer(a, b)


func entries(seen: String) -> Array:
	var out := []
	for e in Data.LOG:
		var v: String = e[0]
		if (seen == "" and v == main.VERSION) or (seen != "" and _newer(v, seen) and not _newer(v, main.VERSION)):
			out.append(e)
	return out.slice(0, 6)


static func links_on(m) -> bool:
	"""«Links zu Neuerungen»: own choice, otherwise the project switch (not published = on)"""
	var v := str(m.get("news_links")) if m != null and m.get("news_links") != null else "auto"
	if v == "on" or v == "off":
		return v == "on"
	return not bool(UG.data().get("projekt_veroeffentlicht", false))


static func ziel(v: String) -> Dictionary:
	var zs = UG.data().get("neu_ziele", {})
	var z = zs.get(v, null) if typeof(zs) == TYPE_DICTIONARY else null
	return z if typeof(z) == TYPE_DICTIONARY else {}


static func _has(z: Dictionary, keys: Array) -> bool:
	for k in keys:
		if z.has(k) and str(z[k]) != "":
			return true
	return false


static func mw_href(z: Dictionary) -> String:
	"""the page of MoveEye (the same rule as news_href in MoveEye, Teil 137)"""
	var page := str(z.get("seite", ""))
	var a := str(z.get("anker", ""))
	var k := str(z.get("einstellung", ""))
	if page == "" and a == "" and k == "":
		return ""
	if not page.begins_with("/"):
		page = "/settings" if (a != "" or k != "") else "/"
	if k != "":
		return page + "?setting=" + k.uri_encode()
	if a.begins_with("grp:") or a.begins_with("sec:"):
		return page + "?open=" + a.uri_encode()
	return page + ("#" + a.uri_encode() if a != "" else "")


func link_kind(v: String) -> String:
	"""'' (no link) | sim (jumps here) | mw (only in MoveEye)"""
	if not links_on(main):
		return ""
	var z := ziel(v)
	if _has(z, SIM_KEYS):
		return "sim"
	if _has(z, MW_KEYS):
		return "mw"
	return ""


func _mw_on() -> bool:
	return str(main.mw_addr) != "" and main.now() - float(main.mw_t) <= 10.0


func go(v: String) -> Dictionary:
	"""the link of a version: close the window and jump to the function"""
	var z := ziel(v)
	if z.is_empty() or not links_on(main):
		return {"ok": false, "error": "no link"}
	if visible:
		close(false)
	if typeof(z.get("sim_aktion")) == TYPE_DICTIONARY:
		var r = main.control(z["sim_aktion"])
		return {"ok": true, "to": "aktion", "r": r}
	if str(z.get("sim_einstellung", "")) != "":
		return goto_setting(str(z["sim_einstellung"]))
	if str(z.get("sim_menue", "")) != "":
		return goto_menu(str(z["sim_menue"]))
	var h := mw_href(z)
	if h != "" and _mw_on():
		OS.shell_open("%s://%s:%d%s" % [str(main.mw.get("mw_scheme", "http")), main.mw_addr, int(main.mw.get("mw_port", 5000)), h])
		return {"ok": true, "to": "moveeye", "href": h}
	return {"ok": false, "to": "moveeye", "href": h, "error": "mw_only"}


func goto_setting(id: String) -> Dictionary:
	"""open the card (and part) of a setting, scroll there and mark it; hidden in «Einfach»: the search field finds it"""
	var c = null
	for x in main.controls:
		if str(x.id) == id:
			c = x
			break
	if c == null:
		return {"ok": false, "error": "unknown setting " + id}
	if c.extra.get("devwin", false):
		return main.dev_window("schalter")
	main.show_panel(true)
	var it = null
	for x in main.ui_items:
		if str(x[1]) == str(c.label):
			it = x
			break
	if it == null:
		return {"ok": false, "error": "not in the panel " + id}
	_open_item(it)
	if not (it[0] as Control).is_visible_in_tree() and main.search_in != null:
		main.search_in.text = str(c.label)                # e.g. a «Experte» setting while «Einfach» is on
		main._search(str(c.label))
	_mark(it[0])
	return {"ok": true, "to": "setting", "id": id, "visible": (it[0] as Control).is_visible_in_tree()}


func _open_item(it: Array) -> void:
	var body: Control = it[3]
	if body.has_meta("card"):
		(body.get_meta("card") as Control).visible = true
	UI.set_open(body, true)
	if it.size() > 4 and it[4] != it[3]:
		var sb: Control = it[4]
		UI.set_sub_open(sb, true)
		if sb.has_meta("wrap"):
			(sb.get_meta("wrap") as Control).visible = true
		if sb.has_meta("outer"):
			UI.set_sub_open(sb.get_meta("outer"), true)


func goto_menu(path: String) -> Dictionary:
	"""«Gruppe/Teil»: open the card and its part, scroll there and mark it"""
	var parts := path.split("/")
	var body = main.group_bodies.get(parts[0], null)
	if body == null:
		return {"ok": false, "error": "unknown group " + parts[0]}
	main.show_panel(true)
	if (body as Control).has_meta("card"):
		((body as Control).get_meta("card") as Control).visible = true
	UI.set_open(body, true)
	var mark: Control = body
	if parts.size() > 1:
		for sb in main.sub_bodies:
			if is_instance_valid(sb) and str(sb.get_meta("title", "")) == parts[1] and (body as Control).is_ancestor_of(sb):
				UI.set_sub_open(sb, true)
				mark = sb.get_meta("wrap") if sb.has_meta("wrap") else sb
				mark.visible = true
				break
	_mark(mark)
	return {"ok": true, "to": "menu", "path": path, "found": mark != body or parts.size() == 1}


func _mark(w: Control) -> void:
	"""scroll to it and let it light up three times (like the marked row in MoveEye)"""
	if w == null or not is_instance_valid(w):
		return
	var tw := w.create_tween()
	for i in 3:
		tw.tween_property(w, "modulate", Color(1.5, 1.35, 0.7), 0.35)
		tw.tween_property(w, "modulate", Color(1, 1, 1), 0.35)
	await get_tree().process_frame
	await get_tree().process_frame
	if not is_instance_valid(w):
		return
	var p := w.get_parent()
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null:
		(p as ScrollContainer).ensure_control_visible(w)


func pick(vs) -> Array:
	"""the entries of these versions (for tests and «show»: empty = the usual choice)"""
	var out := []
	if typeof(vs) == TYPE_ARRAY:
		for e in Data.LOG:
			if str(e[0]) in vs:
				out.append(e)
	return out


func next_list(n := 5) -> Array:
	var out := []
	for x in NEXT_ALL:
		if not (x[0] in DONE):
			out.append(x)
	return out.slice(0, n)


var _scroll: ScrollContainer = null
var _list: VBoxContainer = null


func _ready() -> void:
	visible = false
	add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.97), UI.ORG, 16, 14, 2))
	_box = VBoxContainer.new()
	_box.add_theme_constant_override("separation", 6)
	add_child(_box)


func check() -> void:
	"""at the start: show once per version"""
	if main.news_seen == main.VERSION or not main.news_popup:
		return
	var es := entries(main.news_seen)
	if es.is_empty():
		main.news_seen = main.VERSION
		main._settings_dirty = true
		return
	show_news(es)


func show_news(es := []) -> void:
	if es.is_empty():
		es = entries(main.news_seen) if main.news_seen != main.VERSION else []
	if es.is_empty():
		es = [Data.LOG[0]] if not Data.LOG.is_empty() else []
	for c in _box.get_children():
		c.queue_free()
	var tag := UI.small("MOVEEYE SIM · " + main.VERSION, UI.ORG)
	_box.add_child(tag)
	_box.add_child(UI.heading("✨ Neu in dieser Version"))
	# 3D-4.x: the list scrolls - the window is never higher than the screen, OK always reachable (Daniel 31.10.)
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 6)
	_scroll.add_child(_list)
	_box.add_child(_scroll)
	for e in es:
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 10)
		var v := Label.new()
		v.text = e[0]
		v.add_theme_color_override("font_color", UI.ACC)
		v.custom_minimum_size = Vector2(64, 0)
		v.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		h.add_child(v)
		var col := VBoxContainer.new()
		col.add_theme_constant_override("separation", 2)
		var t := Label.new()
		t.text = e[1]
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		t.custom_minimum_size = Vector2(500, 0)
		t.add_theme_font_size_override("font_size", 13)
		col.add_child(t)
		var lk := _link(str(e[0]))                         # Links zu Neuerungen
		if lk != null:
			col.add_child(lk)
		h.add_child(col)
		_list.add_child(h)
	var nx := next_list()
	if not nx.is_empty():
		var hd := Label.new()
		hd.text = "→ Als Nächstes im Makeover (%d/%d erledigt)" % [DONE.size(), NEXT_ALL.size()]
		hd.add_theme_font_size_override("font_size", 14)
		_list.add_child(hd)
		for x in nx:
			_list.add_child(UI.small("   %d. %s" % [x[0], x[1]]))
	var b := HBoxContainer.new()
	b.alignment = BoxContainer.ALIGNMENT_END
	b.add_theme_constant_override("separation", 8)
	_box.add_child(b)
	var off := Button.new()
	off.text = "Nicht mehr anzeigen"
	off.pressed.connect(func(): close(true))
	b.add_child(off)
	var ok := Button.new()
	ok.text = "OK"
	ok.custom_minimum_size = Vector2(90, 0)
	UI.primary(ok)
	ok.pressed.connect(func(): close(false))
	b.add_child(ok)
	visible = true
	get_parent().move_child(self, -1)


func _link(v: String) -> Control:
	var k := link_kind(v)
	if k == "":
		return null
	if k == "mw" and not _mw_on():
		var l := UI.small("(" + AB.txt("neu_in_mw") + ")", UI.MUT)
		l.name = "neu_link"
		return l
	var b := LinkButton.new()
	b.name = "neu_link"
	b.text = AB.txt("neu_link") if k == "sim" else AB.txt("neu_in_mw") + " ›"
	b.underline = LinkButton.UNDERLINE_MODE_ON_HOVER
	b.add_theme_font_size_override("font_size", 12)
	b.add_theme_color_override("font_color", UI.ACC)
	b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	b.pressed.connect(func(): go(v))
	return b


func _unhandled_input(ev: InputEvent) -> void:
	if visible and ev is InputEventKey and ev.pressed and not ev.echo and ev.keycode == KEY_ESCAPE:
		close(false)
		get_viewport().set_input_as_handled()


func close(off: bool) -> void:
	visible = false
	main.news_seen = main.VERSION
	if off:
		main.news_popup = false
	main._settings_dirty = true


func _process(_dt: float) -> void:
	if visible:
		var vs := get_viewport_rect().size
		if _scroll != null and is_instance_valid(_scroll):
			var room := maxf(120.0, vs.y - 48.0 - (_box.get_combined_minimum_size().y - _scroll.get_combined_minimum_size().y) - 40.0)
			_scroll.custom_minimum_size = Vector2(_list.get_combined_minimum_size().x + 14.0, minf(_list.get_combined_minimum_size().y, room))
		size = get_combined_minimum_size()
		position = ((vs - size) / 2.0).floor()


func info() -> Dictionary:
	var lk := {}
	for e in Data.LOG:
		var k := link_kind(str(e[0]))
		if k != "":
			lk[str(e[0])] = k
	var shown := 0
	if visible and _list != null and is_instance_valid(_list):
		shown = _list.find_children("neu_link", "", true, false).size()
	return {"visible": visible, "seen": main.news_seen, "popup": main.news_popup, "entries": entries(main.news_seen).map(func(e): return e[0]), "next": next_list().size(),
			"links_on": links_on(main), "news_links": str(main.get("news_links")), "links": lk, "links_shown": shown}
