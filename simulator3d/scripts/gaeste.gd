extends Node
## «Gäste besuchen das Zelt» (gaeste-licht, Wunsch des Besitzers 21.11.2026): ein oder zwei Gäste kommen von weit her (aus dem
## Bild), gehen ohne Taschenlampe zum Ziel, bleiben eine Weile und gehen wieder hinaus - so lässt sich das Führungslicht von
## MoveEye («🔦 Gäste erwartet», Teil 639zzzzzg) sehen und testen.
##  Ziel   der Zustand «guests» von MoveEye (schnittstelle.json): target {kind, x, y} in m vom Gerät (x rechts, y geradeaus bei
##         Schwenk 0 - dieselbe Umrechnung wie Zonen / Wegpunkte im Zwilling, main.gd), sonst / bei «tent» das eigene Zelt
##         (main.obj["pir"]).
##  Von selbst  hat MoveEye «Gäste erwartet» an (guests.on, über die Verbindung), kommt der erste Besuch nach GAST_FIRST_S, danach
##         alle GAST_EVERY s (immer nur ein Besuch zur Zeit; nicht während Testlauf / Prüfstand / Messung). Schalter
##         «Gäste von selbst …» (Besuch → Verhalten, main.gaeste_auto).
##  Knopf  «Gäste besuchen das Zelt» (Besuch → Abläufe) - auch ohne MoveEye.
##  Die Gäste bleiben stehen, wenn das Licht angeht, nicht (sie erwarten es: Meta «gast», main.gd look_at_light).
## Steuerung: {"action": "gaeste", "do": "info" | "start" (n = 1 / 2, stay = s)} -> laufende Gäste, Ziel, Zelt in MoveEye-Metern.

const GAST_FIRST_S := 6.0
const GAST_EVERY := [110.0, 170.0]
const STAY := [70.0, 110.0]
const WALK := 1.05                     # m/s: gemütlich (zum Zelt eines Freundes)

var main
var running: Array = []
var next_t := -1.0
var was_on := false
var started := 0


func mw_on() -> bool:
	var g = main.mw.get("guests", {})
	return typeof(g) == TYPE_DICTIONARY and bool(g.get("on", false)) and main.now() - float(main.mw_t) < 10.0


func to_world(x: float, y: float) -> Vector3:
	"""MoveEye-Meter (x rechts, y geradeaus) -> Ort in der Szene (am Boden)"""
	var w: Vector3 = main.rig.global_position + main.rig.global_transform.basis * Vector3(x, 0, -y)
	return Vector3(w.x, main.ground_y(w.x, w.z), w.z)


func to_mw(p: Vector3) -> Array:
	var l: Vector3 = main.rig.global_transform.basis.inverse() * (p - main.rig.global_position)
	return [snappedf(l.x, 0.01), snappedf(-l.z, 0.01)]


func target_world() -> Vector3:
	var g = main.mw.get("guests", {})
	if typeof(g) == TYPE_DICTIONARY and typeof(g.get("target")) == TYPE_DICTIONARY:
		var t: Dictionary = g["target"]
		if str(t.get("kind", "")) != "tent":
			return to_world(float(t.get("x", 0.0)), float(t.get("y", 0.0)))
	return main.obj["pir"]


func start(n := 0, stay := 0.0) -> Dictionary:
	"""ein Besuch: von der Seite (aus dem Bild) zum Ziel, dort bleiben, auf der anderen Seite hinaus"""
	var tg := target_world()
	if n <= 0:
		n = 1 if randf() < 0.5 else 2
	if stay <= 0.0:
		stay = randf_range(STAY[0], STAY[1])
	var side := 1.0 if randf() < 0.5 else -1.0
	var away: Vector3 = (tg - main.rig.global_position)
	away.y = 0.0
	var fwd: Vector3 = away.normalized() if away.length() > 0.5 else Vector3(0, 0, -1)
	var lat := Vector3(-fwd.z, 0, fwd.x)
	var from: Vector3 = main.stories._ground(tg + lat * side * 24.0 + fwd * randf_range(4.0, 9.0))
	var out: Vector3 = main.stories._ground(tg - lat * side * 24.0 + fwd * randf_range(4.0, 9.0))
	var spot: Vector3 = main.stories._ground(main.free_spot(tg + lat * side * 1.3, 0.4, true))
	var a = main.spawn("person", from, spot)
	if a == null:
		return info()
	a.speed = WALK
	a.route = [[spot, stay, 0.0, tg], out]
	a.next_idle = main.now() + 9999.0
	a.set_meta("gast", true)
	running.append(a)
	if n >= 2:
		var b = main.spawn("person", from + lat * side * 0.9, spot)
		if b != null:
			b.leader = a
			b.speed = WALK * 1.3
			b.follow_off = Vector3(0.8, 0, 0.2)
			b.next_idle = main.now() + 9999.0
			b.set_meta("gast", true)
			running.append(b)
	started += 1
	main.start_info = preload("res://scripts/i18n.gd").t("Gäste kommen zum Zelt – ohne Taschenlampe, MoveEye leuchtet ihnen den Weg.")
	return info()


func _process(_dt: float) -> void:
	if main == null or not main.sim_active:
		return
	running = running.filter(func(v): return is_instance_valid(v) and not v.done)
	var on := mw_on()
	var t: float = main.now()
	if on and not was_on:
		next_t = t + GAST_FIRST_S
	was_on = on
	if on and main.gaeste_auto and running.is_empty() and next_t >= 0.0 and t >= next_t and main.busy_with() == "" and not main.measuring():
		start()
		next_t = t + randf_range(GAST_EVERY[0], GAST_EVERY[1])


func info() -> Dictionary:
	var tg := target_world()
	return {"ok": true, "running": running.filter(func(v): return is_instance_valid(v)).size(), "started": started, "mw_on": mw_on(),
			"auto": main.gaeste_auto, "target": [snappedf(tg.x, 0.01), snappedf(tg.z, 0.01)], "target_mw": to_mw(tg),
			"tent_mw": to_mw(main.obj["pir"]), "next_in": snappedf(maxf(0.0, next_t - main.now()), 0.1) if was_on else -1.0}


func control(d: Dictionary) -> Dictionary:
	match str(d.get("do", "info")):
		"start":
			return start(int(d.get("n", 0)), float(d.get("stay", 0.0)))
		_:
			return info()
