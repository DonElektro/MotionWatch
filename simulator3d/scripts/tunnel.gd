extends Node
## Tunnel zu MoveEye (3D-3.45): for a PC or a virtual machine whose firewall lets nothing in (no admin rights to allow
## the port). The simulator connects OUT to MoveEye (port 8766) - every firewall allows that - and keeps a few
## connections ready. When MoveEye wants something it writes "GO <port>" on one of them; the simulator then connects to
## itself (127.0.0.1:<port>: 8765 = the simulator, 5057 = the AI helper of MoveEye on this PC) and passes the bytes both
## ways. Paired with the 6-digit code from the page of MoveEye (Simulator → Simulator hinter einer Firewall).

const PORT := 8766
const IDLE := 10                    # connections kept ready
const CHUNK := 65536

var main
var host := ""
var code := ""
var on := false
var conns := []                     # {"o": StreamPeerTCP (to MoveEye), "st": "connect|hello|idle|pipe", "l": StreamPeerTCP (local), "buf": String, "t": float}
var msg := "aus"
var ok_t := 0.0                     # last time MoveEye accepted the code
var bytes := 0
var _next := 0.0
var _fails := 0                     # 3D-3.75: failed tries in a row - wait longer each time (3 s … 15 s)
const RECYCLE := 40.0               # 3D-3.75: an idle connection is renewed after 40-55 s (routers forget quiet connections)
const PIPE_IDLE := 180.0            # 3D-3.75: a pipe without any byte for 3 minutes is closed


func set_on(v: bool) -> void:
	on = v and host != "" and code.length() == 6
	if on and main.has_method("set_stream") and not main.stream_on:
		main.set_stream.call_deferred(true, true)       # 3D-3.75: busy after an update -> a spare port (main._stream_watch keeps trying)             # MoveEye reaches the simulator only while it «sends»
	_fails = 0
	_next = 0.0
	if not on:
		for c in conns:
			_close(c)
		conns.clear()
		msg = "aus" if not v else "Adresse und Code fehlen"


func state() -> Dictionary:
	return {"on": on, "host": host, "ok": Time.get_ticks_msec() / 1000.0 - ok_t < 30.0, "msg": msg, "pipes": conns.filter(func(c): return c["st"] == "pipe").size(), "mb": snappedf(bytes / 1e6, 0.1)}


func _fail(now: float, text: String) -> void:
	msg = text
	_fails += 1
	_next = now + minf(15.0, 3.0 * pow(1.5, mini(_fails - 1, 6)))


func _close(c: Dictionary) -> void:
	if c.get("o") != null:
		(c["o"] as StreamPeerTCP).disconnect_from_host()
	if c.get("l") != null:
		(c["l"] as StreamPeerTCP).disconnect_from_host()
	c["st"] = "dead"


func _process(_dt: float) -> void:
	if not on:
		return
	var now := Time.get_ticks_msec() / 1000.0
	var ready := 0
	for c in conns:
		_step(c, now)
		if c["st"] in ["connect", "hello", "idle"]:
			ready += 1
	conns = conns.filter(func(c): return c["st"] != "dead")
	if now >= _next:
		for _k in range(IDLE - ready):                  # MoveEye asks often (pictures, state): always some ready
			if conns.size() >= 48:
				break
			var o := StreamPeerTCP.new()
			if o.connect_to_host(host, PORT) == OK:
				conns.append({"o": o, "st": "connect", "l": null, "buf": PackedByteArray(), "t": now})
			else:
				_fail(now, "Adresse ungültig")
				break


func _step(c: Dictionary, now: float) -> void:
	var o: StreamPeerTCP = c["o"]
	o.poll()
	var s := o.get_status()
	if s == StreamPeerTCP.STATUS_ERROR or (s == StreamPeerTCP.STATUS_NONE and c["st"] != "connect"):
		if c["st"] == "connect" or c["st"] == "hello":
			msg = "MoveEye nicht erreichbar (%s:%d)" % [host, PORT]
			_next = now + 3.0                       # wait a little before trying again
		_close(c)
		return
	match c["st"]:
		"connect":
			if s == StreamPeerTCP.STATUS_CONNECTED:
				o.set_no_delay(true)
				o.put_data(("MWTUN1 %s\n" % code).to_utf8_buffer())
				c["st"] = "hello"
				c["t"] = now
			elif now - float(c["t"]) > 6.0:
				_fail(now, "MoveEye antwortet nicht (%s:%d)" % [host, PORT])
				_close(c)
		"hello", "idle":
			var n := o.get_available_bytes()
			if n > 0:
				var r: Array = o.get_partial_data(min(n, CHUNK))
				c["buf"].append_array(r[1])
			while (c["buf"] as PackedByteArray).find(10) >= 0:
				var b: PackedByteArray = c["buf"]
				var k := b.find(10)
				var line: String = b.slice(0, k).get_string_from_ascii().strip_edges()
				c["buf"] = b.slice(k + 1)                # what comes after the line already belongs to the request
				if c["st"] == "hello":
					if line == "OK":
						c["st"] = "idle"
						c["t"] = now
						c["life"] = RECYCLE + randf() * 15.0
						ok_t = now
						_fails = 0
						msg = "verbunden mit MoveEye (%s:%d)" % [host, PORT]
					else:
						_fail(now, "Code falsch – auf der Seite von MoveEye nachsehen")
						_close(c)
						return
				elif line.begins_with("GO "):
					var port := int(line.substr(3))
					if not port in [8765, 5057]:
						_close(c)
						return
					var l := StreamPeerTCP.new()
					l.connect_to_host("127.0.0.1", main.net.port if port == 8765 and main.net != null and main.net.listening else port)   # 3D-3.68: also on a spare port
					for _w in 20:                           # to itself: connected at once - no need to wait a frame
						l.poll()
						if l.get_status() != StreamPeerTCP.STATUS_CONNECTING:
							break
						OS.delay_usec(250)
					c["l"] = l
					c["st"] = "pipe"
					c["t"] = now
					ok_t = now
					_step(c, now)                           # pass the request on in this same frame
					return
			if c["st"] == "hello" and now - float(c["t"]) > 8.0:
				_close(c)
			elif c["st"] == "idle" and now - float(c["t"]) > float(c.get("life", RECYCLE)) and (c["buf"] as PackedByteArray).is_empty():
				_close(c)                               # renewed by _process (a fresh one is opened at once)
		"pipe":
			var l: StreamPeerTCP = c["l"]
			l.poll()
			var ls := l.get_status()
			if ls == StreamPeerTCP.STATUS_CONNECTING:
				if now - float(c["t"]) > 5.0:
					_close(c)
				return
			if ls != StreamPeerTCP.STATUS_CONNECTED:
				_flush(l, o)                           # what the local side still sent
				_close(c)
				return
			if not (c["buf"] as PackedByteArray).is_empty():    # the start of the request came with the GO line
				l.put_data(c["buf"])
				bytes += (c["buf"] as PackedByteArray).size()
				c["buf"] = PackedByteArray()
			if _flush(o, l) + _flush(l, o) > 0:
				c["t"] = now
			elif now - float(c["t"]) > PIPE_IDLE:
				_close(c)


func _flush(a: StreamPeerTCP, b: StreamPeerTCP) -> int:
	"""everything that has arrived on a goes out on b (several chunks per frame); returns the bytes passed on"""
	var got := 0
	for _i in 32:
		var n := a.get_available_bytes()
		if n <= 0:
			break
		var r: Array = a.get_partial_data(min(n, CHUNK))
		var data: PackedByteArray = r[1]
		if data.is_empty():
			break
		b.put_data(data)
		bytes += data.size()
		got += data.size()
	return got
