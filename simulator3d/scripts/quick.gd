extends VBoxContainer
## 3D-3.86: «Schnellzugriff» - ganz oben im Bedienfeld: grosse Kacheln für das, was man oft braucht. Ein Klick tut es oder
## öffnet ein kleines Menü direkt an der Kachel (Tageszeit, Wetter, Besuch). Alles andere bleibt in den Karten darunter.

var main
var _grid: GridContainer
var _tiles := {}
var _subs := {}
var _t := 0.0

const UI = preload("res://scripts/ui_style.gd")

# [id, symbol, name]
const TILES := [["scene", "globe", "Szene"], ["time", "clock", "Tageszeit"], ["weather", "cloud", "Wetter"], ["visit", "person", "Besuch"],
		["inventar", "box", "Gegenstände"], ["map", "map", "Echter Ort"], ["planner", "plan", "Aufstellen"],
		["test", "check", "Testen"], ["pruef", "meter", "Prüfstand"], ["learn", "lens", "Trainingsbilder"], ["game", "pad", "Spiel"],
		["disc", "book", "Entdeckungen"], ["play", "star", "Spielen"]]   # Paket «Spielbereich»: the start screen (spielbereich.gd)                 # Erlebniswelt 20: the Entdeckungsbuch (entdecken.gd), like the tile 📖 of MoveEye 139
# 3D-4.21 (Menü 2): the tiles under the same four headings as the simulator centre of MoveEye
const HEADS := [["Welt", ["scene", "time", "weather", "visit", "inventar", "map", "planner"]], ["Testen", ["test", "pruef"]],
		["Lernen", ["learn"]], ["Spielen", ["play", "game", "disc"]]]
# 3D-4.0 (Gesamtrunde): «Patrouille» (= Rover-Route) and «Kopf steuern» only in the bar below - the bar moves, the tiles hold content
const TIMES := [["Morgen 07:00", 7.0], ["Mittag 13:00", 13.0], ["Abend 19:30", 19.5], ["Dämmerung 21:00", 21.0], ["Nacht 23:00", 23.0], ["Tiefe Nacht 03:00", 3.0]]
const WEATHER := [["Klar", "clear"], ["Bewölkt", "cloudy"], ["Regen", "rain"], ["Nebel", "fog"], ["Schnee", "snow"]]
const VISITS := [["Person", "person"], ["Dieb (Velo, Tür)", "thief"], ["Kind", "child"], ["Spaziergang mit Hund", "dogwalk"], ["Velofahrer", "cyclist"],
		["Auto", "car"], ["Fuchs", "fox"], ["Reh", "deer"], ["Katze", "cat"], ["Wildschwein", "boar"], ["Igel", "hedgehog"], ["Alle wegschicken", "clear"]]


func _ready() -> void:
	add_theme_constant_override("separation", 6)
	var h := HBoxContainer.new()
	add_child(h)
	var t := UI.small("SCHNELLZUGRIFF", UI.MUT)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(t)
	var grids := {}
	for hd in HEADS:
		var hl := UI.small(str(hd[0]).to_upper(), UI.MUT)
		hl.add_theme_font_size_override("font_size", 10)
		add_child(hl)
		var g := GridContainer.new()
		g.columns = 4
		g.add_theme_constant_override("h_separation", 6)
		g.add_theme_constant_override("v_separation", 6)
		add_child(g)
		for k in hd[1]:
			grids[k] = g
	_grid = grids["scene"]
	for d in TILES:
		var b := Button.new()
		b.custom_minimum_size = Vector2(84, 58)
		b.focus_mode = Control.FOCUS_NONE
		b.tooltip_text = d[2]
		var v := VBoxContainer.new()
		v.set_anchors_preset(Control.PRESET_FULL_RECT)
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_theme_constant_override("separation", 3)
		b.add_child(v)
		var ic := UI.group_icon(d[1])
		ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		v.add_child(ic)
		var l := Label.new()
		l.text = d[2]
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.add_theme_font_size_override("font_size", 11)
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(l)
		var s := Label.new()
		s.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		s.add_theme_font_size_override("font_size", 9)
		s.add_theme_color_override("font_color", UI.MUT)
		s.clip_text = true
		s.custom_minimum_size = Vector2(78, 0)
		s.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(s)
		_subs[d[0]] = s
		var id: String = d[0]
		b.pressed.connect(func(): _press(id, b))
		(grids.get(id, _grid) as GridContainer).add_child(b)
		_tiles[id] = b


func _menu(b: Button, items: Array, cb: Callable) -> void:
	var pm := PopupMenu.new()
	pm.theme = main.ui_root.theme
	for i in range(items.size()):
		pm.add_item(items[i][0], i)
	pm.id_pressed.connect(func(i): cb.call(items[i][1]); pm.queue_free())
	pm.popup_hide.connect(func(): pm.queue_free.call_deferred())
	add_child(pm)
	var r := b.get_global_rect()
	pm.popup(Rect2i(Vector2i(r.position + Vector2(0, r.size.y)), Vector2i(0, 0)))


func _press(id: String, b: Button) -> void:
	match id:
		"scene":
			main.templates.toggle(0)
		"time":
			_menu(b, TIMES, func(h): main.set_hour(float(h)); main._settings_dirty = true)
		"weather":
			_menu(b, WEATHER, func(w): main.weather = str(w); main._update_sky(); main._sync_ui(); main._settings_dirty = true)
		"visit":
			_menu(b, VISITS, func(k):
				if k == "clear":
					for v in main.visitors.get_children():
						v.queue_free()
				elif k == "thief":
					main.thief()
				elif k == "car":
					main.car()
				else:
					main.visit(str(k)))
		"inventar":
			main.inventar.toggle()
		"test":                                      # 3D-4.x: one place for testing - the tile opens the card «Testen»
			main.open_testen()
		"game":
			main.gamewiz.open_wiz()
		"disc":
			if main.entdecken != null:
				main.entdecken.open_book()
		"play":
			if main.spielbereich != null:
				main.spielbereich.toggle()
		"learn":
			main.open_train()
		"patrol":
			if main.patrol.active:
				main.patrol.set_active(false)
			else:
				main.patrol.ask()
		"head":
			main.headpad.toggle()
		"map":
			main.open_map()
		"planner":
			main.planner.open(not main.planner.visible)
		"pruef":
			main.pruef.open(not main.pruef.visible)
	_paint()


func _process(dt: float) -> void:
	_t -= dt
	if _t > 0.0 or not is_visible_in_tree():
		return
	_t = 0.5
	_paint()


func _paint() -> void:
	var h: float = main.hour()
	_subs["scene"].text = main.Scenes.name_of(main.scene) + " · Vorlagen"
	_subs["time"].text = "%02d:%02d %s" % [int(h), int(fmod(h, 1.0) * 60), "Nacht" if main.is_dark() else "Tag"]
	_subs["weather"].text = {"clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee"}.get(main.weather, main.weather)
	_subs["visit"].text = "%d da" % main.visitors.get_child_count()
	_subs["inventar"].text = "Zelt, Velo, 80 Dinge"
	_subs["learn"].text = "eigene KI"
	_subs["test"].text = "Testlauf läuft" if main.testrun.running else ("Blinde Flecken" if main.blindmap != null and main.blindmap.busy else "Karte öffnen")
	_subs["game"].text = (main.game.status() if main.game != null and main.game.status() != "" else "Assistent")
	if _subs.has("patrol"):
		_subs["patrol"].text = "fährt" if main.patrol.active else "aus"
	if _subs.has("head"):
		_subs["head"].text = "Pfeile, Licht"
	_subs["map"].text = "Karte der Welt"
	if main.entdecken != null:
		_subs["disc"].text = "%d von %d" % [main.entdecken.count(), main.entdecken.total()]
	if main.spielbereich != null:
		_subs["play"].text = main.spielbereich.tile_text()
	_subs["planner"].text = "wohin?"
	_subs["pruef"].text = "Erkennung"
	var on := {"inventar": main.inventar != null and main.inventar.visible, "test": main.testrun.running,
			"patrol": main.patrol.active, "head": main.headpad != null and main.headpad.visible, "map": main.karte.visible,
			"planner": main.planner.visible, "pruef": main.pruef.visible, "game": main.gamewiz.visible,
			"play": main.spielbereich != null and main.spielbereich.is_open()}
	for k in _tiles:
		var a: bool = on.get(k, false)
		_tiles[k].add_theme_stylebox_override("normal", UI.box(UI.ACC.darkened(0.55) if a else UI.BTN2, UI.ACC if a else UI.LINE, 10, 4, 2 if a else 1))
