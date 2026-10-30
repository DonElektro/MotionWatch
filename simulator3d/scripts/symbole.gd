extends Node
## 3D-4.22 (Angleichen, Daniel 30.10.2026): gezeichnete Symbole statt fehlender Emoji.
## Die Schrift des Simulators (Godot: Open Sans) hat keine Emoji und keine Zeichen wie ⏻ ♪ ⚡ ⚠ - je nach PC erscheinen
## leere Kästchen oder Lücken («Auslöser , Licht»). Darum:
##   * tex(kind): ein kleines gezeichnetes Symbol (Linien und Kreise wie die Kachel-Symbole in ui_style.gd), als Textur -
##     auf Knöpfen als Button.icon, vor Schaltern / Reglern als TextureRect (main.gd _ui_control)
##   * lead(text): steht vorne ein bekanntes Emoji, kommt [Symbol, Rest des Textes] zurück
##   * clean(text): reiner Text - Emoji weg (ohne Lücke vor Satzzeichen); steht nur ein Emoji da, ein kurzes Wort
##   * als Knoten (main.gd fügt ihn ein): schaut alle 1.5 s die sichtbaren Knöpfe, Beschriftungen und Hinweise durch und
##     ersetzt, was noch Emoji enthält (auch Texte, die erst später gesetzt werden, z. B. Statuszeilen)
## Die Seiten von MoveEye (Browser) behalten ihre Emoji - es geht nur um das Fenster des Simulators.

const UI = preload("res://scripts/ui_style.gd")

# emoji -> drawn symbol
const ICON := {"🔋": "battery", "🔌": "plug", "📵": "nonet", "⏻": "power", "♪": "note", "🎵": "note", "🎯": "target", "🧪": "test",
		"⚡": "bolt", "⚠": "warn", "☀": "sun", "⛅": "sun", "❄": "snow", "🌡": "thermo", "💡": "bulb", "🤖": "robot", "🧠": "robot",
		"⚖": "scale", "🚩": "flag", "🏁": "flag", "🏆": "trophy", "🥇": "trophy", "🥈": "trophy", "🥉": "trophy", "🏅": "trophy",
		"🛡": "shield", "⭐": "star", "★": "star", "✨": "star", "🎉": "star", "📷": "camera", "📸": "camera", "🎥": "camera",
		"👁": "eye", "👀": "eye", "🙈": "eyeoff", "⏱": "clock", "⏰": "clock", "⏳": "clock", "✅": "check", "❌": "cross",
		"⚙": "gear", "🔧": "gear", "🔍": "search", "📊": "chart", "📈": "chart", "🚨": "siren", "📢": "megaphone", "🔊": "megaphone",
		"📡": "scan", "🌙": "moon", "🌑": "moon", "🔒": "lock", "🔓": "lock", "📍": "pin", "🎮": "pad", "🕹": "pad", "🏠": "house",
		"🚶": "person", "🏃": "person", "👮": "person", "🕵": "person", "🌳": "tree", "🌿": "tree", "📱": "phone", "📳": "phone",
		"⏹": "stop", "⏸": "pause", "📦": "box", "📺": "tv", "🚗": "car", "🚜": "car", "🚲": "bike"}
# what stands there when the text is ONLY the emoji (a label or a button without words)
const WORD := {"battery": "Akku", "plug": "Netz", "nonet": "kein Netz", "power": "Aus", "note": "Ton", "target": "Ziel", "test": "Test",
		"bolt": "Strom", "warn": "Achtung", "sun": "Sonne", "snow": "Kälte", "thermo": "Temp.", "bulb": "Licht", "robot": "KI",
		"scale": "Vergleich", "flag": "Ziel", "trophy": "Sieg", "shield": "Schutz", "star": "*", "camera": "Foto", "eye": "Sicht",
		"eyeoff": "versteckt", "clock": "Zeit", "check": "✓", "cross": "✗", "gear": "Einst.", "search": "Suche", "chart": "Statistik",
		"siren": "Alarm", "megaphone": "Sirene", "scan": "Scan", "moon": "Nacht", "lock": "Sperre", "pin": "Ort", "pad": "Spiel",
		"house": "Haus", "person": "Person", "tree": "Baum", "phone": "Handy", "stop": "Stopp", "pause": "Pause", "box": "Paket",
		"tv": "TV", "car": "Auto", "bike": "Velo"}
const COL := {"warn": UI.ORG, "cross": UI.RED, "siren": UI.RED, "check": UI.GRN, "nonet": UI.ORG, "power": UI.RED, "trophy": Color("#f2c14e"),
		"star": Color("#f2c14e"), "bolt": Color("#f2c14e"), "sun": Color("#f2c14e")}

static var _re: RegEx = null
static var _cache := {}


static func _rx() -> RegEx:
	if _re == null:
		_re = RegEx.create_from_string("[\\x{1F000}-\\x{1FFFF}\\x{2600}-\\x{2712}\\x{2718}-\\x{27BF}\\x{231A}-\\x{23FF}\\x{2B00}-\\x{2BFF}\\x{FE0E}\\x{FE0F}\\x{200D}]")
	return _re


static func is_emo(u: int) -> bool:
	"""a character the font of the window does not have (emoji, pictographs, ⏻ ⏱ ⚡ ♪ …); arrows, ▸ ▾ ● ✓ ✗ ✕ stay"""
	return u >= 0x1F000 or (u >= 0x2600 and u <= 0x27BF and not (u >= 0x2713 and u <= 0x2717)) or (u >= 0x231A and u <= 0x23FF) \
			or (u >= 0x2B00 and u <= 0x2BFF) or u == 0xFE0E or u == 0xFE0F or u == 0x200D


static func has_emo(t: String) -> bool:
	return t != "" and _rx().search(t) != null


static func lead(t: String) -> Array:
	"""[symbol, rest] when the text starts with a known emoji (after spaces), else ["", text]"""
	var s := t.strip_edges(true, false)
	if s == "":
		return ["", t]
	for k in ICON:
		if s.begins_with(k):
			var rest := s.substr(k.length())
			while rest.length() > 0 and (rest.unicode_at(0) == 0xFE0F or rest.unicode_at(0) == 0xFE0E):
				rest = rest.substr(1)
			return [ICON[k], rest.strip_edges()]
	return ["", t]


static func clean(t: String) -> String:
	"""the text without the characters the font lacks; no gap before a comma («Auslöser 🎯, Licht» -> «Auslöser, Licht»);
	a text that is only an emoji becomes a short word"""
	if not has_emo(t):
		return t
	var o := ""
	var first := ""
	var i := 0
	while i < t.length():
		var u := t.unicode_at(i)
		if is_emo(u):
			if first == "":
				for k in ICON:
					if t.substr(i).begins_with(k):
						first = ICON[k]
						break
			i += 1
			continue
		o += String.chr(u)
		i += 1
	for p in [[" ,", ","], [" .", "."], [" )", ")"], ["( ", "("], [" :", ":"], [" ;", ";"], [" !", "!"], [" ?", "?"], ["()", ""], ["  ", " "], ["\n ", "\n"], ["· ·", "·"]]:
		while o.contains(p[0]):
			o = o.replace(p[0], p[1])
	o = o.strip_edges()
	if o.begins_with(": ") or o.begins_with("– "):
		o = o.substr(2)
	if o == "" and first != "":
		return str(WORD.get(first, ""))
	return o


# ---- the drawn symbols (20 × 20 units, like ui_style.gd _draw_group_icon), rasterised once per size -------------------------
# primitives: ["l", x1, y1, x2, y2] line · ["a", cx, cy, r, from, to] arc (in units of PI) · ["c", cx, cy, r] dot ·
# ["r", x, y, w, h] frame · ["R", x, y, w, h] filled box · ["p", [x1, y1, x2, y2 …]] line through points
const SHAPES := {
	"battery": [["r", 2, 6, 14, 8], ["R", 16.5, 8.5, 2, 3], ["R", 4.5, 8.5, 6, 3]],
	"plug": [["l", 7, 2, 7, 6], ["l", 13, 2, 13, 6], ["p", [4, 6, 16, 6, 16, 10, 13, 14, 7, 14, 4, 10, 4, 6]], ["l", 10, 14, 10, 18]],
	"nonet": [["r", 6, 2, 8, 16], ["c", 10, 15, 1], ["l", 3, 3, 17, 17]],
	"power": [["a", 10, 11, 7, -0.3, 1.3], ["l", 10, 2, 10, 10]],
	"note": [["c", 7, 15, 2.6], ["l", 9.4, 15, 9.4, 3], ["p", [9.4, 3, 15, 5, 15, 8, 9.4, 6]]],
	"target": [["a", 10, 10, 7.5, 0, 2], ["a", 10, 10, 3.5, 0, 2], ["l", 10, 0, 10, 5], ["l", 10, 15, 10, 20], ["l", 0, 10, 5, 10], ["l", 15, 10, 20, 10]],
	"test": [["p", [7, 2, 13, 2]], ["p", [8, 2, 8, 11, 4, 17, 5, 18, 15, 18, 16, 17, 12, 11, 12, 2]], ["l", 6, 14, 14, 14]],
	"bolt": [["p", [12, 1, 4, 11, 10, 11, 8, 19, 16, 8, 10, 8, 12, 1]]],
	"warn": [["p", [10, 2, 18.5, 17, 1.5, 17, 10, 2]], ["l", 10, 7, 10, 12], ["c", 10, 14.6, 1.1]],
	"sun": [["a", 10, 10, 4, 0, 2], ["l", 10, 1, 10, 3.5], ["l", 10, 16.5, 10, 19], ["l", 1, 10, 3.5, 10], ["l", 16.5, 10, 19, 10],
			["l", 3.6, 3.6, 5.4, 5.4], ["l", 14.6, 14.6, 16.4, 16.4], ["l", 3.6, 16.4, 5.4, 14.6], ["l", 14.6, 5.4, 16.4, 3.6]],
	"snow": [["l", 10, 1, 10, 19], ["l", 2.2, 5.5, 17.8, 14.5], ["l", 2.2, 14.5, 17.8, 5.5], ["p", [8, 2.5, 10, 4.5, 12, 2.5]], ["p", [8, 17.5, 10, 15.5, 12, 17.5]]],
	"thermo": [["p", [8, 12, 8, 3, 9, 2, 11, 2, 12, 3, 12, 12]], ["a", 10, 15, 3.6, -0.3, 1.3], ["c", 10, 15, 1.8], ["l", 10, 6, 10, 14]],
	"bulb": [["a", 10, 8, 5.5, 0.8, 2.2], ["l", 7, 12, 7, 15], ["l", 13, 12, 13, 15], ["l", 7, 15, 13, 15], ["l", 8, 17.5, 12, 17.5]],
	"robot": [["r", 4, 6, 12, 10], ["c", 7.8, 10.5, 1.4], ["c", 12.2, 10.5, 1.4], ["l", 10, 2.5, 10, 6], ["c", 10, 2.2, 1.2], ["l", 8, 13.5, 12, 13.5],
			["l", 2, 9, 2, 13], ["l", 18, 9, 18, 13]],
	"scale": [["l", 10, 2, 10, 17], ["l", 6, 17, 14, 17], ["l", 3, 5, 17, 5], ["p", [3, 5, 0.8, 11, 5.2, 11, 3, 5]], ["p", [17, 5, 14.8, 11, 19.2, 11, 17, 5]]],
	"flag": [["l", 4, 2, 4, 19], ["p", [4, 3, 16, 3, 13, 7, 16, 11, 4, 11]]],
	"trophy": [["p", [6, 2, 14, 2, 14, 7, 12, 11, 8, 11, 6, 7, 6, 2]], ["a", 5, 5.5, 2.5, 0.5, 1.5], ["a", 15, 5.5, 2.5, -0.5, 0.5], ["l", 10, 11, 10, 15], ["l", 6, 16, 14, 16]],
	"shield": [["p", [10, 2, 17, 4.5, 16, 11, 10, 18, 4, 11, 3, 4.5, 10, 2]], ["p", [7, 10, 9.3, 12.3, 13.5, 7.5]]],
	"star": [["p", [10, 1.5, 12.3, 7.2, 18.5, 7.6, 13.7, 11.5, 15.3, 17.6, 10, 14.2, 4.7, 17.6, 6.3, 11.5, 1.5, 7.6, 7.7, 7.2, 10, 1.5]]],
	"camera": [["r", 2, 5, 16, 11], ["R", 6, 2.5, 6, 2.5], ["a", 10, 10.5, 3.2, 0, 2]],
	"eye": [["a", 10, 16, 10, 1.22, 1.78], ["a", 10, 4, 10, 0.22, 0.78], ["c", 10, 10, 2.6]],
	"eyeoff": [["a", 10, 16, 10, 1.22, 1.78], ["a", 10, 4, 10, 0.22, 0.78], ["c", 10, 10, 2.2], ["l", 3, 17, 17, 3]],
	"clock": [["a", 10, 10, 8, 0, 2], ["l", 10, 10, 10, 5], ["l", 10, 10, 14, 12]],
	"check": [["r", 3, 3, 14, 14], ["p", [6, 10, 9, 13, 14, 7]]],
	"cross": [["l", 4, 4, 16, 16], ["l", 16, 4, 4, 16]],
	"gear": [["a", 10, 10, 5.5, 0, 2], ["a", 10, 10, 2.2, 0, 2], ["l", 10, 1.5, 10, 4.5], ["l", 10, 15.5, 10, 18.5], ["l", 1.5, 10, 4.5, 10], ["l", 15.5, 10, 18.5, 10],
			["l", 4, 4, 6.1, 6.1], ["l", 13.9, 13.9, 16, 16], ["l", 4, 16, 6.1, 13.9], ["l", 13.9, 6.1, 16, 4]],
	"search": [["a", 8.5, 8.5, 5.5, 0, 2], ["l", 12.5, 12.5, 18, 18]],
	"chart": [["l", 2, 18, 18, 18], ["R", 3.5, 11, 3, 7], ["R", 8.5, 6, 3, 12], ["R", 13.5, 9, 3, 9]],
	"siren": [["p", [5, 16, 5, 9, 6.5, 6, 10, 4.5, 13.5, 6, 15, 9, 15, 16]], ["l", 3, 16.5, 17, 16.5], ["l", 10, 0.5, 10, 2.5], ["l", 2, 4, 3.5, 5.5], ["l", 18, 4, 16.5, 5.5]],
	"megaphone": [["p", [3, 8, 3, 12, 7, 12, 13, 16, 13, 4, 7, 8, 3, 8]], ["a", 13, 10, 4, -0.3, 0.3], ["a", 13, 10, 6.5, -0.3, 0.3]],
	"scan": [["a", 10, 10, 8, 1.0, 2.0], ["a", 10, 10, 5, 1.0, 2.0], ["c", 10, 10, 1.6], ["l", 10, 10, 15, 15]],
	"moon": [["a", 10, 10, 7.5, 0.3, 1.7], ["a", 13.5, 8, 6, 0.55, 1.45]],
	"lock": [["r", 4, 9, 12, 9], ["a", 10, 9, 4, 1, 2], ["c", 10, 13.5, 1.3]],
	"pin": [["a", 10, 7.5, 5, 0.85, 2.15], ["p", [5.4, 9.5, 10, 18, 14.6, 9.5]], ["c", 10, 7.5, 1.8]],
	"pad": [["r", 1, 5, 18, 10], ["l", 4, 10, 8, 10], ["l", 6, 8, 6, 12], ["c", 13, 9, 1.3], ["c", 16, 11.5, 1.3]],
	"house": [["p", [2, 10, 10, 2.5, 18, 10]], ["p", [4.5, 8, 4.5, 18, 15.5, 18, 15.5, 8]], ["r", 8.5, 12, 3, 6]],
	"person": [["a", 10, 5, 3, 0, 2], ["a", 10, 18, 7, 1.1, 1.9], ["l", 3.8, 14.6, 16.2, 14.6]],
	"tree": [["a", 10, 7.5, 6, 0, 2], ["l", 10, 13.5, 10, 19], ["l", 7, 19, 13, 19]],
	"phone": [["r", 5, 1, 10, 18], ["c", 10, 15.5, 1.2]],
	"stop": [["R", 5, 5, 10, 10]],
	"pause": [["R", 5, 4, 3.5, 12], ["R", 11.5, 4, 3.5, 12]],
	"box": [["r", 2, 7, 16, 11], ["p", [2, 7, 5, 2, 15, 2, 18, 7]], ["l", 7, 11, 13, 11]],
	"tv": [["r", 2, 4, 16, 11], ["l", 6, 18, 14, 18], ["l", 10, 15, 10, 18]],
	"car": [["p", [1.5, 14, 1.5, 10, 4.5, 9.5, 7, 5.5, 13, 5.5, 15.5, 9.5, 18.5, 10, 18.5, 14, 1.5, 14]], ["c", 5.5, 14.5, 2], ["c", 14.5, 14.5, 2]],
	"bike": [["a", 5, 13, 4, 0, 2], ["a", 15, 13, 4, 0, 2], ["p", [5, 13, 8.5, 7, 13, 7, 15, 13]], ["l", 8.5, 7, 10.5, 13], ["l", 7.5, 5, 10, 5]],
}


static func _seg(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var t := 0.0 if ab.length_squared() < 0.0001 else clampf((p - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
	return p.distance_to(a + ab * t)


static func _dist(p: Vector2, s: Array) -> float:
	"""distance of the point to the primitive (units of 20 × 20); negative = inside a filled one"""
	match str(s[0]):
		"l":
			return _seg(p, Vector2(s[1], s[2]), Vector2(s[3], s[4]))
		"p":
			var pts: Array = s[1]
			var d := 99.0
			for i in range(0, pts.size() - 2, 2):
				d = minf(d, _seg(p, Vector2(pts[i], pts[i + 1]), Vector2(pts[i + 2], pts[i + 3])))
			return d
		"c":
			return p.distance_to(Vector2(s[1], s[2])) - float(s[3]) - 0.6
		"R":
			var q := Vector2(absf(p.x - (s[1] + s[3] * 0.5)) - s[3] * 0.5, absf(p.y - (s[2] + s[4] * 0.5)) - s[4] * 0.5)
			return Vector2(maxf(q.x, 0.0), maxf(q.y, 0.0)).length() + minf(maxf(q.x, q.y), 0.0) - 0.6
		"r":
			var r := Rect2(s[1], s[2], s[3], s[4])
			var e := [r.position, r.position + Vector2(r.size.x, 0), r.end, r.position + Vector2(0, r.size.y)]
			var d2 := 99.0
			for i in range(4):
				d2 = minf(d2, _seg(p, e[i], e[(i + 1) % 4]))
			return d2
		"a":
			var c := Vector2(s[1], s[2])
			var v := p - c
			var ang := fposmod(atan2(v.y, v.x), TAU)
			var a0 := fposmod(float(s[4]) * PI, TAU)
			var span := (float(s[5]) - float(s[4])) * PI
			if span >= TAU - 0.001 or fposmod(ang - a0, TAU) <= span:
				return absf(v.length() - float(s[3]))
			var e0 := c + Vector2(cos(float(s[4]) * PI), sin(float(s[4]) * PI)) * float(s[3])
			var e1 := c + Vector2(cos(float(s[5]) * PI), sin(float(s[5]) * PI)) * float(s[3])
			return minf(p.distance_to(e0), p.distance_to(e1))
	return 99.0


static func tex(kind: String, px := 18, col = null) -> Texture2D:
	"""the symbol as a texture (drawn once, kept); unknown kind: null"""
	if not SHAPES.has(kind):
		return null
	var c: Color = col if col != null else COL.get(kind, UI.ACC)
	var key := "%s/%d/%s" % [kind, px, c.to_html()]
	if _cache.has(key):
		return _cache[key]
	var img := Image.create(px, px, false, Image.FORMAT_RGBA8)
	var k := 20.0 / float(px)                      # units per pixel
	var half := 0.95                                # half the line width (units)
	for y in range(px):
		for x in range(px):
			var p := Vector2((x + 0.5) * k, (y + 0.5) * k)
			var d := 99.0
			for s in SHAPES[kind]:
				d = minf(d, _dist(p, s))
			var a := clampf(0.5 - (d - half) / k, 0.0, 1.0)
			img.set_pixel(x, y, Color(c.r, c.g, c.b, a))
	var t := ImageTexture.create_from_image(img)
	_cache[key] = t
	return t


static func icon_rect(kind: String, px := 18) -> TextureRect:
	var tr := TextureRect.new()
	tr.texture = tex(kind, px)
	tr.custom_minimum_size = Vector2(px, px)
	tr.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	tr.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return tr


static func deco_button(b: Button) -> void:
	"""a known emoji in front: the drawn symbol as icon, the text without it; other emoji away"""
	if b.icon == null:
		var l := lead(b.text)
		if l[0] != "":
			b.icon = tex(l[0])
			b.text = clean(l[1])
	if has_emo(b.text):
		b.text = clean(b.text)
	if has_emo(b.tooltip_text):
		b.tooltip_text = clean(b.tooltip_text)


# ---- the sweeper (a node of main.gd) ---------------------------------------------------------------------------------
var main
var _t := 0.0
var fixed := 0                         # how many texts were changed (for the test: control «info»)


func _process(dt: float) -> void:
	_t += dt
	if _t < 1.5:
		return
	_t = 0.0
	sweep(get_tree().root)


func sweep(n: Node) -> void:
	for ch in n.get_children():
		if ch is Node3D and ch != main:
			continue                                   # the world: no buttons there
		if ch is CanvasItem and not (ch as CanvasItem).visible:
			continue
		if ch is Window and not (ch as Window).visible:
			continue
		if ch is Button:
			var b := ch as Button
			if has_emo(b.text) or has_emo(b.tooltip_text):
				deco_button(b)
				fixed += 1
			if ch is OptionButton:
				var ob := ch as OptionButton
				for i in range(ob.item_count):
					if has_emo(ob.get_item_text(i)):
						ob.set_item_text(i, clean(ob.get_item_text(i)))
						fixed += 1
		elif ch is Label:
			var l := ch as Label
			if has_emo(l.text):
				l.text = clean(l.text)
				fixed += 1
			if has_emo(l.tooltip_text):
				l.tooltip_text = clean(l.tooltip_text)
		elif ch is RichTextLabel:
			var r := ch as RichTextLabel
			if has_emo(r.text):                        # only when it was set as text (not with add_text)
				r.text = clean(r.text)
				fixed += 1
		elif ch is Control and has_emo((ch as Control).tooltip_text):
			(ch as Control).tooltip_text = clean((ch as Control).tooltip_text)
		sweep(ch)
