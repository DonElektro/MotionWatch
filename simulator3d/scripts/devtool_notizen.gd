extends Node
## Entwicklertool 3 · Notizen an Claude (Daniel 31.10.2026): eine Stelle markieren (in der 3D-Ansicht anklicken, die Kamera
## jetzt, oder auf der Karte), Text dazu, Kategorie (Fehler / Idee / Grafik, freiwillig). Automatisch dabei: Welt, Szene,
## Position (Szene und Welt), Blickrichtung, Uhrzeit, Wetter, Jahreszeit, Version, Lite, ein kleines Bild (480 × 270) der
## Ansicht ohne Bedienelemente. KEINE Einstellungen, keine Passwörter, keine Namen, keine Pfade des PCs in den Metadaten.
## Ablage: user://dev_notizen/<id>.json + <id>.jpg. Liste: hinspringen, abhaken, löschen. Marker auf der Karte (devtool.gd).
## «Alle Notizen exportieren»: user://dev_notizen_export/MoveEye_Notizen_<datum>.zip (notizen.json + LIESMICH.txt + Bilder) -
## Daniel hängt sie im Chat an. Auch über HTTP: GET /dev/notizen.zip, /dev/notizen.json, /dev/notizen/<id>.jpg.
## /control {"action": "dev", "do": "notes" | "note_add" (text, cat, x, z = Welt-Koordinaten, sonst die Kamera) |
##   "note_done" (id, value) | "note_delete" (id) | "note_goto" (id) | "notes_export"}

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Scenes = preload("res://scripts/scenes.gd")

const DIR := "user://dev_notizen"
const EXPORT_DIR := "user://dev_notizen_export"
const CATS := [["", "— ohne —"], ["fehler", "Fehler"], ["idee", "Idee"], ["grafik", "Grafik"]]
const CAT_COL := {"": Color("#f59a4a"), "fehler": Color("#ff4d4d"), "idee": Color("#3fcf6b"), "grafik": Color("#b07cff")}
const PIC := Vector2i(480, 270)

var x                                    # devtool_extra.gd
var dev
var main
var notes: Array = []                    # newest first
var _loaded := false
var arm := ""                            # "" | "3d" | "karte": the next click marks the place
var spot := {}                           # the marked place: {src, pos (scene) | null, wpos (world) | null, world, scene}
var _down = null
var _cat: OptionButton
var _text: TextEdit
var _spot_l: Label
var _list: ItemList
var _sel := ""
var _path: LineEdit
var _b3d: Button
var _bmap: Button


# =============================================================================================================================
# the notes on disk
# =============================================================================================================================
func load_all() -> void:
	_loaded = true
	notes = []
	var d := DirAccess.open(DIR)
	if d == null:
		return
	for f in d.get_files():
		if f.ends_with(".json"):
			var n = JSON.parse_string(FileAccess.get_file_as_string(DIR + "/" + f))
			if n is Dictionary and n.has("id"):
				notes.append(n)
	notes.sort_custom(func(a, b): return str(a.get("t", "")) > str(b.get("t", "")))


func _write(n: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(DIR)
	var f := FileAccess.open("%s/%s.json" % [DIR, n["id"]], FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(n, " "))
		f.close()


func find(id: String) -> Dictionary:
	if not _loaded:
		load_all()
	for n in notes:
		if str(n["id"]) == id:
			return n
	return {}


static func _r(v, s := 0.01):
	return snappedf(float(v), s)


func _here() -> Dictionary:
	"""what is attached to every note (no settings, no names, no paths, no passwords)"""
	var cam: Camera3D = main.view_cam
	var f := -cam.global_transform.basis.z
	var yaw := fposmod(rad_to_deg(atan2(f.x, -f.z)), 360.0)       # 0 = north (-z), 90 = east (+x)
	var pitch := rad_to_deg(asin(clampf(f.y, -1.0, 1.0)))
	var cw = dev.to_world(cam.global_position)
	var ex = main.explore
	return {"world": dev.loaded_world(), "scene": str(main.scene), "scene_name": Scenes.name_of(str(main.scene)),
			"cam": {"pos": dev._v(cam.global_position), "world": dev._w2(cw), "look": [_r(f.x, 0.001), _r(f.y, 0.001), _r(f.z, 0.001)],
				"yaw": _r(yaw, 0.1), "pitch": _r(pitch, 0.1), "fov": _r(cam.fov, 0.1)},
			"hour": _r(main.hour(), 0.01), "clock": "%02d:%02d" % [int(main.hour()), int(fmod(main.hour(), 1.0) * 60.0)],
			"weather": str(main.weather), "season": str(main.get("season")), "dark": bool(main.is_dark()),
			"version": str(main.VERSION), "lite": bool(dev._lite()), "view_mode": int(main.view_mode),
			"explore": bool(ex.on) if ex != null else false, "fly": bool(ex.fly) if ex != null else false,
			"lang": T.lang()}


func add(text: String, cat := "", sp := {}) -> Dictionary:
	"""a new note at the marked place sp (or the camera); the picture follows a moment later"""
	if not _loaded:
		load_all()
	if not cat in ["", "fehler", "idee", "grafik"]:
		cat = ""
	var dt := Time.get_datetime_dict_from_system()
	var id := "n%04d%02d%02d_%02d%02d%02d_%03d" % [dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, randi() % 1000]
	var n := _here()
	n.merge({"id": id, "t": Time.get_datetime_string_from_system(false, true), "text": text.strip_edges().left(4000), "cat": cat, "done": false,
			"src": str(sp.get("src", "kamera")), "jpg": ""}, true)
	var cam: Camera3D = main.view_cam
	var pos = sp.get("pos", null)
	var wpos = sp.get("wpos", null)
	if pos == null and wpos == null:                 # «Hier (Kamera)»: the ground in the middle of the view, else the camera
		var c: Vector2 = main.get_viewport().get_visible_rect().size * 0.5
		pos = _hit(c)
		if pos == null or (pos as Vector3).distance_to(cam.global_position) > 150.0:
			pos = cam.global_position
	if pos != null and wpos == null:
		wpos = dev.to_world(pos)
	if str(sp.get("world", "")) != "":
		n["world"] = str(sp["world"])
	n["pos"] = dev._v(pos) if pos != null else null
	n["wpos"] = dev._w2(wpos) if wpos != null else null
	notes.push_front(n)
	_write(n)
	_take_pic(n, pos)
	_fill()
	return n


func _take_pic(n: Dictionary, pos) -> void:
	var xf = null
	if str(n["src"]) == "karte":                     # marked on the map: a picture looking at the place (if its world is loaded)
		if pos == null and n.get("wpos") != null and str(n["world"]) == dev.loaded_world():
			var fr = dev.frame()
			if fr != null:
				pos = (fr as Transform3D) * Vector3(float(n["wpos"][0]), 0, float(n["wpos"][1]))
				pos.y = main.ground_y(pos.x, pos.z)
		if pos == null or str(n["world"]) != dev.loaded_world():
			return                                   # (another world: no picture)
		var tgt: Vector3 = pos + Vector3(0, 1.0, 0)
		var from: Vector3 = tgt + Vector3(0, 10.0, 16.0)
		from.y = maxf(from.y, main.ground_y(from.x, from.z) + 2.0)
		xf = Transform3D(Basis(), from).looking_at(tgt, Vector3.UP)
	var img: Image = await x.photo(PIC, xf)
	if img == null:
		return
	DirAccess.make_dir_recursive_absolute(DIR)
	if img.save_jpg("%s/%s.jpg" % [DIR, n["id"]], 0.82) == OK:
		n["jpg"] = "%s.jpg" % n["id"]
		_write(n)


func set_done(id: String, v: bool) -> bool:
	var n := find(id)
	if n.is_empty():
		return false
	n["done"] = v
	_write(n)
	_fill()
	return true


func delete(id: String) -> bool:
	var n := find(id)
	if n.is_empty():
		return false
	DirAccess.remove_absolute("%s/%s.json" % [DIR, id])
	DirAccess.remove_absolute("%s/%s.jpg" % [DIR, id])
	notes.erase(n)
	if _sel == id:
		_sel = ""
	_fill()
	return true


func goto(id: String) -> Dictionary:
	var n := find(id)
	if n.is_empty():
		return {"ok": false, "error": "unknown note"}
	var sc := str(n.get("scene", ""))
	if sc != "" and sc != str(main.scene):
		if not main.set_scene(sc):
			return {"ok": false, "error": "cannot load", "scene": sc}
	var cam: Camera3D = main.view_cam
	var c: Dictionary = n.get("cam", {})
	var ex = main.explore
	if str(n.get("src", "")) != "karte" and c.has("pos") and not (ex != null and ex.on):
		main._to_free_view()
		main.follow = false
		if main.spectate:
			main.spectate_stop()
		if main.fly_tw != null:
			main.fly_tw.kill()
		var p := Vector3(float(c["pos"][0]), float(c["pos"][1]), float(c["pos"][2]))
		var lk := Vector3(float(c["look"][0]), float(c["look"][1]), float(c["look"][2]))
		cam.global_transform = Transform3D(Basis(), p).looking_at(p + lk, Vector3.UP if absf(lk.y) < 0.98 else Vector3.FORWARD)
	else:
		var p2 = null
		if n.get("pos") != null and str(n.get("src", "")) != "karte":
			p2 = Vector3(float(n["pos"][0]), float(n["pos"][1]), float(n["pos"][2]))
		elif n.get("wpos") != null:
			var fr = dev.frame()
			if fr != null:
				p2 = (fr as Transform3D) * Vector3(float(n["wpos"][0]), 0, float(n["wpos"][1]))
				p2.y = main.ground_y(p2.x, p2.z)
		if p2 == null:
			return {"ok": false, "error": "no place"}
		dev.view_at(p2, 18.0, true)
	_sel = id
	dev._say(T.t("Sprung zur Notiz: %s") % str(n.get("text", "")).left(40))
	return {"ok": true, "id": id, "scene": main.scene}


func export_zip() -> String:
	"""all notes as one ZIP (to attach in the chat) - returns the user:// path or ''"""
	load_all()
	DirAccess.make_dir_recursive_absolute(EXPORT_DIR)
	var dt := Time.get_datetime_dict_from_system()
	var path := "%s/MoveEye_Notizen_%04d-%02d-%02d_%02d%02d.zip" % [EXPORT_DIR, dt.year, dt.month, dt.day, dt.hour, dt.minute]
	var entries := [["notizen.json", JSON.stringify({"v": 1, "app": "MoveEye 3D-Simulator", "version": str(main.VERSION), "n": notes.size(), "notes": notes}, " ").to_utf8_buffer()]]
	var open_n := notes.filter(func(n): return not bool(n.get("done", false))).size()
	var txt := "Notizen aus dem MoveEye-Simulator (Entwickler → Notizen an Claude)\n%d Notizen, davon %d offen. Version %s.\n\n" % [notes.size(), open_n, main.VERSION]
	for n in notes:
		txt += "[%s] %s%s · %s · %s %s · %s\n  %s\n\n" % ["x" if bool(n.get("done", false)) else " ", (str(n["cat"]).to_upper() + " · ") if str(n.get("cat", "")) != "" else "",
				str(n.get("t", "")), str(n.get("scene", "")), str(n.get("clock", "")), str(n.get("weather", "")), str(n["id"]), str(n.get("text", "")).replace("\n", "\n  ")]
	entries.append(["LIESMICH.txt", txt.to_utf8_buffer()])
	for n in notes:
		var jp := "%s/%s.jpg" % [DIR, n["id"]]
		if FileAccess.file_exists(jp):
			entries.append(["bilder/%s.jpg" % n["id"], FileAccess.get_file_as_bytes(jp)])
	if not pack_zip(path, entries):
		return ""
	return path


static func pack_zip(path: String, entries: Array) -> bool:
	"""one ZIP from [[name in the ZIP, PackedByteArray], …] - also used by the play test (devtool_spieltest.gd «ZIP für Claude»)"""
	var z := ZIPPacker.new()
	if z.open(path) != OK:
		return false
	for e in entries:
		z.start_file(str(e[0]))
		z.write_file(e[1])
		z.close_file()
	z.close()
	return true


# =============================================================================================================================
# marking a place: a click into the 3D view or on the map
# =============================================================================================================================
func _hit(p: Vector2):
	var cam: Camera3D = main.view_cam
	var o := cam.project_ray_origin(p)
	var d := cam.project_ray_normal(p)
	var q := PhysicsRayQueryParameters3D.create(o, o + d * 400.0)
	var r := cam.get_world_3d().direct_space_state.intersect_ray(q)
	if not r.is_empty():
		return r["position"]
	return main.ground_hit(o, d)


func _input(ev: InputEvent) -> void:
	if arm != "3d" or not (ev is InputEventMouseButton) or ev.button_index != MOUSE_BUTTON_LEFT:
		return
	if dev.panel != null and dev.panel.is_visible_in_tree() and dev.panel.get_global_rect().has_point(ev.position):
		return
	if main.fenster != null and main.fenster.has_method("over") and main.fenster.over(ev.position):
		return
	if ev.pressed:
		_down = ev.position
		get_viewport().set_input_as_handled()
		return
	if _down == null:
		return
	_down = null
	get_viewport().set_input_as_handled()
	var h = _hit(ev.position)
	if h == null:
		dev._say(T.t("Dort ist nichts zum Anklicken – nochmals versuchen."))
		return
	_set_spot({"src": "3d", "pos": h, "wpos": dev.to_world(h), "world": dev.loaded_world(), "scene": str(main.scene)})


func map_click(wp: Vector2) -> bool:
	if arm == "karte":
		_set_spot({"src": "karte", "pos": null, "wpos": wp, "world": str(dev.world), "scene": ""})
		return true
	var m = dev._map
	if m == null:
		return false
	var sp: Vector2 = m.S(wp)
	for n in notes:                                    # a click on a note marker: jump there
		if str(n.get("world", "")) == str(dev.world) and n.get("wpos") != null:
			if m.S(Vector2(float(n["wpos"][0]), float(n["wpos"][1]))).distance_to(sp) < 8.0:
				goto(str(n["id"]))
				return true
	return false


func _set_spot(s: Dictionary) -> void:
	spot = s
	arm = ""
	_paint_arm()
	var wp = s.get("wpos")
	_spot_l.text = T.t("Stelle: %s") % ("%s · %s" % [dev.world_name(str(s["world"])) if str(s["world"]) != "" else str(main.scene),
			("x %.0f · z %.0f" % [wp.x, wp.y]) if wp != null else ""])
	dev._say(T.t("Stelle markiert – jetzt den Text schreiben und speichern."))
	if dev._map != null:
		dev._map.queue_redraw()
	if _text != null:
		_text.grab_focus()


func map_draw(m: Control) -> void:
	if not _loaded:
		load_all()
	var font := m.get_theme_default_font()
	for n in notes:
		if str(n.get("world", "")) != str(dev.world) or n.get("wpos") == null:
			continue
		var p: Vector2 = m.S(Vector2(float(n["wpos"][0]), float(n["wpos"][1])))
		if p.x < -10.0 or p.y < -10.0 or p.x > m.size.x + 10.0 or p.y > m.size.y + 10.0:
			continue
		var col: Color = CAT_COL.get(str(n.get("cat", "")), CAT_COL[""])
		if bool(n.get("done", false)):
			col = Color(0.55, 0.6, 0.65)
		m.draw_colored_polygon(PackedVector2Array([p, p + Vector2(-5, -9), p + Vector2(5, -9)]), col)
		m.draw_circle(p + Vector2(0, -11), 5.5, col)
		m.draw_arc(p + Vector2(0, -11), 5.5, 0.0, TAU, 12, Color.BLACK, 1.0)
		m.draw_string(font, p + Vector2(-2.5, -7.5), "✓" if bool(n.get("done", false)) else "!", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color.BLACK)
		if str(n["id"]) == _sel:
			m.draw_arc(p + Vector2(0, -11), 9.0, 0.0, TAU, 16, Color.WHITE, 2.0)
	var wp = spot.get("wpos")
	if wp != null and str(spot.get("world", "")) == str(dev.world):     # the place marked for the next note
		var q: Vector2 = m.S(wp)
		m.draw_arc(q, 7.0, 0.0, TAU, 16, Color("#f59a4a"), 2.0)
		m.draw_line(q - Vector2(11, 0), q + Vector2(11, 0), Color("#f59a4a"), 1.5)
		m.draw_line(q - Vector2(0, 11), q + Vector2(0, 11), Color("#f59a4a"), 1.5)


# =============================================================================================================================
# the part of the window
# =============================================================================================================================
func build(v: VBoxContainer) -> void:
	var r1 := HBoxContainer.new()
	r1.add_theme_constant_override("separation", 6)
	v.add_child(r1)
	var l := Label.new()
	l.text = T.t("Stelle")
	r1.add_child(l)
	_b3d = Button.new()
	_b3d.text = T.t("In 3D anklicken")
	_b3d.toggle_mode = true
	_b3d.tooltip_text = T.t("Danach in die 3D-Ansicht klicken (ausserhalb dieses Fensters)")
	_b3d.toggled.connect(func(on): arm = "3d" if on else ""; _paint_arm())
	r1.add_child(_b3d)
	var bc := Button.new()
	bc.text = T.t("Hier (Kamera)")
	bc.tooltip_text = T.t("Die Mitte der Ansicht jetzt")
	bc.pressed.connect(func(): _set_spot({"src": "kamera", "pos": null, "wpos": null, "world": dev.loaded_world(), "scene": str(main.scene)}))
	r1.add_child(bc)
	_bmap = Button.new()
	_bmap.text = T.t("Auf der Karte")
	_bmap.toggle_mode = true
	_bmap.tooltip_text = T.t("Danach auf die Karte oben klicken")
	_bmap.toggled.connect(func(on): arm = "karte" if on else ""; _paint_arm())
	r1.add_child(_bmap)
	_cat = OptionButton.new()
	for c in CATS:
		_cat.add_item(T.t(str(c[1])))
	_cat.tooltip_text = T.t("Kategorie (freiwillig)")
	r1.add_child(_cat)
	_spot_l = UI.small(T.t("Stelle: noch keine (sonst die Kamera)"), UI.TXT)
	v.add_child(_spot_l)
	_text = TextEdit.new()
	_text.placeholder_text = T.t("Was ist hier? Text an Claude …")
	_text.custom_minimum_size = Vector2(598, 52)
	_text.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	v.add_child(_text)
	var r2 := HBoxContainer.new()
	r2.add_theme_constant_override("separation", 6)
	v.add_child(r2)
	var bs := Button.new()
	bs.text = T.t("Notiz speichern")
	UI.primary(bs)
	bs.pressed.connect(_save_pressed)
	r2.add_child(bs)
	var bg := Button.new()
	bg.text = T.t("Hinspringen")
	bg.pressed.connect(func(): _goto_sel())
	r2.add_child(bg)
	var bd := Button.new()
	bd.text = T.t("Abhaken")
	bd.pressed.connect(func():
		var n := find(_sel)
		if not n.is_empty():
			set_done(_sel, not bool(n.get("done", false))))
	r2.add_child(bd)
	var bx := Button.new()
	bx.text = T.t("Löschen")
	bx.pressed.connect(func(): _delete_sel())
	r2.add_child(bx)
	_list = ItemList.new()
	_list.custom_minimum_size = Vector2(598, 96)
	_list.add_theme_font_size_override("font_size", 13)
	_list.item_selected.connect(func(i):
		_sel = str(_list.get_item_metadata(i))
		if dev._map != null:
			dev._map.queue_redraw())
	_list.item_activated.connect(func(i): goto(str(_list.get_item_metadata(i))))
	v.add_child(_list)
	var r3 := HBoxContainer.new()
	r3.add_theme_constant_override("separation", 6)
	v.add_child(r3)
	var be := Button.new()
	be.text = T.t("Alle Notizen exportieren")
	be.pressed.connect(_export_pressed)
	r3.add_child(be)
	var bo := Button.new()
	bo.text = T.t("Ordner öffnen")
	bo.pressed.connect(func(): x.open_folder(EXPORT_DIR))
	r3.add_child(bo)
	_path = LineEdit.new()
	_path.editable = false
	_path.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_path.placeholder_text = T.t("Die ZIP-Datei kannst du im Chat anhängen.")
	r3.add_child(_path)
	load_all()
	_fill()


func _goto_sel() -> void:
	if _sel != "":
		goto(_sel)


func _delete_sel() -> void:
	if _sel != "":
		delete(_sel)


func on_show(tab: String) -> void:
	if tab != "notizen" and arm != "":
		arm = ""
		_paint_arm()
	if tab == "notizen":
		load_all()
		_fill()


func _paint_arm() -> void:
	if _b3d != null:
		_b3d.set_pressed_no_signal(arm == "3d")
		_bmap.set_pressed_no_signal(arm == "karte")
	if arm == "3d":
		dev._say(T.t("Jetzt in die 3D-Ansicht klicken."))
	elif arm == "karte":
		dev._say(T.t("Jetzt auf die Karte klicken."))


func _save_pressed() -> void:
	if _text.text.strip_edges() == "":
		dev._say(T.t("Bitte zuerst einen Text schreiben."))
		return
	var n := add(_text.text, str(CATS[_cat.selected][0]), spot)
	_text.text = ""
	spot = {}
	_spot_l.text = T.t("Stelle: noch keine (sonst die Kamera)")
	_sel = str(n["id"])
	_fill()
	dev._say(T.t("Notiz gespeichert (%d)") % notes.size())


func _export_pressed() -> void:
	var p := export_zip()
	if p == "":
		dev._say(T.t("Export ging nicht."))
		return
	_path.text = T.t("Datei hier: %s") % ProjectSettings.globalize_path(p)
	dev._say(T.t("%d Notizen exportiert.") % notes.size())


func _fill() -> void:
	if _list == null:
		return
	_list.clear()
	for n in notes:
		var cat := str(n.get("cat", ""))
		var t := "%s %s%s  · %s · %s" % ["✓" if bool(n.get("done", false)) else "•", ("[%s] " % T.t(_cat_name(cat))) if cat != "" else "",
				str(n.get("text", "")).replace("\n", " ").left(60), dev.world_name(str(n.get("world", ""))) if str(n.get("world", "")) != "" else str(n.get("scene", "")),
				str(n.get("t", "")).substr(5, 11).replace("T", " ")]
		var i := _list.add_item(t)
		_list.set_item_metadata(i, str(n["id"]))
		_list.set_item_custom_fg_color(i, Color(0.55, 0.6, 0.65) if bool(n.get("done", false)) else CAT_COL.get(cat, UI.TXT).lerp(UI.TXT, 0.4))
		if str(n["id"]) == _sel:
			_list.select(i)
	if dev._map != null:
		dev._map.queue_redraw()


static func _cat_name(c: String) -> String:
	for e in CATS:
		if e[0] == c:
			return str(e[1])
	return c


# =============================================================================================================================
# /control
# =============================================================================================================================
func control(d: Dictionary) -> Dictionary:
	if not _loaded:
		load_all()
	match str(d.get("do", "")):
		"note_add":
			var sp := {"src": "kamera"}
			if d.has("x") and d.has("z"):
				sp = {"src": "karte", "pos": null, "wpos": Vector2(float(d["x"]), float(d["z"])), "world": str(d.get("world", dev.loaded_world())), "scene": ""}
			var n := add(str(d.get("text", "")), str(d.get("cat", "")), sp)
			return {"ok": true, "note": n}
		"note_done":
			return {"ok": set_done(str(d.get("id", "")), bool(d.get("value", true)))}
		"note_delete":
			return {"ok": delete(str(d.get("id", "")))}
		"note_goto":
			return goto(str(d.get("id", "")))
		"notes_export":
			var p := export_zip()
			return {"ok": p != "", "path": ProjectSettings.globalize_path(p) if p != "" else "", "url": "/dev/notizen.zip"}
	var L := notes.duplicate()
	if d.has("open"):
		L = L.filter(func(n): return not bool(n.get("done", false)))
	return {"ok": true, "n": L.size(), "open": notes.filter(func(n): return not bool(n.get("done", false))).size(), "notes": L,
			"pic_url": "/dev/notizen/<id>.jpg", "zip_url": "/dev/notizen.zip"}
