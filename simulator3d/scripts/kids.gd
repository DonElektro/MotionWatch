extends VBoxContainer
## 3D-3.69: the «Kinder» mode of the panel - big colourful buttons with pictures, short sentences in the «Du» form,
## the marmot of Motion Watch explains in a speech bubble, small sounds and confetti. Technical things are not here.
## Leaving to «Erwachsene» needs a little sum (main.ask_adult).

const UI = preload("res://scripts/ui_style.gd")
const Scenes = preload("res://scripts/scenes.gd")

var main
var bubble: Label
var marmot: Control
var _snd: AudioStreamPlayer
var _waves := {}
var _t := 0.0
var _fx: CanvasLayer = null

const C_PEOPLE := Color("#ff8a3d")
const C_ANIMAL := Color("#3fbf6b")
const C_WILD := Color("#8a6cff")
const C_SKY := Color("#2fa8ff")
const C_PLAY := Color("#ff4f8b")

const FRIENDLY := [["person", "Mensch", "Ein Mensch spaziert vorbei. Sieht Motion Watch ihn?"], ["child", "Kind", "Ein Kind kommt zum Spielen!"],
		["jogger", "Jogger", "Schnell, schnell! Ein Jogger rennt vorbei."], ["fox", "Fuchs", "Ein Fuchs schleicht herbei – psst!"],
		["deer", "Reh", "Ein Reh kommt aus dem Wald."], ["hare", "Hase", "Hoppel, hoppel – ein Hase!"], ["hedgehog", "Igel", "Ein kleiner Igel tapst vorbei."],
		["squirrel", "Eichhörnchen", "Ein Eichhörnchen sucht Nüsse."], ["cat", "Katze", "Miau! Eine Katze schaut vorbei."], ["dog", "Hund", "Wuff! Ein Hund kommt."],
		["cow", "Kuh", "Muuuh! Eine Kuh."], ["sheep", "Schaf", "Mäh! Ein Schaf."], ["horse", "Pferd", "Ein Pferd trabt vorbei."], ["ibex", "Steinbock", "Ein Steinbock aus den Bergen!"]]
const WILD := [["boar", "Wildschwein", "Ein Wildschwein wühlt im Boden!"], ["wolf", "Wolf", "Ein Wolf schleicht durch die Nacht …"],
		["lynx", "Luchs", "Ein Luchs – ganz leise!"]]


func _ready() -> void:
	add_theme_constant_override("separation", 12)
	_build()
	_snd = AudioStreamPlayer.new()
	_snd.volume_db = -8.0
	add_child(_snd)


func _build() -> void:
	for c in get_children():
		if c != _snd:
			c.queue_free()
	# the marmot with its speech bubble
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 8)
	add_child(top)
	marmot = Control.new()
	marmot.custom_minimum_size = Vector2(76, 86)
	marmot.draw.connect(_draw_marmot.bind(marmot))
	marmot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_child(marmot)
	var bp := PanelContainer.new()
	var bs := StyleBoxFlat.new()
	bs.bg_color = Color.WHITE
	bs.set_corner_radius_all(16)
	bs.set_content_margin_all(10)
	bp.add_theme_stylebox_override("panel", bs)
	bp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(bp)
	bubble = Label.new()
	bubble.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	bubble.add_theme_color_override("font_color", Color("#1b2430"))
	bubble.add_theme_font_size_override("font_size", 15)
	bubble.custom_minimum_size = Vector2(150, 0)
	bp.add_child(bubble)
	say("Hallo! Ich bin Murmli. Drück auf ein Bild – dann passiert etwas in der Welt!")
	# who comes to visit
	_title("Wer kommt zu Besuch?")
	var g := _grid()
	for v in FRIENDLY:
		_tile(g, v[1], C_PEOPLE if v[0] in ["person", "child", "jogger"] else C_ANIMAL, v[0], "", v[2], func(): main.visit(v[0]))
	if main.kids_scary:
		for v in WILD:
			_tile(g, v[1], C_WILD, v[0], "", v[2], func(): main.visit(v[0]))
	if main.kids_thief:
		_tile(g, "Schleicher", C_WILD, "", "mask", "Ein Schleicher will das Velo holen! Erwischt ihn Motion Watch?", func(): main.thief())
	_tile(g, "Alle nach Hause", Color("#6b7c93"), "", "broom", "Tschüss zusammen! Alle gehen nach Hause.", func(): main.clear_visitors())
	# weather and time
	_title("Wetter und Zeit")
	var w := _grid()
	_tile(w, "Tag", C_SKY, "", "sun", "Guten Morgen! Die Sonne scheint.", func(): main.set_hour(12.0))
	_tile(w, "Nacht", Color("#3b4a8f"), "", "moon", "Gute Nacht! Jetzt braucht Motion Watch Infrarot.", func(): main.set_hour(22.5))
	_tile(w, "Sonne", Color("#f5b82e"), "", "sun2", "Der Himmel ist ganz klar.", func(): main.weather = "clear"; main._settings_dirty = true)
	_tile(w, "Regen", C_SKY, "", "rain", "Plitsch, platsch – es regnet!", func(): main.weather = "rain"; main._settings_dirty = true)
	_tile(w, "Schnee", Color("#7fb8e6"), "", "snow", "Es schneit! Schau, wie alles weiss wird.", func(): main.weather = "snow"; main._settings_dirty = true)
	_tile(w, "Nebel", Color("#8a9bb0"), "", "fog", "Huch, Nebel! Kann Motion Watch noch etwas sehen?", func(): main.weather = "fog"; main._settings_dirty = true)
	# play
	_title("Spielen")
	var p := _grid()
	_tile(p, "Rover fahren", C_PLAY, "", "rover", "Du fährst den Rover! Pfeiltasten, Maus oder Controller.", func(): main.explore.set_on(not main.explore.on))
	_tile(p, "Versteckspiel", C_PLAY, "", "game", "Spielt mit dem Handy gegen die Kamera! Wer schafft es ungesehen ans Ziel?", func(): main.gamewiz.open_wiz())
	_tile(p, "Andere Welt", Color("#2bb3a3"), "", "world", "", func(): _next_world())
	_tile(p, "Was sieht die Kamera?", Color("#e0613f"), "", "camera", "So sieht Motion Watch die Welt.", func(): main.set_live(not main.live_on))
	# 3D-3.74: missions with stars
	_title("Missionen  ⭐ %d" % main.kids_stars)
	_mtitle = get_child(get_child_count() - 1)
	var mg := _grid()
	_tile(mg, "Finde den Fuchs", Color("#ff8a3d"), "fox", "", "Ein Fuchs hat sich versteckt! Fahr mit dem Rover zu ihm.", func(): _mission("fox"))
	_tile(mg, "Rover zum Velo", Color("#2fa8ff"), "", "rover", "Fahr den Rover ganz nah ans Velo!", func(): _mission("bike"))
	_tile(mg, "Tiere zählen", Color("#3fbf6b"), "", "star", "Wie viele Tiere siehst du? Schau gut hin!", func(): _mission("count"))
	_count_row = HBoxContainer.new()
	_count_row.add_theme_constant_override("separation", 6)
	_count_row.visible = false
	add_child(_count_row)


func _title(t: String) -> void:
	var l := Label.new()
	l.text = t
	l.add_theme_font_override("font", UI.heading_font())
	l.add_theme_font_size_override("font_size", 19)
	l.add_theme_color_override("font_color", Color("#ffd166"))
	add_child(l)


func _grid() -> GridContainer:
	var g := GridContainer.new()
	g.columns = 3
	g.add_theme_constant_override("h_separation", 8)
	g.add_theme_constant_override("v_separation", 8)
	add_child(g)
	return g


func _tile(parent: Control, text: String, col: Color, thumb: String, icon: String, tip: String, act: Callable) -> void:
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(112, 112)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for st in ["normal", "hover", "pressed"]:
		var s := StyleBoxFlat.new()
		s.bg_color = col.lightened(0.12) if st == "hover" else (col.darkened(0.15) if st == "pressed" else col)
		s.set_corner_radius_all(18)
		s.border_color = Color(1, 1, 1, 0.35 if st == "hover" else 0.15)
		s.set_border_width_all(3)
		s.shadow_color = Color(0, 0, 0, 0.35)
		s.shadow_size = 4
		s.shadow_offset = Vector2(0, 3)
		b.add_theme_stylebox_override(st, s)
	parent.add_child(b)
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_theme_constant_override("separation", 2)
	b.add_child(v)
	if thumb != "" and main.thumbs.has(thumb):
		var tr := TextureRect.new()
		tr.texture = main.thumbs[thumb]
		tr.custom_minimum_size = Vector2(80, 70)
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(tr)
	else:
		var d := Control.new()
		d.custom_minimum_size = Vector2(80, 70)
		d.mouse_filter = Control.MOUSE_FILTER_IGNORE
		d.draw.connect(_draw_icon.bind(d, icon if icon != "" else "star"))
		v.add_child(d)
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_override("font", UI.heading_font())
	l.add_theme_font_size_override("font_size", 14)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.45))
	l.add_theme_constant_override("outline_size", 4)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(l)
	b.mouse_entered.connect(func(): if tip != "": say(tip))
	b.pressed.connect(func():
		act.call()
		if tip != "":
			say(tip)
		_fun(b, col))


func say(t: String) -> void:
	if bubble != null:
		bubble.text = t


func _next_world() -> void:
	var L: Array = Scenes.LIST.filter(func(s): return s[0] != "ort")
	var i := 0
	for k in range(L.size()):
		if L[k][0] == main.scene:
			i = k
	var n: Array = L[(i + 1) % L.size()]
	main.set_scene(n[0])
	say("Willkommen in der Welt «%s»!" % n[1])


# ---- sound and confetti ------------------------------------------------------------------------------------------------
func _fun(b: Control, col: Color) -> void:
	if main.kids_sound:
		_play([523.0, 659.0, 784.0] if randf() < 0.5 else [659.0, 784.0, 1046.0])
	if _fx == null:
		_fx = CanvasLayer.new()                       # confetti on its own layer above the panel
		_fx.layer = 8
		main.add_child(_fx)
	var c0: Vector2 = b.get_global_rect().get_center()
	var cols := [Color("#ffd166"), Color("#ff4f8b"), Color("#4fc3f7"), Color("#3fbf6b"), col.lightened(0.4), Color.WHITE]
	for i in range(34):
		var r := ColorRect.new()
		r.color = cols[i % cols.size()]
		var sz := randf_range(5.0, 9.0)
		r.size = Vector2(sz, sz * 0.55)
		r.pivot_offset = r.size / 2.0
		r.position = c0
		r.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_fx.add_child(r)
		var up := Vector2.from_angle(randf_range(-PI * 0.95, -PI * 0.05)) * randf_range(60.0, 150.0)
		var tw := r.create_tween()
		tw.set_parallel(true)
		tw.tween_property(r, "position", c0 + up, 0.35).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(r, "rotation", randf_range(-9.0, 9.0), 1.2)
		tw.chain().tween_property(r, "position", c0 + up + Vector2(up.x * 0.4, randf_range(110.0, 200.0)), 0.85).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		tw.parallel().tween_property(r, "modulate:a", 0.0, 0.85).set_delay(0.3)
		tw.chain().tween_callback(r.queue_free)


func _play(notes: Array) -> void:
	var key := str(notes)
	if not _waves.has(key):
		var rate := 22050
		var data := PackedByteArray()
		var per := int(rate * 0.075)
		for f in notes:
			for i in range(per):
				var env := minf(1.0, float(i) / 200.0) * (1.0 - float(i) / per)
				var s := int(sin(TAU * float(f) * i / rate) * 9000.0 * env)
				data.append(s & 0xff)
				data.append((s >> 8) & 0xff)
		var w := AudioStreamWAV.new()
		w.format = AudioStreamWAV.FORMAT_16_BITS
		w.mix_rate = rate
		w.data = data
		_waves[key] = w
	_snd.stream = _waves[key]
	_snd.play()


func _process(dt: float) -> void:
	if is_visible_in_tree() and marmot != null:
		_t += dt
		marmot.queue_redraw()
	if _m != "":
		_mission_check()                                  # also while exploring (the panel is hidden then)


# ---- 3D-3.74: missions ----------------------------------------------------------------------------------------------------
var _m := ""
var _m_fox = null
var _m_n := 0
var _count_row: HBoxContainer
var _mtitle: Label


func _mission(k: String) -> void:
	_m = k
	_count_row.visible = false
	var rig: Vector3 = main.rig.global_position
	if k == "fox":
		var a := randf() * TAU
		var p: Vector3 = main.free_spot(rig + Vector3(cos(a), 0, sin(a)) * randf_range(12.0, 20.0), 0.6, true)
		if _m_fox != null and is_instance_valid(_m_fox):
			_m_fox.queue_free()
		_m_fox = main.spawn("fox", p, p + Vector3(randf_range(-3, 3), 0, randf_range(-3, 3)))
		_m_fox.speed = 0.3
		main.explore.set_on(true)
	elif k == "bike":
		main.explore.set_on(true)
	elif k == "count":
		_m_n = randi_range(2, 5)
		if main.is_dark():
			main.set_hour(12.0)                                  # counting in the dark is no fun
		var cam: Camera3D = main.cams[0]
		var fwd := -cam.global_transform.basis.z
		fwd.y = 0
		fwd = fwd.normalized()
		for i in range(_m_n):
			var side := fwd.rotated(Vector3.UP, randf_range(-0.45, 0.45))
			var p2: Vector3 = main.free_spot(rig + side * randf_range(6.0, 14.0), 0.6, true)
			var an = main.spawn(["hare", "fox", "deer", "sheep", "cat", "hedgehog"][randi() % 6], p2, p2 + Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)))
			an.speed = 0.05
		main.set_live(true)
		for c in _count_row.get_children():
			c.queue_free()
		for n in range(1, 7):
			var b := Button.new()
			b.text = str(n)
			b.custom_minimum_size = Vector2(44, 44)
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			b.add_theme_font_size_override("font_size", 20)
			b.pressed.connect(func():
				if n == _m_n:
					_won("Richtig, %d Tiere! Super gezählt!" % n, b)
				else:
					say("Hmm, nicht ganz. Schau nochmals genau hin!"))
			_count_row.add_child(b)
		_count_row.visible = true


func _mission_check() -> void:
	var rig: Vector3 = main.rig.global_position
	if _m == "fox" and _m_fox != null and is_instance_valid(_m_fox):
		var d := Vector2(rig.x - _m_fox.position.x, rig.z - _m_fox.position.z).length()
		if d < 4.0:
			_won("Gefunden! Der Fuchs staunt.", self)
	elif _m == "bike":
		var bk: Vector3 = main.obj.get("bike", Vector3.ZERO)
		if Vector2(rig.x - bk.x, rig.z - bk.z).length() < 3.0:
			_won("Geschafft! Der Rover steht beim Velo.", self)


func _won(text: String, at: Control) -> void:
	_m = ""
	main.kids_stars += 1
	main._settings_dirty = true
	_count_row.visible = false
	say("⭐ " + text + " Du hast jetzt %d Sterne." % main.kids_stars)
	if not is_visible_in_tree():                          # exploring: the panel is hidden, so say it in the world
		main._say("⭐ " + text, main.rig.global_position + Vector3(0, 1.5, 0), Color("#ffd166"), main.HELPER_LAYER)
	if _mtitle != null and is_instance_valid(_mtitle):
		_mtitle.text = "Missionen  ⭐ %d" % main.kids_stars
	for i in range(3):
		_fun(at if at != self else marmot, Color("#ffd166"))
		await get_tree().create_timer(0.25).timeout


# ---- drawings ----------------------------------------------------------------------------------------------------------
func _draw_marmot(d: Control) -> void:
	var bob := sin(_t * 2.2) * 2.0
	var c := Vector2(38, 52 + bob)
	var fur := Color("#a86f3e")
	var belly := Color("#e3b98a")
	d.draw_circle(c + Vector2(0, 14), 26, fur)                   # body
	d.draw_circle(c + Vector2(0, 18), 16, belly)
	d.draw_circle(c + Vector2(0, -16), 21, fur)                  # head
	d.draw_circle(c + Vector2(-15, -32), 6, fur)                 # ears
	d.draw_circle(c + Vector2(15, -32), 6, fur)
	d.draw_circle(c + Vector2(-15, -32), 3, belly)
	d.draw_circle(c + Vector2(15, -32), 3, belly)
	d.draw_circle(c + Vector2(0, -8), 10, belly)                 # snout
	var blink := fmod(_t, 3.6) < 0.12
	for sx in [-8.0, 8.0]:
		if blink:
			d.draw_line(c + Vector2(sx - 3, -20), c + Vector2(sx + 3, -20), Color("#1b1b1b"), 2.0)
		else:
			d.draw_circle(c + Vector2(sx, -20), 3.6, Color("#1b1b1b"))
			d.draw_circle(c + Vector2(sx + 1.2, -21.2), 1.2, Color.WHITE)
	d.draw_circle(c + Vector2(0, -12), 3.2, Color("#3a2416"))      # nose
	d.draw_rect(Rect2(c + Vector2(-3, -6), Vector2(6, 6)), Color.WHITE)   # teeth
	d.draw_line(c + Vector2(0, -6), c + Vector2(0, 0), Color("#cccccc"), 1.0)
	var wave := sin(_t * 5.0) * 0.4
	d.draw_line(c + Vector2(20, 8), c + Vector2(30, -6) + Vector2(wave * 10, 0), fur, 7.0)   # waving paw
	d.draw_circle(c + Vector2(30, -6) + Vector2(wave * 10, 0), 5, fur)


func _draw_icon(d: Control, kind: String) -> void:
	var c := d.size / 2.0
	var W := Color.WHITE
	match kind:
		"sun", "sun2":
			for i in range(8):
				var a := TAU * i / 8.0 + _t * 0.0
				d.draw_line(c + Vector2.from_angle(a) * 20, c + Vector2.from_angle(a) * 30, Color("#fff3b0"), 4.0)
			d.draw_circle(c, 17, Color("#ffe066"))
		"moon":
			d.draw_circle(c, 22, Color("#fff3b0"))
			d.draw_circle(c + Vector2(9, -7), 19, Color("#3b4a8f"))
			for s in [Vector2(-24, -20), Vector2(22, 18), Vector2(-18, 22)]:
				d.draw_circle(c + s, 2.5, W)
		"rain", "snow", "fog":
			d.draw_circle(c + Vector2(-10, -4), 13, W)
			d.draw_circle(c + Vector2(6, -10), 16, W)
			d.draw_circle(c + Vector2(18, -2), 11, W)
			d.draw_rect(Rect2(c + Vector2(-22, -4), Vector2(42, 12)), W)
			if kind == "rain":
				for x in [-14.0, -2.0, 10.0]:
					d.draw_line(c + Vector2(x, 14), c + Vector2(x - 4, 26), Color("#cfe9ff"), 3.0)
			elif kind == "snow":
				for x in [-14.0, -2.0, 10.0]:
					d.draw_circle(c + Vector2(x, 20), 3.5, W)
			else:
				for y in [14.0, 22.0]:
					d.draw_line(c + Vector2(-24, y), c + Vector2(22, y), Color(1, 1, 1, 0.8), 4.0)
		"rover":
			d.draw_rect(Rect2(c + Vector2(-26, 2), Vector2(52, 14)), Color("#2b2b2b"))
			for x in [-18.0, -6.0, 6.0, 18.0]:
				d.draw_circle(c + Vector2(x, 16), 6, Color("#555555"))
			d.draw_line(c + Vector2(0, 2), c + Vector2(0, -22), W, 4.0)
			d.draw_circle(c + Vector2(0, -24), 8, W)
			d.draw_circle(c + Vector2(0, -24), 4, Color("#e8590c"))
		"game":
			d.draw_rect(Rect2(c + Vector2(-26, -12), Vector2(52, 26)), W)
			d.draw_circle(c + Vector2(-26, 1), 13, W)
			d.draw_circle(c + Vector2(26, 1), 13, W)
			d.draw_rect(Rect2(c + Vector2(-22, -2), Vector2(14, 4)), Color("#ff4f8b"))
			d.draw_rect(Rect2(c + Vector2(-17, -7), Vector2(4, 14)), Color("#ff4f8b"))
			d.draw_circle(c + Vector2(15, -3), 3.5, Color("#ff4f8b"))
			d.draw_circle(c + Vector2(22, 3), 3.5, Color("#3fbf6b"))
		"world":
			d.draw_circle(c, 24, Color("#4fc3f7"))
			d.draw_circle(c + Vector2(-8, -6), 9, Color("#3fbf6b"))
			d.draw_circle(c + Vector2(10, 8), 8, Color("#3fbf6b"))
			d.draw_circle(c + Vector2(8, -12), 5, Color("#3fbf6b"))
		"camera":
			d.draw_rect(Rect2(c + Vector2(-24, -14), Vector2(48, 32)), W)
			d.draw_rect(Rect2(c + Vector2(-10, -20), Vector2(20, 8)), W)
			d.draw_circle(c + Vector2(0, 2), 11, Color("#1b2430"))
			d.draw_circle(c + Vector2(0, 2), 6, Color("#e8590c"))
		"broom":
			d.draw_line(c + Vector2(16, -26), c + Vector2(-4, 6), Color("#c8a26b"), 5.0)
			d.draw_colored_polygon(PackedVector2Array([c + Vector2(-14, 2), c + Vector2(6, 10), c + Vector2(-4, 30), c + Vector2(-26, 22)]), Color("#ffd166"))
		"mask":
			d.draw_circle(c + Vector2(0, -2), 22, Color("#ffcf9e"))
			d.draw_rect(Rect2(c + Vector2(-22, -12), Vector2(44, 12)), Color("#1b2430"))
			d.draw_circle(c + Vector2(-9, -6), 4, W)
			d.draw_circle(c + Vector2(9, -6), 4, W)
			d.draw_arc(c + Vector2(0, 6), 8, 0.3, PI - 0.3, 12, Color("#7a3b2e"), 3.0)
		_:
			d.draw_circle(c, 18, Color("#ffd166"))

