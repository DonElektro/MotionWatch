extends Node
## Virtueller Zusatz-Bildschirm «GeekMagic SmallTV Ultra» (Plan Daniel 30.10.2026, docs/SmallTV_Anzeige_Plan.md):
## dieselbe HTTP-Schnittstelle wie das echte Gerät (Firmware Ultra-V9.0.40) auf dem Port des Simulators –
##   POST /doUpload?dir=/image/   (multipart, Feld «file», JPEG 240×240)
##   GET  /set?theme=3 · /set?img=/image//name.jpg · /set?brt=0..100 · /set?autoplay=0
##   GET  /filelist?dir=/image/ · /delete?file=/image//name · /v.json · /app.json · /space.json
## So testet MoveEye (Teil 552) ohne Gerät genau den Weg zum echten SmallTV. Das gezeigte Bild steht als kleine Kachel
## links im Fenster (Sensoren → Zusatz-Bildschirm → «Kachel zeigen»), gedimmt wie die eingestellte Helligkeit.
## «Macken wie das echte Gerät»: Upload antwortet HTTP 400, obwohl gespeichert, und jede Antwort kommt 1,2 s später.
## Für Tests / Prüfstand: CONTROL {"action": "smalltv"} (Zähler, letztes Bild, {"reset": true}), GET /smalltv.jpg.

const FILE := "user://smalltv.json"
const TOTAL := 1048576 + 196608            # ca. 1,2 MB Flash für Bilder (das echte Gerät hat etwa 1 MB frei)
const PATHS := ["/doUpload", "/set", "/filelist", "/delete", "/v.json", "/app.json", "/space.json", "/smalltv.jpg"]

var main
var files := {}                             # "/image/name.jpg" -> PackedByteArray
var img := ""                               # gezeigtes Bild
var theme := 1                              # 3 = Fotoalbum (nach dem Einschalten zeigt das Gerät die Uhr)
var brt := 50
var autoplay := 1
var uploads := 0
var sets := 0
var bad_size := 0                           # Bilder, die nicht 240×240 sind
var last_name := ""
var last_t := 0.0
var last_w := 0
var last_h := 0
var last_from := ""
var show := true                            # Kachel zeigen (sobald MoveEye ein Bild geschickt hat)
var quirks := false                         # Macken des echten Geräts nachbilden
var big := false
var _pending: Array = []                    # verzögerte Antworten: [due, net, c, code, body, type]

var tile: PanelContainer
var _tex: TextureRect
var _title: Label
var _sub: Label
var _shown := ""


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		show = bool(d.get("show", true))
		quirks = bool(d.get("quirks", false))
		big = bool(d.get("big", false))


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"show": show, "quirks": quirks, "big": big}))
		f.close()


func add_controls() -> void:
	var sub := {"sub": "Zusatz-Bildschirm"}
	main.add_control("toggle", "smalltv_show", "Virtueller SmallTV: Kachel zeigen, sobald MoveEye Bilder schickt (gleiche Schnittstelle wie der echte GeekMagic SmallTV Ultra)",
			func(): return show, func(v): show = bool(v); save(), "Sensoren", sub)
	main.add_control("toggle", "smalltv_quirks", "Virtueller SmallTV: Macken wie das echte Gerät (Upload antwortet «400», Antworten 1,2 s später)",
			func(): return quirks, func(v): quirks = bool(v); save(), "Sensoren", {"sub": "Zusatz-Bildschirm", "expert": true})
	main.add_control("button", "smalltv_clear", "Virtueller SmallTV: Bilder löschen und Zähler zurücksetzen",
			null, func(): reset(true), "Sensoren", sub)


func reset(all := false) -> void:
	uploads = 0
	sets = 0
	bad_size = 0
	if all:
		files = {}
		img = ""
		theme = 1
		last_name = ""
		_paint()


# ---- HTTP (net.gd ruft das für die Pfade des SmallTV auf) ------------------------------------------------------------
func wants(path: String) -> bool:
	return path in PATHS


func handle(net, c: Dictionary, method: String, path: String, query: Dictionary, body: PackedByteArray, host: String) -> void:
	var code := 200
	var out := "OK"
	var ctype := "text/plain"
	match path:
		"/v.json":
			out = JSON.stringify({"m": "SmallTV-Ultra", "v": "Ultra-V9.0.40", "sim": true, "name": "MoveEye-Simulator"})
			ctype = "application/json"
		"/space.json":
			var used := 0
			for k in files:
				used += (files[k] as PackedByteArray).size()
			out = JSON.stringify({"total": TOTAL, "free": max(0, TOTAL - used)})
			ctype = "application/json"
		"/app.json":
			out = JSON.stringify({"theme": theme, "brt": brt, "img": img, "autoplay": autoplay})
			ctype = "application/json"
		"/filelist":
			var lines := []
			for k in files:
				lines.append('<a href="%s">%s</a> %d<br>' % [k, str(k).get_file(), (files[k] as PackedByteArray).size()])
			out = "<html><body>" + "\n".join(PackedStringArray(lines)) + "</body></html>"
			ctype = "text/html"
		"/delete":
			var f := _norm(str(query.get("file", "")))
			if files.has(f):
				files.erase(f)
				if img == f:
					img = ""
					_paint()
			else:
				code = 404
				out = "not found"
		"/set":
			sets += 1
			if query.has("theme"):
				theme = int(query["theme"])
			if query.has("brt"):
				brt = clampi(int(query["brt"]), 0, 100)
			if query.has("autoplay"):
				autoplay = int(query["autoplay"])
			if query.has("img"):
				var p := _norm(str(query["img"]))
				if files.has(p):
					img = p
				else:
					code = 404
					out = "no such picture"
			_paint()
		"/smalltv.jpg":                                # für Tests und Bildschirmfotos: das gezeigte Bild
			if img == "" or not files.has(img):
				net._json(c, {"ok": false, "error": "no picture"}, 404)
				return
			net._send(c, 200, files[img], "image/jpeg")
			return
		"/doUpload":
			if method != "POST":
				code = 400
				out = "POST only"
			else:
				var r := _multipart(body)
				if r.is_empty():
					code = 400
					out = "no file"
				else:
					var name := str(r["name"]).get_file()
					var used := 0
					for k in files:
						if k != "/image/" + name:
							used += (files[k] as PackedByteArray).size()
					var data: PackedByteArray = r["data"]
					if used + data.size() > TOTAL:
						code = 500
						out = "no space"
					else:
						files["/image/" + name] = data
						uploads += 1
						last_name = name
						last_t = main.now()
						last_from = host
						var im := Image.new()
						if im.load_jpg_from_buffer(data) == OK:
							last_w = im.get_width()
							last_h = im.get_height()
							if last_w != 240 or last_h != 240:
								bad_size += 1
						else:
							last_w = 0
							last_h = 0
							bad_size += 1
						if "/image/" + name == img:
							_shown = ""
							_paint()
						if quirks:
							code = 400                     # Firmware-Fehler des echten Geräts: gespeichert, trotzdem «400»
							out = "Bad Request"
	if quirks:
		_pending.append([Time.get_ticks_msec() + 1200, net, c, code, out.to_utf8_buffer(), ctype])
		return
	net._send(c, code, out.to_utf8_buffer(), ctype)


func _norm(p: String) -> String:
	while p.find("//") >= 0:
		p = p.replace("//", "/")
	return p


func _multipart(body: PackedByteArray) -> Dictionary:
	"""das Feld «file» eines multipart/form-data: {"name", "data"} oder {}"""
	var nl := _find(body, "\r\n".to_utf8_buffer(), 0)
	if nl < 3:
		return {}
	var boundary := body.slice(0, nl)                 # "--xyz"
	var he := _find(body, "\r\n\r\n".to_utf8_buffer(), nl)
	if he < 0:
		return {}
	var head := body.slice(nl + 2, he).get_string_from_utf8()
	var m := RegEx.create_from_string('filename="([^"]*)"').search(head)
	var name := m.get_string(1) if m != null else "upload.jpg"
	var endm := PackedByteArray("\r\n".to_utf8_buffer())
	endm.append_array(boundary)
	var e := _find(body, endm, he + 4)
	if e < 0:
		e = body.size()
	return {"name": name, "data": body.slice(he + 4, e)}


func _find(hay: PackedByteArray, needle: PackedByteArray, from: int) -> int:
	var n := needle.size()
	if n == 0:
		return -1
	var first := needle[0]
	var i := from
	var last := hay.size() - n
	while i <= last:
		i = hay.find(first, i)
		if i < 0 or i > last:
			return -1
		if hay.slice(i, i + n) == needle:
			return i
		i += 1
	return -1


func _process(_dt: float) -> void:
	if not _pending.is_empty():
		var now_ms := Time.get_ticks_msec()
		var keep := []
		for p in _pending:
			if now_ms >= int(p[0]):
				p[1]._send(p[2], int(p[3]), p[4], str(p[5]))
			else:
				keep.append(p)
		_pending = keep
	if tile == null:
		return
	tile.visible = show and uploads + files.size() > 0 and main.ui_root != null
	if not tile.visible:
		return
	var y := 92.0
	if main.minimap != null and main.minimap.visible:
		y = main.minimap.position.y + main.minimap.size.y + 8.0
	if main.liveview != null and main.liveview.visible:
		y = main.liveview.position.y + main.liveview.size.y + 8.0
	tile.position = Vector2(14, y)
	var age := int(main.now() - last_t) if last_t > 0.0 else -1
	_sub.text = "%d Bilder · Hell %d %%%s%s" % [uploads, brt, (" · vor %d s" % age) if age >= 0 and age < 600 else "", " · Macken" if quirks else ""]


# ---- die Kachel im Fenster -------------------------------------------------------------------------------------------
func make_tile(layer: Node) -> void:
	tile = PanelContainer.new()
	tile.mouse_filter = Control.MOUSE_FILTER_STOP
	tile.tooltip_text = "Virtueller SmallTV (GeekMagic SmallTV Ultra) · Klick: grösser / kleiner"
	tile.add_theme_stylebox_override("panel", main.UI.box(Color(0.05, 0.07, 0.09, 0.9), main.UI.LINE, 8, 4, 1))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tile.add_child(v)
	_title = Label.new()
	_title.text = "SmallTV (virtuell)"
	_title.add_theme_font_size_override("font_size", 11)
	_title.add_theme_color_override("font_color", Color(1, 1, 1, 0.85))
	_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(_title)
	var frame := PanelContainer.new()            # schwarzer Rand wie das Gehäuse des echten Geräts
	frame.add_theme_stylebox_override("panel", main.UI.box(Color(0, 0, 0, 1), Color(0.25, 0.25, 0.28), 6, 6, 2))
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(frame)
	_tex = TextureRect.new()
	_tex.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_tex.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_tex.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_tex.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(_tex)
	_sub = Label.new()
	_sub.add_theme_font_size_override("font_size", 10)
	_sub.add_theme_color_override("font_color", main.UI.MUT)
	_sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(_sub)
	tile.gui_input.connect(_tile_input)
	tile.visible = false
	layer.add_child(tile)
	_size()
	_paint()


func _size() -> void:
	if _tex != null:
		var s := 240.0 if big else 168.0
		_tex.custom_minimum_size = Vector2(s, s)
		tile.size = Vector2.ZERO
		tile.reset_size()


func _tile_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
		big = not big
		save()
		_size()
		tile.accept_event()


func _paint() -> void:
	if _tex == null:
		return
	var key := "%s|%d|%d" % [img, theme, uploads]
	if key != _shown:
		_shown = key
		var tx: Texture2D = null
		if theme == 3 and img != "" and files.has(img):
			var im := Image.new()
			if im.load_jpg_from_buffer(files[img]) == OK:
				tx = ImageTexture.create_from_image(im)
		_tex.texture = tx
		_title.text = "SmallTV (virtuell)" + ("" if theme == 3 else " · Uhr (kein Fotoalbum)")
	var b := 0.12 + 0.88 * float(brt) / 100.0       # die Helligkeit des Geräts
	_tex.modulate = Color(b, b, b, 1.0)


func control(d: Dictionary) -> Dictionary:
	"""CONTROL {"action": "smalltv"}: Zähler und letztes Bild für Tests und den Prüfstand; {"reset": true} setzt zurück"""
	if bool(d.get("reset", false)):
		reset(bool(d.get("all", false)))
	if d.has("show"):
		show = bool(d["show"])
		save()
	if d.has("quirks"):
		quirks = bool(d["quirks"])
		save()
	var used := 0
	var names := []
	for k in files:
		used += (files[k] as PackedByteArray).size()
		names.append(str(k).get_file())
	return {"ok": true, "uploads": uploads, "sets": sets, "bad_size": bad_size, "files": names, "used": used, "free": max(0, TOTAL - used),
			"img": img, "theme": theme, "brt": brt, "last": last_name, "last_w": last_w, "last_h": last_h,
			"age": snappedf(main.now() - last_t, 0.1) if last_t > 0.0 else -1, "show": show, "quirks": quirks, "from": last_from,
			"tile": tile != null and tile.visible}


func game_live():
	"""das Spiel in wenigen Zahlen für die Spiel-Anzeige von MoveEye (Antwort auf /state, «game_live»): Runde, Countdown /
	Restzeit, Punkte (wie am Rundenende gerechnet, ohne Abzeichen), wie oft erwischt; null ohne offenes Spiel"""
	var g = main.game
	if g == null or not g.open:
		return null
	var t: float = g.now()
	var ps := []
	for p in g.players:
		if p == null or str(p.get("role", "")) == "watch":
			continue
		var pt: int = max(0, 100 * int(p["items"]) - 150 * int(p["caught"]) + int(p.get("bonus", 0)))
		ps.append({"n": str(p["name"]), "k": int(p["caught"]), "i": int(p["items"]), "pt": pt, "s": str(p["state"]), "r": str(p.get("role", ""))})
	var d := {"round": g.round_state, "players": ps, "lm": g.last_minute, "mw": int(g.mwg.get("catches", 0))}
	if g.round_state == "countdown":
		d["cd"] = int(ceil(g.t_start - t))
	elif g.round_state == "play":
		d["left"] = int(max(0.0, g.t_end - t))
	elif g.round_state == "end":
		var top := []
		for r in g.results.slice(0, 3):
			top.append({"n": str(r.get("n", "")), "pt": int(r.get("score", 0))})
		d["top"] = top
	return d
