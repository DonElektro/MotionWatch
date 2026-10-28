extends Node
## 3D-3.80: the diary of the simulator - every visitor (person, animal, car) from coming to going: when, which scene,
## light, weather, how close to MoveEye, how long the head camera saw it well, when MoveEye noticed it (and how long
## that took), crouching / crawling, scared away. MoveEye fetches the finished visits (control action «visits») and
## shows them in its diary (tab «Simulator») with statistics.

var main
var live := {}                          # instance id -> record
var done: Array = []                    # finished records (the last 500)
var seq := 0
var _t := 0.0
const ANIMALS := ["fox", "deer", "boar", "cat", "dog", "badger", "hare", "hedgehog", "wolf", "marten", "squirrel", "cow", "sheep", "horse", "chamois", "ibex", "lynx"]


func add(v) -> void:
	if v == null or not is_instance_valid(v):
		return
	var k: String = str(v.kind)
	live[v.get_instance_id()] = {"v": v, "kind": k, "var": str(v.variant), "t_in": Time.get_unix_time_from_system(), "scene": str(main.scene),
			"dark": main.is_dark(), "weather": str(main.weather), "hour": snappedf(main.hour(), 0.01), "min_d": 999.0, "vis_s": 0.0, "first_vis": -1.0,
			"det": -1.0, "post": 0, "fled": false, "game": main.game != null and main.game.open and main.game.count() > 0}


func _process(dt: float) -> void:
	_t += dt
	if _t < 0.5:
		return
	var step := _t
	_t = 0.0
	var now := Time.get_unix_time_from_system()
	var head: Vector3 = main.head.global_position
	var fresh: bool = main.now() - main.mw_det_t < 3.0
	var persons: int = int(main.mw_det.get("persons", 0)) if fresh else 0
	var present: Array = main.mw_det.get("present", []) if fresh else []
	var keep: Array = main.testrun.truth_cams
	main.testrun.truth_cams = [0]
	for id in live.keys():
		var r: Dictionary = live[id]
		var v = r["v"]
		if not is_instance_valid(v) or v.done:
			_finish(id, now)
			continue
		r["min_d"] = minf(float(r["min_d"]), v.position.distance_to(head))
		r["post"] = maxi(int(r["post"]), int(v.ctl_posture) if v.controlled else (2 if float(v.prone) > 0.5 else (1 if float(v.crouch) > 0.5 else 0)))
		r["fled"] = bool(r["fled"]) or bool(v.fled)
		var seen: bool = v.kind != "car" and main.testrun.visible(v)
		if seen:
			r["vis_s"] = float(r["vis_s"]) + step
			if float(r["first_vis"]) < 0.0:
				r["first_vis"] = now
			if float(r["det"]) < 0.0:
				var hit: bool = persons > 0 if v.kind == "person" else (not present.is_empty() and v.kind in ANIMALS)
				if hit:
					r["det"] = now
	main.testrun.truth_cams = keep


func _finish(id, now: float) -> void:
	var r: Dictionary = live[id]
	live.erase(id)
	seq += 1
	var fv: float = r["first_vis"]
	var det: float = r["det"]
	var e := {"id": seq, "kind": r["kind"], "var": r["var"], "t_in": int(r["t_in"]), "t_out": int(now), "scene": r["scene"], "dark": r["dark"],
			"weather": r["weather"], "hour": r["hour"], "min_d": snappedf(float(r["min_d"]), 0.1), "vis_s": snappedf(float(r["vis_s"]), 0.1),
			"detected": det > 0.0, "detect_s": snappedf(det - fv, 0.1) if det > 0.0 and fv > 0.0 else -1.0, "post": r["post"], "fled": r["fled"],
			"game": r["game"], "mw": main.now() - main.mw_t < 5.0}
	done.append(e)
	if done.size() > 500:
		done.pop_front()


func since(i: int) -> Array:
	return done.filter(func(e): return int(e["id"]) > i)
