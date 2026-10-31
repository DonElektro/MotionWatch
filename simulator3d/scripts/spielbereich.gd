extends Node
## Spielbereich (Daniel 31.10.2026, Paket «Spielbereich»): ein eigener Startbildschirm «Spielen» – wie der Reiter «Spielen»
## von MoveEye (Teil 639i, gleicher Aufbau):
##   * Blinki oben als Begleiter: begrüsst beim ersten Mal, gibt einen Tipp (das Nächste, das jetzt zu finden ist), freut sich
##     über eine neue Stufe oder ein geschafftes Abenteuer. Keine Musik, keine besonderen Animationen (nur Blinkis Blinzeln).
##   * Abenteuer = die Szenen als Kapitel, eins nach dem anderen: Camping-Platz → Ferienpark → Bergtal → Zuhause. Ein Kapitel
##     ist offen, wenn das vorherige zur Hälfte entdeckt ist (oder man schon dort war); «Neu» = offen, noch nie besucht.
##     Fortschritt pro Kapitel: «12 von 34 entdeckt» aus main.entdecken (zählt, was dort schon angemeldet wurde).
##   * Abzeichen-Sammlung: die Spiel-Abzeichen (game.gd BADGES, alle Namen dieses PCs zusammen) und je ein Kapitel-Abzeichen.
##   * Stufe des Spielers (pro Gerät, user://spiel/spielbereich.json): steigt mit Entdeckungen, Abzeichen, geschafften
##     Abenteuern. Keine Rangliste.
##   * Knöpfe: «Abenteuer starten» (Szene wechseln – Haken adventure_hooks[id] für das spätere Bergtal-Abenteuer),
##     «Spiel-Assistent» (gamewiz.gd), «Entdeckungsbuch» (entdecken.gd).
## /control {"action": "spielbereich", "do": "info" | "open" | "close" | "start" (id) | "seen" | "reset"} – MoveEye zeigt info().

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Tour = preload("res://scripts/tour.gd")

const SAVE := "user://spiel/spielbereich.json"
# [scene id, chapter name, short text, chapter badge symbol, chapter badge name]
const CHAPTERS := [["camping", "Camping-Platz", "Der erste Abend: Zelt, Feuerstelle und neugierige Tiere.", "⛺", "Camper"],
		["ferienpark", "Ferienpark", "Ein grosser Platz am See – viele Leute, viel zu entdecken.", "🏖", "Feriengast"],
		["bergtal", "Bergtal", "Alp, See und Pass – einsam und wild.", "⛰", "Bergfuchs"],
		["daheim", "Zuhause", "Haus, Garten und Baustelle – zu Hause aufpassen.", "🏠", "Heimwächter"]]
# experience points of the level (own curve, gentler than gamexp.gd: 2 = 100, 3 = 300, 4 = 600, 5 = 1000 …)
const XP_DISC := 10                        # per discovery
const XP_BADGE := 25                       # per different badge (game or chapter)
const XP_DONE := 100                       # per finished adventure
const XP_VISIT := 20                       # per adventure started
const MAX_LV := 30

var main
var adventure_hooks := {}                  # id -> Callable: «Abenteuer starten» of a chapter (later: bergtal.gd); none = set_scene
var data := {"visited": [], "seen_lv": 1, "greeted": false, "done_seen": []}
var save_path := SAVE                      # Entwicklertool 3 (devtool_kapitel.gd): the test state goes to its own file (only until restart)
var _body: VBoxContainer = null
var _t := 0.0


static func need(lv: int) -> int:
	return 50 * (lv - 1) * lv


static func level_of(xp: int) -> int:
	var lv := 1
	while lv < MAX_LV and xp >= need(lv + 1):
		lv += 1
	return lv


func _ready() -> void:
	_load()


func _load() -> void:
	if not FileAccess.file_exists(save_path):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(save_path))
	if typeof(d) == TYPE_DICTIONARY:
		for k in data:
			if d.has(k) and typeof(d[k]) == typeof(data[k]):
				data[k] = d[k]
		data["seen_lv"] = int(d.get("seen_lv", 1))


func save() -> void:
	DirAccess.make_dir_recursive_absolute(save_path.get_base_dir())
	var f := FileAccess.open(save_path, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(data))
		f.close()


func _process(dt: float) -> void:
	_t -= dt
	if _t > 0.0 or main == null:
		return
	_t = 1.0
	var sc: String = main.scene
	if _chapter_of(sc) >= 0 and not (sc in data["visited"]):        # a chapter counts as started when its scene ran once
		data["visited"].append(sc)
		save()


# ---- the state -----------------------------------------------------------------------------------------------------------
func _chapter_of(id: String) -> int:
	for i in range(CHAPTERS.size()):
		if CHAPTERS[i][0] == id:
			return i
	return -1


func _exists(id: String) -> bool:
	for s in main.Scenes.LIST:
		if s[0] == id:
			return true
	return false


func tile_text() -> String:
	"""the small line of the quick tile «Spielen»"""
	return T.t("Stufe %d", [int(level().lv)])


var _gb_cache := {}
var _gb_t := -100.0


func _game_badges() -> Dictionary:
	"""badge -> how often, all (human) names of this PC together (the file is read at most every 5 s)"""
	if main.game == null:
		return {}
	if main.now() - _gb_t < 5.0:
		return _gb_cache
	_gb_t = main.now()
	var out := {}
	_gb_cache = out
	var all: Dictionary = main.game.badges_all()
	for nm in all:
		if str(nm).begins_with("bot ") or typeof(all[nm]) != TYPE_DICTIONARY:
			continue
		for b in all[nm]:
			out[b] = int(out.get(b, 0)) + int(all[nm][b])
	return out


func chapters() -> Array:
	"""[{id, n, name, short, found, total, visited, exists, state, current, badge}] - state: locked | new | open | done | soon"""
	var out := []
	var prev_ok := true
	for i in range(CHAPTERS.size()):
		var c: Array = CHAPTERS[i]
		var id: String = c[0]
		var ex := _exists(id)
		var f: int = main.entdecken.count(id) if main.entdecken != null else 0
		var n: int = main.entdecken.total(id) if main.entdecken != null else 0
		var vis: bool = id in data["visited"] or n > 0
		var done: bool = vis and (f >= n if n > 0 else true) and n > 0
		var st := "locked"
		if not ex:
			st = "soon"
		elif done:
			st = "done"
		elif prev_ok or vis:
			st = "open" if vis else "new"
		out.append({"id": id, "n": i + 1, "name": T.t(c[1]), "short": T.t(c[2]), "found": f, "total": n, "visited": vis, "exists": ex,
				"state": st, "current": main.scene == id, "badge": c[3], "badge_name": T.t(c[4])})
		# the next chapter opens when this one is half discovered (or has nothing to discover and was visited);
		# a chapter that is not there yet (Bergtal before its release) does not block the ones after it
		prev_ok = (not ex and prev_ok) or done or (vis and (n == 0 or f * 2 >= n))
	return out


func badges() -> Array:
	"""[{id, sym, name, n, kind}] - the game badges (game.gd) and one per adventure"""
	var out := []
	var gb := _game_badges()
	if main.game != null:
		for b in main.game.BADGES:
			out.append({"id": b, "sym": str(main.game.BADGES[b][0]), "name": T.t(str(main.game.BADGES[b][1])), "n": int(gb.get(b, 0)), "kind": "game"})
	for c in chapters():
		out.append({"id": "ch_" + str(c.id), "sym": c.badge, "name": c.badge_name, "n": 1 if c.state == "done" else 0, "kind": "chapter"})
	return out


func level() -> Dictionary:
	var ch := chapters()
	var disc := 0
	var done := 0
	var vis := 0
	for c in ch:
		disc += int(c.found)
		done += 1 if c.state == "done" else 0
		vis += 1 if c.visited else 0
	var nb := 0
	for b in badges():
		nb += 1 if int(b.n) > 0 else 0
	var xp := disc * XP_DISC + nb * XP_BADGE + done * XP_DONE + vis * XP_VISIT
	var lv := level_of(xp)
	return {"lv": lv, "xp": xp, "from": need(lv), "to": need(lv + 1), "disc": disc, "badges": nb, "done": done,
			"parts": [["Entdeckungen", disc * XP_DISC], ["Abzeichen", nb * XP_BADGE], ["Abenteuer geschafft", done * XP_DONE], ["Abenteuer begonnen", vis * XP_VISIT]]}


func blinki(mark := false) -> Dictionary:
	"""what Blinki says now: {mood: normal | point | happy, title, text}. mark = remember it (the screen was shown)"""
	var lv := level()
	var ch := chapters()
	var r := {}
	var fresh_done := ""
	for c in ch:
		if c.state == "done" and not (c.id in data["done_seen"]):
			fresh_done = c.name
			if mark:
				data["done_seen"].append(c.id)
	if int(lv.lv) > int(data["seen_lv"]):
		r = {"mood": "happy", "title": T.t("Juhu, Stufe %d!", [int(lv.lv)]), "text": T.t("Du hast %d Erfahrungspunkte gesammelt. Weiter so!", [int(lv.xp)])}
	elif fresh_done != "":
		r = {"mood": "happy", "title": T.t("Geschafft: %s!", [fresh_done]), "text": T.t("Alles entdeckt – das nächste Abenteuer wartet schon.")}
	elif not bool(data["greeted"]):
		r = {"mood": "normal", "title": T.t("Hallo, ich bin Blinki!"),
				"text": T.t("Hier spielst du die Abenteuer der Reihe nach. Entdecke alles, sammle Abzeichen – so steigt deine Stufe.")}
	else:
		r = {"mood": "point", "title": T.t("Schön, bist du wieder da!"), "text": _tip(ch)}
	if mark:
		data["seen_lv"] = maxi(int(data["seen_lv"]), int(lv.lv))
		data["greeted"] = true
		save()
	return r


func _tip(ch: Array) -> String:
	for c in ch:
		if c.current and c.state != "done":
			var id: String = main.entdecken.nearest_possible() if main.entdecken != null else ""
			if id != "":
				return main.entdecken.hint_text(id)
			if int(c.total) > int(c.found):
				return T.t("Im %s fehlt noch %d – manches gibt es nur nachts, bei Regen oder am Morgen.", [c.name, int(c.total) - int(c.found)])
	for c in ch:
		if c.state == "new":
			return T.t("Neu: «%s» wartet auf dich!", [c.name])
	for c in ch:
		if c.state == "open":
			return T.t("Weiter geht es im Abenteuer «%s».", [c.name])
	return T.t("Spiel eine Runde mit Freunden – jedes neue Abzeichen gibt Punkte.")


func info() -> Dictionary:
	var ch := chapters()
	var cur := ""
	for c in ch:
		if c.current:
			cur = c.id
	return {"ok": true, "chapters": ch, "badges": badges(), "level": level(), "blinki": blinki(false), "current": cur,
			"open": is_open(), "scene": main.scene}


# ---- actions -------------------------------------------------------------------------------------------------------------
func start_adventure(id: String) -> Dictionary:
	"""«Abenteuer starten»: the hook of the chapter (later the Bergtal adventure), otherwise into its scene"""
	var c := {}
	for x in chapters():
		if x.id == id:
			c = x
	if c.is_empty():
		return {"ok": false, "error": "unknown chapter"}
	if c.state in ["locked", "soon"]:
		return {"ok": false, "error": c.state}
	if adventure_hooks.has(id) and (adventure_hooks[id] as Callable).is_valid():
		(adventure_hooks[id] as Callable).call()
	elif main.scene != id and not main.set_scene(id):
		return {"ok": false, "error": "scene"}
	if not (id in data["visited"]):
		data["visited"].append(id)
		save()
	close()
	if main.mehr != null:
		main.mehr.toast(T.t("Abenteuer «%s» – viel Spass beim Entdecken!", [str(c.name)]))
	return {"ok": true, "id": id}


func reset() -> void:
	data = {"visited": [], "seen_lv": 1, "greeted": false, "done_seen": []}
	save()


func is_open() -> bool:
	return main.mehr != null and main.mehr.win_id == "spiel" and _body != null and is_instance_valid(_body)


func close() -> void:
	if is_open():
		main.mehr.close_window()


func toggle() -> void:
	if is_open():
		close()
	else:
		open()


# ---- the start screen «Spielen» (a window of «Mehr», like the Entdeckungsbuch) ------------------------------------------
func open() -> void:
	if main.mehr == null:
		return
	main.mehr.close_menu()
	_body = main.mehr._window(T.t("Spielen"), "pad")
	main.mehr.win_id = "spiel"
	_paint()


func _paint() -> void:
	if _body == null or not is_instance_valid(_body):
		return
	for c in _body.get_children():
		c.queue_free()
	var W := 600.0
	var vh: float = get_viewport().get_visible_rect().size.y
	# Blinki and what it says
	var bk: Dictionary = blinki(true)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	_body.add_child(row)
	var fig = Tour.BlinkiView.new()
	fig.mood = str(bk.mood)
	fig.custom_minimum_size = Vector2(50, 56)
	fig.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	row.add_child(fig)
	var say := PanelContainer.new()
	say.add_theme_stylebox_override("panel", UI.box(UI.FIELD, UI.LINE, 14, 10, 1))
	say.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(say)
	var sv := VBoxContainer.new()
	sv.add_theme_constant_override("separation", 2)
	say.add_child(sv)
	var st := Label.new()
	st.text = str(bk.title)
	st.add_theme_font_override("font", UI.heading_font())
	st.add_theme_font_size_override("font_size", 15)
	sv.add_child(st)
	var sx := UI.small(str(bk.text), UI.TXT)
	sx.custom_minimum_size = Vector2(W - 100.0, 0)
	sv.add_child(sx)
	# the level
	var lv := level()
	var lh := HBoxContainer.new()
	lh.add_theme_constant_override("separation", 8)
	_body.add_child(lh)
	var ll := Label.new()
	ll.text = T.t("⭐ Stufe %d", [int(lv.lv)])
	ll.add_theme_font_override("font", UI.heading_font())
	ll.add_theme_font_size_override("font_size", 15)
	lh.add_child(ll)
	var lx := UI.small(T.t("%d Punkte · noch %d bis Stufe %d", [int(lv.xp), int(lv.to) - int(lv.xp), int(lv.lv) + 1]))
	lx.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lx.tooltip_text = T.t("Entdeckung +%d · Abzeichen +%d · Abenteuer geschafft +%d · Abenteuer begonnen +%d", [XP_DISC, XP_BADGE, XP_DONE, XP_VISIT])
	lx.mouse_filter = Control.MOUSE_FILTER_PASS
	lh.add_child(lx)
	var lb := ProgressBar.new()
	lb.show_percentage = false
	lb.custom_minimum_size = Vector2(W, 6)
	lb.min_value = float(lv.from)
	lb.max_value = float(lv.to)
	lb.value = float(lv.xp)
	_body.add_child(lb)
	# the adventures
	_body.add_child(UI.heading(T.t("Abenteuer")))
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sc.custom_minimum_size = Vector2(W + 14.0, clampf(vh - 430.0, 150.0, 4 * 78.0))
	_body.add_child(sc)
	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", 6)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(list)
	for c in chapters():
		list.add_child(_chapter_row(c, W))
	# the badges
	_body.add_child(UI.heading(T.t("Abzeichen")))
	var g := GridContainer.new()
	g.columns = 7
	g.add_theme_constant_override("h_separation", 6)
	g.add_theme_constant_override("v_separation", 6)
	_body.add_child(g)
	for b in badges():
		var p := PanelContainer.new()
		var got := int(b.n) > 0
		p.add_theme_stylebox_override("panel", UI.box(UI.PANEL2 if got else UI.FIELD, UI.ACC if got else UI.LINE, 10, 4, 1))
		p.custom_minimum_size = Vector2(80, 0)
		p.tooltip_text = str(b.name) + (" × %d" % int(b.n) if got and b.kind == "game" else "") + ("" if got else " – " + T.t("noch nicht"))
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 0)
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		p.add_child(v)
		var e := Label.new()
		e.text = str(b.sym) if got else "?"
		e.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		e.add_theme_font_size_override("font_size", 18)
		e.add_theme_color_override("font_color", UI.TXT if got else Color(UI.MUT, 0.6))
		v.add_child(e)
		var n := UI.small(str(b.name), UI.TXT if got else UI.MUT)
		n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		n.add_theme_font_size_override("font_size", 10)
		n.autowrap_mode = TextServer.AUTOWRAP_OFF
		n.clip_text = true
		v.add_child(n)
		g.add_child(p)
	# the buttons
	var bt := HBoxContainer.new()
	bt.add_theme_constant_override("separation", 8)
	bt.alignment = BoxContainer.ALIGNMENT_END
	_body.add_child(bt)
	var gw := Button.new()
	gw.text = T.t("Spiel-Assistent")
	gw.tooltip_text = T.t("Team gegen MoveEye: Mitspieler mit dem Handy")
	gw.pressed.connect(func():
		close()
		if main.gamewiz != null:
			main.gamewiz.open_wiz())
	bt.add_child(gw)
	var bb := Button.new()
	bb.text = T.t("Entdeckungsbuch")
	bb.pressed.connect(func():
		if main.entdecken != null:
			main.entdecken.open_book())
	bt.add_child(bb)
	var cl := Button.new()
	cl.text = T.t("Schliessen")
	cl.pressed.connect(close)
	bt.add_child(cl)


func _chapter_row(c: Dictionary, W: float) -> Control:
	var p := PanelContainer.new()
	var cur: bool = c.current
	p.add_theme_stylebox_override("panel", UI.box(UI.PANEL2 if c.state != "locked" and c.state != "soon" else UI.FIELD, UI.ACC if cur else UI.LINE, 12, 8, 1))
	p.custom_minimum_size = Vector2(W, 0)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 10)
	p.add_child(h)
	var num := Label.new()
	num.text = str(c.n)
	num.custom_minimum_size = Vector2(26, 26)
	num.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	num.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	num.add_theme_font_override("font", UI.heading_font())
	num.add_theme_font_size_override("font_size", 16)
	num.add_theme_color_override("font_color", UI.ACC if c.state in ["open", "new"] else (UI.GRN if c.state == "done" else UI.MUT))
	num.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(num)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var tl := HBoxContainer.new()
	tl.add_theme_constant_override("separation", 6)
	v.add_child(tl)
	var t := Label.new()
	t.text = str(c.name)
	t.add_theme_font_override("font", UI.heading_font())
	t.add_theme_font_size_override("font_size", 14)
	t.add_theme_color_override("font_color", UI.MUT if c.state in ["locked", "soon"] else UI.TXT)
	tl.add_child(t)
	var chip: Array = {"new": [T.t("Neu"), UI.ACC], "done": [T.t("✓ Geschafft"), UI.GRN], "locked": [T.t("Gesperrt"), UI.MUT],
			"soon": [T.t("Kommt bald"), UI.MUT], "open": [T.t("Hier bist du") if cur else "", UI.ACC]}.get(c.state, ["", UI.MUT])
	if cur and c.state != "open":
		chip = [str(chip[0]) + " · " + T.t("Hier bist du"), chip[1]]
	if str(chip[0]) != "":
		var ch := UI.small(str(chip[0]), chip[1])
		ch.autowrap_mode = TextServer.AUTOWRAP_OFF
		ch.add_theme_font_size_override("font_size", 11)
		tl.add_child(ch)
	var sh := UI.small(str(c.short), UI.MUT)
	sh.custom_minimum_size = Vector2(W - 230.0, 0)
	v.add_child(sh)
	var prog := ""
	if c.state == "soon":
		prog = T.t("Dieses Abenteuer kommt mit einer nächsten Version.")
	elif c.state == "locked":
		prog = T.t("Öffnet sich, wenn das Abenteuer davor zur Hälfte entdeckt ist.")
	elif int(c.total) > 0:
		prog = T.t("%d von %d entdeckt", [int(c.found), int(c.total)])
	elif c.visited:
		prog = T.t("Hier gibt es (noch) nichts zu entdecken.")
	else:
		prog = T.t("Noch nicht besucht – was es zu entdecken gibt, zeigt sich vor Ort.")
	var ph := HBoxContainer.new()
	ph.add_theme_constant_override("separation", 8)
	v.add_child(ph)
	var pl := UI.small(prog, UI.TXT if int(c.total) > 0 else UI.MUT)
	pl.custom_minimum_size = Vector2(W - 230.0 - (130.0 if int(c.total) > 0 else 0.0), 0)
	ph.add_child(pl)
	if int(c.total) > 0:
		var bar := ProgressBar.new()
		bar.show_percentage = false
		bar.custom_minimum_size = Vector2(120, 6)
		bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		bar.max_value = float(c.total)
		bar.value = float(c.found)
		ph.add_child(bar)
	var b := Button.new()
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	b.custom_minimum_size = Vector2(150, 34)
	if c.state in ["locked", "soon"]:
		b.text = T.t("Gesperrt") if c.state == "locked" else T.t("Kommt bald")
		b.disabled = true
	else:
		b.text = T.t("Weiter spielen") if cur else T.t("Abenteuer starten")
		if not cur:
			UI.primary(b)
		var id: String = c.id
		b.pressed.connect(func(): start_adventure(id))
	h.add_child(b)
	return p


# ---- /control {"action": "spielbereich", …} ---------------------------------------------------------------------------------
func control(d: Dictionary) -> Dictionary:
	match str(d.get("do", "info")):
		"open":
			open()
		"close":
			close()
		"start":
			var r := start_adventure(str(d.get("id", "")))
			r.merge(info())
			return r
		"seen":                                        # MoveEye showed its tab: Blinki's joy counts as seen there too
			var r := info()
			blinki(true)
			return r
		"reset":                                       # tests: only the state of the play area (not the discoveries)
			reset()
	return info()
