extends Node
## Game «Unentdeckt ans Ziel» (from 3D-2.4, much extended in 3D-2.5): up to 4 players with their phones (only a browser,
## same Wi-Fi). Every player has an own view (a camera behind the own figure, JPEG over a WebSocket).
## Modes: «Alle gegen die Kamera» (the simulator guards) or «Ein Spieler ist Wächter» (one phone sees through the head
## camera, turns the head, switches the light on and calls «Erwischt!»).
## The referee (visibility()) works like the real detection of Motion Watch: a person is recognised when it is big enough
## in the picture (pixels) and there is enough light; movement is noticed by the motion detection; the thermal camera
## sees a warm spot also at night; the microphone hears loud steps. Objects hide (with their height).
## Extras (all adjustable): stones to distract, things to collect, lives, cones of view for beginners, random start/goal.
## Page for the phone: http://<PC>:<port+5>/  ·  WebSocket: <port+6>.

var main
var Actor = preload("res://scripts/actor.gd")
var Qr = preload("res://scripts/qr.gd")

const MAX_P := 4
const COLORS := [Color(0.85, 0.12, 0.12), Color(0.12, 0.38, 0.92), Color(0.12, 0.68, 0.22), Color(0.95, 0.78, 0.08)]
const CNAMES := ["Rot", "Blau", "Grün", "Gelb"]
const TEAM_COLORS := [Color(0.92, 0.18, 0.12), Color(0.12, 0.42, 0.98)]
const TEAM_NAMES := ["Team Rot", "Team Blau"]
const SIGNALS := {"wait": "✋ Warte", "go": "▶ Los", "cam": "👁 Kamera!", "here": "📍 Hier"}
const QUAL := {"small": [320, 180, 10.0, 0.55], "mid": [480, 270, 12.0, 0.6], "big": [640, 360, 15.0, 0.65]}
const HEIGHT := [1.7, 1.1, 0.45]                 # standing, crouching, crawling (m)
const SHAPE := [1.0, 0.7, 0.3]                   # how well the person detection recognises the posture
const LOUD := [0.3, 0.12, 0.05]                  # steps (walking), × 3.3 when running
const CAM_W := [960, 640]                        # like main.gd
const CAM_H := [540, 360]
const CAM_FOV := [66.0, 100.0]
const TH_H := 62
const VFOV := [41.0, 62.0, 35.0]                 # vertical field of view of head camera, fixed camera, thermal camera
const LEVEL := {"easy": 0.6, "normal": 1.0, "hard": 1.6}
const STONE_EVERY := 12.0
const LIGHT_EVERY := 20.0

var open := false
var http_port := 8770
var ws_port := 8771
var http: TCPServer
var wss: TCPServer
var http_conns: Array = []              # [StreamPeerTCP, request so far, start time]
var socks: Array = []                   # {"ws": WebSocketPeer, "slot": -1, "t": time}
var players: Array = []                 # per slot: null or Dictionary (see _new_player)
var root: Node3D                        # figures and markers
var round_state := "lobby"              # lobby | countdown | play | end
var t_start := 0.0
var t_end := 0.0
var goal := Vector3.ZERO
var goal_name := "Ziel"
var goal_node: Node3D
var results: Array = []
var team_results: Array = []
var guard_auto := false                 # the game turns the head (automatic guard or a player as guard)
var guard_yaw := 0.0
var guard_tilt := deg_to_rad(-9.0)
var flash_until := 0.0
var light_ready := 0.0
var attention := Vector3.ZERO           # a noise (stone, steps): the automatic guard looks there ...
var attention_until := 0.0              # ... until then
var items: Array = []                   # {"node", "pos", "by": -1}
var cones: Array = []                   # [node of the head camera, node of the fixed camera]
var stones: Array = []                  # [node, until]
var _ref_t := 0.0
var _mw_catch_t := 0.0                  # «Motion Watch decides»: not again before then
var _st_t := 0.0
var capturing := false
var info_label: Label
var addr_label: Label
var qr_rect: TextureRect
var _qr_for := ""
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	root = Node3D.new()
	root.name = "game"
	main.add_child(root)
	players.resize(MAX_P)
	http_port = main.stream_port + 5
	ws_port = main.stream_port + 6
	_rng.randomize()
	_build_cones()
	on_scene()


func now() -> float:
	return Time.get_ticks_msec() / 1000.0


# ---- open / close, address -------------------------------------------------------------------------------------------
func set_open(on: bool) -> void:
	if on == open:
		return
	if on:
		http = TCPServer.new()
		wss = TCPServer.new()
		var e1 := http.listen(http_port)
		var e2 := wss.listen(ws_port)
		if e1 != OK or e2 != OK:
			http.stop()
			wss.stop()
			main.start_info = "Spiel: Port %d / %d belegt" % [http_port, ws_port]
			return
		open = true
	else:
		end_round()
		for s in socks:
			s["ws"].close()
		socks.clear()
		for i in range(MAX_P):
			_remove(i)
		http.stop()
		wss.stop()
		http_conns.clear()
		open = false
	paint()


func address() -> String:
	var best := ""
	for a in IP.get_local_addresses():
		if a.contains(":") or a.begins_with("127.") or a.begins_with("169.254."):
			continue
		if a.begins_with("192.168.") or best == "":
			best = a
	return "http://%s:%d/" % [best if best != "" else "127.0.0.1", http_port]


func count() -> int:
	var n := 0
	for p in players:
		if p != null:
			n += 1
	return n


func guard_player() -> Variant:
	for p in players:
		if p != null and p["role"] == "guard":
			return p
	return null


func busy() -> bool:
	"""somebody plays: the simulation must run (main._check_active)"""
	return open and count() > 0


func guard_watching() -> bool:
	"""a player guards: the head camera must deliver pictures often (main._wanted_fps)"""
	var g = guard_player()
	return g != null and g["sock"] != null


# ---- the scene: goal, starts, things to collect ----------------------------------------------------------------------
func on_scene() -> void:
	_pick_goal(false)
	for i in range(MAX_P):
		if players[i] != null:
			_to_start(players[i])
	_clear_items()


func _pick_goal(random: bool) -> void:
	var o: Dictionary = main.obj
	var keys := ["bike" if main.scene in ["camping", "parkplatz"] else "door"]
	if random:
		keys = []
		for k in ["bike", "door", "pir"]:
			if o.get(k, Vector3.ZERO) != Vector3.ZERO:
				keys.append(k)
		if keys.is_empty():
			keys = ["door"]
	var key: String = keys[_rng.randi() % keys.size()]
	goal = o.get(key, Vector3.ZERO)
	if goal == Vector3.ZERO:
		goal = o.get("door", Vector3(0, 0, -4))
	goal_name = {"bike": "das Velo", "door": "die Tür", "pir": "der Platz beim Bewegungsmelder"}.get(key, "das Ziel")
	goal.y = 0.0
	if goal_node != null:
		goal_node.queue_free()
	goal_node = Node3D.new()
	root.add_child(goal_node)
	goal_node.position = goal
	var beam := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.5
	cm.bottom_radius = 0.7
	cm.height = 7.0
	beam.mesh = cm
	beam.position.y = 3.5
	beam.material_override = _glow(Color(0.2, 1.0, 0.4, 0.28))
	beam.layers = 16                                       # only the players see it (not Motion Watch)
	goal_node.add_child(beam)


func _glow(c: Color) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = c
	if c.a < 1.0:
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	return mat


var _starts: Array = []


func start_point(i: int) -> Vector3:
	var p: Vector3
	if i < _starts.size():
		p = _starts[i]
	else:
		p = Vector3(-9.0 + 6.0 * i, 0, -46.0)
	return main.free_spot(p, 0.6, true)


func _new_starts(random: bool) -> void:
	_starts.clear()
	for i in range(MAX_P):
		if not random:
			_starts.append(Vector3(-9.0 + 6.0 * i, 0, -46.0))
			continue
		var best := Vector3.ZERO
		for _t in range(20):                               # apart from the others
			var c := Vector3(_rng.randf_range(-30.0, 30.0), 0, _rng.randf_range(-50.0, -42.0))
			var ok := true
			for s in _starts:
				if c.distance_to(s) < 5.0:
					ok = false
			if ok:
				best = c
				break
		_starts.append(best if best != Vector3.ZERO else Vector3(-9.0 + 6.0 * i, 0, -46.0))


func _clear_items() -> void:
	for it in items:
		if is_instance_valid(it["node"]):
			it["node"].queue_free()
	items.clear()


func _place_items(n: int) -> void:
	"""shining crystals between the starts and the goal (only the players see them)"""
	_clear_items()
	for i in range(n):
		var p := Vector3.ZERO
		for _t in range(30):
			var c := Vector3(_rng.randf_range(-22.0, 22.0), 0, _rng.randf_range(-36.0, -6.0))
			if c.length() > 7.0 and c.distance_to(goal) > 4.0:
				p = main.free_spot(c, 0.6, true)
				var far := true
				for it in items:
					if p.distance_to(it["pos"]) < 6.0:
						far = false
				if far:
					break
		var nd := MeshInstance3D.new()
		var pm := PrismMesh.new()
		pm.size = Vector3(0.35, 0.45, 0.35)
		nd.mesh = pm
		nd.position = p + Vector3(0, 0.6, 0)
		nd.material_override = _glow(Color(0.35, 0.8, 1.0))
		nd.layers = 16
		root.add_child(nd)
		items.append({"node": nd, "pos": p, "by": -1})


# ---- cones of view (for beginners, only the players see them) --------------------------------------------------------
func _build_cones() -> void:
	for i in range(2):
		var fov: float = deg_to_rad(CAM_FOV[i])
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var n := 16
		for k in range(n):
			var a0 := -fov / 2.0 + fov * k / n
			var a1 := -fov / 2.0 + fov * (k + 1) / n
			st.add_vertex(Vector3.ZERO)
			st.add_vertex(Vector3(-sin(a1), 0, -cos(a1)))
			st.add_vertex(Vector3(-sin(a0), 0, -cos(a0)))
		var mi := MeshInstance3D.new()
		mi.mesh = st.commit()
		mi.material_override = _glow(Color(1.0, 0.25, 0.2, 0.18) if i == 0 else Color(1.0, 0.6, 0.1, 0.15))
		mi.layers = 16
		mi.visible = false
		root.add_child(mi)
		cones.append(mi)


func _update_cones() -> void:
	var on: bool = main.game_cones and open and count() > 0
	var dark: bool = main.is_dark()
	var L: Dictionary = main.mw.get("lights", {})
	var ir: bool = main.ir_on()
	for i in range(2):
		var c: MeshInstance3D = cones[i]
		c.visible = on
		if not on:
			continue
		var cam: Camera3D = main.cams[i]
		var r: float = [26.0, 17.0][i]
		if dark:
			r = float(main.ir_range) * 0.8 if (i == 0 and ir) else 5.0
		c.position = Vector3(cam.global_position.x, 0.06, cam.global_position.z)
		c.rotation.y = cam.global_rotation.y
		c.scale = Vector3(r, 1, r)


# ---- every frame -----------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if not open:
		guard_auto = false
		for c in cones:
			c.visible = false
		return
	_net()
	var t := now()
	for p in players:
		if p != null:
			_steer(p, dt)
	if round_state == "countdown" and t >= t_start:
		round_state = "play"
		for p in players:
			if p != null and p["role"] == "runner":
				p["actor"].frozen = false
	if round_state == "play":
		_ref_t -= dt
		if _ref_t <= 0.0:
			_ref_t = 0.2
			_referee(0.2)
		if t >= t_end or _all_done():
			end_round()
	_guard(dt)
	_update_cones()
	for it in items:
		if is_instance_valid(it["node"]):
			it["node"].rotation.y += dt * 2.0
	for s in stones.duplicate():
		if t > float(s[1]):
			s[0].queue_free()
			stones.erase(s)
	_st_t -= dt
	if _st_t <= 0.0:
		_st_t = 0.2
		for i in range(MAX_P):
			if players[i] != null:
				_send_state(i)
	_send_guard_view()
	if not capturing:
		_capture_next()


func _net() -> void:
	while http.is_connection_available():
		var c := http.take_connection()
		c.set_no_delay(true)
		http_conns.append([c, PackedByteArray(), now()])
	for h in http_conns.duplicate():
		var c: StreamPeerTCP = h[0]
		c.poll()
		if c.get_status() != StreamPeerTCP.STATUS_CONNECTED or now() - float(h[2]) > 5.0:
			http_conns.erase(h)
			continue
		var n := c.get_available_bytes()
		if n > 0:
			var r: Array = c.get_partial_data(n)
			h[1].append_array(r[1])
		var txt: String = (h[1] as PackedByteArray).get_string_from_utf8()
		if txt.contains("\r\n\r\n"):
			var path := txt.get_slice(" ", 1)
			var body := PAGE.replace("%WSPORT%", str(ws_port)).to_utf8_buffer() if path == "/" or path.begins_with("/?") else "nicht gefunden".to_utf8_buffer()
			var head := "HTTP/1.1 %s\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: %d\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n" % [
					"200 OK" if body.size() > 20 else "404 Not Found", body.size()]
			c.put_data(head.to_utf8_buffer() + body)
			c.disconnect_from_host()
			http_conns.erase(h)
	while wss.is_connection_available():
		var tcp := wss.take_connection()
		var w := WebSocketPeer.new()
		w.outbound_buffer_size = 4 << 20
		w.inbound_buffer_size = 1 << 16
		w.max_queued_packets = 64
		if w.accept_stream(tcp) == OK:
			socks.append({"ws": w, "slot": -1, "t": now()})
	for s in socks.duplicate():
		var w: WebSocketPeer = s["ws"]
		w.poll()
		var st := w.get_ready_state()
		if st == WebSocketPeer.STATE_CLOSED or (st == WebSocketPeer.STATE_CONNECTING and now() - float(s["t"]) > 5.0):
			socks.erase(s)
			if int(s["slot"]) >= 0 and players[s["slot"]] != null and players[s["slot"]]["sock"] == s:
				players[s["slot"]]["sock"] = null
				players[s["slot"]]["gone_t"] = now()
			continue
		while w.get_available_packet_count() > 0:
			var pkt := w.get_packet()
			if not w.was_string_packet():
				continue
			var m = JSON.parse_string(pkt.get_string_from_utf8())
			if typeof(m) == TYPE_DICTIONARY:
				_message(s, m)
	for i in range(MAX_P):                                 # gone for 30 s: the place is free again
		var p = players[i]
		if p != null and p["sock"] == null and now() - float(p["gone_t"]) > 30.0:
			_remove(i)
			paint()


func _hello(p: Dictionary) -> void:
	var q: Array = QUAL.get(main.game_quality, QUAL["mid"])
	p["sock"]["ws"].send_text(JSON.stringify({"t": "hello", "slot": p["slot"], "color": "#" + COLORS[p["slot"]].to_html(false),
			"cname": CNAMES[p["slot"]], "name": p["name"], "w": q[0], "h": q[1], "goal": goal_name, "role": p["role"]}))


func _message(s: Dictionary, m: Dictionary) -> void:
	var t := str(m.get("t", ""))
	if t == "join":
		var token := str(m.get("token", "")).left(40)
		var name := str(m.get("name", "")).strip_edges().left(16)
		var slot := -1
		for i in range(MAX_P):                             # back again (page reloaded, phone was asleep)
			if players[i] != null and players[i]["token"] == token and token != "":
				slot = i
		if slot < 0:
			for i in range(MAX_P):
				if players[i] == null:
					slot = i
					break
		if slot < 0:
			s["ws"].send_text(JSON.stringify({"t": "full"}))
			return
		var lk = m.get("look", {})
		if players[slot] == null:
			players[slot] = _new_player(slot, token, name, _clean_look(lk))
			players[slot]["team"] = _smaller_team(slot)
			_paint_cone(players[slot])
		var p: Dictionary = players[slot]
		if name != "":
			p["name"] = name
		p["sock"] = s
		p["want"] = false
		s["slot"] = slot
		_hello(p)
		paint()
		return
	var slot2 := int(s["slot"])
	if slot2 < 0 or players[slot2] == null:
		return
	var p2: Dictionary = players[slot2]
	match t:
		"in":
			p2["mx"] = clamp(float(m.get("mx", 0.0)), -1.0, 1.0)
			p2["my"] = clamp(float(m.get("my", 0.0)), -1.0, 1.0)
			var look: float = deg_to_rad(clamp(float(m.get("look", 0.0)), -90.0, 90.0))
			var pit: float = deg_to_rad(clamp(float(m.get("pitch", 0.0)), -45.0, 45.0))
			if p2["role"] == "guard":                     # the guard turns the head with the drag too
				guard_yaw = wrapf(guard_yaw - look * 0.6, -PI, PI)
				guard_tilt = clamp(guard_tilt - pit * 0.6, deg_to_rad(-40.0), deg_to_rad(15.0))
			else:
				p2["yaw"] = wrapf(float(p2["yaw"]) - look, -PI, PI)
				p2["pitch"] = clamp(float(p2["pitch"]) - pit, deg_to_rad(-40.0), deg_to_rad(15.0))
			p2["actor"].ctl_run = bool(m.get("run", false))
			p2["actor"].ctl_posture = clampi(int(m.get("pos", 0)), 0, 2)
		"frame":
			p2["want"] = true
		"start":
			start_round()
		"team":
			if round_state not in ["countdown", "play"]:
				p2["team"] = clampi(int(m.get("k", 0)), 0, 1)
				_paint_cone(p2)
				paint()
		"look":
			if round_state not in ["countdown", "play"]:
				p2["look"] = _clean_look(m)
				_rebuild(p2)
		"sig":
			_signal(p2, str(m.get("k", "")))
		"role":
			_set_role(p2, str(m.get("r", "runner")))
		"stone":
			_throw(p2)
		"light":
			_guard_light(p2)
		"catch":
			_guard_catch(p2)


func _set_role(p: Dictionary, r: String) -> void:
	if round_state in ["countdown", "play"]:
		return
	if r == "guard":
		if main.game_mode != "guard":
			return
		var g = guard_player()
		if g != null and g != p:
			_say(p, "%s ist schon Wächter" % g["name"], 3.0)
			return
		p["role"] = "guard"
	else:
		p["role"] = "runner"
	var a = p["actor"]
	a.visible = p["role"] == "runner"
	if p["role"] == "guard":
		a.position = Vector3(0, 0, 4.0)                    # the guard has no figure in the world
	else:
		_to_start(p)
	if p["sock"] != null:
		_hello(p)
	paint()


func _clean_look(m) -> Dictionary:
	if typeof(m) != TYPE_DICTIONARY:
		return {}
	var h := str(m.get("hat", ""))
	return {"hat": h if h in ["", "cap", "hood"] else "", "pack": bool(m.get("pack", false)), "camo": bool(m.get("camo", false))}


func _smaller_team(me: int) -> int:
	var n := [0, 0]
	for q in players:
		if q != null and q["slot"] != me:
			n[int(q.get("team", 0))] += 1
	return 0 if n[0] <= n[1] else 1


func on_teams() -> void:
	for p in players:
		if p != null:
			_paint_cone(p)
	paint()


func _paint_cone(p: Dictionary) -> void:
	"""the cone above the head: team colour with teams, else the colour of the player"""
	var c: Color = TEAM_COLORS[int(p.get("team", 0))] if main.game_teams else COLORS[p["slot"]]
	if p.has("cone") and is_instance_valid(p["cone"]):
		p["cone"].material_override = _glow(c)


func _rebuild(p: Dictionary) -> void:
	"""a new look: build the figure again at the same place"""
	var old = p["actor"]
	var parts := _make_actor(p["slot"], p["look"], old.position)
	var a = parts[0]
	a.heading = old.heading
	a.rotation.y = old.rotation.y
	a.frozen = old.frozen
	a.visible = old.visible
	old.queue_free()
	p["actor"] = a
	p["cone"] = parts[1]
	p["loot"] = parts[2]
	p["loot"].visible = p["carry"]
	_paint_cone(p)


func _make_actor(slot: int, lk: Dictionary, pos: Vector3) -> Array:
	var a = Actor.new()
	a.controlled = true
	a.player_color = COLORS[slot]
	a.look = lk
	root.add_child(a)
	a.setup(main, "person", pos, goal, 1.5)
	a.frozen = round_state == "countdown"
	# a small coloured cone above the head: the others see who is who (only the players, not Motion Watch)
	var cone := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.0
	cm.bottom_radius = 0.14
	cm.height = 0.25
	cone.mesh = cm
	cone.rotation.x = PI
	cone.position.y = 2.15
	cone.material_override = _glow(COLORS[slot])
	cone.layers = 16
	a.add_child(cone)
	var loot := MeshInstance3D.new()                       # the loot on the back (game goal «bring it back»; Motion Watch sees it)
	var lm := BoxMesh.new()
	lm.size = Vector3(0.32, 0.26, 0.2)
	loot.mesh = lm
	var lmat := StandardMaterial3D.new()
	lmat.albedo_color = Color(0.85, 0.65, 0.15)
	lmat.metallic = 0.6
	loot.material_override = lmat
	loot.position = Vector3(0, 1.3, 0.24)
	loot.visible = false
	a.body_root.add_child(loot)
	return [a, cone, loot]


func _new_player(slot: int, token: String, name: String, lk := {}) -> Dictionary:
	var parts := _make_actor(slot, lk, start_point(slot))
	var a = parts[0]
	var cone = parts[1]
	var loot = parts[2]
	var q: Array = QUAL.get(main.game_quality, QUAL["mid"])
	var vp := SubViewport.new()
	vp.size = Vector2i(q[0], q[1])
	vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	vp.msaa_3d = Viewport.MSAA_DISABLED
	add_child(vp)
	var cam := Camera3D.new()
	cam.fov = 70.0
	cam.cull_mask = 1 | 16
	cam.near = 0.1
	cam.far = 400.0
	var ca := CameraAttributesPractical.new()
	cam.attributes = ca
	vp.add_child(cam)
	var to_goal: Vector3 = goal - a.position
	var p := {"slot": slot, "token": token, "name": name if name != "" else CNAMES[slot], "sock": null, "gone_t": now(),
			"actor": a, "vp": vp, "cam": cam, "attr": ca, "gain": 1.0, "yaw": atan2(-to_goal.x, -to_goal.z), "pitch": deg_to_rad(-12.0),
			"mx": 0.0, "my": 0.0, "want": false, "last_cap": 0.0, "susp": 0.0, "seen": false, "heard": 0.0, "caught": 0,
			"state": "play" if round_state == "play" else "lobby", "t_goal": 0.0, "safe_until": 0.0, "msg": "", "msg_until": 0.0,
			"role": "runner", "items": 0, "stone_t": 0.0, "catches": 0, "false": 0, "catch_t": 0.0, "sent_no": -1,
			"loot": loot, "carry": false, "cone": cone, "look": lk, "team": 0, "sig_t": 0.0}
	return p


func _remove(i: int) -> void:
	var p = players[i]
	if p == null:
		return
	if p["sock"] != null:
		p["sock"]["slot"] = -1
	p["actor"].queue_free()
	p["vp"].queue_free()
	players[i] = null


# ---- moving and the own view -------------------------------------------------------------------------------------------
func _steer(p: Dictionary, dt: float) -> void:
	var a = p["actor"]
	if p["role"] == "guard":
		a.ctl_move = Vector2.ZERO
		return
	var yaw: float = p["yaw"]
	var fwd := Vector2(-sin(yaw), -cos(yaw))
	var right := Vector2(cos(yaw), -sin(yaw))
	var mv: Vector2 = right * float(p["mx"]) + fwd * (-float(p["my"]))
	a.ctl_move = mv if p["state"] in ["lobby", "play"] else Vector2.ZERO
	var cam: Camera3D = p["cam"]
	if p["state"] == "out":                                # out of lives: watches somebody who still plays
		var other = null
		for q in players:
			if q != null and q["role"] == "runner" and q["state"] == "play":
				other = q
		var c: Vector3 = goal if other == null else other["actor"].position
		var oy := now() * 0.3
		cam.look_at_from_position(c + Vector3(sin(oy) * 6.0, 4.0, cos(oy) * 6.0), c + Vector3(0, 0.8, 0), Vector3.UP)
		return
	# the camera: behind and above the figure, lower when crouching / crawling
	var post: int = a.ctl_posture
	var back: float = [3.2, 2.7, 2.3][post]
	var up: float = [1.95, 1.45, 0.95][post]
	var pos: Vector3 = a.position + Vector3(sin(yaw) * back, up, cos(yaw) * back)
	var q2: Vector2 = main.keep_out(Vector2(pos.x, pos.z), 0.25, true)
	pos.x = q2.x
	pos.z = q2.y
	if p["state"] == "goal":                               # at the goal: slowly round the figure
		var oy2 := now() * 0.4
		pos = a.position + Vector3(sin(oy2) * 4.0, 2.4, cos(oy2) * 4.0)
		cam.look_at_from_position(pos, a.position + Vector3(0, 1.0, 0), Vector3.UP)
		return
	cam.position = cam.position.lerp(pos, clamp(dt * 10.0, 0.0, 1.0)) if cam.position.distance_to(pos) < 4.0 else pos
	cam.rotation = Vector3(float(p["pitch"]), yaw, 0)


func _capture_next() -> void:
	var t := now()
	var best: Dictionary = {}
	var late := 0.0
	var q: Array = QUAL.get(main.game_quality, QUAL["mid"])
	for p in players:
		if p == null or not p["want"] or p["sock"] == null or p["role"] == "guard":
			continue
		var over: float = (t - float(p["last_cap"])) * float(q[2])
		if over >= 1.0 and over > late:
			late = over
			best = p
	if not best.is_empty():
		_capture(best, q)


func _capture(p: Dictionary, q: Array) -> void:
	capturing = true
	p["last_cap"] = now()
	var vp: SubViewport = p["vp"]
	if vp.size != Vector2i(q[0], q[1]):
		vp.size = Vector2i(q[0], q[1])
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	capturing = false
	if players[p["slot"]] != p or p["sock"] == null or not is_instance_valid(vp):
		return
	var img := vp.get_texture().get_image()
	if img == null or img.is_empty():
		return
	_exposure(p, img)
	var w: WebSocketPeer = p["sock"]["ws"]
	if w.get_ready_state() == WebSocketPeer.STATE_OPEN and w.get_current_outbound_buffered_amount() < 600000:
		w.send(img.save_jpg_to_buffer(float(q[3])))
		p["want"] = false


func _send_guard_view() -> void:
	"""the guard sees what Motion Watch sees: the picture of the head camera (with grain, light, raindrops)"""
	var g = guard_player()
	if g == null or g["sock"] == null or not g["want"]:
		return
	if int(main.frame_no[0]) == int(g["sent_no"]):
		return
	var w: WebSocketPeer = g["sock"]["ws"]
	if w.get_ready_state() == WebSocketPeer.STATE_OPEN and w.get_current_outbound_buffered_amount() < 600000:
		g["sent_no"] = int(main.frame_no[0])
		w.send(main.latest_jpg(0))
		g["want"] = false


func _exposure(p: Dictionary, img: Image) -> void:
	"""like a phone camera: brighter at night, so the player still sees where to go"""
	var small: Image = img.duplicate()
	small.resize(24, 14, Image.INTERPOLATE_BILINEAR)
	var sum := 0.0
	for y in range(14):
		for x in range(24):
			var c := small.get_pixel(x, y)
			sum += (c.r + c.g + c.b) / 3.0
	var mean: float = max(0.01, sum / (24.0 * 14.0))
	var want: float = clamp(float(p["gain"]) * 0.33 / mean, 0.7, 10.0)
	p["gain"] = float(p["gain"]) + (want - float(p["gain"])) * 0.3
	(p["attr"] as CameraAttributesPractical).exposure_multiplier = p["gain"]


# ---- the round -------------------------------------------------------------------------------------------------------
func start_round() -> void:
	if not open or count() == 0 or round_state in ["countdown", "play"]:
		return
	var runners := 0
	for p in players:
		if p != null and p["role"] == "runner":
			runners += 1
	if runners == 0:
		return
	if main.game_mode != "guard":                          # no player as guard in this mode
		for p in players:
			if p != null and p["role"] == "guard":
				_set_role(p, "runner")
	_new_starts(main.game_random)
	_pick_goal(main.game_random)
	_place_items(int(main.game_items))
	round_state = "countdown"
	t_start = now() + 4.0
	t_end = t_start + float(main.game_minutes) * 60.0
	results.clear()
	light_ready = 0.0
	for p in players:
		if p == null:
			continue
		p["caught"] = 0
		p["items"] = 0
		p["catches"] = 0
		p["false"] = 0
		p["stone_t"] = 0.0
		p["t_goal"] = 0.0
		p["carry"] = false
		p["loot"].visible = false
		if p["role"] == "guard":
			p["state"] = "play"
			continue
		_to_start(p)
		p["state"] = "play"
		p["actor"].visible = true
		p["actor"].frozen = true
	if guard_player() != null:
		guard_yaw = 0.0
		guard_tilt = deg_to_rad(-9.0)
	paint()


func end_round() -> void:
	if round_state not in ["countdown", "play"]:
		return
	round_state = "end"
	results.clear()
	var missed := 0
	for p in players:
		if p != null and p["role"] == "runner" and p["state"] != "goal":
			missed += 1
	for p in players:
		if p == null:
			continue
		var sc: int
		var info := ""
		if p["role"] == "guard":
			sc = max(0, 150 * int(p["catches"]) - 50 * int(p["false"]) + 100 * missed)
			info = "Wächter · %d× erwischt, %d× Fehlalarm" % [p["catches"], p["false"]]
		else:
			var d: float = p["actor"].position.distance_to(goal)
			if p["state"] == "goal":
				sc = 1000 - int((float(p["t_goal"]) - t_start) * 2.0)
				info = "🏁 %d:%02d" % [int(float(p["t_goal"]) - t_start) / 60, int(float(p["t_goal"]) - t_start) % 60]
			elif p["state"] == "out":
				sc = 0
				info = "keine Leben mehr"
			else:
				sc = max(0, 300 - int(d * 6.0))
				info = "noch %d m" % int(d)
			sc = max(0, sc - 150 * int(p["caught"]) + 100 * int(p["items"]))
			info += " · %d× erwischt" % p["caught"] + (" · 💎 %d" % p["items"] if int(p["items"]) > 0 else "")
		results.append({"n": p["name"], "c": "#" + COLORS[p["slot"]].to_html(false), "info": info, "score": sc})
		if p["role"] == "runner":
			p["state"] = "lobby"
			p["actor"].frozen = false
			p["actor"].visible = true
		else:
			p["state"] = "lobby"
		p["susp"] = 0.0
	results.sort_custom(func(x, y): return x["score"] > y["score"])
	team_results.clear()
	if main.game_teams:                                    # team totals
		var sums := [0, 0]
		for p in players:
			if p != null:
				for r in results:
					if r["n"] == p["name"] and r["c"] == "#" + COLORS[p["slot"]].to_html(false):
						sums[int(p["team"])] += int(r["score"])
		team_results = [{"n": TEAM_NAMES[0], "c": "#" + TEAM_COLORS[0].to_html(false), "score": sums[0]},
				{"n": TEAM_NAMES[1], "c": "#" + TEAM_COLORS[1].to_html(false), "score": sums[1]}]
		team_results.sort_custom(func(x, y): return x["score"] > y["score"])
	_clear_items()
	paint()


func _all_done() -> bool:
	for p in players:
		if p != null and p["role"] == "runner" and p["state"] == "play":
			return false
	return true


func _to_start(p: Dictionary) -> void:
	var a = p["actor"]
	a.position = start_point(p["slot"])
	a.cur_speed = 0.0
	var to_goal: Vector3 = goal - a.position
	p["yaw"] = atan2(-to_goal.x, -to_goal.z)
	p["pitch"] = deg_to_rad(-12.0)
	a.heading = p["yaw"]
	a.rotation.y = a.heading
	p["susp"] = 0.0
	p["cam"].position = a.position + Vector3(sin(p["yaw"]) * 3.2, 1.95, cos(p["yaw"]) * 3.2)


# ---- the referee -----------------------------------------------------------------------------------------------------
func light_at(pos: Vector3, i: int) -> float:
	"""how much light a camera has on this place (1 = day). Night: lamps of the scene, the white light of the head,
	the infrared light (only the head camera sees it)"""
	if not main.is_dark():
		return {"cloudy": 0.85, "rain": 0.7, "fog": 0.75, "snow": 0.8}.get(main.weather, 1.0)
	var l: float = 0.05 + 0.1 * float(main.moon)
	for lamp in main.lamps:
		if is_instance_valid(lamp) and lamp is OmniLight3D and lamp.light_energy > 0.05:
			var r: float = lamp.omni_range
			var d: float = lamp.global_position.distance_to(pos)
			if d < r:
				l = max(l, 0.85 * (1.0 - d / r))
	var L: Dictionary = main.mw.get("lights", {})
	var head: Vector3 = main.cams[0].global_position
	var dh := head.distance_to(pos)
	var in_beam: bool = main.cams[0].is_position_in_frustum(pos + Vector3(0, 0.8, 0))
	if (L.get("white", false) or now() < flash_until) and in_beam:
		l = max(l, clamp(1.15 - dh / 25.0, 0.0, 1.0))
	if i == 0 and main.ir_on() and in_beam:
		l = max(l, clamp(0.95 * (1.0 - dh / float(main.ir_range)), 0.0, 0.85))
	return l


func cam_sees(p: Dictionary, i: int) -> float:
	"""how surely camera i (0 head, 1 fixed, 2 thermal) notices this player (0..1)"""
	var a = p["actor"]
	var post: int = a.ctl_posture
	var pos: Vector3 = a.position
	var h: float = HEIGHT[post]
	var spd: float = a.cur_speed
	var cam: Camera3D = main.cams[i]
	var cp := cam.global_position
	var d: float = max(0.5, cp.distance_to(pos))
	if d > 70.0:
		return 0.0
	if not (cam.is_position_in_frustum(pos + Vector3(0, h * 0.85, 0)) or cam.is_position_in_frustum(pos + Vector3(0, h * 0.4, 0))):
		return 0.0
	if not main.line_free(cp, pos + Vector3(0, h * 0.95, 0)):
		return 0.0                                         # hidden (the line of sight to the top of the head)
	var rows: float = TH_H if i == 2 else CAM_H[i]
	var px: float = h / (2.0 * d * tan(deg_to_rad(VFOV[i]) / 2.0)) * rows    # height of the person in the picture
	if i == 2:                                             # thermal: a warm spot, also at night, not through fog well
		var contrast: float = clamp(abs(34.0 - float(main.ambient)) / 18.0, 0.2, 1.0) * {"fog": 0.7, "rain": 0.8}.get(main.weather, 1.0)
		return smoothstep(2.5, 9.0, px) * contrast * (0.65 + 0.35 * clamp(spd, 0.0, 1.0))   # a warm spot of a few pixels
	var light := light_at(pos, i)
	var optic: float = {"fog": 0.4, "rain": 0.75, "snow": 0.7}.get(main.weather, 1.0)
	var see := light * optic
	var cols: float = CAM_W[i]
	var hfov: float = deg_to_rad(CAM_FOV[i])
	# person detection (AI): needs enough pixels, a recognisable shape and light
	var ai: float = smoothstep(18.0, 70.0, px) * SHAPE[post] * smoothstep(0.08, 0.5, see)
	if bool(a.look.get("camo", false)) and not main.is_dark() and main.scene != "parkplatz":
		ai *= 0.8                                          # camouflage in the green: the person is a bit harder to recognise
	# motion detection: something moves across the picture (pixels per second), big enough, visible
	var move_px: float = spd / (2.0 * d * tan(hfov / 2.0)) * cols
	var motion: float = smoothstep(6.0, 45.0, move_px) * smoothstep(20.0, 60.0, px) * smoothstep(0.03, 0.3, see)
	return max(ai * 0.9, motion)


func visibility(p: Dictionary) -> float:
	"""how well the cameras see this player right now (0 = not at all, 1 = clearly)"""
	var best := 0.0
	var sum := 0.0
	for i in range(3):
		var f := cam_sees(p, i)
		sum += f
		best = max(best, f)
	return best + 0.35 * (sum - best)


func hearing(p: Dictionary) -> float:
	"""the microphone at the head hears loud steps (running!), less in rain or wind"""
	if not main.game_noise:
		return 0.0
	var a = p["actor"]
	var spd: float = a.cur_speed
	if spd < 0.2:
		return 0.0
	var loud: float = LOUD[a.ctl_posture] * (3.3 if spd > 2.2 else 1.0)
	loud *= (0.5 if main.weather == "rain" else 1.0) * (0.6 if main.wind > 30.0 else 1.0)
	var d: float = a.position.distance_to(Vector3.ZERO)
	var reach: float = 3.0 + 12.0 * loud
	return clamp(loud * (1.0 - d / reach), 0.0, 1.0)


func vis_debug(p: Dictionary) -> Array:
	"""for tests: per camera [distance, in the picture, what hides, how surely it notices]"""
	var out := []
	var pos: Vector3 = p["actor"].position
	for i in range(3):
		var cam: Camera3D = main.cams[i]
		out.append([snappedf(cam.global_position.distance_to(pos), 0.1), cam.is_position_in_frustum(pos + Vector3(0, 1.0, 0)),
				str(main.line_blocker(cam.global_position, pos + Vector3(0, HEIGHT[p["actor"].ctl_posture] * 0.95, 0)).get("c", "")),
				snappedf(cam_sees(p, i), 0.01)])
	return out


func mw_decides() -> bool:
	"""game mode «Motion Watch entscheidet» and Motion Watch is connected (and sends its detections, from 2.93.3)"""
	return main.game_mode == "mw" and main.now() - main.mw_det_t < 3.0


func _mw_referee() -> void:
	"""the real detection of Motion Watch decides: it reports a person -> the player the cameras see best is caught"""
	if int(main.mw_det.get("persons", 0)) <= 0 or now() < _mw_catch_t:
		return
	var best = null
	var top := 0.02
	for p in players:
		if p == null or p["role"] != "runner" or p["state"] != "play" or now() < float(p["safe_until"]):
			continue
		var f: float = max(cam_sees(p, 0), cam_sees(p, 1))
		if f > top:
			top = f
			best = p
	if best != null:
		_mw_catch_t = now() + 3.0
		_caught(best, null)
		_say(best, "Motion Watch hat dich erkannt!", 3.0)


func _referee(dt: float) -> void:
	var lv: float = LEVEL.get(main.game_level, 1.0)
	var mw := mw_decides()
	if mw:
		_mw_referee()
	for p in players:
		if p == null or p["state"] != "play" or p["role"] != "runner":
			continue
		var a = p["actor"]
		for it in items:                                   # collecting
			if int(it["by"]) < 0 and a.position.distance_to(it["pos"]) < 1.3:
				it["by"] = p["slot"]
				p["items"] = int(p["items"]) + 1
				it["node"].visible = false
				_say(p, "💎 gefunden! (+100)", 2.5)
				_event(p, "item")
		if main.game_goal == "return" and not p["carry"] and a.position.distance_to(goal) < 1.7:
			p["carry"] = true                              # the loot: now back to the start
			p["loot"].visible = true
			_say(p, "💰 Beute geholt – zurück zum Start!", 3.0)
			_event(p, "item")
			continue
		var home := start_point(p["slot"])
		if (main.game_goal != "return" and a.position.distance_to(goal) < 1.7) or (p["carry"] and a.position.distance_to(home) < 3.0):
			p["state"] = "goal"
			p["t_goal"] = now()
			a.frozen = true
			_say(p, "Im Ziel! 🎉", 4.0)
			a.play_emote("goal", 5.0)
			_event(p, "goal")
			paint()
			continue
		if now() < float(p["safe_until"]):
			p["seen"] = false
			p["heard"] = 0.0
			continue
		var v := visibility(p)
		var hr := hearing(p)
		if v < 0.1:
			v = 0.0                                        # like a real detection: below its threshold nothing counts
		p["seen"] = v > 0.0
		p["heard"] = hr
		if hr > 0.25:
			attention = a.position
			attention_until = now() + 3.0
		var rate := v * 55.0 + hr * 30.0
		if rate > 0.5:
			p["susp"] = min(100.0, float(p["susp"]) + rate * lv * dt)
		else:
			p["susp"] = max(0.0, float(p["susp"]) - 8.0 * dt)
		if float(p["susp"]) >= 100.0:
			if mw:
				p["susp"] = 99.0                           # the meter only hints: Motion Watch itself decides
			else:
				_caught(p, null)


func _caught(p: Dictionary, by) -> void:
	p["caught"] = int(p["caught"]) + 1
	if p["carry"]:                                         # the loot goes back to its place
		p["carry"] = false
		p["loot"].visible = false
	flash_until = now() + 3.0                             # the light goes on, like at a real alarm
	var g = by if by != null else guard_player()
	if g != null:
		g["catches"] = int(g["catches"]) + 1
	_event(p, "caught")
	p["actor"].play_emote("caught", 1.5)
	var lives := int(main.game_lives)
	if lives > 0 and int(p["caught"]) >= lives:
		p["state"] = "out"
		p["actor"].visible = false
		p["actor"].position = Vector3(0, 0, 4.0)
		_say(p, "Erwischt – keine Leben mehr. Du schaust zu.", 5.0)
	else:
		_say(p, "Erwischt! Zurück zum Start", 3.0)
		_to_start(p)
		p["safe_until"] = now() + 3.0
	paint()


func _event(p: Dictionary, k: String) -> void:
	if p["sock"] != null:
		p["sock"]["ws"].send_text(JSON.stringify({"t": "ev", "k": k}))


func _say(p: Dictionary, txt: String, secs: float) -> void:
	p["msg"] = txt
	p["msg_until"] = now() + secs


# ---- stones, light, «Erwischt!» --------------------------------------------------------------------------------------
func _throw(p: Dictionary) -> void:
	"""a stone lands about 10 m ahead: noise there - the automatic guard looks there, a player guard hears it"""
	if not main.game_stones or p["role"] != "runner" or p["state"] != "play" or round_state != "play":
		return
	if now() < float(p["stone_t"]):
		return
	p["stone_t"] = now() + STONE_EVERY
	p["actor"].play_emote("throw", 0.6)
	var yaw: float = p["yaw"]
	var to: Vector3 = p["actor"].position + Vector3(-sin(yaw), 0, -cos(yaw)) * 10.0
	to = main.free_spot(to, 0.3, true)
	var s := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.09
	sm.height = 0.14
	s.mesh = sm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.5, 0.5, 0.48)
	s.material_override = mat
	s.position = to + Vector3(0, 0.07, 0)
	root.add_child(s)
	stones.append([s, now() + 8.0])
	main.add_sound(-14.0, to, 0.6)                         # the microphone of Motion Watch hears it too
	attention = to
	attention_until = now() + 4.0
	var g = guard_player()
	if g != null:
		var rel := rad_to_deg(wrapf(atan2(-to.x, -to.z) - guard_yaw, -PI, PI))
		_say(g, "🔊 Geräusch " + ("links" if rel > 15.0 else ("rechts" if rel < -15.0 else "vorne")), 3.0)
	_say(p, "🪨 geworfen – der Wächter hört es", 2.0)


func _signal(p: Dictionary, k: String) -> void:
	"""a short sign to the team (or to everybody without teams): wait, go, camera looks here, here"""
	if not SIGNALS.has(k) or now() < float(p["sig_t"]):
		return
	p["sig_t"] = now() + 1.0
	var a = p["actor"]
	var lb := Label3D.new()                                # above the head, only the players see it
	lb.text = SIGNALS[k]
	lb.font_size = 64
	lb.pixel_size = 0.004
	lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lb.no_depth_test = true
	lb.modulate = TEAM_COLORS[int(p["team"])] if main.game_teams else COLORS[p["slot"]]
	lb.outline_size = 12
	lb.position = Vector3(0, 2.55, 0)
	lb.layers = 16
	a.add_child(lb)
	get_tree().create_timer(2.5).timeout.connect(func(): if is_instance_valid(lb): lb.queue_free())
	for q in players:
		if q == null or q == p or q["sock"] == null:
			continue
		if main.game_teams and int(q["team"]) != int(p["team"]):
			continue
		var to: Vector3 = a.position - q["actor"].position
		var ga := rad_to_deg(wrapf(atan2(-to.x, -to.z) - float(q["yaw"]), -PI, PI))
		q["sock"]["ws"].send_text(JSON.stringify({"t": "sig", "n": p["name"], "c": "#" + COLORS[p["slot"]].to_html(false), "k": k,
				"txt": SIGNALS[k], "ga": int(ga), "d": int(to.length())}))


func _guard_light(g: Dictionary) -> void:
	if g["role"] != "guard" or now() < light_ready:
		return
	light_ready = now() + LIGHT_EVERY
	flash_until = now() + 6.0


func _guard_catch(g: Dictionary) -> void:
	"""the guard calls «Erwischt!»: right if the head camera sees somebody (meter at least 30 %)"""
	if g["role"] != "guard" or round_state != "play" or now() < float(g["catch_t"]):
		return
	var hit = null
	for p in players:
		if p != null and p["role"] == "runner" and p["state"] == "play" and float(p["susp"]) >= 30.0 and cam_sees(p, 0) > 0.02:
			hit = p
	if hit == null:
		g["false"] = int(g["false"]) + 1
		g["catch_t"] = now() + 4.0
		_say(g, "Fehlalarm! (−50, 4 s warten)", 3.0)
		return
	_say(g, "✓ %s erwischt! (+150)" % hit["name"], 3.0)
	_caught(hit, g)


func _guard(dt: float) -> void:
	"""the head: a player as guard turns it with the joystick; without Motion Watch it guards by itself
	(swings to and fro, turns towards noises and suspects)"""
	var g = guard_player()
	if g != null and main.game_mode == "guard":
		guard_auto = true
		guard_yaw = wrapf(guard_yaw - float(g["mx"]) * 1.3 * dt, -PI, PI)
		guard_tilt = clamp(guard_tilt - float(g["my"]) * 0.7 * dt, deg_to_rad(-40.0), deg_to_rad(15.0))
		return
	guard_auto = main.game_guard and count() > 0 and main.now() - main.mw_t > 3.0
	if not guard_auto:
		return
	guard_tilt = deg_to_rad(-9.0)
	var want: float = 1.0 * sin(now() * 0.32)
	if now() < attention_until:
		want = atan2(-attention.x, -attention.z)
	var top := 35.0
	for p in players:
		if p != null and p["state"] == "play" and p["role"] == "runner" and float(p["susp"]) > top:
			top = float(p["susp"])
			var d: Vector3 = p["actor"].position
			want = atan2(-d.x, -d.z)
	guard_yaw = lerp_angle(guard_yaw, want, clamp(dt * 3.0, 0.0, 1.0))


# ---- what the phone shows --------------------------------------------------------------------------------------------
func _send_state(i: int) -> void:
	var p: Dictionary = players[i]
	if p["sock"] == null:
		return
	var w: WebSocketPeer = p["sock"]["ws"]
	if w.get_ready_state() != WebSocketPeer.STATE_OPEN:
		return
	var a = p["actor"]
	var target: Vector3 = start_point(p["slot"]) if p["carry"] else goal
	var to: Vector3 = target - a.position
	var ga := rad_to_deg(wrapf(atan2(-to.x, -to.z) - float(p["yaw"]), -PI, PI))
	var lst := []
	for q in players:
		if q != null:
			lst.append({"n": q["name"], "c": "#" + COLORS[q["slot"]].to_html(false), "s": q["state"], "k": q["caught"], "on": q["sock"] != null,
					"r": q["role"], "i": q["items"], "tm": int(q["team"])})
	var left_items := 0
	for it in items:
		if int(it["by"]) < 0:
			left_items += 1
	var d := {"t": "st", "rs": round_state, "susp": int(p["susp"]), "seen": p["seen"], "heard": snappedf(p["heard"], 0.01),
			"caught": p["caught"], "ps": p["state"], "role": p["role"], "mode": main.game_mode, "gd": snappedf(to.length(), 0.1),
			"ga": int(ga), "goal": goal_name, "list": lst, "items": p["items"], "items_left": left_items, "items_all": items.size(),
			"lives": int(main.game_lives), "stone": int(max(0.0, float(p["stone_t"]) - now())) if main.game_stones else -1,
			"msg": p["msg"] if now() < float(p["msg_until"]) else "", "has_guard": guard_player() != null, "mwd": mw_decides(),
			"goal_mode": main.game_goal, "carry": p["carry"], "teams": main.game_teams, "team": int(p["team"]), "look": p["look"],
			"tres": team_results if round_state == "end" else []}
	if p["role"] == "guard":
		d["light"] = int(max(0.0, light_ready - now()))
		d["catch"] = int(max(0.0, float(p["catch_t"]) - now()))
		d["catches"] = p["catches"]
		d["pan"] = int(rad_to_deg(guard_yaw))
	if round_state == "countdown":
		d["cd"] = int(ceil(t_start - now()))
	if round_state == "play":
		d["left"] = int(max(0.0, t_end - now()))
	if round_state == "end":
		d["res"] = results
	w.send_text(JSON.stringify(d))


# ---- in the window: address, QR code, players ------------------------------------------------------------------------
func add_info(body, UI) -> void:
	addr_label = UI.small("", UI.TXT)
	addr_label.add_theme_font_size_override("font_size", 15)
	body.add_child(addr_label)
	qr_rect = TextureRect.new()
	qr_rect.custom_minimum_size = Vector2(170, 170)
	qr_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	qr_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	qr_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	qr_rect.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	body.add_child(qr_rect)
	info_label = UI.small("")
	body.add_child(info_label)
	paint()


func paint() -> void:
	if info_label == null:
		return
	var ad := address()
	addr_label.visible = open
	qr_rect.visible = open
	if open:
		addr_label.text = "Mit dem Handy (gleiches WLAN): QR-Code scannen oder %s öffnen" % ad
		if _qr_for != ad:
			_qr_for = ad
			qr_rect.texture = Qr.texture(ad, 4)
	var lines := PackedStringArray()
	if open and main.game_mode == "mw" and not mw_decides():
		lines.append("⚠ «Motion Watch entscheidet»: Motion Watch ist nicht verbunden (ab Version 2.93.3) – bis dahin entscheidet der Simulator.")
	if not open:
		lines.append("Bis zu 4 Spieler schleichen mit dem Handy unentdeckt zum Ziel (%s). Zuerst «Spiel öffnen»." % goal_name)
	else:
		lines.append({"lobby": "Bereit – «Runde starten» (hier oder auf einem Handy)", "countdown": "Gleich geht es los …",
				"play": "Runde läuft", "end": "Runde fertig"}.get(round_state, "") + " · Ziel: " + goal_name)
		for p in players:
			if p != null:
				var st: String = {"goal": " – im Ziel", "out": " – ausgeschieden"}.get(p["state"], "")
				lines.append("● %s (%s)%s%s%s · erwischt %d%s" % [p["name"], CNAMES[p["slot"]], (" · " + TEAM_NAMES[int(p["team"])]) if main.game_teams else "", " – Wächter" if p["role"] == "guard" else "", st,
						p["caught"] if p["role"] == "runner" else p["catches"], "" if p["sock"] != null else " · getrennt"])
		if count() == 0:
			lines.append("Noch niemand dabei.")
		if round_state == "end" and not results.is_empty():
			lines.append("Rangliste: " + ", ".join(PackedStringArray(results.map(func(r): return "%s %d" % [r["n"], r["score"]]))))
	info_label.text = "\n".join(lines)


func status() -> String:
	if not open:
		return ""
	return "Spiel: %d Spieler%s" % [count(), {"play": ", Runde läuft", "countdown": ", Start", "end": ", fertig"}.get(round_state, "")]


const PAGE := r"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="theme-color" content="#0a0e14"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">
<title>Unentdeckt ans Ziel</title>
<style>
:root{--bg:#0a0e14;--panel:#111822;--line:#1f2b3a;--txt:#e6edf3;--mut:#8b98a8;--acc:#3b8cff;--grn:#34c759;--org:#ff9f0a;--red:#ff453a}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;height:100%;background:var(--bg);color:var(--txt);font:15px system-ui,-apple-system,Segoe UI,Roboto,sans-serif;overflow:hidden;touch-action:none;user-select:none;-webkit-user-select:none}
#v{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;background:#000}
body.guard #v{object-fit:contain}
.top{position:fixed;left:0;right:0;top:0;display:flex;gap:8px;align-items:center;padding:8px 10px;padding-top:max(8px,env(safe-area-inset-top));background:linear-gradient(#000a,#0000);pointer-events:none}
.pill{background:#0a0e14cc;border:1px solid var(--line);border-radius:999px;padding:4px 10px;font-size:13px;white-space:nowrap}
#me .dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}
#meter{flex:1;max-width:340px;margin:0 auto;height:14px;border-radius:999px;background:#0a0e14cc;border:1px solid var(--line);overflow:hidden;position:relative}
#bar{height:100%;width:0;background:var(--grn);transition:width .2s,background .2s}
#eye{position:absolute;left:50%;top:-1px;transform:translateX(-50%);font-size:12px;white-space:nowrap}
#goal{display:flex;align-items:center;gap:6px}
#arrow{display:inline-block;transition:transform .2s;font-size:18px;line-height:1}
#stick{position:fixed;left:0;top:0;bottom:0;width:45%}
#look{position:fixed;right:0;top:0;bottom:0;width:55%}
.base{position:fixed;width:130px;height:130px;border-radius:50%;border:2px solid #ffffff55;background:#ffffff14;transform:translate(-50%,-50%);pointer-events:none;display:none}
.knob{position:absolute;left:50%;top:50%;width:56px;height:56px;margin:-28px;border-radius:50%;background:#ffffffaa}
.hint{position:fixed;left:16px;bottom:max(16px,env(safe-area-inset-bottom));color:#fff9;font-size:12px;pointer-events:none}
.btns{position:fixed;right:max(12px,env(safe-area-inset-right));bottom:max(12px,env(safe-area-inset-bottom));display:flex;gap:10px;align-items:flex-end}
.b{width:70px;height:70px;border-radius:50%;border:2px solid #ffffff55;background:#0a0e14aa;color:#fff;font-size:11px;font-weight:600;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;position:relative}
.b i{font-style:normal;font-size:21px}
.b.on{background:var(--acc);border-color:var(--acc)}
.b.wait{opacity:.45}
.b.big{width:86px;height:86px;font-size:13px}
.b.red{background:#ff453acc;border-color:var(--red)}
#side{position:fixed;right:10px;top:46px;display:flex;flex-direction:column;gap:8px}
#side button{width:38px;height:38px;border-radius:10px;border:1px solid var(--line);background:#0a0e14aa;color:#fff;font-size:17px}
.ov{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none}
.card{background:#111822ee;border:1px solid var(--line);border-radius:16px;padding:18px 20px;max-width:min(92vw,560px);max-height:92vh;overflow:auto;text-align:center;pointer-events:auto}
.card h1{font-size:20px;margin:0 0 8px}.card p{margin:6px 0;color:var(--mut)}
button.pr{background:var(--acc);color:#fff;border:0;border-radius:12px;padding:12px 18px;font-size:16px;font-weight:600;margin-top:10px}
button.sec{background:#151e2b;color:var(--txt);border:1px solid var(--line);border-radius:12px;padding:10px 14px;font-size:15px;margin:10px 4px 0}
button.sec.on{border-color:var(--acc);background:#3b8cff33}
input{background:#0a0e14;color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:11px 12px;font-size:16px;width:100%}
#big{font-size:96px;font-weight:800;text-shadow:0 4px 24px #000;pointer-events:none}
#msg{position:fixed;left:50%;top:22%;transform:translateX(-50%);font-size:24px;font-weight:800;text-shadow:0 2px 12px #000;pointer-events:none;text-align:center;width:90%}
table{border-collapse:collapse;margin:8px auto;font-size:14px}td{padding:4px 8px;border-bottom:1px solid var(--line);text-align:left}
#list{position:fixed;left:10px;top:44px;font-size:12px;line-height:1.5;pointer-events:none;text-shadow:0 1px 4px #000}
#extra{position:fixed;left:10px;bottom:calc(max(16px,env(safe-area-inset-bottom)) + 22px);font-size:13px;pointer-events:none;text-shadow:0 1px 4px #000}
#ear{position:fixed;left:50%;top:34px;transform:translateX(-50%);font-size:13px;pointer-events:none;opacity:0;transition:opacity .2s}
#rot{display:none;position:fixed;inset:0;background:#0a0e14f2;align-items:center;justify-content:center;text-align:center;padding:30px;font-size:18px}
@media (orientation:portrait){#rot.ask{display:flex}}
.redfl{animation:fl .4s 3}@keyframes fl{50%{background:#ff453a88}}
.cnt{position:absolute;top:-6px;right:-6px;background:#000c;border-radius:999px;font-size:11px;padding:1px 6px}
#sig{position:fixed;left:10px;top:120px;display:flex;flex-direction:column;gap:6px;z-index:5}
#sig[hidden]{display:none}
#sig button{width:46px;height:40px;border-radius:12px;border:1px solid #ffffff44;background:#0a0e14aa;color:#fff;font-size:18px}
#sigt{position:fixed;left:50%;top:58px;transform:translateX(-50%);background:#111822ee;border:1px solid var(--line);border-radius:12px;padding:6px 12px;font-size:15px;font-weight:700;pointer-events:none;opacity:0;transition:opacity .25s;white-space:nowrap}
#sigt .ar{display:inline-block;margin-left:6px}
.chips{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin:6px 0}
.chips button{background:#151e2b;color:var(--txt);border:1px solid var(--line);border-radius:999px;padding:8px 12px;font-size:14px}
.chips button.on{border-color:var(--acc);background:#3b8cff33}
.lab{font-size:12px;color:var(--mut);margin-top:8px}
.teams{display:flex;gap:10px;justify-content:center;margin:8px 0;flex-wrap:wrap}
.teams .tm{border:1px solid var(--line);border-radius:12px;padding:8px 12px;min-width:140px;text-align:left}
.teams .tm.me{border-color:var(--acc)}
.teams .tm b{display:block;margin-bottom:4px}
</style></head><body>
<img id="v" alt="">
<div class="top"><span class="pill" id="me"><span class="dot"></span><b id="nm">…</b> <span id="lv"></span></span>
<div id="meter"><div id="bar"></div><span id="eye">👁</span></div>
<span class="pill" id="goal"><span id="arrow">⬆</span><span id="gd">–</span></span><span class="pill" id="tm">–</span></div>
<div id="ear">👂 man hört dich</div>
<div id="list"></div><div id="extra"></div>
<div id="stick"></div><div id="look"></div><div class="base" id="base"><div class="knob" id="knob"></div></div>
<div class="hint" id="hint">links: gehen · rechts wischen: umschauen</div>
<div class="btns" id="rb"><div class="b" id="b-stone"><i>🪨</i>Werfen</div><div class="b" id="b-run"><i>🏃</i>Rennen</div><div class="b" id="b-crouch"><i>🧎</i>Ducken</div><div class="b" id="b-crawl"><i>🐍</i>Kriechen</div></div>
<div class="btns" id="gb" style="display:none"><div class="b" id="b-light"><i>💡</i>Licht</div><div class="b big red" id="b-catch"><i>🚨</i>Erwischt!</div></div>
<div id="side"><button id="full" title="Vollbild">⛶</button><button id="snd" title="Ton">🔊</button></div>
<div id="msg"></div>
<div id="sig" hidden><button data-k="wait" title="Warte">✋</button><button data-k="go" title="Los">▶</button><button data-k="cam" title="Kamera schaut her">👁</button><button data-k="here" title="Hier">📍</button></div>
<div id="sigt"></div>
<div class="ov" id="ov"></div>
<div id="rot"><div>📱↻<br><br>Handy bitte <b>quer</b> halten.<br><small style="color:#8b98a8">Mit dem Knopf ⛶ wird es Vollbild.</small></div></div>
<script>
const $ = s => document.querySelector(s), WSP = %WSPORT%;
let ws = null, me = null, token = "", name = "", st = {}, posture = 0, run = false, mx = 0, my = 0, look = 0, pitch = 0, lastSent = "", lastT = 0, lastFrame = 0, oldUrl = "", sound = true, role = "runner";
try { token = localStorage.getItem("mw3d-token") || ""; name = localStorage.getItem("mw3d-name") || ""; sound = localStorage.getItem("mw3d-sound") !== "0"; } catch (e) {}
if (!token) { token = Math.random().toString(36).slice(2) + Date.now().toString(36); try { localStorage.setItem("mw3d-token", token); } catch (e) {} }
let lastOv = null, editing = false;
const ov = (html) => { if (html === lastOv) return; lastOv = html; $("#ov").innerHTML = html ? '<div class="card">' + html + '</div>' : ""; };
let outfit = {hat: "", pack: false, camo: false};
try { outfit = Object.assign(outfit, JSON.parse(localStorage.getItem("mw3d-look") || "{}")); } catch (e) {}
function lookHtml() {
  const c = (grp, v, txt) => '<button type="button" data-g="' + grp + '" data-v="' + v + '" class="' + (String(outfit[grp]) === String(v) ? "on" : "") + '">' + txt + '</button>';
  return '<div class="lab">Kopf</div><div class="chips">' + c("hat", "", "Haare") + c("hat", "cap", "Mütze") + c("hat", "hood", "Kapuze") + '</div>' +
    '<div class="lab">Rucksack</div><div class="chips">' + c("pack", false, "ohne") + c("pack", true, "mit") + '</div>' +
    '<div class="lab">Jacke</div><div class="chips">' + c("camo", false, "meine Farbe") + c("camo", true, "Tarnung (im Grünen schwerer zu sehen)") + '</div>';
}
function bindLook() { document.querySelectorAll(".chips button[data-g]").forEach(b => b.onclick = () => {
  const g = b.dataset.g; outfit[g] = g === "hat" ? b.dataset.v : b.dataset.v === "true";
  try { localStorage.setItem("mw3d-look", JSON.stringify(outfit)); } catch (e) {}
  document.querySelectorAll('.chips button[data-g="' + g + '"]').forEach(x => x.classList.toggle("on", x === b)); }); }
// ---- sounds (Web Audio, no files): tick while seen, heartbeat when close to being caught, signals ----
let ac = null;
function tone(f, d, type, vol, when) { if (!sound) return; try { ac = ac || new (window.AudioContext || window.webkitAudioContext)(); const o = ac.createOscillator(), g = ac.createGain(), t = ac.currentTime + (when || 0); o.type = type || "sine"; o.frequency.value = f; g.gain.setValueAtTime(vol || 0.15, t); g.gain.exponentialRampToValueAtTime(0.001, t + d); o.connect(g); g.connect(ac.destination); o.start(t); o.stop(t + d); } catch (e) {} }
const sfx = {caught: () => { tone(220, 0.25, "sawtooth", 0.2); tone(160, 0.4, "sawtooth", 0.2, 0.22); }, goal: () => [523, 659, 784, 1046].forEach((f, i) => tone(f, 0.25, "triangle", 0.18, i * 0.12)),
  item: () => { tone(880, 0.12, "triangle", 0.15); tone(1320, 0.18, "triangle", 0.15, 0.1); }, tick: (s) => tone(400 + s * 6, 0.05, "square", 0.05), beat: () => { tone(70, 0.12, "sine", 0.35); tone(60, 0.12, "sine", 0.3, 0.16); }};
$("#snd").onclick = () => { sound = !sound; $("#snd").textContent = sound ? "🔊" : "🔇"; try { localStorage.setItem("mw3d-sound", sound ? "1" : "0"); } catch (e) {} if (sound) tone(660, 0.1); };
$("#snd").textContent = sound ? "🔊" : "🔇";
let tickT = 0, beatT = 0;
setInterval(() => { if (!me || st.rs !== "play" || st.ps !== "play" || role !== "runner") return; const n = Date.now();
  if (st.seen && n - tickT > 450) { tickT = n; sfx.tick(st.susp); } if (st.susp > 60 && n - beatT > (st.susp > 85 ? 500 : 800)) { beatT = n; sfx.beat(); } }, 100);
function joinForm() {
  ov('<h1>🕵️ Unentdeckt ans Ziel</h1><p>Schleiche zum grünen Licht, ohne dass dich die Kameras entdecken. Ducken und Kriechen hilft, im Dunkeln und hinter Dingen sieht man dich schlechter. Rennen hört man.</p>' +
     '<input id="nmi" maxlength="16" placeholder="Dein Name" value="' + name.replace(/"/g, "") + '">' + lookHtml() + '<button class="pr" id="go">Mitspielen</button>');
  bindLook();
  $("#go").onclick = () => { name = $("#nmi").value.trim(); try { localStorage.setItem("mw3d-name", name); } catch (e) {} goFull(); tone(660, 0.05, "sine", 0.01); connect(); };
}
function connect() {
  ov('<h1>Verbinde …</h1>');
  ws = new WebSocket("ws://" + location.hostname + ":" + WSP); ws.binaryType = "blob";
  ws.onopen = () => ws.send(JSON.stringify({t: "join", name, token, look: outfit}));
  ws.onmessage = (e) => {
    if (typeof e.data !== "string") { const u = URL.createObjectURL(e.data); $("#v").onload = () => { if (oldUrl) URL.revokeObjectURL(oldUrl); oldUrl = u; askFrame(); }; $("#v").src = u; lastFrame = Date.now(); return; }
    const m = JSON.parse(e.data);
    if (m.t === "hello") { me = m; role = m.role; $("#nm").textContent = m.name; $("#me .dot").style.background = m.color; setRole(); ov(""); askFrame(); }
    else if (m.t === "full") { ov('<h1>Schon 4 Spieler</h1><p>Das Spiel ist voll. Warte, bis jemand aufhört.</p>'); }
    else if (m.t === "st") paint(m);
    else if (m.t === "sig") { const t = $("#sigt"); t.innerHTML = '<span style="color:' + m.c + '">●</span> ' + esc(m.n) + ': ' + esc(m.txt) + ' <span class="ar" style="transform:rotate(' + (-m.ga) + 'deg)">⬆</span> ' + m.d + ' m';
      t.style.opacity = 1; clearTimeout(window.__sigT); window.__sigT = setTimeout(() => t.style.opacity = 0, 3000); tone(880, 0.08, "triangle", 0.12); tone(1175, 0.1, "triangle", 0.12, 0.09); if (navigator.vibrate) navigator.vibrate(60); }
    else if (m.t === "ev") { if (m.k === "caught") { if (navigator.vibrate) navigator.vibrate([300, 100, 300]); document.body.classList.remove("redfl"); void document.body.offsetWidth; document.body.classList.add("redfl"); }
      if (sfx[m.k]) sfx[m.k](); }
  };
  ws.onclose = () => { me = null; ov('<h1>Verbindung weg</h1><p>Neuer Versuch …</p>'); setTimeout(connect, 1500); };
}
function setRole() { const g = role === "guard"; document.body.classList.toggle("guard", g); $("#rb").style.display = g ? "none" : "flex"; $("#gb").style.display = g ? "flex" : "none";
  $("#meter").style.visibility = g ? "hidden" : "visible"; $("#goal").style.visibility = g ? "hidden" : "visible"; $("#hint").textContent = g ? "links: Kopf drehen · rechts wischen: fein drehen" : "links: gehen · rechts wischen: umschauen"; }
function askFrame() { if (ws && ws.readyState === 1) ws.send('{"t":"frame"}'); }
setInterval(() => { if (me && Date.now() - lastFrame > 1500) { lastFrame = Date.now(); askFrame(); } }, 500);
function fmtT(s) { return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); }
function cool(el, s) { el.classList.toggle("wait", s > 0); let c = el.querySelector(".cnt"); if (s > 0) { if (!c) { c = document.createElement("span"); c.className = "cnt"; el.appendChild(c); } c.textContent = s; } else if (c) c.remove(); }
function paint(m) {
  st = m; if (m.role !== role) { role = m.role; setRole(); }
  const s = Math.max(0, Math.min(100, m.susp)); $("#bar").style.width = s + "%";
  $("#bar").style.background = s > 70 ? "var(--red)" : s > 35 ? "var(--org)" : "var(--grn)"; $("#eye").style.opacity = m.seen ? 1 : 0.35; $("#eye").textContent = m.seen ? "👁 gesehen" : "👁";
  $("#ear").style.opacity = m.heard > 0.05 && role === "runner" ? 1 : 0;
  $("#arrow").style.transform = "rotate(" + (-m.ga) + "deg)"; $("#gd").textContent = Math.round(m.gd) + " m";
  $("#tm").textContent = m.rs === "play" ? "⏱ " + fmtT(m.left) : m.rs === "countdown" ? "gleich" : "–";
  $("#lv").textContent = role === "guard" ? "· Wächter · " + (m.catches || 0) + "× erwischt" : (m.lives ? "· " + "❤️".repeat(Math.max(0, m.lives - m.caught)) + "🤍".repeat(Math.min(m.lives, m.caught)) : "· " + m.caught + "× erwischt");
  $("#list").innerHTML = (m.list || []).map(p => '<span style="color:' + p.c + '">●</span> ' + esc(p.n) + (p.r === "guard" ? " 👁" : "") + (p.s === "goal" ? " 🏁" : p.s === "out" ? " ✖" : "") + (p.r !== "guard" && p.k ? " · " + p.k + "×" : "") + (p.on ? "" : " (weg)")).join("<br>");
  $("#extra").textContent = (m.carry ? "💰 Beute dabei – zurück zum Start! " : (m.goal_mode === "return" && role === "runner" ? "Ziel: Beute holen und zurückbringen · " : "")) + (m.items_all && role === "runner" ? "💎 " + m.items + " · noch " + m.items_left + " zu finden" : "");
  $("#msg").textContent = m.msg || "";
  $("#sig").hidden = !(m.rs === "play" && role === "runner" && m.ps === "play");
  if (m.stone < 0) $("#b-stone").style.display = "none"; else { $("#b-stone").style.display = "flex"; cool($("#b-stone"), m.stone); }
  if (role === "guard") { cool($("#b-light"), m.light); cool($("#b-catch"), m.catch); $("#gd").textContent = (m.pan > 0 ? "◀ " : "▶ ") + Math.abs(m.pan) + "°"; }
  if (m.rs === "countdown") ov('<div id="big">' + Math.max(1, m.cd) + '</div>');
  else if ((m.rs === "lobby" || m.rs === "end") && editing) { /* the player changes the look */ }
  else if (m.rs === "lobby" || m.rs === "end") {
    let h = m.rs === "end" ? (m.tres && m.tres.length ? '<h1>' + esc(m.tres[0].n) + ' gewinnt!</h1><p>' + m.tres.map(t => '<span style="color:' + t.c + '">●</span> ' + esc(t.n) + ' <b>' + t.score + '</b>').join(" · ") + '</p>' : '') + '<h1>Rangliste</h1><table>' + (m.res || []).map((r, i) => '<tr><td>' + (i + 1) + '.</td><td><span style="color:' + r.c + '">●</span> ' + esc(r.n) + '</td><td>' + esc(r.info) + '</td><td><b>' + r.score + '</b></td></tr>').join("") + '</table>'
      : '<h1>Bereit?</h1><p>Ziel: <b>' + esc(m.goal) + '</b> – folge dem Pfeil oben rechts zum grünen Licht.</p><p>Links ziehen = gehen · rechts wischen = umschauen</p>';
    if (m.mode === "mw") h += '<p>' + (m.mwd ? '🛡 Diesmal entscheidet die <b>echte Erkennung von Motion Watch</b>: meldet sie eine Person, ist der erwischt, den die Kamera am besten sieht.' : '⚠ Motion Watch ist nicht verbunden – der Simulator entscheidet.') + '</p>';
    if (m.mode === "guard") h += '<p>Ein Spieler kann Wächter sein: er sieht durch die Kamera, dreht den Kopf und ruft «Erwischt!».</p><button class="sec' + (role === "runner" ? " on" : "") + '" id="r-run">🕵️ Schleicher</button><button class="sec' + (role === "guard" ? " on" : "") + '" id="r-guard">👁 Wächter</button><br>';
    if (m.teams) { const tm = [0, 1].map(k => '<div class="tm' + (m.team === k ? " me" : "") + '"><b style="color:' + ["#eb2e1f", "#1f6bfa"][k] + '">' + ["Team Rot", "Team Blau"][k] + '</b>' +
        (m.list || []).filter(p => p.tm === k).map(p => '<span style="color:' + p.c + '">●</span> ' + esc(p.n)).join("<br>") + '<br><button class="sec' + (m.team === k ? " on" : "") + '" data-team="' + k + '">' + (m.team === k ? "✓ dabei" : "wechseln") + '</button></div>').join("");
      h += '<div class="teams">' + tm + '</div>'; }
    h += '<button class="sec" id="lk">👕 Aussehen ändern</button><br><button class="pr" id="st">' + (m.rs === "end" ? "Nochmal" : "Runde starten") + '</button>';
    ov(h);
    document.querySelectorAll("[data-team]").forEach(b => b.onclick = () => ws.send(JSON.stringify({t: "team", k: +b.dataset.team})));
    const lkb = $("#lk"); if (lkb) lkb.onclick = () => { editing = true; ov('<h1>Aussehen</h1>' + lookHtml() + '<button class="pr" id="lkok">Fertig</button>'); bindLook();
      $("#lkok").onclick = () => { ws.send(JSON.stringify(Object.assign({t: "look"}, outfit))); editing = false; lastOv = null; paint(st); }; };
    const rr = $("#r-run"), rg = $("#r-guard"); if (rr) rr.onclick = () => ws.send('{"t":"role","r":"runner"}'); if (rg) rg.onclick = () => ws.send('{"t":"role","r":"guard"}');
  }
  else if (m.ps === "goal") ov('<h1>🏁 Im Ziel!</h1><p>Warte auf die anderen.</p>');
  else if (m.ps === "out") ov('');
  else ov("");
  const b = $("#st"); if (b) b.onclick = () => ws.send('{"t":"start"}');
}
function esc(s) { return String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c])); }
// joystick (left), looking round (right)
let sid = null, sx = 0, sy = 0, lid = null, lx = 0, ly = 0;
$("#stick").addEventListener("pointerdown", e => { sid = e.pointerId; sx = e.clientX; sy = e.clientY; const b = $("#base"); b.style.left = sx + "px"; b.style.top = sy + "px"; b.style.display = "block"; $("#hint").style.display = "none"; e.target.setPointerCapture(sid); });
$("#stick").addEventListener("pointermove", e => { if (e.pointerId !== sid) return; let dx = e.clientX - sx, dy = e.clientY - sy; const l = Math.hypot(dx, dy), R = 55; if (l > R) { dx *= R / l; dy *= R / l; } mx = dx / R; my = dy / R; $("#knob").style.transform = "translate(" + dx + "px," + dy + "px)"; });
const stickEnd = e => { if (e.pointerId !== sid) return; sid = null; mx = my = 0; $("#base").style.display = "none"; $("#knob").style.transform = ""; };
$("#stick").addEventListener("pointerup", stickEnd); $("#stick").addEventListener("pointercancel", stickEnd);
$("#look").addEventListener("pointerdown", e => { lid = e.pointerId; lx = e.clientX; ly = e.clientY; e.target.setPointerCapture(lid); });
$("#look").addEventListener("pointermove", e => { if (e.pointerId !== lid) return; look += (e.clientX - lx) * 0.3; pitch += (e.clientY - ly) * 0.2; lx = e.clientX; ly = e.clientY; });
const lookEnd = e => { if (e.pointerId === lid) lid = null; };
$("#look").addEventListener("pointerup", lookEnd); $("#look").addEventListener("pointercancel", lookEnd);
const hold = (el, on, off) => { el.addEventListener("pointerdown", e => { e.preventDefault(); on(); }); el.addEventListener("pointerup", off); el.addEventListener("pointercancel", off); el.addEventListener("pointerleave", off); };
const send = (o) => { if (ws && ws.readyState === 1) ws.send(JSON.stringify(o)); };
hold($("#b-run"), () => { run = true; posture = 0; btns(); }, () => { run = false; btns(); });
$("#b-crouch").addEventListener("pointerdown", e => { e.preventDefault(); posture = posture === 1 ? 0 : 1; btns(); });
$("#b-crawl").addEventListener("pointerdown", e => { e.preventDefault(); posture = posture === 2 ? 0 : 2; btns(); });
$("#b-stone").addEventListener("pointerdown", e => { e.preventDefault(); send({t: "stone"}); });
$("#b-light").addEventListener("pointerdown", e => { e.preventDefault(); send({t: "light"}); });
$("#b-catch").addEventListener("pointerdown", e => { e.preventDefault(); send({t: "catch"}); });
document.querySelectorAll("#sig button").forEach(b => b.addEventListener("pointerdown", e => { e.preventDefault(); e.stopPropagation(); send({t: "sig", k: b.dataset.k}); b.style.background = "var(--acc)"; setTimeout(() => b.style.background = "", 300); }));
function btns() { $("#b-run").classList.toggle("on", run); $("#b-crouch").classList.toggle("on", posture === 1); $("#b-crawl").classList.toggle("on", posture === 2); }
// keyboard (for a computer): W A S D / arrows, Shift = run, C = crouch, X = crawl, Q / E = look round, F = throw / light, Space = «Erwischt!»
const keys = {};
addEventListener("keydown", e => { if (e.target.tagName === "INPUT") return; keys[e.code] = true; if (e.code === "KeyC") { posture = posture === 1 ? 0 : 1; btns(); } if (e.code === "KeyX") { posture = posture === 2 ? 0 : 2; btns(); }
  if (e.code === "KeyF") send({t: role === "guard" ? "light" : "stone"}); if (e.code === "Space") send({t: "catch"}); });
addEventListener("keyup", e => { keys[e.code] = false; });
setInterval(() => {
  if (!me || !ws || ws.readyState !== 1) return;
  let kx = (keys.KeyD || keys.ArrowRight ? 1 : 0) - (keys.KeyA || keys.ArrowLeft ? 1 : 0), ky = (keys.KeyS || keys.ArrowDown ? 1 : 0) - (keys.KeyW || keys.ArrowUp ? 1 : 0);
  if (keys.KeyQ) look -= 6; if (keys.KeyE) look += 6;
  const r = run || keys.ShiftLeft || keys.ShiftRight;
  const d = {t: "in", mx: sid !== null ? mx : kx, my: sid !== null ? my : ky, look: Math.round(look * 10) / 10, pitch: Math.round(pitch * 10) / 10, run: !!r, pos: posture};
  look = 0; pitch = 0;
  const j = JSON.stringify(d), now = Date.now();
  if (j !== lastSent || now - lastT > 250 || d.look || d.pitch) { ws.send(j); lastSent = j; lastT = now; }
}, 50);
function goFull() { const el = document.documentElement; try { (el.requestFullscreen || el.webkitRequestFullscreen).call(el).then(() => screen.orientation && screen.orientation.lock && screen.orientation.lock("landscape").catch(() => {})).catch(() => {}); } catch (e) {} $("#rot").classList.add("ask"); }
$("#full").onclick = goFull;
joinForm();
</script></body></html>"""
