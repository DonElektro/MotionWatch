extends Node
## «Entdecken belohnen» (Erlebniswelt Punkt 20–23, Daniel 31.10.2026, Stil «dezent»): ein System für ALLE Szenen.
##   * Szenen und Vignetten melden ihre Entdeckungen mit register() an (Ort, Szene, Tier, Mensch).
##   * Gefunden ist etwas, wenn die Ansicht (frei fliegen, Erkunden, Spielen am PC) näher als «radius» kommt, es im Bild ist
##     und nichts davor steht (Sichtlinie) – oder, bei photo_required, wenn MoveEyes Kopfkamera es ganz im Bild hat und ein
##     Foto gemacht wird (📷 im Simulator oder «Foto für Entdeckungsbuch» in MoveEye).
##   * Entdeckungsbuch (Spiel → Entdecken): «2 von 3 entdeckt», kleines Bild, Titel, kurzer Text; nicht Gefundenes als «???»
##     mit Art und Zeit-Symbol (Nacht / Regen / Morgen …).
##   * Blinki-Hinweis: wenn man N Minuten (Standard 5) nichts Neues gefunden hat, ein kleiner, wegklickbarer Hinweis auf das
##     nächste Ungefundene, das JETZT möglich ist (Tageszeit, Wetter).
##   * gespeichert pro Szene in user://entdecken.json (A6: das ist Spielstand 1; Platz 2/3 unter user://spielstand/<n>/), Bilder in user://entdecken/<szene>/<id>.jpg
## API (Doku mit Beispiel: REAL_ENTDECKEN.md): main.entdecken.register(id, info) · mark_found(id, how) · is_found(id) ·
## count(scene) · total(scene) · Signal found(id). Lite: _lite() -> kleinere Bilder, seltener prüfen.

signal found(id: String)

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Icons = preload("res://scripts/mehr_icons.gd")
const Sym = preload("res://scripts/symbole.gd")
const Tour = preload("res://scripts/tour.gd")
const Quality = preload("res://scripts/quality.gd")   # 3D-4.27: Lite (Raspberry Pi) from the one central switch

const SAVE := "user://entdecken.json"
const PIC_DIR := "user://entdecken"
const KINDS := ["ort", "szene", "tier", "mensch"]
const WHENS := ["any", "day", "night", "morning", "evening", "rain", "dry", "snow", "fog"]
# the hint category in the book («???» – ein Ort …) and the symbol for the time / weather
const KIND_NAME := {"ort": "ein Ort", "szene": "eine Szene", "tier": "ein Tier", "mensch": "ein Mensch"}
const WHEN_SYM := {"night": "moon", "rain": "rain", "morning": "dawn", "evening": "dawn", "day": "sun", "snow": "snow", "fog": "cloud"}
const WHEN_EMOJI := {"night": "🌙", "rain": "🌧", "morning": "🌅", "evening": "🌇", "day": "☀", "snow": "❄", "fog": "🌫", "dry": "", "any": ""}
const WHEN_NAME := {"night": "nur nachts", "rain": "nur bei Regen", "morning": "nur am Morgen", "evening": "nur am Abend", "day": "nur am Tag",
		"snow": "nur bei Schnee", "fog": "nur bei Nebel", "dry": "nur wenn es trocken ist"}
const THUMB := Vector2i(192, 108)          # 16:9 like the cameras
const SEEN_S := 0.5                        # in view this long = found (no «found» while flying past)
const PHOTO_MIN_PX := 22.0                 # the thing must be at least this wide in the picture of the head camera (960 px)

var main
var items := {}                            # id -> the registration (live, this scene)
var data := {"v": 1, "scenes": {}}         # saved: scene -> {"found": {id: {t, how, title, pic}}, "known": {id: {title, kind, when, photo, short}}}
var hints_on := true                       # setting «Blinki-Hinweise» (saved here)
var hint_min := 5.0                        # minutes without anything new before a hint
var last_new_t := 0.0                      # time (main.now) of the last find or of the scene start
var last_hint_t := -1000.0
var hint_id := ""                          # the item of the hint shown now
var photo_id := ""                         # the item the head camera has in the picture now ('' = none)
var photo_rect := Rect2()                  # its box in the picture of the head camera (px of 960 × 540)
var demo_on := true                        # the three demo discoveries of «Camping-Platz»
var _seen := {}                            # id -> seconds in view
var _t := 0.0
var _dirty := false
var _save_t := 0.0
var _busy_photo := false
var _thumb_vp: SubViewport
var _thumb_cam: Camera3D
var _layer: CanvasLayer
var _hint_box: PanelContainer
var _hint_l: Label
var _hint_bk: Control
var _hint_t := 0.0
var _hint_x: Button = null
var _photo_chip: Button
var _found_box: PanelContainer
var _found_pic: TextureRect
var _found_l: Label
var _found_t := 0.0
var _book_list: VBoxContainer = null
var _demo_nodes: Array = []
var _demo_glow: Node3D = null
var _tex_cache := {}                       # pic path -> ImageTexture
var save_path := SAVE                      # A6: the file of the active Spielstand (spielstand.gd; place 1 = SAVE)
var check_us := 0.0                        # how long one check of all items took (µs, smoothed) - for the report / tests


func _lite() -> bool:
	"""the «Lite» graphics (Raspberry Pi): smaller pictures, fewer checks (quality.gd, set by main.lite_update)"""
	return Quality.lite()


# =============================================================================================================================
# ---- the API ----------------------------------------------------------------------------------------------------------------
# =============================================================================================================================
func register(id: String, info: Dictionary) -> bool:
	"""announce a discovery. id: unique over all scenes (e.g. "see.steg_quietschen"). info (all optional except title):
	  scene        the scene id (default: the scene being built now, main.scene)
	  title        «Quietschender Steg»
	  short_text   one or two sentences for the book (shown when found)
	  hint         Blinki's hint («Hörst du das Quietschen beim Steg?»); empty = a hint by direction and distance
	  icon         an emoji for MoveEye's page (the window draws the symbol of the kind)
	  position     Vector3 in the world (where it is; centre of the thing)
	  node         Node3D (optional): the position follows it (moving things); position is then an offset to it
	  size         Vector3 of the box around it (default 1 × 1 × 1) - for the photo: the whole box must be in the picture
	  radius       metres: so near the view must come (default 6); for photos the head camera may be up to max(radius, 25) m away
	  when         "any" | "day" | "night" | "morning" | "evening" | "rain" | "dry" | "snow" | "fog" or an Array (all must hold)
	  kind         "ort" | "szene" | "tier" | "mensch"
	  photo_required  true = only a photo with the head camera of MoveEye counts
	  active       Callable -> bool (optional): only now possible (e.g. while the fox is at the bin)
	  los          false = no line of sight needed (e.g. a sound you hear)
	  demo         true = a demo entry (shown with «Demo»)
	Registering the same id again replaces it (the scene is built again). Returns false for a bad id."""
	if id.strip_edges() == "":
		return false
	var sc := str(info.get("scene", main.scene if main != null else ""))
	var w = info.get("when", "any")
	var wl: Array = w if typeof(w) == TYPE_ARRAY else [str(w)]
	wl = wl.filter(func(x): return str(x) in WHENS and str(x) != "any")
	var k := str(info.get("kind", "ort"))
	if not k in KINDS:
		k = "ort"
	var it := {"id": id, "scene": sc, "title": str(info.get("title", id)), "short": str(info.get("short_text", "")), "hint": str(info.get("hint", "")),
			"icon": str(info.get("icon", "")), "pos": info.get("position", Vector3.ZERO) as Vector3, "node": info.get("node", null),
			"size": info.get("size", Vector3.ONE) as Vector3, "radius": maxf(0.5, float(info.get("radius", 6.0))), "when": wl, "kind": k,
			"photo": bool(info.get("photo_required", false)), "active": info.get("active", null), "los": bool(info.get("los", true)),
			"demo": bool(info.get("demo", false)), "order": items.size()}
	items[id] = it
	var S := _scene(sc)
	var kn := {"title": it.title, "kind": k, "when": wl, "photo": it.photo, "short": it.short, "icon": it.icon, "demo": it.demo}
	if JSON.stringify(S["known"].get(id, {})) != JSON.stringify(kn):
		S["known"][id] = kn
		_dirty = true
	return true


func unregister(id: String) -> void:
	"""takes the live entry away (the book keeps it as known for its scene)"""
	items.erase(id)
	_seen.erase(id)


func forget(id: String) -> void:
	"""gone for good: live entry, «known» and «found» of every scene (an entry renamed or taken out of a scene)"""
	unregister(id)
	for sc in data["scenes"]:
		var S: Dictionary = data["scenes"][sc]
		S["known"].erase(id)
		var f: Dictionary = S["found"].get(id, {})
		if str(f.get("pic", "")) != "" and FileAccess.file_exists(str(f["pic"])):
			DirAccess.remove_absolute(str(f["pic"]))
		S["found"].erase(id)
	_dirty = true
	_save_t = 0.0
	_refresh_book()


func mark_found(id: String, how := "api") -> bool:
	"""found! how: "view" (seen while walking / flying), "photo" (head camera), "api" (a vignette decides itself, e.g. the
	angler fell into the water while you watched). A picture is made from the current view (photo: from the head camera).
	Returns false if it was found before or is unknown."""
	var it: Dictionary = items.get(id, {})
	var sc: String = str(it.get("scene", main.scene))
	var S := _scene(sc)
	if S["found"].has(id) or (it.is_empty() and not S["known"].has(id)):
		return false
	S["found"][id] = {"t": int(Time.get_unix_time_from_system()), "how": how, "title": str(it.get("title", S["known"].get(id, {}).get("title", id))), "pic": ""}
	_dirty = true
	_save_t = 0.0
	last_new_t = main.now()
	if hint_id == id:
		hide_hint()
	if how != "photo":
		_make_thumb(id)                          # async: the picture comes a moment later
	found.emit(id)
	_show_found(id)
	if main.mehr != null and main.mehr.protokoll != null:
		main.mehr.protokoll.add("info", T.t("Entdeckt: %s (%d von %d)", [str(S["found"][id]["title"]), count(sc), total(sc)]))
	return true


func is_found(id: String) -> bool:
	for sc in data["scenes"]:
		if data["scenes"][sc]["found"].has(id):
			return true
	return false


func count(scene := "") -> int:
	"""how many of the scene are found (default: this scene)"""
	return (_scene(scene if scene != "" else main.scene)["found"] as Dictionary).size()


func total(scene := "") -> int:
	"""how many the scene has (all ever registered there)"""
	return (_scene(scene if scene != "" else main.scene)["known"] as Dictionary).size()


func possible_now(id: String) -> bool:
	"""time, weather and the own condition of the vignette allow it now"""
	var it: Dictionary = items.get(id, {})
	if it.is_empty():
		return false
	if not when_ok(it.when):
		return false
	var a = it.get("active", null)
	if a is Callable and (a as Callable).is_valid():
		return bool((a as Callable).call())
	return true


func when_ok(w) -> bool:
	"""the conditions of «when» against the clock and the weather of the simulator"""
	var wl: Array = w if typeof(w) == TYPE_ARRAY else [str(w)]
	var h: float = main.hour()
	for c in wl:
		match str(c):
			"night":
				if not main.is_dark():
					return false
			"day":
				if main.is_dark():
					return false
			"morning":
				if h < 5.0 or h >= 10.0:
					return false
			"evening":
				if h < 17.5 or h >= 22.0:
					return false
			"rain":
				if main.weather != "rain":
					return false
			"dry":
				if main.weather in ["rain", "snow"]:
					return false
			"snow", "fog":
				if main.weather != str(c):
					return false
	return true


func list(scene := "") -> Array:
	"""the entries of a scene for the book and for MoveEye: [{id, title, short, kind, when, photo, found, how, t, pic, possible}]"""
	var sc: String = scene if scene != "" else main.scene
	var S := _scene(sc)
	var out := []
	var ids: Array = S["known"].keys()
	ids.sort_custom(func(a, b): return int(items.get(a, {}).get("order", 999)) < int(items.get(b, {}).get("order", 999)))
	for id in ids:
		var kn: Dictionary = S["known"][id]
		var f: Dictionary = S["found"].get(id, {})
		out.append({"id": id, "title": str(kn.get("title", id)), "short": str(kn.get("short", "")), "kind": str(kn.get("kind", "ort")),
				"when": kn.get("when", []), "photo": bool(kn.get("photo", false)), "icon": str(kn.get("icon", "")), "demo": bool(kn.get("demo", false)),
				"found": not f.is_empty(), "how": str(f.get("how", "")), "t": int(f.get("t", 0)), "pic": str(f.get("pic", "")),
				"possible": items.has(id) and possible_now(id)})
	return out


func reset(scene := "") -> void:
	"""forget what was found (one scene, or all with "*") - for tests and «Neu anfangen»"""
	var scs: Array = data["scenes"].keys() if scene == "*" else [scene if scene != "" else main.scene]
	for sc in scs:
		var S := _scene(sc)
		for id in S["found"]:
			var p := str(S["found"][id].get("pic", ""))
			if p != "" and FileAccess.file_exists(p):
				DirAccess.remove_absolute(p)
		S["found"] = {}
	_tex_cache.clear()
	_dirty = true
	_save_t = 0.0
	last_new_t = main.now()
	_refresh_book()


# ---- called by main.gd ---------------------------------------------------------------------------------------------------
func begin_scene(_sc: String) -> void:
	"""main._build_scene, BEFORE scenes.build: the live entries of the old scene go (the new scene registers its own)"""
	items.clear()
	_seen.clear()
	photo_id = ""
	hide_hint()
	_demo_nodes.clear()
	_demo_glow = null
	last_new_t = main.now() if main != null else 0.0


func on_scene() -> void:
	"""main._build_scene, AFTER scenes.build: the demo set of «Camping-Platz»"""
	if main.scene == "camping" and demo_on:
		_demo_camping()
	_refresh_book()


# =============================================================================================================================
func _ready() -> void:
	save_path = preload("res://scripts/spielstand.gd").path_ent()   # A6
	_load()
	_thumb_vp = SubViewport.new()
	_thumb_vp.size = THUMB
	_thumb_vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	_thumb_vp.msaa_3d = Viewport.MSAA_DISABLED
	add_child(_thumb_vp)
	_thumb_cam = Camera3D.new()
	_thumb_cam.fov = 55.0
	_thumb_cam.near = 0.1
	_thumb_cam.far = 600.0
	_thumb_cam.cull_mask = 1                    # like the cameras of MoveEye: no helper marks, no thermal layer
	_thumb_cam.attributes = CameraAttributesPractical.new()
	_thumb_vp.add_child(_thumb_cam)
	_layer = CanvasLayer.new()
	_layer.layer = 58                            # above the panel, below the windows of «Mehr» (60) and the tour (63)
	add_child(_layer)
	_build_hint()
	_build_photo_chip()
	_build_found()
	last_new_t = main.now()
	call_deferred("_late")


func _late() -> void:
	if main.mehr != null and main.mehr.farben != null:
		for c in [_hint_box, _photo_chip, _found_box]:
			main.mehr.farben.register(c, "all")


func _scene(sc: String) -> Dictionary:
	if not data["scenes"].has(sc):
		data["scenes"][sc] = {"found": {}, "known": {}}
	var S: Dictionary = data["scenes"][sc]
	if not S.has("found"):
		S["found"] = {}
	if not S.has("known"):
		S["known"] = {}
	return S


func _load() -> void:
	if not FileAccess.file_exists(save_path):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(save_path))
	if typeof(d) != TYPE_DICTIONARY:
		return
	if typeof(d.get("scenes", null)) == TYPE_DICTIONARY:
		data["scenes"] = d["scenes"]
	hints_on = bool(d.get("hints_on", true))
	hint_min = clampf(float(d.get("hint_min", 5.0)), 1.0, 60.0)
	demo_on = bool(d.get("demo_on", true))


func save() -> void:
	_dirty = false
	var d := {"v": 1, "scenes": data["scenes"], "hints_on": hints_on, "hint_min": hint_min, "demo_on": demo_on}
	DirAccess.make_dir_recursive_absolute(save_path.get_base_dir())
	var f := FileAccess.open(save_path, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))
		f.close()


func use_file(path: String) -> void:
	"""A6 Spielstand: another place - its «found» lists; what exists («known») and the hint settings stay (they are the same
	for everybody on this PC)"""
	var known := {}
	for sc in data["scenes"]:
		known[sc] = (data["scenes"][sc] as Dictionary).get("known", {})
	var keep := [hints_on, hint_min, demo_on]
	save_path = path
	data = {"v": 1, "scenes": {}}
	_load()
	hints_on = keep[0]
	hint_min = keep[1]
	demo_on = keep[2]
	for sc in known:
		var S := _scene(sc)
		for id in known[sc]:
			S["known"][id] = known[sc][id]
	_tex_cache.clear()
	last_new_t = main.now() if main != null else 0.0
	_dirty = true
	_save_t = 0.0
	_refresh_book()


func set_hints(on: bool) -> void:
	hints_on = on
	if not on:
		hide_hint()
	_dirty = true


func set_hint_min(v: float) -> void:
	hint_min = clampf(v, 1.0, 60.0)
	_dirty = true


# =============================================================================================================================
# ---- found by looking, the photo of the head camera, the hint -----------------------------------------------------------
# =============================================================================================================================
func _pos(it: Dictionary) -> Vector3:
	var n = it.get("node", null)
	if n is Node3D and is_instance_valid(n) and (n as Node3D).is_inside_tree():
		return (n as Node3D).global_position + (it.pos as Vector3)
	return it.pos


func _los(a: Vector3, b: Vector3) -> bool:
	"""nothing in between (main.gd line_blocker: objects with their height, hills) - the thing the item stands in does not count"""
	var o: Dictionary = main.line_blocker(a, b)
	if o.is_empty():
		return true
	if bool(o.get("terrain", false)):
		return false
	var cl: Array = main._ob_closest(o, Vector2(b.x, b.z))
	return float(cl[1]) < 0.6


func _quiet() -> bool:
	"""automatic runs: nobody is discovering anything (test run, test bench, spectator camera, replay, pictures)"""
	if main.spectate or main.measuring():
		return true
	if main.testrun != null and main.testrun.running:
		return true
	if main.pruef != null and main.pruef.get("running") == true:
		return true
	if main.dataset != null and main.dataset.servo != null:
		return true
	return false


func _process(dt: float) -> void:
	if main == null or not main.is_processing():
		return
	if _dirty:
		_save_t -= dt
		if _save_t <= 0.0:
			_save_t = 2.0
			save()
	if _hint_t > 0.0:
		_hint_t -= dt
		if _hint_t <= 0.0:
			hide_hint()
	if _found_t > 0.0:
		_found_t -= dt
		if _found_t <= 0.0:
			_found_box.visible = false
	if _demo_glow != null and is_instance_valid(_demo_glow):
		_demo_glow.visible = main.is_dark()
	var step := 0.5 if _lite() else 0.25
	_t += dt
	if _t < step:
		return
	var el := _t
	_t = 0.0
	if items.is_empty():
		_set_photo("")
		return
	var t_us := Time.get_ticks_usec()
	var quiet := _quiet()
	var cam := get_viewport().get_camera_3d()
	var best_photo := ""
	var best_d := 1e9
	for id in items:
		var it: Dictionary = items[id]
		if is_found(id) or not possible_now(id):
			_seen.erase(id)
			continue
		var p := _pos(it)
		if it.photo:
			var r := _in_head_cam(it, p)
			if r.size.x > 0.0:
				var dd: float = main.cams[0].global_position.distance_to(p)
				if dd < best_d:
					best_d = dd
					best_photo = id
					photo_rect = r
			continue
		if quiet or cam == null or not main.win_open:
			continue
		var cp := cam.global_position
		var ok: bool = cp.distance_to(p) <= float(it.radius) and cam.is_position_in_frustum(p) and (not it.los or _los(cp, p))
		if ok:
			_seen[id] = float(_seen.get(id, 0.0)) + el
			if float(_seen[id]) >= SEEN_S:
				mark_found(id, "view")
		else:
			_seen.erase(id)
	_set_photo(best_photo)
	_hint_tick()
	check_us = lerpf(check_us, float(Time.get_ticks_usec() - t_us), 0.2)


func _in_head_cam(it: Dictionary, p: Vector3) -> Rect2:
	"""the box of the thing in the picture of the head camera (960 × 540) if it is whole inside, near enough, not hidden;
	else an empty Rect2"""
	if main.cams.is_empty() or main.sabotage_cover:
		return Rect2()
	var c: Camera3D = main.cams[0]
	var cp := c.global_position
	if cp.distance_to(p) > maxf(float(it.radius), 25.0):
		return Rect2()
	var hs: Vector3 = (it.size as Vector3) * 0.5
	var vs := Vector2(main.CAM_W[0], main.CAM_H[0])
	var lo := Vector2(1e9, 1e9)
	var hi := Vector2(-1e9, -1e9)
	for sx in [-1, 1]:
		for sy in [-1, 1]:
			for sz in [-1, 1]:
				var q := p + Vector3(hs.x * sx, hs.y * sy, hs.z * sz)
				if c.is_position_behind(q):
					return Rect2()
				var s := c.unproject_position(q)
				lo = Vector2(minf(lo.x, s.x), minf(lo.y, s.y))
				hi = Vector2(maxf(hi.x, s.x), maxf(hi.y, s.y))
	if lo.x < 0.0 or lo.y < 0.0 or hi.x > vs.x or hi.y > vs.y:
		return Rect2()                               # not whole in the picture
	if hi.x - lo.x < PHOTO_MIN_PX:
		return Rect2()                               # too far / too small
	if it.los and not _los(cp, p):
		return Rect2()                               # something stands in front
	return Rect2(lo, hi - lo)


func _set_photo(id: String) -> void:
	photo_id = id
	if _photo_chip != null:
		_photo_chip.visible = id != "" and not _busy_photo
		if _photo_chip.visible:
			_place_chip()


func take_photo() -> Dictionary:
	"""the shutter: is a «photo» discovery whole in the picture of the head camera? -> the picture of the camera, found"""
	if _busy_photo:
		return {"ok": false, "error": "busy"}
	var id := photo_id
	if id == "":
		_say_small(T.t("Nichts Besonderes im Bild der Kamera."))
		return {"ok": true, "found": false, "id": ""}
	var r := photo_rect
	_busy_photo = true
	_set_photo(id)
	_photo_pic(id, r)
	return {"ok": true, "found": true, "id": id, "title": str(items[id].title)}


func _photo_pic(id: String, r: Rect2) -> void:
	var n0: int = main.frame_no[0]
	main.want_snapshot(0)
	var t0: float = main.now()
	while main.frame_no[0] == n0 and main.now() - t0 < 2.0:
		await get_tree().process_frame
	var jb: PackedByteArray = main.latest_jpg(0)
	if mark_found(id, "photo") and not jb.is_empty():
		var img := Image.new()
		if img.load_jpg_from_buffer(jb) == OK:
			var c := r.get_center()                  # cut around the thing (16:9, with room around it)
			var w := clampf(maxf(r.size.x * 2.4, r.size.y * 2.4 * 16.0 / 9.0), 160.0, float(img.get_width()))
			var h := w * 9.0 / 16.0
			var x0 := clampf(c.x - w / 2.0, 0.0, img.get_width() - w)
			var y0 := clampf(c.y - h / 2.0, 0.0, maxf(0.0, img.get_height() - h))
			var cut := img.get_region(Rect2i(int(x0), int(y0), int(w), int(minf(h, img.get_height()))))
			_store_pic(id, cut)
	_busy_photo = false


func _make_thumb(id: String) -> void:
	"""a small picture of the place from the current view (own small camera, aimed at the thing)"""
	var it: Dictionary = items.get(id, {})
	var cam := get_viewport().get_camera_3d()
	if it.is_empty() or cam == null:
		return
	var p := _pos(it)
	var from := cam.global_position
	if from.distance_to(p) > float(it.radius) * 3.0 or from.distance_to(p) < 0.3:
		from = p + (from - p).normalized() * minf(float(it.radius), 6.0) if from.distance_to(p) > 0.3 else p + Vector3(0, 1.5, 3.0)
	_thumb_vp.size = Vector2i(128, 72) if _lite() else THUMB
	_thumb_cam.global_position = from
	if absf((p - from).normalized().y) < 0.98:
		_thumb_cam.look_at(p, Vector3.UP)
	_thumb_cam.fov = clampf(rad_to_deg(2.0 * atan2(maxf((it.size as Vector3).length(), 1.0) * 1.4, from.distance_to(p))), 25.0, 70.0)
	var dark: bool = main.is_dark()
	(_thumb_cam.attributes as CameraAttributesPractical).exposure_multiplier = 6.0 if dark else 1.0   # the book: night pictures a little lighter
	_thumb_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	var img := _thumb_vp.get_texture().get_image()
	if img == null or img.is_empty():
		return
	if dark:                                         # the night is drawn dark (like a camera): a little lighter for the book
		img.convert(Image.FORMAT_RGB8)
		img.adjust_bcs(1.8, 1.1, 0.9)
	_store_pic(id, img)


func _store_pic(id: String, img: Image) -> void:
	var sc := str(items.get(id, {}).get("scene", main.scene))
	var S := _scene(sc)
	if not S["found"].has(id):
		return
	var sz := Vector2i(128, 72) if _lite() else THUMB
	if img.get_size() != sz:
		img.resize(sz.x, sz.y, Image.INTERPOLATE_BILINEAR)
	var dir := "%s/%s" % [PIC_DIR, sc.validate_filename()]
	DirAccess.make_dir_recursive_absolute(dir)
	var p := "%s/%s.jpg" % [dir, id.validate_filename()]
	img.save_jpg(p, 0.82)
	S["found"][id]["pic"] = p
	_tex_cache.erase(p)
	_dirty = true
	if _found_box.visible and _found_box.get_meta("id", "") == id:
		_found_pic.texture = _tex(p)
	_refresh_book()


func pic_bytes(scene: String, i: int) -> PackedByteArray:
	"""for /disc_pic/<i>.jpg (MoveEye's page): the picture of entry i of the list of the scene"""
	var L := list(scene)
	if i < 0 or i >= L.size():
		return PackedByteArray()
	var p := str(L[i].pic)
	if p == "" or not FileAccess.file_exists(p):
		return PackedByteArray()
	return FileAccess.get_file_as_bytes(p)


func _tex(p: String) -> Texture2D:
	if p == "" or not FileAccess.file_exists(p):
		return null
	if not _tex_cache.has(p):
		var img := Image.load_from_file(p)
		_tex_cache[p] = ImageTexture.create_from_image(img) if img != null else null
	return _tex_cache[p]


# ---- Blinki's hint -----------------------------------------------------------------------------------------------------------
func _hint_tick() -> void:
	if not hints_on or _hint_box.visible or _quiet() or not main.win_open or main.kids_on:
		return
	if main.mehr != null and main.mehr.tour != null and main.mehr.tour.active:
		return
	if main.game != null and main.game.open:
		return
	var wait := hint_min * 60.0
	if main.now() - last_new_t < wait or main.now() - last_hint_t < wait:
		return
	show_hint()


func nearest_possible() -> String:
	var cam := get_viewport().get_camera_3d()
	var at: Vector3 = cam.global_position if cam != null else Vector3.ZERO
	var best := ""
	var bd := 1e9
	for id in items:
		if is_found(id) or not possible_now(id):
			continue
		var d := at.distance_to(_pos(items[id]))
		if d < bd:
			bd = d
			best = id
	return best


func hint_text(id: String) -> String:
	var it: Dictionary = items.get(id, {})
	if it.is_empty():
		return ""
	if str(it.hint) != "":
		return T.t(str(it.hint))
	var cam := get_viewport().get_camera_3d()
	var p := _pos(it)
	var dir := T.t("in der Nähe")
	var dist := 0.0
	if cam != null:
		var v := p - cam.global_position
		dist = Vector2(v.x, v.z).length()
		var fw := -cam.global_transform.basis.z
		var a := rad_to_deg(Vector2(fw.x, fw.z).angle_to(Vector2(v.x, v.z)))
		dir = T.t("vor dir") if absf(a) < 40.0 else (T.t("hinter dir") if absf(a) > 130.0 else (T.t("rechts von dir") if a > 0.0 else T.t("links von dir")))
	var far := T.t(", etwa %d m", [int(round(dist / 5.0) * 5.0)]) if dist > 8.0 else ""
	if it.photo:
		return T.t("Da gibt es etwas für MoveEyes Kamera – %s%s. Dreh den Kopf und mach ein Foto.", [dir, far])
	return T.t("Schau dich mal um – %s%s gibt es noch etwas zu entdecken.", [dir, far])


func show_hint(id := "") -> bool:
	if id == "":
		id = nearest_possible()
	if id == "":
		return false
	hint_id = id
	last_hint_t = main.now()
	_hint_l.text = hint_text(id)
	_hint_box.visible = true
	_hint_box.reset_size()
	_place_hint()
	if _hint_bk.has_method("hop"):
		_hint_bk.hop()
	_hint_t = 14.0
	return true


func hide_hint() -> void:
	if _hint_box != null:
		_hint_box.visible = false
	hint_id = ""
	_hint_t = 0.0


func _right_edge() -> float:
	var vs := get_viewport().get_visible_rect().size
	return vs.x - (main.ui_root.size.x if main.ui_root != null and main.ui_root.visible else 0.0)


func _place_hint() -> void:
	if _hint_box.has_meta("fenster"):                   # in the window frame (fenster.gd): the frame places it
		return
	var vs := get_viewport().get_visible_rect().size
	_hint_box.position = Vector2(16.0, vs.y - _hint_box.size.y - 96.0)


func _place_chip() -> void:
	_photo_chip.reset_size()
	_photo_chip.position = Vector2(maxf(8.0, (_right_edge() - _photo_chip.size.x) / 2.0), 52.0)


# ---- the small things on the screen (dezent: small, dark, no speech bubbles) -------------------------------------------------
func _build_hint() -> void:
	_hint_box = PanelContainer.new()
	_hint_box.theme = UI.theme()
	_hint_box.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.9), Color(1, 1, 1, 0.10), 12, 8, 1))
	_hint_box.visible = false
	_layer.add_child(_hint_box)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	_hint_box.add_child(h)
	_hint_bk = Tour.BlinkiView.new()
	_hint_bk.custom_minimum_size = Vector2(28, 32)
	_hint_bk.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(_hint_bk)
	_hint_l = Label.new()
	_hint_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hint_l.custom_minimum_size = Vector2(260, 0)
	_hint_l.add_theme_font_size_override("font_size", 13)
	_hint_l.add_theme_color_override("font_color", UI.TXT)
	_hint_l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(_hint_l)
	var x := Button.new()
	x.flat = true
	x.text = "✕"
	x.tooltip_text = T.t("Hinweis schliessen (Blinki-Hinweise ausschalten: Spiel → Entdecken)")
	x.focus_mode = Control.FOCUS_NONE
	x.add_theme_color_override("font_color", UI.MUT)
	x.pressed.connect(hide_hint)
	x.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	h.add_child(x)
	_hint_x = x


func join_fenster(f) -> void:
	"""3D-4.27: the Blinki hint in the common window frame (fenster.gd): drag, snap, remembered place. Its «✕» = the frame's;
	the check box in «Fenster» is the setting «Blinki-Hinweise» (the same switch as Spiel → Entdecken, no second one)"""
	if f == null or _hint_box == null:
		return
	f.add("blinki", "Blinki-Hinweis", _hint_box, {"hide": [_hint_x], "hint": "wenn man lange nichts findet",
			"home": func(w): return Vector2(16.0, f.view_size().y - w.size.y - 96.0),
			"on": func(): return hints_on, "set_on": func(v): set_hints(bool(v))})


func _build_photo_chip() -> void:
	_photo_chip = Button.new()
	_photo_chip.theme = UI.theme()
	_photo_chip.icon = Sym.tex("camera", 16, UI.TXT)
	_photo_chip.text = T.t("Foto fürs Buch")
	_photo_chip.tooltip_text = T.t("MoveEyes Kamera hat etwas Besonderes im Bild – Foto fürs Entdeckungsbuch")
	_photo_chip.focus_mode = Control.FOCUS_NONE
	_photo_chip.add_theme_font_size_override("font_size", 13)
	for s in ["normal", "hover", "pressed"]:
		_photo_chip.add_theme_stylebox_override(s, UI.box(Color(UI.PANEL, 0.82 if s == "normal" else 0.95), UI.ORG if s != "normal" else Color(1, 1, 1, 0.16), 14, 6, 1))
	_photo_chip.visible = false
	_photo_chip.pressed.connect(func(): take_photo())
	_layer.add_child(_photo_chip)


func _build_found() -> void:
	_found_box = PanelContainer.new()
	_found_box.theme = UI.theme()
	_found_box.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.92), Color(1, 1, 1, 0.12), 12, 8, 1))
	_found_box.mouse_filter = Control.MOUSE_FILTER_STOP
	_found_box.visible = false
	_found_box.gui_input.connect(func(e):
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			open_book())
	_layer.add_child(_found_box)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 10)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_found_box.add_child(h)
	_found_pic = TextureRect.new()
	_found_pic.custom_minimum_size = Vector2(80, 45)
	_found_pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_found_pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_found_pic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(_found_pic)
	_found_l = Label.new()
	_found_l.add_theme_font_size_override("font_size", 13)
	_found_l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_found_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(_found_l)


func _show_found(id: String) -> void:
	var sc := str(items.get(id, {}).get("scene", main.scene))
	var S := _scene(sc)
	_found_l.text = T.t("Entdeckt: %s", [str(S["found"][id]["title"])]) + "\n" + T.t("%d von %d entdeckt", [count(sc), total(sc)])
	_found_pic.texture = _tex(str(S["found"][id].get("pic", "")))
	_found_box.set_meta("id", id)
	_found_box.visible = true
	_found_box.reset_size()
	var vs := get_viewport().get_visible_rect().size
	_found_box.position = Vector2(maxf(8.0, (_right_edge() - _found_box.size.x) / 2.0), vs.y - _found_box.size.y - 96.0)
	_found_t = 5.0
	_refresh_book()


func _say_small(t: String) -> void:
	if main.mehr != null:
		main.mehr.toast(t)


# =============================================================================================================================
# ---- the book (a window of «Mehr»: the same look as every window there) -------------------------------------------------
# =============================================================================================================================
func open_book() -> void:
	if main.mehr == null:
		return
	main.mehr.close_menu()
	var b: VBoxContainer = main.mehr._window(T.t("Entdeckungsbuch"), "book")
	main.mehr.win_id = "book"
	var top := UI.small("", UI.TXT)
	top.add_theme_font_size_override("font_size", 14)
	top.set_meta("count", true)
	b.add_child(top)
	var bar := ProgressBar.new()
	bar.show_percentage = false
	bar.custom_minimum_size = Vector2(560, 6)
	b.add_child(bar)
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	var rows := int(ceil(list().size() / 2.0))           # as high as needed, at most what the window allows
	sc.custom_minimum_size = Vector2(580, clampf(rows * 120.0 + 240.0, 240.0, minf(460.0, get_viewport().get_visible_rect().size.y - 260.0)))
	b.add_child(sc)
	_book_list = VBoxContainer.new()
	_book_list.add_theme_constant_override("separation", 8)
	_book_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_book_list.set_meta("top", top)
	_book_list.set_meta("bar", bar)
	sc.add_child(_book_list)
	var bt := HBoxContainer.new()
	bt.add_theme_constant_override("separation", 8)
	bt.alignment = BoxContainer.ALIGNMENT_END
	b.add_child(bt)
	var hb := Button.new()
	hb.text = T.t("Blinki-Hinweis jetzt")
	hb.tooltip_text = T.t("Ein Hinweis auf das Nächste, das jetzt zu finden ist")
	hb.pressed.connect(func():
		main.mehr.close_window()
		if not show_hint():
			_say_small(T.t("Gerade gibt es hier nichts mehr zu finden – vielleicht nachts, bei Regen oder am Morgen?")))
	bt.add_child(hb)
	var cl := Button.new()
	cl.text = T.t("Schliessen")
	cl.pressed.connect(main.mehr.close_window)
	bt.add_child(cl)
	_refresh_book()


func book_open() -> bool:
	return main.mehr != null and main.mehr.win_id == "book" and _book_list != null and is_instance_valid(_book_list)


func _refresh_book() -> void:
	if not book_open():
		return
	for c in _book_list.get_children():
		c.queue_free()
	var L := list()
	var nf := count()
	(_book_list.get_meta("top") as Label).text = T.t("%s: %d von %d entdeckt", [_scene_name(main.scene), nf, L.size()])
	var bar: ProgressBar = _book_list.get_meta("bar")
	bar.max_value = maxf(1.0, L.size())
	bar.value = nf
	if L.is_empty():
		_book_list.add_child(UI.small(T.t("In dieser Szene gibt es (noch) nichts zu entdecken.")))
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	_book_list.add_child(grid)
	for e in L:
		grid.add_child(_entry(e))
	var others := []                                # the other scenes (as far as they were visited)
	for s in data["scenes"]:
		if s == main.scene:
			continue
		var S: Dictionary = data["scenes"][s]
		if (S["known"] as Dictionary).size() > 0:
			others.append("%s %d / %d" % [_scene_name(s), (S["found"] as Dictionary).size(), (S["known"] as Dictionary).size()])
	if not others.is_empty():
		_book_list.add_child(UI.heading(T.t("Andere Szenen")))
		var o := UI.small(" · ".join(others))
		o.custom_minimum_size = Vector2(560, 0)
		_book_list.add_child(o)
	if main.spielbereich != null:                   # Geschichten-Menü: the badges live here now (not on «Spielen») - on top
		var bh := UI.heading(T.t("Abzeichen"))
		var bg: Control = main.spielbereich.badge_grid(560.0)
		_book_list.add_child(bh)
		_book_list.add_child(bg)
		_book_list.move_child(bh, 0)
		_book_list.move_child(bg, 1)
		var lh := UI.heading(T.t("Entdeckungen"))
		_book_list.add_child(lh)
		_book_list.move_child(lh, 2)


func _scene_name(s: String) -> String:
	return T.t(str(main.Scenes.name_of(s))) if main.Scenes != null else s


func _entry(e: Dictionary) -> Control:
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(282, 0)
	p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	p.add_theme_stylebox_override("panel", UI.box(UI.PANEL2 if e.found else UI.FIELD, UI.LINE, 12, 8, 1))
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	p.add_child(h)
	var pic := TextureRect.new()
	pic.custom_minimum_size = Vector2(96, 54)
	pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	pic.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	if e.found:
		pic.texture = _tex(str(e.pic))
	if pic.texture == null:                         # no picture (yet): a dark box with «?» / the symbol of the kind
		var ph := ColorRect.new()
		ph.color = Color(0, 0, 0, 0.35)
		ph.custom_minimum_size = pic.custom_minimum_size
		ph.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		var q := Label.new()
		q.text = "?" if not e.found else "·"
		q.set_anchors_preset(Control.PRESET_FULL_RECT)
		q.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		q.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		q.add_theme_font_size_override("font_size", 22)
		q.add_theme_color_override("font_color", Color(UI.MUT, 0.6))
		ph.add_child(q)
		h.add_child(ph)
	else:
		h.add_child(pic)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var tl := HBoxContainer.new()
	tl.add_theme_constant_override("separation", 4)
	v.add_child(tl)
	var t := Label.new()
	t.text = T.t(str(e.title)) if e.found else "???"
	t.add_theme_font_override("font", UI.heading_font())
	t.add_theme_font_size_override("font_size", 13)
	t.add_theme_color_override("font_color", UI.TXT if e.found else UI.MUT)
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	t.custom_minimum_size = Vector2(110, 0)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tl.add_child(t)
	for w in e.when:                                # the time / weather symbol: come back at night, in the rain …
		if WHEN_SYM.has(str(w)) and Sym.SHAPES.has(WHEN_SYM[str(w)]):
			var ic := Sym.icon_rect(WHEN_SYM[str(w)], 14)
			ic.tooltip_text = T.t(WHEN_NAME.get(str(w), ""))
			ic.mouse_filter = Control.MOUSE_FILTER_PASS
			ic.modulate = Color(1, 1, 1, 0.85 if e.found else 0.6)
			tl.add_child(ic)
	if e.photo:
		var cm := Sym.icon_rect("camera", 14)
		cm.tooltip_text = T.t("mit MoveEyes Kamera fotografieren")
		cm.mouse_filter = Control.MOUSE_FILTER_PASS
		cm.modulate = Color(1, 1, 1, 0.85 if e.found else 0.6)
		tl.add_child(cm)
	var sub := ""
	if e.found:
		sub = T.t(str(e.short))
	else:
		sub = T.t(KIND_NAME.get(str(e.kind), "etwas"))
		var wn := []
		for w in e.when:
			if WHEN_NAME.has(str(w)):
				wn.append(T.t(WHEN_NAME[str(w)]))
		if not wn.is_empty():
			sub += " · " + ", ".join(wn)
		if e.photo:
			sub += " · " + T.t("Foto")
	var s := UI.small(sub, UI.TXT if e.found else UI.MUT)
	s.custom_minimum_size = Vector2(150, 0)
	v.add_child(s)
	if e.demo:
		var d := UI.small(T.t("Demo"), Color(UI.MUT, 0.7))
		d.add_theme_font_size_override("font_size", 10)
		v.add_child(d)
	return p


# =============================================================================================================================
# ---- the settings (card «Spiel» → part «Entdecken», also on MoveEye's page through /control) -------------------------------
# =============================================================================================================================
func register_controls() -> void:
	"""main._register_controls: the ids are placed by main.gd PLACE / DISC_IDS (group «Spiel», part «Entdecken»)"""
	main.add_control("button", "disc_book", "📖 Entdeckungsbuch", null, func(): open_book(), "Spiel")
	main.add_control("button", "disc_photo", "📷 Foto für Entdeckungsbuch", null, func(): take_photo(), "Spiel")
	main.add_control("toggle", "disc_hints", "Blinki-Hinweise, wenn man lange nichts findet", func(): return hints_on, func(v): set_hints(bool(v)), "Spiel")
	main.add_control("slider", "disc_hint_min", "Blinki-Hinweis nach (Minuten ohne Fund)", func(): return hint_min, func(v): set_hint_min(float(v)), "Spiel",
			{"min": 1, "max": 30, "step": 1, "unit": "min"})
	main.add_control("toggle", "disc_demo", "Demo-Entdeckungen im Camping-Platz", func(): return demo_on, func(v): set_demo(bool(v)), "Spiel")


func set_demo(on: bool) -> void:
	demo_on = on
	_dirty = true
	if main.scene == "camping":
		main.set_scene("camping")                  # build again: with / without the demo things


# ---- /control {"action": "entdecken", "do": …} (tests and MoveEye) -------------------------------------------------------------
func info(lite := false) -> Dictionary:
	var L := list()
	for e in L:                                       # in the language of MoveEye (i18n.gd: the language MoveEye sent)
		e["title"] = T.t(str(e.title)) if e.found else ""
		e["short"] = T.t(str(e.short)) if e.found and not lite else ""
		if not e.found:
			e["icon"] = ""                            # no spoiler on MoveEye's page
	return {"ok": true, "scene": main.scene, "scene_name": _scene_name(main.scene), "found": count(), "total": L.size(), "items": L,
			"photo": photo_id != "", "photo_id": photo_id, "hint": hint_id, "hint_text": _hint_l.text if _hint_box.visible else "",
			"hints_on": hints_on, "hint_min": hint_min, "book": book_open(), "check_us": roundi(check_us),
			"badges": main.spielbereich.badges() if main.spielbereich != null and not lite else []}


func control(d: Dictionary) -> Dictionary:
	match str(d.get("do", "info")):
		"open":
			open_book()
		"close":
			if book_open():
				main.mehr.close_window()
		"photo":
			var r := take_photo()
			r.merge(info(true))
			return r
		"mark":
			return {"ok": mark_found(str(d.get("id", "")), str(d.get("how", "api")))}
		"reset":
			reset(str(d.get("scene", "")))
		"hint":
			return {"ok": show_hint(str(d.get("id", ""))), "text": _hint_l.text}
		"hide_hint":
			hide_hint()
		"set":
			if d.has("hints_on"):
				set_hints(bool(d["hints_on"]))
			if d.has("hint_min"):
				set_hint_min(float(d["hint_min"]))
			if d.has("last_new_ago"):                 # tests: «nothing new since n seconds»
				last_new_t = main.now() - float(d["last_new_ago"])
				last_hint_t = -1000.0
		"save":
			save()
		"register":                                  # tests: an entry from outside {id, info: {…, position: [x, y, z], size: [x, y, z]}}
			var inf: Dictionary = (d.get("info", {}) as Dictionary).duplicate()
			for k in ["position", "size"]:
				if typeof(inf.get(k, null)) == TYPE_ARRAY and (inf[k] as Array).size() == 3:
					inf[k] = Vector3(float(inf[k][0]), float(inf[k][1]), float(inf[k][2]))
				else:
					inf.erase(k)
			inf.erase("node")
			inf.erase("active")
			return {"ok": register(str(d.get("id", "")), inf)}
		"unregister":
			unregister(str(d.get("id", "")))
		"forget":
			forget(str(d.get("id", "")))
		"where":                                     # tests: where an item is, and what the cameras see of it
			var id := str(d.get("id", ""))
			if not items.has(id):
				return {"ok": false, "error": "unknown id"}
			var it: Dictionary = items[id]
			var p := _pos(it)
			var cam := get_viewport().get_camera_3d()
			return {"ok": true, "pos": [p.x, p.y, p.z], "possible": possible_now(id), "found": is_found(id),
					"view_dist": cam.global_position.distance_to(p) if cam != null else -1.0,
					"in_frustum": cam.is_position_in_frustum(p) if cam != null else false,
					"los": _los(cam.global_position, p) if cam != null else false,
					"head_rect": [photo_rect.position.x, photo_rect.position.y, photo_rect.size.x, photo_rect.size.y] if photo_id == id else []}
	return info(bool(d.get("lite", false)))


# =============================================================================================================================
# ---- demo: three discoveries in «Camping-Platz» (Daniel: testable before the Ferienpark; can stay as a mini set) ----------
# =============================================================================================================================
func _demo_camping() -> void:
	var root: Node3D = main.scene_parent
	var stone_m: Material = main.mat(Color(0.52, 0.5, 0.47))
	# 1 · a place: a small cairn behind the head, at the edge of the meadow (any time)
	var cairn_p: Vector3 = main.pos_of(160.0, 19.0)
	var cn := Node3D.new()
	root.add_child(cn)
	cn.position = cairn_p
	var y := 0.0
	for i in range(5):
		var r := 0.22 - i * 0.035
		var s := SphereMesh.new()
		s.radius = r
		s.height = r * 1.1
		var mi := MeshInstance3D.new()
		mi.mesh = s
		mi.material_override = stone_m
		mi.position = Vector3(0.02 * (i % 2), y + r * 0.5, 0.015 * (i % 3))
		mi.rotation.y = i * 0.9
		cn.add_child(mi)
		y += r * 1.0
	_demo_nodes.append(cn)
	register("camping.demo_steinmann", {"title": "Steinmännchen", "short_text": "Jemand hat am Wiesenrand Steine gestapelt – fünf Stück, ganz ruhig.",
			"hint": "Hinter dem Kopf von MoveEye, am Rand der Wiese, hat jemand Steine gestapelt …", "icon": "🪨",
			"position": cairn_p + Vector3(0, 0.4, 0), "size": Vector3(0.5, 0.9, 0.5), "radius": 7.0, "when": "any", "kind": "ort", "demo": true})
	# 2 · only at night: a woodpile where fireflies glow (the glow is hidden by day)
	var wood_p: Vector3 = main.pos_of(-100.0, 17.0)
	var wn := Node3D.new()
	root.add_child(wn)
	wn.position = wood_p
	wn.rotation.y = 0.6
	var wood_m: Material = main.mat(Color(0.36, 0.25, 0.15))
	for row in range(3):
		for k in range(4 - row):
			var c := CylinderMesh.new()
			c.top_radius = 0.09
			c.bottom_radius = 0.09
			c.height = 1.1
			c.radial_segments = 8
			var mi2 := MeshInstance3D.new()
			mi2.mesh = c
			mi2.material_override = wood_m
			mi2.rotation.z = PI / 2.0
			mi2.position = Vector3(0, 0.09 + row * 0.16, (k - (3 - row) * 0.5) * 0.19)
			wn.add_child(mi2)
	main.add_obstacle(wood_p, 0.5)
	main.set_obstacle_height(0.5)
	var glow := Node3D.new()
	wn.add_child(glow)
	var gm := StandardMaterial3D.new()
	gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	gm.albedo_color = Color(0.75, 1.0, 0.35)
	gm.emission_enabled = true
	gm.emission = Color(0.7, 1.0, 0.3)
	gm.emission_energy_multiplier = 3.0
	var rng := RandomNumberGenerator.new()
	rng.seed = 31
	for i in range(14):
		var dot := SphereMesh.new()
		dot.radius = 0.018
		dot.height = 0.036
		dot.radial_segments = 6
		dot.rings = 3
		var md := MeshInstance3D.new()
		md.mesh = dot
		md.material_override = gm
		md.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		md.position = Vector3(rng.randf_range(-0.7, 0.7), rng.randf_range(0.3, 1.2), rng.randf_range(-0.6, 0.6))
		glow.add_child(md)
	glow.visible = main.is_dark()
	_demo_glow = glow
	main.anims.append(func(_dt, t):                  # they drift a little and blink (slow, quiet)
		if glow.visible and is_instance_valid(glow):
			for i in range(glow.get_child_count()):
				var n: Node3D = glow.get_child(i)
				n.position.y += sin(t * 0.7 + i) * 0.0015
				n.visible = fmod(t * 0.6 + i * 0.37, 2.0) < 1.4)
	_demo_nodes.append(wn)
	register("camping.demo_gluehwuermchen", {"title": "Glühwürmchen am Holzstapel", "short_text": "Nachts tanzen beim Holzstapel kleine grüne Lichter. Am Tag sieht man nichts davon.",
			"hint": "Nachts glimmt beim Holzstapel links hinten etwas …", "icon": "✨",
			"position": wood_p + Vector3(0, 0.6, 0), "size": Vector3(1.2, 1.0, 1.0), "radius": 7.0, "when": "night", "kind": "tier", "demo": true})
	# 3 · photo: an owl on a post - turn the head of MoveEye and take a picture
	var owl_p: Vector3 = main.pos_of(58.0, 9.0)
	var on := Node3D.new()
	root.add_child(on)
	on.position = owl_p
	on.rotation.y = deg_to_rad(180.0 + 58.0)            # it looks towards MoveEye
	var post := CylinderMesh.new()
	post.top_radius = 0.06
	post.bottom_radius = 0.07
	post.height = 1.3
	var pm := MeshInstance3D.new()
	pm.mesh = post
	pm.material_override = wood_m
	pm.position = Vector3(0, 0.65, 0)
	on.add_child(pm)
	main.add_obstacle(owl_p, 0.1)
	var owl_m: Material = main.mat(Color(0.48, 0.38, 0.27))
	var body := SphereMesh.new()
	body.radius = 0.13
	body.height = 0.34
	var bm := MeshInstance3D.new()
	bm.mesh = body
	bm.material_override = owl_m
	bm.position = Vector3(0, 1.47, 0)
	on.add_child(bm)
	var hd := SphereMesh.new()
	hd.radius = 0.1
	hd.height = 0.18
	var hm := MeshInstance3D.new()
	hm.mesh = hd
	hm.material_override = owl_m
	hm.position = Vector3(0, 1.68, 0)
	on.add_child(hm)
	var eye_m: Material = main.mat(Color(0.95, 0.75, 0.2))
	for sx in [-1, 1]:
		var e := SphereMesh.new()
		e.radius = 0.025
		e.height = 0.05
		var em := MeshInstance3D.new()
		em.mesh = e
		em.material_override = eye_m
		em.position = Vector3(0.04 * sx, 1.70, -0.085)
		on.add_child(em)
	main.anims.append(func(_dt, t):                  # now and then it turns its head (slowly - you have to look closely)
		if is_instance_valid(hm):
			var k := fmod(t, 9.0)
			hm.rotation.y = (deg_to_rad(70.0) * sin(clampf((k - 6.0) / 1.5, 0.0, 1.0) * PI)) if k > 6.0 else 0.0)
	_demo_nodes.append(on)
	register("camping.demo_eule", {"title": "Eule auf dem Pfosten", "short_text": "Sie sitzt ganz still auf dem Pfosten und dreht nur ab und zu den Kopf. Fotografiert mit MoveEyes Kamera.",
			"hint": "Rechts von MoveEye sitzt jemand ganz still auf einem Pfosten – etwas für ein Foto mit MoveEyes Kamera?", "icon": "🦉",
			"position": owl_p + Vector3(0, 1.55, 0), "size": Vector3(0.3, 0.45, 0.3), "radius": 6.0, "when": "any", "kind": "tier",
			"photo_required": true, "demo": true})
