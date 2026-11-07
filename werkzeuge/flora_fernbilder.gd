extends SceneTree
## Ferne-Bilder für «Flora und Fauna» Paket 1 (simulator3d/scripts/baeume.gd): baut je Art einen Baum mit genau dem Code
## des Simulators (Stufe Hoch), rendert ihn von der Seite (orthogonal, nur Umgebungslicht) in drei Durchgängen
## (alles / nur Blätter / nur Rinde) und schreibt texturen/flora_fern_<art>.png:
##   R = Helligkeit der Blätter (zur Farbe der Krone, /2), G = 1 Blätter vorne, B = Helligkeit der Rinde (/2), A = Deckung.
## Gibt die Rahmen-Grösse (Breite, Höhe in m) aus – die gehört nach baeume.gd (FERN). Mit «--grafik normal» starten.
##   cd simulator3d && HOME=<test-home> xvfb-run -a -s "-screen 0 1280x720x24" <godot> --path . -s "$PWD/../werkzeuge/flora_fernbilder.gd" \
##       -- --no-update [--aus <ordner>]   (ohne --aus: texturen/)

const ARTEN := {"fichte": [320, 512, 4], "buche": [448, 448, 7], "hasel": [448, 320, 3], "kiefer": [320, 512, 5],
		"birke": [240, 512, 6], "eiche": [576, 448, 8], "tanne": [320, 512, 4], "laerche": [320, 512, 9], "ahorn": [448, 448, 11],
		"esche": [448, 448, 12], "obst": [448, 384, 13], "holunder": [448, 320, 14]}   # Pixel, Startwert

var main
var out := "res://texturen/"


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--aus")
	if i >= 0:
		out = args[i + 1]
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	_run.call_deferred()


func _frames(n: int) -> void:
	for k in range(n):
		await process_frame


func _shot(vp: SubViewport) -> Image:
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	return vp.get_texture().get_image()


func _show(holder: Node, names: Array, kern: bool) -> void:
	for n in holder.find_children("*", "GeometryInstance3D", true, false):
		var g := n as GeometryInstance3D
		if g.layers != 1:
			g.visible = false
			continue
		if g.has_meta("flora_teil"):
			g.visible = names.has(str(g.get_meta("flora_teil")))
		elif g is MeshInstance3D and g.material_override is ShaderMaterial:
			g.visible = kern                                   # the cores of the crown parts
		else:
			g.visible = false


func _lum(c: Color) -> float:
	var l := c                                          # (sRGB, like the colour of the crown)
	return l.r * 0.2126 + l.g * 0.7152 + l.b * 0.0722


func _run() -> void:
	await create_timer(3.0).timeout
	var Flora = load("res://scripts/flora.gd")
	var Baeume = load("res://scripts/baeume.gd")
	var Veg = load("res://scripts/vegetation.gd")
	Flora.modus = "hoch"
	main.wind = 0.0
	for fm in main.foliage_mats:
		fm.set_shader_parameter("wind", 0.0)
	var sc = main.scenes
	var old_root: Node3D = sc.root
	for art in ARTEN:
		var px: Array = ARTEN[art]
		var vp := SubViewport.new()
		vp.size = Vector2i(px[0], px[1])
		vp.own_world_3d = true
		vp.transparent_bg = true
		vp.msaa_3d = Viewport.MSAA_4X
		vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		root.add_child(vp)
		var we := WorldEnvironment.new()
		var env := Environment.new()
		env.background_mode = Environment.BG_CLEAR_COLOR
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.ambient_light_color = Color(1, 1, 1)
		env.ambient_light_energy = 1.0
		env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
		env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
		we.environment = env
		vp.add_child(we)
		var holder := Node3D.new()
		vp.add_child(holder)
		sc.root = holder
		sc.rng.seed = int(px[2])
		Baeume.force = art
		match art:
			"fichte", "tanne", "laerche":
				sc.tree(holder, Vector3.ZERO, 1.0, 1)
			"buche", "ahorn", "esche":
				sc.tree(holder, Vector3.ZERO, 1.0, 0)
			"hasel":
				Veg.bush(sc, holder, Vector3.ZERO, "hasel", 1.0)
			"holunder":
				Veg.bush(sc, holder, Vector3.ZERO, "beeren", 1.0)
			_:
				Veg.tree(sc, holder, Vector3.ZERO, art, 1.0)
		Baeume.force = ""
		await _frames(3)                                           # Flora flushes on the next frame
		var info: Dictionary = Baeume.last
		var h: float = info["h"]
		var w: float = h * float(px[0]) / float(px[1])
		var foot: Vector3 = holder.get_child(0).position if holder.get_child_count() > 0 else Vector3.ZERO
		var cam := Camera3D.new()
		cam.projection = Camera3D.PROJECTION_ORTHOGONAL
		cam.size = h
		cam.keep_aspect = Camera3D.KEEP_HEIGHT
		cam.cull_mask = 1
		cam.near = 0.1
		cam.far = 80.0
		vp.add_child(cam)
		cam.position = foot + Vector3(0, h * 0.5, 30.0)
		cam.current = true
		var crown_l := _lum(info["crown"].get_shader_parameter("color"))
		var bc: Color = Baeume.RINDE[art]
		var bark_l := bc.r * 0.2126 + bc.g * 0.7152 + bc.b * 0.0722
		_show(holder, ["rinde", "baum_karten"], true)
		var ia := await _shot(vp)
		_show(holder, ["baum_karten"], true)
		var ib := await _shot(vp)
		_show(holder, ["rinde"], false)
		var ic := await _shot(vp)
		var img := Image.create(px[0], px[1], false, Image.FORMAT_RGBA8)
		for y in range(px[1]):
			for x in range(px[0]):
				var a := ia.get_pixel(x, y)
				var b := ib.get_pixel(x, y)
				var c := ic.get_pixel(x, y)
				if a.a < 0.5 and c.a < 0.5:
					img.set_pixel(x, y, Color(0.4, 1.0, 0.0, 0.0))
					continue
				var bark_front := c.a > 0.5 and (b.a < 0.5 or Vector3(a.r - c.r, a.g - c.g, a.b - c.b).length() < 0.03)
				var leaf_src := a if not bark_front else b
				var r := clampf(_lum(leaf_src) / crown_l / 2.0, 0.0, 1.0) if leaf_src.a > 0.5 else 0.4
				var bb := clampf(_lum(c) / bark_l / 2.0, 0.02, 1.0) if c.a > 0.5 else 0.0
				img.set_pixel(x, y, Color(r, 0.0 if bark_front else 1.0, bb, 1.0 if a.a > 0.5 else 0.0))
		Baeume._bleed(img)
		var path := out + "flora_fern_%s.png" % art
		img.save_png(ProjectSettings.globalize_path(path) if path.begins_with("res://") else path)
		print("FERN ", art, " w=%.2f h=%.2f -> %s   (baeume.gd FERN: \"%s\": Vector2(%.2f, %.2f))" % [w, h, path, art, w, h])
		for ch in holder.get_children():
			ch.free()
		vp.queue_free()
	sc.root = old_root
	quit(0)
