extends Node
## «Kopf steuern» ohne MoveEye (Besitzer 12.11.2026): ist MoveEye NICHT verbunden, drehen die Pfeile, ⌂, das Ziehen im Bild
## und der Controller den Kopf des Simulators selbst - vorher gingen sie nur als Wunsch «look» an MoveEye (main.mw_look ->
## mw_cmd), und ohne Verbindung hörte niemand zu (das Licht ging schon: main.mw_light schaltet es dann selbst).
## Alle Wege laufen über main.mw_look (headpad.gd, padmap.gd, parcours.gd) - dort wird look() hier zuerst gefragt.
## Wie MoveEye es täte (nichts erfunden - Werte der Standardeinstellung von MoveEye):
##   Schritt in % des Drehbereichs wie move_camera (quelle/020: 0.5 … 25 %, servo_range 180° -> 1 % = 1.8°),
##   Grenzen pan_limit ± 90°, tilt_limit ± 60° (quelle/020 DEFAULTS; dazu wie immer die Kabel-Grenze weit.pan_clamp),
##   Tempo servo_vmax_pan 120°/s, servo_vmax_tilt 90°/s (quelle/072; ohne die Anfahr-Rampe des Planers).
## Der Kopf selbst folgt wie immer mw["servo"] (main._process: Servo-Modell, Störungen, Kameras) - hier wird nur der Winkel
## geschrieben, den sonst MoveEye schickt. Darum folgen die Bilder im Fenster und in «Kameras» von selbst.
## Wem der Kopf gehört:
##   MoveEye verbunden (Zustand jünger als 3 s) -> nur MoveEye. look() tut nichts, ein offenes eigenes Ziel wird verworfen.
##     Beim Verbinden ersetzt MoveEyes Zustand mw ganz: die Stellung von MoveEye gewinnt, der Kopf fährt dorthin.
##   Nicht verbunden -> hier. Nach dem Trennen geht es ohne Neustart von der letzten Stellung aus weiter.
##   Nie während einer Messung (main.measuring(), Nacht-Testlauf) und nie, wenn etwas anderes den Kopf dreht (head_owner:
##   Patrouille, Spiel, Trainingsbilder, Alarm-Rückblick).
## Test: werkzeuge/kopf_selbst_test.gd.

const PCT_DEG := 1.8                   # 1 % of the travel = 1.8° (MoveEye: servo_range 180)
const LIMIT := {"pan": 90.0, "tilt": 60.0}      # MoveEye DEFAULTS pan_limit / tilt_limit (± degrees from the middle)
const VMAX := {"pan": 120.0, "tilt": 90.0}      # MoveEye servo_vmax_pan / servo_vmax_tilt (degrees per second)
const CON_S := 3.0                     # MoveEye counts as connected while its state is younger (as headpad.gd, mw_light)

var main
var goal := {"pan": 0.0, "tilt": 0.0}
var active := false                    # a goal of our own is being approached


func mw_on() -> bool:
	return main.now() - float(main.mw_t) < CON_S


func allowed() -> bool:
	"""may the simulator turn the head itself right now?"""
	if mw_on() or main.measuring() or main.busy_with() == "Nacht-Testlauf":
		return false
	return str(main.head_owner()) == ""


func _take() -> void:
	"""take over from the last state: the angles as they are now, without the speed / goal MoveEye sent last"""
	var s: Dictionary = main.mw.get("servo", {})
	var neu := {"moving": false}
	for ax in ["pan", "tilt"]:
		neu[ax + "_deg"] = clampf(float(main._srv_ahead(s, ax)), -LIMIT[ax], LIMIT[ax])
		goal[ax] = neu[ax + "_deg"]
	main.mw["servo"] = neu


func look(dir: String, step := 3.0) -> bool:
	"""one step like MoveEye's move_camera; true = done here (nothing is sent to MoveEye)"""
	if not allowed():
		active = false
		return false
	if not dir in ["left", "right", "up", "down", "center"]:
		return false
	if not active:
		_take()
	var d: float = clampf(float(step), 0.5, 25.0) * PCT_DEG
	match dir:
		"left":
			goal["pan"] -= d
		"right":
			goal["pan"] += d
		"up":
			goal["tilt"] += d
		"down":
			goal["tilt"] -= d
		"center":
			goal["pan"] = 0.0
			goal["tilt"] = 0.0
	for ax in ["pan", "tilt"]:
		goal[ax] = clampf(goal[ax], -LIMIT[ax], LIMIT[ax])
	active = true
	return true


func _process(dt: float) -> void:
	if not active:
		return
	if not allowed():                                   # MoveEye is back / a measurement starts: hands off at once
		active = false
		if not mw_on() and main.mw.has("servo"):
			main.mw["servo"]["moving"] = false
		return
	var s: Dictionary = main.mw.get("servo", {})
	var moving := false
	for ax in ["pan", "tilt"]:
		var cur := float(s.get(ax + "_deg", 0.0))
		var nxt := move_toward(cur, goal[ax], VMAX[ax] * dt)
		s[ax + "_deg"] = nxt
		moving = moving or absf(goal[ax] - nxt) > 0.01
	s["moving"] = moving
	main.mw["servo"] = s
	active = moving
