extends Node
## 3D-3.85 (Makeover 22 + 23): blinde Flecken / Nacht-Generalprobe. Eine Person steht nacheinander an Punkten rund um MoveEye
## (Richtung × Abstand, vom Kopf aus) und geht dort ein paar Schritte; der Simulator schaut, ob MoveEye sie erkennt
## (mw_det.persons) und ob sie überhaupt im Bild der Kopfkamera ist (testrun.visible). Andere Besucher kommen solange nicht.
## Steuerbefehl blindmap {do: start (az [°], dist [m], hour, walk) | info | stop}. MoveEye (143) zeichnet daraus die Karte.

var main
var busy := false
var pts: Array = []                   # [az, d]
var i := -1
var phase := ""                        # wait_clear | show
var t0 := 0.0
var cur = null
var res: Array = []
var result := {}
var _saved := {}
var walk := false

const SHOW_S := 6.0


func start(d: Dictionary) -> Dictionary:
	if busy:
		return {"ok": false, "error": "already running"}
	var _b: String = main.busy_with()
	if _b != "":
		return {"ok": false, "error": "busy: " + _b}
	pts = []
	var azs = d.get("az", [-60, -30, 0, 30, 60])
	var ds = d.get("dist", [5, 10, 15, 20, 25])
	for dd in ds:
		for a in azs:
			pts.append([float(a), float(dd)])
	walk = bool(d.get("walk", false))
	_saved = {"auto": main.auto_visitors, "hour": main.hour()}
	main.auto_visitors = false
	if d.has("hour"):
		main.set_hour(float(d["hour"]))
	for v in main.visitors.get_children():
		v.queue_free()
	res = []
	result = {}
	i = -1
	busy = true
	_next()
	return {"ok": true, "n": pts.size()}


func stop() -> void:
	if not busy:
		return
	_end()


func _next() -> void:
	if cur != null and is_instance_valid(cur):
		cur.queue_free()
	cur = null
	i += 1
	if i >= pts.size():
		_end()
		return
	phase = "wait_clear"
	t0 = main.now()


func _process(_dt: float) -> void:
	if not busy:
		return
	var t: float = main.now()
	if phase == "wait_clear":                           # MoveEye has forgotten the last one (or 5 s)
		if int(main.mw_det.get("persons", 0)) == 0 or t - t0 > 5.0:
			var f: Vector3 = -(main.cams[0] as Camera3D).global_transform.basis.z
			var az: float = rad_to_deg(atan2(f.x, -f.z)) + float(pts[i][0])          # relative to where the head looks now
			var dd: float = float(pts[i][1])
			var c: Vector3 = main.rig.global_position + main.pos_of(az, dd)
			var side: Vector3 = main.pos_of(az + 90.0, 1.0)
			var a: Vector3 = c - side * (2.5 if walk else 1.8)
			var b: Vector3 = c + side * (2.5 if walk else 1.8)
			cur = main.spawn("person", Vector3(a.x, 0, a.z), Vector3(b.x, 0, b.z))
			res.append({"az": pts[i][0], "d": pts[i][1], "inview": false, "found": false})
			phase = "show"
			t0 = t
	elif phase == "show":
		var r: Dictionary = res[-1]
		if cur != null and is_instance_valid(cur):                 # in the picture of the head camera and not hidden
			var cam: Camera3D = main.cams[0]
			var pp: Vector3 = cur.global_position + Vector3(0, 1.0, 0)
			if cam.is_position_in_frustum(pp) and main.line_free(cam.global_position, pp):
				r["inview"] = true
		if main.now() - main.mw_det_t < 2.0 and int(main.mw_det.get("persons", 0)) > 0 and t - t0 > 0.5:
			r["found"] = true
			r["inview"] = true
		if t - t0 > SHOW_S or (r["found"] and t - t0 > 2.0):
			_next()


func _end() -> void:
	if cur != null and is_instance_valid(cur):
		cur.queue_free()
	cur = null
	busy = false
	main.auto_visitors = bool(_saved.get("auto", true))
	if _saved.has("hour"):
		main.set_hour(float(_saved["hour"]))
	var found := res.filter(func(r): return r["found"])
	var mx := 0.0
	for r in found:
		mx = maxf(mx, float(r["d"]))
	result = {"points": res, "found": found.size(), "inview": res.filter(func(r): return r["inview"]).size(), "n": res.size(),
			"max_found": mx if mx > 0.0 else null}
	main.start_info = "Blinde Flecken: %d von %d Stellen erkannt" % [found.size(), res.size()]


func info() -> Dictionary:
	return {"ok": true, "busy": busy, "prog": "%d/%d" % [maxi(0, i + 1), pts.size()] if busy else "", "result": result}
