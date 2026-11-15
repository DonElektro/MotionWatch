extends Node
## Fenster-Wächter (Besitzer 15.11.2026: «Schau, dass sämtliche Fenster, die sich öffnen, sauber bedienen lassen»):
## gilt für jedes Fenster des Simulators, auf dem Handy und am PC - als Netz unter den Fenstern, die schon selbst passen.
##   * ein offenes Fenster (Panel direkt in einer Ebene, oder ein eingebettetes Godot-Fenster), das grösser ist als der
##     freie Platz, wird verkleinert (scale) und ins Bild geschoben - nie mehr links / rechts aus dem Bild
##   * ein grosses Fenster ohne sichtbares «✕» / «Schliessen» bekommt oben rechts ein eigenes ✕ (44 × 44)
##   * ein ✕ / × im Kopf eines Fensters wird mindestens 44 × 44 gross (Finger)
## Der freie Platz: die Ansicht, im Handy-Modus ohne die Leiste (handy.free_rect). Nicht angefasst: das Bedienfeld (das
## macht handy.gd), die schwebenden Fenster (fenster.gd hält sie selbst im Bild), Ebenen über die ganze Ansicht
## (Vollbild wie TV, Spiele) und alles mit set_meta("waechter_aus", true).
## Tests: /control {"action": "waechter"} -> welche Fenster eingepasst / mit ✕ versehen sind.

const UI = preload("res://scripts/ui_style.gd")
const CLOSE_TXT := ["✕", "×", "✖", "Schliessen", "Zu", "Fertig", "OK", "Abbrechen", "Zurück", "Close"]
const BIG_W := 0.4                     # ab diesem Anteil der Breite (und BIG_H der Höhe) ist es ein «Fenster»
const BIG_H := 0.25

var main
var _layers: Array = []
var _layers_t := 0.0
var _scan_t := 0.0
var _track := {}                       # Control -> {"k": scale, "x": Button or null}
var fitted := 0                        # wie oft ein Fenster eingepasst wurde (Tests)
var _scan := false
var big_open := false                  # ein grosses Fenster ist offen (handy.gd blendet dann Rand-Knöpfe und Steuerkreuz aus)
var _win_t := 0.0


func _ready() -> void:
	process_priority = 1000                             # nach den Fenstern (manche setzen Grösse / Ort in jedem Bild)


func free_rect() -> Rect2:
	var h = main.get("handy")
	if h != null and h.on:
		return h.free_rect()
	return Rect2(Vector2.ZERO, main.get_viewport().get_visible_rect().size)


func _find_layers(n: Node, out: Array, depth: int) -> void:
	for c in n.get_children():
		if c is CanvasLayer:
			out.append(c)
		if depth < 3 and not (c is Control):
			_find_layers(c, out, depth + 1)


func _skip(c: Control) -> bool:
	if c == main.ui_root or c.has_meta("waechter_aus"):
		return true
	var h = main.get("handy")
	if h != null and h.layer != null and c.get_parent() == h.layer:
		return true
	if not (c is PanelContainer or c is Panel):
		return true
	var vs: Vector2 = main.get_viewport().get_visible_rect().size
	if c.anchor_left == 0.0 and c.anchor_top == 0.0 and c.anchor_right == 1.0 and c.anchor_bottom == 1.0 \
			and c.size.x <= vs.x + 1.0 and c.size.y <= vs.y + 1.0 and c.position.x >= -1.0 and c.position.y >= -1.0:
		return true                                     # Vollbild-Ebene, die passt (TV, Spiel, Abdunkeln)
	return false


func _process(dt: float) -> void:
	_layers_t -= dt
	if _layers_t <= 0.0:
		_layers_t = 2.0
		_layers.clear()
		_find_layers(main, _layers, 0)
	_scan_t -= dt
	_scan = _scan_t <= 0.0
	if _scan:
		_scan_t = 0.25
		for l in _layers:
			if not is_instance_valid(l) or not (l as CanvasLayer).visible:
				continue
			for c in (l as CanvasLayer).get_children():
				if c is Control and (c as Control).visible and not _track.has(c) and not _skip(c):
					_track[c] = {"k": 1.0, "x": null, "ok": true}
	_win_t -= dt
	if _win_t <= 0.0:
		_win_t = 1.0
		_windows()
	var fr := free_rect()
	big_open = false
	for c in _track.keys():
		if not is_instance_valid(c):
			_track.erase(c)
			continue
		var t: Dictionary = _track[c]
		var cc := c as Control
		if not cc.is_visible_in_tree():
			if t["x"] != null and is_instance_valid(t["x"]):
				(t["x"] as Control).visible = false
			if t["k"] != 1.0:
				cc.scale = Vector2.ONE
				t["k"] = 1.0
			_track.erase(c)
			if t["x"] != null and is_instance_valid(t["x"]):
				(t["x"] as Node).queue_free()
			continue
		_fit(cc, t, fr)


func _fit(c: Control, t: Dictionary, fr: Rect2) -> void:
	var s := c.size
	if s.x < 2.0 or s.y < 2.0:
		return
	var k := minf(1.0, minf(fr.size.x / s.x, fr.size.y / s.y))
	if absf(k - float(t["k"])) > 0.001:
		c.pivot_offset = Vector2.ZERO
		c.scale = Vector2(k, k)
		t["k"] = k
		if k < 1.0:
			fitted += 1
			print("waechter: «%s» %d × %d passt nicht in %d × %d - verkleinert auf %.2f" % [_name(c), s.x, s.y, fr.size.x, fr.size.y, k])
	var r := Rect2(c.global_position, s * k)
	if k < 1.0:
		t["fix"] = true
	if not fr.grow(0.5).encloses(r):                    # aus dem Bild: hinein, 4 Punkte vom Rand, wenn es Platz hat
		t["fix"] = true
		var ins := fr.grow(-4.0) if r.size.x <= fr.size.x - 8.0 and r.size.y <= fr.size.y - 8.0 else fr
		var p := r.position
		p.x = clampf(p.x, ins.position.x, maxf(ins.position.x, ins.end.x - r.size.x))
		p.y = clampf(p.y, ins.position.y, maxf(ins.position.y, ins.end.y - r.size.y))
		c.global_position = p.floor()
		r.position = p
	# ✕: ein grosses Fenster braucht ein sichtbares Schliessen
	var big := r.size.x >= fr.size.x * BIG_W and r.size.y >= fr.size.y * BIG_H
	# ein eigenes ✕ nur für echte Fenster: mit eigenem Skript (Dialog) oder eines, das eingepasst werden musste
	if big and c.get_script() == null and not t.get("fix", false):
		big = false
	if not big:
		return
	big_open = true
	if _scan or not t.has("seen"):
		t["seen"] = true
		t["ok"] = _close_in(c, fr)
	if bool(t["ok"]):
		if t["x"] != null and is_instance_valid(t["x"]):
			(t["x"] as Control).visible = false
		return
	if t["x"] == null or not is_instance_valid(t["x"]):
		var x := Button.new()
		x.text = "✕"
		x.tooltip_text = "Schliessen"
		x.focus_mode = Control.FOCUS_NONE
		x.add_theme_font_size_override("font_size", 20)
		x.add_theme_stylebox_override("normal", UI.box(UI.BTN2, UI.LINE, 22, 0))
		x.add_theme_stylebox_override("hover", UI.box(UI.BTN2.lightened(0.1), UI.ACC, 22, 0))
		x.add_theme_stylebox_override("pressed", UI.box(UI.ACC.darkened(0.4), UI.ACC, 22, 0))
		x.size = Vector2(44, 44)
		x.set_meta("waechter_aus", true)
		x.pressed.connect(func(): _close(c))
		c.get_parent().add_child(x)
		t["x"] = x
		print("waechter: «%s» hatte kein sichtbares Schliessen - ✕ dazu" % _name(c))
	var xb := t["x"] as Button
	xb.visible = true
	if xb.get_index() != c.get_index() + 1:
		c.get_parent().move_child(xb, mini(c.get_index() + 1, c.get_parent().get_child_count() - 1))
	xb.global_position = Vector2(r.end.x - 48.0, r.position.y + 4.0)


func _close_in(n: Node, fr: Rect2) -> bool:
	"""is there a visible close button inside the free room? (small ✕ / × get 44 × 44 on the way)"""
	var ok := false
	for c in n.get_children():
		if c is Button and (c as Button).is_visible_in_tree() and not c.has_meta("waechter_aus"):
			var b := c as Button
			var tx := b.text.strip_edges()
			if tx in CLOSE_TXT or b.tooltip_text.contains("chliess"):
				if b.custom_minimum_size.x < 44.0 or b.custom_minimum_size.y < 44.0:   # Finger: mindestens 44 × 44
					b.custom_minimum_size = Vector2(maxf(44.0, b.custom_minimum_size.x), maxf(44.0, b.custom_minimum_size.y))
				var k := b.get_global_transform().get_scale()
				var br := Rect2(b.global_position, b.size * k)
				# nur gut, wenn es auch nach dem Verkleinern (scale) noch gross genug zum Tippen ist; sonst kommt ein eigenes ✕
				if fr.grow(2).encloses(br) and br.size.x >= 40.0 and br.size.y >= 40.0:
					ok = true
		if not ok and c is Node and c.get_child_count() > 0:
			ok = _close_in(c, fr)
		if ok:
			return true
	return ok


func _close(c: Control) -> void:
	if c.has_method("close") and c.get_method_argument_count("close") == 0:
		c.call("close")
	elif c.has_method("close"):
		c.call("close", false)
	elif c.has_method("open") and _first_arg_bool(c, "open"):
		c.call("open", false)                           # home_editor, planner, pruefstand: open(on: bool)
	elif c.has_method("toggle") and c.get_method_argument_count("toggle") == 0:
		c.call("toggle")
	else:
		c.visible = false
	if c.visible:
		c.visible = false


func _first_arg_bool(o: Object, m: String) -> bool:
	for d in o.get_method_list():
		if d["name"] == m:
			var a: Array = d.get("args", [])
			return a.size() > 0 and int(a[0].get("type", -1)) == TYPE_BOOL
	return false


func _windows() -> void:
	"""embedded Godot windows (dialogs, file dialog): never larger than the view, always inside"""
	var vs := Vector2i(main.get_viewport().get_visible_rect().size)
	var ws := []
	for l in _layers:
		if is_instance_valid(l):
			_all_windows(l, ws, 0)
	for w in ws:
		var win := w as Window
		if not win.visible or win is PopupMenu:
			continue
		var sz := win.size
		var nsz := Vector2i(mini(sz.x, vs.x - 8), mini(sz.y, vs.y - 8))
		if nsz != sz:
			win.size = nsz
			fitted += 1
		var p := win.position
		var np := Vector2i(clampi(p.x, 4, maxi(4, vs.x - nsz.x - 4)), clampi(p.y, 4, maxi(4, vs.y - nsz.y - 4)))
		if np != p:
			win.position = np


func _all_windows(n: Node, out: Array, depth: int) -> void:
	for c in n.get_children():
		if c is Window:
			out.append(c)
		elif depth < 4 and c.get_child_count() > 0 and not (c is ScrollContainer):
			_all_windows(c, out, depth + 1)


func _name(c: Node) -> String:
	var s = c.get_script()
	return (s.resource_path.get_file() if s != null else "") + ":" + str(c.name)


func info() -> Dictionary:
	var l := []
	for c in _track:
		if is_instance_valid(c):
			l.append({"name": _name(c), "scale": snappedf(float(_track[c]["k"]), 0.01), "x": _track[c]["x"] != null})
	return {"tracked": l, "fitted": fitted}
