extends Node
## The connection to MoveEye: a small HTTP server with the same protocol as motionwatch_sim_interface.py
## (POST /state, GET /info, /events, /cam/<n>/video.mjpg, /cam/<n>/snapshot.jpg, /thermal.bin, GET+POST /control).

const BOUNDARY := "mwsimframe"
const MAX_BUFFER := 4 * 1024 * 1024        # a client that does not read its pictures: frames are skipped

var main                                   # the main script (world, cameras)
var server := TCPServer.new()
var clients: Array = []                    # {peer, buf, out, stream_cam, fps, last_sent, last_frame}
var port := 8765
var listening := false
var error_text := ""


var beacon := PacketPeerUDP.new()
var beacon_t := 0.0


func start(p: int) -> void:
	if listening and p == port and server.is_listening():
		return                                        # 3D-3.98: already sending on this port (a second start broke it: «already in use»)
	if server.is_listening():
		server.stop()
	port = p
	beacon.set_broadcast_enabled(true)
	var err := server.listen(port, "*")
	listening = err == OK
	error_text = "" if listening else "Port %d is busy (another simulator running?)" % port


func stop() -> void:
	"""sending off: no more pictures, no more "here is a simulator" messages - MoveEye does not see the simulator"""
	for c in clients:
		c["peer"].disconnect_from_host()
	clients = []
	server.stop()
	listening = false
	error_text = ""


func _send_beacon() -> void:
	"""every 2 s into the network: "here is a simulator" - MoveEye finds it by itself (UDP port 8764)"""
	var nm: String = main.beacon_name() if main.has_method("beacon_name") else "MoveEye Sim · 3D %s" % main.VERSION
	var cp: Dictionary = main.cpu_now() if main.has_method("cpu_now") else {}
	var msg := JSON.stringify({"mwsim": 1, "name": nm, "pc_cpu": cp.get("pc"), "sim_cpu": cp.get("sim"), "port": port, "version": main.VERSION, "host": main.host_name()}).to_utf8_buffer()
	for dest in ["255.255.255.255", "127.0.0.1"]:
		beacon.set_dest_address(dest, 8764)
		beacon.put_packet(msg)


func _process(_dt: float) -> void:
	if not listening:
		return
	var tnow := Time.get_ticks_msec() / 1000.0
	if tnow - beacon_t > 2.0:
		beacon_t = tnow
		_send_beacon()
	while server.is_connection_available():
		var peer: StreamPeerTCP = server.take_connection()
		peer.set_no_delay(true)
		clients.append({"peer": peer, "buf": PackedByteArray(), "out": PackedByteArray(), "stream_cam": -1, "fps": 0.0,
				"last_sent": 0.0, "last_frame": -1, "close_after": false, "t0": Time.get_ticks_msec()})
	var keep: Array = []
	for c in clients:
		var peer: StreamPeerTCP = c["peer"]
		peer.poll()
		var st := peer.get_status()
		if st != StreamPeerTCP.STATUS_CONNECTED and st != StreamPeerTCP.STATUS_CONNECTING:
			continue
		if c["stream_cam"] < 0:
			var n := peer.get_available_bytes()
			if n > 0:
				var r: Array = peer.get_data(n)
				if r[0] == OK:
					var bb: PackedByteArray = c["buf"]
					bb.append_array(r[1])
					c["buf"] = bb
			if c["out"].size() == 0 and not c["close_after"]:
				_try_request(c)
			elif c["out"].size() == 0 and c["close_after"] and Time.get_ticks_msec() - c["t0"] > 20000:
				continue
		else:
			_stream_tick(c)
		_flush(c)
		if c["close_after"] and c["out"].size() == 0:
			peer.disconnect_from_host()
			continue
		if c["stream_cam"] < 0 and c["out"].size() == 0 and Time.get_ticks_msec() - c["t0"] > 30000:
			peer.disconnect_from_host()          # idle connection
			continue
		keep.append(c)
	clients = keep


func stream_demand() -> Dictionary:
	"""pictures per second wanted per camera by the streams that are open (cam -> fps)"""
	var d := {}
	for c in clients:
		if c["stream_cam"] >= 0:
			d[c["stream_cam"]] = max(float(d.get(c["stream_cam"], 0.0)), float(c["fps"]))
	return d


func _flush(c: Dictionary) -> void:
	if c["out"].size() == 0:
		return
	var o: PackedByteArray = c["out"]
	var r: Array = c["peer"].put_partial_data(o)
	if r[0] == OK and int(r[1]) > 0:
		c["out"] = o.slice(int(r[1]))


func _try_request(c: Dictionary) -> void:
	var buf: PackedByteArray = c["buf"]
	var end := _find(buf, "\r\n\r\n".to_utf8_buffer())
	if end < 0:
		return
	var head := buf.slice(0, end).get_string_from_utf8()
	var lines := head.split("\r\n")
	var first := lines[0].split(" ")
	if first.size() < 2:
		c["close_after"] = true
		return
	var method := first[0]
	var target := first[1]
	var headers := {}
	for i in range(1, lines.size()):
		var p := lines[i].find(":")
		if p > 0:
			headers[lines[i].substr(0, p).strip_edges().to_lower()] = lines[i].substr(p + 1).strip_edges()
	var length := int(headers.get("content-length", "0"))
	if buf.size() < end + 4 + length:
		return                                   # body not complete yet
	var body := buf.slice(end + 4, end + 4 + length)
	c["buf"] = buf.slice(end + 4 + length)
	c["t0"] = Time.get_ticks_msec()
	var path := target
	var query := {}
	var q := target.find("?")
	if q >= 0:
		path = target.substr(0, q)
		for kv in target.substr(q + 1).split("&"):
			var e := kv.find("=")
			if e > 0:
				query[kv.substr(0, e)] = kv.substr(e + 1).uri_decode()
	_handle(c, method, path, query, body, c["peer"].get_connected_host())


func _find(hay: PackedByteArray, needle: PackedByteArray) -> int:
	if hay.size() < needle.size():
		return -1
	for i in range(hay.size() - needle.size() + 1):
		if hay[i] == needle[0]:
			var ok := true
			for j in range(1, needle.size()):
				if hay[i + j] != needle[j]:
					ok = false
					break
			if ok:
				return i
	return -1


func _send(c: Dictionary, code: int, body: PackedByteArray, ctype := "application/json", extra := {}) -> void:
	var reason: String = {200: "OK", 400: "Bad Request", 404: "Not Found", 500: "Error"}.get(code, "OK")
	var h := "HTTP/1.1 %d %s\r\nContent-Type: %s\r\nContent-Length: %d\r\nCache-Control: no-store\r\nConnection: keep-alive\r\n" % [code, reason, ctype, body.size()]
	for k in extra:
		h += "%s: %s\r\n" % [k, str(extra[k])]
	h += "\r\n"
	var o: PackedByteArray = c["out"]
	o.append_array(h.to_utf8_buffer())
	o.append_array(body)
	c["out"] = o


func _json(c: Dictionary, obj, code := 200) -> void:
	_send(c, code, JSON.stringify(obj).to_utf8_buffer())


func _handle(c: Dictionary, method: String, path: String, query: Dictionary, body: PackedByteArray, host: String) -> void:
	if main.smalltv != null and main.smalltv.wants(path):      # 3D-4.19: virtueller SmallTV (smalltv.gd), gleiche Schnittstelle wie das Gerät
		main.smalltv.handle(self, c, method, path, query, body, host)
		return
	if method == "POST" and path == "/state":
		var d = JSON.parse_string(body.get_string_from_utf8())
		if typeof(d) != TYPE_DICTIONARY:
			_json(c, {"ok": false, "error": "bad state"}, 400)
			return
		var lead: bool = main.on_state(d, host)
		var rep: Dictionary = main.world_reply()
		if main.get("simint") != null:
			rep.merge(main.simint.reply(), true)       # 30.10.2026: servo faults, 5 V, thermal model, warm hand (simint.gd)
		if not lead:                                   # 3D-4.9: another MoveEye steers the simulator - this one only watches
			rep["follower"] = true
			rep["leader"] = main.mw_owner_name
			rep["mw_cmd"] = null
		_json(c, rep)
		return
	if method == "POST" and path == "/control":
		var d2 = JSON.parse_string(body.get_string_from_utf8())
		_json(c, main.control(d2 if typeof(d2) == TYPE_DICTIONARY else {}))
		return
	if method == "POST" and path == "/upload":
		_json(c, {"ok": false, "error": "not supported"})
		return
	if method != "GET" and method != "HEAD":
		_json(c, {"ok": false, "error": "unknown path"}, 404)
		return
	if path.begins_with("/dataset/") and path.ends_with(".jpg"):          # Trainingsbilder (3D-3.44)
		var i := int(path.get_file().get_basename())
		var b: PackedByteArray = main.dataset.jpg(i)
		if b.is_empty():
			_json(c, {"ok": false, "error": "no such picture"}, 404)
		else:
			_send(c, 200, b, "image/jpeg")
		return
	match path:
		"/info":
			_json(c, main.info())
		"/control":
			_json(c, main.control_info())
		"/events":
			_json(c, {"v": 1, "events": main.events_since(int(query.get("since", "0")))})
		"/thermal.bin":
			var a: PackedFloat32Array = main.thermal_values()
			if a.size() == 0:
				_json(c, {"ok": false, "error": "no thermal picture yet"}, 404)
			else:
				_send(c, 200, a.to_byte_array(), "application/octet-stream", {"X-Width": main.TH_W, "X-Height": main.TH_H, "X-Unit": "C"})
		"/thermal.json":
			var a2: PackedFloat32Array = main.thermal_values()
			var arr := []
			for v in a2:
				arr.append(snappedf(v, 0.01))
			_json(c, {"v": 1, "w": main.TH_W, "h": main.TH_H, "unit": "C", "data": arr})
		"/game_qr.png":                                  # the QR code of the game (for the page of MoveEye) - 3D-3.20
			if main.game == null or not main.game.open:
				_json(c, {"ok": false, "error": "game not open"}, 404)
			else:
				var tq: ImageTexture = main.game.Qr.texture(main.game.address(), 8)
				_send(c, 200, tq.get_image().save_png_to_buffer() if tq != null else PackedByteArray(), "image/png")
		"/view.jpg":                                     # the simulator window (3D view with map, compass, buttons) - 3D-3.18
			main.view_want_t = main.now()
			main.view_request(query)                     # 3D-3.58: size, quality, WebP of the next pictures
			_send(c, 200, main.view_jpg, main.view_mime)
		"/view.mjpg":
			main.view_want_t = main.now()
			var fv := float(query.get("fps", "6"))
			c["fps"] = clampf(fv, 1.0, 12.0)
			main.view_fps = c["fps"]
			c["stream_cam"] = 3
			c["dock"] = str(query.get("dock", "")) == "1"   # 3D-4.x: MoveEye's simulator page: only the 3D view and the dock (padview.gd)
			var hv := "HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace; boundary=%s\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n" % BOUNDARY
			var ov: PackedByteArray = c["out"]
			ov.append_array(hv.to_utf8_buffer())
			c["out"] = ov
		_:
			var parts := path.strip_edges().trim_prefix("/").split("/")
			if parts.size() == 2 and parts[0] == "shut_pic":    # 3D-4.x: the photo of an «Auslöser» hit (for MoveEye's test inbox)
				var sj: PackedByteArray = main.game.shut.pic(int(parts[1].get_basename())) if main.game != null and main.game.shut != null else PackedByteArray()
				if sj.is_empty():
					_json(c, {"ok": false, "error": "no picture"}, 404)
				else:
					_send(c, 200, sj, "image/jpeg")
				return
			if parts.size() == 2 and parts[0] == "disc_pic":    # Erlebniswelt 20–23: the picture of entry <i> of the Entdeckungsbuch (this scene)
				var dj: PackedByteArray = main.entdecken.pic_bytes(str(query.get("scene", "")), int(parts[1].get_basename())) if main.entdecken != null else PackedByteArray()
				if dj.is_empty():
					_json(c, {"ok": false, "error": "no picture"}, 404)
				else:
					_send(c, 200, dj, "image/jpeg")
				return
			if parts.size() == 2 and parts[0] == "game_pic":    # the «caught» photos (3D-3.25)
				var gj: PackedByteArray = main.game.gallery_jpg(int(parts[1].get_basename())) if main.game != null else PackedByteArray()
				if gj.is_empty():
					_json(c, {"ok": false, "error": "no picture"}, 404)
				else:
					_send(c, 200, gj, "image/jpeg")
				return
			if parts.size() == 3 and parts[0] == "cam" and parts[1].is_valid_int():
				var cam := int(parts[1])
				if cam < 0 or cam > 1:
					_json(c, {"ok": false, "error": "no such camera"}, 404)
					return
				var wt = main.get("weit")                    # (the second device, device.gd, has no wide camera object)
				if cam == 1 and wt != null and not wt.installed():
					_json(c, {"ok": false, "error": "wide camera not installed (blind cover)"}, 404)   # P9
					return
				if parts[2] == "snapshot.jpg":
					main.want_snapshot(cam)
					_send(c, 200, main.latest_jpg(cam), "image/jpeg")
					return
				if parts[2] == "video.mjpg":
					var top: float = main.CAM_FPS[cam]
					var f := float(query.get("fps", "0"))
					c["fps"] = min(top, max(1.0, f)) if f > 0 else top
					c["stream_cam"] = cam
					var h := "HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace; boundary=%s\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n" % BOUNDARY
					var o: PackedByteArray = c["out"]
					o.append_array(h.to_utf8_buffer())
					c["out"] = o
					return
			_json(c, {"ok": false, "error": "unknown path"}, 404)


func _stream_tick(c: Dictionary) -> void:
	var cam: int = c["stream_cam"]
	var now := Time.get_ticks_msec() / 1000.0
	if now - float(c["last_sent"]) < 1.0 / max(1.0, float(c["fps"])) * 0.95:
		return
	if cam == 3:
		main.view_want_t = main.now()
		if bool(c.get("dock", false)) and main.padview != null:
			main.padview.dock_t = main.now()
	var n: int = main.view_no if cam == 3 else main.frame_no[cam]
	if n == c["last_frame"]:
		return
	if c["out"].size() > MAX_BUFFER:
		return                                   # slow client: skip this picture
	if cam == 3:
		main.view_mjpg_t = main.now()
		if main.view_mime != "image/jpeg":
			return                                   # the next picture comes as JPEG
	var jpg: PackedByteArray = main.view_jpg if cam == 3 else main.latest_jpg(cam)
	if jpg.size() == 0:
		return
	var h := "--%s\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % [BOUNDARY, jpg.size()]
	var o: PackedByteArray = c["out"]
	o.append_array(h.to_utf8_buffer())
	o.append_array(jpg)
	o.append_array("\r\n".to_utf8_buffer())
	c["out"] = o
	c["last_sent"] = now
	c["last_frame"] = n
