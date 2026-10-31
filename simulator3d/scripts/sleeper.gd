extends Node
## 3D-3.96: the person in the bed of the bedroom scene - to test the wake-up alarm of MoveEye 2.98.9 (gestures at the
## sleeping place). States: sleep (breathes, turns over now and then), wave (raises the arm and waves), sit (sits up),
## up (sits up, gets out of bed and walks to the door), gone. «auto» reacts to the alarm of MoveEye like a person:
## the first time it rings it waves (snooze), the next time it gets up. Warm in the thermal picture.
## Steuerbefehl: {"action": "sleeper", "do": "sleep" | "wave" | "sit" | "up" | "turn" | "auto" | "info"}

var main
var root: Node3D            # below the bed (freed with the scene)
var upper: Node3D           # turns at the hip when sitting up
var arm: Node3D             # shoulder joint
var blanket: Node3D
var legs: Node3D
var state := "sleep"
var auto := true
var t0 := 0.0
var _turn_t := 0.0
var _next_turn := 0.0
var _ring_seen := 0.0
var _plan := ""
var _snoozes_seen := 0
var _walk_from := Vector3.ZERO


func place(bed: Node3D) -> void:
	"""build the sleeper into the bed (bed: head end at local +x, the mattress top at y 0.6)"""
	root = Node3D.new()
	bed.add_child(root)
	var skin := Color(0.85, 0.66, 0.55)
	var shirt := Color(0.3, 0.45, 0.7)
	blanket = Node3D.new()
	root.add_child(blanket)
	main.add_mesh(blanket, main.box(1.35, 0.22, 1.25), Vector3(-0.3, 0.66, 0), main.mat(Color(0.55, 0.62, 0.78)), preload("res://scripts/waerme.gd").T("bed_blanket_person"))   # 3D-4.26: was 31 °C
	upper = Node3D.new()                                   # hip joint
	upper.position = Vector3(0.1, 0.66, 0.0)
	root.add_child(upper)
	main.add_mesh(upper, main.box(0.6, 0.22, 0.42), Vector3(0.3, 0.02, 0), main.mat(shirt), 33.0)            # chest
	var hs := SphereMesh.new()
	hs.radius = 0.12
	hs.height = 0.24
	main.add_mesh(upper, hs, Vector3(0.74, 0.08, 0), main.mat(skin), 36.0)                                   # head on the pillow
	var hair := SphereMesh.new()
	hair.radius = 0.125
	hair.height = 0.2
	main.add_mesh(upper, hair, Vector3(0.79, 0.1, 0), main.mat(Color(0.35, 0.22, 0.12)), 34.0)
	arm = Node3D.new()                                     # shoulder (the side to the camera)
	arm.position = Vector3(0.52, 0.04, 0.24)
	upper.add_child(arm)
	main.add_mesh(arm, main.box(0.48, 0.09, 0.09), Vector3(-0.24, 0, 0), main.mat(shirt), 33.0)              # arm along the body
	main.add_mesh(arm, main.box(0.1, 0.06, 0.1), Vector3(-0.52, 0, 0), main.mat(skin), 35.0)                 # hand
	legs = Node3D.new()                                    # only seen when the person stands up
	legs.position = Vector3(0.1, 0.66, 0.0)
	root.add_child(legs)
	for zz in [-0.1, 0.1]:
		main.add_mesh(legs, main.box(0.14, 0.85, 0.16), Vector3(0, -0.43, zz), main.mat(Color(0.2, 0.22, 0.3)), 31.0)
	legs.visible = false
	root.visible = true
	set_state("sleep")


func ok() -> bool:
	return root != null and is_instance_valid(root)


func set_state(s: String) -> void:
	state = s
	t0 = main.now()
	if not ok():
		return
	if s == "sleep":
		root.visible = true
		root.position = Vector3.ZERO
		root.rotation = Vector3.ZERO
		upper.rotation = Vector3.ZERO
		arm.rotation = Vector3.ZERO
		blanket.visible = true
		if legs != null:
			legs.visible = false
		_next_turn = main.now() + randf_range(40.0, 120.0)


func command(d: Dictionary) -> Dictionary:
	var w := str(d.get("do", "info"))
	if w == "auto":
		auto = bool(d.get("on", true))
	elif w in ["sleep", "wave", "sit", "up", "turn"]:
		if w == "turn":
			_turn_t = main.now()
		else:
			set_state(w)
	return {"ok": ok(), "state": state, "auto": auto, "scene": main.scene, "wake": main.mw.get("wake", {}), "mw_age": snappedf(main.now() - main.mw_t, 0.1), "ring_seen": _ring_seen, "plan": _plan, "t": main.now(), "frames": _frames}


var _frames := 0


func _process(_dt: float) -> void:
	_frames += 1
	if not ok() or main.scene != "schlafzimmer":
		return
	var t: float = main.now()
	var wk: Dictionary = main.mw.get("wake", {}) if typeof(main.mw.get("wake", {})) == TYPE_DICTIONARY else {}
	var ring: bool = str(wk.get("state", "")) == "ring" and t - main.mw_t < 5.0
	if auto and wk.has("state"):                             # (some answers of MoveEye come without the alarm: ignore those)
		_auto(t, ring, int(wk.get("snoozes", 0)), float(wk.get("t0", 0.0)))
	var k := t - t0                                          # after _auto: it may just have started a new state
	match state:
		"sleep":
			blanket.scale.y = 1.0 + 0.012 * sin(t * 1.6)           # breathing (a few mm, like real)
			if t >= _next_turn and not ring:
				_turn_t = t
				_next_turn = t + randf_range(60.0, 180.0)
			var tk := t - _turn_t
			root.rotation.x = 0.25 * sin(clampf(tk / 1.4, 0.0, 1.0) * PI) if tk < 1.4 else 0.0     # turns over: a short big movement
		"wave":
			arm.rotation.z = lerpf(0.0, -2.0, clampf(k / 0.6, 0.0, 1.0))                           # arm up
			arm.rotation.y = 0.55 * sin(k * TAU * 1.3) if k > 0.6 else 0.0                        # to and fro
			if k > 4.5:
				set_state("sleep")
		"sit":
			upper.rotation.z = lerpf(0.0, 1.3, clampf(k / 1.5, 0.0, 1.0))
			arm.rotation.z = 0.0
		"up":
			upper.rotation.z = lerpf(0.0, PI / 2, clampf(k / 1.2, 0.0, 1.0))                     # sits up
			if k > 1.2:                                                                           # out of bed on the side of the camera
				var s := clampf((k - 1.2) / 1.5, 0.0, 1.0)
				blanket.visible = false
				legs.visible = true
				root.position = Vector3(-0.3 * s, 0.24 * s, 1.1 * s)
			if k > 2.7:                                                                           # walks to the door
				var w := clampf((k - 2.7) / 3.5, 0.0, 1.0)
				var a2 := Vector3(-0.3, 0.24, 1.1)
				var b2 := Vector3(-1.5, 0.24, 1.2)
				var c2 := Vector3(-3.7, 0.24, -1.6)
				root.position = a2.lerp(b2, clampf(w * 2.0, 0.0, 1.0)) if w < 0.5 else b2.lerp(c2, (w - 0.5) * 2.0)
				legs.rotation.z = 0.35 * sin(k * 7.0)
			if k > 6.5:
				root.visible = false
				state = "gone"
				t0 = t
		"gone":
			if k > 90.0 and not ring:
				set_state("sleep")                                                               # back in bed for the next test


var _ring_id := 0.0


func _auto(t: float, ring: bool, snoozes: int, ring_id: float) -> void:
	if ring and ring_id != _ring_id:                         # a new ring of MoveEye (each one has its own start time)
		_ring_id = ring_id
		_ring_seen = t
		_plan = "wave" if snoozes < 1 else "up"
	if not ring:
		_plan = ""
		return
	if state == "sleep" and _plan != "" and t - _ring_seen > randf_range(5.0, 9.0):
		set_state(_plan)
		_plan = ""
