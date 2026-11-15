extends SceneTree
## Test «Handy-Modus und Fenster» (Besitzer 15.11.2026): der echte Simulator in 390 × 844 Punkten (Handy hoch) oder 844 × 390
## (quer). Geprüft wird:
##   1. der Handy-Modus ist an (handy.gd): Leiste mit 5 Knöpfen ganz im Bild, jeder Knopf mindestens 44 × 44
##   2. jedes Blatt (Szene, Tageszeit, Besuch, Schutz, Mehr): ganz im Bild, ✕ sichtbar und mindestens 44 × 44
##   3. Karte / Gerät / Kamera gross: im Bild, ✕ sichtbar und mindestens 44 × 44
##   4. jedes Fenster des Simulators (alle Panels in einer Ebene, eingebettete Fenster), einzeln geöffnet: ist es ein grosses
##      Fenster (mindestens 40 % der Breite und 25 % der Höhe), dann passt es ins Bild (über der Leiste) und hat ein
##      sichtbares Schliessen (✕ / Schliessen …) von mindestens 44 × 44, das nicht von etwas anderem im Fenster verdeckt ist
##   5. die Szenenliste («Vorlagen»): eine Spalte, ✕ sichtbar
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/sim_fenster_handy_test.gd" -- --no-update --no-tour
##   (oder mit Bildschirm: --rendering-driver opengl3; das Fenster stellt der Test selbst auf 780 × 1688 / 1688 × 780 Pixel,
##   Massstab 2 wie ein Handy; TEST_HANDY=hoch|quer = nur eine Lage, sonst beide nacheinander).
##   Ende: «Handy-Fenster-Test OK (…)» (Exit 0) oder «SCRIPT ERROR: Handy-Fenster-Test: …» (Exit 1).

const CLOSE := ["✕", "×", "✖", "Schliessen", "Zu", "Fertig", "OK", "Abbrechen", "Zurück", "Close"]
const TAP := 43.5                                  # 44 Punkte (Rundung)
var main
var n := 0
var tag := "hoch"
var scale := 2.0
var errs: Array = []
var notes: Array = []
var cands: Array = []
var i := -1
var phase := 0
var wait := 0
var checked := 0


var tags: Array = ["hoch", "quer"]
var wait0 := 240                                   # Bilder bis zur ersten Prüfung (Szene aufbauen)


func _orient() -> void:
	"""das Fenster wie ein Handy (Massstab 2): hoch 780 × 1688 Pixel = 390 × 844 Punkte, quer umgekehrt"""
	root.size = Vector2i(780, 1688) if tag == "hoch" else Vector2i(1688, 780)
	root.content_scale_factor = scale


func _initialize() -> void:
	var t := OS.get_environment("TEST_HANDY")          # hoch | quer (ohne: beide nacheinander)
	if t in ["hoch", "quer"]:
		tags = [t]
	tag = tags[0]
	_orient()
	main = load("res://main.tscn").instantiate()
	root.add_child(main)


func view() -> Rect2:
	return Rect2(Vector2.ZERO, root.get_visible_rect().size)


func free_rect() -> Rect2:
	return main.handy.free_rect() if main.handy != null and main.handy.on else view()


func fail(s: String) -> void:
	errs.append(s)
	print("  FEHLER: ", s)


func ok(s: String) -> void:
	print("  ok: ", s)


func _closes(nd: Node, outl: Array) -> void:
	for c in nd.get_children():
		if c is Button and (c as Button).is_visible_in_tree():
			var t := (c as Button).text.strip_edges()
			if t in CLOSE or (c as Button).tooltip_text.contains("chliess"):
				outl.append(c)
		_closes(c, outl)


func _covered(b: Control, win: Control) -> bool:
	"""liegt im selben Fenster ein später gezeichneter, sichtbarer Knopf / Panel über der Mitte des Schliessen-Knopfs?"""
	var p := b.get_global_rect().get_center()
	var hit := false
	var after := false
	var stack: Array = [win]
	var order: Array = []
	while not stack.is_empty():
		var x: Node = stack.pop_front()
		order.append(x)
		var kids := x.get_children()
		for k in range(kids.size() - 1, -1, -1):
			stack.push_front(kids[k])
	for x in order:
		if x == b:
			after = true
			continue
		if after and x is Control and (x as Control).is_visible_in_tree() and not b.is_ancestor_of(x) \
				and (x as Control).mouse_filter == Control.MOUSE_FILTER_STOP and (x is Button or x is LineEdit or x is PanelContainer) \
				and (x as Control).get_global_rect().has_point(p) and not (x as Control).is_ancestor_of(b):
			hit = true
	return hit


func _close_ok(win: Control, name: String, room: Rect2) -> void:
	var cl := []
	_closes(win, cl)
	var good := []
	var why := []
	for b in cl:
		var k: Vector2 = (b as Control).get_global_transform().get_scale()
		var r := Rect2((b as Control).global_position, (b as Control).size * k)   # so gross, wie man es sieht
		if not room.grow(1.0).encloses(r):
			why.append("%s ausserhalb" % (b as Button).text)
		elif r.size.x < 40.0 or r.size.y < 40.0:
			why.append("%s nur %d × %d" % [(b as Button).text, r.size.x, r.size.y])
		elif _covered(b, win):
			why.append("%s verdeckt" % (b as Button).text)
		else:
			good.append(b)
	if good.is_empty():
		fail("%s: kein sichtbares Schliessen ≥ 44 × 44 (%s)" % [name, ", ".join(why) if not why.is_empty() else "keines"])
	else:
		var g0 := good[0] as Control
		ok("%s: Schliessen sichtbar (%d × %d)" % [name, g0.size.x * g0.get_global_transform().get_scale().x, g0.size.y * g0.get_global_transform().get_scale().y])


func _fits(c: Control, name: String, room: Rect2) -> void:
	var r := Rect2(c.global_position, c.size * c.get_global_transform().get_scale())
	if room.grow(1.0).encloses(r):
		ok("%s passt (%d,%d %d × %d)" % [name, r.position.x, r.position.y, r.size.x, r.size.y])
	else:
		fail("%s passt nicht: %d,%d %d × %d in %d × %d" % [name, r.position.x, r.position.y, r.size.x, r.size.y, room.size.x, room.size.y])


func _collect(nd: Node, depth: int) -> void:
	for c in nd.get_children():
		if c is SubViewport:
			continue
		if c is Window and not (c is PopupMenu) and not (c is FileDialog) and not (c is AcceptDialog and depth > 5):
			cands.append(c)
			continue
		if c is Control and c.get_parent() is CanvasLayer and (c is PanelContainer or c is Panel) and not (c as Control).visible \
				and not _mini_part(c):
			cands.append(c)
		if depth < 6:
			_collect(c, depth + 1)


func _mini_part(c: Node) -> bool:
	"""kein Fenster: mini.gd (Kästchen / Symbol, wenn das Fenster des Simulators minimiert ist - dann ist das ganze
	Fenster so klein, im Browser und auf dem Handy nie)"""
	var s = c.get_parent().get_script()
	return s != null and s.resource_path.get_file() == "mini.gd"


func _texts(nd: Node, out: Array) -> void:
	for c in nd.get_children():
		if out.size() >= 3:
			return
		if (c is Label or c is Button) and str(c.text).strip_edges() != "":
			out.append(str(c.text).strip_edges().left(30))
		_texts(c, out)


func _pc_part(c: Node) -> bool:
	"""kein Fenster: Teile der PC-Oberfläche ohne eigenes Skript in der Ebene des Bedienfelds (Kopf des Bedienfelds,
	Untermenüs der Leiste - im Handy-Modus weg, «Alle Einstellungen» hat das ✕ von handy.gd), oder leere Rahmen ohne Text,
	die erst gefüllt gezeigt werden"""
	if c is Window or c.get_script() != null:
		return false
	if main.ui_root != null and c.get_parent() == main.ui_root.get_parent() and c.get_parent() is CanvasLayer:
		return true
	var t := []
	_texts(c, t)
	return t.is_empty()


func _name(c: Node) -> String:
	var t := []
	_texts(c, t)
	return "%s %s" % [_name0(c), t]


func _name0(c: Node) -> String:
	var s = c.get_script()
	return "%s[%s] in %s" % [c.name, s.resource_path.get_file() if s != null else "", str(c.get_parent().get_path()).get_file()]


func _open(c: Node) -> void:
	if c is Window:
		(c as Window).popup_centered()
	elif c.has_method("toggle") and c.get_method_argument_count("toggle") == 0:
		c.call("toggle")
	elif c.has_method("open") and c.get_method_argument_count("open") == 0:
		c.call("open")
	if c is Control and not (c as Control).visible:
		(c as Control).visible = true


func _shut(c: Node) -> void:
	if c is Window:
		(c as Window).hide()
	else:
		(c as Control).visible = false


func _done() -> void:
	print("Handy-Fenster-Test %s: %d Fenster geprüft, %d Fehler bisher" % [tag, checked, errs.size()])
	var k := tags.find(tag)
	if k + 1 < tags.size():                         # nächste Lage (quer): Fenster drehen, warten, von vorn
		tag = tags[k + 1]
		_orient()
		cands.clear()
		phase = 0
		i = -1
		wait = 0
		n = 0
		wait0 = 90
		return
	if errs.is_empty():
		print("Handy-Fenster-Test OK (%s, %d Fenster)" % [", ".join(tags), checked])
		quit(0)
	else:
		push_error("Handy-Fenster-Test: " + "; ".join(errs.slice(0, 12)))
		quit(1)


func _process(_dt: float) -> bool:
	n += 1
	if n == 5:
		_orient()
	if n < wait0:
		return false
	var h = main.handy
	match phase:
		0:
			print("1. Handy-Modus (%s, Ansicht %s)" % [tag, view().size])
			if h == null or not h.on:
				fail("Handy-Modus ist nicht an")
				_done()
				return false
			ok("Handy-Modus an, quer %s" % h.landscape())
			_fits(h.bar, "Leiste", view())
			for k in h.bar_btns:
				var b: Control = h.bar_btns[k]
				if b.size.x < TAP or b.size.y < TAP:
					fail("Leiste: Knopf %s nur %d × %d" % [k, b.size.x, b.size.y])
			for k in h.win_btns:
				var b: Control = h.win_btns[k]
				_fits(b, "Randknopf " + k, h.free_rect())
			_fits(h.dpad, "Steuerkreuz", h.free_rect())
			phase = 1
			i = 0
		1:                                         # die Blätter
			if wait == 0:
				h.control({"do": "sheet", "id": h.SHEETS[i][0]})
				wait = 1
			elif wait < 6:
				wait += 1
			else:
				wait = 0
				_fits(h.sheet, "Blatt " + h.SHEETS[i][0], view())
				_close_ok(h.sheet, "Blatt " + h.SHEETS[i][0], view())
				if h.SHEETS[i][0] == "scene" and h._scene_list != null and h._scene_list.get_child_count() > 0:
					var c0: Control = h._scene_list.get_child(0)
					if c0.size.x < h.sheet.size.x * 0.8:
						fail("Szenenliste nicht einspaltig (%d von %d)" % [c0.size.x, h.sheet.size.x])
				h.close()
				i += 1
				if i >= h.SHEETS.size():
					phase = 2
					i = 0
		2:                                         # Karte / Gerät / Kamera gross
			var id: String = h.WINS[i][0]
			if wait == 0:
				h.show_win(id, true)
				wait = 1
			elif wait < 8:
				wait += 1
			else:
				wait = 0
				if h.big_id == id:
					_fits(h.big, "gross " + id, h.free_rect() if not h.landscape() else view())
					_close_ok(h.big, "gross " + id, view())
				else:
					notes.append("gross %s: nicht da (Fenster fehlt hier)" % id)
				h.show_win(id, false)
				i += 1
				if i >= h.WINS.size():
					phase = 3
		3:
			print("4. alle Fenster einzeln")
			_collect(root, 0)
			var seen := {}
			var u := []
			for c in cands:
				if not seen.has(c) and c != h.sheet and c != h.big and not (c as Node).has_meta("waechter_aus") and not h.layer.is_ancestor_of(c) \
						and not c in h._hideables() and not _pc_part(c):
					seen[c] = true
					u.append(c)
			cands = u
			print("   %d Kandidaten" % cands.size())
			phase = 4
			i = 0
		4:
			if i >= cands.size():
				phase = 5
				return false
			var c = cands[i]
			if not is_instance_valid(c):
				i += 1
				return false
			if wait == 0:
				_open(c)
				wait = 1
			elif wait < 16:                        # 16 Bilder: der Wächter (alle 0.25 s) hat eingepasst
				wait += 1
			else:
				wait = 0
				var shown: bool = (c as Window).visible if c is Window else (c as Control).is_visible_in_tree()
				if shown:
					var room := free_rect()
					if c is Window:
						var w := c as Window
						var r := Rect2(Vector2(w.position) / scale, Vector2(w.size) / scale)
						checked += 1
						if not view().grow(1.0).encloses(r):
							fail("%s (Fenster) passt nicht: %s" % [_name(c), r])
					else:
						var cc := c as Control
						var r := Rect2(cc.global_position, cc.size * cc.get_global_transform().get_scale())
						var big: bool = r.size.x >= room.size.x * 0.4 and r.size.y >= room.size.y * 0.25
						if big and (cc.get_script() != null or cc.get_child_count() > 0):
							checked += 1
							_fits(cc, _name(cc), room)
							# das Schliessen kann im Fenster liegen oder vom Wächter daneben (gleiche Ebene) kommen
							var host: Control = cc
							var extra: Control = null
							for t in main.waechter._track:
								if t == cc and main.waechter._track[t]["x"] != null and is_instance_valid(main.waechter._track[t]["x"]) \
										and (main.waechter._track[t]["x"] as Control).visible:
									extra = main.waechter._track[t]["x"]
							if extra != null:
								var er := extra.get_global_rect()
								if room.grow(1.0).encloses(er) and er.size.x >= TAP and er.size.y >= TAP:
									ok("%s: Schliessen vom Wächter" % _name(cc))
								else:
									fail("%s: Wächter-✕ nicht im Bild" % _name(cc))
							else:
								_close_ok(host, _name(cc), room)
				_shut(c)
				i += 1
		5:
			phase = 6
			_done()
	return false
