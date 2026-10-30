extends Node
## 3D-4.2x «Mehr» → Protokoll (Wunsch Daniel 30.10.2026): die letzten Ereignisse und Fehler des Simulators – Start,
## Verbindung zu MoveEye, Szene, Testlauf, Spiel, Update, Grafik, Rückmeldung und die Fehler / Warnungen von Godot (aus
## dem Log user://logs/godot.log, wenn es geschrieben wird). Ein Ringspeicher (400 Einträge, nur im Speicher), Filter,
## Kopieren. Die Ereignisse werden zweimal pro Sekunde aus dem Zustand von main.gd gelesen – main.gd muss nichts melden.

var main
var items: Array = []                  # {"t": unix, "k": kind, "x": text}
var seq := 0
const MAX := 400
const KINDS := [["", "Alle"], ["fehler", "Fehler"], ["verbindung", "Verbindung"], ["szene", "Szene"], ["test", "Test"],
		["spiel", "Spiel"], ["system", "System"]]
const KIND_OF := {"fehler": "fehler", "warnung": "fehler", "verbindung": "verbindung", "szene": "szene", "test": "test",
		"spiel": "spiel", "start": "system", "update": "system", "info": "system", "grafik": "system", "rueckmeldung": "system"}
const UI = preload("res://scripts/ui_style.gd")

var _t := 0.0
var _st := {}
var _log_pos := -1
var _log_rest := ""
var _log_t := 0.0
var _slow_t := 0.0
var _slow_said := -1000.0
var _err_n := 0                        # how many Godot errors since the start (also in the self-check)


func _ready() -> void:
	var v: Dictionary = Engine.get_version_info()
	add("start", "Simulator %s gestartet · Godot %s · %s · Grafik «%s»" % [main.VERSION, str(v.get("string", "")), OS.get_name(), str(main.quality)])


func add(kind: String, text: String) -> void:
	seq += 1
	items.append({"t": Time.get_unix_time_from_system(), "k": kind, "x": text.strip_edges().substr(0, 400), "n": seq})
	if items.size() > MAX:
		items = items.slice(items.size() - MAX)


func errors() -> int:
	return _err_n


# ---- what happened: read from the state of main.gd ---------------------------------------------------------------------
func _changed(key: String, v, first := false) -> bool:
	if not _st.has(key):
		_st[key] = v
		return first
	if _st[key] == v:
		return false
	_st[key] = v
	return true


func _process(dt: float) -> void:
	_t -= dt
	_log_t -= dt
	if _log_t <= 0.0:
		_log_t = 2.0
		_read_godot_log()
	if _t > 0.0:
		return
	_t = 0.5
	var m = main
	var conn: bool = m.mw_addr != "" and m.now() - m.mw_t < 3.0
	if _changed("conn", conn):
		if conn:
			add("verbindung", "Verbunden mit «%s» (MoveEye %s) von %s" % [str(m.mw.get("device", "MoveEye")), str(m.mw.get("mw_version", "?")), m.mw_addr])
		else:
			add("verbindung", "Verbindung zu MoveEye unterbrochen (seit 3 s nichts mehr gehört)")
	if _changed("stream", bool(m.stream_on)):
		add("verbindung", ("An MoveEye senden: ein (Port %d)" % int(m.stream_port)) if m.stream_on else "An MoveEye senden: aus")
	if m.tunnel != null and _changed("tunnel", str(m.tunnel.msg) if m.tunnel_on else "aus"):
		add("verbindung", "Tunnel: " + (str(m.tunnel.msg) if m.tunnel_on else "aus"))
	if _changed("scene", str(m.scene), true):
		add("szene", "Szene: " + str(m.Scenes.name_of(m.scene)))
	if _changed("weather", str(m.weather), true):
		add("szene", "Wetter: " + {"clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee"}.get(str(m.weather), str(m.weather)))
	if m.testrun != null and _changed("test", bool(m.testrun.running)):
		add("test", ("Testlauf gestartet (Plan «%s»)" % str(m.testrun.plan)) if m.testrun.running else ("Testlauf zu Ende · " + str(m.testrun.status())))
	if m.game != null:
		if _changed("game_open", bool(m.game.open)):
			add("spiel", "Spiel geöffnet" if m.game.open else "Spiel geschlossen")
		if _changed("game_round", str(m.game.round_state)):
			add("spiel", "Spielrunde: " + {"lobby": "Warteraum", "countdown": "Countdown", "play": "läuft", "end": "fertig"}.get(str(m.game.round_state), str(m.game.round_state)))
	if _changed("update", str(m.update_info)) and str(m.update_info) != "":
		add("update", "Update: " + str(m.update_info))
	if _changed("start_info", str(m.start_info)) and str(m.start_info) != "":
		add("info", str(m.start_info))
	if _changed("quality", str(m.quality)):
		add("grafik", "Grafik: " + str(m.quality))
	if _changed("kids", bool(m.kids_on)):
		add("info", "Kinder-Modus " + ("ein" if m.kids_on else "aus"))
	if m.schnitt != null and _changed("schnitt", str(m.schnitt.get("result"))) and str(m.schnitt.get("result")) != "":
		var r := str(m.schnitt.get("result"))
		add("fehler" if r.begins_with("SCRIPT ERROR") or r.find("Schnittstelle: OK") < 0 else "info", r)
	var fps := Engine.get_frames_per_second()           # slow for 10 s: once per 5 minutes
	_slow_t = _slow_t + 0.5 if fps > 0 and fps < 8 and m.win_open else 0.0
	if _slow_t >= 10.0 and m.now() - _slow_said > 300.0:
		_slow_said = m.now()
		add("warnung", "Nur %d Bilder pro Sekunde seit 10 s – Grafik leichter stellen oder andere Programme schliessen" % fps)


func _read_godot_log() -> void:
	"""the new lines of Godot's own log: errors and warnings (first line + «at: …»)"""
	var p := OS.get_user_data_dir().path_join("logs").path_join("godot.log")
	if not FileAccess.file_exists(p):
		return
	var f := FileAccess.open(p, FileAccess.READ)
	if f == null:
		return
	var n := f.get_length()
	if _log_pos < 0 or n < _log_pos:
		_log_pos = 0
	if n - _log_pos > 400000:                              # a huge log: only the end
		_log_pos = n - 400000
	if n == _log_pos:
		return
	f.seek(_log_pos)
	var chunk := f.get_buffer(n - _log_pos).get_string_from_utf8()
	_log_pos = n
	var lines := (_log_rest + chunk).split("\n")
	_log_rest = lines[lines.size() - 1]
	var last := {}
	for i in range(lines.size() - 1):
		var ln := lines[i].strip_edges()
		if ln.begins_with("ERROR:") or ln.begins_with("SCRIPT ERROR:") or ln.begins_with("USER ERROR:") or ln.begins_with("USER SCRIPT ERROR:"):
			_err_n += 1
			add("fehler", "Godot: " + ln)
			last = items[items.size() - 1]
		elif ln.begins_with("WARNING:") or ln.begins_with("USER WARNING:"):
			add("warnung", "Godot: " + ln)
			last = items[items.size() - 1]
		elif ln.begins_with("at:") and not last.is_empty():
			last["x"] = str(last["x"]) + "  (" + ln.substr(3).strip_edges() + ")"
			last = {}
		else:
			last = {}


# ---- the window ------------------------------------------------------------------------------------------------------------
var _list: VBoxContainer
var _filter := ""
var _seg_btns := {}
var _shown := -1
var _info: Label


func build(body: VBoxContainer, mehr) -> void:
	_shown = -1
	var seg := HBoxContainer.new()
	seg.add_theme_constant_override("separation", 4)
	body.add_child(seg)
	_seg_btns = {}
	for k in KINDS:
		var b := Button.new()
		b.text = k[1]
		b.toggle_mode = true
		b.focus_mode = Control.FOCUS_NONE
		b.add_theme_font_size_override("font_size", 12)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.pressed.connect(func(): _filter = k[0]; _shown = -1; refresh())
		seg.add_child(b)
		_seg_btns[k[0]] = b
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(560, 360)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(sc)
	_list = VBoxContainer.new()
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_list.add_theme_constant_override("separation", 3)
	sc.add_child(_list)
	_info = UI.small("")
	body.add_child(_info)
	var bt := HBoxContainer.new()
	bt.alignment = BoxContainer.ALIGNMENT_END
	bt.add_theme_constant_override("separation", 8)
	body.add_child(bt)
	var cp := Button.new()
	cp.text = "Kopieren"
	cp.tooltip_text = "Die angezeigten Einträge als Text in die Zwischenablage (z. B. für eine Rückmeldung)"
	cp.pressed.connect(func():
		DisplayServer.clipboard_set(as_text(_filter))
		_info.text = "Kopiert: %d Einträge in der Zwischenablage." % _filtered(_filter).size())
	bt.add_child(cp)
	var cl := Button.new()
	cl.text = "Schliessen"
	cl.pressed.connect(func(): mehr.close_window())
	bt.add_child(cl)
	refresh()


func _filtered(f: String) -> Array:
	if f == "":
		return items
	return items.filter(func(e): return KIND_OF.get(str(e["k"]), "system") == f)


func as_text(f := "") -> String:
	var out := PackedStringArray()
	out.append("3D-Simulator %s · Protokoll · %s" % [main.VERSION, Time.get_datetime_string_from_system(false, true)])
	for e in _filtered(f):
		out.append("%s  %-10s  %s" % [_hms(float(e["t"])), str(e["k"]), str(e["x"])])
	return "\n".join(out)


func _hms(t: float) -> String:
	var d := Time.get_datetime_dict_from_unix_time(int(t + Time.get_time_zone_from_system().get("bias", 0) * 60))
	return "%02d:%02d:%02d" % [d.hour, d.minute, d.second]


func refresh() -> void:
	if _list == null or not is_instance_valid(_list):
		return
	for k in _seg_btns:
		var b: Button = _seg_btns[k]
		b.button_pressed = k == _filter
	if _shown == seq:
		return
	_shown = seq
	for c in _list.get_children():
		c.queue_free()
	var rows := _filtered(_filter)
	var start: int = max(0, rows.size() - 150)
	for i in range(rows.size() - 1, start - 1, -1):           # the newest at the top
		var e: Dictionary = rows[i]
		var r := HBoxContainer.new()
		r.add_theme_constant_override("separation", 8)
		var dot := Control.new()
		dot.custom_minimum_size = Vector2(10, 18)
		var col: Color = {"fehler": UI.RED, "warnung": UI.ORG, "verbindung": UI.ACC, "szene": UI.GRN, "test": Color("#b794f6"),
				"spiel": Color("#e0a526"), "update": UI.ACC}.get(str(e["k"]), UI.MUT)
		dot.draw.connect(func(): dot.draw_circle(Vector2(5, 9), 4.0, col))
		r.add_child(dot)
		var tl := UI.small(_hms(float(e["t"])))
		tl.autowrap_mode = TextServer.AUTOWRAP_OFF
		r.add_child(tl)
		var xl := UI.small(str(e["x"]), UI.RED.lightened(0.25) if str(e["k"]) == "fehler" else UI.TXT)
		xl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		xl.custom_minimum_size = Vector2(420, 0)
		r.add_child(xl)
		_list.add_child(r)
	if rows.is_empty():
		_list.add_child(UI.small("Noch keine Einträge in dieser Auswahl."))
	_info.text = "%d Einträge (die letzten %d werden gezeigt) · %d Fehler von Godot seit dem Start" % [rows.size(), rows.size() - start, _err_n]


func state() -> Dictionary:
	return {"n": items.size(), "errors": _err_n, "last": items.slice(max(0, items.size() - 12))}
