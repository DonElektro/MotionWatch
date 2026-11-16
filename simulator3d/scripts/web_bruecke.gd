extends Node
## Browser-Demo, nur mit «?test=1» in der Adresse (web.gd legt den Knoten dann an): die Steuerung (main.control, sonst nur über
## HTTP /control) aus JavaScript, für die Tests in Chromium (werkzeuge/sim_web_handy_test.py):
##   window.mwControl('{"action":"handy","do":"info"}')  -> Antwort als JSON in window.mwLast
## Dazu {"action": "webdiag"}: was die 3D-Ansicht gerade zeichnet (Kamera, sichtbare Körper, Auflösung, Lichter); mit «probe»,
## «iso», «fog», «env», «shadows», «lights», «fx» zum Ausprobieren. {"action": "webbisect"}: sucht mit einem roten Würfel vor der
## Kamera, welche Knoten der Welt das Zeichnen verhindern (so wurde 15.11.2026 die Grenze von 1000 Dingen gefunden, Ausgabe
## «BISECT …» in der Konsole); {"action": "webbisect", "nur_probe": true}: nur «Würfel zu sehen?» -> window.mwProbe.
## Ohne «?test=1» gibt es diesen Knoten nicht.

var main
var _cb                                   # JavaScriptObject - muss gehalten werden, sonst ist der Rückruf weg
var _win


func _ready() -> void:
	if not OS.has_feature("web"):
		return
	_win = JavaScriptBridge.get_interface("window")
	_cb = JavaScriptBridge.create_callback(_on_js)
	_win.mwControl = _cb
	_win.mwLast = "{}"
	print("web: Testbrücke bereit (window.mwControl)")


func _on_js(args: Array) -> void:
	var d = JSON.parse_string(str(args[0])) if args.size() > 0 else null
	var r: Dictionary = {"ok": false, "error": "bad json"}
	if d is Dictionary:
		if str(d.get("action", "")) == "webbisect":     # nur_probe: nur «ist der rote Würfel zu sehen?» -> window.mwProbe
			_bisect(bool(d.get("nur_probe", false)))
			r = {"ok": true, "started": true}
		else:
			r = diag(d) if str(d.get("action", "")) == "webdiag" else main.control(d)
	_win.mwLast = JSON.stringify(r)


# ---- Suche: welcher Knoten der Welt verhindert, dass im Browser Körper gezeichnet werden? --------------------------------
var _sv: SubViewport
var _probe: MeshInstance3D


func _probe_ok() -> bool:
	for i in range(4):
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var img := _sv.get_texture().get_image()
	var c := img.get_pixel(img.get_width() / 2, img.get_height() / 2)
	return c.r > 0.8 and c.g < 0.3 and c.b < 0.3


func _cands(parent: Node, cam: Node) -> Array:
	var out := []
	for c in parent.get_children():
		if c == _sv or c == _probe or c == self or not (c is Node3D) or (c as Node3D).is_ancestor_of(cam) or c == cam:
			continue
		if (c as Node3D).visible:
			out.append(c)
	return out


func _set_vis(arr: Array, v: bool) -> void:
	for n in arr:
		if is_instance_valid(n):
			(n as Node3D).visible = v


func _ddmin(lst: Array) -> Array:
	"""lst (alle aus) zusammen an = kaputt: Stücke weglassen, solange es kaputt bleibt"""
	var n := 2
	while lst.size() >= 2:
		var k := ceili(float(lst.size()) / n)
		var reduced := false
		for i in range(0, lst.size(), k):
			var rest := lst.slice(0, i) + lst.slice(i + k)
			_set_vis(rest, true)
			var ok := await _probe_ok()
			_set_vis(rest, false)
			if not ok:
				lst = rest
				n = maxi(n - 1, 2)
				reduced = true
				var nm := []
				for x in lst:
					nm.append(str(x.name) + ":" + x.get_class() + (":" + x.get_script().resource_path.get_file() if x.get_script() != null else "") + ":" + str(x.find_children("*", "Light3D", true, false).size()) + "L" + str(x.find_children("*", "GeometryInstance3D", true, false).size()) + "G")
				print("BISECT ddmin: ", lst.size(), " ", nm.slice(0, 60))
				break
		if not reduced:
			if n >= lst.size():
				break
			n = mini(n * 2, lst.size())
	return lst


func _bisect(only_probe := false) -> void:
	var cam: Camera3D = main.get_viewport().get_camera_3d()
	_sv = SubViewport.new()
	_sv.size = Vector2i(64, 64)
	_sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var c3 := Camera3D.new()
	c3.transform = cam.global_transform
	c3.cull_mask = 0xFFFFF
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color.BLACK
	c3.environment = e
	_sv.add_child(c3)
	main.add_child(_sv)
	_probe = MeshInstance3D.new()
	_probe.mesh = BoxMesh.new()
	var m := StandardMaterial3D.new()
	m.albedo_color = Color.RED
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_probe.material_override = m
	main.add_child(_probe)
	_probe.global_position = cam.global_position - cam.global_transform.basis.z * 2.0
	var seen := await _probe_ok()
	print("BISECT start: probe sichtbar = ", seen)
	if only_probe:
		_win.mwProbe = "true" if seen else "false"
		_probe.queue_free()
		_sv.queue_free()
		return
	var parent: Node = main
	var path := []
	for depth in range(8):
		var cs := _cands(parent, cam)
		if cs.is_empty():
			break
		_set_vis(cs, false)
		var ok_all := await _probe_ok()
		print("BISECT %s: %d Kinder aus -> sichtbar %s" % [str(parent.get_path()), cs.size(), ok_all])
		if not ok_all:
			_set_vis(cs, true)
			print("BISECT: nicht unter ", parent.get_path())
			break
		var lst := cs.duplicate()
		while lst.size() > 1:                       # nur die erste Hälfte an: geht es dann noch nicht?
			var a := lst.slice(0, lst.size() / 2)
			var b := lst.slice(lst.size() / 2)
			_set_vis(a, true)
			var ok_a := await _probe_ok()
			_set_vis(a, false)
			if not ok_a:
				lst = a
			else:
				_set_vis(b, true)
				var ok_b := await _probe_ok()
				_set_vis(b, false)
				if not ok_b:
					lst = b
				else:
					print("BISECT: nur zusammen (", a.size(), " + ", b.size(), ") - verkleinern")
					lst = await _ddmin(lst)
					var names := []
					for n in lst:
						names.append(str(n.name) + ":" + n.get_class() + (":" + n.get_script().resource_path.get_file() if n.get_script() != null else ""))
					print("BISECT kleinste Menge (", lst.size(), "): ", names.slice(0, 40))
					var nlights := 0
					var ngeo := 0
					for n in lst:
						for x in n.find_children("*", "Light3D", true, false) + ([n] if n is Light3D else []):
							nlights += 1
						for x in n.find_children("*", "GeometryInstance3D", true, false) + ([n] if n is GeometryInstance3D else []):
							ngeo += 1
					print("BISECT darin: Lichter ", nlights, ", Körper ", ngeo)
					lst = []
					break
		_set_vis(cs, true)
		if lst.size() != 1:
			break
		var bad: Node = lst[0]
		path.append(str(bad.get_path()) + " (" + bad.get_class() + (" " + bad.get_script().resource_path.get_file() if bad.get_script() != null else "") + ")")
		print("BISECT Schuldiger: ", path[-1])
		parent = bad
	print("BISECT Ende: ", path)
	if parent is GeometryInstance3D:
		var gi := parent as GeometryInstance3D
		var info := {"class": gi.get_class(), "mat_override": str(gi.material_override)}
		if gi is MeshInstance3D and (gi as MeshInstance3D).mesh != null:
			var me: Mesh = (gi as MeshInstance3D).mesh
			info["mesh"] = str(me)
			info["surfaces"] = me.get_surface_count()
			for s in range(me.get_surface_count()):
				var sm = me.surface_get_material(s)
				info["mat%d" % s] = str(sm) + (" " + (sm as ShaderMaterial).shader.resource_path if sm is ShaderMaterial and (sm as ShaderMaterial).shader != null else "")
		print("BISECT Körper: ", info)


func diag(d := {}) -> Dictionary:
	var vp: Viewport = main.get_viewport()
	var cam: Camera3D = vp.get_camera_3d()
	if d.has("fog"):
		main.env.fog_enabled = bool(d["fog"])
	if d.has("glow"):
		main.env.glow_enabled = bool(d["glow"])
	if d.has("env") and cam != null:
		cam.environment = null if not bool(d["env"]) else cam.environment
		if not bool(d["env"]):
			for c in main.get_children():
				if c is WorldEnvironment:
					(c as WorldEnvironment).environment = null
	if d.has("sun_shadow"):
		main.sun.shadow_enabled = bool(d["sun_shadow"])
	var lights := {"n": 0, "shadow": 0, "omni": 0, "spot": 0, "dir": 0}
	var todo3: Array = [main]
	while not todo3.is_empty():
		var x3: Node = todo3.pop_back()
		todo3.append_array(x3.get_children())
		if x3 is Light3D and (x3 as Light3D).is_visible_in_tree():
			lights["n"] += 1
			lights["omni" if x3 is OmniLight3D else ("spot" if x3 is SpotLight3D else "dir")] += 1
			if (x3 as Light3D).shadow_enabled:
				lights["shadow"] += 1
				if d.has("shadows") and not bool(d["shadows"]):
					(x3 as Light3D).shadow_enabled = false
			if d.has("lights") and not bool(d["lights"]) and not (x3 is DirectionalLight3D):
				(x3 as Light3D).visible = false
	var fx := []                                       # Ebenen mit Bild-Shadern über der 3D-Ansicht (lesen den Bildschirm)
	var todo2: Array = [main]
	while not todo2.is_empty():
		var x2: Node = todo2.pop_back()
		if x2 is SubViewport:
			continue
		todo2.append_array(x2.get_children())
		if x2 is CanvasItem and (x2 as CanvasItem).material is ShaderMaterial and (x2 as CanvasItem).is_visible_in_tree():
			var sh: Shader = ((x2 as CanvasItem).material as ShaderMaterial).shader
			fx.append(str(x2.get_path()).right(60) + " " + (sh.resource_path if sh != null else "?"))
			if d.has("fx") and not bool(d["fx"]):
				(x2 as CanvasItem).visible = false
	if d.has("iso"):                                   # eigene Welt in einer SubViewport: geht 3D hier überhaupt?
		var sv := SubViewport.new()
		sv.size = Vector2i(200, 200)
		sv.own_world_3d = str(d["iso"]) != "world"          # "world": dieselbe Welt wie die Ansicht, eigene Kamera
		sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		var c3 := Camera3D.new()
		sv.add_child(c3)
		c3.position = Vector3(0, 0, 4)
		if not sv.own_world_3d and cam != null:
			c3.transform = cam.global_transform
			c3.cull_mask = 1
			if str(d.get("isoenv", "")) == "clear":
				var e := Environment.new()
				e.background_mode = Environment.BG_COLOR
				e.background_color = Color.DARK_GREEN
				c3.environment = e
		var bx := MeshInstance3D.new()
		bx.mesh = BoxMesh.new()
		var bm := StandardMaterial3D.new()
		bm.albedo_color = Color.MAGENTA
		bm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		bx.material_override = bm
		sv.add_child(bx)
		var cl := CanvasLayer.new()
		cl.layer = 100
		var tr := TextureRect.new()
		tr.texture = sv.get_texture()
		tr.position = Vector2(float(d.get("x", 0)), 300)
		cl.add_child(tr)
		main.add_child(sv)
		main.add_child(cl)
	if d.has("probe") and cam != null:               # zwei Würfel vor der Kamera: unschattiert rot, schattiert blau
		for i in range(2):
			var mi := MeshInstance3D.new()
			mi.mesh = BoxMesh.new()
			var m := StandardMaterial3D.new()
			m.albedo_color = Color.RED if i == 0 else Color.BLUE
			if i == 0:
				m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				m.no_depth_test = true
				m.render_priority = 100
			mi.material_override = m
			main.add_child(mi)
			mi.global_position = cam.global_position - cam.global_transform.basis.z * 4.0 + cam.global_transform.basis.x * (i - 0.5) * 2.0
	var n_geo := 0
	var n_vis := 0
	var todo: Array = [main]
	while not todo.is_empty():
		var x: Node = todo.pop_back()
		todo.append_array(x.get_children())
		if x is GeometryInstance3D:
			n_geo += 1
			if (x as GeometryInstance3D).is_visible_in_tree():
				n_vis += 1
	var w := get_tree().root
	return {"ok": true, "fps": Engine.get_frames_per_second(), "scene": main.scene, "quality": main.quality,
		"lite": main.get("lite_why"), "scale3d": vp.scaling_3d_scale, "window": [w.size.x, w.size.y],
		"content_scale": w.content_scale_factor, "dpr": DisplayServer.screen_get_scale(),
		"cam": {"near": cam.near, "far": cam.far, "pos": [cam.global_position.x, cam.global_position.y, cam.global_position.z],
			"cull": cam.cull_mask} if cam != null else null,
		"geo": n_geo, "geo_visible": n_vis, "fx": fx, "lights": lights,
		"draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		"objects": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
		"prims": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)}
