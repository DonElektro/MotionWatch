extends Node
## «Frei erkunden mit eigener Figur», Etappe 4 (Besitzer 21.11.2026): Fotomodus, Ort merken / weiter am gemerkten Ort,
## Startpunkte (Haken für andere Spiele, z. B. Grossvater: der Grat beim Sonnenaufgang nach dem Ende der Geschichte).
## Ein Kind von explore_person.gd («person»). Tageszeit und Wetter wählt man im Fenster «Figur gestalten», Reiter «Welt».
##   * Fotomodus (P / Knopf im Rucksack-Menü / Reiter «Welt»): die Figur bleibt stehen, die Kamera kreist frei um sie
##     (Maus ziehen / Pfeile / rechter Stick drehen, Rad / + / − Abstand, Bild ↑↓ Höhe), «Foto» speichert ein Bild OHNE
##     Bedienung (eigene Kamera, user://erkunden_fotos/), «Zurück» / Esc / P beendet ihn.
##   * Ort merken (Knopf im Reiter «Welt»): Welt, Stelle und Richtung (main.ex_ort, bleibt gespeichert). «Frei erkunden» in
##     derselben Welt beginnt dort; «Weiter am gemerkten Ort» (Spielen) lädt die Welt und beginnt dort.
##   * Startpunkte: main.ex_startpunkte {id: {name, scene, x, y, z, h}} - andere Teile melden einen mit
##     explore.person.extras.startpunkt_melden(id, name, scene, welt_pos, heading) (bleibt gespeichert), «Spielen» zeigt sie
##     unter «Frei erkunden», frei_ab(id) beginnt dort. Grossvater K1 (Sonnenaufgang auf dem Grat): nach dem Ende melden.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const FOTO_DIR := "user://erkunden_fotos"

var person
var main
var foto_an := false
var _yaw := 0.0
var _pitch := 0.25
var _dist := 3.2
var _hoch := 0.0
var _layer: CanvasLayer
var _leiste: HBoxContainer
var _fotos := 0
var letztes_foto := ""


func _ready() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 21
	add_child(_layer)
	_leiste = HBoxContainer.new()
	_leiste.add_theme_constant_override("separation", 10)
	_leiste.visible = false
	_layer.add_child(_leiste)
	for e in [["foto", "Foto"], ["zurueck", "Zurück"]]:
		var b := Button.new()
		b.name = str(e[0])
		b.set_meta("t", str(e[1]))
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(120, 52)
		var id := str(e[0])
		b.pressed.connect(func(): foto() if id == "foto" else fotomodus(false))
		if id == "foto":
			UI.primary(b)
		_leiste.add_child(b)


# ---- photo mode ------------------------------------------------------------------------------------------------------------
func fotomodus(v: bool) -> void:
	if v and (person == null or not person.ok() or not bool(person.active)):
		return
	foto_an = v
	_leiste.visible = v
	if v:
		if person.sachen != null:
			person.sachen.feldstecher(false)
			person.sachen.menu(false)
		var to: Vector3 = main.view_cam.global_position - person.figur.pos()
		_yaw = atan2(to.x, to.z)
		_pitch = 0.25
		_dist = 3.2
		_hoch = 0.0
		for b in _leiste.get_children():
			(b as Button).text = T.t(str(b.get_meta("t")))
	else:
		person.portrait_ende()


func kamera(cam: Camera3D, dt: float, d_or: float, d_pi: float, d_di: float) -> void:
	"""the free camera of the photo mode round the figure"""
	_yaw = wrapf(_yaw - d_or, -PI, PI)
	_pitch = clampf(_pitch + d_pi, -0.2, 1.4)
	_dist = clampf(_dist + d_di * 0.5, 1.2, 25.0)
	if not main.typing():
		var k := 1.6 * dt
		if Input.is_key_pressed(KEY_LEFT):
			_yaw -= k
		if Input.is_key_pressed(KEY_RIGHT):
			_yaw += k
		if Input.is_key_pressed(KEY_UP):
			_pitch = clampf(_pitch + k * 0.6, -0.2, 1.4)
		if Input.is_key_pressed(KEY_DOWN):
			_pitch = clampf(_pitch - k * 0.6, -0.2, 1.4)
	var pm = main.get("padmap")
	if pm != null:
		var st: Vector2 = pm.drive_cmd()
		_yaw += st.y * dt * 1.6
		_dist = clampf(_dist - st.x * dt * 3.0, 1.2, 25.0)
	var ziel: Vector3 = person.figur.pos() + Vector3(0, clampf(person.hoehe(), 0.3, 2.0) * 0.55 + _hoch, 0)
	var at := ziel + Vector3(sin(_yaw) * cos(_pitch), sin(_pitch), cos(_yaw) * cos(_pitch)) * _dist
	at.y = maxf(at.y, main.ground_y(at.x, at.z) + 0.25)
	main.view_mode = 0
	cam.fov = 55.0
	cam.global_transform = Transform3D(Basis.IDENTITY, at).looking_at(ziel, Vector3.UP)


func foto() -> String:
	"""a picture of the 3D view without any controls: an own camera at the place of the view, rendered once"""
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FOTO_DIR))
	var vs: Vector2i = Vector2i(get_viewport().get_visible_rect().size)
	var sv := SubViewport.new()
	sv.size = Vector2i(maxi(320, vs.x), maxi(240, vs.y))
	sv.world_3d = get_viewport().world_3d
	sv.own_world_3d = false
	sv.render_target_update_mode = SubViewport.UPDATE_ONCE
	var cam := Camera3D.new()
	cam.cull_mask = 1                                     # what MoveEye could see too: no helper marks, no thermal layer
	cam.fov = main.view_cam.fov
	cam.far = main.view_cam.far
	sv.add_child(cam)
	add_child(sv)
	cam.global_transform = main.view_cam.global_transform
	cam.current = true
	await RenderingServer.frame_post_draw
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var img := sv.get_texture().get_image()
	_fotos += 1
	var nm := "%s/foto_%s_%d.png" % [FOTO_DIR, Time.get_datetime_string_from_system().replace(":", "-"), _fotos]
	if img != null:
		img.save_png(nm)
	sv.queue_free()
	letztes_foto = nm
	if person.sachen != null:
		person.sachen.sag(T.t("Foto gespeichert"), 2.0)
	return nm


# ---- remember the place ------------------------------------------------------------------------------------------------------
func ort_merken() -> Dictionary:
	if person == null or not person.ok():
		return {}
	var p: Vector3 = person.figur.pos()
	main.ex_ort = {"scene": str(main.scene), "x": snappedf(p.x, 0.01), "y": snappedf(p.y, 0.01), "z": snappedf(p.z, 0.01),
			"h": snappedf(float(person.actor.heading), 0.001), "name": _welt_name(str(main.scene))}
	main._settings_dirty = true
	if person.sachen != null:
		person.sachen.sag(T.t("Ort gemerkt – beim nächsten Mal geht es hier weiter"), 2.5)
	return main.ex_ort


func ort() -> Dictionary:
	var o = main.get("ex_ort")
	return o if o is Dictionary and o.has("scene") else {}


func _welt_name(id: String) -> String:
	var Sc = load("res://scripts/scenes.gd")
	for e in Sc.LIST:
		if str(e[0]) == id:
			return T.t(str(e[1]))
	return id


func am_ort_beginnen(o: Dictionary) -> bool:
	"""puts the figure on the remembered place (same world)"""
	if o.is_empty() or str(o.get("scene", "")) != str(main.scene) or not person.ok():
		return false
	person.place(Vector3(float(o["x"]), 0, float(o["z"])))
	person.figur.setzen(person.figur.pos(), float(o.get("h", 0.0)))
	person.regie.hinter_figur()
	return true


# ---- start points (other games) --------------------------------------------------------------------------------------------
func startpunkt_melden(id: String, name: String, scene: String, w: Vector3, heading := 0.0) -> void:
	"""another part offers a start point (e.g. Grossvater: the ridge at sunrise, after the end of the story) - kept"""
	var sp: Dictionary = main.get("ex_startpunkte") if main.get("ex_startpunkte") is Dictionary else {}
	sp[id] = {"name": name, "scene": scene, "x": snappedf(w.x, 0.01), "y": snappedf(w.y, 0.01), "z": snappedf(w.z, 0.01), "h": snappedf(heading, 0.001)}
	main.ex_startpunkte = sp
	main._settings_dirty = true


func startpunkte() -> Dictionary:
	var sp = main.get("ex_startpunkte")
	return sp if sp is Dictionary else {}


func info() -> Dictionary:
	return {"foto": foto_an, "ort": ort(), "startpunkte": startpunkte().keys(), "letztes_foto": letztes_foto}


func _process(_dt: float) -> void:
	if foto_an:
		if person == null or not person.ok() or not bool(person.active) or not bool(person.ex.on):
			fotomodus(false)
			return
		var s: Vector2 = get_viewport().get_visible_rect().size
		_leiste.position = Vector2((s.x - 250.0) * 0.5, s.y - 140.0)
