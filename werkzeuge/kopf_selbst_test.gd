extends SceneTree
## Test «Kopf steuern ohne MoveEye» (scripts/kopf_selbst.gd) - ohne Bild, ohne Welt, mit einer Ersatz-Hauptszene:
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/kopf_selbst_test.gd"   (absoluter Pfad nötig)
## Nicht verbunden: Pfeile / ⌂ drehen den Kopf selbst (Schritt, Grenzen, Tempo wie MoveEye), nichts geht an MoveEye.
## Verbunden: die Pfeile drehen hier nichts, der Wunsch «look» geht wie bisher an MoveEye. Verbinden mitten in einer
## eigenen Bewegung: MoveEyes Stellung gewinnt, kein Hin und Her. Trennen: es geht ohne Neustart von dort weiter.
## Messung / Patrouille / Spiel: keine eigene Bewegung. Ende: «Kopf-selbst-Test OK» oder «SCRIPT ERROR: Kopf-selbst-Test: …».

const T = preload("res://scripts/i18n.gd")
var errs := []


func ok(what: String, cond: bool) -> void:
	if not cond:
		errs.append(what)


func _fake_main() -> Node:
	var s := GDScript.new()
	s.source_code = """extends Node
var t := 1000.0
var mw_t := -100.0
var mw := {"servo": {"pan_deg": 0.0, "tilt_deg": 0.0, "moving": false}}
var mw_cmd := {}
var mess := false
var busy := ""
var owner_ := ""
var kopf_selbst = null
func now() -> float:
	return t
func measuring() -> bool:
	return mess
func busy_with(_e := "") -> String:
	return busy
func head_owner() -> String:
	return owner_
func _srv_ahead(s: Dictionary, ax: String) -> float:      # as main.gd
	var deg := float(s.get(ax + "_deg", 0.0))
	if not s.has(ax + "_dps"):
		return deg
	var ahead := deg + float(s.get(ax + "_dps", 0.0)) * clampf(now() - mw_t, 0.0, 0.15)
	var goal := float(s.get(ax + "_goal", ahead))
	return clampf(ahead, minf(deg, goal), maxf(deg, goal))
func mw_look(dir: String, step := 3.0) -> void:           # as main.gd
	if kopf_selbst != null and kopf_selbst.look(dir, step):
		return
	mw_cmd = {"id": int(mw_cmd.get("id", 0)) + 1, "op": "look", "dir": dir, "step": step}
func on_state(d: Dictionary) -> void:                     # as main.gd: MoveEye's state replaces mw
	mw = d
	mw_t = now()
"""
	s.reload()
	var m := Node.new()
	m.set_script(s)
	return m


func _run(m, k, sek: float) -> void:
	"""Zeit vergehen lassen: 60 Bilder pro Sekunde"""
	var n := int(round(sek * 60.0))
	for i in range(n):
		m.t += 1.0 / 60.0
		k._process(1.0 / 60.0)


func _pan(m) -> float:
	return float(m.mw["servo"]["pan_deg"])


func _tilt(m) -> float:
	return float(m.mw["servo"]["tilt_deg"])


func _initialize() -> void:
	var K = load("res://scripts/kopf_selbst.gd")
	var m := _fake_main()
	root.add_child(m)
	var k = K.new()
	k.main = m
	m.kopf_selbst = k
	m.add_child(k)

	# 1. nicht verbunden: der Pfeil dreht den Kopf selbst
	ok("nicht verbunden: erlaubt", k.allowed() and not k.mw_on())
	m.mw_look("right", 2.5)
	ok("Pfeil rechts: nichts an MoveEye", m.mw_cmd.is_empty() and k.active)
	_run(m, k, 0.01)
	ok("Tempo: nach einem Bild höchstens 120°/s (%.2f°)" % _pan(m), _pan(m) > 0.0 and _pan(m) <= 120.0 / 60.0 + 0.001)
	_run(m, k, 0.5)
	ok("Pfeil rechts 2.5 %% = 4.5° wie MoveEye (%.2f°)" % _pan(m), absf(_pan(m) - 4.5) < 0.01 and not k.active and m.mw["servo"]["moving"] == false)
	m.mw_look("left", 2.5)
	m.mw_look("left", 2.5)
	_run(m, k, 0.5)
	ok("zweimal links: −4.5° (%.2f°)" % _pan(m), absf(_pan(m) + 4.5) < 0.01)
	m.mw_look("up", 3.0)
	_run(m, k, 0.5)
	ok("auf: Neigung +5.4° (%.2f°)" % _tilt(m), absf(_tilt(m) - 5.4) < 0.01 and absf(_pan(m) + 4.5) < 0.01)
	m.mw_look("down", 99.0)
	_run(m, k, 1.0)
	ok("Schritt höchstens 25 %% = 45° (%.2f°)" % _tilt(m), absf(_tilt(m) - (5.4 - 45.0)) < 0.01)
	# gehalten (headpad: alle 0.15 s ein Schritt von 2.5 %): läuft bis zur Grenze, nie darüber
	for i in range(80):
		m.mw_look("right", 2.5)
		m.mw_look("down", 2.5)
		_run(m, k, 0.15)
	_run(m, k, 2.0)
	ok("Grenzen wie MoveEye: Schwenken +90°, Neigen −60° (%.1f° / %.1f°)" % [_pan(m), _tilt(m)], absf(_pan(m) - 90.0) < 0.01 and absf(_tilt(m) + 60.0) < 0.01)
	for i in range(80):
		m.mw_look("left", 25.0)
		m.mw_look("up", 25.0)
	_run(m, k, 0.5)
	ok("Tempo Schwenken 120°/s, Neigen 90°/s (nach 0.5 s: %.1f° / %.1f°)" % [_pan(m), _tilt(m)], absf(_pan(m) - 30.0) < 0.5 and absf(_tilt(m) + 15.0) < 0.5 and m.mw["servo"]["moving"] == true)
	_run(m, k, 3.0)
	ok("andere Grenzen: −90° / +60°", absf(_pan(m) + 90.0) < 0.01 and absf(_tilt(m) - 60.0) < 0.01)
	m.mw_look("center")
	_run(m, k, 2.0)
	ok("⌂: zur Mitte", absf(_pan(m)) < 0.01 and absf(_tilt(m)) < 0.01 and not k.active)
	m.mw_look("unsinn", 5.0)
	ok("unbekannte Richtung: nichts", not k.active and absf(_pan(m)) < 0.01)

	# 2. verbunden: MoveEye gehört der Kopf - die Pfeile gehen wie bisher als Wunsch an MoveEye
	m.on_state({"servo": {"pan_deg": 20.0, "tilt_deg": -5.0, "moving": false}})
	ok("verbunden: nicht erlaubt", k.mw_on() and not k.allowed())
	m.mw_cmd = {}
	m.mw_look("right", 2.5)
	_run(m, k, 0.5)
	m.on_state({"servo": {"pan_deg": 20.0, "tilt_deg": -5.0, "moving": false}})
	ok("verbunden: der Pfeil dreht hier nichts, der Wunsch «look» geht an MoveEye", absf(_pan(m) - 20.0) < 0.001 and not k.active
			and str(m.mw_cmd.get("op", "")) == "look" and str(m.mw_cmd.get("dir", "")) == "right")

	# 3. Trennen: nach 3 s ohne Zustand geht es ohne Neustart von MoveEyes letzter Stellung aus weiter
	m.mw["servo"] = {"pan_deg": 20.0, "tilt_deg": -5.0, "pan_dps": 40.0, "pan_goal": 60.0, "moving": true}   # MoveEye war mitten in einer Fahrt
	m.t += 2.0
	m.mw_cmd = {}
	m.mw_look("left", 2.5)
	ok("2 s nach dem letzten Zustand: noch MoveEye", not k.active and str(m.mw_cmd.get("op", "")) == "look")
	m.t += 2.0
	var vor: float = m._srv_ahead(m.mw["servo"], "pan")
	m.mw_cmd = {}
	m.mw_look("left", 2.5)
	ok("getrennt: wieder selbst, ohne Sprung (von %.1f°), alte Fahrt von MoveEye vergessen" % vor, k.active and m.mw_cmd.is_empty()
			and absf(_pan(m) - vor) < 0.001 and not m.mw["servo"].has("pan_dps") and not m.mw["servo"].has("pan_goal"))
	_run(m, k, 0.5)
	ok("getrennt: Pfeil links wirkt (%.2f°)" % _pan(m), absf(_pan(m) - (vor - 4.5)) < 0.01)

	# 4. Verbinden mitten in einer eigenen Bewegung: MoveEyes Stellung gewinnt, kein Hin und Her
	m.mw_look("right", 25.0)
	_run(m, k, 0.1)
	ok("eigene Fahrt läuft", k.active)
	m.on_state({"servo": {"pan_deg": -30.0, "tilt_deg": 10.0, "moving": false}})
	_run(m, k, 1.0)
	ok("verbunden: MoveEyes Stellung bleibt (%.1f°), das eigene Ziel ist verworfen" % _pan(m), absf(_pan(m) + 30.0) < 0.001 and absf(_tilt(m) - 10.0) < 0.001 and not k.active)
	for i in range(30):                                   # MoveEye schickt weiter, der Kopf springt nie zurück
		m.on_state({"servo": {"pan_deg": -30.0 + i, "tilt_deg": 10.0, "moving": true}})
		_run(m, k, 0.1)
		if absf(_pan(m) - (-30.0 + i)) > 0.001:
			errs.append("verbunden: der Kopf weicht von MoveEye ab (%d)" % i)
			break
	m.t += 5.0
	m.mw_look("center")
	_run(m, k, 2.0)
	ok("wieder getrennt: ⌂ wirkt", absf(_pan(m)) < 0.01 and absf(_tilt(m)) < 0.01)

	# 5. nie während einer Messung, nie wenn etwas anderes den Kopf dreht
	for fall in [["mess", true, false], ["busy", "Nacht-Testlauf", ""], ["owner_", "Patrouille", ""], ["owner_", "Spiel (Wächter)", ""]]:
		m.set(fall[0], fall[1])
		m.mw_cmd = {}
		m.mw_look("right", 10.0)
		_run(m, k, 0.5)
		ok("%s = %s: keine eigene Bewegung" % [fall[0], fall[1]], absf(_pan(m)) < 0.001 and not k.active)
		m.set(fall[0], fall[2])
	m.mw_look("right", 25.0)
	_run(m, k, 0.1)
	var p0 := _pan(m)
	m.mess = true                                         # eine Messung beginnt mitten in der Fahrt: sofort Schluss
	_run(m, k, 1.0)
	ok("Messung beginnt während der Fahrt: der Kopf bleibt stehen (%.2f°)" % _pan(m), absf(_pan(m) - p0) < 0.001 and not k.active and m.mw["servo"]["moving"] == false)
	m.mess = false

	# 6. eingehängt und beschriftet
	var src := FileAccess.get_file_as_string("res://scripts/main.gd")
	var i0 := src.find("func mw_look(")
	ok("main.mw_look fragt zuerst kopf_selbst.look", i0 >= 0 and src.substr(i0, 500).find("kopf_selbst.look(dir, step)") > 0
			and src.substr(i0, 500).find("kopf_selbst.look(dir, step)") < src.substr(i0, 500).find("mw_cmd ="))
	ok("main_menues.gd legt kopf_selbst an", FileAccess.get_file_as_string("res://scripts/main_menues.gd").find("main.kopf_selbst = preload(\"res://scripts/kopf_selbst.gd\").new()") > 0)
	var hp := FileAccess.get_file_as_string("res://scripts/headpad.gd")
	ok("headpad.gd: der alte Hinweis ist weg", hp.find("zuerst «An MoveEye senden»") < 0 and hp.find("du steuerst den Kopf selbst") > 0)
	for de in ["MoveEye ist nicht verbunden – du steuerst den Kopf selbst.", "MoveEye ist nicht verbunden – während einer Messung steht der Kopf still.",
			"MoveEye ist nicht verbunden. Den Kopf steuert gerade: %s."]:
		for lg in ["en", "fr", "it", "rm"]:
			var x: String = T.lookup(de, lg)
			if x == "" or x == de:
				errs.append("Text ohne %s: %s" % [lg, de])
	if errs.is_empty():
		print("Kopf-selbst-Test OK")
		quit(0)
	else:
		printerr("SCRIPT ERROR: Kopf-selbst-Test (%d): " % errs.size() + " | ".join(errs.slice(0, 12)))
		quit(1)
