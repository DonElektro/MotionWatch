extends RefCounted
## «Simulator im Browser» (Machbarkeit, Besitzer 14.11.2026): die Web-Ausgabe (Godot 4.3 Web, ohne Threads) für
## kevlaschef.com/moveeye/sim/. Im Browser gibt es keine Startoptionen; die Adresse ersetzt sie:
##   index.html?szene=wald&grafik=normal&stunde=21&sprache=fr
## Ohne Angaben: Grafik-Modus Lite, die Demo-Szene DEMO_SCENE, Mittag (DEMO_HOUR) und die Sprache des Browsers. MoveEye ist
## im Browser nie verbunden (der Simulator ist sonst der Server für MoveEye – ein Browser kann keinen Server öffnen); dafür
## gibt es das kleine eingebaute MoveEye der Demo (web_demo.gd).

const DEMO_SCENE := "garten"
const DEMO_HOUR := "12"                 # Tageslicht, auch wenn es beim Besucher Nacht ist (?stunde=… wählt die Uhrzeit)
const T = preload("res://scripts/i18n.gd")


static func on() -> bool:
	return OS.has_feature("web")


static func _query() -> Dictionary:
	var out := {}
	if not on():
		return out
	var q = JavaScriptBridge.eval("window.location.search", true)
	if typeof(q) != TYPE_STRING:
		return out
	for part in str(q).trim_prefix("?").split("&", false):
		var kv := part.split("=", true, 1)
		out[kv[0].uri_decode().to_lower()] = kv[1].uri_decode() if kv.size() > 1 else "1"
	return out


static func args() -> PackedStringArray:
	"""die Startoptionen für main.gd aus der Adresse (leer ausserhalb des Browsers)"""
	if not on():
		return PackedStringArray()
	var q := _query()
	var a := PackedStringArray(["--grafik", str(q.get("grafik", "lite")), "--scene", str(q.get("szene", DEMO_SCENE))])
	a.append_array(PackedStringArray(["--hour", str(q.get("stunde", DEMO_HOUR))]))
	if q.has("qualitaet"):
		a.append_array(PackedStringArray(["--quality", str(q["qualitaet"])]))
	return a


static func start(main: Node) -> void:
	"""im Browser: Sprache, die Demo (web_demo.gd) und alle 10 s Bilder pro Sekunde und Speicher in die Konsole des Browsers
	(F12) – für Tests am Handy/PC"""
	if not on():
		return
	var q := _query()
	var sp := str(q.get("sprache", "")).to_lower()
	if sp in T.codes():
		T.set_lang(sp)
	elif T.choice() in ["", "auto"]:
		var nav = JavaScriptBridge.eval("(navigator.language || 'de').slice(0, 2).toLowerCase()", true)
		if typeof(nav) == TYPE_STRING and str(nav) in T.codes():
			T.set_moveeye_lang(str(nav))             # wie die Sprache, die MoveEye meldet: eine eigene Wahl gilt vor
	_symbols()
	var demo = preload("res://scripts/web_demo.gd").new()
	demo.name = "WebDemo"
	demo.main = main
	main.web_demo = demo
	main.add_child(demo)
	if q.has("test"):                               # Tests in Chromium: window.mwControl (web_bruecke.gd)
		var wt = preload("res://scripts/web_bruecke.gd").new()
		wt.name = "WebTest"
		wt.main = main
		main.add_child(wt)
	var t := Timer.new()
	t.wait_time = 10.0
	t.autostart = true
	t.timeout.connect(func():
		print("web: %d fps, %d MB statisch, %d MB Grafik" % [Engine.get_frames_per_second(), OS.get_static_memory_usage() / 1048576,
			Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576]))
	main.add_child(t)


static func _symbols() -> void:
	"""im Browser gibt es keine Schriften des Systems: Zeichen wie ✕ ● ▲ ↳ ⚠ wären leere Kästchen. Eine kleine Schrift mit genau
	diesen Zeichen (schrift/symbole.ttf, aus DejaVu Sans, werkzeuge: pyftsubset) hängt als Rückfall an der Standardschrift"""
	var sym = load("res://schrift/symbole.ttf")
	var fb: Font = ThemeDB.fallback_font
	if sym == null or fb == null or sym in fb.fallbacks:
		return
	var l := fb.fallbacks.duplicate()
	l.append(sym)
	fb.fallbacks = l
