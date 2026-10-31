extends Node
## Entwicklertool 3 «Notizen, Kontaktbogen, Kapitel-Sprung» (Daniel 31.10.2026) - die Teile im Fenster «Mehr → Entwickler»
## (devtool.gd) in eigenen Dateien, damit devtool.gd fast unverändert bleibt (parallel: Entwicklertool 2 «Regler + Ebenen»).
## devtool.gd ruft nur: extra.build(vbox) · extra.control(d) (null = nicht meins) · extra.map_click(world_xz) ·
## extra.map_draw(map); net.gd ruft extra.http_get(path) für GET /dev/… .
##   * Notizen an Claude: devtool_notizen.gd (user://dev_notizen/<id>.json + .jpg, ZIP-Export)
##   * Kontaktbogen:      devtool_kontakt.gd (user://kontaktbogen/<welt>/<id>.jpg + index.html)
##   * Kapitel-Sprung:    devtool_kapitel.gd (Abenteuer, Spielbereich, Horror nur wenn schon entsperrt; Test-Spielstand)
## Hier: die Knopfzeile (ein Teil offen), das Foto ohne Bedienelemente (eigene kleine Kamera wie entdecken.gd, cull_mask 1 =
## wie die Kameras von MoveEye: keine Helfer-Marken) und GET /dev/kontakt/… · /dev/notizen/… · /dev/notizen.zip.
## Lite: dev._lite() (Quality.lite()) - die Fotos warten länger, bis die Szene steht (Kontaktbogen langsamer, sonst gleich).

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")

var dev                                  # devtool.gd
var main
var notizen                              # devtool_notizen.gd
var kontakt                              # devtool_kontakt.gd
var kapitel                              # devtool_kapitel.gd
var _tabs := {}                          # id -> Button
var _bodies := {}                        # id -> Control
var open_tab := ""
var _vp: SubViewport = null
var _cam: Camera3D = null
var _photo_busy := false


func _ready() -> void:
	notizen = preload("res://scripts/devtool_notizen.gd").new()
	kontakt = preload("res://scripts/devtool_kontakt.gd").new()
	kapitel = preload("res://scripts/devtool_kapitel.gd").new()
	for p in [notizen, kontakt, kapitel]:
		p.x = self
		p.dev = dev
		p.main = main
		add_child(p)


# =============================================================================================================================
# the row «Notizen · Kontaktbogen · Kapitel» in the window (one part open at a time, below the map)
# =============================================================================================================================
func build(v: VBoxContainer) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	v.add_child(row)
	var holder := VBoxContainer.new()
	holder.add_theme_constant_override("separation", 6)
	for it in [["notizen", "📝 " + T.t("Notizen an Claude"), notizen], ["kontakt", "🖼 " + T.t("Kontaktbogen"), kontakt],
			["kapitel", "⏭ " + T.t("Kapitel-Sprung"), kapitel]]:
		var b := Button.new()
		b.text = str(it[1])
		b.toggle_mode = true
		b.focus_mode = Control.FOCUS_NONE
		var id: String = it[0]
		b.toggled.connect(func(on): show_tab(id if on else ""))
		row.add_child(b)
		_tabs[id] = b
		var body := VBoxContainer.new()
		body.add_theme_constant_override("separation", 6)
		body.custom_minimum_size = Vector2(598, 0)
		body.visible = false
		(it[2]).build(body)
		holder.add_child(body)
		_bodies[id] = body
	v.add_child(holder)


func show_tab(id: String) -> void:
	open_tab = id
	for k in _tabs:
		(_tabs[k] as Button).set_pressed_no_signal(k == id)
		(_bodies[k] as Control).visible = k == id
	for p in [notizen, kontakt, kapitel]:
		if p.has_method("on_show"):
			p.on_show(open_tab)
	if dev.panel != null:
		dev.panel.reset_size()


# =============================================================================================================================
# hooks of devtool.gd
# =============================================================================================================================
const MINE := ["notes", "note_add", "note_done", "note_delete", "note_goto", "notes_export",
		"contact", "contact_state", "contact_stop", "contact_list",
		"chapters", "chapter", "test_end"]


func control(d: Dictionary):
	var w := str(d.get("do", ""))
	if not w in MINE:
		return null
	if w.begins_with("note"):
		return notizen.control(d)
	if w.begins_with("contact"):
		return kontakt.control(d)
	return kapitel.control(d)


func map_click(wp: Vector2) -> bool:
	"""a click on the map that is not a jump to a place: «Stelle auf der Karte» of a note, or a note marker"""
	return notizen.map_click(wp)


func map_draw(m: Control) -> void:
	notizen.map_draw(m)


# =============================================================================================================================
# a picture of the 3D view without buttons (own small camera, like entdecken.gd)
# =============================================================================================================================
func photo(sz: Vector2i, xf = null, fov := -1.0) -> Image:
	"""the view of main.view_cam (or xf: Transform3D in the scene) as an Image of size sz - await it"""
	while _photo_busy:
		await get_tree().process_frame
	_photo_busy = true
	if _vp == null:
		_vp = SubViewport.new()
		_vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		_vp.msaa_3d = Viewport.MSAA_DISABLED
		add_child(_vp)
		_cam = Camera3D.new()
		_cam.cull_mask = 1                       # like the cameras of MoveEye: no helper marks, no thermal layer
		_vp.add_child(_cam)
	var src: Camera3D = main.view_cam
	_vp.size = sz
	_cam.current = true
	_cam.global_transform = xf if xf is Transform3D else src.global_transform
	_cam.fov = fov if fov > 0.0 else src.fov
	_cam.near = src.near
	_cam.far = src.far
	_cam.environment = src.environment
	_cam.attributes = src.attributes
	for i in 2:                                  # (the first picture after a new size can be empty)
		_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		await RenderingServer.frame_post_draw
	var img: Image = _vp.get_texture().get_image()
	_photo_busy = false
	if img == null or img.is_empty():
		return null
	img.convert(Image.FORMAT_RGB8)
	return img


static func open_folder(dir: String) -> void:
	DirAccess.make_dir_recursive_absolute(dir)
	OS.shell_open(ProjectSettings.globalize_path(dir))


# =============================================================================================================================
# GET /dev/kontakt/<welt>/<id>.jpg · /dev/kontakt/index.html · /dev/kontakt.json · /dev/notizen/<id>.jpg|json · /dev/notizen.zip
# =============================================================================================================================
const CTYPE := {"jpg": "image/jpeg", "html": "text/html; charset=utf-8", "json": "application/json", "zip": "application/zip"}


func http_get(path: String) -> Array:
	"""[bytes, content type] or [] (not found). Only these two folders, only plain names (no «..»)."""
	var p := path.trim_prefix("/dev/")
	if p.find("..") >= 0 or p.find("\\") >= 0 or p.find(":") >= 0:
		return []
	if p == "kontakt.json":
		return [JSON.stringify(kontakt.control({"do": "contact_list"})).to_utf8_buffer(), CTYPE["json"]]
	if p == "notizen.json":
		return [JSON.stringify(notizen.control({"do": "notes"})).to_utf8_buffer(), CTYPE["json"]]
	if p == "notizen.zip":
		var z: String = notizen.export_zip()
		return [FileAccess.get_file_as_bytes(z), CTYPE["zip"]] if z != "" else []
	var file := ""
	if p.begins_with("kontakt/"):
		file = kontakt.DIR + "/" + p.trim_prefix("kontakt/")
		if p == "kontakt/" or p == "kontakt":
			file = kontakt.DIR + "/index.html"
	elif p.begins_with("notizen/"):
		file = notizen.DIR + "/" + p.trim_prefix("notizen/")
	var ext := file.get_extension().to_lower()
	if file == "" or not CTYPE.has(ext) or not FileAccess.file_exists(file):
		return []
	return [FileAccess.get_file_as_bytes(file), CTYPE[ext]]
