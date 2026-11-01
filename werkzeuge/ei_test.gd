extends SceneTree
## Test des Bergtal-Geheimnisses (simulator3d/scripts/bergtal_ei.gd) ohne Bild – der ganze Ablauf über die Steuer-API.
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/ei_test.gd"            (nur Regeln)
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/ei_test.gd" -- --mit-welt --no-update --no-tour --port 9461
## Regeln: ccw_heart wie MoveEye (Herz im Gegenuhrzeigersinn ja, im Uhrzeigersinn / zu klein / offen nein), belly_matrix gleich
## wie _BELLY in quelle/230_waermebild.py, das Blinkmuster, die Texte in texte.json übersetzt.
## Mit der Welt (Bergtal, Nacht): falsches Muster / nicht gezielt -> nichts; das richtige Muster mit echten Pausen (Licht-Kanten
## wie von MoveEye, mit Zittern) -> drei schnelle Blitze, Strahl schwenkt zum Wasserfall, Höhle öffnet sich; das Murmeltier ist
## dunkel, sein Wärme-Zwilling warm; Herz im Uhrzeigersinn / daneben -> nichts, Herz auf dem Murmeltier -> es dreht sich um
## (Bauch), Entdeckung + geheimes Abzeichen; MoveEye-Weg (Kopfkamera, x/y aus «egg» in world_reply); Strahl geht nach 30 s;
## reset -> alles wieder zu. Ende: «Ei-Test OK» oder «SCRIPT ERROR: Ei-Test: …» (Exit 0 / 1).

var errs := []
var m = null


func _init() -> void:
	var Ei = load("res://scripts/bergtal_ei.gd")
	var hp: Array = Ei.heart_points(400.0, 300.0, 120.0)
	var ccw := hp.duplicate()
	ccw.reverse()
	_ok("Herz im Gegenuhrzeigersinn erkannt", Ei.ccw_heart(ccw))
	_ok("Herz im Uhrzeigersinn abgelehnt", not Ei.ccw_heart(hp))
	var small: Array = Ei.heart_points(400.0, 300.0, 30.0)
	small.reverse()
	_ok("kleines Herz abgelehnt", not Ei.ccw_heart(small))
	var circ := []
	for i in range(40):
		circ.append(Vector2(400 + 120 * cos(-TAU * i / 40.0), 300 + 120 * sin(-TAU * i / 40.0)))
	_ok("Kreis abgelehnt", not Ei.ccw_heart(circ))
	_ok("offenes Herz abgelehnt", not Ei.ccw_heart(ccw.slice(0, 30)))
	# the same pattern as MoveEye (part 230)
	var src := FileAccess.get_file_as_string(ProjectSettings.globalize_path("res://").path_join("../quelle/230_waermebild.py"))
	var rx := RegEx.create_from_string('_BELLY = "([0-9]+:[0-9a-f]+)"')
	var mt := rx.search(src)
	_ok("belly_matrix gleich wie MoveEye (_BELLY, Teil 230)", mt != null and mt.get_string(1) == Ei.BELLY)
	var bm: Array = Ei.belly_matrix()
	_ok("belly_matrix 25 × 25", bm.size() == 25 and (bm[0] as Array).size() == 25 and bool(bm[0][0]))
	# the pattern of the light: on-times sum up as MUSTER says
	var on := 0
	var flanks := 0
	var prev := false
	for i in range(int(20.0 / 0.01)):
		var o: bool = Ei.pattern_on(i * 0.01)
		if o and not prev:
			flanks += 1
		on += 1 if o else 0
		prev = o
	print("Muster: %d Blitze in 20 s" % flanks)
	_ok("Muster blinkt (2–3 Durchgänge in 20 s)", flanks >= 8 and flanks <= 15)
	# texts
	var tx = JSON.parse_string(FileAccess.get_file_as_string("res://i18n/texte.json"))
	for t in ["Das Murmeltier hinter dem Wasserfall", "Du hast das Licht vom Chalchstock verstanden. Das Murmeltier hat dir sein Geheimnis gezeigt.",
			"Murmeltier-Geheimnis", "Psst … es gibt ein verstecktes Easter Egg."]:
		var row = tx.get(t, null)
		var full: bool = row is Dictionary
		if full:
			for l in ["en", "fr", "it", "rm"]:
				full = full and str(row.get(l, "")) != ""
		_ok("übersetzt: " + t.left(40), full)
	if "--mit-welt" in OS.get_cmdline_user_args():
		_welt.call_deferred()
		return
	_ende()


func _ok(what: String, cond: bool, info = null) -> void:
	print(("  ok   " if cond else "  FEHLER ") + what + ("" if cond or info == null else "  -> " + str(info).left(300)))
	if not cond:
		errs.append(what)


func _ende() -> void:
	if errs.is_empty():
		print("Ei-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Ei-Test: " + str(e))
		quit(1)


func _warte(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func E(d: Dictionary) -> Dictionary:
	return m.control(d.merged({"action": "egg"}, true))


func _welt() -> void:
	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in range(60):
		await process_frame
	m.control({"action": "scenario", "id": "bergtal"})
	var w := 0
	while w < 240 and (m.bt_ei == null or not is_instance_valid(m.bt_ei)):
		await _warte(0.5)
		w += 1
	if m.bt_ei == null:
		errs.append("Bergtal ohne bergtal_ei (nach %d s)" % int(w * 0.5))
		_ende()
		return
	print("Bergtal gebaut nach %.1f s" % (w * 0.5))
	m.set_hour(23.0)
	await _warte(1.0)
	E({"do": "reset"})
	var i: Dictionary = E({"do": "info"})
	_ok("Nacht, Höhle zu, nicht gefunden", i.dark and not i.cave_open and not i.found and i.stage == "idle", i)
	_ok("vorher kein Eintrag im Entdeckungsbuch", not m.entdecken.items.has("berg.geheim.murmeltier") and not _badge())
	_ok("vorher nichts für MoveEye (world_reply egg)", m.world_reply().get("egg") == null)
	# the light blinks in the pattern at night
	var seen_on := 0
	for k in range(40):
		await _warte(0.1)
		seen_on += 1 if bool(E({"do": "info"}).lamp_on) else 0
	_ok("Antenne blinkt nachts (an und aus)", seen_on > 3 and seen_on < 37, seen_on)
	# wrong answers
	var r: Dictionary = E({"do": "signal", "falsch": true})
	_ok("falsches Muster: nichts", not r.accepted and r.stage == "idle", r)
	r = E({"do": "signal", "daneben": true})
	_ok("richtiges Muster, aber nicht auf die Antenne: nichts", not r.accepted and r.last == "zielen", r)
	# the right answer with real time, like MoveEye's light: edges with jitter (latency, few pictures per second)
	E({"do": "look", "what": "antenna"})
	await _warte(0.3)
	_ok("Ansicht zielt auf die Antenne", bool(E({"do": "info"}).aimed))
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for c in "kklkl":
		m.bt_ei.on_light(true, "mw")
		await _warte((0.3 if c == "k" else 1.0) + rng.randf_range(-0.08, 0.15))
		m.bt_ei.on_light(false, "mw")
		await _warte(0.5 + rng.randf_range(-0.1, 0.3))
	i = E({"do": "info"})
	_ok("richtiges Muster (echte Zeit, Zittern): Antwort", i.last == "ok" and i.stage in ["ack", "swing"], i)
	await _warte(2.0)
	i = E({"do": "info"})
	_ok("Strahl schwenkt", i.stage == "swing" and i.beam, i)
	await _warte(7.5)
	i = E({"do": "info"})
	var we: Array = i.waterfall
	var be: Array = i.beam_end
	_ok("Strahl steht auf dem Tuffwasserfall, Licht dort an", i.stage == "hold" and i.spot and Vector3(we[0], we[1], we[2]).distance_to(Vector3(be[0], be[1], be[2])) < 0.5, i)
	_ok("Höhle öffnet sich", i.cave_open)
	await _warte(3.5)
	i = E({"do": "info"})
	_ok("Stein ist zur Seite gerollt", float(i.slab_moved) > 1.0, i)
	# dark marmot, warm twin
	var mm: Node3D = m.bt_ei.marmot
	var vis_dark := true
	var warm := 0
	for ch in mm.get_children():
		if ch is MeshInstance3D and (ch as MeshInstance3D).layers == 1 and ch.material_override is StandardMaterial3D and ch != m.bt_ei._belly:
			var col: Color = (ch.material_override as StandardMaterial3D).albedo_color
			vis_dark = vis_dark and col.get_luminance() < 0.15
		if ch is MeshInstance3D and (ch as MeshInstance3D).layers == 2 and ch.material_override is ShaderMaterial:
			if float((ch.material_override as ShaderMaterial).get_shader_parameter("temp")) > float(m.ambient) + 6.0:
				warm += 1
	_ok("Murmeltier dunkel (von blossem Auge kaum zu sehen)", vis_dark)
	_ok("Murmeltier im Wärmebild warm (%d Teile)" % warm, warm >= 8)
	# hearts in the window
	E({"do": "look", "what": "cave"})
	await _warte(0.3)
	i = E({"do": "info"})
	_ok("Murmeltier im Fenster sichtbar", i.screen != null, i)
	if i.screen != null:
		var sp := Vector2(i.screen[0], i.screen[1])
		var Ei = load("res://scripts/bergtal_ei.gd")
		var cw: Array = Ei.heart_points(sp.x, sp.y, 110.0)
		r = E({"do": "draw", "pts": _arr(cw)})
		_ok("Herz im Uhrzeigersinn: nichts", not r.ok and not E({"do": "info"}).turned, r)
		var far: Array = Ei.heart_points(sp.x + 420.0, sp.y, 110.0)
		far.reverse()
		r = E({"do": "draw", "pts": _arr(far)})
		_ok("Herz daneben: nichts", not r.ok, r)
		var ok_h: Array = Ei.heart_points(sp.x, sp.y - 10.0, 110.0)
		ok_h.reverse()
		r = E({"do": "draw", "pts": _arr(ok_h)})
		_ok("Herz auf dem Murmeltier: angenommen", r.ok, r)
	await _warte(2.0)
	i = E({"do": "info"})
	_ok("Murmeltier hat sich umgedreht (Bauch nach aussen)", i.turned and i.belly_facing_out, i)
	_ok("gefunden: Entdeckungsbuch + geheimes Abzeichen", i.found and m.entdecken.items.has("berg.geheim.murmeltier") and _badge(), i)
	_ok("kein Blinki-Hinweis darauf", m.entdecken.nearest_possible() != "berg.geheim.murmeltier")
	_ok("danach nichts mehr für MoveEye", m.world_reply().get("egg") == null)
	# beam goes after 30 s
	var w2 := 0
	while w2 < 80 and bool(E({"do": "info"}).beam):
		await _warte(0.5)
		w2 += 1
	i = E({"do": "info"})
	_ok("Strahl nach ca. 30 s weg", not i.beam and i.stage == "turned", i)
	# the MoveEye way: the head camera sees the marmot -> «egg» in world_reply -> heart at x / y
	E({"do": "reset"})
	E({"do": "cave"})
	r = E({"do": "place"})
	print("MoveEye vor die Höhle: ", str(r).left(160))
	w = 0
	while w < 240:
		await _warte(0.5)
		w += 1
		if m.bt_ei != null and is_instance_valid(m.bt_ei) and m.bt_ei.cave != null and m.bt_ei.cave.is_inside_tree():
			break
	await _warte(2.0)
	i = E({"do": "info"})
	_ok("Höhle bleibt offen nach dem Neubau des Tals", i.cave_open, i)
	var eg = m.world_reply().get("egg")
	_ok("world_reply «egg»: Murmeltier im Bild der Kopfkamera", eg is Dictionary and str(eg.get("st")) == "heart", {"egg": eg, "head": i.head})
	if eg is Dictionary:
		r = E({"do": "heart", "x": float(eg.x) + 0.4, "y": float(eg.y)})
		_ok("MoveEye-Herz daneben: nichts", not r.ok, r)
		r = E({"do": "heart", "x": float(eg.x) + 0.02, "y": float(eg.y) - 0.02, "src": "mw"})
		_ok("MoveEye-Herz auf dem Murmeltier: angenommen", r.ok, r)
	# reset
	E({"do": "reset"})
	i = E({"do": "info"})
	_ok("reset: Höhle zu, nicht gefunden, Abzeichen weg", not i.cave_open and not i.found and not _badge(), i)
	print("Welt-Test fertig")
	_ende()


func _arr(pts: Array) -> Array:
	var out := []
	for p in pts:
		out.append([p.x, p.y])
	return out


func _badge() -> bool:
	if m.spielbereich == null:
		return false
	for b in m.spielbereich.badges():
		if str(b.get("id", "")) == "geheim_murmeltier":
			return true
	return false
