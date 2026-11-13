extends Node
## «Als Person gehen» (Besitzer 13.11.2026): beim Erkunden (explore.gd) und in der Geschichte «Die Karte des Grossvaters»
## geht man statt mit dem Mover als Person durch die Welt. Ein Kind von explore.gd («ex»), das den Rest dort lässt.
##   * Umschalten: Knopf «🚶 Person» / «🚜 Mover» (Erkunden-Leiste oben, Menü «Ansicht» der Leiste unten, Abenteuer-Spalte
##     unterwegs und am Nachtlager), Taste U, Controller: Select 1 s halten (Select ⏱ ist im Modus «sim» von padmap.gd frei;
##     kurz Select bleibt «Bilder / Ansichten tauschen»). Hinter dem Knopf läuft dasselbe set_person() von explore.gd.
##   * Steuerung genau wie der Mover (rover_pad.command): W A S D / Pfeile (W / ↑ vorwärts, S / ↓ zurück, A D / ← → drehen),
##     grüner Stick (Maus, Touch), rechter Stick des Controllers (padmap.drive_cmd). Rennen: Shift, oder Stick / grüne Kugel
##     ganz am Rand. Ansichten (V / R3): hinterher, Ich-Sicht (auf Augenhöhe), von oben; rechte Maustaste = umschauen.
##   * Die Figur ist der Wanderer von maggie_zwei.gd bzw. die Figur der Handy-Spieler (actor.gd, controlled): gleiche
##     Hindernis-Regeln (main.keep_out) und gleiche Höhe über dem Gelände (main.ground_y) wie alle Gehenden, Tempo 1,5 m/s,
##     rennen × 2,3 (actor.PLAYER_SPEED). Die Kameras von MoveEye sehen sie (wie einen Besucher).
##   * Zurück in den Mover: die Person bleibt stehen, wo sie ist (MoveEye kann sie sehen); die Ansicht geht zurück zum Mover,
##     der dort steht, wo man ihn gelassen hat - MoveEye fährt auf dem Mover mit, sein Bild springt also nicht. Wieder
##     «Person»: weiter an derselben Stelle. Erkunden beenden (Esc) = die Person geht weg.
##   * Nie während einer Messung (main.measuring(), Nacht-Testlauf), nicht beim Spiel am PC, nicht in einer Spielrunde ausser
##     «Zonen-Check» (frei bewegen, Mitspieler mit dem Handy bleiben dabei), nicht zu zweit im Abenteuer (eigene Wanderer) und
##     nicht in «Maggie» (eigene Figur): dann ist der Knopf weg und eine laufende Person wird wieder zum Mover (why_not).
## In der Geschichte (bergtal_abenteuer.gd, Schritte «Unterwegs» und «Nachtlager»): die Person zählt wie ein Wanderer zu zweit
##   (abenteuer_geheim.gd walkers(): Steinmännchen bis 3,5 m, Tagebuchblatt beim Licht bis 4 m) und wie der Mover für alles,
##   was die Welt am Spieler misst (main.walker_pos(): Aussichtspunkte und Feldstecher, Absturzkanten, Grat, «Hier
##   übernachten», Stirnlampe). Sie geht mit der Gruppe mit (die Tour läuft auf den Wanderwegen weiter) und darf sich bis
##   LEASH = 110 m entfernen - dieselbe Regel wie «gemeinsam» zu zweit (abenteuer_zweit.gd). Kraft, Zeit und Essen kommen
##   weiter von den Wegstücken: herumgehen kostet nichts extra (wie zu zweit), so bleibt die Geschichte gleich fair.
## Steuerbefehl (über explore): {"action": "explore", "person": true | false, "pwalk": [vor, drehen, Sekunden, rennen],
##   "pplace": [x, z] (Welt)} - Zustand in explore.state() unter «person».

const T = preload("res://scripts/i18n.gd")
const ActorS = preload("res://scripts/actor.gd")
const Figur = preload("res://scripts/figur.gd")
const Bt = preload("res://scripts/bergtal.gd")

const TURN := 2.4                    # rad/s: A / D drehen (der Mover dreht an Ort etwa gleich schnell)
const LEASH := 110.0                 # m: so weit von der Gruppe weg in der Geschichte (wie abenteuer_zweit.gd)
const EYE := 1.62                    # m: Augenhöhe für die Ich-Sicht
const BOUND := 180.0                 # m: ausserhalb des Bergtals so weit wie der Mover (main._drive)
const FULL := 0.95                   # Stick / grüne Kugel so weit draussen = rennen

var ex
var main
var active := false                  # die Person wird gesteuert (sonst steht sie, wo man sie gelassen hat)
var actor: Node3D = null
var yaw := 0.0                       # wohin die Person schaut / geht (wie rig.rotation.y beim Mover)
var cmd := Vector2.ZERO              # (vorwärts, rechts drehen) von rover_pad.command()
var run := false
var _scene := ""
var _anchor = null                   # Geschichte: wo die Gruppe zuletzt war (Tal)
var _test := {}                      # Tests: {"v": Vector2, "run": bool, "until": s}
var _far_t := -100.0


static func why_not(m) -> String:
	"""'' = hier darf man als Person gehen; sonst der Grund (der Knopf ist dann weg)"""
	if m == null:
		return "-"
	if m.measuring() or m.busy_with() == "Nacht-Testlauf":
		return "Messung läuft"
	if m.localplay != null and m.localplay.active:
		return "Spiel am PC"
	if m.game != null and bool(m.game.open) and str(m.game.round_state) in ["countdown", "play"] and str(m.game_mode) != "free":
		return "Spielrunde läuft"
	var ab = m.get("abenteuer")
	if ab != null and ab.get("zweit") != null and bool(ab.zweit.on):
		return "zu zweit unterwegs"
	var mg = m.get("maggie")
	if mg != null and is_instance_valid(mg) and bool(mg.get("running")):
		return "Maggie läuft"
	return ""


func _now() -> float:
	return main.now()


# ---- die Geschichte -------------------------------------------------------------------------------------------------------
func story():
	"""bergtal_abenteuer.gd, wenn die Person dort mitgeht (Unterwegs / Nachtlager im Bergtal), sonst null"""
	var ab = main.get("abenteuer")
	if ab == null or ab.R.is_empty() or main.scene != "bergtal" or ab.bt() == null:
		return null
	if not int(ab.step) in [4, 5]:
		return null
	return ab


func _anchor_of(ab) -> Vector2:
	if int(ab.step) == 5:
		return ab.R.get("camp_xz", ab.R["pos"])
	return ab.R["pos"]


func valley_pos():
	"""wo die Person im Tal steht (Vector2) - null ohne Bergtal oder ohne Person"""
	if actor == null or not is_instance_valid(actor):
		return null
	var b = main.scenes.data.get("bergtal", null) if main.scene == "bergtal" and main.scenes != null else null
	if b == null:
		return null
	var q: Vector3 = b.V(actor.global_position)
	return Vector2(q.x, q.z)


# ---- die Figur ------------------------------------------------------------------------------------------------------------
func _spawn_at() -> Vector3:
	var ab = story()
	if ab != null:
		var an := _anchor_of(ab)
		var q := an + Vector2(1.6, 2.0)                   # neben der Gruppe (wie Spieler 1 zu zweit)
		return ab.bt().WG(q.x, q.y, 0.0)
	var r: Node3D = main.rig
	var side: Vector3 = r.global_transform.basis.x
	var back: Vector3 = r.global_transform.basis.z
	var p: Vector3 = r.global_position + side * 1.4 + back * 0.6   # neben dem Mover
	var q2: Vector2 = main.keep_out(Vector2(p.x, p.z), 0.35, true)
	return Vector3(q2.x, main.ground_y(q2.x, q2.y), q2.y)


func _ensure() -> void:
	if actor != null and is_instance_valid(actor) and _scene == main.scene:
		return
	remove()
	var at := _spawn_at()
	var a = ActorS.new()
	a.controlled = true
	a.look = {"col": "red", "size": "", "build": "", "hat": "", "pack": true}
	a.player_color = Figur.LOOK_COLS["red"]
	a.name = "erkunden_person"
	main.add_child(a)
	yaw = main.rig.rotation.y if story() == null else yaw
	var fwd := Vector3(-sin(yaw), 0, -cos(yaw))
	a.setup(main, "person", at, at + fwd, 1.5)
	actor = a
	_scene = main.scene
	_anchor = null


func remove() -> void:
	if actor != null and is_instance_valid(actor):
		actor.queue_free()
	actor = null
	active = false
	_anchor = null


func set_active(v: bool) -> void:
	if v:
		_ensure()
		if actor != null:
			actor.frozen = false
	active = v
	cmd = Vector2.ZERO
	run = false
	if not v and actor != null and is_instance_valid(actor):
		actor.ctl_move = Vector2.ZERO
		actor.frozen = true                                 # bleibt stehen, wo sie ist


func place(p: Vector3) -> void:
	if actor == null or not is_instance_valid(actor):
		return
	var q: Vector2 = main.keep_out(Vector2(p.x, p.z), 0.35, true)
	actor.position = Vector3(q.x, main.ground_y(q.x, q.y), q.y)
	actor.cur_speed = 0.0
	_anchor = null


func test_walk(v: Vector2, secs: float, r: bool) -> void:
	_test = {"v": v, "run": r, "until": _now() + secs}


func speed_now() -> float:
	return float(actor.cur_speed) if actor != null and is_instance_valid(actor) else 0.0


func tick(dt: float) -> void:
	if actor == null or not is_instance_valid(actor):
		return
	if _scene != main.scene:                                # eine andere Szene: neu neben dem Mover
		_ensure()
	if not active:
		actor.frozen = true
		actor.ctl_move = Vector2.ZERO
		return
	actor.frozen = false
	var c := cmd
	var r := run
	if not _test.is_empty():
		if _now() < float(_test["until"]):
			c = _test["v"]
			r = bool(_test["run"])
		else:
			_test = {}
	c = c.limit_length(1.0)
	yaw = wrapf(yaw - c.y * TURN * dt, -PI, PI)
	var fwd := Vector2(-sin(yaw), -cos(yaw))
	actor.ctl_move = fwd * c.x * (0.6 if c.x < 0.0 else 1.0)   # zurück: etwas langsamer
	actor.ctl_run = r and c.x > 0.1
	if absf(c.x) < 0.08:                                    # an Ort drehen: der Körper dreht mit
		actor.heading = rotate_toward(float(actor.heading), yaw, 6.0 * dt)
		actor.rotation.y = actor.heading
	_bounds()


func _bounds() -> void:
	var ab = story()
	var p: Vector3 = actor.position
	if ab != null:                                          # mit der Gruppe mitgehen, höchstens LEASH weg
		var b = ab.bt()
		var an := _anchor_of(ab)
		var v3: Vector3 = b.V(p)
		var q := Vector2(v3.x, v3.z)
		var q0 := q
		if _anchor is Vector2 and an.distance_to(_anchor) > 0.001:
			q += an - (_anchor as Vector2)
		var off := q - an
		if off.length() > LEASH:
			off = off.normalized() * LEASH
			if _now() - _far_t > 8.0:
				_far_t = _now()
				main.start_info = T.t("Nicht weiter weg von der Gruppe (%d m)") % int(LEASH)
		q = an + off
		q = Vector2(clampf(q.x, Bt.LO + 30.0, -Bt.LO - 30.0), clampf(q.y, Bt.LO + 30.0, -Bt.LO - 30.0))
		_anchor = an
		if q.distance_to(q0) > 0.001:
			var w: Vector3 = b.WG(q.x, q.y, 0.0)
			actor.position = Vector3(w.x, main.ground_y(w.x, w.z), w.z)
		return
	_anchor = null
	if main.scene != "bergtal":
		var cx := clampf(p.x, -BOUND, BOUND)
		var cz := clampf(p.z, -BOUND, BOUND)
		if cx != p.x or cz != p.z:
			actor.position = Vector3(cx, main.ground_y(cx, cz), cz)


func state() -> Dictionary:
	var o := {"on": active, "why_not": why_not(main), "there": actor != null and is_instance_valid(actor)}
	if o["there"]:
		var p: Vector3 = actor.global_position
		o["x"] = snappedf(p.x, 0.01)
		o["y"] = snappedf(p.y, 0.01)
		o["z"] = snappedf(p.z, 0.01)
		o["speed"] = snappedf(speed_now(), 0.01)
		var vq = valley_pos()
		if vq is Vector2:
			o["tal"] = [snappedf(vq.x, 0.1), snappedf(vq.y, 0.1)]
	o["story"] = story() != null
	return o
