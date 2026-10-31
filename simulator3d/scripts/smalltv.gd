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
## MoveEye 553 (Daniel 30.10.2026 Abend): auch GIF (me_a.gif / me_b.gif, Alarm-Animation) – wie das Fotoalbum des
## echten Geräts spielt die Kachel es ab (eigener kleiner GIF-Leser unten: Godot 4.3 kann kein GIF laden).

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
var _gifs := {}                             # "/image/name.gif" -> {"w", "h", "frames": [Image], "delays": [s]}
var _anim: Array = []                       # die Bilder des gezeigten GIF als Texturen
var _anim_d: Array = []
var _anim_i := 0
var _anim_t := 0.0


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
		_gifs = {}
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
				_gifs.erase(f)
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
			net._send(c, 200, files[img], "image/gif" if img.ends_with(".gif") else "image/jpeg")
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
						var gif := {}
						if name.to_lower().ends_with(".gif"):
							gif = gif_decode(data)
							_gifs["/image/" + name] = gif
						if not gif.is_empty() and not (gif["frames"] as Array).is_empty():
							last_w = int(gif["w"])
							last_h = int(gif["h"])
							if last_w != 240 or last_h != 240:
								bad_size += 1
						elif not name.to_lower().ends_with(".gif") and im.load_jpg_from_buffer(data) == OK:
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
	if _anim.size() > 1 and tile.visible:              # GIF abspielen wie das Fotoalbum des Geräts
		_anim_t += _dt
		if _anim_t >= float(_anim_d[_anim_i]):
			_anim_t = 0.0
			_anim_i = (_anim_i + 1) % _anim.size()
			_tex.texture = _anim[_anim_i]
	tile.visible = show and uploads + files.size() > 0 and main.ui_root != null
	if not tile.visible:
		return
	if not tile.has_meta("fenster"):                   # in a window frame (fenster.gd) the frame places it
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
		_anim = []
		_anim_d = []
		_anim_i = 0
		_anim_t = 0.0
		if theme == 3 and img != "" and files.has(img):
			if img.ends_with(".gif"):
				var g: Dictionary = _gifs.get(img, {})
				if g.is_empty():
					g = gif_decode(files[img])
					_gifs[img] = g
				for fr in g.get("frames", []):
					_anim.append(ImageTexture.create_from_image(fr))
				_anim_d = g.get("delays", [])
				if not _anim.is_empty():
					tx = _anim[0]
			else:
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
			"tile": tile != null and tile.visible, "anim_frames": _anim.size(),
			"gif_frames": (_gifs[img]["frames"] as Array).size() if _gifs.has(img) and not (_gifs[img] as Dictionary).is_empty() else 0}


var _gl = null                     # Aufräumen 2: game_live of the last 0.25 s (world_reply asks 10 × a second)
var _gl_t := -10.0


func game_live():
	"""das Spiel in wenigen Zahlen - EINE Quelle für alle Spiel-Anzeigen (Aufräumen 2): Antwort auf /state «game_live» für
	MoveEye (SmallTV 552, TV-Anzeige am HDMI 150) und der TV-Modus hier (tv.gd). Runde, Countdown / Restzeit, letzte
	Minute, Ziel, Spieler (Name, Farbe, Zustand, wie oft erwischt, Kristalle, Punkte wie am Rundenende ohne Abzeichen),
	was passiert ist, Rangliste, Aufgabe, Sieger und wer als Nächstes dran ist, die Adresse zum Mitspielen; null ohne Spiel"""
	var g = main.game
	if g == null or not g.open:
		_gl = null
		return null
	if _gl != null and main.now() - _gl_t < 0.25:
		return _gl
	var t: float = g.now()
	var ps := []
	for p in g.players:
		if p == null or str(p.get("role", "")) == "watch":
			continue
		var pt: int = max(0, 100 * int(p["items"]) - 150 * int(p["caught"]) + int(p.get("bonus", 0)))
		ps.append({"n": str(p["name"]), "k": int(p["caught"]), "i": int(p["items"]), "pt": pt, "s": str(p["state"]), "r": str(p.get("role", "")),
				"c": "#" + (g.COLORS[int(p["slot"]) % g.COLORS.size()] as Color).to_html(false)})
	var d := {"round": g.round_state, "players": ps, "lm": g.last_minute, "mw": int(g.mwg.get("catches", 0)), "goal": str(g.goal_name),
			"url": g.address(), "task": str(g.task.get("text", ""))}
	var fd := []
	for e in g.feed.slice(max(0, g.feed.size() - 4)):
		fd.push_front(str(e[1]))                     # the newest first
	d["feed"] = fd
	var bd := []
	for b in g.board_list().slice(0, 6):
		bd.append({"n": str(b.get("n", "")), "c": str(b.get("c", "#3b8cff")), "score": int(b.get("score", 0))})
	d["board"] = bd
	if g.rules != null:
		d["next"] = str(g.rules.next_txt)
	if g.round_state == "countdown":
		d["cd"] = int(ceil(g.t_start - t))
	elif g.round_state == "play":
		d["left"] = int(max(0.0, g.t_end - t))
	elif g.round_state == "end":
		var top := []
		for r in g.results.slice(0, 3):
			top.append({"n": str(r.get("n", "")), "pt": int(r.get("score", 0))})
		d["top"] = top
		if g.rules != null and not (g.rules.win as Dictionary).is_empty():
			var W: Dictionary = g.rules.win
			d["win"] = {"title": str(W.get("title", "")), "score": int(W.get("score", -1)), "hl": str((W.get("hl", {}) as Dictionary).get("text", ""))}
	_gl = d
	_gl_t = main.now()
	return d


# ---- ein kleiner GIF-Leser (Godot 4.3 lädt kein GIF): Kopf, Farbtabellen, Grafik-Steuerung (Pause, Transparenz,
# Entsorgung), Teilbilder mit Versatz, Zeilensprung, LZW. Ergebnis: alle Bilder ganz (RGBA) mit ihrer Dauer.
func gif_decode(b: PackedByteArray) -> Dictionary:
	if b.size() < 13 or b.slice(0, 3).get_string_from_ascii() != "GIF":
		return {}
	var w: int = b[6] | (b[7] << 8)
	var h: int = b[8] | (b[9] << 8)
	if w <= 0 or h <= 0 or w > 1024 or h > 1024:
		return {}
	var flags: int = b[10]
	var p := 13
	var gct := PackedByteArray()
	if flags & 0x80:
		var n: int = 3 * (1 << ((flags & 7) + 1))
		gct = b.slice(p, p + n)
		p += n
	var canvas := PackedByteArray()
	canvas.resize(w * h * 4)
	canvas.fill(0)
	var frames := []
	var delays := []
	var delay := 0.1
	var transp := -1
	var disposal := 0
	while p < b.size() and frames.size() < 64:
		var t: int = b[p]
		p += 1
		if t == 0x3B:
			break
		if t == 0x21:
			if p >= b.size():
				break
			var label: int = b[p]
			p += 1
			if label == 0xF9 and p + 4 < b.size() and b[p] >= 4:
				var pf: int = b[p + 1]
				disposal = (pf >> 2) & 7
				delay = maxf(0.02, float(b[p + 2] | (b[p + 3] << 8)) / 100.0)
				transp = b[p + 4] if pf & 1 else -1
			while p < b.size() and b[p] != 0:
				p += b[p] + 1
			p += 1
		elif t == 0x2C:
			if p + 9 > b.size():
				break
			var fx: int = b[p] | (b[p + 1] << 8)
			var fy: int = b[p + 2] | (b[p + 3] << 8)
			var fw: int = b[p + 4] | (b[p + 5] << 8)
			var fh: int = b[p + 6] | (b[p + 7] << 8)
			var lf: int = b[p + 8]
			p += 9
			var ct := gct
			if lf & 0x80:
				var n2: int = 3 * (1 << ((lf & 7) + 1))
				ct = b.slice(p, p + n2)
				p += n2
			var inter := (lf & 0x40) != 0
			if p >= b.size():
				break
			var min_code: int = b[p]
			p += 1
			var data := PackedByteArray()
			while p < b.size() and b[p] != 0:
				var n3: int = b[p]
				data.append_array(b.slice(p + 1, p + 1 + n3))
				p += n3 + 1
			p += 1
			var idx := _lzw(data, min_code, fw * fh)
			var before := canvas.duplicate() if disposal == 3 else PackedByteArray()
			var rows := PackedInt32Array()
			rows.resize(fh)
			if inter:
				var r := 0
				for st in [[0, 8], [4, 8], [2, 4], [1, 2]]:
					var y0: int = st[0]
					while y0 < fh:
						rows[r] = y0
						r += 1
						y0 += int(st[1])
			else:
				for r in range(fh):
					rows[r] = r
			var ncol: int = ct.size() / 3
			for r in range(fh):
				var y: int = fy + rows[r]
				if y >= h:
					continue
				var base: int = r * fw
				var o: int = (y * w + fx) * 4
				for cx in range(fw):
					var ci: int = idx[base + cx]
					if ci != transp and ci < ncol and fx + cx < w:
						canvas[o] = ct[ci * 3]
						canvas[o + 1] = ct[ci * 3 + 1]
						canvas[o + 2] = ct[ci * 3 + 2]
						canvas[o + 3] = 255
					o += 4
			frames.append(Image.create_from_data(w, h, false, Image.FORMAT_RGBA8, canvas))
			delays.append(delay)
			if disposal == 2:                            # Fläche wieder leer
				for yy in range(fy, mini(h, fy + fh)):
					for xx in range(fx, mini(w, fx + fw)):
						var q: int = (yy * w + xx) * 4
						canvas[q] = 0
						canvas[q + 1] = 0
						canvas[q + 2] = 0
						canvas[q + 3] = 0
			elif disposal == 3:
				canvas = before
			transp = -1
			disposal = 0
			delay = 0.1
		else:
			break
	return {"w": w, "h": h, "frames": frames, "delays": delays}


func _lzw(data: PackedByteArray, min_size: int, npix: int) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(npix)
	out.fill(0)
	if min_size < 2 or min_size > 11:
		return out
	var clear: int = 1 << min_size
	var eoi: int = clear + 1
	var size: int = min_size + 1
	var nxt: int = eoi + 1
	var prefix := PackedInt32Array()
	prefix.resize(4096)
	var suffix := PackedByteArray()
	suffix.resize(4096)
	var first := PackedByteArray()
	first.resize(4096)
	var lens := PackedInt32Array()
	lens.resize(4096)
	for i in range(clear):
		prefix[i] = -1
		suffix[i] = i
		first[i] = i
		lens[i] = 1
	var prev := -1
	var acc := 0
	var bits := 0
	var bp := 0
	var nb := data.size()
	var op := 0
	while op < npix:
		while bits < size:
			if bp >= nb:
				return out
			acc |= data[bp] << bits
			bp += 1
			bits += 8
		var code: int = acc & ((1 << size) - 1)
		acc >>= size
		bits -= size
		if code == clear:
			size = min_size + 1
			nxt = eoi + 1
			prev = -1
			continue
		if code == eoi:
			break
		var fb := 0
		if code < nxt and (code < clear or code > eoi):
			fb = first[code]
		elif code == nxt and prev >= 0:
			fb = first[prev]
		else:
			break                                         # kaputt
		if prev >= 0 and nxt < 4096:
			prefix[nxt] = prev
			suffix[nxt] = fb
			first[nxt] = first[prev]
			lens[nxt] = lens[prev] + 1
			nxt += 1
			if nxt == (1 << size) and size < 12:
				size += 1
		var L: int = lens[code]
		var pos: int = op + L - 1
		var k: int = code
		while k >= 0 and pos >= op:
			if pos < npix:
				out[pos] = suffix[k]
			k = prefix[k]
			pos -= 1
		op += L
		prev = code
	return out
