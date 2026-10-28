extends PanelContainer
## 3D-3.77: «Kopf steuern» - turn the head of Motion Watch from the simulator window: big arrows (hold = keeps turning),
## centre, the white light, and the picture of the head camera (drag in it = turn). Motion Watch does it (2.95.103,
## request «look» / «light» through mw_cmd) - like the arrows on its own page. In a game with a PC guard the game turns
## the head (localplay.gd).

var main
var img: TextureRect
var info: Label
var _hold := ""
var _hold_t := 0.0
var _light := false
var _drag := false
var _acc := Vector2.ZERO

const UI = preload("res://scripts/ui_style.gd")


func _ready() -> void:
	visible = false
	add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.94), UI.ACC, 14, 10, 1))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	add_child(v)
	var hd := HBoxContainer.new()
	v.add_child(hd)
	var t := UI.heading("Kopf steuern")
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(t)
	var x := Button.new()
	x.text = "✕"
	x.pressed.connect(func(): visible = false)
	hd.add_child(x)
	img = TextureRect.new()
	img.custom_minimum_size = Vector2(320, 180)
	img.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	img.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	img.mouse_filter = Control.MOUSE_FILTER_STOP
	img.gui_input.connect(_img_input)
	img.tooltip_text = "Im Bild ziehen = Kopf drehen"
	v.add_child(img)
	var g := GridContainer.new()
	g.columns = 3
	g.add_theme_constant_override("h_separation", 6)
	g.add_theme_constant_override("v_separation", 6)
	v.add_child(g)
	for d in [["", ""], ["▲", "up"], ["", ""], ["◀", "left"], ["⌂", "center"], ["▶", "right"], ["", ""], ["▼", "down"], ["💡", "light"]]:
		if d[1] == "":
			g.add_child(Control.new())
			continue
		var b := Button.new()
		b.text = d[0]
		b.custom_minimum_size = Vector2(70, 46)
		b.add_theme_font_size_override("font_size", 20)
		var k: String = d[1]
		if k in ["up", "down", "left", "right"]:
			b.button_down.connect(func(): _hold = k; _hold_t = 0.0)
			b.button_up.connect(func(): _hold = "")
		elif k == "center":
			b.pressed.connect(func(): main.mw_look("center"))
		else:
			b.tooltip_text = "Weisses Licht ein / aus"
			b.pressed.connect(func(): _light = not _light; main.mw_light(_light))
		g.add_child(b)
	info = UI.small("")
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.custom_minimum_size = Vector2(320, 0)
	v.add_child(info)


func toggle() -> void:
	visible = not visible
	if visible:
		get_parent().move_child(self, -1)


func _img_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		_drag = ev.pressed
		_acc = Vector2.ZERO
	elif ev is InputEventMouseMotion and _drag:
		_acc += ev.relative
		while absf(_acc.x) > 12.0:                       # 12 px = one small step
			main.mw_look("left" if _acc.x > 0 else "right", 1.5)   # drag the picture: like pulling the view along
			_acc.x -= signf(_acc.x) * 12.0
		while absf(_acc.y) > 12.0:
			main.mw_look("up" if _acc.y > 0 else "down", 1.5)
			_acc.y -= signf(_acc.y) * 12.0


func _process(dt: float) -> void:
	if not visible:
		return
	var vs := get_viewport_rect().size
	position = Vector2(14, vs.y - size.y - 110)
	img.texture = main.vps[0].get_texture()
	var con: bool = main.now() - main.mw_t < 3.0
	info.text = ("Motion Watch dreht den Kopf (auch Tracking und Patrouille pausieren kurz)." if con
			else "Motion Watch ist nicht verbunden – zuerst «An Motion Watch senden» und Motion Watch verbinden.")
	if _hold != "":
		_hold_t -= dt
		if _hold_t <= 0.0:
			_hold_t = 0.15
			main.mw_look(_hold, 2.5)
