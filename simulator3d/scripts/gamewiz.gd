extends PanelContainer
## The game wizard (from 3D-3.41): it lives here in the simulator. Step by step: game type -> goal -> difficulty (with
## the extras) -> start (summary, rules, QR code, players). Motion Watch shows the same steps on its page and works them
## from afar (CONTROL action «gamewiz»: get, open, close, pick, set, next, back, last). The settings are the normal
## controls of the game; «Like last time» is kept in user://gamewiz_last.json.

var main
var shown := false               # open (in this window and / or on the page of Motion Watch)
var step := 0
var W := {}                      # the choice being made
var lvl := "normal"
var extras_open := false
var error := ""
var seq := 0                     # every change counts up: Motion Watch repaints only when it changed

var steps_box: HBoxContainer
var body: VBoxContainer
var back_btn: Button
var next_btn: Button
var _painted := -1
var _qr_for := ""

const LAST := "user://gamewiz_last.json"
const Pics = preload("res://scripts/wizpics.gd")
var _tex := {}
const KEYS := ["game_mode", "game_goal", "game_level", "game_lives", "game_minutes", "game_items", "game_teams", "game_rescue", "game_stones",
		"game_cones", "game_powers", "game_spectate", "game_photos", "game_hides", "game_decoy", "game_night", "game_events", "game_checkpoints",
		"game_autohandicap", "game_tasks"]
const STEPS := ["Spielart", "Ziel", "Schwierigkeit", "Start"]
const MODES := [["camera", "🎥", "Alle gegen die Kamera", "Alle schleichen zum Ziel. Der Kopf von Motion Watch dreht sich und sucht euch. Wer zu lange gesehen wird, ist erwischt."],
		["guard", "👮", "Ein Spieler ist Wächter", "Ein Spieler ist Wächter: Er dreht mit dem Handy den Kopf, schaltet das Licht ein und ruft «Erwischt!», wenn er jemanden sieht."],
		["teamguard", "🔴🔵", "Team gegen Team", "Räuber und Wächter: Rot gegen Blau. Ein Team schleicht, das andere bewacht mit dem Kopf und ruft «Erwischt!»."],
		["mw", "🛡", "Motion Watch entscheidet", "Die echte Erkennung von Motion Watch passt auf: Meldet sie eine Person, ist der erwischt, den die Kamera am besten sieht."],
		["mwhand", "🕹", "Team gegen Motion Watch", "Die Spieler schleichen mit dem Handy. Die Wächter sitzen an Motion Watch: Sie drehen die echte Kamera mit dem Joystick auf der Live-Seite und drücken «Erwischt!»."]]
const GOALS := [["reach", "🟢", "Zum Ziel schleichen", "Ziel: zum grünen Licht schleichen, ohne erwischt zu werden. Der Pfeil auf dem Handy zeigt den Weg."],
		["return", "💰", "Beute holen und zurückbringen", "Ziel: die Beute beim grünen Licht holen und zurück zum Start bringen."],
		["flag", "🚩", "Fahne erobern (zwei Teams)", "Ziel: zwei Teams. Holt die Fahne der anderen und bringt sie zur eigenen Basis. Wer mit der Fahne erwischt wird, verliert sie."]]
const LEVELS := [["easy", "🌱", "Anfänger", "Wächter leicht, unbegrenzte Leben, 8 Minuten, Sichtfeld der Kameras sichtbar."],
		["normal", "🎯", "Normal", "Wächter normal, 3 Leben, 5 Minuten."],
		["hard", "🔥", "Profis", "Wächter schwer, nur 1 Leben, 4 Minuten, kein Sichtfeld."]]
const LEVEL_SET := {"easy": {"game_level": "easy", "game_lives": "0", "game_minutes": 8, "game_cones": true},
		"normal": {"game_level": "normal", "game_lives": "3", "game_minutes": 5, "game_cones": false},
		"hard": {"game_level": "hard", "game_lives": "1", "game_minutes": 4, "game_cones": false}}
# [key, label, type, min, max, unit, extra]
const OPTIONS := [["game_minutes", "Dauer einer Runde", "range", 1, 15, " min", false], ["game_lives", "Leben", "select", 0, 0, "", false],
		["game_items", "Kristalle zum Sammeln", "range", 0, 6, "", false], ["game_teams", "Zwei Teams (Rot gegen Blau)", "toggle", 0, 0, "", false],
		["game_rescue", "Befreien (Erwischte warten in der Zelle)", "toggle", 0, 0, "", false], ["game_stones", "Steine werfen zum Ablenken", "toggle", 0, 0, "", false],
		["game_cones", "Sichtfeld der Kameras zeigen", "toggle", 0, 0, "", false], ["game_powers", "Power-ups: Tarnkappe (lila) und Turbo (gelb)", "toggle", 0, 0, "", false],
		["game_spectate", "Zuschauer-Kamera: fliegt selbst übers Spielfeld", "toggle", 0, 0, "", false],
		["game_photos", "📸 Erwischt-Fotos (Galerie am Schluss)", "toggle", 0, 0, "", true], ["game_hides", "🌳 Verstecke (Büsche, 8 s unsichtbar)", "range", 0, 6, "", true],
		["game_decoy", "🦆 Lockvogel erlaubt", "toggle", 0, 0, "", true], ["game_night", "🌙 Nacht-Runde mit Taschenlampen", "toggle", 0, 0, "", true],
		["game_events", "⛈ Zufallsereignisse (Gewitter, Hund, Auto)", "toggle", 0, 0, "", true], ["game_checkpoints", "🚩 Checkpoints (+150 Punkte je)", "range", 0, 3, "", true],
		["game_autohandicap", "🎯 Handicap für den Ersten der Rangliste", "toggle", 0, 0, "", true], ["game_tasks", "✅ Eine Aufgabe für jede Runde (Bonus)", "toggle", 0, 0, "", true]]
const LIVES := [["0", "unbegrenzt"], ["3", "3 Leben"], ["1", "1 Leben"]]
const RULES := {"tips": "Tipps: Ducken und Kriechen hilft. Im Dunkeln und hinter Dingen sieht euch die Kamera schlechter. Rennen hört das Mikrofon.",
		"rescue": "Befreien: Wer erwischt wird, wartet in der Zelle, bis ihn ein Teamkollege befreit.",
		"items": "Kristalle: Wer welche einsammelt, bekommt Extrapunkte.",
		"powers": "Power-ups: Die lila Kugel ist eine Tarnkappe (9 s fast unsichtbar), die gelbe ein Turbo (7 s schneller, aber lauter).",
		"lastmin": "Letzte Minute: Die Kamera passt dann besser auf – jetzt wird es spannend!",
		"photos": "📸 Erwischt-Fotos: Wer erwischt wird, sieht auf dem Handy das Bild der Kamera. Am Schluss gibt es eine Galerie.",
		"hides": "🌳 Verstecke: In einem Busch geduckt oder kriechend sieht dich die Kamera nicht – aber nur 8 Sekunden lang.",
		"decoy": "🦆 Lockvogel: Wer will, wählt auf dem Handy «Lockvogel». Er lässt sich absichtlich sehen, lockt die Kamera weg und holt Teampunkte.",
		"night": "🌙 Nacht-Runde: Es ist dunkel. Mit 🔦 siehst du mehr – aber die Kamera sieht dich auch.",
		"events": "⛈ Zufallsereignisse: Gewitter (man hört dich kaum), ein bellender Hund, ein Auto mit Scheinwerfern.",
		"cps": "🚩 Checkpoints: Leuchtende Ringe unterwegs geben je 150 Punkte.",
		"tasks": "🎯 Jede Runde hat eine Aufgabe, z. B. «nur kriechend ins Ziel» oder «nie über 50 % Verdacht». Wer sie schafft, bekommt Bonuspunkte.",
		"hc": "🎯 Handicap: Wer in der Rangliste vorne liegt, wird leichter gesehen und ist etwas langsamer."}


# ---- the model (the same for this window and for Motion Watch) ------------------------------------------------------
func _cur() -> Dictionary:
	var o := {}
	for c in main.controls:
		if c.id in KEYS and c["get"] != null:
			o[c.id] = c["get"].call()
	return o


func _last():
	if not FileAccess.file_exists(LAST):
		return null
	var d = JSON.parse_string(FileAccess.get_file_as_string(LAST))
	return d if typeof(d) == TYPE_DICTIONARY else null


func open_wiz() -> void:
	W = _cur()
	W["game_lives"] = str(W.get("game_lives", "3"))
	lvl = str(W.get("game_level", "normal"))
	step = 0
	error = ""
	shown = true
	visible = true
	get_parent().move_child(self, -1)
	_changed()


func close_wiz() -> void:
	shown = false
	visible = false
	_changed()


func _changed() -> void:
	seq += 1
	_painted = -1


func _summary(c: Dictionary) -> String:
	var md := ""
	var gl := ""
	for m in MODES:
		if m[0] == str(c.get("game_mode", "")):
			md = m[2]
	for g in GOALS:
		if g[0] == str(c.get("game_goal", "")):
			gl = g[2]
	return "%s · %s · %d min" % [md, gl, int(c.get("game_minutes", 5))]


func _rules() -> Array:
	var out := []
	for m in MODES:
		if m[0] == str(W.get("game_mode")):
			out.append(m[3])
	for g in GOALS:
		if g[0] == str(W.get("game_goal")):
			out.append(g[3])
	out.append(RULES["tips"])
	for pair in [["game_rescue", "rescue"], ["game_items", "items"], ["game_powers", "powers"], ["game_powers", "lastmin"], ["game_photos", "photos"],
			["game_hides", "hides"], ["game_night", "night"], ["game_events", "events"], ["game_checkpoints", "cps"], ["game_tasks", "tasks"], ["game_autohandicap", "hc"]]:
		var v = W.get(pair[0], false)
		if (typeof(v) == TYPE_BOOL and v) or (typeof(v) != TYPE_BOOL and float(v) > 0.0):
			out.append(RULES[pair[1]])
	if W.get("game_decoy", false) and str(W.get("game_mode")) in ["camera", "mw"]:
		out.append(RULES["decoy"])
	return out


func model() -> Dictionary:
	var g = main.game
	var cards := []
	var key := ""
	var title := ""
	var lead := ""
	var src := []
	match step:
		0:
			title = "Welches Spiel?"
			lead = "Bis zu 4 Spieler machen mit dem Handy mit. Wähle die Spielart – der Assistent erklärt die Regeln und stellt alles ein."
			key = "game_mode"
			src = MODES
		1:
			title = "Was ist das Ziel?"
			key = "game_goal"
			src = GOALS
		2:
			title = "Wie schwierig?"
			key = "_lvl"
			src = LEVELS
		3:
			title = "Bereit!"
	for c in src:
		var on: bool = (lvl == c[0]) if key == "_lvl" else str(W.get(key, "")) == c[0]
		cards.append({"v": c[0], "icon": c[1], "title": c[2], "text": c[3], "on": on, "pic": Pics.PICS.get(c[0], "")})
	var opts := []
	if step == 2:
		for o in OPTIONS:
			if not W.has(o[0]):
				continue
			var d := {"id": o[0], "label": o[1], "type": o[2], "value": W[o[0]], "extra": o[6]}
			if o[2] == "range":
				d["min"] = o[3]
				d["max"] = o[4]
				d["unit"] = o[5]
			elif o[2] == "select":
				d["options"] = LIVES
			opts.append(d)
	var summary := []
	if step == 3:
		var md := ""
		var gl := ""
		for m in MODES:
			if m[0] == str(W.get("game_mode")):
				md = m[1] + " " + m[2]
		for x in GOALS:
			if x[0] == str(W.get("game_goal")):
				gl = x[1] + " " + x[2]
		summary = [["Spielart", md], ["Ziel", gl], ["Dauer einer Runde", "%d min" % int(W.get("game_minutes", 5))],
				["Leben", "unbegrenzt" if str(W.get("game_lives")) == "0" else str(W.get("game_lives"))], ["Kristalle", str(int(W.get("game_items", 0)))],
				["Teams", "Rot gegen Blau" if W.get("game_teams", false) else "nein"]]
	var last = _last()
	var nl := "Weiter ›"
	if step == 3:
		nl = "▶ Runde starten" if g.open else "✓ Spiel öffnen & QR-Code zeigen"
	return {"ok": true, "shown": shown, "seq": seq, "step": step, "steps": STEPS, "title": title, "lead": lead, "key": key, "cards": cards,
			"options": opts, "extras_open": extras_open, "summary": summary,
			"pics": [Pics.PICS.get(str(W.get("game_mode")), ""), Pics.PICS.get(str(W.get("game_goal")), "")] if step == 3 else [], "rules": _rules() if step == 3 else [],
			"last": _summary(last) if last != null and step == 0 else "", "error": error, "next": nl, "back": step > 0,
			"game": {"open": g.open, "url": g.address() if g.open else "", "players": g.count(), "round": g.round_state}}


func op(d: Dictionary) -> Dictionary:
	"""Motion Watch (or this window) works the wizard"""
	var o := str(d.get("op", "get"))
	match o:
		"open":
			open_wiz()
		"close":
			close_wiz()
		"pick":
			_pick(str(d.get("key", "")), str(d.get("value", "")))
		"set":
			var k := str(d.get("key", ""))
			if W.has(k):
				var v = d.get("value")
				if typeof(W[k]) == TYPE_BOOL:
					v = bool(v)
				elif typeof(W[k]) in [TYPE_INT, TYPE_FLOAT]:
					v = float(v) if typeof(W[k]) == TYPE_FLOAT else int(float(v))
				else:
					v = str(v)
				W[k] = v
				_changed()
		"extras":
			extras_open = bool(d.get("value", not extras_open))
			_changed()
		"next":
			_next()
		"back":
			step = max(0, step - 1)
			_changed()
		"last":
			var l = _last()
			if l != null:
				for k in l:
					if W.has(k) or k == "_lvl":
						W[k] = l[k]
				lvl = str(l.get("_lvl", lvl))
				step = 3
				_changed()
	return model()


func _pick(key: String, v: String) -> void:
	if key == "_lvl":
		lvl = v
		for k in LEVEL_SET.get(v, {}):
			if W.has(k):
				W[k] = LEVEL_SET[v][k]
	elif W.has(key):
		W[key] = v
		if key == "game_mode" and v == "teamguard":
			W["game_teams"] = true
		if key == "game_goal" and v == "flag":
			W["game_teams"] = true
	_changed()


func _next() -> void:
	if step < 3:
		step += 1
		error = ""
		_changed()
		return
	var g = main.game
	if g.open:                                         # the game is open: start the round
		g.start_round()
		close_wiz()
		return
	var save := W.duplicate()
	save["_lvl"] = lvl
	var f := FileAccess.open(LAST, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(save))
	var errs := []
	for k in KEYS:
		if W.has(k):
			var r: Dictionary = main.control_set(k, W[k])
			if not r.get("ok", false):
				errs.append(k)
	g.set_open(true)
	if not g.open:
		errs.append("Spiel öffnen")
	error = ("⚠ Nicht übernommen: " + ", ".join(PackedStringArray(errs))) if not errs.is_empty() else ""
	_changed()


# ---- in this window ---------------------------------------------------------------------------------------------------
func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	offset_left = 60
	offset_top = 40
	offset_right = -440
	offset_bottom = -40
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.07, 0.08, 0.1, 0.97)
	sb.set_corner_radius_all(14)
	sb.set_content_margin_all(14)
	sb.border_color = Color(0.2, 0.27, 0.35)
	sb.set_border_width_all(1)
	add_theme_stylebox_override("panel", sb)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	add_child(v)
	var top := HBoxContainer.new()
	v.add_child(top)
	var t := Label.new()
	t.text = "Spiel-Assistent"
	t.add_theme_font_size_override("font_size", 17)
	top.add_child(t)
	steps_box = HBoxContainer.new()
	steps_box.add_theme_constant_override("separation", 6)
	steps_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	steps_box.alignment = BoxContainer.ALIGNMENT_CENTER
	top.add_child(steps_box)
	var x := Button.new()
	x.text = "×"
	x.tooltip_text = "Schliessen (Esc)"
	x.pressed.connect(close_wiz)
	top.add_child(x)
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(sc)
	body = VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 8)
	sc.add_child(body)
	var nav := HBoxContainer.new()
	v.add_child(nav)
	back_btn = Button.new()
	back_btn.text = "‹ Zurück"
	back_btn.pressed.connect(func(): op({"op": "back"}))
	nav.add_child(back_btn)
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	nav.add_child(sp)
	next_btn = Button.new()
	next_btn.pressed.connect(func(): op({"op": "next"}))
	if main.UI.has_method("primary"):
		main.UI.primary(next_btn)
	nav.add_child(next_btn)
	visible = false


func _unhandled_key_input(ev: InputEvent) -> void:
	if visible and ev is InputEventKey and ev.pressed and ev.keycode == KEY_ESCAPE:
		close_wiz()
		get_viewport().set_input_as_handled()


func _process(_dt: float) -> void:
	if visible != shown:
		visible = shown
	if not visible:
		return
	var g = main.game
	var sig: int = seq * 100 + (1 if g.open else 0) * 10 + mini(9, g.count())
	if sig != _painted:
		_painted = sig
		_paint()


static func plain(t: String) -> String:
	"""without emoji (the font of the window does not have them on every PC); Motion Watch shows them"""
	var o := ""
	for i in range(t.length()):
		var c := t.unicode_at(i)
		if c >= 0x2600 and c != 0x2715 or c == 0xFE0F or c == 0x200D:
			continue
		o += String.chr(c)
	return o.strip_edges()


func _lab(t: String, sz := 14, col := Color(0.85, 0.88, 0.92), wrap := true) -> Label:
	var l := Label.new()
	l.text = plain(t)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART if wrap else TextServer.AUTOWRAP_OFF
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", col)
	return l


func _paint() -> void:
	var M := model()
	for c in steps_box.get_children():
		c.queue_free()
	for i in range(STEPS.size()):
		var s := _lab("%d %s" % [i + 1, STEPS[i]], 12, Color(1, 1, 1) if i == step else (Color(0.85, 0.88, 0.92) if i < step else Color(0.55, 0.6, 0.68)), false)
		var pc := PanelContainer.new()
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.23, 0.55, 1.0) if i == step else Color(0, 0, 0, 0)
		sb.border_color = Color(0.23, 0.55, 1.0) if i == step else Color(0.2, 0.27, 0.35)
		sb.set_border_width_all(1)
		sb.set_corner_radius_all(10)
		sb.content_margin_left = 8
		sb.content_margin_right = 8
		pc.add_theme_stylebox_override("panel", sb)
		pc.add_child(s)
		steps_box.add_child(pc)
	for c in body.get_children():
		c.queue_free()
	if error != "":
		body.add_child(_lab(error, 13, Color(1.0, 0.55, 0.45)))
	body.add_child(_lab(M["title"], 20, Color(1, 1, 1)))
	if M["lead"] != "":
		body.add_child(_lab(M["lead"], 13, Color(0.6, 0.66, 0.74)))
	if not M["cards"].is_empty():
		var grid := GridContainer.new()
		grid.columns = 3 if M["cards"].size() >= 3 else 2
		grid.add_theme_constant_override("h_separation", 8)
		grid.add_theme_constant_override("v_separation", 8)
		body.add_child(grid)
		for c in M["cards"]:
			var b := Button.new()
			b.toggle_mode = true
			b.button_pressed = c["on"]
			b.custom_minimum_size = Vector2(190, 230)
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			b.text = plain("%s\n%s" % [c["title"], c["text"]])
			b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
			b.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
			b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
			b.expand_icon = false
			b.add_theme_font_size_override("font_size", 13)
			if not _tex.has(c["v"]):
				_tex[c["v"]] = Pics.texture(c["v"], 0.8)
			if _tex[c["v"]] != null:
				b.icon = _tex[c["v"]]
			var k: String = M["key"]
			var vv: String = c["v"]
			b.pressed.connect(func(): op({"op": "pick", "key": k, "value": vv}))
			grid.add_child(b)
	if M["last"] != "":
		var lb := Button.new()
		lb.text = "Wie letztes Mal: " + M["last"]
		lb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		lb.pressed.connect(func(): op({"op": "last"}))
		body.add_child(lb)
	var ex_box: VBoxContainer = null
	for o in M["options"]:
		var parent: Control = body
		if o["extra"]:
			if ex_box == null:
				var eb := Button.new()
				eb.text = ("▾ " if extras_open else "▸ ") + "Extras – Fotos, Verstecke, Lockvogel, Nacht, Ereignisse, Checkpoints, Handicap"
				eb.flat = true
				eb.alignment = HORIZONTAL_ALIGNMENT_LEFT
				eb.pressed.connect(func(): op({"op": "extras", "value": not extras_open}))
				body.add_child(eb)
				ex_box = VBoxContainer.new()
				ex_box.visible = extras_open
				body.add_child(ex_box)
			parent = ex_box
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		parent.add_child(row)
		var l := _lab(o["label"], 14)
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(l)
		var id: String = o["id"]
		match o["type"]:
			"range":
				var s := HSlider.new()
				s.min_value = o["min"]
				s.max_value = o["max"]
				s.step = 1
				s.value = float(o["value"])
				s.custom_minimum_size = Vector2(160, 0)
				var vl := _lab("%d%s" % [int(o["value"]), o["unit"]], 14, Color(1, 1, 1))
				vl.custom_minimum_size = Vector2(54, 0)
				var unit: String = o["unit"]
				s.value_changed.connect(func(x): vl.text = "%d%s" % [int(x), unit]; W[id] = int(x) if typeof(W[id]) == TYPE_INT else float(x); seq += 1)
				row.add_child(s)
				row.add_child(vl)
			"toggle":
				var cb := CheckButton.new()
				cb.button_pressed = bool(o["value"])
				cb.toggled.connect(func(x): W[id] = x; seq += 1)
				row.add_child(cb)
			"select":
				var ob := OptionButton.new()
				for i in range(LIVES.size()):
					ob.add_item(LIVES[i][1])
					if LIVES[i][0] == str(o["value"]):
						ob.select(i)
				ob.item_selected.connect(func(i): W[id] = LIVES[i][0]; seq += 1)
				row.add_child(ob)
		if id in ["game_minutes", "game_items", "game_hides", "game_checkpoints"] or o["type"] != "range":
			pass
	if step == 3:                                      # the pictures of the chosen game and goal
		var pr := HBoxContainer.new()
		pr.add_theme_constant_override("separation", 10)
		body.add_child(pr)
		for k2 in [str(W.get("game_mode")), str(W.get("game_goal"))]:
			if not _tex.has(k2):
				_tex[k2] = Pics.texture(k2, 0.8)
			if _tex[k2] != null:
				var tr := TextureRect.new()
				tr.texture = _tex[k2]
				pr.add_child(tr)
	if not M["summary"].is_empty():
		var gs := GridContainer.new()
		gs.columns = 2
		gs.add_theme_constant_override("h_separation", 16)
		body.add_child(gs)
		for p in M["summary"]:
			gs.add_child(_lab(p[0], 14, Color(0.6, 0.66, 0.74), false))
			gs.add_child(_lab(p[1], 14, Color(1, 1, 1), false))
		for r in M["rules"]:
			body.add_child(_lab("• " + r, 13))
		var G: Dictionary = M["game"]
		if G["open"]:
			var row2 := HBoxContainer.new()
			row2.add_theme_constant_override("separation", 14)
			body.add_child(row2)
			var qr := TextureRect.new()
			qr.custom_minimum_size = Vector2(180, 180)
			qr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			qr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
			qr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			qr.texture = main.game.Qr.texture(G["url"], 4)
			row2.add_child(qr)
			var tx := _lab("Die Spieler scannen den QR-Code mit dem Handy (gleiches WLAN) oder öffnen:\n%s\n\nSpieler: %d / 4" % [G["url"], G["players"]], 14)
			tx.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			row2.add_child(tx)
	back_btn.visible = M["back"]
	next_btn.text = plain(M["next"])
