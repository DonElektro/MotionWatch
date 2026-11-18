extends Node
## «Demo beim Host» (Besitzer 15.11.2026): der Simulator im Browser (kevlaschef.com/moveeye/sim/ bzw. die Homepage) verbindet
## sich mit dem Demo-MoveEye auf dem Webspace – wss://<diese Seite>/demo/simtun, also relativ zur Herkunft der Seite (kein
## fester Rechnername). Schalter «on», ab Werk an; «?moveeye=aus» in der Adresse schaltet ihn ab.
## Sonst ist der Simulator der Server für MoveEye (net.gd, Port 8765) – ein Browser kann keinen Server öffnen. Darum trägt EINE
## WebSocket-Leitung alle HTTP-Verbindungen, die MoveEye zum Simulator öffnet (Protokoll MWTUN2, MoveEye Teil 639zzzzw):
##   Simulator -> «MWTUN2 <code> <instanz>» (Text), MoveEye -> «OK» / «NO»
##   MoveEye -> «OPEN <id> 8765»: eine neue Verbindung (wie TCP zu Port 8765) – hier ein Kanal, den net.gd wie einen
##             StreamPeerTCP behandelt (add_peer); beide Richtungen: Binär = 4 Byte Kanal (big endian) + Bytes; «CLOSE <id>»
##   «PING» / «PONG» (Text); «TAKEN»: ein neueres Simulator-Fenster hat übernommen – nicht von selbst neu verbinden.
##   «VIS hidden» / «VIS visible» (Text, Sim 3.72.0): der Tab dieses Simulators ist im Hintergrund / wieder sichtbar. Im
##             Hintergrund zeichnet der Browser nichts (requestAnimationFrame steht, Godot rechnet nicht) - MoveEye 4.16.0 behält
##             dann das letzte Bild, fragt nichts und verbindet nicht neu; die Leitung hält (der Browser beantwortet Pings selbst).
## Verbunden: main.stream_on = true (main.connected() / Bilder wie mit einem echten MoveEye), getrennt: wieder wie vorher.
## Wird von web.gd (nur im Browser) angelegt:  var wm = preload("res://scripts/web_moveeye.gd").new(); wm.main = main; main.add_child(wm)
## Zustand für die Oberfläche: state() -> {"on", "status": "aus|verbinde|verbunden|besetzt|fehler", "url", "kanaele"}.

const T = preload("res://scripts/i18n.gd")
const PATH := "/demo/simtun"
const MAX_OUT := 2 * 1024 * 1024           # nicht mehr in die Leitung, solange so viel noch nicht weg ist (net.gd überspringt Bilder)

var main
var on := true
var status := "aus"
var ws: WebSocketPeer = null
var chans := {}                              # id -> Kanal
var inst := ""
var _hello := false
var _next := 0.0
var _fails := 0
var _was_stream := false
var _url := ""
var _vis_cb = null                           # JavaScriptBridge-Rückruf für «visibilitychange» (muss am Leben bleiben)


class Kanal extends RefCounted:
	## eine HTTP-Verbindung von MoveEye – die Methoden, die net.gd von StreamPeerTCP braucht
	var wm
	var id := 0
	var inbuf := PackedByteArray()
	var open := true

	func poll() -> void:
		pass

	func get_status() -> int:
		return StreamPeerTCP.STATUS_CONNECTED if open and wm.verbunden() else StreamPeerTCP.STATUS_NONE

	func get_available_bytes() -> int:
		return inbuf.size()

	func get_data(n: int) -> Array:
		var d := inbuf.slice(0, n)
		inbuf = inbuf.slice(n)
		return [OK, d]

	func put_partial_data(d: PackedByteArray) -> Array:
		if not open or not wm.verbunden():
			return [ERR_CONNECTION_ERROR, 0]
		return [OK, wm.senden(id, d)]

	func disconnect_from_host() -> void:
		if open:
			open = false
			wm.schliessen(id, true)

	func get_connected_host() -> String:
		return "127.0.0.1"                       # das Demo-MoveEye dieses Besuchers (es ist sein eigener Simulator)

	func set_no_delay(_b: bool) -> void:
		pass


const CFG_DATEI := "user://web_moveeye.cfg"


func _ready() -> void:
	inst = "%d-%d" % [int(Time.get_unix_time_from_system()), randi() % 100000]
	if main != null:
		main.set_meta("web_moveeye", self)           # web_demo.gd / handy.gd fragen danach (kein Feld in main.gd nötig)
	if _url == "":
		_url = adresse()
	var cf := ConfigFile.new()
	if cf.load(CFG_DATEI) == OK:
		on = bool(cf.get_value("demo", "verbinden", true))    # der Schalter im Handy-Menü «Mehr» (ab Werk an)
	if OS.has_feature("web"):
		var q = JavaScriptBridge.eval("new URLSearchParams(location.search).get('moveeye') || ''", true)
		if typeof(q) == TYPE_STRING and str(q).to_lower() in ["aus", "off", "0", "nein", "no"]:
			on = false
		# der Rückruf läuft im Ereignis des Browsers - auch wenn der Tab gerade verschwindet und Godot danach still steht
		_vis_cb = JavaScriptBridge.create_callback(_vis_changed)
		var doc = JavaScriptBridge.get_interface("document")
		if doc != null:
			doc.addEventListener("visibilitychange", _vis_cb)


func im_hintergrund() -> bool:
	"""der Tab ist nicht sichtbar (document.visibilityState) - ausserhalb des Browsers nie"""
	if not OS.has_feature("web"):
		return false
	return str(JavaScriptBridge.eval("document.visibilityState", true)) == "hidden"


func _vis_changed(_args) -> void:
	_vis_senden()


func _vis_senden() -> void:
	"""MoveEye sagen, ob der Tab sichtbar ist (gleich beim Wechsel, ohne auf den nächsten Godot-Frame zu warten)"""
	if verbunden():
		_ws_send("VIS " + ("hidden" if im_hintergrund() else "visible"))


func adresse() -> String:
	"""wss://<Herkunft der Seite>/demo/simtun (http -> ws); ausserhalb des Browsers leer (dort gibt es net.gd)"""
	if not OS.has_feature("web"):
		return ""
	var o = JavaScriptBridge.eval("location.origin", true)
	if typeof(o) != TYPE_STRING or not (str(o).begins_with("https://") or str(o).begins_with("http://")):
		return ""
	return ("wss://" + str(o).substr(8) if str(o).begins_with("https://") else "ws://" + str(o).substr(7)) + PATH


func set_on(v: bool, merken := false) -> void:
	if merken:
		var cf := ConfigFile.new()
		cf.load(CFG_DATEI)
		cf.set_value("demo", "verbinden", v)
		cf.save(CFG_DATEI)
	on = v
	_fails = 0
	_next = 0.0
	if not v:
		_trennen("aus")
	elif status == "besetzt":
		status = "aus"


func state() -> Dictionary:
	return {"on": on, "status": status, "url": _url, "kanaele": chans.size()}


func status_text() -> String:
	"""der Zustand für die Oberfläche, übersetzt"""
	if not on:
		return T.t("Demo-MoveEye: aus")
	match status:
		"verbunden":
			return T.t("Demo-MoveEye: verbunden")
		"verbinde":
			return T.t("Demo-MoveEye: verbinde …")
		"besetzt":
			return T.t("Demo-MoveEye: ein anderes Fenster ist verbunden")
		"fehler":
			return T.t("Demo-MoveEye: nicht erreichbar")
	return T.t("Demo-MoveEye: aus")


func verbunden() -> bool:
	return ws != null and ws.get_ready_state() == WebSocketPeer.STATE_OPEN and status == "verbunden"


func senden(id: int, d: PackedByteArray) -> int:
	if ws.get_current_outbound_buffered_amount() > MAX_OUT:
		return 0
	var n := mini(d.size(), 60000)
	var p := PackedByteArray([(id >> 24) & 255, (id >> 16) & 255, (id >> 8) & 255, id & 255])
	p.append_array(d.slice(0, n))
	if ws.put_packet(p) != OK:
		return 0
	return n


func schliessen(id: int, sagen: bool) -> void:
	var k = chans.get(id)
	chans.erase(id)
	if k != null:
		k.open = false
	if sagen and verbunden():
		_ws_send("CLOSE %d" % id)


func _trennen(neu: String) -> void:
	for id in chans.keys():
		chans[id].open = false
	chans.clear()
	if ws != null and ws.get_ready_state() in [WebSocketPeer.STATE_OPEN, WebSocketPeer.STATE_CONNECTING]:
		ws.close()
	ws = null
	_hello = false
	if status == "verbunden" and main != null:
		main.stream_on = _was_stream
	status = neu


func _process(_dt: float) -> void:
	if not on or _url == "" or status == "besetzt":
		return
	var t := Time.get_ticks_msec() / 1000.0
	if ws == null:
		if t < _next:
			return
		ws = WebSocketPeer.new()
		ws.inbound_buffer_size = 1 << 20
		ws.outbound_buffer_size = 4 << 20
		if ws.connect_to_url(_url) != OK:
			_fehler(t); return
		status = "verbinde"
		return
	ws.poll()
	var rs := ws.get_ready_state()
	if rs == WebSocketPeer.STATE_CONNECTING:
		return
	if rs != WebSocketPeer.STATE_OPEN:
		var war := status == "verbunden"
		_trennen("fehler")
		_fehler(t, war)
		return
	if not _hello:
		_hello = true
		_ws_send("MWTUN2 demo " + inst)
	while ws.get_available_packet_count() > 0:
		var pkt := ws.get_packet()
		if ws.was_string_packet():
			_text(pkt.get_string_from_utf8().strip_edges(), t)
			if ws == null:
				return
		elif pkt.size() >= 4:
			var id := (pkt[0] << 24) | (pkt[1] << 16) | (pkt[2] << 8) | pkt[3]
			var k = chans.get(id)
			if k != null:
				k.inbuf.append_array(pkt.slice(4))


func _text(m: String, t: float) -> void:
	var w := m.split(" ", false)
	if w.is_empty():
		return
	match w[0]:
		"OK":
			status = "verbunden"
			_fails = 0
			if main != null:
				_was_stream = bool(main.stream_on)
				main.stream_on = true                # main.connected(): wie mit einem echten MoveEye (Bilder nur, wenn es fragt)
			print("web: mit dem Demo-MoveEye verbunden (%s)" % _url)
			_vis_senden()                            # 3.72.0: gleich sagen, ob der Tab sichtbar ist
		"NO":
			_trennen("fehler")
			_fehler(t)
		"TAKEN":
			_trennen("besetzt")                      # ein neueres Fenster hat übernommen: nicht von selbst wieder
			print("web: ein anderes Simulator-Fenster ist jetzt mit dem Demo-MoveEye verbunden")
		"OPEN":
			if w.size() >= 2 and w[1].is_valid_int() and main != null and main.net != null:
				var k := Kanal.new()
				k.wm = self
				k.id = int(w[1])
				chans[k.id] = k
				main.net.add_peer(k)
		"CLOSE":
			if w.size() >= 2 and w[1].is_valid_int():
				schliessen(int(w[1]), false)
		"PING":
			_ws_send("PONG")


func _ws_send(t: String) -> void:
	"""Protokoll-Text an MoveEye (kein Text für die Oberfläche: sim_texte.py übergeht _ws_send)"""
	if ws != null:
		ws.send_text(t)


func _fehler(t: float, war_verbunden := false) -> void:
	_fails = 0 if war_verbunden else _fails + 1
	_next = t + minf(30.0, 3.0 * pow(1.6, mini(_fails, 6)))
