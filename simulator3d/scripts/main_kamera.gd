extends Object
## Teil von main.gd (Vorschlag 24 «main.gd zerlegen»): die Kamera-Ausgabe: Linsen-Bild, Wärmebild-Abgleich, Bilder für MoveEye (JPEG), die Ansicht als Bild für die Fernbedienung.
## main.gd lädt diesen Teil erst beim ersten Aufruf (_mod) und leitet seine Funktionen weiter: main.xyz bleibt gleich.
## Hier steht «main.» vor allem, was zu main.gd gehört.

var main                              # main.gd
const Quality := preload("res://scripts/quality.gd")


func _build_lens() -> void:
	"""a quad right in front of camera 0 and 1 (own layer 32 / 64): grain, dark corners, raindrops (shaders/lens.gdshader).
	Insects round the head at night when a light is on (CPU particles, only the normal cameras see them, not the thermal one)."""
	var sh: Shader = load("res://shaders/lens.gdshader")
	for i in range(2):
		var cam: Camera3D = main.cams[i]
		var lay := 32 if i == 0 else 64
		cam.cull_mask = 1 | lay
		var dist := 0.12
		var w = 2.0 * dist * tan(deg_to_rad(main.CAM_FOV[i]) / 2.0) * 1.04
		var hgt = w * float(main.CAM_H[i]) / float(main.CAM_W[i]) * 1.04
		var q := MeshInstance3D.new()
		var qm := QuadMesh.new()
		qm.size = Vector2(w, hgt)
		q.mesh = qm
		q.position = Vector3(0, 0, -dist)
		q.layers = lay
		q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var m := ShaderMaterial.new()
		m.shader = sh
		m.set_shader_parameter("res", Vector2(main.CAM_W[i], main.CAM_H[i]))
		q.material_override = m
		cam.add_child(q)
		main.lens_mats.append(m)
		var eq := MeshInstance3D.new()                       # exposure: a bit behind the lens quad, so it is drawn first
		var eqm := QuadMesh.new()
		eqm.size = Vector2(w, hgt) * 1.05
		eq.mesh = eqm
		eq.position = Vector3(0, 0, -dist * 1.05)
		eq.layers = lay
		eq.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var em := ShaderMaterial.new()
		em.shader = load("res://shaders/expo.gdshader")
		eq.material_override = em
		cam.add_child(eq)
		main.expo_mats.append(em)
		var fq := MeshInstance3D.new()                       # 3D-3.94: the camera effects - between exposure and lens (drawn in that order)
		var fqm := QuadMesh.new()
		fqm.size = Vector2(w, hgt) * 1.02
		fq.mesh = fqm
		fq.position = Vector3(0, 0, -dist * 1.02)
		fq.layers = lay
		fq.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var fm := ShaderMaterial.new()
		fm.shader = load("res://shaders/camfx.gdshader")
		fm.set_shader_parameter("res", Vector2(main.CAM_W[i], main.CAM_H[i]))
		fq.material_override = fm
		cam.add_child(fq)
		main.camfx_mats.append(fm)
	main.insects = CPUParticles3D.new()
	main.insects.amount = 28
	main.insects.lifetime = 2.5
	main.insects.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	main.insects.emission_sphere_radius = 0.7
	main.insects.direction = Vector3(0, 0, -1)
	main.insects.spread = 180.0
	main.insects.gravity = Vector3.ZERO
	main.insects.initial_velocity_min = 0.3
	main.insects.initial_velocity_max = 1.4
	main.insects.orbit_velocity_min = -1.5
	main.insects.orbit_velocity_max = 1.5
	main.insects.damping_min = 0.0
	main.insects.damping_max = 0.8
	main.insects.angular_velocity_min = -200.0
	main.insects.angular_velocity_max = 200.0
	var im := SphereMesh.new()
	im.radius = 0.012
	im.height = 0.02
	im.radial_segments = 4
	im.rings = 2
	var imm := StandardMaterial3D.new()
	imm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	imm.albedo_color = Color(0.95, 0.93, 0.85)
	im.material = imm
	main.insects.mesh = im
	main.insects.position = Vector3(0, 0.2, -0.9)          # in front of the head, in its light
	main.insects.emitting = false
	main.insects.layers = 1
	main.head_pitch.add_child(main.insects)


func _calibrate_thermal() -> void:
	"""3D-4.26: measure how the renderer stores colours (a ramp 128 … 255 in a 16 × 8 picture: linear, sRGB, squeezed?) and
	build th_inv; then check with a surface of exactly 20 °C"""
	var vp := SubViewport.new()
	vp.size = Vector2i(16, 16)
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	main.add_child(vp)
	var cam := Camera3D.new()
	cam.cull_mask = 8
	cam.environment = main.th_env
	vp.add_child(cam)
	cam.global_transform = Transform3D(Basis(), Vector3(0, -500, 3))
	var rq := MeshInstance3D.new()                       # the ramp: pixel x + 16 y shows 128 + that (written like the code)
	rq.mesh = main.box(40, 40, 0.1)
	var rs := Shader.new()
	rs.code = "shader_type spatial;\nrender_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;\nuniform float srgb = 0.0;\n" + \
			"void fragment() { vec3 c = vec3(min(255.0, 128.0 + floor(FRAGCOORD.x) + 16.0 * floor(FRAGCOORD.y)) / 255.0);\n" + \
			"if (srgb > 0.5) { c = mix(c / 12.92, pow((c + vec3(0.055)) / 1.055, vec3(2.4)), step(vec3(0.04045), c)); }\nALBEDO = c; }"
	var rm := ShaderMaterial.new()
	rm.shader = rs
	rq.material_override = rm
	rq.layers = 8
	main.add_child(rq)
	rq.global_position = Vector3(0, -500, 0)
	var bg_was = main.th_env.background_color
	main._make_lut(false)
	var ok := false
	for srgb in [false, true]:
		rm.set_shader_parameter("srgb", 1.0 if srgb else 0.0)
		vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		var ri := vp.get_texture().get_image()
		if ri == null or ri.is_empty():
			break
		var inv := PackedInt32Array()
		inv.resize(256)
		inv.fill(-1)
		var distinct := true
		for k in range(128):
			var st := roundi(ri.get_pixel(k % 16, k / 16).r * 255.0)
			if inv[st] >= 0:
				distinct = false
			inv[st] = 128 + k
		if distinct:
			var last := 128
			for b2 in range(256):                         # bytes the ramp never gave: the nearest below (or 128)
				if inv[b2] >= 0:
					last = inv[b2]
				else:
					inv[b2] = last
			main.th_inv = inv
			main._make_lut(srgb)
			ok = true
			break
	rq.queue_free()
	var q := MeshInstance3D.new()                        # the check: 20 °C in the middle, background in the corners
	q.mesh = main.box(4, 4, 0.1)
	q.material_override = main.tmat_fixed(20.0)
	q.layers = 8
	main.add_child(q)
	q.global_position = Vector3(0, -500, 0)
	q.scale = Vector3(0.5, 0.5, 1)
	main.th_env.background_color = Color(0.25, 0.25, 0.25)
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	if img != null and not img.is_empty():
		var rb := img.get_pixel(0, 0).r                 # background colour 0.25 comes back as ...
		main.th_bg_raw = abs(rb - 0.25) < 0.04
		var got = main._th_read(img, 8, 8)
		print("thermal calibration: 20.00 °C -> %.2f °C (%s%s), background %.3f -> %s" % [got, "sRGB" if main.th_srgb else "linear",
				"" if ok else ", ramp not clean", rb, "raw" if main.th_bg_raw else "converted"])
	main.th_env.background_color = bg_was
	q.queue_free()
	vp.queue_free()


func _capture(i: int) -> void:
	main.capturing = true
	main.last_cap[i] = main.now()
	var L: Dictionary = main.mw.get("lights", {})
	var dark = main.is_dark()
	main.ir_light.spot_range = main.ir_range
	main.ir_light.light_energy = 9.0 if (i == 0 and main.ir_on()) else 0.0   # infrared: only the NoIR camera sees it
	if i == 0:
		var grey: bool = main.ir_on() and dark and not main.white_light.light_energy > 0.0   # infrared picture: black and white
		main.cams[0].environment = (main.night_envs[0] if grey else main.night_envs[1]) if dark and main.night_envs[0] != null else null
	if i == 1:
		main.cams[1].environment = main.night_envs[1] if dark and main.night_envs[1] != null else null    # little light: little colour
	if i < 2 and main.expo_mats.size() > i:
		var ex: float = main.NIGHT_SCALE * main.gain[i] if dark else 1.0
		if i == 0 and dark and main.ir_on() and not main.white_light.light_energy > 0.0:
			ex = main.ir_ex                           # 3D-4.1: the infrared picture has its own exposure (before: fixed 0.85 - almost white)
		main.expo_mats[i].set_shader_parameter("expo", ex)
		main.lens_mats[i].set_shader_parameter("expo", ex)
	if i < 2:
		main.cam_attr[i].exposure_multiplier = main.gain[i] if not dark else 1.0   # at night the lens shader does the exposure
		if main.realism != null:
			main.realism.before_capture(i)
		if main.simreal != null:
			main.simreal.before_capture(i)            # 3D-4.4: lens, rolling shutter, noise, infrared, reflectors
		main.weit.before_capture(i)                   # 3D-4.17: NoIR Wide - infrared picture, fisheye, the wide infrared light
		if main.zwilling != null and main.zwilling.fm != null:
			main.zwilling.fm.before_capture(i)        # 3D-4.27: Foto-Modus - the camera sees the real photo, the figures are fitted to it
		if main.wetter != null:
			main.wetter.before_capture(i)             # real-wetter: drops and fog on the lens, ground fog
		if main.camphys != null:
			main.camphys.before_capture(i)            # 3D-4.x P1: last - exposure time, gain, sensor noise, NoIR colours
	main.vps[i].render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	var img: Image = main.vps[i].get_texture().get_image()
	main.ir_light.light_energy = 0.0
	main.weit.after_capture(i, img)
	if img != null and not img.is_empty():
		if i < 2:
			main._auto_exposure(i, img)
			if main.realism != null:
				main.realism.after_capture(i, img)
			var hold := false
			if main.cond["net"] and i == 0:                   # 3D-3.74: bad Wi-Fi - pictures get lost, sometimes it stands still
				if main.now() < main._net_hold:
					hold = true
				elif randf() < 0.05:
					main._net_hold = main.now() + randf_range(0.8, 2.5)
					hold = true
				elif randf() < 0.3:
					hold = true
			if not hold:
				main.jpgs[i] = img.save_jpg_to_buffer(main.realism.jpg_q if main.realism != null and main.realism.fx_on else 0.8)
				main.frame_no[i] += 1
				if main.simreal != null:
					main.simreal.on_jpg(i, main.jpgs[i])           # 3D-4.4: «Wie ein echter Pi 5» - the picture comes late
		else:
			main._decode_thermal(img)
	main.capturing = false


func view_request(q: Dictionary) -> void:
	if q.has("w") and str(q["w"]).is_valid_int():
		main.view_w = clampi(int(q["w"]), 320, 2560)
	if q.has("q") and str(q["q"]).is_valid_float():
		main.view_q = clampf(float(q["q"]) / 100.0, 0.3, 0.95)
	if Quality.lite():                          # 3D-4.25: Lite - a smaller picture of the window (the cameras for MoveEye stay)
		main.view_w = mini(main.view_w, Quality.VIEW_W)
		main.view_q = minf(main.view_q, Quality.VIEW_Q)
	if q.has("fmt"):
		main.view_webp = str(q["fmt"]) == "webp"
	if str(q.get("clean", "")) == "1":
		main.view_clean_t = main.now()                    # 3D-3.67: MoveEye shows the picture in full screen: no rover stick
	if str(q.get("bare", "")) == "1" and main.padview != null:
		main.padview.bare_t = main.now()                  # «Controller-Ansicht»: the picture without the buttons of the window
	if str(q.get("dock", "")) == "1" and main.padview != null:
		main.padview.dock_t = main.now()                  # 3D-4.x: MoveEye's simulator page: only the 3D view and the dock (padview.gd)


func view_rect() -> Rect2:
	"""the part of the window with the 3D world (without the panel on the right)"""
	var vs: Vector2 = Vector2(main.remote_vp.size) if main.remote_vp != null else main.get_viewport().get_visible_rect().size
	var w := vs.x
	if main.ui_root != null and main.ui_root.visible:
		w = min(w, main.ui_root.get_global_rect().position.x)
	return Rect2(0, 0, max(64.0, w), vs.y)


func _view_capture() -> void:
	var t = main.now()
	for kc in main._rkeys.keys():
		if t > float(main._rkeys[kc]):
			main._rkeys.erase(kc)
			var ku := InputEventKey.new()
			ku.keycode = kc
			ku.physical_keycode = kc
			ku.pressed = false
			Input.parse_input_event(ku)
	# the window is the small box (or minimized): the view for MoveEye is drawn in a picture of its own (3D-3.19)
	main._remote_set(t - main.view_want_t < (10.0 if main.remote_vp != null else 3.0) and not main.win_open)
	if t - main.view_want_t > 3.0 or t - main._view_t < 1.0 / max(1.0, minf(main.view_fps, Quality.VIEW_FPS) if Quality.lite() else main.view_fps):
		return
	main._view_t = t
	var img = (main.remote_vp.get_texture() if main.remote_vp != null else main.get_viewport().get_texture()).get_image()
	if img == null or img.is_empty():
		return
	var vs: Vector2 = Vector2(main.remote_vp.size) if main.remote_vp != null else main.get_viewport().get_visible_rect().size
	var k: float = float(img.get_width()) / maxf(1.0, vs.x)
	if main.padview != null and main.padview.dock_compose():      # 3D-4.x: MoveEye's simulator page: only the 3D view and the dock
		img = main.padview.compose(img, k)
		if img == null:
			return
	var r = main.view_rect()
	var rr := Rect2i(int(r.position.x * k), int(r.position.y * k), int(r.size.x * k), int(r.size.y * k)).intersection(Rect2i(Vector2i.ZERO, img.get_size()))
	if rr.size.x < 16 or rr.size.y < 16:
		return
	var sub = img.get_region(rr)
	if sub.get_width() > main.view_w:
		sub.resize(main.view_w, int(sub.get_height() * float(main.view_w) / sub.get_width()), Image.INTERPOLATE_BILINEAR)
	if main.view_webp and t - main.view_mjpg_t > 3.0:            # 3D-3.58: WebP - the same sharpness with about a third less data
		main.view_jpg = sub.save_webp_to_buffer(true, main.view_q)
		main.view_mime = "image/webp"
	else:
		main.view_jpg = sub.save_jpg_to_buffer(main.view_q)
		main.view_mime = "image/jpeg"
	main.view_no += 1


func view_input(evs: Array) -> int:
	"""events from MoveEye: x / y 0 … 1 in the picture of /view.mjpg -> the same as mouse / keys here"""
	var r = main.view_rect()
	var n := 0
	for e in evs.slice(0, 60):
		if not (e is Dictionary):
			continue
		var t := str(e.get("t", ""))
		var p = r.position + Vector2(clampf(float(e.get("x", 0.5)), 0.0, 1.0) * r.size.x, clampf(float(e.get("y", 0.5)), 0.0, 1.0) * r.size.y)
		if t == "move":
			var m := InputEventMouseMotion.new()
			m.position = p
			m.global_position = p
			m.relative = p - main._in_pos
			m.velocity = m.relative * 30.0
			m.button_mask = main._in_mask
			main._view_send(m)
		elif t in ["down", "up", "dbl"]:
			var b := clampi(int(e.get("b", 1)), 1, 3)
			var mb := InputEventMouseButton.new()
			mb.button_index = b
			mb.pressed = t != "up"
			mb.double_click = t == "dbl"
			mb.alt_pressed = bool(e.get("alt", false))
			mb.shift_pressed = bool(e.get("shift", false))
			mb.position = p
			mb.global_position = p
			var bit := 1 << (b - 1)
			main._in_mask = (main._in_mask | bit) if mb.pressed else (main._in_mask & ~bit)
			mb.button_mask = main._in_mask
			main._view_send(mb)
		elif t == "wheel":
			for pr in [true, false]:
				var w := InputEventMouseButton.new()
				w.button_index = MOUSE_BUTTON_WHEEL_UP if float(e.get("d", 1)) > 0 else MOUSE_BUTTON_WHEEL_DOWN
				w.pressed = pr
				w.factor = 1.0
				w.position = p
				w.global_position = p
				main._view_send(w)
		elif t == "key":
			var kc = main.VIEW_KEYS.get(str(e.get("k", "")))
			if kc == null:
				continue
			var ke := InputEventKey.new()
			ke.keycode = kc
			ke.physical_keycode = kc
			ke.pressed = bool(e.get("down", true))
			Input.parse_input_event(ke)
			if ke.pressed:
				main._rkeys[kc] = main.now() + 1.2                 # held from MoveEye: let go by itself if no news comes (lost connection)
			else:
				main._rkeys.erase(kc)
		else:
			continue
		if t != "key":
			main._in_pos = p
		n += 1
	return n


func _remote_set(on: bool) -> void:
	"""small box / minimized while MoveEye looks at the window: the window (3D view, map, compass, buttons, panel)
	is drawn into an invisible picture of the normal window size; back into the window as soon as it is big again"""
	if on == (main.remote_vp != null) or main.ui_layer == null or main.view_cam == null:
		return
	if on:
		var sz := Vector2i(1440, 860)
		if main.mini_box != null and main.mini_box.mini:
			sz = main.mini_box.saved.get("size", sz)
		main.remote_vp = SubViewport.new()
		main.remote_vp.size = Vector2i(clampi(sz.x, 640, 2560), clampi(sz.y, 400, 1600))
		main.remote_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		main.remote_vp.msaa_3d = Viewport.MSAA_2X
		main.add_child(main.remote_vp)
		main._remote_back = []
		for n in [main.ui_layer, main.view_cam]:
			main._remote_back.append([n, n.get_parent(), n.get_index()])
			n.reparent(main.remote_vp)
		main.view_cam.current = true
		print("view for MoveEye: drawn on its own (window small)")
	else:
		for e in main._remote_back:
			var n: Node = e[0]
			if is_instance_valid(n):
				n.reparent(e[1])
				(e[1] as Node).move_child(n, mini(int(e[2]), (e[1] as Node).get_child_count() - 1))
		main._remote_back = []
		main.view_cam.current = true
		main.remote_vp.queue_free()
		main.remote_vp = null
		print("view for MoveEye: back in the window")


func _view_send(ev: InputEvent) -> void:
	"""a mouse event from MoveEye: into the window, or into the picture of its own (then the 3D view gets what the
	panel, the map and the buttons do not take)"""
	if main.remote_vp == null:
		Input.parse_input_event(ev)
		return
	main.remote_vp.push_input(ev, true)
	if not main.remote_vp.is_input_handled():
		main._unhandled_input(ev)
