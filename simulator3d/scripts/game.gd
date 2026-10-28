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
# ---- 3D-3.1: team against team (robbers and guards), jail, team goal, distraction bonus ----
var guard_team := 1                    # «Team gegen Team»: this team guards in the current round
var match_round := 0                   # 0 = first round, 1 = second round (roles swapped)
var match_scores := [0, 0]
var jail := Vector3(0, 0, -44)
var jail_node: Node3D
var bases: Array = []                  # «Fahne erobern» (3D-3.2): [base of red, base of blue]
var flags: Array = []                  # per team: {"node", "home", "by": carrier or null}
var captures := [0, 0]
var distract := {}                     # {"by": player, "until": t, "start": {slot: distance to the goal}, "caught": {slot: n}}
var guard_auto := false                 # the game turns the head (automatic guard or a player as guard)
var guard_yaw := 0.0
var guard_tilt := deg_to_rad(-9.0)
var flash_until := 0.0
var light_ready := 0.0
var attention := Vector3.ZERO           # a noise (stone, steps): the automatic guard looks there ...
var attention_until := 0.0              # ... until then
var items: Array = []                   # {"node", "pos", "by": -1}
var powers: Array = []                  # power-ups (3D-3.21): {"node", "pos", "kind": "cloak" | "turbo", "back": time it comes back}
var last_minute := false                # the last minute of a round: the cameras are more watchful
var feed: Array = []                    # what happened (for the spectators, 3D-3.22): [time, text]
# ---- more game (3D-3.25) ----
var gallery: Array = []                 # «caught» photos: {"n", "c", "jpg"} (the last 8)
var hides: Array = []                   # hiding places (bushes): {"node", "pos"}
var checkpoints: Array = []             # checkpoints between start and goal: {"node", "pos"}
var ev_kind := ""                       # random event now: storm | dog | car
var ev_until := 0.0
var ev_next := 0.0
var ev_node = null
var ev_weather := ""
var ev_warned := {}
var night_saved := -1.0                 # night round: the time of day before
var decoy_pos := Vector3.ZERO           # the decoy is seen: the automatic head looks there
var decoy_until := 0.0
# ---- 3D-3.27: a task for every round (bonus) and the ranking of the week ----
const TASKS := [["crawl", "🐍 Nur kriechend ins Ziel", 250], ["nostone", "🤫 Ins Ziel, ohne einen Stein zu werfen", 150],
		["fast", "⚡ In unter 60 Sekunden ins Ziel", 250], ["calm", "🧘 Nie über 50 % Verdacht", 200], ["nocatch", "🛡 Kein einziges Mal erwischt", 150],
		["items", "💎 Mindestens 2 Dinge sammeln", 200], ["hide", "🌳 Mindestens 10 Sekunden in einem Versteck", 150]]
var task := {}                          # the task of this round {"id", "text", "bonus"}
var week := {}                          # the ranking of the week: name -> {"n", "c", "score", "rounds", "wins", "tasks"}
var week_id := ""
var board := {}                         # the ranking of the evening: name -> {"n", "c", "score", "rounds", "wins", "best", "clean"}
var records := {}                       # "fast": [name, seconds], "items": [name, n], "catches": [name, n]
var board_day := ""
const HIDE_MAX := 8.0                   # seconds in a hiding place, then out
const CP_BONUS := 150


func news(txt: String) -> void:
	feed.append([now(), txt])
	if feed.size() > 12:
		feed.pop_front()
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
var learn                                # gamelearn.gd (3D-3.52)
var fx_nodes: Array = []                 # [node, until] of the hit sequence (laser, paint, flash)


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
	learn = preload("res://scripts/gamelearn.gd").new()     # 3D-3.52: the game teaches Motion Watch
	learn.main = main
	learn.game = self
	add_child(learn)


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
	"""the guard who turns the head (the first guard)"""
	for p in players:
		if p != null and p["role"] == "guard":
			return p
	return null


func guard_cam(g: Dictionary) -> int:
	"""which camera a guard looks through: the first one the head camera, a second one the fixed camera"""
	return 0 if guard_player() == g else 1


func guard2_watching() -> bool:
	for p in players:
		if p != null and p["role"] == "guard" and p != guard_player() and p["sock"] != null:
			return true
	return false


func team_mode() -> bool:
	return main.game_mode == "teamguard"


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
	_place_powers(false)


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
	goal = _g(goal)
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
	if flag_mode() and bases.size() == 2 and players[i] != null:   # «Fahne erobern»: start at the own base
		var b: Vector3 = bases[int(players[i]["team"])]
		return _g(main.free_spot(b + Vector3((i - 1.5) * 1.3, 0, -3.0), 0.6, true))
	var p: Vector3
	if i < _starts.size():
		p = _starts[i]
	else:
		p = Vector3(-9.0 + 6.0 * i, 0, -46.0)
	return _g(main.free_spot(p, 0.6, true))


func _g(p: Vector3) -> Vector3:
	"""the point on the ground (a real place has hills, from 3D-3.8)"""
	return Vector3(p.x, main.ground_y(p.x, p.z), p.z)


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


const POWER_KIND := {"cloak": [Color(0.75, 0.45, 1.0), 9.0, "🌫 Tarnkappe! %d s lang sieht dich die Kamera kaum"],
		"turbo": [Color(1.0, 0.85, 0.2), 7.0, "⚡ Turbo! %d s lang schneller – aber lauter"]}


func _spot_far(min_d: float) -> Vector3:
	var p := Vector3.ZERO
	for _t in range(30):
		var c := Vector3(_rng.randf_range(-22.0, 22.0), 0, _rng.randf_range(-36.0, -6.0))
		if c.length() > 7.0 and c.distance_to(goal) > 4.0:
			p = _g(main.free_spot(c, 0.6, true))
			var far := true
			for it in items + powers + hides:
				if p.distance_to(it["pos"]) < min_d:
					far = false
			if far:
				break
	return p


func _place_powers(on: bool) -> void:
	"""two power-ups that float and glow (only the players see them): purple = cloak, yellow = turbo"""
	for w in powers:
		if is_instance_valid(w["node"]):
			w["node"].queue_free()
	powers.clear()
	if not on:
		return
	for k in ["cloak", "turbo"]:
		var nd := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.2
		sm.height = 0.4
		nd.mesh = sm
		nd.material_override = _glow(POWER_KIND[k][0])
		nd.layers = 16
		root.add_child(nd)
		var pos := _spot_far(6.0)
		nd.position = pos + Vector3(0, 0.7, 0)
		powers.append({"node": nd, "pos": pos, "kind": k, "back": 0.0})


func _powers_tick(t: float, dt: float) -> void:
	for w in powers:
		var nd: Node3D = w["node"]
		if not is_instance_valid(nd):
			continue
		if float(w["back"]) > 0.0 and t >= float(w["back"]):        # comes back somewhere else
			w["back"] = 0.0
			w["pos"] = _spot_far(6.0)
			nd.visible = true
		nd.position = w["pos"] + Vector3(0, 0.7 + 0.12 * sin(t * 2.5 + float(w["pos"].x)), 0)
		nd.rotation.y += dt * 1.5


func _place_items(n: int) -> void:
	"""shining crystals between the starts and the goal (only the players see them)"""
	_clear_items()
	_place_powers(false)
	for i in range(n):
		var p := Vector3.ZERO
		for _t in range(30):
			var c := Vector3(_rng.randf_range(-22.0, 22.0), 0, _rng.randf_range(-36.0, -6.0))
			if c.length() > 7.0 and c.distance_to(goal) > 4.0:
				p = _g(main.free_spot(c, 0.6, true))
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
		c.position = Vector3(cam.global_position.x, main.ground_y(cam.global_position.x, cam.global_position.z) + 0.06, cam.global_position.z)
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
	if main.game_mode == "free" and round_state not in ["countdown", "play"] and count() > 0:
		start_round()                                      # 3D-3.60: free moving starts as soon as somebody is there
	for p in players:
		if p != null:
			_steer(p, dt)
	if round_state == "countdown" and t >= t_start:
		round_state = "play"
		for p in players:
			if p != null and p["role"] == "runner":
				p["actor"].frozen = false
	if round_state == "play":
		_powers_tick(t, dt)
		if main.game_mode != "free":
			_events_tick(t)
		if not last_minute and t_end - t <= 60.0 and t_end - t > 5.0 and main.game_minutes > 1:
			last_minute = true                              # the last minute: more tension
			news("⏰ Letzte Minute!")
			for q in players:
				if q != null:
					_say(q, "⏰ Letzte Minute! Die Kamera passt jetzt besser auf." if q["role"] == "runner" else "⏰ Letzte Minute!", 4.0)
					_event(q, "item")
		_ref_t -= dt
		if _ref_t <= 0.0:
			_ref_t = 0.2
			_referee(0.2)
		if t >= t_end or _all_done():
			end_round()
	_guard(dt)
	if not fx_nodes.is_empty():
		_fx_tick()
	_flags_follow()
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
			var ctype := "text/html; charset=utf-8"
			if path == "/manifest.json":                   # «Zum Home-Bildschirm»: then the game runs without the address bar (3D-3.23)
				body = JSON.stringify({"name": "Unentdeckt ans Ziel", "short_name": "Unentdeckt", "start_url": "/", "display": "fullscreen",
						"orientation": "landscape", "background_color": "#0a0e14", "theme_color": "#0a0e14"}).to_utf8_buffer()
				ctype = "application/manifest+json"
			var head := "HTTP/1.1 %s\r\nContent-Type: %s\r\nContent-Length: %d\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n" % [
					"200 OK" if body.size() > 20 else "404 Not Found", ctype, body.size()]
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
			if p2["role"] == "guard" and p2 == guard_player():   # the (first) guard turns the head with the drag too
				guard_yaw = wrapf(guard_yaw - look * 0.6, -PI, PI)
				guard_tilt = clamp(guard_tilt - pit * 0.6, deg_to_rad(-40.0), deg_to_rad(15.0))
			elif p2["role"] != "guard":
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
		"decoy":                                       # the decoy (3D-3.25): attracts the camera, team points
			if round_state not in ["countdown", "play"]:
				p2["decoy"] = bool(m.get("v", false)) and main.game_decoy
				paint()
		"lamp":                                        # night round: the torch
			p2["lamp"] = not bool(p2.get("lamp", false))
			var la = p2["actor"]
			if la.torch == null:
				la.add_torch()
			la.player_lamp = p2["lamp"]
		"light":
			_guard_light(p2)
		"catch":
			_guard_catch(p2)


func _assign(p: Dictionary, r: String) -> void:
	p["role"] = r
	var a = p["actor"]
	a.visible = r == "runner"
	if r == "guard":
		a.position = Vector3(0, 0, 4.0)
	if p["sock"] != null:
		_hello(p)


func _set_role(p: Dictionary, r: String) -> void:
	if round_state in ["countdown", "play"] or team_mode():
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
			"loot": loot, "carry": false, "cone": cone, "look": lk, "team": 0, "sig_t": 0.0,
			"decoy": false, "watched": 0.0, "hc": 0, "lamp": false, "hide_i": -1, "hide_t0": 0.0, "hide_cd": {}, "cps": []}
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
	for g in players:                                      # first guard: head camera, others: fixed camera
		if g == null or g["role"] != "guard" or g["sock"] == null or not g["want"]:
			continue
		var ci := guard_cam(g)
		if int(main.frame_no[ci]) == int(g["sent_no"]):
			continue
		var w: WebSocketPeer = g["sock"]["ws"]
		if w.get_ready_state() == WebSocketPeer.STATE_OPEN and w.get_current_outbound_buffered_amount() < 600000:
			g["sent_no"] = int(main.frame_no[ci])
			w.send(main.latest_jpg(ci))
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
	if runners == 0 and not team_mode():
		return
	if flag_mode() and not main.game_teams:                # «Fahne erobern» needs teams
		main.game_teams = true
		on_teams()
	if team_mode():                                        # team against team: one team guards, the other sneaks
		if not main.game_teams:
			main.game_teams = true
			on_teams()
		var n := [0, 0]
		for p in players:
			if p != null:
				n[int(p["team"])] += 1
		if n[0] == 0 or n[1] == 0:
			for p in players:
				if p != null:
					_say(p, "Für «Team gegen Team» braucht jedes Team mindestens einen Spieler", 4.0)
			return
		for p in players:
			if p != null:
				_assign(p, "guard" if int(p["team"]) == guard_team else "runner")
	elif main.game_mode != "guard":                        # no player as guard in this mode
		for p in players:
			if p != null and p["role"] == "guard":
				_assign(p, "runner")
	_new_starts(main.game_random)
	_pick_goal(main.game_random)
	_place_items(int(main.game_items))
	_place_powers(main.game_powers)
	_place_hides(int(main.game_hides))
	_place_checkpoints(int(main.game_checkpoints))
	gallery.clear()
	ev_kind = ""
	ev_next = now() + 4.0 + randf_range(35.0, 55.0)
	ev_warned.clear()
	if main.game_night and night_saved < 0.0:          # night round: 23 o'clock, back afterwards
		night_saved = main.hour()
		main.set_hour(23.0)
	_auto_handicap()
	_pick_task()
	mwg = {"catches": 0, "false": 0, "t": 0.0, "names": []}
	last_minute = false
	feed.clear()
	news("▶ Die Runde beginnt")
	if main.game_spectate:
		main.spectate_start()
	round_state = "countdown"
	t_start = now() + 4.0
	t_end = t_start + float(main.game_minutes) * 60.0
	if main.game_mode == "free":                           # 3D-3.60: free moving - until it is stopped (6 h at most)
		t_end = t_start + 6.0 * 3600.0
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
		p["bonus"] = 0
		p["rescues"] = 0
		p["watched"] = 0.0
		p["hide_i"] = -1
		p["hide_cd"] = {}
		p["cps"] = []
		p["up_m"] = 0.0
		p["stones"] = 0
		p["max_susp"] = 0.0
		p["hide_s"] = 0.0
		p["task_ok"] = false
		p["actor"].handicap = int(p.get("hc", 0))
		if p["role"] == "guard":
			p["state"] = "play"
			continue
		_to_start(p)
		p["state"] = "play"
		p["actor"].visible = true
		p["actor"].frozen = true
		if not task.is_empty():
			_say(p, "Aufgabe: %s (+%d)" % [task["text"], task["bonus"]], 6.0)
	if guard_player() != null:
		guard_yaw = 0.0
		guard_tilt = deg_to_rad(-9.0)
	distract = {}
	_build_flags()
	for p in players:
		if p != null and p["role"] == "runner":
			p["flag"] = -1
			if flag_mode():
				_to_start(p)
	_build_jail()
	_paint_goal()
	learn.round_start()
	if main.game_mode == "patrol" and main.patrol != null:  # 3D-3.61: the patrol drives during the round
		main.patrol.set_active(true)
	paint()


func _build_jail() -> void:
	"""the jail (with «Befreien»): a red ring near the starts, only the players see it"""
	if jail_node != null:
		jail_node.queue_free()
		jail_node = null
	if not main.game_rescue:
		return
	jail = _g(main.free_spot(Vector3(0, 0, -44), 2.0, true))
	jail_node = Node3D.new()
	root.add_child(jail_node)
	jail_node.position = jail
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 1.8
	tm.outer_radius = 2.0
	ring.mesh = tm
	ring.position.y = 0.05
	ring.material_override = _glow(Color(1.0, 0.2, 0.15, 0.7))
	ring.layers = 16
	jail_node.add_child(ring)
	var lb := Label3D.new()
	lb.text = "🔒 Zelle"
	lb.font_size = 64
	lb.pixel_size = 0.006
	lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lb.position.y = 2.6
	lb.layers = 16
	lb.outline_size = 12
	jail_node.add_child(lb)


func flag_mode() -> bool:
	return main.game_goal == "flag" and not team_mode()


func _build_flags() -> void:
	"""two bases at the sides, each with the flag of its team; the way between them crosses the picture of the cameras"""
	_clear_flags()
	if not flag_mode():
		return
	captures = [0, 0]
	bases = [_g(main.free_spot(Vector3(-24, 0, -22), 1.5, true)), _g(main.free_spot(Vector3(24, 0, -22), 1.5, true))]
	for t in range(2):
		var n := Node3D.new()
		root.add_child(n)
		n.position = bases[t]
		var pole := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.03
		cm.bottom_radius = 0.04
		cm.height = 2.2
		pole.mesh = cm
		pole.position.y = 1.1
		var pm := StandardMaterial3D.new()
		pm.albedo_color = Color(0.8, 0.8, 0.82)
		pole.material_override = pm
		n.add_child(pole)
		var cl = main.scenes.cloth(n, Vector2(0.8, 0.5), Vector3(0.42, 1.95, 0), Vector3.ZERO, TEAM_COLORS[t])
		cl.visible = true
		cl.remove_from_group("cloth")                      # the flag of the game is always there
		var ring := MeshInstance3D.new()                   # the base: a ring in the team colour (only the players see it)
		var tm := TorusMesh.new()
		tm.inner_radius = 2.0
		tm.outer_radius = 2.2
		ring.mesh = tm
		ring.material_override = _glow(Color(TEAM_COLORS[t], 0.6))
		ring.layers = 16
		ring.position = bases[t] + Vector3(0, 0.05, 0)
		root.add_child(ring)
		flags.append({"node": n, "home": bases[t], "by": null, "ring": ring})
	if goal_node != null:
		goal_node.visible = false


func _clear_flags() -> void:
	for f in flags:
		if is_instance_valid(f["node"]):
			f["node"].queue_free()
		if is_instance_valid(f["ring"]):
			f["ring"].queue_free()
	flags.clear()
	if goal_node != null:
		goal_node.visible = true


func _flag_home(t: int) -> void:
	var f: Dictionary = flags[t]
	if f["by"] != null:
		f["by"]["flag"] = -1
	f["by"] = null
	f["node"].position = f["home"]


func _flags_follow() -> void:
	"""a carried flag sits on the back of its carrier"""
	for f in flags:
		if f["by"] != null:
			var a = f["by"]["actor"]
			f["node"].position = a.position + a.global_transform.basis * Vector3(0, 0.2, 0.35)


func _flag_rules(p: Dictionary) -> void:
	var a = p["actor"]
	var my := int(p["team"])
	var other := 1 - my
	var f: Dictionary = flags[other]
	if f["by"] == null and int(p.get("flag", -1)) < 0 and a.position.distance_to(f["home"]) < 1.8:
		f["by"] = p                                        # take the flag of the other team
		p["flag"] = other
		_say(p, "🚩 Fahne geholt – zurück zur eigenen Basis!", 3.0)
		_event(p, "item")
		for q in players:
			if q != null and q != p and q["sock"] != null and int(q["team"]) == other:
				_say(q, "⚠ %s hat eure Fahne!" % p["name"], 3.0)
	if int(p.get("flag", -1)) == other and a.position.distance_to(bases[my]) < 2.2:
		captures[my] += 1                                  # brought home
		p["bonus"] = int(p.get("bonus", 0)) + 500
		_flag_home(other)
		_say(p, "🏆 Fahne erobert! (+500)", 3.5)
		a.play_emote("goal", 3.0)
		_event(p, "goal")
		for q in players:
			if q != null and q != p:
				_say(q, "🏆 %s erobert die Fahne für %s" % [p["name"], TEAM_NAMES[my]], 3.0)
		paint()
	# tag: touch somebody of the other team who carries your flag -> the flag goes home
	var mine: Dictionary = flags[my]
	if mine["by"] != null and mine["by"] != p and a.position.distance_to(mine["by"]["actor"].position) < 1.3:
		var thief: Dictionary = mine["by"]
		_flag_home(my)
		_to_start(thief)
		thief["safe_until"] = now() + 3.0
		p["bonus"] = int(p.get("bonus", 0)) + 100
		_say(thief, "✋ %s hat dich erwischt – die Fahne ist zurück" % p["name"], 3.0)
		_say(p, "✋ Fahne zurückgeholt (+100)", 3.0)
		_event(thief, "caught")


func goal_open() -> bool:
	"""with «Team-Ziel» the goal opens only when all crystals are found"""
	if not main.game_teamgoal or items.is_empty():
		return true
	for it in items:
		if int(it["by"]) < 0:
			return false
	return true


func _paint_goal() -> void:
	if goal_node == null or goal_node.get_child_count() == 0:
		return
	var beam: MeshInstance3D = goal_node.get_child(0)
	beam.material_override = _glow(Color(0.2, 1.0, 0.4, 0.28) if goal_open() else Color(1.0, 0.25, 0.2, 0.25))


func end_round() -> void:
	if round_state not in ["countdown", "play"]:
		return
	round_state = "end"
	learn.round_end()                                      # 3D-3.52: before the players go back to the lobby
	if main.game_mode == "patrol" and main.patrol != null:
		main.patrol.set_active(false)
	news("🏁 Die Runde ist vorbei")
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
			if flag_mode():
				sc = 0
				info = "🚩 Fahnen-Runde"
			elif p["state"] == "goal":
				sc = 1000 - int((float(p["t_goal"]) - t_start) * 2.0)
				info = "🏁 %d:%02d" % [int(float(p["t_goal"]) - t_start) / 60, int(float(p["t_goal"]) - t_start) % 60]
			elif p["state"] == "out":
				sc = 0
				info = "keine Leben mehr"
			else:
				sc = max(0, 300 - int(d * 6.0))
				info = "noch %d m" % int(d)
			if bool(p.get("decoy", false)):                     # the decoy: points for every second the cameras watched it
				var dp: int = min(400, int(float(p.get("watched", 0.0)) * 12.0))
				p["bonus"] = int(p.get("bonus", 0)) + dp
				info += " · 🦆 %d s beobachtet" % int(float(p.get("watched", 0.0)))
			if p.get("cps", []).size() > 0:
				info += " · 🚩 %d" % p["cps"].size()
			if _task_done(p):
				p["task_ok"] = true
				p["bonus"] = int(p.get("bonus", 0)) + int(task["bonus"])
				info += " · ✅ Aufgabe (+%d)" % int(task["bonus"])
			var bb: int = learn.bonus(p)                    # 3D-3.52: the blind spots of Motion Watch
			if bb > 0:
				info += " · 🙈 %d s unerkannt (+%d)" % [learn.blind_s(p), bb]
			sc = max(0, sc - 150 * int(p["caught"]) + 100 * int(p["items"]) + int(p.get("bonus", 0)) + bb)
			info += " · %d× erwischt" % p["caught"] + (" · 💎 %d" % p["items"] if int(p["items"]) > 0 else "")
			if int(p.get("rescues", 0)) > 0:
				info += " · %d× befreit" % p["rescues"]
		results.append({"n": p["name"], "c": "#" + COLORS[p["slot"]].to_html(false), "info": info, "score": sc})
		if p["role"] == "runner":
			p["state"] = "lobby"
			p["actor"].frozen = false
			p["actor"].visible = true
		else:
			p["state"] = "lobby"
		p["susp"] = 0.0
	if main.game_mode == "mwhand":                         # the guards at Motion Watch
		var mn: String = ", ".join(PackedStringArray(mwg["names"])) if not mwg["names"].is_empty() else "Motion Watch"
		results.append({"n": "🛡 " + mn, "c": "#3b8cff", "info": "Wächter an Motion Watch · %d× erwischt, %d× Fehlalarm" % [mwg["catches"], mwg["false"]],
				"score": max(0, 150 * int(mwg["catches"]) - 50 * int(mwg["false"]) + 100 * missed)})
	results.sort_custom(func(x, y): return x["score"] > y["score"])
	_board_add()
	_event_end()
	_place_hides(0)
	_place_checkpoints(0)
	if night_saved >= 0.0:
		main.set_hour(night_saved)
		night_saved = -1.0
	_send_gallery()
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
		if team_mode():                                    # two rounds with swapped roles, then the winner of the match
			match_scores[0] += sums[0]
			match_scores[1] += sums[1]
			var first := match_round == 0
			team_results = [{"n": TEAM_NAMES[0], "c": "#" + TEAM_COLORS[0].to_html(false), "score": match_scores[0], "round": sums[0], "lead": first},
					{"n": TEAM_NAMES[1], "c": "#" + TEAM_COLORS[1].to_html(false), "score": match_scores[1], "round": sums[1], "lead": first}]
			match_round += 1
			guard_team = 1 - guard_team                    # swap the roles for the next round
			if match_round >= 2:
				match_round = 0
				match_scores = [0, 0]
		team_results.sort_custom(func(x, y): return x["score"] > y["score"])
	_clear_items()
	_place_powers(false)
	_clear_flags()
	if jail_node != null:
		jail_node.queue_free()
		jail_node = null
	paint()


func _all_done() -> bool:
	if main.game_mode == "free":
		return false
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
	if a.player_lamp:
		light = max(light, 0.75)                           # the torch: the player sees more, but the cameras see the player
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
	return (main.game_mode == "mw" or (main.game_mode == "patrol" and main.patrol_judge == "mw")) and main.now() - main.mw_det_t < 3.0


# 3D-3.53: the difficulty also for Motion Watch as the hunter (Spiel → Regeln → «Schwierigkeit»):
# how long Motion Watch must report a player before he is caught, the pause after a catch, crawling players safe in easy
const MW_HOLD := {"easy": 2.5, "normal": 1.0, "hard": 0.2}
const MW_PAUSE := {"easy": 6.0, "normal": 3.0, "hard": 2.0}
var _mw_hold := {}                       # slot (or -1 = any person) -> seconds reported without a break
var _mw_ref_t := 0.0


func _mw_referee() -> void:
	"""the real detection of Motion Watch decides: it reports a person -> the player it means (its boxes, from Motion Watch
	2.95.75) or else the player the cameras see best is caught - after it was reported long enough (difficulty)"""
	var t := now()
	var dt: float = clampf(t - _mw_ref_t, 0.0, 0.5)
	_mw_ref_t = t
	var lvl: String = main.game_level
	var need: float = MW_HOLD.get(lvl, 1.0)
	if t < _mw_catch_t:
		return
	var boxes: bool = learn.has_boxes()
	var any: bool = int(main.mw_det.get("persons", 0)) > 0
	if not boxes:
		_mw_hold[-1] = (float(_mw_hold.get(-1, 0.0)) + dt) if any else 0.0
	var best = null
	var top := 0.02
	for p in players:
		if p == null or p["role"] != "runner" or p["state"] != "play" or t < float(p["safe_until"]):
			continue
		var s_ := int(p["slot"])
		if boxes:
			_mw_hold[s_] = (float(_mw_hold.get(s_, 0.0)) + dt) if learn.reported_for(p) else 0.0
			if float(_mw_hold[s_]) < need:
				continue
		elif float(_mw_hold.get(-1, 0.0)) < need:
			continue
		if lvl == "easy" and int(p["actor"].ctl_posture) == 2:
			continue                                       # easy: crawling players are safe from Motion Watch
		var f: float = max(cam_sees(p, 0), cam_sees(p, 1))
		if f > top:
			top = f
			best = p
	if best != null:
		_mw_catch_t = t + float(MW_PAUSE.get(lvl, 3.0))
		_mw_hold.clear()
		_caught(best, null)
		_say(best, "Motion Watch hat dich erkannt!", 3.0)


func _check_distract() -> void:
	"""a stone distracted the guard: did a team mate get 3 m closer to the goal meanwhile, unseen? -> bonus for the thrower"""
	if distract.is_empty() or now() < float(distract["until"]):
		return
	var by: Dictionary = distract["by"]
	for q in players:
		if q == null or q == by or q["role"] != "runner" or not distract["start"].has(q["slot"]):
			continue
		if main.game_teams and int(q["team"]) != int(by["team"]):
			continue
		var gained: float = float(distract["start"][q["slot"]]) - q["actor"].position.distance_to(goal)
		if gained >= 3.0 and int(q["caught"]) == int(distract["caught"][q["slot"]]):
			by["bonus"] = int(by.get("bonus", 0)) + 50
			_say(by, "🪨 Ablenkung geklappt – %s kam näher (+50)" % q["name"], 3.0)
			break
	distract = {}


func _referee(dt: float) -> void:
	var lv: float = LEVEL.get(main.game_level, 1.0)
	_check_distract()
	_paint_goal()
	var mw: bool = mw_decides() or main.game_mode == "mwhand"     # 3D-3.27: a person at Motion Watch decides «Erwischt!»
	if mw:
		_mw_referee()
	learn.tick(dt)
	if main.game_mode == "free":                           # 3D-3.60: free moving: nobody is caught, no goal - Motion Watch is only watched
		return
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
				news("💎 %s findet einen Kristall" % p["name"])
				_event(p, "item")
		for w in powers:                                   # power-ups
			if float(w["back"]) == 0.0 and a.position.distance_to(w["pos"]) < 1.3:
				var pk: Array = POWER_KIND[w["kind"]]
				a.power = w["kind"]
				a.power_until = now() + float(pk[1]) * (1.0 - 0.35 * int(p.get("hc", 0)))
				w["back"] = now() + 35.0
				w["node"].visible = false
				_say(p, pk[2] % int(pk[1]), 3.0)
				news(("🌫 %s hat die Tarnkappe" if w["kind"] == "cloak" else "⚡ %s hat den Turbo") % p["name"])
				_event(p, "item")
		for q in players:                                  # rescue somebody from the jail
			if q != null and q["state"] == "jail" and (not main.game_teams or int(q["team"]) == int(p["team"])) and a.position.distance_to(q["actor"].position) < 1.6:
				q["state"] = "play"
				q["actor"].frozen = false
				q["safe_until"] = now() + 3.0
				p["rescues"] = int(p.get("rescues", 0)) + 1
				p["bonus"] = int(p.get("bonus", 0)) + 100
				_say(q, "🔓 %s hat dich befreit!" % p["name"], 3.0)
				news("🔓 %s befreit %s" % [p["name"], q["name"]])
				_say(p, "🔓 %s befreit (+100)" % q["name"], 3.0)
				_event(q, "item")
				_event(p, "item")
				paint()
		if flag_mode() and flags.size() == 2:
			_flag_rules(p)
		var near_goal: bool = a.position.distance_to(goal) < 1.7 and not flag_mode()
		if near_goal and not goal_open():
			_say(p, "🔒 Ziel noch zu – zuerst alle Kristalle finden", 1.0)
			near_goal = false
		if main.game_goal == "return" and not p["carry"] and near_goal:
			p["carry"] = true                              # the loot: now back to the start
			p["loot"].visible = true
			_say(p, "💰 Beute geholt – zurück zum Start!", 3.0)
			_event(p, "item")
			continue
		var home := start_point(p["slot"])
		if (main.game_goal != "return" and near_goal) or (p["carry"] and a.position.distance_to(home) < 3.0):
			p["state"] = "goal"
			p["t_goal"] = now()
			a.frozen = true
			_say(p, "Im Ziel! 🎉", 4.0)
			news("🎉 %s ist im Ziel" % p["name"])
			main.spectate_cut("cheer", int(p["slot"]), "🎉 %s ist im Ziel!" % p["name"])
			a.play_emote("goal", 5.0)
			_event(p, "goal")
			paint()
			continue
		for ci in range(checkpoints.size()):               # checkpoints: bonus on the first visit
			if not (ci in p["cps"]) and a.position.distance_to(checkpoints[ci]["pos"]) < 1.6:
				p["cps"].append(ci)
				p["bonus"] = int(p.get("bonus", 0)) + CP_BONUS
				_say(p, "🚩 Checkpoint %d/%d (+%d)" % [p["cps"].size(), checkpoints.size(), CP_BONUS], 2.5)
				_event(p, "item")
				news("🚩 %s erreicht einen Checkpoint" % p["name"])
		if now() < float(p["safe_until"]):
			p["seen"] = false
			p["heard"] = 0.0
			continue
		var v := visibility(p)
		var hr := hearing(p)
		var hid := _hide_check(p)
		if hid:
			v = 0.0
			hr = 0.0
		v *= 1.0 + 0.25 * int(p.get("hc", 0))           # handicap: easier to see
		if ev_kind == "storm":
			hr *= 0.2                                      # thunder and rain: the microphone hears nearly nothing
			v *= 0.85
		elif ev_kind == "car" and ev_node != null and is_instance_valid(ev_node):
			if a.position.distance_to(ev_node.position) < 7.0:
				if main.is_dark():
					v = max(v, 0.5)                        # in the headlights
				hr *= 0.4                                  # the engine covers the steps
		elif ev_kind == "dog" and ev_node != null and is_instance_valid(ev_node):
			if a.position.distance_to(ev_node.position) < 5.0:
				hr = max(hr, 0.7)                          # the dog barks
				attention = a.position
				attention_until = now() + 3.0
				if not ev_warned.has(p["slot"]):
					ev_warned[p["slot"]] = true
					news("🐕 Der Hund bellt bei %s!" % p["name"])
					_say(p, "🐕 Der Hund bellt dich an!", 2.5)
		if a.ctl_posture < 2 and a.cur_speed > 0.25:     # for the tasks: metres not crawled, time in a hiding place
			p["up_m"] = float(p.get("up_m", 0.0)) + a.cur_speed * dt
		if int(p.get("hide_i", -1)) >= 0:
			p["hide_s"] = float(p.get("hide_s", 0.0)) + dt
		if bool(p.get("decoy", false)) and v > 0.1:       # the decoy: the camera follows it, it collects seconds
			p["watched"] = float(p.get("watched", 0.0)) + dt * v
			decoy_pos = a.position
			decoy_until = now() + 1.0
		if v < 0.1:
			v = 0.0                                        # like a real detection: below its threshold nothing counts
		p["seen"] = v > 0.0
		p["heard"] = hr
		if hr > 0.25:
			attention = a.position
			attention_until = now() + 3.0
		if a.power == "cloak" and now() < float(a.power_until):
			v *= 0.25                                      # cloak: hardly seen
		if a.power == "turbo" and now() < float(a.power_until):
			hr = min(1.0, hr * 1.6 + 0.1)                  # turbo: louder
		var rate := (v * 55.0 + hr * 30.0) * (1.3 if last_minute else 1.0) * (0.55 if bool(p.get("decoy", false)) else 1.0)
		if rate > 0.5:
			p["susp"] = min(100.0, float(p["susp"]) + rate * lv * dt)
		else:
			p["susp"] = max(0.0, float(p["susp"]) - 8.0 * dt)
		p["max_susp"] = max(float(p.get("max_susp", 0.0)), float(p["susp"]))
		if float(p["susp"]) >= 100.0:
			if mw:
				p["susp"] = 99.0                           # the meter only hints: Motion Watch itself decides
			else:
				_caught(p, null)


func _caught(p: Dictionary, by) -> void:
	p["caught"] = int(p["caught"]) + 1
	var fx := hit_fx(p)                                   # 3D-3.52: laser / paint / flash (each can be switched)
	if main.game_photos:                               # the «caught» photo: what the camera saw (3D-3.25)
		main.want_snapshot(0)
		get_tree().create_timer(0.35).timeout.connect(func(): _grab_pic(p))
	news("🚨 %s erwischt" % p["name"] + ((" von %s" % by["name"]) if by is Dictionary else ""))
	main.spectate_cut("caught", int(p["slot"]), "🚨 %s erwischt!" % p["name"])
	if int(p.get("flag", -1)) >= 0 and flags.size() == 2:   # the flag goes back to its base
		_flag_home(int(p["flag"]))
	if p["carry"]:                                         # the loot goes back to its place
		p["carry"] = false
		p["loot"].visible = false
	flash_until = now() + 3.0                             # the light goes on, like at a real alarm
	var g = by if by != null else guard_player()
	if g != null:
		g["catches"] = int(g["catches"]) + 1
	_event(p, "caught", {"fx": fx})
	p["actor"].play_emote("caught", 1.5)
	var lives := int(main.game_lives)
	if lives > 0 and int(p["caught"]) >= lives:
		p["state"] = "out"
		p["actor"].visible = false
		p["actor"].position = Vector3(0, 0, 4.0)
		_say(p, "Erwischt – keine Leben mehr. Du schaust zu.", 5.0)
	elif main.game_rescue and _others_can_rescue(p):
		p["state"] = "jail"                                # in the jail until a team mate comes
		var a = p["actor"]
		a.position = jail + Vector3(cos(p["slot"] * 1.6) * 0.9, 0, sin(p["slot"] * 1.6) * 0.9)
		a.frozen = true
		a.ctl_posture = 0
		_say(p, "🔒 In der Zelle – ein Teamkollege muss dich befreien", 4.0)
	else:
		_say(p, "Erwischt! Zurück zum Start", 3.0)
		p["safe_until"] = now() + 3.0
		if fx.is_empty():
			_to_start(p)
		else:                                              # the sequence is seen where it happened, then back to the start
			p["safe_until"] = now() + 3.9
			p["actor"].frozen = true
			get_tree().create_timer(0.9).timeout.connect(func():
				if p["state"] == "play":
					_to_start(p)
					p["actor"].frozen = round_state != "play"
				)
	paint()


func _others_can_rescue(p: Dictionary) -> bool:
	for q in players:
		if q != null and q != p and q["role"] == "runner" and q["state"] == "play" and (not main.game_teams or int(q["team"]) == int(p["team"])):
			return true
	return false


func _event(p: Dictionary, k: String, extra := {}) -> void:
	if p["sock"] != null:
		var m := {"t": "ev", "k": k}
		m.merge(extra)
		p["sock"]["ws"].send_text(JSON.stringify(m))


# ---- 3D-3.52: the hit sequence - not a real shot, but the player feels hit: a red laser from the camera head, a
# paint ball with a splash, a flash like a speed camera. Each can be switched on its own (Spiel → Treffer).
func _mat(c: Color, glow: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.emission_enabled = glow > 0.0
	m.emission = Color(c, 1.0)
	m.emission_energy_multiplier = glow
	if glow > 0.0:
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if c.a < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return m


func _fx_keep(n: Node3D, secs: float) -> void:
	root.add_child(n)
	fx_nodes.append([n, now() + secs])


func hit_fx(p: Dictionary) -> Array:
	var on: Array = []
	if main.game_fx_laser and (not main.kids_on or main.kids_laser):     # 3D-3.69: Kinder-Modus without laser if so set
		on.append("laser")
	if main.game_fx_paint:
		on.append("paint")
	if main.game_fx_flash:
		on.append("flash")
	if on.is_empty():
		return on
	var a = p["actor"]
	var src: Vector3 = main.cams[0].global_position
	var tgt: Vector3 = a.position + Vector3(0, HEIGHT[int(a.ctl_posture)] * 0.62, 0)
	if "laser" in on:                                      # a thin red beam for half a second, a red glow on the player
		var d := src.distance_to(tgt)
		var beam := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.025
		cm.bottom_radius = 0.025
		cm.height = d
		cm.radial_segments = 6
		cm.rings = 1
		beam.mesh = cm
		beam.material_override = _mat(Color(1.0, 0.1, 0.08, 0.85), 6.0)
		beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_fx_keep(beam, 0.8)
		var dirv := (tgt - src).normalized()
		var bx := Basis()
		bx.y = dirv                                       # the cylinder stands along y: turn y onto the beam
		bx.x = dirv.cross(Vector3.FORWARD if abs(dirv.dot(Vector3.FORWARD)) < 0.95 else Vector3.RIGHT).normalized()
		bx.z = bx.x.cross(bx.y).normalized()
		beam.global_transform = Transform3D(bx, (src + tgt) * 0.5)
		var gl := OmniLight3D.new()
		gl.light_color = Color(1.0, 0.15, 0.1)
		gl.light_energy = 3.0
		gl.omni_range = 2.2
		_fx_keep(gl, 0.8)
		gl.global_position = tgt
		var dot := MeshInstance3D.new()                   # the red dot on the jacket
		var sm := SphereMesh.new()
		sm.radius = 0.07
		sm.height = 0.14
		dot.mesh = sm
		dot.material_override = _mat(Color(1.0, 0.1, 0.08), 8.0)
		_fx_keep(dot, 1.0)
		dot.global_position = tgt
	if "paint" in on:                                      # a paint ball flies, a splash stays on the ground
		var pc := Color.from_hsv(_rng.randf(), 0.85, 1.0)
		var ball := MeshInstance3D.new()
		var bm := SphereMesh.new()
		bm.radius = 0.07
		bm.height = 0.14
		ball.mesh = bm
		ball.material_override = _mat(pc, 1.5)
		_fx_keep(ball, 0.4)
		ball.global_position = src
		create_tween().tween_property(ball, "global_position", tgt, 0.32)
		var gp := Vector3(tgt.x, main.ground_y(tgt.x, tgt.z) + 0.02, tgt.z)
		get_tree().create_timer(0.32).timeout.connect(func():
			var splat := MeshInstance3D.new()
			var dm := CylinderMesh.new()
			dm.top_radius = 0.45
			dm.bottom_radius = 0.45
			dm.height = 0.01
			dm.radial_segments = 14
			dm.rings = 1
			splat.mesh = dm
			splat.material_override = _mat(Color(pc, 0.85), 0.0)
			splat.scale = Vector3(0.05, 1, 0.05)
			_fx_keep(splat, 25.0)
			splat.global_position = gp
			splat.rotation.y = _rng.randf() * TAU
			create_tween().tween_property(splat, "scale", Vector3(1.0, 1, 0.75 + _rng.randf() * 0.5), 0.15))
	if "flash" in on:                                      # a bright flash at the camera, like a speed camera
		var fl := OmniLight3D.new()
		fl.light_color = Color(1, 1, 1)
		fl.light_energy = 12.0
		fl.omni_range = 30.0
		_fx_keep(fl, 0.18)
		fl.global_position = src
	return on


func _fx_tick() -> void:
	var t := now()
	for e in fx_nodes.duplicate():
		if t > float(e[1]):
			if is_instance_valid(e[0]):
				e[0].queue_free()
			fx_nodes.erase(e)



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
	p["stones"] = int(p.get("stones", 0)) + 1
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
	s.position = _g(to) + Vector3(0, 0.07, 0)
	root.add_child(s)
	stones.append([s, now() + 8.0])
	main.add_sound(-14.0, to, 0.6)                         # the microphone of Motion Watch hears it too
	attention = to
	attention_until = now() + 4.0
	var st := {}
	var cn := {}
	for q in players:
		if q != null and q["role"] == "runner":
			st[q["slot"]] = q["actor"].position.distance_to(goal)
			cn[q["slot"]] = int(q["caught"])
	distract = {"by": p, "until": now() + 5.0, "start": st, "caught": cn}
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


# ---- 3D-3.27: «Team gegen Motion Watch»: the guards sit at Motion Watch, turn the real camera head with its joystick and
# press «Erwischt!» there. Right if the head camera sees a runner (meter at least 30 %), else a false alarm.
var mwg := {"catches": 0, "false": 0, "t": 0.0, "names": []}


func mw_catch(who: String, x := -1.0, y := -1.0) -> Dictionary:
	"""3D-3.52: x, y (0..1) = the hunter tapped this spot of the live picture (head camera): hit only who is there"""
	if main.game_mode != "mwhand" or round_state != "play":
		return {"ok": false, "error": "Gerade läuft keine Runde «Team gegen Motion Watch»."}
	if now() < float(mwg["t"]):
		return {"ok": false, "error": "Noch %d s warten (Fehlalarm)." % int(ceil(float(mwg["t"]) - now()))}
	if who != "" and not (who in mwg["names"]):
		mwg["names"].append(who)
	var hit = null
	var best := 0.02
	var rep_mw: bool = learn.reported_recently()
	if x >= 0.0 and y >= 0.0 and main.game_tap:
		var near := 9.0
		for p in players:
			if p == null or p["role"] != "runner" or p["state"] != "play" or now() < float(p["safe_until"]) or cam_sees(p, 0) <= 0.0:
				continue
			var b: Array = learn.box(p)
			if b.is_empty():
				continue
			var mx: float = max(0.03, b[2] * 0.35)          # a little room around the figure
			var my: float = max(0.03, b[3] * 0.15)
			if x >= b[0] - mx and x <= b[0] + b[2] + mx and y >= b[1] - my and y <= b[1] + b[3] + my:
				var dd: float = Vector2(x - (b[0] + b[2] / 2.0), y - (b[1] + b[3] / 2.0)).length()
				if dd < near:
					near = dd
					hit = p
	else:
		for p in players:
			if p != null and p["role"] == "runner" and p["state"] == "play" and now() >= float(p["safe_until"]) and float(p["susp"]) >= 30.0:
				var f: float = cam_sees(p, 0)
				if f > best:
					best = f
					hit = p
	learn.on_shot(hit, learn.reported_recently(hit) if hit != null else rep_mw)
	if hit == null:
		mwg["false"] = int(mwg["false"]) + 1
		mwg["t"] = now() + 4.0
		news("❌ Fehlalarm von Motion Watch" + ((" (%s)" % who) if who != "" else ""))
		return {"ok": true, "hit": false, "text": "Fehlalarm! 4 s warten."}
	mwg["catches"] = int(mwg["catches"]) + 1
	_say(hit, "🚨 Motion Watch hat dich erwischt!", 3.0)
	_caught(hit, {"name": who if who != "" else "Motion Watch"})
	return {"ok": true, "hit": true, "text": "✓ %s erwischt!" % hit["name"]}


func _guard_catch(g: Dictionary) -> void:
	"""the guard calls «Erwischt!»: right if the head camera sees somebody (meter at least 30 %)"""
	if g["role"] != "guard" or round_state != "play" or now() < float(g["catch_t"]):
		return
	var hit = null
	for p in players:
		if p != null and p["role"] == "runner" and p["state"] == "play" and float(p["susp"]) >= 30.0 and cam_sees(p, guard_cam(g)) > 0.02:
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
	if g != null and main.game_mode in ["guard", "teamguard"]:
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
	if now() < decoy_until:                            # the decoy is seen: the head stays on it unless somebody is nearly caught
		want = atan2(-decoy_pos.x, -decoy_pos.z)
		top = 70.0
	for p in players:
		if p != null and p["state"] == "play" and p["role"] == "runner" and float(p["susp"]) > top:
			top = float(p["susp"])
			var d: Vector3 = p["actor"].position
			want = atan2(-d.x, -d.z)
	guard_yaw = lerp_angle(guard_yaw, want, clamp(dt * {"easy": 1.6, "normal": 3.0, "hard": 4.5}.get(main.game_level, 3.0), 0.0, 1.0))   # 3D-3.53: easy turns slower


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
	if flag_mode() and flags.size() == 2 and p["role"] == "runner":
		var my := int(p["team"])
		if int(p.get("flag", -1)) >= 0:
			target = bases[my]                                 # bring it home
		elif flags[my]["by"] != null:
			target = flags[my]["by"]["actor"].position         # get your flag back
		else:
			target = bases[1 - my]                             # fetch the flag of the others
	var to: Vector3 = target - a.position
	var ga := rad_to_deg(wrapf(atan2(-to.x, -to.z) - float(p["yaw"]), -PI, PI))
	var lst := []
	for q in players:
		if q != null:
			lst.append({"n": q["name"], "c": "#" + COLORS[q["slot"]].to_html(false), "s": q["state"], "k": q["caught"], "on": q["sock"] != null,
					"r": q["role"], "i": q["items"], "tm": int(q["team"]), "dc": bool(q.get("decoy", false))})
	var left_items := 0
	for it in items:
		if int(it["by"]) < 0:
			left_items += 1
	var d := {"t": "st", "rs": round_state, "susp": int(p["susp"]), "seen": p["seen"], "heard": snappedf(p["heard"], 0.01),
			"caught": p["caught"], "ps": p["state"], "role": p["role"], "mode": main.game_mode, "gd": snappedf(to.length(), 0.1),
			"ga": int(ga), "goal": goal_name, "list": lst, "items": p["items"], "items_left": left_items, "items_all": items.size(),
			"lives": int(main.game_lives), "stone": int(max(0.0, float(p["stone_t"]) - now())) if main.game_stones else -1,
			"msg": p["msg"] if now() < float(p["msg_until"]) else "", "has_guard": guard_player() != null, "mwd": mw_decides(),
			"goal_mode": "flag" if flag_mode() else main.game_goal, "carry": p["carry"], "gopen": goal_open(), "flag": int(p.get("flag", -1)),
			"caps": captures, "gcam": guard_cam(p) if p["role"] == "guard" else -1,
			"tg": guard_team, "mround": match_round, "teams": main.game_teams, "team": int(p["team"]), "look": p["look"],
			"tres": team_results if round_state == "end" else [],
			"decoy": bool(p.get("decoy", false)), "decoy_ok": main.game_decoy and main.game_mode in ["camera", "mw"],
			"lamp": bool(p.get("lamp", false)), "dark": main.is_dark(), "hid": int(p.get("hide_i", -1)) >= 0, "hc": int(p.get("hc", 0)),
			"cps": p.get("cps", []).size(), "cps_all": checkpoints.size(), "ev": ev_kind,
			"board": board_list() if round_state in ["end", "lobby"] else [], "week": week_list() if round_state in ["end", "lobby"] else [],
			"task": task.get("text", ""), "task_bonus": int(task.get("bonus", 0)), "task_ok": bool(p.get("task_ok", false))}
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
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="apple-mobile-web-app-title" content="Unentdeckt"><link rel="manifest" href="/manifest.json">
<title>Unentdeckt ans Ziel</title>
<style>
:root{--bg:#0a0e14;--panel:#111822;--line:#1f2b3a;--txt:#e6edf3;--mut:#8b98a8;--acc:#3b8cff;--grn:#34c759;--org:#ff9f0a;--red:#ff453a}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;height:100%;height:100dvh;background:var(--bg);color:var(--txt);font:15px system-ui,-apple-system,Segoe UI,Roboto,sans-serif;overflow:hidden;touch-action:none;user-select:none;-webkit-user-select:none}
#v{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;background:#000}
body.guard #v{object-fit:contain}
.top{position:fixed;left:0;right:0;top:0;display:flex;gap:8px;align-items:center;padding:8px 10px;padding-top:max(8px,env(safe-area-inset-top));padding-left:max(10px,env(safe-area-inset-left));padding-right:max(10px,env(safe-area-inset-right));background:linear-gradient(#000a,#0000);pointer-events:none}
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
.hint{position:fixed;left:calc(max(10px,env(safe-area-inset-left)) + 58px);bottom:max(16px,env(safe-area-inset-bottom));color:#fff9;font-size:12px;pointer-events:none}
.btns{position:fixed;right:max(12px,env(safe-area-inset-right));bottom:max(12px,env(safe-area-inset-bottom));display:flex;gap:10px;align-items:flex-end}
.b{width:70px;height:70px;border-radius:50%;border:2px solid #ffffff55;background:#0a0e14aa;color:#fff;font-size:11px;font-weight:600;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;position:relative}
.b i{font-style:normal;font-size:21px}
.b.on{background:var(--acc);border-color:var(--acc)}
.b.wait{opacity:.45}
.b.big{width:86px;height:86px;font-size:13px}
.b.red{background:#ff453acc;border-color:var(--red)}
#side{position:fixed;right:max(10px,env(safe-area-inset-right));top:calc(max(8px,env(safe-area-inset-top)) + 40px);display:flex;flex-direction:column;gap:8px}
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
#list{position:fixed;left:max(10px,env(safe-area-inset-left));top:calc(max(8px,env(safe-area-inset-top)) + 38px);font-size:12px;line-height:1.5;pointer-events:none;text-shadow:0 1px 4px #000}
#extra{position:fixed;left:calc(max(10px,env(safe-area-inset-left)) + 58px);bottom:calc(max(16px,env(safe-area-inset-bottom)) + 22px);max-width:42vw;font-size:13px;pointer-events:none;text-shadow:0 1px 4px #000}
#ear{position:fixed;left:50%;top:34px;transform:translateX(-50%);font-size:13px;pointer-events:none;opacity:0;transition:opacity .2s}
#rot{display:none;position:fixed;inset:0;background:#0a0e14f2;align-items:center;justify-content:center;text-align:center;padding:30px;font-size:18px}
@media (orientation:portrait){#rot.ask{display:flex}}
.redfl{animation:fl .4s 3}@keyframes fl{50%{background:#ff453a88}}
#hitfx{position:fixed;inset:0;pointer-events:none;z-index:90;overflow:hidden}
#hitfx .xh{position:absolute;left:50%;top:50%;width:70vmin;height:70vmin;margin:-35vmin 0 0 -35vmin;border:3px solid #ff3b30;border-radius:50%;animation:xh .45s ease-in forwards;box-shadow:0 0 18px #ff3b30}
#hitfx .xh::before,#hitfx .xh::after{content:"";position:absolute;background:#ff3b30;left:50%;top:-12%;width:3px;height:124%;margin-left:-1.5px}#hitfx .xh::after{transform:rotate(90deg)}
@keyframes xh{0%{transform:scale(1.4);opacity:0}60%{opacity:1}100%{transform:scale(.12);opacity:1}}
#hitfx .rd{position:absolute;inset:0;background:radial-gradient(circle,#ff3b30cc 0,#ff3b3000 60%);animation:rd .7s .4s ease-out forwards;opacity:0}
@keyframes rd{0%{opacity:1}100%{opacity:0}}
#hitfx svg.sp{position:absolute;width:62vmin;height:62vmin;animation:sp 2.6s ease-out forwards}
@keyframes sp{0%{transform:scale(.2)}12%{transform:scale(1.05)}20%{transform:scale(1)}75%{opacity:1}100%{opacity:0}}
#hitfx .wf{position:absolute;inset:0;background:#fff;animation:wf .5s ease-out forwards}
@keyframes wf{0%{opacity:1}100%{opacity:0}}
#hitfx .ph{position:absolute;left:8%;right:8%;top:30%;border:4px solid #fff;padding:10px;color:#fff;font:700 22px system-ui;text-align:center;background:#0008;animation:rd 1.8s .5s ease-out forwards;opacity:1}
.cnt{position:absolute;top:-6px;right:-6px;background:#000c;border-radius:999px;font-size:11px;padding:1px 6px}
#sig{position:fixed;left:max(10px,env(safe-area-inset-left));top:50%;transform:translateY(-38%);display:flex;flex-direction:column;gap:6px;z-index:5}
#tip{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);width:min(88vw,460px);background:#111822f2;border:1px solid var(--line);border-radius:14px;padding:14px 16px;font-size:15px;line-height:1.4;text-align:center;z-index:20}
#tip[hidden]{display:none}
#pic{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:15;background:#111822f2;border:2px solid var(--red);border-radius:14px;padding:8px;text-align:center;pointer-events:none}
#pic[hidden]{display:none}#pic img{display:block;width:min(70vw,420px);max-height:60vh;object-fit:contain;border-radius:8px}#pictxt{font-weight:700;margin-top:6px}
.gal{display:flex;gap:6px;overflow-x:auto;margin:8px 0;padding-bottom:4px}.gal figure{margin:0;flex:0 0 auto;text-align:center;font-size:12px}
.gal img{height:90px;border-radius:8px;display:block}
.brd td.n{font-weight:600}.rec{font-size:12px;color:var(--mut)}
@media (max-height:440px){                      /* a phone lying on its side: everything a bit smaller, nothing on top of each other */
  .b{width:58px;height:58px;font-size:10px}.b i{font-size:18px}.b.big{width:70px;height:70px;font-size:11px}.btns{gap:8px}
  #side button{width:34px;height:34px;font-size:15px}#side{gap:6px}
  #sig button{width:42px;height:34px;font-size:16px}#sig{gap:5px}
  .pill{font-size:12px;padding:3px 9px}#meter{height:12px}#list{font-size:11px}
  #msg{font-size:20px}#big{font-size:72px}
}
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
<div class="btns" id="rb"><div class="b" id="b-lamp" style="display:none"><i>🔦</i>Lampe</div><div class="b" id="b-stone"><i>🪨</i>Werfen</div><div class="b" id="b-run"><i>🏃</i>Rennen</div><div class="b" id="b-crouch"><i>🧎</i>Ducken</div><div class="b" id="b-crawl"><i>🐍</i>Kriechen</div></div>
<div class="btns" id="gb" style="display:none"><div class="b" id="b-light"><i>💡</i>Licht</div><div class="b big red" id="b-catch"><i>🚨</i>Erwischt!</div></div>
<div id="tip" hidden></div>
<div id="pic" hidden><img id="picimg" alt=""><div id="pictxt"></div></div>
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
let lastOv = null, editing = false, GAL = [];
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
function hitFx(fx) {                     // 3D-3.52: the player feels hit - crosshair (laser), paint splash, flash
  let o = document.getElementById("hitfx"); if (o) o.remove(); if (!fx.length) return;
  o = document.createElement("div"); o.id = "hitfx"; document.body.appendChild(o);
  if (fx.includes("flash")) { o.insertAdjacentHTML("beforeend", '<div class="wf"></div><div class="ph">📸 GEBLITZT</div>'); }
  if (fx.includes("laser")) { o.insertAdjacentHTML("beforeend", '<div class="xh"></div><div class="rd"></div>'); }
  if (fx.includes("paint")) { const h = Math.floor(Math.random() * 360), x = 10 + Math.random() * 40, y = 15 + Math.random() * 40;
    let d = "M50 18"; for (let k = 1; k <= 14; k++) { const a = k / 14 * 6.283, r = 26 + Math.random() * 12; d += " L" + (50 + Math.cos(a) * r).toFixed(1) + " " + (50 + Math.sin(a) * r).toFixed(1); }
    o.insertAdjacentHTML("beforeend", '<svg class="sp" viewBox="0 0 100 100" style="left:' + x + '%;top:' + y + '%"><path d="' + d + 'Z" fill="hsl(' + h + ',90%,55%)"/><circle cx="20" cy="22" r="5" fill="hsl(' + h + ',90%,55%)"/><circle cx="84" cy="70" r="4" fill="hsl(' + h + ',90%,55%)"/></svg>'); }
  if (navigator.vibrate) navigator.vibrate(fx.includes("laser") ? [80, 40, 80, 40, 260] : [300, 100, 300]);
  setTimeout(() => { if (o.isConnected) o.remove(); }, 3000);
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
    else if (m.t === "pic") { $("#picimg").src = "data:image/jpeg;base64," + m.b64; $("#pictxt").textContent = m.txt || ""; $("#pic").hidden = false;
      clearTimeout(window.__picT); window.__picT = setTimeout(() => $("#pic").hidden = true, 3500); }
    else if (m.t === "gal") { GAL = m.pics || []; lastOv = null; if (st && st.rs) paint(st); }
    else if (m.t === "sig") { const t = $("#sigt"); t.innerHTML = '<span style="color:' + m.c + '">●</span> ' + esc(m.n) + ': ' + esc(m.txt) + ' <span class="ar" style="transform:rotate(' + (-m.ga) + 'deg)">⬆</span> ' + m.d + ' m';
      t.style.opacity = 1; clearTimeout(window.__sigT); window.__sigT = setTimeout(() => t.style.opacity = 0, 3000); tone(880, 0.08, "triangle", 0.12); tone(1175, 0.1, "triangle", 0.12, 0.09); if (navigator.vibrate) navigator.vibrate(60); }
    else if (m.t === "ev") { if (m.k === "caught") { hitFx(m.fx || []); if (navigator.vibrate) navigator.vibrate([300, 100, 300]); document.body.classList.remove("redfl"); void document.body.offsetWidth; document.body.classList.add("redfl"); }
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
  $("#list").hidden = (m.list || []).length < 2;                // alone: the name stands at the top already
  $("#list").innerHTML = (m.list || []).map(p => '<span style="color:' + p.c + '">●</span> ' + esc(p.n) + (p.r === "guard" ? " 👁" : "") + (p.s === "goal" ? " 🏁" : p.s === "out" ? " ✖" : "") + (p.r !== "guard" && p.k ? " · " + p.k + "×" : "") + (p.on ? "" : " (weg)")).join("<br>");
  $("#extra").textContent = (m.goal_mode === "flag" && role === "runner" ? "🚩 Rot " + m.caps[0] + " : " + m.caps[1] + " Blau · " + (m.flag >= 0 ? "Fahne dabei – zur eigenen Basis! · " : "") : "") + (m.gopen === false && role === "runner" ? "🔒 Ziel noch zu – zuerst alle Kristalle finden · " : "") + (m.carry ? "💰 Beute dabei – zurück zum Start! " : (m.goal_mode === "return" && role === "runner" ? "Ziel: Beute holen und zurückbringen · " : "")) + (m.items_all && role === "runner" ? "💎 " + m.items + " · noch " + m.items_left + " zu finden" : "");
  if (m.cps_all && role === "runner") $("#extra").textContent = "🚩 " + m.cps + "/" + m.cps_all + " · " + $("#extra").textContent;
  if (m.decoy && role === "runner") $("#extra").textContent = "🦆 Lockvogel – lass dich sehen! · " + $("#extra").textContent;
  $("#msg").textContent = m.msg || "";
  $("#sig").hidden = !(m.rs === "play" && role === "runner" && m.ps === "play");
  if (m.stone < 0) $("#b-stone").style.display = "none"; else { $("#b-stone").style.display = "flex"; cool($("#b-stone"), m.stone); }
  $("#b-lamp").style.display = m.dark && role === "runner" ? "flex" : "none"; $("#b-lamp").classList.toggle("on", !!m.lamp);
  if (role === "guard") { cool($("#b-light"), m.light); cool($("#b-catch"), m.catch); $("#gd").textContent = m.gcam === 1 ? "feste Kamera" : (m.pan > 0 ? "◀ " : "▶ ") + Math.abs(m.pan) + "°"; }
  if (m.rs === "countdown") { GAL = []; ov('<div id="big">' + Math.max(1, m.cd) + '</div>'); }
  else if ((m.rs === "lobby" || m.rs === "end") && editing) { /* the player changes the look */ }
  else if (m.rs === "lobby" || m.rs === "end") {
    let h = m.rs === "end" ? (m.tres && m.tres.length ? '<h1>' + (m.tres[0].lead ? 'Runde 1 von 2: ' + esc(m.tres[0].n) + ' führt' : esc(m.tres[0].n) + ' gewinnt!') + '</h1><p>' + m.tres.map(t => '<span style="color:' + t.c + '">●</span> ' + esc(t.n) + ' <b>' + t.score + '</b>' + (t.round !== undefined ? ' <small>(diese Runde ' + t.round + ')</small>' : '')).join(" · ") + '</p>' : '') + '<h1>Rangliste</h1><table>' + (m.res || []).map((r, i) => '<tr><td>' + (i + 1) + '.</td><td><span style="color:' + r.c + '">●</span> ' + esc(r.n) + '</td><td>' + esc(r.info) + '</td><td><b>' + r.score + '</b></td></tr>').join("") + '</table>'
      : '<h1>Bereit?</h1><p>Ziel: <b>' + esc(m.goal) + '</b> – folge dem Pfeil oben rechts zum grünen Licht.</p><p>Links ziehen = gehen · rechts wischen = umschauen</p>';
    if (m.goal_mode === "flag") h += '<p>🚩 <b>Fahne erobern</b>: hol die Fahne der anderen bei ihrer Basis und bring sie zu deiner Basis (+500). Berührst du jemanden, der eure Fahne trägt, geht sie zurück (+100). Die Kamera passt auf alle auf.</p>';
    if (m.mode === "teamguard") h += '<p>⚔️ Team gegen Team · Runde ' + (m.mround + 1) + ' von 2: <b style="color:' + ["#eb2e1f", "#1f6bfa"][m.tg] + '">' + ["Team Rot", "Team Blau"][m.tg] + '</b> bewacht (Kopfkamera und feste Kamera), das andere Team schleicht. Danach wird getauscht.</p>';
    if (m.mode === "mwhand") h += '<p>🕹 <b>Team gegen Motion Watch:</b> Die Wächter sitzen an Motion Watch, drehen die echte Kamera mit dem Joystick und drücken dort «Erwischt!». Der Balken zeigt nur, wie gut man dich sieht.</p>';
    if (m.mode === "mw") h += '<p>' + (m.mwd ? '🛡 Diesmal entscheidet die <b>echte Erkennung von Motion Watch</b>: meldet sie eine Person, ist der erwischt, den die Kamera am besten sieht.' : '⚠ Motion Watch ist nicht verbunden – der Simulator entscheidet.') + '</p>';
    if (m.mode === "guard") h += '<p>Ein Spieler kann Wächter sein: er sieht durch die Kamera, dreht den Kopf und ruft «Erwischt!».</p><button class="sec' + (role === "runner" ? " on" : "") + '" id="r-run">🕵️ Schleicher</button><button class="sec' + (role === "guard" ? " on" : "") + '" id="r-guard">👁 Wächter</button><br>';
    if (m.teams) { const tm = [0, 1].map(k => '<div class="tm' + (m.team === k ? " me" : "") + '"><b style="color:' + ["#eb2e1f", "#1f6bfa"][k] + '">' + ["Team Rot", "Team Blau"][k] + '</b>' +
        (m.list || []).filter(p => p.tm === k).map(p => '<span style="color:' + p.c + '">●</span> ' + esc(p.n)).join("<br>") + '<br><button class="sec' + (m.team === k ? " on" : "") + '" data-team="' + k + '">' + (m.team === k ? "✓ dabei" : "wechseln") + '</button></div>').join("");
      h += '<div class="teams">' + tm + '</div>'; }
    if (m.decoy_ok && role === "runner") h += '<p>🦆 Ein <b>Lockvogel</b> lässt sich absichtlich sehen und lockt die Kamera weg. Er wird langsamer entdeckt und bekommt Punkte für jede Sekunde, in der ihn die Kamera beobachtet.</p><button class="sec' + (m.decoy ? " on" : "") + '" id="r-decoy">🦆 ' + (m.decoy ? "Ich bin Lockvogel" : "Lockvogel sein") + '</button><br>';
    if (m.rs === "end" && GAL.length) h += '<h1>📸 Erwischt!</h1><div class="gal">' + GAL.map(g => '<figure><img src="data:image/jpeg;base64,' + g.b64 + '"><figcaption style="color:' + g.c + '">' + esc(g.n) + '</figcaption></figure>').join("") + '</div>';
    if (m.board && m.board.length) h += '<h1>🏆 Rangliste des Abends</h1><table class="brd">' + m.board.map((b, i) => '<tr><td>' + (["🥇", "🥈", "🥉"][i] || (i + 1) + ".") + '</td><td class="n" style="color:' + b.c + '">' + esc(b.n) + '</td><td><b>' + b.score + '</b></td><td class="rec">' + b.rounds + ' Runden' + (b.wins ? ' · ' + b.wins + '× Sieg' : '') + (b.best ? ' · Bestzeit ' + fmtT(b.best) : '') + (b.clean ? ' · ' + b.clean + '× nie erwischt' : '') + '</td></tr>').join("") + '</table>';
    if (m.week && m.week.length) h += '<h1>📅 Rangliste der Woche</h1><table class="brd">' + m.week.map((b, i) => '<tr><td>' + (["🥇", "🥈", "🥉"][i] || (i + 1) + ".") + '</td><td class="n" style="color:' + b.c + '">' + esc(b.n) + '</td><td><b>' + b.score + '</b></td><td class="rec">' + b.rounds + ' Runden' + (b.wins ? ' · ' + b.wins + '× Sieg' : '') + (b.tasks ? ' · ' + b.tasks + '× Aufgabe' : '') + '</td></tr>').join("") + '</table>';
    if (m.task && m.rs !== "end") h += '<p>🎯 <b>Aufgabe:</b> ' + esc(m.task) + ' (+' + m.task_bonus + ')</p>';
    h += '<button class="sec" id="lk">👕 Aussehen ändern</button><br><button class="pr" id="st">' + (m.rs === "end" ? "Nochmal" : "Runde starten") + '</button>';
    ov(h);
    document.querySelectorAll("[data-team]").forEach(b => b.onclick = () => ws.send(JSON.stringify({t: "team", k: +b.dataset.team})));
    const lkb = $("#lk"); if (lkb) lkb.onclick = () => { editing = true; ov('<h1>Aussehen</h1>' + lookHtml() + '<button class="pr" id="lkok">Fertig</button>'); bindLook();
      $("#lkok").onclick = () => { ws.send(JSON.stringify(Object.assign({t: "look"}, outfit))); editing = false; lastOv = null; paint(st); }; };
    const rd = $("#r-decoy"); if (rd) rd.onclick = () => ws.send(JSON.stringify({t: "decoy", v: !m.decoy}));
    const rr = $("#r-run"), rg = $("#r-guard"); if (rr) rr.onclick = () => ws.send('{"t":"role","r":"runner"}'); if (rg) rg.onclick = () => ws.send('{"t":"role","r":"guard"}');
  }
  else if (m.ps === "goal") ov('<h1>🏁 Im Ziel!</h1><p>Warte auf die anderen.</p>');
  else if (m.ps === "jail") ov('<h1>🔒 In der Zelle</h1><p>Ein Teamkollege muss zu dir kommen und dich berühren – dann bist du frei.</p>');
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
$("#b-lamp").addEventListener("pointerdown", e => { e.preventDefault(); send({t: "lamp"}); });
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
function goFull() { const el = document.documentElement;
  if (!(el.requestFullscreen || el.webkitRequestFullscreen) || window.navigator.standalone === false && /iPhone|iPod/.test(navigator.userAgent)) {
    const tp = $("#tip"); tp.innerHTML = "<b>Vollbild auf dem iPhone</b><br>Safari kann hier kein Vollbild. So geht es: unten <b>Teilen</b> ⬆︎ → <b>«Zum Home-Bildschirm»</b>, dann das Spiel über das neue Symbol starten – ohne Adressleiste.<br><small>Antippen zum Schliessen</small>";
    tp.hidden = false; tp.onclick = () => { tp.hidden = true; }; setTimeout(() => { tp.hidden = true; }, 9000); return; }
  try { (el.requestFullscreen || el.webkitRequestFullscreen).call(el).then(() => screen.orientation && screen.orientation.lock && screen.orientation.lock("landscape").catch(() => {})).catch(() => {}); } catch (e) {} $("#rot").classList.add("ask"); }
$("#full").onclick = goFull;
joinForm();
</script></body></html>"""


func spectator_info() -> Dictionary:
	"""everything the spectators see in Motion Watch (3D-3.22): time, players, meters, what happened"""
	var t := now()
	var ps := []
	for p in players:
		if p == null:
			continue
		var a = p["actor"]
		var pw := ""
		if a.power != "" and t < float(a.power_until):
			pw = a.power
		ps.append({"n": p["name"], "c": "#" + COLORS[p["slot"]].to_html(false), "s": p["state"], "r": p["role"], "susp": int(p["susp"]),
				"k": int(p["caught"]), "i": int(p["items"]), "pw": pw, "tm": int(p["team"]), "on": p["sock"] != null, "carry": bool(p["carry"]),
				"d": snappedf(a.position.distance_to(goal), 0.1), "slot": int(p["slot"]), "hc": int(p.get("hc", 0)),
				"dc": bool(p.get("decoy", false)), "hid": int(p.get("hide_i", -1)) >= 0, "cp": p.get("cps", []).size()})
	var left_items := 0
	for it in items:
		if int(it["by"]) < 0:
			left_items += 1
	var fd := []
	for e in feed.slice(max(0, feed.size() - 6)):
		fd.append({"a": int(t - float(e[0])), "x": e[1]})
	var d := {"open": open, "round": round_state, "mode": main.game_mode, "goal_mode": "flag" if flag_mode() else main.game_goal,
			"goal": goal_name, "players": ps, "items_left": left_items, "items_all": items.size(), "feed": fd, "last_minute": last_minute,
			"teams": main.game_teams, "caps": captures, "shot": main.spec_label if main.spectate else "", "spectate": main.spectate,
			"lives": int(main.game_lives), "ev": ev_kind, "cps_all": checkpoints.size(), "board": board_list(), "records": records,
			"week": week_list(), "sneak": sneak_list(), "week_id": week_id, "task": task.get("text", ""), "task_bonus": int(task.get("bonus", 0)),
			"mwg": {"catches": mwg["catches"], "false": mwg["false"], "wait": int(max(0.0, float(mwg["t"]) - now()))},
			"pics": gallery.map(func(g): return {"n": g["n"], "c": g["c"]}), "night": night_saved >= 0.0}
	if round_state == "countdown":
		d["cd"] = int(ceil(t_start - t))
	if round_state == "play":
		d["left"] = int(max(0.0, t_end - t))
	if round_state == "end":
		d["res"] = results
	return d


# ==== more game (3D-3.25): photos, hiding places, decoy, night, events, checkpoints, ranking, handicap ==============
func _grab_pic(p: Dictionary) -> void:
	var j: PackedByteArray = main.latest_jpg(0)
	if j.size() < 100:
		return
	var img := Image.new()
	if img.load_jpg_from_buffer(j) != OK:
		return
	if img.get_width() > 480:
		img.resize(480, int(480.0 * img.get_height() / img.get_width()), Image.INTERPOLATE_BILINEAR)
	var small := img.save_jpg_to_buffer(0.72)
	gallery.append({"n": p["name"], "c": "#" + COLORS[p["slot"]].to_html(false), "jpg": small})
	if gallery.size() > 8:
		gallery.pop_front()
	if p["sock"] != null:
		p["sock"]["ws"].send_text(JSON.stringify({"t": "pic", "b64": Marshalls.raw_to_base64(small), "txt": "📸 So hat dich die Kamera gesehen"}))


func _send_gallery() -> void:
	"""end of the round: every phone gets the «caught» photos of this round"""
	if gallery.is_empty():
		return
	var arr := []
	for g in gallery:
		arr.append({"n": g["n"], "c": g["c"], "b64": Marshalls.raw_to_base64(g["jpg"])})
	var msg := JSON.stringify({"t": "gal", "pics": arr})
	for q in players:
		if q != null and q["sock"] != null:
			q["sock"]["ws"].send_text(msg)


func gallery_jpg(i: int) -> PackedByteArray:
	return gallery[i]["jpg"] if i >= 0 and i < gallery.size() else PackedByteArray()


func _bush(pos: Vector3) -> Node3D:
	var n := Node3D.new()
	n.position = pos
	var mt := StandardMaterial3D.new()
	mt.albedo_color = Color(0.16, 0.36, 0.14)
	mt.roughness = 0.95
	for k in range(4):
		var m := MeshInstance3D.new()
		var sm := SphereMesh.new()
		var r := randf_range(0.45, 0.65)
		sm.radius = r
		sm.height = r * 1.7
		m.mesh = sm
		m.material_override = mt
		m.position = Vector3(randf_range(-0.35, 0.35), r * 0.65, randf_range(-0.35, 0.35))
		n.add_child(m)
	root.add_child(n)
	return n


func _place_hides(n: int) -> void:
	"""hiding places: bushes. Crouching or lying in one, the cameras do not see you - but only for 8 seconds"""
	for h in hides:
		if is_instance_valid(h["node"]):
			h["node"].queue_free()
	hides.clear()
	for i in range(n):
		var pos := _spot_far(7.0)
		hides.append({"node": _bush(pos), "pos": pos})


func _hide_check(p: Dictionary) -> bool:
	var a = p["actor"]
	var t := now()
	var hi: int = int(p.get("hide_i", -1))
	if hi >= 0:
		if hi >= hides.size() or a.position.distance_to(hides[hi]["pos"]) > 1.3 or a.ctl_posture == 0:
			p["hide_i"] = -1                             # left the bush
			return false
		var left: float = HIDE_MAX - (t - float(p["hide_t0"]))
		if left <= 0.0:
			p["hide_i"] = -1
			p["hide_cd"][hi] = t + 12.0
			_say(p, "🌳 Zu lange im Versteck – raus da!", 2.5)
			return false
		_say(p, "🌳 Versteckt – noch %d s" % int(ceil(left)), 0.4)
		return true
	if a.ctl_posture == 0:
		return false
	for i in range(hides.size()):
		if a.position.distance_to(hides[i]["pos"]) < 1.0 and t > float(p["hide_cd"].get(i, 0.0)):
			p["hide_i"] = i
			p["hide_t0"] = t
			news("🌳 %s versteckt sich" % p["name"])
			return true
	return false


func _place_checkpoints(n: int) -> void:
	"""checkpoints: glowing rings between start and goal (only the players see them), bonus on the first visit"""
	for c in checkpoints:
		if is_instance_valid(c["node"]):
			c["node"].queue_free()
	checkpoints.clear()
	if n <= 0:
		return
	var a0 := Vector3.ZERO
	var cnt := 0
	for p in players:
		if p != null and p["role"] == "runner":
			a0 += start_point(p["slot"])
			cnt += 1
	a0 = (a0 / cnt) if cnt > 0 else start_point(0)
	for i in range(n):
		var f: float = float(i + 1) / float(n + 1)
		var c: Vector3 = a0.lerp(goal, f)
		var side := (goal - a0).cross(Vector3.UP).normalized()
		c += side * randf_range(-8.0, 8.0)
		var pos := _g(main.free_spot(c, 0.6, true))
		var nd := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = 0.55
		tm.outer_radius = 0.7
		nd.mesh = tm
		nd.rotation = Vector3(PI / 2, 0, 0)
		nd.position = pos + Vector3(0, 0.75, 0)
		nd.material_override = _glow(Color(1.0, 0.55, 0.15))
		nd.layers = 16
		root.add_child(nd)
		checkpoints.append({"node": nd, "pos": pos})


func _events_tick(t: float) -> void:
	"""random events: thunderstorm, a dog, a car - one at a time, about every minute"""
	if not main.game_events:
		return
	if ev_kind != "":
		if t >= ev_until:
			_event_end()
		return
	if t < ev_next:
		return
	var kinds := ["storm", "dog", "car"]
	ev_kind = kinds[randi() % kinds.size()]
	ev_until = t + 15.0
	ev_warned.clear()
	match ev_kind:
		"storm":
			ev_weather = main.weather
			main.weather = "rain"
			news("⛈ Gewitter! 15 s lang hört das Mikrofon fast nichts")
			for q in players:
				if q != null:
					_say(q, "⛈ Gewitter – jetzt hört man dich kaum!", 3.0)
		"dog":
			var rs := []
			for q in players:
				if q != null and q["role"] == "runner" and q["state"] == "play":
					rs.append(q)
			var c: Vector3 = rs[randi() % rs.size()]["actor"].position if not rs.is_empty() else goal * 0.5
			var from := c + Vector3(randf_range(-12.0, 12.0), 0, randf_range(-12.0, 12.0))
			ev_node = main.spawn("dog", from, c + (c - from) * 1.5)
			news("🐕 Ein Hund läuft übers Feld – nicht zu nahe kommen!")
		"car":
			var z: float = goal.z * randf_range(0.3, 0.7)
			var sgn := 1.0 if randf() < 0.5 else -1.0
			ev_node = main.spawn("car", Vector3(-45.0 * sgn, 0, z), Vector3(45.0 * sgn, 0, z))
			news("🚗 Ein Auto fährt vorbei" + (" – Vorsicht, Scheinwerfer!" if main.is_dark() else " – der Motor übertönt die Schritte"))


func _event_end() -> void:
	if ev_kind == "storm" and ev_weather != "":
		main.weather = ev_weather
	ev_weather = ""
	ev_kind = ""
	ev_node = null
	ev_next = now() + randf_range(50.0, 85.0)


func week_of(unix: float) -> String:
	"""the ISO week (Monday to Sunday) as «2026-W44»"""
	var d := Time.get_datetime_dict_from_unix_time(int(unix))
	var wd := (int(d["weekday"]) + 6) % 7                       # 0 = Monday
	var thu := int(unix) + (3 - wd) * 86400                     # the Thursday of this week decides the year
	var td := Time.get_datetime_dict_from_unix_time(thu)
	var jan1 := Time.get_unix_time_from_datetime_dict({"year": td["year"], "month": 1, "day": 1, "hour": 0, "minute": 0, "second": 0})
	return "%d-W%02d" % [int(td["year"]), int((thu - jan1) / 86400) / 7 + 1]


func _board_load() -> void:
	var day := Time.get_date_string_from_system()
	var wk := week_of(Time.get_unix_time_from_system())
	if board_day == day and week_id == wk:
		return
	board_day = day
	board = {}
	records = {}
	week = {}
	week_id = wk
	var f := FileAccess.open("user://game_board.json", FileAccess.READ)
	if f != null:
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary and str(d.get("day", "")) == day:    # the ranking of the evening: from the same day only
			board = d.get("board", {})
			records = d.get("records", {})
		if d is Dictionary and str(d.get("week_id", "")) == wk:  # the ranking of the week: from the same week only
			week = d.get("week", {})


func _board_save() -> void:
	var f := FileAccess.open("user://game_board.json", FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"day": board_day, "board": board, "records": records, "week_id": week_id, "week": week}))


func _board_add() -> void:
	_board_load()
	var top := -1
	for r in results:
		top = max(top, int(r["score"]))
	for p in players:
		if p == null:
			continue
		var key := str(p["name"]).to_lower()
		var b: Dictionary = board.get(key, {"n": p["name"], "c": "#" + COLORS[p["slot"]].to_html(false), "score": 0, "rounds": 0, "wins": 0, "best": 0, "clean": 0})
		var sc := 0
		for r in results:
			if r["n"] == p["name"]:
				sc = int(r["score"])
		b["n"] = p["name"]
		b["c"] = "#" + COLORS[p["slot"]].to_html(false)
		b["score"] = int(b["score"]) + sc
		b["rounds"] = int(b["rounds"]) + 1
		if sc == top and top > 0:
			b["wins"] = int(b["wins"]) + 1
		if p["role"] == "runner" and int(p["caught"]) == 0:
			b["clean"] = int(b["clean"]) + 1
		if p["role"] == "runner" and float(p.get("t_goal", 0.0)) > 0.0:
			var secs := int(float(p["t_goal"]) - t_start)
			if secs > 0 and (int(b["best"]) == 0 or secs < int(b["best"])):
				b["best"] = secs
			if secs > 0 and (not records.has("fast") or secs < int(records["fast"][1])):
				records["fast"] = [p["name"], secs]
		if int(p["items"]) > 0 and (not records.has("items") or int(p["items"]) > int(records["items"][1])):
			records["items"] = [p["name"], int(p["items"])]
		if p["role"] == "guard" and int(p["catches"]) > 0 and (not records.has("catches") or int(p["catches"]) > int(records["catches"][1])):
			records["catches"] = [p["name"], int(p["catches"])]
		var bl: int = learn.blind_s(p) if p["role"] == "runner" else 0   # 3D-3.53: «Bester Schleicher» - blind spots found
		if bl > 0:
			b["blind"] = int(b.get("blind", 0)) + bl
			if not records.has("blind") or bl > int(records["blind"][1]):
				records["blind"] = [p["name"], bl]
		board[key] = b
		var w: Dictionary = week.get(key, {"n": p["name"], "c": b["c"], "score": 0, "rounds": 0, "wins": 0, "tasks": 0})
		w["n"] = p["name"]
		w["c"] = b["c"]
		w["score"] = int(w["score"]) + sc
		w["rounds"] = int(w["rounds"]) + 1
		if sc == top and top > 0:
			w["wins"] = int(w["wins"]) + 1
		if bool(p.get("task_ok", false)):
			w["tasks"] = int(w["tasks"]) + 1
			b["tasks"] = int(b.get("tasks", 0)) + 1
		if bl > 0:
			w["blind"] = int(w.get("blind", 0)) + bl
		week[key] = w
	_board_save()


func board_list() -> Array:
	_board_load()
	var out: Array = board.values()
	out.sort_custom(func(x, y): return int(x["score"]) > int(y["score"]))
	return out.slice(0, 10)


func sneak_list() -> Array:
	"""3D-3.53: «Bester Schleicher der Woche»: who was longest visible but not reported by Motion Watch"""
	_board_load()
	var out: Array = week.values().filter(func(x): return int(x.get("blind", 0)) > 0)
	out.sort_custom(func(x, y): return int(x.get("blind", 0)) > int(y.get("blind", 0)))
	return out.slice(0, 5)


func week_list() -> Array:
	_board_load()
	var out: Array = week.values()
	out.sort_custom(func(x, y): return int(x["score"]) > int(y["score"]))
	return out.slice(0, 10)


func _pick_task() -> void:
	task = {}
	if not main.game_tasks or flag_mode():
		return
	var pool := []
	for t in TASKS:
		if t[0] == "items" and int(main.game_items) < 2:
			continue
		if t[0] == "hide" and int(main.game_hides) <= 0:
			continue
		if t[0] == "nostone" and not main.game_stones:
			continue
		pool.append(t)
	var t2: Array = pool[randi() % pool.size()]
	task = {"id": t2[0], "text": t2[1], "bonus": t2[2]}
	news("🎯 Aufgabe dieser Runde: " + str(task["text"]))


func _task_done(p: Dictionary) -> bool:
	if task.is_empty() or p["role"] != "runner":
		return false
	var at_goal: bool = p["state"] == "goal"
	var secs := float(p.get("t_goal", 0.0)) - t_start
	match str(task["id"]):
		"crawl":
			return at_goal and float(p.get("up_m", 0.0)) < 3.0
		"nostone":
			return at_goal and int(p.get("stones", 0)) == 0
		"fast":
			return at_goal and secs > 0.0 and secs < 60.0
		"calm":
			return float(p.get("max_susp", 0.0)) <= 50.0 and (at_goal or p["state"] == "play")
		"nocatch":
			return int(p["caught"]) == 0 and (at_goal or p["state"] == "play")
		"items":
			return int(p["items"]) >= 2
		"hide":
			return float(p.get("hide_s", 0.0)) >= 10.0
	return false


func board_reset() -> void:
	board = {}
	records = {}
	board_day = Time.get_date_string_from_system()
	_board_save()
	news("🏆 Rangliste zurückgesetzt")


func set_handicap(slot: int, level: int) -> void:
	if slot >= 0 and slot < players.size() and players[slot] != null:
		players[slot]["hc"] = clampi(level, 0, 2)
		players[slot]["actor"].handicap = clampi(level, 0, 2)
		paint()


func _auto_handicap() -> void:
	"""whoever leads the ranking of the evening gets a handicap (if switched on)"""
	if not main.game_autohandicap:
		return
	var bl := board_list()
	var lead := str(bl[0]["n"]).to_lower() if not bl.is_empty() and int(bl[0]["rounds"]) > 0 else ""
	for p in players:
		if p != null and p["role"] == "runner":
			var on := lead != "" and str(p["name"]).to_lower() == lead and count() > 1
			p["hc"] = 1 if on else 0
			if on:
				news("🎯 Handicap für %s (führt die Rangliste an)" % p["name"])
