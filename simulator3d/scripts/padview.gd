extends Node
## «Controller-Ansicht» of MoveEye (MoveEye part 538, wish of the owner 29.10.2026): a phone / tablet shows the live picture
## and this view next to each other, steered with a game controller or the fingers. MoveEye sends
##   {action: "padview", view: follow | driver | top | head | free | next | rnext | off,
##    look: [x, y] (turn the view, stick -1 … 1 for «dt» s), fly: [forward, turn] (free view, no rover), zoom: +1 / -1}
## With the rover (the mover) «follow / driver / top» are the views of «Erkunden» (explore.gd: hinterher, Fahrersicht,
## von oben) - the rover itself is driven by MoveEye (its mover stick, MOVER), so a real mover later uses the same way.
## Without the rover: head camera (view 1), from above (the «Von oben» of the view bar) and the free view.
## view.jpg?bare=1: the picture for MoveEye without the buttons, the map and the boxes of the window (for 3 s after the
## last such picture - the window at the PC shows them again by itself).
## 3D-4.x view.jpg?dock=1 (MoveEye's simulator page, wish of the owner 30.10.2026): only the 3D view and the dock at the bottom -
## no camera picture, no map with the compass, no rover stick, no news box. The window at the PC stays as it is: the 3D view
## is drawn once more without anything on it (a small picture of its own, one drawing per picture for MoveEye, the same
## camera) and the dock is copied in from the window (compose). Window small / minimized (main.remote_vp): nobody sees it,
## so there the layer with the buttons is hidden and the dock moves into a layer of its own (3 s after the last such
## picture everything is back).
## 3.51.x (Daniel 02.11.2026): dock=1 copies in everything over the 3D view (cards of the stories and games, Tagebuch, windows
## such as «Gerät» / «Kameras» / Karte, «Mehr», popups, hints) - only the panel, the phone picture and the mover stick stay
## out (overlay_rects); also with the window small, so the hidden layer of _dock() is not used any more.

var main
var bare_t := -100.0
var dock_t := -100.0                  # 3D-4.x: last picture asked for with dock=1
var _dock_on := false
var _dock_layer: CanvasLayer
var _dock_moved: Array = []           # [node, index in ui_layer]
var _cvp: SubViewport                  # the clean 3D view (compose)
var _ccam: Camera3D
var _cvp_t := -100.0
var view := ""                        # the view padview set last ("" = none)
var _ex_ours := false                 # padview switched «Erkunden» on (and switches it off again)
var _hid := false
var _ui_was := true
var _look_t := -100.0

const NEXT_ROVER := ["head", "top", "follow"]       # double tap: head camera → from above → behind the rover
const NEXT_FREE := ["head", "top", "free"]
const RNEXT := ["follow", "driver", "top"]          # R3: behind the rover → driver → from above


func command(d: Dictionary) -> Dictionary:
	var rover: bool = main.mover_on
	if d.has("view"):
		var v := str(d["view"])
		if v == "next":
			v = _next(NEXT_ROVER if rover else NEXT_FREE)
		elif v == "rnext":
			v = _next(RNEXT if rover else NEXT_FREE)
		_set_view(v)
	var dt := clampf(float(d.get("dt", 0.1)), 0.0, 0.5)
	if d.has("look") and d["look"] is Array and d["look"].size() >= 2:
		_look(clampf(float(d["look"][0]), -1.0, 1.0), clampf(float(d["look"][1]), -1.0, 1.0), dt)
	if d.has("fly") and d["fly"] is Array and d["fly"].size() >= 2:
		_fly(clampf(float(d["fly"][0]), -1.0, 1.0), clampf(float(d["fly"][1]), -1.0, 1.0), dt)
	if d.has("zoom"):
		_zoom(signf(float(d["zoom"])))
	return state()


func state() -> Dictionary:
	var ex = main.explore
	var c: Vector3 = main.view_cam.global_position
	return {"ok": true, "view": view, "rover": main.mover_on, "explore": ex != null and ex.on, "ex_view": ex.view if ex != null else "",
			"vm": main.view_mode, "bare": _hid, "dock": _dock_on, "cam": [snappedf(c.x, 0.01), snappedf(c.y, 0.01), snappedf(c.z, 0.01)],
			"cam_yaw": snappedf(rad_to_deg(main.view_cam.global_rotation.y), 0.1),
			"orbit": snappedf(ex.orbit, 0.01) if ex != null else 0.0, "dist": snappedf(ex.dist, 0.01) if ex != null else 0.0,
			"x": snappedf(main.rig.position.x, 0.01), "z": snappedf(main.rig.position.z, 0.01), "yaw": snappedf(rad_to_deg(main.rig.rotation.y), 0.1),
			"mm": main.padhud.map_data() if main.padhud != null else {}, "rumble": main.padmap.take_web_rumble() if main.padmap != null else ""}   # 3D-4.13: mini-map (MWPad.drawMap), vibration


func _next(L: Array) -> String:
	var i := L.find(view)
	return str(L[(i + 1) % L.size()])


func _explore(on: bool) -> void:
	var ex = main.explore
	if ex == null:
		return
	if on and not ex.on:
		ex.set_on(true)
		_ex_ours = true
	elif not on and ex.on and _ex_ours:
		ex.set_on(false)
		_ex_ours = false


func _set_view(v: String) -> void:
	var ex = main.explore
	var rover: bool = main.mover_on
	if main.fly_tw != null:
		main.fly_tw.kill()
	match v:
		"follow", "driver", "top":
			if rover and ex != null:
				_explore(true)
				ex.view = {"follow": "chase", "driver": "driver", "top": "top"}[v]
				ex.orbit = 0.0
				ex.auto_top = false
			elif v == "top":
				_explore(false)
				main._view_preset("top")
			else:
				v = "free"
				_explore(false)
				main.set_view(0)
		"head":
			_explore(false)
			main.set_view(1)
		"free":
			_explore(false)
			main.set_view(0)
		"off":
			_explore(false)
			v = ""
		_:
			return
	view = v


func _look(x: float, y: float, dt: float) -> void:
	"""turn the view: with the rover around it (explore), else the free view on the spot (from the head camera: from there)"""
	_look_t = main.now()
	var ex = main.explore
	if ex != null and ex.on:
		ex.orbit -= x * dt * 2.2
		ex.pitch = clampf(ex.pitch + y * dt * 1.2, 0.05, 1.3)
		return
	if main.fly_tw != null:
		main.fly_tw.kill()
	main.set_view(0)
	main.follow = false
	if view in ["head", "top"]:
		view = "free"
	var r: Vector3 = main.view_cam.rotation
	main.view_cam.rotation = Vector3(clampf(r.x - y * dt * 1.2, -1.45, 1.2), r.y - x * dt * 1.8, 0.0)


func _fly(fwd: float, turn: float, dt: float) -> void:
	"""no rover: the right stick moves the free view (up = forward, sideways = turn)"""
	var ex = main.explore
	if ex != null and ex.on:
		return
	if main.fly_tw != null:
		main.fly_tw.kill()
	main.set_view(0)
	main.follow = false
	if view in ["head", "top"]:
		view = "free"
	var cam: Camera3D = main.view_cam
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	if f.length() < 0.01:
		f = -cam.global_transform.basis.y                   # looking straight down: forward is the top of the picture
		f.y = 0.0
	f = f.normalized()
	cam.global_position += f * fwd * dt * clampf(float(main.fly_speed), 2.0, 40.0)
	cam.rotation.y -= turn * dt * 1.6
	main._keep_above()


func _zoom(dir: float) -> void:
	var ex = main.explore
	if ex != null and ex.on:
		ex.dist = clampf(ex.dist - dir * 1.2, 2.5, 30.0)
		return
	var r: Rect2 = main.view_rect()
	main._zoom_at(r.position + r.size * 0.5, dir)
	if view in ["head", "top"]:
		view = "free"


func _process(dt: float) -> void:
	var t: float = main.now()
	var want := t - bare_t < 3.0
	var want_dock := false                                 # 3.51.x: compose() also for the small window (before: ui_layer hidden there,
	# so the Tagebuch, the game wizard, the cards and the windows were missing in the stream); _dock() stays for a way back
	if _cvp != null and t - _cvp_t > 10.0:
		_cvp.queue_free()                                  # not asked for a while: no second drawing any more
		_cvp = null
		_ccam = null
	if want_dock != _dock_on and main.ui_layer != null:
		_dock(want_dock)
	if want != _hid and main.ui_layer != null:
		if want:
			_ui_was = main.ui_layer.visible
			main.ui_layer.visible = false
		else:
			main.ui_layer.visible = _ui_was
		_hid = want
	if not want and view != "" and bare_t > 0.0 and t - bare_t > 30.0:
		_set_view("off")                                   # the phone is gone (closed without «off»): hand the view back
		bare_t = -100.0
	# behind the rover: while MoveEye drives and nobody turns the view, it swings back behind the rover
	var ex = main.explore
	if ex != null and ex.on and view == "follow" and t - _look_t > 1.5 and t - float(main.mw_t) < 1.0:
		var dr: Dictionary = main.mw.get("drive", {})
		if absf(float(dr.get("l", 0.0))) + absf(float(dr.get("r", 0.0))) > 0.05:
			ex.orbit = lerp_angle(ex.orbit, 0.0, clampf(dt * 0.8, 0.0, 1.0))


func _dock(on: bool) -> void:
	"""3D-4.x: only the 3D view and the dock (MoveEye's simulator page asks with dock=1)"""
	var ul: CanvasLayer = main.ui_layer
	var tb = main.toolbar
	if on:
		if tb == null:
			return
		if _dock_layer == null:
			_dock_layer = CanvasLayer.new()
			_dock_layer.name = "dock_only"
			main.add_child(_dock_layer)
		_dock_layer.layer = ul.layer
		_dock_moved = []
		var nodes: Array = [tb]
		for c in [tb._hint, tb._sub, tb._help]:
			if c != null and c.get_parent() == ul:
				nodes.append(c)
		for n in nodes:
			if n.get_parent() == ul:
				_dock_moved.append([n, n.get_index()])
				ul.remove_child(n)
				_dock_layer.add_child(n)
		_ui_was = ul.visible
		ul.visible = false
	else:
		_dock_moved.sort_custom(func(a, b): return int(a[1]) < int(b[1]))
		for e in _dock_moved:
			var n: Node = e[0]
			if is_instance_valid(n) and n.get_parent() == _dock_layer:
				_dock_layer.remove_child(n)
				ul.add_child(n)
				ul.move_child(n, mini(int(e[1]), ul.get_child_count() - 1))
		_dock_moved = []
		ul.visible = _ui_was
	_dock_on = on


func dock_compose() -> bool:
	"""main._view_capture: the picture for MoveEye's simulator page is composed (window open)"""
	var t: float = main.now()
	return t - dock_t < 3.0 and t - bare_t >= 3.0             # 3.51.x: also with the window small (remote_vp) - no hidden layer any more


func compose(img: Image, k: float) -> Image:
	"""the 3D view without anything on it, the dock (and its open menu) copied in from the window picture img (k = pixels
	of img per point of the window). null = not ready yet (keep the last picture)."""
	_cvp_t = main.now()
	var sz := img.get_size()
	var src: Camera3D = main.view_cam if main.remote_vp != null else main.get_viewport().get_camera_3d()
	if src == null:
		return img
	if _cvp == null:
		_cvp = SubViewport.new()
		_cvp.name = "clean_view"
		_cvp.world_3d = main.get_viewport().world_3d
		_cvp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		_ccam = Camera3D.new()
		_cvp.add_child(_ccam)
		main.add_child(_cvp)
	var out: Image = null
	if _cvp.size == sz and _cvp.has_meta("drawn"):
		out = _cvp.get_texture().get_image()
	if _cvp.size != sz:
		_cvp.size = sz
		_cvp.remove_meta("drawn")
	_ccam.current = true                                   # the next picture: the same camera as the window
	_ccam.global_transform = src.global_transform
	_ccam.projection = src.projection
	_ccam.fov = src.fov
	_ccam.size = src.size
	_ccam.near = src.near
	_ccam.far = src.far
	_ccam.keep_aspect = src.keep_aspect
	_ccam.h_offset = src.h_offset
	_ccam.v_offset = src.v_offset
	_ccam.cull_mask = src.cull_mask
	_ccam.environment = src.environment
	_ccam.attributes = src.attributes
	_cvp.msaa_3d = main.get_viewport().msaa_3d
	_cvp.render_target_update_mode = SubViewport.UPDATE_ONCE
	_cvp.set_meta("drawn", true)
	if out == null or out.is_empty():
		return null
	if out.get_format() != img.get_format():
		out.convert(img.get_format())
	var tb = main.toolbar
	if tb != null and tb.is_visible_in_tree():
		for c in [tb, tb._sub, tb._hint, tb._help]:
			if c == null or not (c as Control).is_visible_in_tree():
				continue
			var r: Rect2 = (c as Control).get_global_rect().grow(12.0)       # with the shadow
			var ri := Rect2i(int(r.position.x * k), int(r.position.y * k), int(r.size.x * k), int(r.size.y * k)).intersection(Rect2i(Vector2i.ZERO, sz))
			if ri.size.x > 0 and ri.size.y > 0:
				out.blit_rect(img, ri, ri.position)
	for r in overlay_rects():                          # 3.51.x: everything else that lies over the 3D view (cards, windows, hints, popups)
		var ri := Rect2i(int(r.position.x * k), int(r.position.y * k), int(ceilf(r.size.x * k)), int(ceilf(r.size.y * k))).intersection(Rect2i(Vector2i.ZERO, sz))
		if ri.size.x > 0 and ri.size.y > 0:
			out.blit_rect(img, ri, ri.position)
	return out


# ---- 3.51.x (Daniel, 02.11.2026): what lies over the 3D view also goes into the clean picture for MoveEye ---------------------
# Before only the dock was copied in: the cards of the stories (own CanvasLayer, e.g. 60), the Tagebuch, the game wizard, the
# windows «Gerät» / «Kameras», popups and hints were seen at the PC but not on the phone. Now every visible Control of every
# CanvasLayer of the window is copied in - except the parts MoveEye has itself (the panel on the right, the phone picture on
# the left, the mover stick - MoveEye shows its own) and the cross hair / the ring round the chosen visitor.
var _ovl_layers: Array = []
var _ovl_t := -100.0
var _ovl_vp: Viewport = null


func chrome() -> Array:
	var out := []
	for n in ["ui_root", "show_btn", "phone", "rover_pad", "crosshair", "sel_ring"]:
		var c = main.get(n)
		if c != null and is_instance_valid(c) and c is Control:
			out.append(c)
	return out


func overlay_rects() -> Array:
	"""the rectangles (window points) of everything over the 3D view that MoveEye's picture shows"""
	var vp: Viewport = main.remote_vp if main.remote_vp != null else main.get_viewport()
	var t: float = main.now()
	if vp != _ovl_vp or t - _ovl_t > 1.0:                # new layers (a story starts …): look again once a second
		_ovl_vp = vp
		_ovl_t = t
		_ovl_layers = []
		for l in main.get_tree().root.find_children("*", "CanvasLayer", true, false):
			if (l as CanvasLayer).get_viewport() == vp and l != _dock_layer:
				_ovl_layers.append(l)
		_ovl_layers.sort_custom(func(a, b): return (a as CanvasLayer).layer < (b as CanvasLayer).layer)
	var vs: Vector2 = vp.get_visible_rect().size
	var ch := chrome()
	var out := []
	for l in _ovl_layers:
		if is_instance_valid(l) and (l as CanvasLayer).visible:
			_ovl_walk(l, out, ch, vs.x * vs.y)
	for w in vp.get_embedded_subwindows():              # popups: drop-down lists, menus, tooltips
		if is_instance_valid(w) and (w as Window).visible:
			out.append(Rect2(Vector2((w as Window).position), Vector2((w as Window).size)).grow(4.0))
	return out


func _ovl_walk(n: Node, out: Array, ch: Array, area: float) -> void:
	for c in n.get_children():
		if c is CanvasLayer or c is Window or c is Node3D or c is Viewport:
			continue                                     # own layers come by themselves, popups above, no 3D
		if not (c is Control):
			if not (c is CanvasItem) or (c as CanvasItem).visible:
				_ovl_walk(c, out, ch, area)              # a plain Node / Node2D that holds Controls
			continue
		var ctl := c as Control
		if not ctl.visible or ctl in ch or ctl.modulate.a < 0.02 or ctl.self_modulate.a < 0.02 and ctl.get_child_count() == 0:
			continue
		var r: Rect2 = ctl.get_global_transform_with_canvas() * Rect2(Vector2.ZERO, ctl.size)
		var big := r.get_area() > 0.6 * area
		var holds := false
		for x in ch:
			if (x as Control).is_visible_in_tree() and ctl.is_ancestor_of(x):
				holds = true
				break
		if r.size.x < 2.0 or r.size.y < 2.0 or (big and _see_through(ctl)) or (holds and big):
			_ovl_walk(ctl, out, ch, area)                # a frame without a picture of its own: what is in it counts
		elif not holds:
			out.append(r.grow(4.0))                     # (with a little of the shadow / the border)


func _see_through(c: Control) -> bool:
	if c is ColorRect:
		return (c as ColorRect).color.a < 0.05 and c.material == null
	if c is PanelContainer or c is Panel:
		var sb: StyleBox = c.get_theme_stylebox("panel")
		return sb == null or sb is StyleBoxEmpty or (sb is StyleBoxFlat and (sb as StyleBoxFlat).bg_color.a < 0.05)
	return (c is Container and not (c is PanelContainer)) or c.get_class() == &"Control"   # frames without a picture of their own
