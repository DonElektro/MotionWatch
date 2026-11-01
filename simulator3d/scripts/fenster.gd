extends Node
## Paket «Fenster im Simulator» (31.10.2026, Wunsch des Besitzers: 1a, 2a, 3a, 4): EIN Rahmen für alle schwebenden Fenster über
## der 3D-Ansicht - Kompass, Karte, Livebild, SmallTV, Gerät, Mover-Stick, Kopf steuern, Kameras (Bedienfeld zu), CPU -
## im Aussehen des alten Fensters «Kameras» (dunkle Karte, runde Ecken, Titelleiste mit ✥):
##   * Titelleiste ziehen = verschieben (Maus; Finger über die Maus-Nachbildung von Godot, emulate_mouse_from_touch)
##   * Ecke unten rechts ziehen = Grösse (der Griff erscheint, wenn die Maus über dem Fenster ist); Grenzen pro Fenster;
##     Bilder (Karte, Kameras, Livebild, SmallTV) ändern nur die Breite - die Höhe folgt, das Seitenverhältnis bleibt
##   * «✕» blendet aus; zurück über «Fenster» in der Leiste unten (Liste mit Häkchen + «Anordnung zurücksetzen»);
##     Fenster mit eigener Taste (M Karte, L Livebild …) schalten über dieselbe Stelle wie die Taste
##   * schnappt an den Bildschirmrand (14 px wie die alten Plätze), ans Bedienfeld, an die Leiste unten und an andere
##     Fenster (Fang 12 px)
##   * Doppelklick auf die Titelleiste = zurück an den Standardplatz
##   * merkt sich Ort, Grösse und «ausgeblendet» pro PC in user://fenster.json; der Ort relativ zum freien Platz
##     (0 = links / oben, 1 = rechts / unten), damit er eine andere Auflösung übersteht; beim Start ins Bild geholt.
##     Die Grösse bleibt in Pixeln (die Schrift wächst nicht mit der Auflösung), wird aber ins Fenster eingepasst.
## Solange ein Fenster nie verschoben wurde, steht es am alten Platz (folgt dem Handy-Simulator, dem Bedienfeld …).
## Rechnet in den Koordinaten der Ansicht (get_visible_rect): eine Grössen-Einstellung der Oberfläche
## (content_scale_factor) gilt damit von selbst. Leicht für Lite: keine Schatten, kein Shader; pro Fenster nur ein paar
## Vergleiche je Bild, Titel 4 × pro Sekunde.
##
## Ein neues Fenster anmelden - eine Zeile (z. B. Blinki-Hinweis, Entdeckerbuch auf den anderen Zweigen):
##   main.fenster.add("blinki", "Blinki", mein_panel)
##   main.fenster.add("buch", "Entdeckerbuch", panel, {"resize": "w", "min": Vector2(260, 0), "max": Vector2(640, 0)})
## Der Inhalt darf schon in einer Ebene hängen (er wird an derselben Stelle in den Rahmen gehängt) oder noch nirgends
## (dann kommt er in main.ui_layer). Optionen (alle freiwillig):
##   home: Vector2 oder Callable(win) -> Vector2   Platz, solange nie verschoben (Standard: links oben gestapelt)
##   resize: "none" (Standard) | "w" (Breite; Höhe folgt dem Inhalt - für Bilder) | "wh" (frei)
##   min / max: Vector2   Grenzen der Inhaltsgrösse (bei "w" zählt x)
##   set_size: Callable(w, h)   wie der Inhalt eine neue Grösse übernimmt (Standard: custom_minimum_size)
##   on / set_on: Callable() -> bool / Callable(bool)   eigener Schalter (Taste, Einstellung) statt des Häkchens hier
##   shown: Callable() -> bool   will der Inhalt jetzt gezeigt werden (Standard: inhalt.visible)
##   hint: String   kurzer Hinweis in der Liste (z. B. «nur mit Mover»)
##   compact: true   schmale Leiste ohne Titeltext (Kompass, CPU); der Titel steht dann im Tooltip
##   hide: [Control]   Teile des Inhalts, die der Rahmen ersetzt (eigene Titelzeile)
##   on_hide: Callable()   das Fenster ist eben verschwunden
##   list: false   nicht in der Liste «Fenster»
## Der Inhalt bekommt set_meta("fenster", id): Skripte, die sich bisher selbst platziert haben, lassen das dann.
## Tests: /control {"action": "fenster", "do": "info" | "drag" | "resize" | "close" | "list" | "check" | "reset" | "over"}
##
## Paket «Andocken» (Besitzer 01.11.2026, wie die Karten in MoveEye):
##   * Andockleisten links und rechts (Spalten, optional unten): die Fenster rasten ohne Überlappung ein, die Werkzeugleiste
##     unten und der Knopf «Bedienfeld zeigen» bleiben frei (pack(): rein rechnerisch, Test werkzeuge/fenster_dock_test.gd)
##   * passt sich an Fenstergrösse / Auflösung an: Bilder (Karte, Livebild, SmallTV, Kameras …) wachsen mit der Höhe der
##     Ansicht und werden kleiner, bis alles in eine Spalte je Seite passt (schmal: 1 Spalte, ab 1700 px: 2)
##   * «Neu anordnen» in der Liste «Fenster»; ziehen bleibt frei: loslassen am Rand = andocken (Reihenfolge nach der Höhe),
##     anderswo = frei schwebend (wie bisher, mit Schnappen); Doppelklick = zurück in die Leiste. Alles in fenster.json.
##   * Karte, Kompass, SmallTV und CPU in EINEM Seitenfenster mit Reitern (Fenster «tabs»); jedes bleibt als Reiter
##     erreichbar und in der Liste; Schalter «… als Reiter» in der Liste (aus = einzelne Fenster wie bisher)
##   * Optionen: top (immer zuoberst), fold (einklappbar zur schmalen Leiste), sizes (Knopf klein / mittel / gross),
##     fit: false (zählt nicht beim Einpassen), auto: false (Grösse nie automatisch). Entwickler: alle vier.
##   * /control {"action": "fenster", "do": "arrange" | "layout" | "tab" (id) | "fold" (id, on) | "dock" (on) | "tabs" (on)}

const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
const FILE := "user://fenster.json"
const SNAP := 12.0                     # Fang beim Schnappen (px)
const EDGE := 14.0                     # Abstand zum Bildschirmrand (wie die alten Plätze)
const GAP := 6.0                       # Abstand zwischen zwei Fenstern
const STACK := ["compass", "map", "live", "smalltv"]   # links oben untereinander (wie bisher)

var main
var wins := {}                         # id -> Win
var order: Array = []                  # ids in the order they were added
var _saved := {}                       # from user://fenster.json
var _save_t := -1.0
var _vs := Vector2.ZERO
var _list: PanelContainer = null
var _list_anchor: Control = null
var _checks := {}                      # id -> CheckBox of the open list
var _list_t := 0.0

# ---- Paket «Andocken» -------------------------------------------------------------------------------------------------------
## id -> [Leiste "L" | "R" | "B", Reihenfolge, unten in der Spalte]; nicht aufgeführte Fenster schweben wie bisher
const DOCK_DEF := {"tabs": ["L", 0], "compass": ["L", 1], "map": ["L", 2], "smalltv": ["L", 3], "cpu": ["L", 4],
		"live": ["L", 10], "kopf": ["L", 20], "blinki": ["L", 90, true],
		"dev": ["R", -10], "kameras": ["R", 0], "geraet": ["R", 10], "mover": ["R", 90, true]}
const GROUP := ["map", "compass", "smalltv", "cpu"]         # zusammen in einem Fenster mit Reitern
const TAB_NAME := {"map": "Karte", "compass": "Kompass", "smalltv": "SmallTV", "cpu": "CPU"}
const AUTO_BASE := {"map": 220.0, "live": 260.0, "kopf": 320.0, "kameras": 330.0}   # Breite bei Massstab 1 (sonst die erste Breite)
const DOCK_ZONE := 48.0                # so nah am Rand losgelassen = andocken
const TOP := 8.0                       # oberster Platz in einer Leiste
const S_MIN := 0.55                    # kleinster Massstab der Bilder

var dock_on := true                    # Fenster automatisch andocken (aus = wie vor dem Paket)
var tabs_on := true                    # Karte, Kompass, SmallTV und CPU als Reiter
var tab_active := "map"
var tab_host: Win = null
var _tab_btns := {}                    # id -> Button in der Reiterleiste
var _tab_ph: Label = null              # «SmallTV: sobald MoveEye ein Bild schickt» im leeren Reiter
var _auto_s := -1.0                    # Massstab der Bilder in den Leisten
var _fit_t := 0.0
var _grow_block := 0.0
var _pack_pos := {}                    # id -> Platz aus pack()
var _pack_ok := true


func _ready() -> void:
	process_priority = 100                               # Paket «Andocken»: nach den Fenstern - Grösse und Platz im selben Bild
	_saved = {}
	if FileAccess.file_exists(FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if typeof(d) == TYPE_DICTIONARY and typeof(d.get("win")) == TYPE_DICTIONARY:
			_saved = d["win"]
		if typeof(d) == TYPE_DICTIONARY:
			dock_on = bool(d.get("dock", true))
			tabs_on = bool(d.get("tabs", true))
			tab_active = str(d.get("tab", "map")) if str(d.get("tab", "map")) in GROUP else "map"


# ---- anmelden --------------------------------------------------------------------------------------------------------------
func add(id: String, title, content: Control, opts := {}) -> Control:
	"""put «content» into a window frame (see the head of the file). title: German text (T.t) or Callable() -> String"""
	if content == null or not is_instance_valid(content):
		return null
	if wins.has(id):
		return wins[id]
	var w := Win.new()
	w.mgr = self
	w.id = id
	w.title_src = title
	w.content = content
	w.opts = opts
	var parent: Node = content.get_parent()
	var idx := -1
	if parent == null:
		parent = main.ui_layer
	else:
		idx = content.get_index()
		parent.remove_child(content)
	content.set_meta("fenster", id)
	w.def_cms = content.custom_minimum_size
	if content is PanelContainer:                       # the frame is the card now (no card in the card)
		content.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	content.set_anchors_preset(Control.PRESET_TOP_LEFT)
	content.position = Vector2.ZERO
	for h in opts.get("hide", []):
		if h is Control:
			(h as Control).visible = false
	w.build()
	parent.add_child(w)
	if idx >= 0:
		parent.move_child(w, idx)
	var s: Dictionary = _saved.get(id, {}) if typeof(_saved.get(id, {})) == TYPE_DICTIONARY else {}
	w.user_hidden = bool(s.get("hid", false)) and not opts.has("set_on")
	_dock_default(w)
	if s.has("d"):                                       # Paket «Andocken»: eigene Leiste / frei («F»)
		w.dock = "" if str(s["d"]) == "F" else str(s["d"])
		w.dock_i = float(s.get("di", w.dock_i))
		w.dock_end = bool(s.get("de", w.dock_end))
	w.folded = bool(s.get("fo", false)) and opts.get("fold", false)
	wins[id] = w
	order.append(id)
	return w


func win(id_or_content) -> Win:
	if id_or_content is String:
		return wins.get(id_or_content)
	for k in wins:
		if (wins[k] as Win).content == id_or_content:
			return wins[k]
	return null


func home_at(id_or_content, p: Vector2) -> void:
	"""the standard place of a window (used while it was never moved by hand)"""
	var w := win(id_or_content)
	if w != null:
		w.home_pos = p


func is_on(id: String) -> bool:
	var w: Win = wins.get(id)
	if w == null:
		return false
	return bool((w.opts["on"] as Callable).call()) if w.opts.has("on") else not w.user_hidden


func set_on(id: String, v: bool, from_close := false) -> void:
	var w: Win = wins.get(id)
	if w == null:
		return
	if w.opts.has("set_on"):
		(w.opts["set_on"] as Callable).call(v)
	else:
		w.user_hidden = not v
	changed()
	if from_close and main.mehr != null and main.mehr.has_method("toast"):
		main.mehr.toast(T.t("«%s» ausgeblendet – wieder zeigen: «Fenster» in der Leiste unten", [w.title()]))


func over(p: Vector2) -> bool:
	"""is p over one of the windows? (main._over_hud: the 3D view does not move there)"""
	for k in wins:
		var w: Win = wins[k]
		if w.visible and w.is_visible_in_tree() and w.card.get_global_rect().has_point(p):
			return true
	return _list != null and _list.visible and _list.get_global_rect().has_point(p)


func reset() -> void:
	"""«Anordnung zurücksetzen»: every window back to its place and size; the ones hidden with ✕ come back"""
	for k in wins:
		var w: Win = wins[k]
		w.placed = false
		w.user_hidden = false
		_reset_size(w)
		_dock_default(w)
		w.folded = false
	_saved = {}
	_auto_s = -1.0
	changed()


func _reset_size(w: Win) -> void:
	if w.sized and w.opts.has("reset_size"):
		(w.opts["reset_size"] as Callable).call(w)
	elif w.sized and not w.opts.has("set_size"):
		w.content.custom_minimum_size = w.def_cms
		w.card.reset_size()
	elif w.sized and w.def_w > 0.0:
		w.apply_size(w.def_w, w.def_h)
	w.sized = false


func arrange() -> void:
	"""«Neu anordnen» (Paket «Andocken»): alle Fenster zurück in ihre Leiste, Grösse wieder automatisch; ausgeblendete
	bleiben aus, eingeklappte bleiben eingeklappt"""
	dock_on = true
	for k in wins:
		var w: Win = wins[k]
		w.placed = false
		w.rel = Vector2(-1, -1)
		if bool(w.opts.get("auto", true)):
			_reset_size(w)
		_dock_default(w)
	_auto_s = -1.0
	_fit_t = 0.0
	changed()


func set_fold(w: Win, on: bool) -> void:
	"""einklappen zur schmalen Leiste (nur die Titelleiste bleibt) - opts.fold"""
	if w == null or not w.opts.get("fold", false):
		return
	w.folded = on
	w._title()
	changed()


func size_name(w: Win) -> String:
	var i := size_index(w)
	return [T.t("klein"), T.t("mittel"), T.t("gross")][i] if i >= 0 else "◱"


func size_index(w: Win) -> int:
	"""welche der drei Grössen (opts.sizes) gerade gilt; -1 = eigene (von Hand gezogen)"""
	var ss: Array = w.opts.get("sizes", [])
	var cur: Vector2 = Vector2(w.want_w, w.want_h) if w.sized else (ss[ss.size() - 1] if ss.size() > 0 else Vector2.ZERO)
	for i in range(ss.size()):
		if (ss[i] as Vector2).distance_to(cur) < 2.0:
			return i
	return -1


func next_size(w: Win) -> void:
	"""Knopf klein → mittel → gross → klein (die Grösse wird gemerkt)"""
	var ss: Array = w.opts.get("sizes", [])
	if ss.size() < 3:
		return
	var i := size_index(w)
	var v: Vector2 = ss[(i + 1) % 3] if i >= 0 else ss[0]
	w.apply_size(v.x, v.y)
	w.sized = true
	w._title()
	changed()


func _dock_default(w: Win) -> void:
	var dd: Array = DOCK_DEF.get(w.id, ["", 0.0])
	w.dock = str(dd[0])
	w.dock_i = float(dd[1])
	w.dock_end = dd.size() > 2 and bool(dd[2])


func changed() -> void:
	_save_t = 0.6


func _process(dt: float) -> void:
	var vs := view_size()
	if vs != _vs:                                        # the window got another size: placed windows keep their share
		_vs = vs
		for k in wins:
			var w: Win = wins[k]
			if w.placed and w.rel.x >= 0.0:
				w.position = clamp_pos(w, w.rel * (vs - w.size))
		_fit_t = 0.0
	_dock_tick(dt)
	if _save_t >= 0.0:
		_save_t -= dt
		if _save_t < 0.0:
			save()
	if _list != null and _list.visible:
		_list_t -= dt
		if _list_t <= 0.0:
			_list_t = 0.4
			_paint_list()
		if main.toolbar != null and not main.toolbar.visible:
			_list.visible = false


func _exit_tree() -> void:
	if _save_t >= 0.0:
		save()


func save() -> void:
	_save_t = -1.0
	var out := {}
	for k in _saved:                                     # windows of other branches / not yet shown keep their entry
		out[k] = _saved[k]
	for k in wins:
		var w: Win = wins[k]
		if not w._init_done:
			continue
		var e := {}
		if w.placed and w.rel.x >= 0.0:
			e["x"] = snappedf(w.rel.x, 0.0001)
			e["y"] = snappedf(w.rel.y, 0.0001)
		if w.sized:
			e["w"] = roundf(w.want_w)
			e["h"] = roundf(w.want_h)
		if w.user_hidden:
			e["hid"] = true
		var dd: Array = DOCK_DEF.get(k, ["", 0.0])            # Paket «Andocken»: nur was vom Standard abweicht
		if w.dock != str(dd[0]) or not is_equal_approx(w.dock_i, float(dd[1])) or w.dock_end != (dd.size() > 2 and bool(dd[2])):
			e["d"] = "F" if w.dock == "" else w.dock
			e["di"] = snappedf(w.dock_i, 0.01)
			e["de"] = w.dock_end
		if w.folded:
			e["fo"] = true
		if e.is_empty():
			out.erase(k)
		else:
			out[k] = e
	_saved = out
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"v": 1, "win": out, "dock": dock_on, "tabs": tabs_on, "tab": tab_active}, " "))


# ---- Platz, Schnappen ---------------------------------------------------------------------------------------------------
func view_size() -> Vector2:
	return main.get_viewport().get_visible_rect().size


func free_lr() -> Vector2:
	"""left and right end of the free view (between the phone simulator and the control panel)"""
	var vw: float = view_size().x
	var right: float = main.ui_root.get_global_rect().position.x if main.ui_root != null and main.ui_root.visible else vw
	var left: float = main.phone.get_global_rect().end.x + 10.0 if main.phone != null and main.phone.visible else 0.0
	return Vector2(left, right)


func phone_open() -> bool:
	return main.phone != null and main.phone.visible


func home_of(w: Win) -> Vector2:
	var h = w.opts.get("home")
	if h is Callable:
		return (h as Callable).call(w)
	if h is Vector2:
		return h
	if w.home_pos.x > -9000.0:
		return w.home_pos
	return Vector2(stack_x(w), stack_y(w))


func stack_x(w: Win) -> float:
	"""the column at the top left (with the phone simulator open: at the right of the free view, like before)"""
	if phone_open():
		return free_lr().y - w.size.x - EDGE
	return EDGE


func stack_y(w: Win) -> float:
	var y := 8.0
	var x := stack_x(w)
	for k in wins:                                       # a window at the top in the way (the CPU display)
		var o: Win = wins[k]
		if not (k in STACK) and o.visible and not o.placed and o.position.y < 40.0 and o.position.x < x + w.size.x and o.position.x + o.size.x > x:
			y = maxf(y, o.position.y + o.size.y + GAP)
	for k in STACK:
		if k == w.id:
			break
		var o: Win = wins.get(k)
		if o != null and o.visible and not o.placed:
			y = maxf(y, o.position.y + o.size.y + GAP)
	return y


func clamp_pos(w: Win, p: Vector2) -> Vector2:
	var vs := view_size()
	var sz: Vector2 = w.size
	var x := clampf(p.x, 0.0, maxf(0.0, vs.x - sz.x))
	var y := clampf(p.y, 0.0, maxf(0.0, vs.y - (sz.y if sz.y <= vs.y else 24.0)))
	return Vector2(x, y).floor()


func _rects(w: Win) -> Array:
	"""what a window snaps to: the other windows, the control panel, the phone, the bar at the bottom"""
	var out := []
	for k in wins:
		var o: Win = wins[k]
		if o != w and o.visible:
			out.append(o.get_global_rect())
	for c in [main.ui_root, main.phone, main.toolbar, main.show_btn]:
		if c != null and is_instance_valid(c) and (c as Control).is_visible_in_tree():
			out.append((c as Control).get_global_rect())
	return out


func _best(edges: Array, lines: Array) -> float:
	"""the smallest move (≤ SNAP) that puts one of the edges on one of the lines; 0 = none"""
	var best := SNAP + 1.0
	var mv := 0.0
	for e in edges:
		for l in lines:
			var d: float = float(l) - float(e)
			if absf(d) < best:
				best = absf(d)
				mv = d
	return mv if best <= SNAP else 0.0


func _lines(w: Win, r: Rect2) -> Array:
	"""[x lines for the left edge, x lines for the right edge, y lines for the top, y lines for the bottom]"""
	var vs := view_size()
	var xl := [EDGE, 0.0]
	var xr := [vs.x - EDGE, vs.x]
	var yt := [EDGE, 0.0]
	var yb := [vs.y - EDGE, vs.y]
	for o in _rects(w):
		var q: Rect2 = o
		if q.position.y < r.end.y + SNAP and q.end.y > r.position.y - SNAP:   # side by side
			xl.append_array([q.end.x + GAP, q.position.x])
			xr.append_array([q.position.x - GAP, q.end.x])
		if q.position.x < r.end.x + SNAP and q.end.x > r.position.x - SNAP:   # one above the other
			yt.append_array([q.end.y + GAP, q.position.y])
			yb.append_array([q.position.y - GAP, q.end.y])
	return [xl, xr, yt, yb]


func snap_pos(w: Win, p: Vector2) -> Vector2:
	var r := Rect2(p, w.size)
	var ln := _lines(w, r)
	var dx := _best([r.position.x], ln[0])
	var dx2 := _best([r.end.x], ln[1])
	if dx == 0.0 or (dx2 != 0.0 and absf(dx2) < absf(dx)):
		dx = dx2
	if dx != 0.0:                                        # side by side now: the top / bottom of the neighbour counts too
		r.position.x += dx
		ln = _lines(w, r)
	var dy := _best([r.position.y], ln[2])
	var dy2 := _best([r.end.y], ln[3])
	if dy == 0.0 or (dy2 != 0.0 and absf(dy2) < absf(dy)):
		dy = dy2
	return p + Vector2(dx, dy)


func resize_drag(w: Win, d: Vector2) -> void:
	var mode: String = w.opts.get("resize", "none")
	var s0: Vector2 = w._res_size
	var mn: Vector2 = w.opts.get("min", Vector2(80, 60))
	var mx: Vector2 = w.opts.get("max", Vector2(900, 700))
	var over_v: Vector2 = w._res_frame - s0                 # frame around the content (strip, margins)
	var vs := view_size()
	var r := Rect2(w.position, w._res_frame)
	var ln := _lines(w, r)
	var nw := s0.x + d.x
	var nh := s0.y + d.y
	if mode == "w":
		var k := s0.y / maxf(1.0, s0.x)                     # a picture: height per width
		if k > 0.01 and absf(d.y) > absf(d.x):
			nw = s0.x + d.y / k                              # pulled down: the width follows
		nh = 0.0
	var right := w.position.x + nw + over_v.x
	nw += _best([right], ln[1])
	nw = clampf(nw, mn.x, maxf(mn.x, minf(mx.x, vs.x - w.position.x - over_v.x)))
	if mode == "wh":
		var bottom := w.position.y + nh + over_v.y
		nh += _best([bottom], ln[3])
		nh = clampf(nh, mn.y, maxf(mn.y, minf(mx.y, vs.y - w.position.y - over_v.y)))
	w.apply_size(roundf(nw), roundf(nh))


func raise(w: Win) -> void:
	"""to the front of the other windows, but below the control panel"""
	var p := w.get_parent()
	if p == null:
		return
	var ui: Control = main.ui_root
	if ui != null and ui.get_parent() == p:
		var ti := ui.get_index()
		p.move_child(w, ti - 1 if w.get_index() < ti else ti)
	else:
		p.move_child(w, -1)


func _shown(w: Win) -> void:
	"""a window appears: the first time its saved size and place, later its own size again (Kameras)"""
	if not w._init_done:
		w._init_done = true
		var cm: Vector2 = w.content.get_combined_minimum_size()
		w.def_w = cm.x
		w.def_h = cm.y if w.opts.get("resize", "none") == "wh" else 0.0
		var s: Dictionary = _saved.get(w.id, {}) if typeof(_saved.get(w.id, {})) == TYPE_DICTIONARY else {}
		if s.has("w") and w.opts.get("resize", "none") != "none":
			var mn: Vector2 = w.opts.get("min", Vector2(80, 60))
			var mx: Vector2 = w.opts.get("max", Vector2(900, 700))
			var vs := view_size()
			w.apply_size(clampf(float(s["w"]), mn.x, maxf(mn.x, minf(mx.x, vs.x - 40.0))),
					clampf(float(s.get("h", 0.0)), 0.0, maxf(mn.y, minf(mx.y, vs.y - 60.0))) if w.opts.get("resize") == "wh" else 0.0)
			w.sized = true
		if s.has("x"):
			w.rel = Vector2(clampf(float(s["x"]), 0.0, 1.0), clampf(float(s.get("y", 0.0)), 0.0, 1.0))
			w.placed = true
			w._rel_frames = 3                                 # the size settles in the first frames
	elif w.sized:
		w.apply_size(w.want_w, w.want_h)


func _hidden(w: Win) -> void:
	if w.opts.has("on_hide"):
		(w.opts["on_hide"] as Callable).call()


# ---- Paket «Andocken»: Leisten links / rechts / unten ------------------------------------------------------------------------
func grouped(w: Win) -> bool:
	"""steckt das Fenster gerade als Reiter im Seitenfenster?"""
	return tabs_on and w.group != null


func docked(w: Win) -> bool:
	return dock_on and w.dock != "" and not grouped(w)


func area() -> Dictionary:
	"""der Platz für die Leisten: zwischen Handy-Simulator und Bedienfeld; was frei bleiben muss (Werkzeugleiste,
	Knopf «Bedienfeld zeigen», Ansichtsleiste) als Hindernis"""
	var lr := free_lr()
	var obs := []
	for c in [main.toolbar, main.show_btn, main.view_bar]:
		if c != null and is_instance_valid(c) and (c as Control).is_visible_in_tree() and (c as Control).modulate.a > 0.01:
			obs.append((c as Control).get_global_rect())
	var vs := view_size()
	return {"l": lr.x, "r": lr.y, "vs": vs, "obs": obs, "maxcols": 1 if vs.x < 1700.0 else 2}


func _dock_items(for_fit: bool, k := 1.0) -> Array:
	"""die angedockten, sichtbaren Fenster für pack(); k: Bilder um diesen Faktor grösser schätzen (passt es noch?)"""
	var out := []
	for id in order:
		var w: Win = wins[id]
		if not docked(w) or not w.visible or w._drag:
			continue
		if for_fit and w.opts.get("fit", true) == false:
			continue
		var sz: Vector2 = w.size
		if k != 1.0:
			var a: Win = w
			if w == tab_host and wins.has(tab_active):
				a = wins[tab_active]
			if is_auto(a) and a.visible:
				sz += a.content.size * (k - 1.0)
		out.append({"id": id, "side": w.dock, "i": w.dock_i, "end": w.dock_end, "size": sz})
	return out


static func _vlim(ar: Dictionary, x0: float, x1: float) -> Vector2:
	"""oberster und unterster Platz einer Spalte von x0 bis x1 (Hindernisse oben schieben nach unten und umgekehrt)"""
	var vs: Vector2 = ar["vs"]
	var top := TOP
	var bot := vs.y - EDGE
	for o in ar["obs"]:
		var r: Rect2 = o
		if r.end.x <= x0 or r.position.x >= x1:
			continue
		if r.get_center().y < vs.y * 0.5:
			top = maxf(top, r.end.y + GAP)
		else:
			bot = minf(bot, r.position.y - GAP)
	return Vector2(top, bot)


static func _pack_side(items: Array, ar: Dictionary, right: bool, out: Dictionary) -> Dictionary:
	var x: float = (float(ar["r"]) - EDGE) if right else (float(ar["l"]) + EDGE)   # Aussenkante der Spalte
	var ends := []
	var norm := []
	for it in items:
		(ends if it["end"] else norm).append(it)
	var ok := true
	var cols := 1
	var col_w := 0.0
	var end_top := INF
	var yb := INF
	for j in range(ends.size() - 1, -1, -1):              # unten in der ersten Spalte, das letzte zuunterst
		var sz: Vector2 = ends[j]["size"]
		var x0 := x - sz.x if right else x
		var lim := _vlim(ar, x0, x0 + sz.x)
		yb = minf(yb, lim.y) - sz.y
		if yb < lim.x:
			ok = false
		out[ends[j]["id"]] = Vector2(x0, yb)
		end_top = yb
		yb -= GAP
		col_w = maxf(col_w, sz.x)
	var y := -1.0
	for it in norm:
		var sz: Vector2 = it["size"]
		var x0 := x - sz.x if right else x
		var lim := _vlim(ar, x0, x0 + sz.x)
		if y < 0.0:
			y = lim.x
		var bot := lim.y
		if cols == 1 and end_top < INF:
			bot = minf(bot, end_top - GAP)
		if y + sz.y > bot and y > lim.x + 0.5:             # die Spalte ist voll: eine neue weiter innen
			x = x - col_w - GAP if right else x + col_w + GAP
			col_w = 0.0
			cols += 1
			x0 = x - sz.x if right else x
			lim = _vlim(ar, x0, x0 + sz.x)
			y = lim.x
			bot = lim.y
		if y + sz.y > bot:
			ok = false
		out[it["id"]] = Vector2(x0, y)
		y += sz.y + GAP
		col_w = maxf(col_w, sz.x)
	var inner := (x - col_w) if right else (x + col_w)
	if items.is_empty():
		inner = x + EDGE if right else x - EDGE
	return {"ok": ok and cols <= int(ar["maxcols"]), "cols": cols if not items.is_empty() else 0, "inner": inner}


static func pack(items: Array, ar: Dictionary) -> Dictionary:
	"""die Plätze in den Leisten - rein rechnerisch (Test ohne Bild: werkzeuge/fenster_dock_test.gd).
	items: [{id, side "L"|"R"|"B", i, end, size}], ar: area(). Ergebnis {pos: {id: Vector2}, ok, cols_l, cols_r}"""
	var by := {"L": [], "R": [], "B": []}
	for it in items:
		if by.has(str(it["side"])):
			by[str(it["side"])].append(it)
	for s in by:
		(by[s] as Array).sort_custom(func(a, b): return float(a["i"]) < float(b["i"]))
	var pos := {}
	var lres := _pack_side(by["L"], ar, false, pos)
	var rres := _pack_side(by["R"], ar, true, pos)
	var ok: bool = lres["ok"] and rres["ok"]
	if not (by["L"] as Array).is_empty() and not (by["R"] as Array).is_empty() and float(lres["inner"]) + GAP > float(rres["inner"]):
		ok = false                                           # die Leisten stossen zusammen
	var b: Array = by["B"]
	if not b.is_empty():                                     # unten: eine Reihe über der Werkzeugleiste, in der Mitte
		var lx: float = float(lres["inner"]) + GAP
		var rx: float = float(rres["inner"]) - GAP
		var tw := -GAP
		for it in b:
			tw += (it["size"] as Vector2).x + GAP
		var x := maxf(lx, (lx + rx - tw) * 0.5)
		if x + tw > rx:
			ok = false
		for it in b:
			var sz: Vector2 = it["size"]
			var lim := _vlim(ar, x, x + sz.x)
			pos[it["id"]] = Vector2(x, lim.y - sz.y)
			if lim.y - sz.y < lim.x:
				ok = false
			x += sz.x + GAP
	return {"pos": pos, "ok": ok, "cols_l": lres["cols"], "cols_r": rres["cols"]}


func is_auto(w: Win) -> bool:
	"""wächst und schrumpft das Fenster mit der Ansicht? (Bilder in einer Leiste, Grösse nie von Hand geändert)"""
	return dock_on and (w.dock != "" or grouped(w)) and w.opts.get("resize", "none") != "none" and not w.sized \
			and w._init_done and bool(w.opts.get("auto", true)) and (AUTO_BASE.has(w.id) or w.def_w > 0.0)


func _target_s() -> float:
	var vs := view_size()
	return clampf(minf(vs.y / 900.0, vs.x / 1500.0), 0.7, 1.6)


func _apply_auto() -> void:
	for k in wins:
		var w: Win = wins[k]
		if not is_auto(w) or not w.visible:
			continue
		var mn: Vector2 = w.opts.get("min", Vector2(80, 60))
		var mx: Vector2 = w.opts.get("max", Vector2(900, 700))
		var want := roundf(clampf(float(AUTO_BASE.get(k, w.def_w)) * _auto_s, mn.x, mx.x))
		if absf(want - w.want_w) > 1.0:
			w.apply_size(want, w.def_h * _auto_s if w.opts.get("resize") == "wh" else 0.0)


func _dock_tick(dt: float) -> void:
	_tab_tick()
	_keep_top()
	if not dock_on:
		_pack_pos = {}
		return
	var ar := area()
	place_now(ar)
	_grow_block -= dt
	_fit_t -= dt
	if _fit_t > 0.0:
		return
	_fit_t = 0.3
	var tgt := _target_s()
	if _auto_s < 0.0:
		_auto_s = tgt
		_apply_auto()
		return
	var fit := pack(_dock_items(true), ar)
	_pack_ok = fit["ok"]
	if not _pack_ok and _auto_s > S_MIN + 0.001:              # passt nicht: Bilder kleiner
		_auto_s = maxf(S_MIN, _auto_s - 0.1)
		_grow_block = 2.0
		_apply_auto()
	elif _auto_s > tgt + 0.001:
		_auto_s = tgt
		_apply_auto()
	elif _auto_s < tgt - 0.001 and _grow_block <= 0.0:       # Platz frei: grösser, wenn es geschätzt noch passt
		var s2 := minf(tgt, _auto_s + 0.1)
		if pack(_dock_items(true, s2 / _auto_s * 1.05), ar)["ok"]:
			_auto_s = s2
			_apply_auto()
		else:
			_grow_block = 3.0
	else:
		_apply_auto()                                        # neu gezeigte Fenster


func place_now(ar := {}) -> void:
	"""die Plätze rechnen und gleich setzen (die Fenster haben ihre Grösse in diesem Bild schon)"""
	if not dock_on:
		return
	for k in wins:                                           # Grösse wie in Win._process (Tests fragen vor den Fenstern)
		var w: Win = wins[k]
		if w.visible and w.size != w.card.get_combined_minimum_size():
			w.card.size = w.card.get_combined_minimum_size()
			w.size = w.card.size
	_pack_pos = pack(_dock_items(false), ar if not ar.is_empty() else area())["pos"]
	for id in _pack_pos:
		var w: Win = wins[id]
		w.position = clamp_pos(w, _pack_pos[id])
	if tab_host != null and tab_host.visible and wins.has(tab_active) and grouped(wins[tab_active]):
		(wins[tab_active] as Win).position = tab_host.content.global_position.floor()


func dock_pos(w: Win) -> Vector2:
	return _pack_pos.get(w.id, Vector2(-1, -1))


func drop(w: Win) -> void:
	"""Fenster losgelassen: am Rand = in diese Leiste (Reihenfolge nach der Höhe), sonst frei schwebend"""
	var r := w.get_global_rect()
	var lr := free_lr()
	var vs := view_size()
	var lim := _vlim(area(), r.position.x, r.end.x)
	var side := ""
	if r.position.x <= lr.x + EDGE + DOCK_ZONE:
		side = "L"
	elif r.end.x >= lr.y - EDGE - DOCK_ZONE:
		side = "R"
	elif r.end.y >= lim.y - DOCK_ZONE:
		side = "B"
	if side == "":
		w.dock = ""
		w.placed = true
		var room: Vector2 = vs - w.size
		w.rel = Vector2(clampf(w.position.x / maxf(1.0, room.x), 0.0, 1.0), clampf(w.position.y / maxf(1.0, room.y), 0.0, 1.0))
		changed()
		return
	w.dock = side
	w.placed = false
	w.dock_end = side != "B" and r.get_center().y > vs.y * 0.62
	var keyed := []                                          # neu nummerieren: sichtbare nach ihrem Platz
	for k in order:
		var o: Win = wins[k]
		if o.dock != side or grouped(o):
			continue
		var c: Vector2 = r.get_center() if o == w else (o.get_global_rect().get_center() if o.visible else Vector2(o.dock_i * 1000.0, o.dock_i * 1000.0))
		keyed.append([c.x if side == "B" else c.y, o])
	keyed.sort_custom(func(a, b): return float(a[0]) < float(b[0]))
	for j in range(keyed.size()):
		(keyed[j][1] as Win).dock_i = float(j * 10)
	changed()


func _keep_top() -> void:
	"""Fenster mit «top» (Entwickler) immer zuoberst - über den anderen Fenstern und dem Bedienfeld"""
	for k in wins:
		var w: Win = wins[k]
		if not w.opts.get("top", false) or not w.visible:
			continue
		var p := w.get_parent()
		if p == null:
			continue
		var last := p.get_child_count() - 1
		if _list != null and _list.get_parent() == p and _list.visible:
			last -= 1
		if w.get_index() < last:
			p.move_child(w, last)


func check_layout() -> Dictionary:
	"""für Tests: überlappen sich sichtbare Fenster, ragt eines aus dem Bild, deckt eines die Werkzeugleiste?"""
	place_now()
	var vs := view_size()
	var bad := []
	var rs := []
	for k in order:
		var w: Win = wins[k]
		if w.visible:
			rs.append([k, w.get_global_rect()])
	for i in range(rs.size()):
		var a: Rect2 = rs[i][1]
		if a.position.x < -0.5 or a.position.y < -0.5 or a.end.x > vs.x + 0.5 or a.end.y > vs.y + 0.5:
			bad.append("out:" + str(rs[i][0]))
		for c in [main.toolbar, main.show_btn]:
			if c != null and (c as Control).is_visible_in_tree() and a.grow(-1).intersects((c as Control).get_global_rect()):
				bad.append("over:" + str(rs[i][0]) + ">" + str((c as Control).name))
		for j in range(i + 1, rs.size()):
			if a.grow(-1).intersects((rs[j][1] as Rect2).grow(-1)):
				var ia: String = rs[i][0]
				var ib: String = rs[j][0]
				if (ia == "tabs" and (wins[ib] as Win).group == tab_host) or (ib == "tabs" and (wins[ia] as Win).group == tab_host):
					continue                                   # der gezeigte Reiter liegt im Seitenfenster
				bad.append("%s / %s" % [rs[i][0], rs[j][0]])
	return {"ok": bad.is_empty(), "bad": bad, "scale": snappedf(_auto_s, 0.01), "fit": _pack_ok, "view": [vs.x, vs.y]}


# ---- das Seitenfenster mit Reitern -----------------------------------------------------------------------------------------
func _build_tabs() -> void:
	var body := Control.new()                               # Platz für den gezeigten Reiter (sein Fenster liegt darüber)
	body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tab_ph = Label.new()
	_tab_ph.add_theme_font_size_override("font_size", 12)
	_tab_ph.add_theme_color_override("font_color", UI.MUT)
	_tab_ph.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_tab_ph.custom_minimum_size = Vector2(170, 0)
	_tab_ph.position = Vector2(6, 6)
	_tab_ph.visible = false
	body.add_child(_tab_ph)
	var bar := HBoxContainer.new()
	bar.add_theme_constant_override("separation", 1)
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for id in GROUP:
		if not wins.has(id):
			continue
		var b := Button.new()
		b.text = T.t(str(TAB_NAME[id]))
		b.tooltip_text = wins[id].title() + " · " + T.t("Reiter: Klick = zeigen")
		b.flat = true
		b.focus_mode = Control.FOCUS_NONE
		b.add_theme_font_size_override("font_size", 11)
		var e := StyleBoxFlat.new()
		e.bg_color = Color(1, 1, 1, 0.0)
		e.content_margin_left = 5
		e.content_margin_right = 5
		e.set_corner_radius_all(5)
		var a := e.duplicate() as StyleBoxFlat
		a.bg_color = Color(UI.ACC, 0.85)
		b.set_meta("st", [e, a])
		b.pressed.connect(func(): show_tab(id))
		bar.add_child(b)
		_tab_btns[id] = b
	if _tab_btns.is_empty():
		return
	add("tabs", func(): return T.t("Reiter") + " · " + (wins[tab_active].title() if wins.has(tab_active) else ""), body,
			{"tabs": bar, "list": false, "shown": func(): return tabs_on and _any_tab_on(),
			"on": func(): return _any_tab_on(), "set_on": func(v): _all_tabs(bool(v))})
	tab_host = wins["tabs"]
	tab_host.card.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	tab_host.card.mouse_filter = Control.MOUSE_FILTER_IGNORE   # der gezeigte Reiter bekommt die Maus
	for id in _tab_btns:
		(wins[id] as Win).group = tab_host
	_paint_tabs()


func _any_tab_on() -> bool:
	for id in _tab_btns:
		if is_on(id):
			return true
	return false


func _all_tabs(v: bool) -> void:
	for id in _tab_btns:
		set_on(id, v)


func show_tab(id: String) -> void:
	if not _tab_btns.has(id):
		return
	if not is_on(id):
		set_on(id, true)
	tab_active = id
	_paint_tabs()
	changed()


func _paint_tabs() -> void:
	for id in _tab_btns:
		var b: Button = _tab_btns[id]
		var st: Array = b.get_meta("st")
		var act: bool = id == tab_active
		for s in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
			b.add_theme_stylebox_override(s, st[1] if act else st[0])
		var c := Color.WHITE if act else (Color(0.85, 0.88, 0.92) if is_on(id) else Color(1, 1, 1, 0.4))
		b.add_theme_color_override("font_color", c)
		b.add_theme_color_override("font_hover_color", Color.WHITE)


var _tab_t := 0.0


func _tab_tick() -> void:
	if tab_host == null:
		return
	if tabs_on and not is_on(tab_active):                   # der gezeigte Reiter wurde ausgeschaltet (z. B. Taste M)
		for id in _tab_btns:
			if is_on(id):
				tab_active = id
				break
	var a: Win = wins.get(tab_active)
	var body: Control = tab_host.content
	var want := Vector2(120, 40)
	var ph := false
	if a != null and a.wants():
		want = a.card.get_combined_minimum_size()
	else:
		ph = true
		_tab_ph.text = (a.title() + ": " + T.t(str(a.opts.get("hint", "ausgeschaltet")))) if a != null else ""
		want = Vector2(182, _tab_ph.get_combined_minimum_size().y + 12.0)
	if _tab_ph.visible != ph:
		_tab_ph.visible = ph
	if body.custom_minimum_size != want:
		body.custom_minimum_size = want
	_tab_t -= get_process_delta_time()
	if _tab_t <= 0.0:
		_tab_t = 0.25
		_paint_tabs()


# ---- die Liste «Fenster» (Knopf in der Leiste unten) ---------------------------------------------------------------------
func list_open() -> bool:
	return _list != null and _list.visible


func toggle_list(anchor: Control = null) -> void:
	if list_open():
		_list.visible = false
		return
	_list_anchor = anchor
	_build_list()
	_list.visible = true
	_list.reset_size()
	var vs := view_size()
	var p := Vector2(EDGE, vs.y - _list.size.y - 80.0)
	if anchor != null and is_instance_valid(anchor):
		var ar := anchor.get_global_rect()
		p = Vector2(ar.position.x + ar.size.x / 2.0 - _list.size.x / 2.0, ar.position.y - _list.size.y - 12.0)
	_list.position = Vector2(clampf(p.x, 4.0, vs.x - _list.size.x - 4.0), maxf(4.0, p.y)).floor()
	if anchor != null and anchor.has_focus() and not _checks.is_empty():
		(_checks.values()[0] as Control).grab_focus.call_deferred()   # opened with the controller


func _build_list() -> void:
	if _list != null:
		_list.queue_free()
	_checks = {}
	_mode_checks = {}
	_list = PanelContainer.new()
	_list.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.09, 0.95), Color(1, 1, 1, 0.14), 14, 10, 1))
	_list.mouse_filter = Control.MOUSE_FILTER_STOP
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	_list.add_child(v)
	var hd := HBoxContainer.new()
	v.add_child(hd)
	var t := Label.new()
	t.text = T.t("Fenster").to_upper()
	t.add_theme_font_size_override("font_size", 11)
	t.add_theme_color_override("font_color", UI.MUT)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(t)
	var x := _flat_button("✕", T.t("Schliessen"))
	x.pressed.connect(func(): _list.visible = false)
	hd.add_child(x)
	for id in order:
		var w: Win = wins[id]
		if w.opts.get("list", true) == false:
			continue
		var cb := CheckBox.new()
		cb.text = w.title()
		cb.add_theme_font_size_override("font_size", 13)
		cb.add_theme_color_override("font_color", Color(0.85, 0.88, 0.92))
		cb.add_theme_color_override("font_pressed_color", Color.WHITE)
		cb.add_theme_color_override("font_hover_color", Color.WHITE)
		cb.add_theme_color_override("font_hover_pressed_color", Color.WHITE)
		cb.add_theme_color_override("font_focus_color", Color(1.0, 0.83, 0.3))
		cb.add_theme_icon_override("checked", _box_icon(true))
		cb.add_theme_icon_override("unchecked", _box_icon(false))
		cb.button_pressed = is_on(id)
		cb.tooltip_text = T.t("Fenster zeigen / ausblenden")
		cb.toggled.connect(func(on: bool): set_on(id, on))
		cb.set_meta("pad_back", func(): _list.visible = false)   # B of the controller (padmap.gd)
		if w.opts.has("hint"):
			var row := HBoxContainer.new()
			row.add_theme_constant_override("separation", 6)
			row.add_child(cb)
			var hl := Label.new()
			hl.text = T.t(str(w.opts["hint"]))
			hl.add_theme_font_size_override("font_size", 11)
			hl.add_theme_color_override("font_color", UI.MUT)
			hl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			row.add_child(hl)
			v.add_child(row)
		else:
			v.add_child(cb)
		_checks[id] = cb
	var sep := HSeparator.new()
	sep.add_theme_constant_override("separation", 8)
	v.add_child(sep)
	for it in [["dock", T.t("Fenster automatisch andocken"), T.t("Leisten links und rechts, ohne Überlappung; die Grösse passt sich dem Bildschirm an")],
			["tabs", T.t("Karte, Kompass, SmallTV und CPU als Reiter"), T.t("Ein Seitenfenster mit Reitern statt vier kleiner Fenster")]]:
		var key: String = it[0]
		var sw := CheckBox.new()
		sw.text = str(it[1])
		sw.tooltip_text = str(it[2])
		sw.add_theme_font_size_override("font_size", 13)
		sw.add_theme_color_override("font_color", Color(0.85, 0.88, 0.92))
		sw.add_theme_color_override("font_pressed_color", Color.WHITE)
		sw.add_theme_color_override("font_hover_color", Color.WHITE)
		sw.add_theme_color_override("font_hover_pressed_color", Color.WHITE)
		sw.add_theme_icon_override("checked", _box_icon(true))
		sw.add_theme_icon_override("unchecked", _box_icon(false))
		sw.button_pressed = dock_on if key == "dock" else tabs_on
		sw.toggled.connect(func(on: bool): set_mode(key, on))
		sw.set_meta("pad_back", func(): _list.visible = false)
		v.add_child(sw)
		_mode_checks[key] = sw
	var ab := Button.new()
	ab.text = T.t("Neu anordnen")
	ab.tooltip_text = T.t("Alle Fenster zurück in die Leisten links und rechts, Grösse passend zum Bildschirm")
	ab.add_theme_font_size_override("font_size", 13)
	ab.pressed.connect(func(): arrange(); _paint_list())
	ab.set_meta("pad_back", func(): _list.visible = false)
	v.add_child(ab)
	var rb := Button.new()
	rb.text = T.t("Anordnung zurücksetzen")
	rb.tooltip_text = T.t("Alle Fenster an ihren Standardplatz und in die Standardgrösse; mit ✕ ausgeblendete kommen zurück")
	rb.add_theme_font_size_override("font_size", 13)
	rb.pressed.connect(func(): reset(); _paint_list())
	rb.set_meta("pad_back", func(): _list.visible = false)
	v.add_child(rb)
	var h2 := Label.new()
	h2.text = T.t("Titelleiste ziehen = verschieben · Ecke unten rechts = Grösse · Doppelklick auf die Leiste = zurück an den Platz") \
			+ "\n" + T.t("Am Rand loslassen = andocken, anderswo = frei schwebend")
	h2.add_theme_font_size_override("font_size", 10)
	h2.add_theme_color_override("font_color", UI.MUT)
	h2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	h2.custom_minimum_size = Vector2(260, 0)
	v.add_child(h2)
	_list.visible = false
	main.ui_layer.add_child(_list)                       # above the windows and the panel


var _icons := {}


func _box_icon(on: bool) -> Texture2D:
	"""a check box that is seen on the dark card (blue and ticked like the active switches, or a grey frame)"""
	if _icons.has(on):
		return _icons[on]
	var n := 16
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for y in range(n):
		for x in range(n):
			var edge := x <= 1 or y <= 1 or x >= n - 2 or y >= n - 2
			var corner := (x <= 1 or x >= n - 2) and (y <= 1 or y >= n - 2)
			if corner:
				continue
			if on:
				img.set_pixel(x, y, UI.ACC)
			elif edge:
				img.set_pixel(x, y, Color(0.6, 0.66, 0.74))
	if on:                                               # the tick
		for p in [[4, 8], [5, 9], [6, 10], [7, 9], [8, 8], [9, 7], [10, 6], [11, 5]]:
			for dy in [0, 1]:
				img.set_pixel(p[0], p[1] + dy - 1, Color.WHITE)
	var t := ImageTexture.create_from_image(img)
	_icons[on] = t
	return t


var _mode_checks := {}


func set_mode(key: String, on: bool) -> void:
	"""Schalter der Liste: «dock» (automatisch andocken) / «tabs» (als Reiter)"""
	if key == "dock":
		dock_on = on
		_auto_s = -1.0
	elif key == "tabs":
		tabs_on = on
	_fit_t = 0.0
	changed()


func _paint_list() -> void:
	for key in _mode_checks:
		var sw: CheckBox = _mode_checks[key]
		if is_instance_valid(sw) and sw.button_pressed != (dock_on if key == "dock" else tabs_on):
			sw.set_pressed_no_signal(dock_on if key == "dock" else tabs_on)
	for id in _checks:
		var cb: CheckBox = _checks[id]
		var on := is_on(id)
		if cb.button_pressed != on:
			cb.set_pressed_no_signal(on)


var mouse := Vector2(-1, -1)           # last mouse position (also of events sent by MoveEye / the tests)


func _input(ev: InputEvent) -> void:
	if ev is InputEventMouse:
		mouse = (ev as InputEventMouse).global_position
	if not list_open():
		return
	if ev is InputEventMouseButton and ev.pressed:
		var p: Vector2 = ev.position
		if _list.get_global_rect().has_point(p):
			return
		if _list_anchor != null and is_instance_valid(_list_anchor) and _list_anchor.get_global_rect().has_point(p):
			return                                       # the button itself closes it (toggle)
		_list.visible = false                            # a click elsewhere closes the list (the click still counts)
	elif ev is InputEventKey and ev.pressed and ev.keycode == KEY_ESCAPE:
		_list.visible = false


func _flat_button(tx: String, tip: String) -> Button:
	var b := Button.new()
	b.text = tx
	b.tooltip_text = tip
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", 11)
	b.add_theme_color_override("font_color", Color(1, 1, 1, 0.6))
	b.add_theme_color_override("font_hover_color", Color(1.0, 0.55, 0.5))
	b.add_theme_color_override("font_pressed_color", Color(1.0, 0.45, 0.4))
	var e := StyleBoxEmpty.new()
	e.content_margin_left = 3
	e.content_margin_right = 3
	for st in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
		b.add_theme_stylebox_override(st, e)
	b.custom_minimum_size = Vector2(16, 14)
	return b


# ---- die Fenster des Simulators ------------------------------------------------------------------------------------------
func setup_sim() -> void:
	"""all floating boxes of the simulator in one frame each (called once after main._build_ui)"""
	var m = main
	if m.compass != null:                                # the needle and the «N» around it need room
		m.compass.custom_minimum_size = Vector2(84, 84)
		add("compass", "Kompass", m.compass, {"compact": true})
	if m.minimap != null:
		add("map", "Karte", m.minimap, {"resize": "w", "min": Vector2(130, 0), "max": Vector2(520, 0),
				"on": func(): return m.map_on, "set_on": func(v): m.set_map(bool(v)), "set_size": _map_size,
				"reset_size": func(_w): _map_size(220.0, 0.0)})
	if m.liveview != null:
		var lv = m.liveview
		add("live", func(): return T.t(lv.title.text), lv, {"resize": "w", "min": Vector2(160, 0), "max": Vector2(640, 0), "hide": [lv.title],
				"on": func(): return m.live_on, "set_on": func(v): m.set_live(bool(v)), "set_size": _live_size,
				"reset_size": func(_w): _live_size(260.0, 0.0)})
	if m.smalltv != null and m.smalltv.tile != null:
		var tv = m.smalltv
		add("smalltv", "SmallTV (virtuell)", tv.tile, {"resize": "w", "min": Vector2(130, 0), "max": Vector2(460, 0), "hide": [tv._title],
				"hint": "sobald MoveEye ein Bild schickt", "set_size": _tv_size, "reset_size": func(_w): tv.big = false; tv._size(),
				"on": func(): return tv.show, "set_on": func(v): tv.show = bool(v); tv.save()})
	if m.statusled != null and m.statusled.tile != null:
		var sl = m.statusled
		add("geraet", "Gerät (LED und Tasten)", sl.tile, {"resize": "w", "min": Vector2(240, 0), "max": Vector2(560, 0),
				"hide": [sl._title] if sl.get("_title") != null else [], "home": _home_geraet,
				"on": func(): return sl.show_panel, "set_on": func(v): sl.show_panel = bool(v); sl.save()})
	if m.rover_pad != null:
		add("mover", "Mover fahren", m.rover_pad, {"compact": true, "hint": "nur mit «Mover simulieren»", "home": _home_mover})
	if m.headpad != null:
		var hp = m.headpad
		add("kopf", "Kopf steuern", hp, {"resize": "w", "min": Vector2(260, 0), "max": Vector2(760, 0),
				"hide": [hp.head_row] if hp.get("head_row") != null else [], "hint": "Knopf «Kopf» unten",
				"on": func(): return hp.visible, "set_on": func(v): hp.visible = bool(v), "set_size": _kopf_size, "home": _home_kopf,
				"reset_size": func(_w): hp.img.custom_minimum_size = Vector2(320, 180); hp.info.custom_minimum_size.x = 320})
	if m.cam_float != null and m.cam_card != null:
		var cf: Control = m.cam_float
		var cc: Control = m.cam_card
		_cam_keep = [m.prev0.custom_minimum_size, m.prev1.custom_minimum_size, m.prevt.custom_minimum_size]
		add("kameras", "Kameras · H = Bedienfeld", cf, {"resize": "w", "min": Vector2(240, 0), "max": Vector2(720, 0),
				"hide": [cf.get_child(0)] if cf.get_child_count() > 0 else [], "hint": "wenn das Bedienfeld zu ist (H)",
				"shown": func(): return cf.visible and cc.visible and cc.get_parent() == cf,
				"on": func(): return cc.visible, "set_on": func(v): cc.visible = bool(v),
				"set_size": _cam_size, "on_hide": _cam_restore, "reset_size": _cam_reset})
		home_at(cf, Vector2(EDGE, 300))
	if m.cpu_pill != null:
		add("cpu", "CPU-Anzeige", m.cpu_pill, {"compact": true, "home": _home_cpu})
	_build_tabs()                                         # Paket «Andocken»: Karte, Kompass, SmallTV, CPU als Reiter


func _map_size(w: float, _h: float) -> void:
	main.minimap.size_px = w
	main.minimap._apply_size()
	main.minimap.queue_redraw()
	main.map_size = w
	main._settings_dirty = true


func _live_size(w: float, _h: float) -> void:
	main.live_size = w
	main.liveview.width_px = w
	main.liveview.apply()
	main._settings_dirty = true


func _tv_size(w: float, _h: float) -> void:
	var tv = main.smalltv
	var pad: float = tv.tile.size.x - tv._tex.size.x if tv._tex.size.x > 0.0 else 16.0
	var s: float = maxf(80.0, w - pad)
	tv._tex.custom_minimum_size = Vector2(s, s)


func _kopf_size(w: float, _h: float) -> void:
	main.headpad.img.custom_minimum_size = Vector2(w, roundf(w * 9.0 / 16.0))
	main.headpad.info.custom_minimum_size.x = w


var _cam_keep := []


func _cam_size(w: float, _h: float) -> void:
	"""Kameras (Bedienfeld zu): the card and its three pictures grow together"""
	var cc: Control = main.cam_card
	if cc.get_parent() != main.cam_float:
		return
	var f: float = w / 330.0
	cc.custom_minimum_size.x = w
	main.prev0.custom_minimum_size = (_cam_keep[0] as Vector2) * f
	main.prev1.custom_minimum_size = (_cam_keep[1] as Vector2) * f
	main.prevt.custom_minimum_size = (_cam_keep[2] as Vector2) * f


func _cam_restore() -> void:
	"""back in the panel: the pictures in their usual size"""
	main.prev0.custom_minimum_size = _cam_keep[0]
	main.prev1.custom_minimum_size = _cam_keep[1]
	main.prevt.custom_minimum_size = _cam_keep[2]


func _cam_reset(w: Win) -> void:
	_cam_restore()
	if main.cam_card.get_parent() == main.cam_float:
		main.cam_card.custom_minimum_size.x = w.def_w


func _home_geraet(w: Win) -> Vector2:
	var lr := free_lr()
	return Vector2(lr.x + EDGE if phone_open() else lr.y - w.size.x - EDGE, 64.0)


func _home_mover(w: Win) -> Vector2:
	return Vector2(free_lr().y - w.size.x - 18.0, view_size().y - w.size.y - 70.0)


func _home_kopf(w: Win) -> Vector2:
	return Vector2(free_lr().x + EDGE, view_size().y - w.size.y - 110.0)


func _home_cpu(w: Win) -> Vector2:
	var lr := free_lr()
	return Vector2((lr.x + lr.y - w.size.x) / 2.0, 2.0)


# ---- Tests (/control {"action": "fenster", …}) ------------------------------------------------------------------------------
func control(d: Dictionary) -> Dictionary:
	var dd := str(d.get("do", "info"))
	var id := str(d.get("id", ""))
	var w: Win = wins.get(id)
	match dd:
		"drag":                                          # the title strip with the mouse: {id, dx, dy}
			if w == null or not w.visible:
				return {"ok": false, "error": "window not shown"}
			var a := w.strip.get_global_rect().get_center() + Vector2(-10, 0)
			_mouse_path(a, a + Vector2(float(d.get("dx", 0)), float(d.get("dy", 0))))
		"resize":                                        # the corner: {id, dx, dy}
			if w == null or not w.visible:
				return {"ok": false, "error": "window not shown"}
			var a := w.get_global_rect().end - Vector2(5, 5)
			_mouse_path(a, a + Vector2(float(d.get("dx", 0)), float(d.get("dy", 0))))
		"close":                                         # click on «✕»
			if w == null or not w.visible:
				return {"ok": false, "error": "window not shown"}
			_mouse_path(w.close_b.get_global_rect().get_center(), w.close_b.get_global_rect().get_center())
		"dblclick":
			if w == null or not w.visible:
				return {"ok": false, "error": "window not shown"}
			_mouse_path(w.strip.get_global_rect().get_center(), w.strip.get_global_rect().get_center(), true)
		"list":                                          # the button «Fenster» of the bar
			if main.toolbar != null:
				main.toolbar._press_item("windows")
		"check":                                         # click on the check box of a window in the open list
			if not list_open() or not _checks.has(id):
				return {"ok": false, "error": "list not open"}
			var c := (_checks[id] as Control).get_global_rect()
			_mouse_path(c.position + Vector2(10, c.size.y / 2.0), c.position + Vector2(10, c.size.y / 2.0))
		"reset":
			reset()
		"save":
			save()
		"arrange":                                       # Paket «Andocken»
			arrange()
		"layout":
			return check_layout()
		"tab":
			show_tab(id)
		"fold":
			set_fold(w, bool(d.get("on", true)))
		"size":                                          # Knopf klein / mittel / gross
			if w != null:
				next_size(w)
		"dock", "tabs":
			set_mode(dd, bool(d.get("on", true)))
		"view":                                          # Tests: Fenstergrösse ändern
			get_window().size = Vector2i(int(d.get("w", 1280)), int(d.get("h", 720)))
		"over":
			return {"ok": true, "hud": main._over_hud(Vector2(float(d.get("x", 0)), float(d.get("y", 0))))}
	return info()


func info() -> Dictionary:
	var o := {}
	for k in order:
		var w: Win = wins[k]
		o[k] = {"vis": w.visible, "on": is_on(k), "placed": w.placed, "sized": w.sized, "rect": [w.position.x, w.position.y, w.size.x, w.size.y],
				"content": [w.content.size.x, w.content.size.y], "grip": w.grip.visible, "dock": w.dock, "di": w.dock_i, "fold": w.folded,
				"tab": grouped(w), "auto": is_auto(w)}
	return {"ok": true, "busy": _busy > 0, "wins": o, "list": list_open(), "file": ProjectSettings.globalize_path(FILE), "saved": _saved, "view": [view_size().x, view_size().y],
			"dock": dock_on, "tabs": tabs_on, "tab": tab_active, "scale": _auto_s}


func _mouse_path(a: Vector2, b: Vector2, dbl := false) -> void:
	"""for tests: real mouse events through the GUI (move there, press, move in steps, let go)"""
	_busy += 1
	_ev_move(a, 0)
	await get_tree().process_frame
	await get_tree().process_frame
	_ev_button(a, true, false)
	await get_tree().process_frame
	var n := 8
	for i in range(1, n + 1):
		_ev_move(a.lerp(b, float(i) / n), MOUSE_BUTTON_MASK_LEFT)
		await get_tree().process_frame
	_ev_button(b, false, false)
	if dbl:
		await get_tree().process_frame
		_ev_button(b, true, true)
		await get_tree().process_frame
		_ev_button(b, false, false)
	await get_tree().process_frame
	_ev_move(b + Vector2(0, 1), 0)
	await get_tree().process_frame
	_busy -= 1


var _last_mouse := Vector2.ZERO
var _busy := 0


func _ev_move(p: Vector2, mask: int) -> void:
	var m := InputEventMouseMotion.new()
	m.position = p
	m.global_position = p
	m.relative = p - _last_mouse
	m.button_mask = mask
	_last_mouse = p
	Input.parse_input_event(m)


func _ev_button(p: Vector2, down: bool, dbl: bool) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = down
	e.double_click = dbl
	e.position = p
	e.global_position = p
	e.button_mask = MOUSE_BUTTON_MASK_LEFT if down else 0
	Input.parse_input_event(e)


# ---- der Rahmen ---------------------------------------------------------------------------------------------------------
class Win extends Control:
	var mgr
	var id := ""
	var title_src = ""
	var content: Control
	var opts := {}
	var card: PanelContainer
	var strip: PanelContainer
	var title_l: Label
	var close_b: Button
	var grip: Grip
	var placed := false                # moved by hand (else at its standard place)
	var sized := false                 # resized by hand
	var user_hidden := false           # hidden with ✕ (windows without their own switch)
	var rel := Vector2(-1, -1)         # the place as a share of the free room (0 … 1), what is saved
	var home_pos := Vector2(-9999, -9999)
	var want_w := 0.0
	var want_h := 0.0
	var def_w := -1.0
	var def_h := 0.0
	var def_cms := Vector2.ZERO          # the minimum size of the content before any change (for «zurücksetzen»)
	var dock := ""                       # Paket «Andocken»: "L" | "R" | "B" = in dieser Leiste, "" = frei
	var dock_i := 0.0                    # Reihenfolge in der Leiste
	var dock_end := false                # unten in der Spalte (Mover, Blinki)
	var group: Win = null                # das Seitenfenster mit Reitern, in dem es steckt
	var folded := false                  # eingeklappt zur schmalen Leiste (opts.fold)
	var fold_b: Button = null
	var size_b: Button = null
	var _init_done := false
	var _rel_frames := 0
	var _was := false
	var _t := 0.0
	var _drag := false
	var _drag_off := Vector2.ZERO
	var _drag_from := Vector2.ZERO
	var _res := false
	var _res_from := Vector2.ZERO
	var _res_size := Vector2.ZERO
	var _res_frame := Vector2.ZERO

	func title() -> String:
		if title_src is Callable:
			return str((title_src as Callable).call())
		return T.t(str(title_src))

	func wants() -> bool:
		"""will der Inhalt gezeigt werden (ohne Reiter-Regel)?"""
		var want: bool = bool((opts["shown"] as Callable).call()) if opts.has("shown") else content.visible
		if not opts.has("set_on"):
			want = want and not user_hidden
		return want and content.modulate.a > 0.01     # the rover stick: MoveEye shows the picture full screen

	func build() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE        # only the card catches the mouse, never the room around it
		visible = false
		card = PanelContainer.new()
		card.mouse_filter = Control.MOUSE_FILTER_STOP
		card.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.09, 0.88), UI.LINE, 8, 4, 1))
		add_child(card)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 3)
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(v)
		strip = PanelContainer.new()                    # the title strip (like the grip of the old «Kameras» window)
		var ss := UI.box(Color(UI.BG, 0.92), UI.LINE, 6, 2, 1)
		ss.content_margin_left = 6
		ss.content_margin_right = 2
		ss.content_margin_top = 1
		ss.content_margin_bottom = 1
		strip.add_theme_stylebox_override("panel", ss)
		strip.mouse_filter = Control.MOUSE_FILTER_STOP
		strip.mouse_default_cursor_shape = Control.CURSOR_MOVE
		strip.gui_input.connect(_strip_input)
		v.add_child(strip)
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 4)
		h.mouse_filter = Control.MOUSE_FILTER_IGNORE
		strip.add_child(h)
		var dots := Dots.new()                         # the grip: six dots (drawn - no font needed)
		dots.custom_minimum_size = Vector2(8, 12)
		dots.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		dots.mouse_filter = Control.MOUSE_FILTER_IGNORE
		h.add_child(dots)
		title_l = Label.new()
		title_l.add_theme_font_size_override("font_size", 11)
		title_l.add_theme_color_override("font_color", UI.MUT)
		title_l.clip_text = true
		title_l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		title_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		title_l.custom_minimum_size = Vector2(12, 0)
		title_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		h.add_child(title_l)
		if opts.has("tabs"):                               # Paket «Andocken»: die Reiter stehen in der Titelleiste
			title_l.visible = false
			h.add_child(opts["tabs"])
			var sp := Control.new()
			sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			sp.custom_minimum_size = Vector2(6, 0)
			sp.mouse_filter = Control.MOUSE_FILTER_IGNORE
			h.add_child(sp)
		if opts.has("sizes"):                              # Knopf klein / mittel / gross
			size_b = mgr._flat_button("", T.t("Grösse: klein · mittel · gross (Klick = nächste)"))
			size_b.add_theme_color_override("font_hover_color", Color.WHITE)
			size_b.pressed.connect(func(): mgr.next_size(self))
			h.add_child(size_b)
		if opts.get("fold", false):                        # einklappen zur schmalen Leiste
			fold_b = mgr._flat_button("▾", T.t("Einklappen / aufklappen"))
			fold_b.add_theme_color_override("font_hover_color", Color.WHITE)
			fold_b.pressed.connect(func(): mgr.set_fold(self, not folded))
			h.add_child(fold_b)
		close_b = mgr._flat_button("✕", T.t("Fenster ausblenden (zurück über «Fenster» in der Leiste unten)"))
		close_b.pressed.connect(func(): mgr.set_on(id, false, true))
		h.add_child(close_b)
		v.add_child(content)
		grip = Grip.new()
		grip.size = Vector2(16, 16)
		grip.mouse_filter = Control.MOUSE_FILTER_STOP
		grip.mouse_default_cursor_shape = Control.CURSOR_FDIAGSIZE
		grip.tooltip_text = T.t("Ziehen: Grösse ändern")
		grip.gui_input.connect(_grip_input)
		grip.visible = false
		add_child(grip)
		_title()

	func _title() -> void:
		var tx := title()
		var compact: bool = opts.get("compact", false)
		title_l.text = "" if compact else tx
		if size_b != null:
			size_b.text = mgr.size_name(self)
		if fold_b != null:
			fold_b.text = "▸" if folded else "▾"
			title_l.custom_minimum_size.x = 110.0 if folded else 12.0
		strip.tooltip_text = tx + " · " + T.t("Ziehen zum Verschieben · Doppelklick: zurück an den Platz")

	func apply_size(w: float, h: float) -> void:
		var mode: String = opts.get("resize", "none")
		if mode == "none":
			return
		if opts.has("set_size"):
			(opts["set_size"] as Callable).call(w, h)
		else:
			content.custom_minimum_size = Vector2(w, h if mode == "wh" else content.custom_minimum_size.y)
		want_w = w
		want_h = h
		card.reset_size()

	func _process(dt: float) -> void:
		var grp: bool = mgr.grouped(self)
		var vis: bool = wants()
		if grp:                                           # als Reiter: nur der gezeigte, und nur mit dem Seitenfenster
			vis = vis and group.visible and mgr.tab_active == id
		if strip.visible == grp:
			strip.visible = not grp
		if opts.get("fold", false) and content.visible == folded:
			content.visible = not folded
		if vis != visible:
			visible = vis
		if vis != _was:
			_was = vis
			if vis:
				mgr._shown(self)
			else:
				_drag = false
				_res = false
				mgr._hidden(self)
		if not vis:
			return
		var cs := card.get_combined_minimum_size()
		if card.size != cs:
			card.size = cs
		if size != card.size:
			size = card.size
		_t -= dt
		if _t <= 0.0:
			_t = 0.25
			_title()
		if grp:
			position = group.content.global_position.floor()
		elif not (_drag or _res):
			if mgr.docked(self) and mgr.dock_pos(self).x > -0.5:
				position = mgr.clamp_pos(self, mgr.dock_pos(self))
			elif placed and not mgr.docked(self):
				if _rel_frames > 0:
					_rel_frames -= 1
					position = mgr.clamp_pos(self, rel * (mgr.view_size() - size))
				else:
					position = mgr.clamp_pos(self, position)
			else:
				position = mgr.clamp_pos(self, mgr.home_of(self))
		var g: bool = opts.get("resize", "none") != "none" and (_res or get_global_rect().has_point(mgr.mouse))
		if g != grip.visible:
			grip.visible = g
		if g:
			grip.position = size - grip.size

	func _strip_input(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
			if ev.pressed and ev.double_click:              # back to its place
				_drag = false
				placed = false
				rel = Vector2(-1, -1)
				mgr._dock_default(self)                      # Paket «Andocken»: zurück in die Leiste
				mgr.changed()
			elif ev.pressed:
				_drag = true
				_drag_off = ev.global_position - position
				_drag_from = ev.global_position
				mgr.raise(self)
			elif _drag:
				_end_drag(ev.global_position)
			strip.accept_event()
		elif ev is InputEventMouseMotion and _drag:
			if not (ev.button_mask & MOUSE_BUTTON_MASK_LEFT):   # let go somewhere else
				_end_drag(ev.global_position)
				return
			position = mgr.clamp_pos(self, mgr.snap_pos(self, ev.global_position - _drag_off))
			strip.accept_event()

	func _end_drag(p: Vector2) -> void:
		_drag = false
		if p.distance_to(_drag_from) < 3.0:
			return                                       # only a click: stays where it is (and at its place)
		if mgr.dock_on:                                  # Paket «Andocken»: am Rand = Leiste, sonst frei
			mgr.drop(self)
			return
		placed = true
		var room: Vector2 = mgr.view_size() - size
		rel = Vector2(clampf(position.x / maxf(1.0, room.x), 0.0, 1.0), clampf(position.y / maxf(1.0, room.y), 0.0, 1.0))
		mgr.changed()

	func _grip_input(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
			if ev.pressed:
				_res = true
				_res_from = ev.global_position
				_res_size = content.size
				_res_frame = size
				mgr.raise(self)
			elif _res:
				_res = false
				sized = true
				if placed:                                   # the share of the room changes with the size
					var room: Vector2 = mgr.view_size() - card.get_combined_minimum_size()
					rel = Vector2(clampf(position.x / maxf(1.0, room.x), 0.0, 1.0), clampf(position.y / maxf(1.0, room.y), 0.0, 1.0))
				mgr.changed()
			grip.accept_event()
		elif ev is InputEventMouseMotion and _res:
			if not (ev.button_mask & MOUSE_BUTTON_MASK_LEFT):
				_res = false
				sized = true
				mgr.changed()
				return
			mgr.resize_drag(self, ev.global_position - _res_from)
			grip.accept_event()


class Dots extends Control:
	func _draw() -> void:
		for i in range(3):
			for j in range(2):
				draw_circle(Vector2(2.0 + j * 4.0, 2.0 + i * 4.0), 1.2, Color(1, 1, 1, 0.55))


class Grip extends Control:
	func _draw() -> void:
		var s := size
		for j in range(3):
			var o := 4.0 + j * 4.0
			draw_line(Vector2(s.x - o, s.y - 2), Vector2(s.x - 2, s.y - o), Color(1, 1, 1, 0.75), 1.5, true)
