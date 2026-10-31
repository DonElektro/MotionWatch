extends Node
## Web-Machbarkeit (Zweig real-web-test, nur zum Probieren): im Browser gibt es keinen HTTP-Server (--stream / /control).
## Diese Brücke macht dieselbe Steuerung (main.control) aus JavaScript erreichbar:
##   window.mwControl('{"action":"maggie","do":"info"}')  → Antwort als JSON in window.mwLast
## Zusätzlich alle 2 s eine Zeile «MWWEB fps=…» in der Browser-Konsole (für Playwright-Messungen).
## Nur aktiv mit OS.has_feature("web"); auf dem PC passiert nichts.

var main
var _cb                                   # JavaScriptObject – muss gehalten werden, sonst ist der Callback weg
var _win
var _t := 0.0


func _ready() -> void:
	if not OS.has_feature("web"):
		set_process(false)
		return
	_win = JavaScriptBridge.get_interface("window")
	_cb = JavaScriptBridge.create_callback(_on_js)
	_win.mwControl = _cb
	_win.mwLast = "{}"
	print("MWWEB bridge ready")


func _on_js(args: Array) -> void:
	var d = JSON.parse_string(str(args[0])) if args.size() > 0 else null
	var r: Dictionary = {"ok": false, "error": "bad json"}
	if d is Dictionary:
		r = main.control(d)
	_win.mwLast = JSON.stringify(r)


func _process(dt: float) -> void:
	_t += dt
	if _t >= 2.0:
		_t = 0.0
		print("MWWEB fps=%d frame_ms=%.1f mem_mb=%.0f" % [Engine.get_frames_per_second(), Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
				Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0])
