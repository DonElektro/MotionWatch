extends Object
## Teil von main.gd (Vorschlag 24 «main.gd zerlegen»): Start, Qualität und Grafik: Grafikstufe, Lite, Leistung, Neustart-Argumente, Fenster, Updates, Autostart.
## main.gd lädt diesen Teil erst beim ersten Aufruf (_mod) und leitet seine Funktionen weiter: main.xyz bleibt gleich.
## Hier steht «main.» vor allem, was zu main.gd gehört.

var main                              # main.gd
const Quality := preload("res://scripts/quality.gd")
const Versionen = preload("res://scripts/versionen.gd")


func _perf_tick() -> void:
	"""3D-3.75: the window draws fewer than 14 pictures per second for 20 s: one step lighter (quality, then sharpness of the
	view, then the grass). The pictures for MoveEye are not touched."""
	if not main.auto_perf or not main.win_open or not main.sim_active or main.now() - main._perf_t < 30.0 or main.busy_with() != "":
		main._slow_n = 0 if not main.auto_perf else main._slow_n
		return
	var lim: int = main.win_fps if main.win_fps > 0 else 60
	if Engine.get_frames_per_second() < min(14.0, lim * 0.7):
		main._slow_n += 1
	else:
		main._slow_n = max(0, main._slow_n - 2)
	if main._slow_n < 40:
		return
	main._slow_n = 0
	main._perf_t = main.now()
	for k_ in ["quality", "view_scale", "meadow_on"]:     # 3D-3.88: only for this session - the own choice stays saved
		if not main._perf_orig.has(k_):
			main._perf_orig[k_] = main.get(k_)
	main._perf_auto = true
	var lvl: int = ["simple", "medium", "nice", "ultra"].find(main.quality)
	var what := ""
	if lvl > 0:
		main._set_quality(["simple", "medium", "nice", "ultra"][lvl - 1])
		what = "Grafik «%s»" % ["einfach", "mittel", "schön"][lvl - 1]
	elif main.view_scale > 0.75:
		main.set_view_scale(0.75)
		what = "Ansicht 75 % scharf"
	elif main.meadow_on:
		main.set_meadow(false)
		what = "ohne Gras und Blumen"
	elif main.view_scale > 0.55:
		main.set_view_scale(0.55)
		what = "Ansicht 55 % scharf"
	else:
		main._perf_auto = false
		return
	main._perf_auto = false
	main.start_info = "Der PC ist langsam – leichter gemacht: %s (nur bis zum Neustart; Bilder für MoveEye unverändert)" % what
	print("auto graphics: " + what)


func _set_quality(v: String) -> void:
	if not main._perf_auto:
		main._perf_orig.erase("quality")
	main.quality = v
	main._apply_quality()


func auto_quality() -> String:
	"""3D-3.33: first start - the graphics level from the graphics card (later the own choice is kept)"""
	var a := RenderingServer.get_video_adapter_name().to_lower() + " " + RenderingServer.get_video_adapter_vendor().to_lower()
	if Engine.get_architecture_name() in ["arm64", "arm32"] or a.contains("v3d") or a.contains("videocore"):
		return "simple"                                   # 3D-3.43: Raspberry Pi - the light graphics
	if main.in_vm or a.contains("llvmpipe") or a.contains("swiftshader") or a.contains("basic render") or a.contains("software"):
		return "simple"
	if a.contains("nvidia") or a.contains("geforce") or a.contains("radeon") or a.contains("amd") or a.contains("arc"):
		return "nice"
	return "medium"                                       # Intel and other built-in graphics


func _apply_quality() -> void:
	if not main.quality in ["simple", "medium", "nice", "ultra"]:
		main.quality = "nice"
	var lvl: int = ["simple", "medium", "nice", "ultra"].find(main.quality)
	var nice := lvl >= 2
	main.sun.shadow_enabled = lvl >= 1
	main.sun.directional_shadow_max_distance = [40.0, 60.0, 80.0, 120.0][lvl]
	main.sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS if lvl <= 1 else DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	main.white_light.shadow_enabled = lvl >= 1
	main.env.glow_enabled = lvl >= 1
	main.env.glow_intensity = 0.5 if lvl == 1 else 0.7
	main.env.glow_bloom = 0.0 if lvl < 2 else 0.06
	RenderingServer.directional_shadow_atlas_set_size(2048 if lvl <= 1 else 4096, true)
	var aa: Viewport.MSAA = [Viewport.MSAA_DISABLED, Viewport.MSAA_2X, Viewport.MSAA_2X, Viewport.MSAA_4X][lvl]
	for i in range(2):
		main.vps[i].msaa_3d = aa
	main.get_viewport().msaa_3d = aa
	main.sky_mat.set_shader_parameter("detail", 1.0 if lvl >= 1 else 0.0)
	for m in main.mats.values():
		main._mat_detail(m, lvl >= 1)
	# Forward+ (Vulkan) only: light bouncing off surfaces, shadows in corners, reflections, light shafts in the fog
	var fwd: bool = RenderingServer.get_rendering_device() != null       # Vulkan / Forward+ (not the OpenGL renderer)
	main.env.ssao_enabled = fwd and lvl >= 2
	main.env.ssao_intensity = 1.6
	main.env.ssil_enabled = fwd and lvl >= 3
	main.env.ssr_enabled = fwd and lvl >= 3
	main.env.sdfgi_enabled = fwd and lvl >= 3
	main.env.volumetric_fog_enabled = fwd and lvl >= 3
	main.env.volumetric_fog_density = 0.008
	main.env.volumetric_fog_length = 80.0
	main.get_viewport().use_taa = fwd and lvl >= 3
	if main.hoch != null:
		main.hoch.after_quality()                       # F1: «Hoch» on top of the chosen level (or away again)


func set_grafik_mode(v: String) -> void:
	main.grafik_mode = Quality.mode_id(v)
	main._grafik_keep = ""                                     # von Hand gewählt: das gilt (auch nach --grafik)
	main.lite_update()
	if main.hoch != null and (main.grafik_mode == "hoch") != (main.hoch.stufe == "hoch"):
		main.hoch.set_stufe(main.grafik_mode)                       # F1: Hoch = Neustart mit Forward+; jede andere Wahl = wieder normal
	main._settings_dirty = true


func lite_update() -> void:
	"""Lite on or off - from «Grafik-Modus» and the hardware (quality.gd)"""
	var why := ""
	if main.grafik_mode == "lite":
		why = "von Hand"
	elif main.grafik_mode == "auto":
		var w := Quality.weak_reason()
		if w != "":
			why = "automatisch: " + w
		elif main._lite_slow:
			why = "automatisch: wenige Bilder pro Sekunde beim Start"
	main.lite_why = why
	var on := why != ""
	if Engine.has_meta("lite") and on == Quality.lite():
		return
	Quality.set_lite(on)
	main._lite_apply(on)
	print("graphics mode %s -> Lite %s%s" % [main.grafik_mode, "on" if on else "off", (" (" + why + ")") if on else ""])


func _lite_apply(on: bool) -> void:
	if on:
		for k_ in main.LITE_KEYS:
			if not main._perf_orig.has(k_):
				main._perf_orig[k_] = main.get(k_)
		main._perf_auto = true                                  # not the own choice: the setters keep _perf_orig
		main._set_quality("simple")
		main.set_view_scale(minf(main.view_scale, Quality.SCALE))
		if main.win_fps <= 0 or main.win_fps > Quality.FPS:
			main.win_fps = Quality.FPS
		main.max_visitors = mini(main.max_visitors, Quality.VISITORS)
		main._perf_auto = false
		main.view_w = mini(main.view_w, Quality.VIEW_W)
		main.view_q = minf(main.view_q, Quality.VIEW_Q)
	else:
		for k_ in main.LITE_KEYS:
			if main._perf_orig.has(k_):
				var v = main._perf_orig[k_]
				main._perf_orig.erase(k_)
				if k_ == "quality":
					main.quality = str(v)
					main._apply_quality()
				elif k_ == "view_scale":
					main.set_view_scale(float(v))
				else:
					main.set(k_, int(v))
	for pa in [[main.rain, 2500], [main.snow, 3000], [main.splashes, 700]]:
		if pa[0] != null:
			pa[0].amount = Quality.n(pa[1])
	main._lite_scene(on)
	main._settings_dirty = true


func _lite_scene(on: bool) -> void:
	"""the things of the scene: fewer particles, thinner grass, small things far away not drawn (visibility range)"""
	if main.scene_parent == null:
		return
	var todo: Array = [main.scene_parent]
	while not todo.is_empty():
		var n = todo.pop_back()
		todo.append_array(n.get_children())
		if n is CPUParticles3D or n is GPUParticles3D:
			if not n.has_meta("full_n"):
				n.set_meta("full_n", n.amount)
			n.amount = maxi(1, roundi(int(n.get_meta("full_n")) * Quality.KEEP)) if on else int(n.get_meta("full_n"))
		elif n is MultiMeshInstance3D and n.is_in_group("meadow"):
			if n.multimesh != null:
				n.multimesh.visible_instance_count = roundi(n.multimesh.instance_count * Quality.KEEP) if on else -1
		elif n is GeometryInstance3D:
			if on:
				var sz: Vector3 = n.get_aabb().size * n.global_transform.basis.get_scale()
				if maxf(sz.x, maxf(sz.y, sz.z)) < 1.5 and n.visibility_range_end == 0.0:
					n.visibility_range_end = Quality.FAR
					n.set_meta("lite_far", true)
			elif n.has_meta("lite_far"):
				n.visibility_range_end = 0.0
				n.remove_meta("lite_far")


func _lite_tick() -> void:
	"""«Automatisch» on a normal PC: are the first seconds very slow (under 12 pictures per second)? Then Lite for this session"""
	if main.grafik_mode != "auto" or Quality.lite() or main._lite_slow or not main._lite_auto_ok:
		return
	var age = main.now() - main._lite_t0
	if age < 6.0 or age > 40.0 or not main.win_open or not main.sim_active or main.busy_with() != "":
		return
	main._lite_fps.append(Engine.get_frames_per_second())
	if main._lite_fps.size() < 16:
		return
	var avg := 0.0
	for f in main._lite_fps:
		avg += float(f) / main._lite_fps.size()
	main._lite_fps.clear()
	main._lite_t0 = -1000.0                                   # decided once per start
	if avg < 12.0:
		main._lite_slow = true
		main.lite_update()
		main.start_info = "Der Rechner ist langsam (%d Bilder/s) – «Grafik-Modus: Automatisch» hat Lite eingeschaltet (System → Grafik)." % roundi(avg)


func perf_info() -> Dictionary:
	"""for «Leistung» in the self-diagnosis and «Über»: frames per second, renderer, Lite, resolution"""
	var vs: Vector2 = main.get_viewport().get_visible_rect().size
	var k: float = main.get_viewport().scaling_3d_scale
	return {"fps": Engine.get_frames_per_second(), "renderer": Quality.renderer(), "lite": Quality.lite(), "why": main.lite_why,
			"mode": main.grafik_mode, "res": "%d × %d" % [roundi(vs.x * k), roundi(vs.y * k)], "scale": roundi(k * 100.0),
			"cams": "%d × %d" % [main.CAM_W[0], main.CAM_H[0]], "max_fps": Engine.max_fps}


func set_view_scale(v: float) -> void:
	if not main._perf_auto:
		main._perf_orig.erase("view_scale")
	main.view_scale = clampf(v, 0.4, 1.0)
	main.get_viewport().scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	main.get_viewport().scaling_3d_scale = main.view_scale
	main._settings_dirty = true


func restart_args() -> PackedStringArray:
	"""options for the start after an update: as before, plus what is on now (sending, scene, MoveEye on this PC,
	the window: size and place, full screen, or the small box)"""
	var a := OS.get_cmdline_user_args()
	var out := PackedStringArray()
	var skip := false
	var early = main.net == null                     # the update check right at the start: nothing is switched on yet - keep what was asked for
	for x in a:
		if skip:
			skip = false
			continue
		if x in ["--stream", "--updated", "--mwpc"] or (not early and x in ["--mini", "--mini-tiny", "--maximized"]):
			continue
		if x == "--scene" or x == "--old-pid" or (x == "--win" and not early):
			skip = true
			continue
		out.append(x)
	if main.stream_on or (early and "--stream" in a):
		out.append("--stream")
	if not early:
		var w = main.get_window()
		if main.mini_box != null and main.mini_box.mini:
			out.append("--mini-tiny" if main.mini_box.tiny else "--mini")
			var sz: Vector2i = main.mini_box.saved.get("size", Vector2i(1440, 860))
			var ps: Vector2i = main.mini_box.saved.get("pos", Vector2i(60, 60))
			out.append("--win")
			out.append("%d,%d,%d,%d" % [ps.x, ps.y, sz.x, sz.y])
		elif w.mode == Window.MODE_MAXIMIZED or w.mode == Window.MODE_FULLSCREEN:
			out.append("--maximized")
		elif w.mode == Window.MODE_MINIMIZED:
			out.append("--mini")
		else:
			out.append("--win")
			out.append("%d,%d,%d,%d" % [w.position.x, w.position.y, w.size.x, w.size.y])
	out.append("--scene")
	out.append(main.scene)
	out.append("--old-pid")                       # 3D-3.75: the new simulator may stop this one if it still holds the port
	out.append(str(OS.get_process_id()))
	if main.mwpc != null and main.mwpc.state == "running":
		out.append("--mwpc")
	return out


func _restore_window(args: PackedStringArray) -> void:
	"""after an update (or from the options): the window comes back as it was - size and place, full screen, or the
	small box / icon in the corner"""
	var w = main.get_window()
	var i := args.find("--win")
	if i >= 0 and i + 1 < args.size():
		var p := args[i + 1].split(",")
		if p.size() == 4:
			w.size = Vector2i(maxi(400, int(p[2])), maxi(300, int(p[3])))
			w.position = Vector2i(int(p[0]), int(p[1]))
	if "--maximized" in args:
		w.mode = Window.MODE_MAXIMIZED
	if "--mini" in args or "--mini-tiny" in args:
		var tiny := "--mini-tiny" in args
		main.get_tree().create_timer(1.0).timeout.connect(func():
			if not main.mini_box.mini:
				main.mini_box.enter()
			if tiny:
				main.mini_box.set_tiny(true))


func check_updates() -> void:
	"""button «Nach Updates suchen» in the window: asks before installing and also says when there is nothing new"""
	main.run_update(false, true)


func run_update(automatic: bool, by_hand: bool) -> void:
	"""check GitHub for a newer simulator. automatic: install by itself after 15 s (can be cancelled) - for the setting
	«Neue Versionen automatisch installieren» and for the button on the web page of MoveEye (from far away)."""
	if main.update_busy:
		return
	main.update_busy = true
	if main.update_btn != null:
		main.update_btn.disabled = true
	main.update_info = "suche …"
	var up = main.Updater.new()
	up.manual = by_hand
	up.quiet = not by_hand
	up.auto = automatic
	main.add_child(up)
	main.update_node = up                              # Ruhebild: busy_reply() tells MoveEye about the update
	await up.check(main.VERSION, main.update_url)
	main.update_info = up.result
	main.update_node = null
	up.queue_free()
	main.update_busy = false
	if main.update_btn != null:
		main.update_btn.disabled = false
	main._sync_update_ui()


func _dev_check() -> void:
	"""3D-3.81: the development phase - has simulator3d/version.json a new commit on GitHub? The answer «unchanged» (304
	with the ETag) does not count against GitHub's limit of 60 questions per hour. New commit -> update at once."""
	main._dev["busy"] = true
	main._dev["t"] = main.now()
	var h := HTTPRequest.new()
	h.timeout = 8.0
	main.add_child(h)
	var hd := ["User-Agent: MoveEye-Sim", "Accept: application/vnd.github+json"]
	if str(main._dev["etag"]) != "":
		hd.append("If-None-Match: " + str(main._dev["etag"]))
	var err := h.request("https://api.github.com/repos/DonElektro/MotionWatch/commits?path=simulator3d/version.json&per_page=1", hd)
	if err == OK:
		var r: Array = await h.request_completed
		if r[0] == HTTPRequest.RESULT_SUCCESS and r[1] == 200:
			for x in r[2]:
				if str(x).to_lower().begins_with("etag:"):
					main._dev["etag"] = str(x).substr(5).strip_edges()
			var j = JSON.parse_string((r[3] as PackedByteArray).get_string_from_utf8())
			var sha: String = str(j[0].get("sha", "")) if typeof(j) == TYPE_ARRAY and j.size() > 0 else ""
			if sha != "" and sha != str(main._dev["sha"]):
				var first: bool = str(main._dev["sha"]) == ""
				main._dev["sha"] = sha
				if not first:                               # (the first answer only notes the state)
					print("development phase: new simulator commit - looking for the update")
					main.run_update(true, false)
	h.queue_free()
	main._dev["busy"] = false


func set_autostart(on: bool) -> void:
	var err: String = main.Autostart.set_on(on)
	main.autostart_on = main.Autostart.is_on()
	main.start_info = "Autostart: " + err if err != "" else ("Startet mit dem PC" if main.autostart_on else "")
	main._sync_ui()


func setup_autologon() -> void:
	"""without signing in: Windows signs in by itself (Autologon of Microsoft), the simulator starts and locks the screen"""
	main.start_info = "Autologon wird geladen …"
	main._update_status()
	await main.get_tree().process_frame
	var err: String = main.Autostart.get_autologon()
	if err != "":
		main.start_info = "Autologon: " + err
		return
	if not main.autostart_on:
		main.set_autostart(true)
	main.autostart_lock = true
	main._settings_dirty = true
	main.start_info = "Im Fenster «Autologon» das Windows-Passwort eingeben und «Enable» drücken"
	main._sync_ui()


func set_auto_update(on: bool) -> void:
	main.auto_update = on
	main._save_settings()
	main.next_update_check = main.now() + 5.0 if on else main.now() + main.UPDATE_EVERY   # switched on: look soon
	main._sync_update_ui()
