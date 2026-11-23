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


## Spar-Modus im Browser (Besitzer 23.11.2026, iPad Pro 12.9": «WebGL context lost» schon beim Laden): Safari auf iPhone / iPad
## gibt einer Seite nur wenig Grafikspeicher und nimmt ihn bei Knappheit ganz weg. Das iPad Pro zeichnete mit Pixeldichte 2 auf
## 2732 × 2048 Bildpunkte – 3.5-mal so viele wie ein iPhone mit der Schärfe 0.67. Darum:
##   «ios»  = iPhone / iPad (iPadOS meldet sich als Mac: Touch-Punkte > 1) - automatisch, ohne Angabe in der Adresse
##   «lite» = ?lite=1 in der Adresse (Knopf «Im Spar-Modus neu laden» der Meldung in index.html, werkzeuge/sim_web_speicher.py)
## Die Seite (index.html) begrenzt dazu schon die Pixeldichte der Leinwand (iOS höchstens 2 und 3.2 Mio. Bildpunkte: iPad Pro 1.53; lite 1.0); hier kommt die 3D-Ansicht dazu.
const SPAR_PX := {"ios": 1800000.0, "lite": 1000000.0}      # höchstens so viele Bildpunkte zeichnet die 3D-Ansicht


static func spar() -> String:
	"""«» (normal) / «ios» / «lite» - einmal gefragt, danach aus der Engine-Meta (in Tests von aussen setzbar)"""
	if Engine.has_meta("web_spar"):
		return str(Engine.get_meta("web_spar"))
	var s := ""
	if on():
		if str(_query().get("lite", "")).to_lower() in ["1", "true", "ja", "an", "on"]:
			s = "lite"
		else:
			var ios = JavaScriptBridge.eval("(/iPad|iPhone|iPod/.test(navigator.userAgent || '') || (/Mac/.test(navigator.platform || '') && navigator.maxTouchPoints > 1)) ? 1 : 0", true)
			if typeof(ios) in [TYPE_INT, TYPE_FLOAT] and int(ios) == 1:
				s = "ios"
	Engine.set_meta("web_spar", s)
	return s


static func spar_scale(px: Vector2i, k: float) -> float:
	"""die Schärfe k der 3D-Ansicht, im Spar-Modus so weit gesenkt, dass höchstens SPAR_PX Bildpunkte gezeichnet werden"""
	var s := spar()
	var n := float(maxi(px.x, 1) * maxi(px.y, 1)) * k * k
	if not SPAR_PX.has(s) or n <= float(SPAR_PX[s]):
		return k
	return clampf(k * sqrt(float(SPAR_PX[s]) / n), 0.5, k)


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
	a.append_array(grossvater_args(q))
	a.append_array(roboter_args(q))
	return a


static func roboter_args(q: Dictionary) -> PackedStringArray:
	"""die Kachel «Roboter-Labor» auf der Startseite (Besitzer 22.11.2026): ?roboter=1 öffnet nach dem Laden gleich das
	Roboter-Labor (Startoption --roboter=<Wert>, roboter_start.gd); zusammen mit ?grossvater=… gilt das Spiel. Der Wert geht
	unverändert als «variante» an das Labor (control {"do": "open", "variante": …}; z. B. 4 = der 4er-Roboter), 0 / false = aus"""
	var v := str(q.get("roboter", "")).to_lower().strip_edges()
	if q.has("grossvater") or v in ["", "0", "false"] or not v.is_valid_identifier() and not v.is_valid_int():
		return PackedStringArray()
	return PackedStringArray(["--roboter=" + v.left(12)])


static func grossvater_args(q: Dictionary) -> PackedStringArray:
	"""die Kachel auf der Startseite (22.11.2026): ?grossvater=1 = der Kapitelwähler (vorher die Heldenwahl, wenn keiner
	gespeichert ist), ?grossvater=1&kapitel=N = gleich Kapitel N; danach geht es Kapitel um Kapitel weiter (kit_abenteuer.gd)"""
	var a := PackedStringArray()
	if str(q.get("grossvater", "")) in ["1", "neu", "k2"]:
		a.append("--grossvater-neu")
		if str(q.get("kapitel", "")).is_valid_int():
			a.append("--grossvater-kapitel=" + str(int(str(q["kapitel"]))))
		elif str(q["grossvater"]) == "k2":                  # (the old address of chapter 2)
			a.append("--grossvater-kapitel=2")
		if q.has("name"):                               # tests on the phone: without the start card (…&name=Nina&k2szene=s06_bruecke)
			a.append("--kit-name=" + str(q["name"]).uri_decode().left(20))
		if q.has("messen"):                             # a line with frame times in the game (phone / iPad tests)
			a.append("--kit-messen")
		if q.has("k2szene"):
			a.append("--kit-szene=" + str(q["k2szene"]).left(40))
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
	var spm := spar()
	if spm != "":                                    # schon vor dem Aufbau der Welt: kein MSAA, 3D-Ansicht im Rahmen von SPAR_PX
		var vp := main.get_viewport()
		vp.msaa_3d = Viewport.MSAA_DISABLED
		vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
		vp.scaling_3d_scale = spar_scale(main.get_tree().root.size, vp.scaling_3d_scale)
		print("web: Spar-Modus «%s» (Fenster %d × %d, 3D-Schärfe %.2f)" % [spm, main.get_tree().root.size.x,
			main.get_tree().root.size.y, vp.scaling_3d_scale])
	var demo = preload("res://scripts/web_demo.gd").new()
	demo.name = "WebDemo"
	demo.main = main
	main.web_demo = demo
	main.add_child(demo)
	var wm = preload("res://scripts/web_moveeye.gd").new()     # Demo beim Host: mit dem Demo-MoveEye der Homepage (Schalter «Mehr»)
	wm.name = "WebMoveEye"
	wm.main = main
	main.add_child(wm)
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
