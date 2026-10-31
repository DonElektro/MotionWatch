extends Node
## Entwicklertool 3 · Kontaktbogen (Daniel 31.10.2026): «Alle Orte fotografieren» - für jeden Ort aus Dev.alle_orte (eine
## Welt oder alle): hinspringen (devtool.goto, lädt nötigenfalls die Szene), warten bis sie steht, ein Foto 640 × 360 ohne
## Bedienelemente (devtool_extra.photo). Ablage: user://kontaktbogen/<welt>/<id>.jpg, dazu user://kontaktbogen/index.html
## (Raster mit Namen, pro Welt) und kontakt.json. Im Fenster: Fortschritt, Abbrechen, kleines Raster (Klick = hinspringen).
## «bei Tag» (Standard): für jedes Foto 12 Uhr und klares Wetter (danach wieder wie vorher), damit man die Orte vergleicht.
## Danach stehen Szene, Ansicht, Uhrzeit und Wetter wieder wie vorher. Nicht während ein Testlauf / Abenteuer die Welt hat.
## Kamera (K1, 31.10.2026): devtool_kamera.gd wählt sie (freie Sicht, Augenhöhe, Abstand); nach dem Laden einer Szene wird sie
## nochmals gewählt (reaim). Danach ein kleines Probebild (96 × 54): fast schwarz oder einfarbig (Schlucht, Höhle, Hang/Wand
## direkt vor der Linse) -> die nächstbesten Kameras (kam().alts, auch eine von hoch oben) probieren, das beste Bild nehmen.
## Lite: gleich, nur länger warten (dev._lite()).
## /control {"action": "dev", "do": "contact" (world: "" = alle, day: true, ids: [...], limit: n) | "contact_state" |
##   "contact_stop" | "contact_list" (world)} - Bilder per HTTP: GET /dev/kontakt/<welt>/<id>.jpg, /dev/kontakt/index.html,
##   /dev/kontakt.json.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Dev = preload("res://scripts/devtool.gd")
const Worlds = preload("res://scripts/worlds.gd")

const DIR := "user://kontaktbogen"
const SIZE := Vector2i(640, 360)

var x                                    # devtool_extra.gd
var dev
var main
var running := false
var _cancel := false
var queue: Array = []                    # the places of this run
var done: Array = []                     # {id, name, world, kind, ok, file, url, error}
var cur := ""
var world := ""
var day := true
var t0 := 0.0
var t_end := 0.0
var _world_opt: OptionButton
var _day_chk: CheckBox
var _go: Button
var _bar: ProgressBar
var _lab: Label
var _grid: GridContainer
var _path: LineEdit
var _grid_dirty := false


# =============================================================================================================================
# the run
# =============================================================================================================================
func start(w := "", by_day := true, ids: Array = [], limit := 0) -> Dictionary:
	if running:
		return state()
	var b: String = main.busy_with("")
	if b != "":
		return {"ok": false, "error": "busy", "busy": b, "msg": main.busy_msg(b) if main.has_method("busy_msg") else b}
	var L: Array = Dev.alle_orte(main)
	if w != "":
		L = L.filter(func(e): return str(e["world"]) == w)
	if not ids.is_empty():
		L = L.filter(func(e): return str(e["id"]) in ids)
	var order := {}
	for i in Worlds.SHOWN.size():
		order[Worlds.SHOWN[i]] = i
	L.sort_custom(func(a, b2):                         # world by world, a scene at a time (fewer loads)
		var ka := "%02d|%s|%s" % [int(order.get(str(a["world"]), 99)), str(a["scene"]), str(a["id"])]
		var kb := "%02d|%s|%s" % [int(order.get(str(b2["world"]), 99)), str(b2["scene"]), str(b2["id"])]
		return ka < kb)
	if limit > 0:
		L = L.slice(0, limit)
	if L.is_empty():
		return {"ok": false, "error": "no places", "world": w}
	world = w
	day = by_day
	queue = L
	done = []
	_cancel = false
	running = true
	t0 = Time.get_ticks_msec() / 1000.0
	_run()
	_paint()
	return {"ok": true, "started": true, "n": L.size(), "world": w, "dir": ProjectSettings.globalize_path(DIR), "url": "/dev/kontakt/",
			"state_cmd": {"action": "dev", "do": "contact_state"}}


func stop() -> void:
	_cancel = true


func _wait_frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _run() -> void:
	var cam: Camera3D = main.view_cam
	var keep := {"scene": str(main.scene), "xf": cam.global_transform, "hour": main.hour(), "weather": str(main.weather)}
	var lite: bool = dev._lite()
	var last_scene := str(main.scene)
	for e in queue:
		if _cancel:
			break
		cur = str(e["id"])
		_paint()
		var r: Dictionary = dev.goto(cur)
		var loaded: bool = str(r.get("loaded", "")) != "" or str(main.scene) != last_scene
		last_scene = str(main.scene)
		var item := {"id": cur, "name": str(e["name"]), "world": str(e["world"]), "kind": str(e["kind"]), "ok": false, "geheim": bool(e.get("geheim", false))}
		if not bool(r.get("ok", false)):
			item["error"] = str(r.get("error", "?"))
			done.append(item)
			continue
		if main.fly_tw != null and main.fly_tw.is_valid():
			main.fly_tw.custom_step(10.0)            # the flight of the view: at once
		if day:
			main.set_hour(12.0)
			main.weather = "clear"
		# wait until it stands: a new scene builds, shaders compile, the sky follows the clock (Lite: longer)
		await _wait_frames((40 if lite else 16) if loaded else (10 if lite else 4))
		await get_tree().create_timer((1.5 if lite else 0.6) if loaded else (0.5 if lite else 0.15)).timeout
		if main.fly_tw != null and main.fly_tw.is_valid():
			main.fly_tw.custom_step(10.0)
		if loaded:                                   # K1: the scene is built now - choose the camera once more (devtool_kamera.gd)
			var ra: Dictionary = dev.reaim(cur)
			if ra.has("cam"):
				r["cam"] = ra["cam"]
			await _wait_frames(2 if not lite else 4)
		item["cam"] = r.get("cam", {})
		if not bool(e.get("room", false)) and not bool(r.get("room", false)):
			var chk: Dictionary = await _check_view()
			if not chk.is_empty():
				item["check"] = chk
		if _cancel:
			break
		# the view from outside is blocked (a room, the bedroom in the house): the picture of MoveEye's camera instead
		var xf = null
		var fov := -1.0
		var tp = r.get("pos", null)
		if tp is Array and tp.size() == 3 and not main.cams.is_empty():
			var to := Vector3(float(tp[0]), float(tp[1]) + 1.2, float(tp[2]))
			var from: Vector3 = main.view_cam.global_position
			var hit: Dictionary = (main.view_cam as Camera3D).get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from, to))
			var blocked: bool = not hit.is_empty() and (hit["position"] as Vector3).distance_to(to) > 1.5
			var indoor: bool = main.scenes != null and bool(main.scenes.data.get("indoor", false))
			if (blocked or indoor) and bool(e.get("at_mw", false)):
				xf = (main.cams[0] as Camera3D).global_transform
				fov = (main.cams[0] as Camera3D).fov
				item["view"] = "moveeye"
		var img: Image = await x.photo(SIZE, xf, fov)
		if img == null:
			item["error"] = "no picture"
			done.append(item)
			continue
		var wdir := "%s/%s" % [DIR, str(e["world"]).validate_filename()]
		DirAccess.make_dir_recursive_absolute(wdir)
		var fn := "%s/%s.jpg" % [wdir, cur.validate_filename()]
		if img.save_jpg(fn, 0.85) == OK:
			item["ok"] = true
			item["file"] = "%s/%s.jpg" % [str(e["world"]).validate_filename(), cur.validate_filename()]
			item["url"] = "/dev/kontakt/" + str(item["file"])
		else:
			item["error"] = "cannot save"
		done.append(item)
		_grid_dirty = true
	cur = ""
	# back as before
	if str(main.scene) != str(keep["scene"]):
		main.set_scene(str(keep["scene"]))
		await _wait_frames(3)
	if main.fly_tw != null:
		main.fly_tw.kill()
	main.view_cam.global_transform = keep["xf"]
	main.set_hour(float(keep["hour"]))
	main.weather = str(keep["weather"])
	write_index()
	running = false
	t_end = Time.get_ticks_msec() / 1000.0
	dev._say(T.t("Kontaktbogen fertig: %d Fotos") % done.filter(func(i): return bool(i["ok"])).size() if not _cancel else T.t("Kontaktbogen abgebrochen"))
	_grid_dirty = true
	_paint()


static func _look(img: Image) -> Dictionary:
	"""how a small picture looks: mean brightness and contrast (0..1) - nearly black or one colour = the view is blocked"""
	if img == null or img.is_empty():
		return {"ok": false, "q": -1.0}
	var n := 0
	var sm := 0.0
	var sq := 0.0
	var cols := {}
	for y in range(0, img.get_height(), 2):
		for x in range(0, img.get_width(), 2):
			var c := img.get_pixel(x, y)
			var l := c.get_luminance()
			sm += l
			sq += l * l
			n += 1
			cols[Vector3i(int(c.r * 6.0), int(c.g * 6.0), int(c.b * 6.0))] = true
	var mean := sm / maxf(1.0, float(n))
	var sd := sqrt(maxf(0.0, sq / maxf(1.0, float(n)) - mean * mean))
	var ok := mean > 0.13 and sd > 0.045 and cols.size() > 6
	return {"ok": ok, "mean": snappedf(mean, 0.01), "sd": snappedf(sd, 0.001), "cols": cols.size(),
			"q": minf(mean, 0.35) + sd * 2.0 + minf(float(cols.size()), 30.0) * 0.005}


func _check_view() -> Dictionary:
	"""K1: a small test picture of the chosen view; dark (gorge, cave) or one colour (slope, wall right in front): try the
	other good cameras of devtool_kamera.gd (alts) and take the best picture"""
	var k = dev.kam()
	var sz := Vector2i(96, 54)
	var cur_xf: Transform3D = main.view_cam.global_transform
	var q0 := _look(await x.photo(sz, cur_xf))
	if bool(q0.get("ok", false)) or k.alts.is_empty():
		return {} if bool(q0.get("ok", false)) else {"first": q0}
	var best_xf := cur_xf
	var best: Dictionary = q0
	var tried := 0
	for xf in k.alts:
		tried += 1
		var q := _look(await x.photo(sz, xf))
		if float(q["q"]) > float(best["q"]):
			best = q
			best_xf = xf
		if bool(q.get("ok", false)):
			break
	main.view_cam.global_transform = best_xf
	await _wait_frames(2)
	return {"first": q0, "tried": tried, "chosen": best, "changed": best_xf != cur_xf}


func state() -> Dictionary:
	var ok_n := done.filter(func(i): return bool(i["ok"])).size()
	var el := ((t_end if not running and t_end > 0.0 else Time.get_ticks_msec() / 1000.0) - t0) if t0 > 0.0 else 0.0
	return {"ok": true, "running": running, "cancelled": _cancel, "world": world, "n": queue.size(), "done": done.size(), "photos": ok_n,
			"current": cur, "seconds": snappedf(el, 0.1), "day": day, "lite": dev._lite(), "dir": ProjectSettings.globalize_path(DIR),
			"index": "/dev/kontakt/index.html", "list": done}


func list_files(w := "") -> Array:
	"""the pictures there are (from earlier runs too): [{id, name, world, kind, file, url}]"""
	var names := {}
	for e in Dev.alle_orte(main):
		names[str(e["id"]).validate_filename()] = e
	var out := []
	var d := DirAccess.open(DIR)
	if d == null:
		return out
	for wd in d.get_directories():
		if w != "" and wd != w:
			continue
		var d2 := DirAccess.open(DIR + "/" + wd)
		if d2 == null:
			continue
		for f in d2.get_files():
			if not f.ends_with(".jpg"):
				continue
			var id := f.get_basename()
			var e: Dictionary = names.get(id, {})
			out.append({"id": str(e.get("id", id)), "name": str(e.get("name", id)), "world": wd, "kind": str(e.get("kind", "")),
					"file": "%s/%s" % [wd, f], "url": "/dev/kontakt/%s/%s" % [wd, f]})
	var order := {}
	for i in Worlds.SHOWN.size():
		order[Worlds.SHOWN[i]] = i
	out.sort_custom(func(a, b): return "%02d|%s" % [int(order.get(a["world"], 99)), a["id"]] < "%02d|%s" % [int(order.get(b["world"], 99)), b["id"]])
	return out


static func _esc(s: String) -> String:
	return s.xml_escape(true)


func write_index() -> void:
	"""user://kontaktbogen/index.html: all the pictures there are, a grid per world with names"""
	var L := list_files()
	var by := {}
	for i in L:
		if not by.has(i["world"]):
			by[i["world"]] = []
		by[i["world"]].append(i)
	var h := "<!doctype html><html lang=\"de\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
	h += "<title>%s</title><style>" % _esc(T.t("Kontaktbogen"))
	h += "body{margin:0;padding:16px;background:#0a0e14;color:#e8eef5;font:14px system-ui,sans-serif}h1{font-size:20px}h2{font-size:16px;margin:24px 0 8px;color:#8a9bb0}"
	h += ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}figure{margin:0;background:#111822;border:1px solid #1f2b3a;border-radius:10px;overflow:hidden}"
	h += "img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover}figcaption{padding:6px 8px}figcaption small{display:block;color:#8a9bb0;font-size:11px;word-break:break-all}"
	h += "</style></head><body><h1>%s</h1><p>%s</p>" % [_esc(T.t("Kontaktbogen")), _esc(T.t("%d Orte · Simulator %s · %s") % [L.size(), main.VERSION, Time.get_datetime_string_from_system(false, true)])]
	for w in Worlds.SHOWN + by.keys():
		if not by.has(w):
			continue
		h += "<h2>%s (%d)</h2><div class=\"g\">" % [_esc(dev.world_name(str(w))), (by[w] as Array).size()]
		for i in by[w]:
			h += "<figure><a href=\"%s\"><img loading=\"lazy\" src=\"%s\" alt=\"\"></a><figcaption>%s<small>%s · %s</small></figcaption></figure>" % [
					_esc(i["file"]), _esc(i["file"]), _esc(T.t(str(i["name"]))), _esc(T.t(str(Dev.KIND_NAME.get(str(i["kind"]), i["kind"]))) + (" · " + T.t("geheim") if bool(i.get("geheim", false)) else "")), _esc(str(i["id"]))]
		h += "</div>"
		by.erase(w)
	h += "</body></html>"
	DirAccess.make_dir_recursive_absolute(DIR)
	var f := FileAccess.open(DIR + "/index.html", FileAccess.WRITE)
	if f != null:
		f.store_string(h)
		f.close()
	var j := FileAccess.open(DIR + "/kontakt.json", FileAccess.WRITE)
	if j != null:
		j.store_string(JSON.stringify({"v": 1, "version": str(main.VERSION), "n": L.size(), "pictures": L}, " "))
		j.close()


# =============================================================================================================================
# the part of the window
# =============================================================================================================================
func build(v: VBoxContainer) -> void:
	var r1 := HBoxContainer.new()
	r1.add_theme_constant_override("separation", 6)
	v.add_child(r1)
	_world_opt = OptionButton.new()
	_world_opt.add_item(T.t("Alle Welten"))
	_world_opt.set_item_metadata(0, "")
	for w in Worlds.SHOWN:
		_world_opt.add_item(dev.world_name(w))
		_world_opt.set_item_metadata(_world_opt.item_count - 1, w)
	_world_opt.item_selected.connect(func(_i): _paint(); _grid_dirty = true)
	r1.add_child(_world_opt)
	_day_chk = CheckBox.new()
	_day_chk.text = T.t("bei Tag (12 Uhr, klar)")
	_day_chk.button_pressed = true
	r1.add_child(_day_chk)
	_go = Button.new()
	UI.primary(_go)
	_go.pressed.connect(func():
		if running:
			stop()
		else:
			var r := start(str(_world_opt.get_item_metadata(_world_opt.selected)), _day_chk.button_pressed)
			if not bool(r.get("ok", false)):
				dev._say(str(r.get("msg", r.get("error", "")))))
	r1.add_child(_go)
	_bar = ProgressBar.new()
	_bar.custom_minimum_size = Vector2(598, 14)
	_bar.show_percentage = false
	v.add_child(_bar)
	_lab = UI.small("", UI.TXT)
	_lab.clip_text = true
	_lab.custom_minimum_size = Vector2(598, 0)
	v.add_child(_lab)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(598, 150)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(sc)
	_grid = GridContainer.new()
	_grid.columns = 4
	_grid.add_theme_constant_override("h_separation", 4)
	_grid.add_theme_constant_override("v_separation", 4)
	sc.add_child(_grid)
	var r3 := HBoxContainer.new()
	r3.add_theme_constant_override("separation", 6)
	v.add_child(r3)
	var bh := Button.new()
	bh.text = T.t("Übersicht öffnen (HTML)")
	bh.pressed.connect(func():
		write_index()
		OS.shell_open(ProjectSettings.globalize_path(DIR + "/index.html")))
	r3.add_child(bh)
	var bo := Button.new()
	bo.text = T.t("Ordner öffnen")
	bo.pressed.connect(func(): x.open_folder(DIR))
	r3.add_child(bo)
	_path = LineEdit.new()
	_path.editable = false
	_path.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_path.text = ProjectSettings.globalize_path(DIR)
	r3.add_child(_path)
	_paint()


func on_show(tab: String) -> void:
	if tab == "kontakt":
		_grid_dirty = true
		_paint()


func _paint() -> void:
	if _go == null:
		return
	_go.text = T.t("Abbrechen") if running else T.t("Alle Orte fotografieren")
	_world_opt.disabled = running
	var n := queue.size()
	_bar.max_value = maxf(1.0, float(n))
	_bar.value = float(done.size())
	if running:
		var nm := cur
		for e in queue:
			if str(e["id"]) == cur:
				nm = T.t(str(e["name"]))
		_lab.text = "%d / %d · %s" % [done.size(), n, nm]
	elif n > 0:
		var ok_n := done.filter(func(i): return bool(i["ok"])).size()
		_lab.text = T.t("Fertig: %d Fotos von %d Orten (%.0f s)") % [ok_n, n, t_end - t0] if not _cancel else T.t("Abgebrochen nach %d von %d Orten") % [done.size(), n]
	else:
		var w := str(_world_opt.get_item_metadata(_world_opt.selected))
		var cnt: int = Dev.alle_orte(main).filter(func(e): return w == "" or str(e["world"]) == w).size()
		_lab.text = T.t("%d Orte · Foto 640 × 360 · user://kontaktbogen/<welt>/<id>.jpg") % cnt


func _process(_dt: float) -> void:
	if _grid == null or not _grid.is_visible_in_tree():
		return
	if running:
		_paint()
	if _grid_dirty:
		_grid_dirty = false
		_fill_grid()


func _fill_grid() -> void:
	for c in _grid.get_children():
		c.queue_free()
	var w := str(_world_opt.get_item_metadata(_world_opt.selected)) if _world_opt != null else ""
	var L: Array = done.filter(func(i): return bool(i["ok"])) if running or not done.is_empty() else list_files(w)
	for i in L.slice(maxi(0, L.size() - 48)):
		var img := Image.load_from_file(ProjectSettings.globalize_path(DIR + "/" + str(i["file"])))
		if img == null or img.is_empty():
			continue
		img.resize(142, 80, Image.INTERPOLATE_BILINEAR)
		var b := TextureButton.new()
		b.texture_normal = ImageTexture.create_from_image(img)
		b.tooltip_text = "%s · %s" % [T.t(str(i["name"])), str(i["id"])]
		b.custom_minimum_size = Vector2(142, 80)
		var id := str(i["id"])
		b.pressed.connect(func(): dev.goto(id))
		_grid.add_child(b)


# =============================================================================================================================
# /control
# =============================================================================================================================
func control(d: Dictionary) -> Dictionary:
	match str(d.get("do", "")):
		"contact":
			if running:
				return state()
			var ids: Array = d.get("ids", []) if d.get("ids", []) is Array else []
			return start(str(d.get("world", d.get("value", ""))), bool(d.get("day", true)), ids, int(d.get("limit", 0)))
		"contact_stop":
			stop()
			return state()
		"contact_list":
			var L := list_files(str(d.get("world", "")))
			return {"ok": true, "n": L.size(), "pictures": L, "index": "/dev/kontakt/index.html", "dir": ProjectSettings.globalize_path(DIR)}
	return state()
