extends PanelContainer
## Live picture of a camera below the overview map (from 3D-3.34): camera 1, camera 2 or the thermal picture, size
## adjustable. Button «Livebild» in the bar below, key L, or the settings (System → Ansicht). Click = look through it.

var main
var tex: TextureRect
var title: Label
var cam := 0                       # 0 = camera 1, 1 = camera 2, 2 = thermal picture
var width_px := 260.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	tooltip_text = "Livebild · Klick: durch diese Kamera schauen · L: aus / ein"
	add_theme_stylebox_override("panel", main.UI.box(Color(0.05, 0.07, 0.09, 0.88), main.UI.LINE, 8, 4, 1))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(v)
	title = Label.new()
	title.add_theme_font_size_override("font_size", 11)
	title.add_theme_color_override("font_color", Color(1, 1, 1, 0.85))
	title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(title)
	tex = TextureRect.new()
	tex.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tex.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	tex.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	tex.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(tex)
	apply()


func apply() -> void:
	cam = clampi(cam, 0, 2)
	title.text = ["Livebild · Kamera 1", "Livebild · Kamera 2", "Livebild · Wärmebild"][cam]
	if cam < 2:
		tex.texture = main.vps[cam].get_texture()
		tex.custom_minimum_size = Vector2(width_px, width_px * 9.0 / 16.0)
	else:
		tex.texture = main.th_preview
		tex.custom_minimum_size = Vector2(width_px, width_px * 0.75)
	size = Vector2.ZERO                     # shrink to the content
	reset_size()


func _process(_dt: float) -> void:
	if not visible or has_meta("fenster"):
		return                             # in a window frame (fenster.gd): the frame places it
	var y := 92.0                          # below the map when it is shown, else where the map would be
	if main.minimap != null and main.minimap.visible:
		y = main.minimap.position.y + main.minimap.size.y + 8.0
	position = Vector2(14, y)


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
		main.set_view(cam + 1)               # 1 = camera 1, 2 = camera 2, 3 = thermal picture
		accept_event()
