extends RefCounted
## «Simulator im Browser» (Machbarkeit, Besitzer 14.11.2026): die Web-Ausgabe (Godot 4.3 Web, ohne Threads) für
## kevlaschef.com/moveeye/sim/. Im Browser gibt es keine Startoptionen; die Adresse ersetzt sie:
##   index.html?szene=wald&grafik=normal&stunde=21
## Ohne Angaben: Grafik-Modus Lite und die Demo-Szene DEMO_SCENE. MoveEye ist im Browser nie verbunden (der Simulator
## ist sonst der Server für MoveEye – ein Browser kann keinen Server öffnen); der Kopf bewacht dann selbst (Spiel-Wache).

const DEMO_SCENE := "garten"


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
	if q.has("stunde"):
		a.append_array(PackedStringArray(["--hour", str(q["stunde"])]))
	if q.has("qualitaet"):
		a.append_array(PackedStringArray(["--quality", str(q["qualitaet"])]))
	return a


static func start(main: Node) -> void:
	"""im Browser: alle 10 s Bilder pro Sekunde und Speicher in die Konsole des Browsers (F12) – für Tests am Handy/PC"""
	if not on():
		return
	var t := Timer.new()
	t.wait_time = 10.0
	t.autostart = true
	t.timeout.connect(func():
		print("web: %d fps, %d MB statisch, %d MB Grafik" % [Engine.get_frames_per_second(), OS.get_static_memory_usage() / 1048576,
			Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576]))
	main.add_child(t)
