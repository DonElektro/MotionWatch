extends SceneTree
## Test ohne Bild für die Symbol-Animation (Besitzer 22.11.2026, wie MW_SYMBOL_HTML in MoveEye Teil 144): mw_logo.gd (eine
## Quelle für alle Sim-Stellen) - Ecken + rote Person ±9 in 7 s, Fächer ±12°, Schritt 0.7 s mit Bein / Arm einen halben Schritt
## versetzt, zweimal blinzeln in 23 s, «Bewegung reduzieren» = still; Blinkis Sprechblase im Zustand «normal» zeichnet die
## Person (mehr_icons.gd blinki_bubble), die anderen Zustände ihre Zeichen.
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/symbol_anim_test.gd"   (absoluter Pfad nötig)
## Ende: «Symbol-Animation-Test OK» oder «SCRIPT ERROR: Symbol-Animation-Test: …» (Exit-Code 0 / 1).

var errs := []


func ok(what: String, cond: bool) -> void:
	if not cond:
		errs.append(what)
		print("  FEHLER ", what)


func near(a: float, b: float, e := 0.01) -> bool:
	return absf(a - b) <= e


func _init() -> void:
	var L = load("res://scripts/mw_logo.gd")
	var UI = load("res://scripts/ui_style.gd")
	var I = load("res://scripts/mehr_icons.gd")
	UI.motion_still = false
	ok("Gang links bei 0 s", near(L.walk(0.0), -1.0))
	ok("Gang rechts bei 3.5 s", near(L.walk(3.5), 1.0))
	ok("Gang Mitte bei 1.75 s", near(L.walk(1.75), 0.0))
	ok("Gang weich (ease-in-out)", L.walk(0.2) < -0.97 and L.walk(1.2) > -0.75)
	ok("Gang wieder links bei 7 s", near(L.walk(7.0), -1.0))
	ok("Schritt 0.7 s", near(L.step(0.0), 1.0) and near(L.step(0.35), -1.0) and near(L.step(0.7), 1.0))
	ok("Abstand ±9 / ±12°", near(L.WALK, 9.0) and near(L.SWING, 12.0))
	ok("Person rot wie LOGO_RED", L.RED.to_html(false) == "e0242b")
	var closed := []
	var t := 0.0
	var was := false
	while t < 23.0:
		var c: bool = L.lid(t) > 0.99
		if c and not was:
			closed.append(snappedf(t, 0.01))
		was = c
		t += 0.005
	ok("zweimal blinzeln in 23 s %s" % [closed], closed.size() == 2 and closed[0] > 9.1 and closed[0] < 9.3 and closed[1] > 22.0 and closed[1] < 22.2)
	ok("sonst offen", L.lid(5.0) == 0.0 and L.lid(15.0) == 0.0)
	UI.motion_still = true
	ok("Bewegung reduzieren: still", L.walk(1.0) == 0.0 and L.step(0.2) == 0.0 and L.lid(9.2) == 0.0)
	UI.motion_still = false
	# zeichnen (ohne Bild: nur keine Fehler) - das Logo in der Grösse der Stellen und die Sprechblase in allen Zuständen
	var box := Control.new()
	root.add_child(box)
	for s in [22, 30, 52]:
		var lg: Control = L.new()
		lg.custom_minimum_size = Vector2(s, s)
		lg.size = Vector2(s, s)
		box.add_child(lg)
	var cv := Control.new()
	cv.size = Vector2(120, 120)
	cv.draw.connect(func():
		for m in ["normal", "point", "think", "happy"]:
			I.blinki_bubble(cv, Vector2(10, 40), 60.0, m, 1.0)
			I.blinki(cv, Vector2(10, 40), 60.0, "watch" if m == "normal" else m, 0.0, 0.5))
	box.add_child(cv)
	_finish.call_deferred()


func _finish() -> void:
	for i in range(6):
		await process_frame
	if errs.is_empty():
		print("Symbol-Animation-Test OK")
		quit(0)
	else:
		push_error("Symbol-Animation-Test: " + "; ".join(errs))
		quit(1)
