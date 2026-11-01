extends RefCounted
## Fehler-QR (Wunsch Daniel 01.11.2026): neben jeder Fehlermeldung des Simulators ein Knopf bzw. QR-Code, der das Problem löst.
## Liest den gemeinsamen Fehler-Katalog res://fehler_katalog.json (dieselbe Datei bettet MoveEye ein, Teil 639s): pro Fehler
## Kennung, Titel, Erklärung, Schritte und optional eine Aktion, in de / en / fr / it / rm (Sprache wie i18n.gd).
##   · Selbstdiagnose (diagnose.gd): unter jedem Problem mit Katalog-Eintrag «Hilfe & Beheben» -> Fenster «fehler:<ID>» (mehr.gd).
##   · Fenster: Erklärung, Schritte; verbunden mit MoveEye: QR-Code (hier gezeichnet, eigener Encoder wie qr_matrix in MoveEye
##     Teil 110) mit <MoveEye>/hilfe/fehler/<ID> – nur die Adresse, keine Passwörter/Schlüssel; ohne Verbindung die Anleitung
##     lokal, ohne QR.
##   · «Jetzt beheben» für die Aktionen des Simulators: sim_verbinden (Senden aus und wieder ein), sim_neustart (wie nach einem
##     Update: gleiche Optionen), sim_notfall (Neustart mit «--grafik lite», nur für diesen Start – Notfall-Start, main.gd).
##     MoveEye kann dasselbe über /control {"action": "fehler", "do": "fix", "aktion": …} (nur von MoveEye / diesem PC, net.gd).
## Test ohne Bild: werkzeuge/fehler_qr_test.gd (Katalog, QR-Bild -> PNG, das MoveEye-Test mit OpenCV liest).

const FILE := "res://fehler_katalog.json"
const UI = preload("res://scripts/ui_style.gd")
const I18N = preload("res://scripts/i18n.gd")
const SIM_ACTIONS := ["sim_verbinden", "sim_neustart", "sim_notfall"]

static var _kat := {}
static var _loaded := false


static func katalog() -> Dictionary:
	if not _loaded:
		_loaded = true
		var f := FileAccess.open(FILE, FileAccess.READ)
		if f != null:
			var d = JSON.parse_string(f.get_as_text())
			if typeof(d) == TYPE_DICTIONARY:
				_kat = d
	return _kat


static func entries() -> Array:
	var out := []
	for e in katalog().get("fehler", []):
		if typeof(e) == TYPE_DICTIONARY and str(e.get("id", "")) != "":
			out.append(e)
	return out


static func entry(id: String) -> Dictionary:
	for e in entries():
		if str(e["id"]) == id:
			return e
	return {}


static func lang() -> String:
	var l := str(I18N.lang())
	return l if l in ["de", "en", "fr", "it", "rm"] else "de"


static func tx(d, l := "") -> Variant:
	"""a {de, en, fr, it, rm} value in the language (rm -> de, otherwise -> en)"""
	if typeof(d) != TYPE_DICTIONARY:
		return d if d != null else ""
	if l == "":
		l = lang()
	for k in [l, "de" if l == "rm" else "en", "de"]:
		if d.has(k) and d[k] != null and str(d[k]) != "":
			return d[k]
	return ""


static func ui(key: String, l := "") -> String:
	return str(tx(katalog().get("ui", {}).get(key, {"de": key}), l))


static func act_name(a: String, l := "") -> String:
	return str(tx(katalog().get("aktionen", {}).get(a, {"de": a}), l))


static func for_diag(item: Dictionary) -> Dictionary:
	"""the catalogue entry of one line of the self-diagnosis (empty: none / ok)"""
	if not str(item.get("level", "")) in ["bad", "warn"]:
		return {}
	for e in entries():
		if not str(e.get("seite", "")) in ["sim", "beide"]:
			continue
		if str(item.get("id", "")) in (e.get("quelle", {}).get("sim_diag", []) as Array):
			return e
	return {}


static func mw_base(main) -> String:
	"""the address of MoveEye, when it is connected now (else ""): then the QR code can point there"""
	if main == null or str(main.mw_addr) == "" or main.now() - float(main.mw_t) > 10.0:
		return ""
	var hb := str(main.mw.get("help_base", ""))         # MoveEye names the address a phone can open (639s)
	if hb.begins_with("http") and hb.find("://127.") < 0 and hb.find("://localhost") < 0:
		return hb.rstrip("/")
	return "%s://%s:%d" % [str(main.mw.get("mw_scheme", "http")), str(main.mw_addr), int(main.mw.get("mw_port", 5000))]


static func url(main, id: String, base := "") -> String:
	var b := base if base != "" else mw_base(main)
	if b == "":
		return ""
	return b.rstrip("/") + str(katalog().get("pfad", "/hilfe/fehler/")) + id


# ---- the window «fehler:<ID>» (mehr.gd open_window) ---------------------------------------------------------------------------
static func build(main, body: VBoxContainer, mehr, id: String) -> void:
	var e := entry(id)
	var l := lang()
	if e.is_empty():
		body.add_child(UI.small(ui("unknown", l) + ": " + id, UI.TXT))
		return
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 8)
	body.add_child(top)
	var col: Color = UI.RED if str(e.get("stufe", "bad")) == "bad" else UI.ORG
	var dot := Control.new()
	dot.custom_minimum_size = Vector2(12, 22)
	dot.draw.connect(func(): dot.draw_circle(Vector2(6, 11), 5.0, col))
	top.add_child(dot)
	var tl := Label.new()
	tl.text = str(tx(e["titel"], l))
	tl.add_theme_font_override("font", UI.heading_font())
	tl.add_theme_font_size_override("font_size", 15)
	top.add_child(tl)
	var codel := UI.small("%s: %s" % [ui("code", l), id])
	codel.autowrap_mode = TextServer.AUTOWRAP_OFF
	top.add_child(codel)
	var t1 := UI.small(str(tx(e["text"], l)), UI.TXT)
	t1.custom_minimum_size = Vector2(520, 0)
	body.add_child(t1)
	body.add_child(UI.heading(ui("steps", l)))
	var st: Array = tx(e.get("schritte", {}), l) if typeof(tx(e.get("schritte", {}), l)) == TYPE_ARRAY else []
	for i in range(st.size()):
		var s := UI.small("%d. %s" % [i + 1, str(st[i])], UI.TXT)
		s.custom_minimum_size = Vector2(520, 0)
		body.add_child(s)
	var u := url(main, id)
	if u != "":
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 12)
		body.add_child(row)
		row.add_child(qr_view(u, 168.0))
		var ul := UI.small(ui("scan", l) + "\n" + u, UI.TXT)
		ul.custom_minimum_size = Vector2(330, 0)
		ul.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(ul)
	else:
		var off := UI.small(ui("offline", l))
		off.custom_minimum_size = Vector2(520, 0)
		body.add_child(off)
	var res := UI.small("")
	body.add_child(res)
	var bt := HBoxContainer.new()
	bt.add_theme_constant_override("separation", 8)
	bt.alignment = BoxContainer.ALIGNMENT_END
	body.add_child(bt)
	var a := str(e.get("aktion", ""))
	if a in SIM_ACTIONS:
		var fx := Button.new()
		fx.text = ui("fix_now", l) + ": " + act_name(a, l)
		UI.primary(fx)
		fx.pressed.connect(func():
			var r := fix(main, a, "Knopf")
			res.text = ("✓ " + ui("done", l) if bool(r.get("ok")) else "⚠ " + ui("failed", l)) + " – " + str(r.get("msg", "")))
		bt.add_child(fx)
	elif a != "" and u != "":
		var op := Button.new()                       # a fix of MoveEye: only there, as the owner (login, CSRF)
		op.text = ui("fix_now", l) + " (MoveEye)"
		op.tooltip_text = act_name(a, l) + " – " + u
		op.pressed.connect(func(): OS.shell_open(u))
		bt.add_child(op)
	elif a == "":
		var mn := UI.small(ui("manual", l))
		mn.custom_minimum_size = Vector2(520, 0)
		body.add_child(mn)
	if mehr != null:
		var back := Button.new()
		back.text = "← " + "Selbstdiagnose"
		back.pressed.connect(func(): mehr.open_window("diag"))
		bt.add_child(back)
		var cl := Button.new()
		cl.text = ui("close", l)
		cl.pressed.connect(func(): mehr.close_window())
		bt.add_child(cl)


# ---- the actions of the simulator ------------------------------------------------------------------------------------------
static func fix(main, a: String, who := "") -> Dictionary:
	print("Fehler-QR: beheben «%s» (%s)" % [a, who])
	if main == null:
		return {"ok": false, "msg": "not ready"}
	if a == "sim_verbinden":
		if not main.has_method("set_stream"):
			return {"ok": false, "msg": "not supported"}
		var tr_ = main.get_tree()                  # a little later: the answer to /control goes out first (same server)
		tr_.create_timer(0.4).timeout.connect(func():
			main.set_stream(false)
			tr_.create_timer(0.6).timeout.connect(func(): main.set_stream(true, true)))
		return {"ok": true, "msg": ui("busy")}
	if a in ["sim_neustart", "sim_notfall"]:
		main.get_tree().create_timer(1.0).timeout.connect(func(): restart(main, a == "sim_notfall"))
		return {"ok": true, "msg": ui("busy")}
	return {"ok": false, "msg": "unknown action"}


static func restart_user_args(main, notfall: bool) -> PackedStringArray:
	"""the options of the new start: as after an update (main.restart_args); emergency start = --grafik lite (only this start)"""
	var ua: PackedStringArray = main.restart_args() if main.has_method("restart_args") else OS.get_cmdline_user_args()
	var out := PackedStringArray()
	var i := 0
	while i < ua.size():
		if ua[i] == "--grafik":
			i += 2
			continue
		if ua[i] != "--updated":
			out.append(ua[i])
		i += 1
	if notfall:
		out.append("--grafik")
		out.append("lite")
	return out


static func restart(main, notfall: bool) -> void:
	if OS.get_environment("MWSIM_NO_RESTART") == "1":    # tests: only say what would happen
		print("Fehler-QR: Neustart ", " ".join(restart_user_args(main, notfall)))
		return
	var args := OS.get_cmdline_args()
	args.append("--")
	args.append_array(restart_user_args(main, notfall))
	if main.has_method("release_ports"):
		main.release_ports()
	var pid := OS.create_process(OS.get_executable_path(), args)
	if pid <= 0:
		print("Fehler-QR: Neustart ging nicht")
		return
	main.get_tree().quit()


static func control(main, mehr, d: Dictionary) -> Dictionary:
	"""/control {"action": "fehler", "do": info | zeige (id) | fix (aktion)}"""
	var w := str(d.get("do", "info"))
	if w == "zeige":
		var id := str(d.get("id", ""))
		if entry(id).is_empty():
			return {"ok": false, "error": "unknown id"}
		if mehr != null:
			mehr.open_window("fehler:" + id)
		return {"ok": true, "id": id, "url": url(main, id)}
	if w == "fix":
		var a := str(d.get("aktion", ""))
		if not a in SIM_ACTIONS:
			return {"ok": false, "error": "unknown action"}
		return fix(main, a, "MoveEye")
	var ids := []
	for e in entries():
		ids.append(str(e["id"]))
	return {"ok": true, "n": ids.size(), "ids": ids, "connected": mw_base(main) != ""}


# ---- QR code: own encoder (byte mode, ISO 18004), the same as qr_matrix of MoveEye (part 110) -------------------------------
const ECW := [[-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
		[-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],
		[-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
		[-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]]
const NBL := [[-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25],
		[-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49],
		[-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68],
		[-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81]]


static func _raw_modules(v: int) -> int:
	var r := (16 * v + 128) * v + 64
	if v >= 2:
		var na := v / 7 + 2
		r -= (25 * na - 10) * na - 55
		if v >= 7:
			r -= 36
	return r


static func _data_cw(e: int, v: int) -> int:
	return _raw_modules(v) / 8 - int(ECW[e][v]) * int(NBL[e][v])


static func _gmul(x: int, y: int) -> int:
	var z := 0
	for i in range(7, -1, -1):
		z = (z << 1) ^ ((z >> 7) * 0x11D)
		z ^= ((y >> i) & 1) * x
	return z & 0xFF


static func _mask(m: int, x: int, y: int) -> bool:
	match m:
		0: return (x + y) % 2 == 0
		1: return y % 2 == 0
		2: return x % 3 == 0
		3: return (x + y) % 3 == 0
		4: return (x / 3 + y / 2) % 2 == 0
		5: return x * y % 2 + x * y % 3 == 0
		6: return (x * y % 2 + x * y % 3) % 2 == 0
	return ((x + y) % 2 + x * y % 3) % 2 == 0


static func matrix(text: String, ecl := "M") -> Array:
	"""rows of bool (true = dark); [] when the text is too long"""
	var E: int = {"L": 0, "M": 1, "Q": 2, "H": 3}[ecl]
	var FMT: int = [1, 0, 3, 2][E]
	var data := text.to_utf8_buffer()
	var ver := 0
	for v in range(1, 41):
		if 4 + (8 if v < 10 else 16) + 8 * data.size() <= _data_cw(E, v) * 8:
			ver = v
			break
	if ver == 0:
		return []
	var bits := []
	var put := func(val: int, n: int):
		for i in range(n - 1, -1, -1):
			bits.append((val >> i) & 1)
	put.call(4, 4)
	put.call(data.size(), 8 if ver < 10 else 16)
	for b in data:
		put.call(b, 8)
	var cap := _data_cw(E, ver) * 8
	put.call(0, mini(4, cap - bits.size()))
	put.call(0, posmod(-bits.size(), 8))
	var pad := 0xEC
	while bits.size() < cap:
		put.call(pad, 8)
		pad ^= 0xEC ^ 0x11
	var cws := []
	for i in range(0, bits.size(), 8):
		var c := 0
		for j in range(8):
			c = (c << 1) | int(bits[i + j])
		cws.append(c)
	var nb := int(NBL[E][ver])
	var el := int(ECW[E][ver])
	var rawcw := _raw_modules(ver) / 8
	var nshort := nb - rawcw % nb
	var slen := rawcw / nb
	var div := []
	div.resize(el)
	div.fill(0)
	div[el - 1] = 1
	var root := 1
	for _k in range(el):
		for j in range(el):
			div[j] = _gmul(int(div[j]), root)
			if j + 1 < el:
				div[j] = int(div[j]) ^ int(div[j + 1])
		root = _gmul(root, 0x02)
	var blocks := []
	var k := 0
	for i in range(nb):
		var ln := slen - el + (0 if i < nshort else 1)
		var dat: Array = cws.slice(k, k + ln)
		k += dat.size()
		var rem := []
		rem.resize(el)
		rem.fill(0)
		for b in dat:
			var f: int = int(b) ^ int(rem.pop_front())
			rem.append(0)
			for j in range(el):
				rem[j] = int(rem[j]) ^ _gmul(int(div[j]), f)
		if i < nshort:
			dat.append(0)
		blocks.append(dat + rem)
	var allcw := []
	for i in range((blocks[0] as Array).size()):
		for j in range(blocks.size()):
			if i != slen - el or j >= nshort:
				allcw.append(blocks[j][i])
	var size := ver * 4 + 17
	var M := []
	var F := []
	for _y in range(size):
		var r1 := []
		r1.resize(size)
		r1.fill(false)
		M.append(r1)
		var r2 := []
		r2.resize(size)
		r2.fill(false)
		F.append(r2)
	var setf := func(x: int, y: int, dark: bool):
		M[y][x] = dark
		F[y][x] = true
	for i in range(size):
		setf.call(6, i, i % 2 == 0)
		setf.call(i, 6, i % 2 == 0)
	for c in [[3, 3], [size - 4, 3], [3, size - 4]]:
		for dy in range(-4, 5):
			for dx in range(-4, 5):
				var x: int = c[0] + dx
				var y: int = c[1] + dy
				if x >= 0 and x < size and y >= 0 and y < size:
					setf.call(x, y, not (maxi(absi(dx), absi(dy)) in [2, 4]))
	if ver > 1:
		var na := ver / 7 + 2
		var step := 26 if ver == 32 else (ver * 4 + na * 2 + 1) / (na * 2 - 2) * 2
		var pos := [6]
		var tail := []
		for i in range(na - 1):
			tail.append(size - 7 - i * step)
		tail.reverse()
		pos.append_array(tail)
		for i in range(pos.size()):
			for j in range(pos.size()):
				if (i == 0 and j == 0) or (i == 0 and j == na - 1) or (i == na - 1 and j == 0):
					continue
				for dy in range(-2, 3):
					for dx in range(-2, 3):
						setf.call(int(pos[i]) + dx, int(pos[j]) + dy, maxi(absi(dx), absi(dy)) != 1)
	var draw_format := func(mask: int):
		var d := FMT << 3 | mask
		var rm := d
		for _i in range(10):
			rm = (rm << 1) ^ ((rm >> 9) * 0x537)
		var b := (d << 10 | rm) ^ 0x5412
		for i in range(6):
			setf.call(8, i, (b >> i) & 1 == 1)
		setf.call(8, 7, (b >> 6) & 1 == 1)
		setf.call(8, 8, (b >> 7) & 1 == 1)
		setf.call(7, 8, (b >> 8) & 1 == 1)
		for i in range(9, 15):
			setf.call(14 - i, 8, (b >> i) & 1 == 1)
		for i in range(8):
			setf.call(size - 1 - i, 8, (b >> i) & 1 == 1)
		for i in range(8, 15):
			setf.call(8, size - 15 + i, (b >> i) & 1 == 1)
		setf.call(8, size - 8, true)
	draw_format.call(0)
	if ver >= 7:
		var rv := ver
		for _i in range(12):
			rv = (rv << 1) ^ ((rv >> 11) * 0x1F25)
		var bv := ver << 12 | rv
		for i in range(18):
			var bit := (bv >> i) & 1 == 1
			var aa := size - 11 + i % 3
			var cc := i / 3
			setf.call(aa, cc, bit)
			setf.call(cc, aa, bit)
	var bi := 0
	var right := size - 1
	var total := allcw.size() * 8
	while right >= 1:
		if right == 6:
			right = 5
		for vert in range(size):
			for j in range(2):
				var x := right - j
				var up := ((right + 1) & 2) == 0
				var y := size - 1 - vert if up else vert
				if not F[y][x] and bi < total:
					M[y][x] = ((int(allcw[bi >> 3]) >> (7 - (bi & 7))) & 1) == 1
					bi += 1
		right -= 2
	var apply := func(m: int):
		for y in range(size):
			for x in range(size):
				if not F[y][x] and _mask(m, x, y):
					M[y][x] = not M[y][x]
	var best := -1
	var bm := 0
	for m in range(8):
		apply.call(m)
		draw_format.call(m)
		var pen := _penalty(M, size)
		if best < 0 or pen < best:
			best = pen
			bm = m
		apply.call(m)
	apply.call(bm)
	draw_format.call(bm)
	return M


static func _penalty(M: Array, size: int) -> int:
	var p := 0
	var lines := []
	for y in range(size):
		var s := ""
		for x in range(size):
			s += "1" if M[y][x] else "0"
		lines.append(s)
	for x in range(size):
		var s := ""
		for y in range(size):
			s += "1" if M[y][x] else "0"
		lines.append(s)
	for ln in lines:
		var run := 0
		var last := ""
		for ch in (str(ln) + "x"):
			if ch == last:
				run += 1
			else:
				if run >= 5:
					p += 3 + run - 5
				run = 1
				last = ch
		p += 40 * (str(ln).count("10111010000") + str(ln).count("00001011101"))
	for y in range(size - 1):
		for x in range(size - 1):
			if M[y][x] == M[y][x + 1] and M[y][x] == M[y + 1][x] and M[y][x] == M[y + 1][x + 1]:
				p += 3
	var dark := 0
	for y in range(size):
		for x in range(size):
			if M[y][x]:
				dark += 1
	var tot := size * size
	p += ((absi(dark * 20 - tot * 10) + tot - 1) / tot - 1) * 10
	return p


static func image(text: String, scale := 6) -> Image:
	"""the QR code as a picture (white quiet zone of 4 modules) - for tests and saving"""
	var M := matrix(text)
	var n := M.size()
	var q := 4
	var w := (n + 2 * q) * scale
	var im := Image.create(maxi(w, 1), maxi(w, 1), false, Image.FORMAT_RGB8)
	im.fill(Color.WHITE)
	for y in range(n):
		for x in range(n):
			if M[y][x]:
				im.fill_rect(Rect2i((x + q) * scale, (y + q) * scale, scale, scale), Color.BLACK)
	return im


static func qr_view(text: String, px := 168.0) -> Control:
	"""a Control that draws the QR code (white field, black modules) - no picture file, no network"""
	var M := matrix(text)
	var c := Control.new()
	c.custom_minimum_size = Vector2(px, px)
	c.tooltip_text = text
	c.set_meta("qr_text", text)
	c.draw.connect(func():
		var n := M.size()
		c.draw_rect(Rect2(Vector2.ZERO, Vector2(px, px)), Color.WHITE)
		if n == 0:
			return
		var m := px / float(n + 8)
		for y in range(n):
			for x in range(n):
				if M[y][x]:
					c.draw_rect(Rect2(Vector2((x + 4) * m, (y + 4) * m), Vector2(ceilf(m), ceilf(m))), Color.BLACK))
	return c
