extends RefCounted
## Entwicklertool · Kamera für Sprung und Kontaktbogen (K1, 31.10.2026). Vorher übernahm devtool.view_at() die Blickrichtung
## des vorherigen Bilds und prüfte nur die Bodenhöhe am Kamerapunkt - im steilen Bergtal stand die Kamera so im Hang, im Wasser,
## in der Schlucht oder hinter einem Baum (Kontaktbogen-Prüfung REAL_KONTAKT.md: 55 Fotos). Jetzt:
##   * Ziel = Ortsmitte (bzw. Fokuspunkt) auf Gelände- oder Wasserhöhe + 1.2 m; Kamera mindestens in Augenhöhe (1.7 m) über
##     Gelände und Wasser an ihrem eigenen Punkt; Abstand nach dem Radius des Orts (devtool._dist); liegt die Ortsmitte im See,
##     steht die Kamera am Ufer (Abstand bis zum Ufer + Rand).
##   * Viele Kandidaten (12 Richtungen × 3 Abstände × 3 Höhen; Lite 8 × 3 × 2), jeder wird bewertet: freie Sicht zur Mitte
##     (Gelände + Dinge), Kamera nicht in einem Ding, Bildrand nicht voller Hang/Baum/Wasser direkt vor der Linse
##     («Füllstrahlen» durch das Bild), hinter dem Ort Weite statt Hang (obere Bildhälfte), offener Himmel (keine Schlucht),
##     nicht zu steil nach unten/oben, bevorzugte
##     Blickrichtung (Bergtal: Aussichtspunkte und Schlafplätze haben eine eigene), sonst leicht die vorherige Richtung.
##     Die besten 8 werden genau geprüft, der beste genommen. Sind alle schlecht (Mulde, Schlucht): nochmals höher und weiter weg.
##   * Schluchten, Höhlen, Bunker, Wasserfälle (Kennzeichen im Namen, DEEP): auch höhere Kamerapunkte (über dem Rand) und
##     der Himmel zählt doppelt - sonst ist das Bild fast schwarz.
##   * Räume (… (innen), bergtal_orte.gd INSIDE): der Punkt der Liste wird leicht verschoben (vor/seitlich), wenn ein Ding
##     (Türblatt, Pfosten, Seilwinde) direkt vor der Linse steht.
## «Raycast»: die Welt hat keine Physik-Körper (kein StaticBody3D), darum eigene Strahlen: Gelände per main.ground_y in
## Schritten, Wasser (Bergtal-Seen, Ferienpark-See), Dinge per RenderingServer.instances_cull_aabb (die Hüllquader der
## sichtbaren Teile und der MultiMesh-Bäume/-Felsen in der Nähe; sehr grosse Teile wie Gelände-Stücke, Seen, Strassen und
## sehr flache wie Gras zählen nicht).
## Lite: _lite() - weniger Kandidaten und Strahlen.

const Bt = preload("res://scripts/bergtal.gd")
const Orte = preload("res://scripts/bergtal_orte.gd")

const EYE := 1.7                       # m: eye height over ground / water
const TGT_H := 1.2                     # m: the point looked at above the ground of the place
const CELL := 8.0                      # m: grid of the box lookup
# places whose front looks one way (degrees, 0 = north, like VIEWPOINTS): the camera stands in front of it
const LOOK := {"bergtal.ort.fort_chruezli_bunker": 90.0}     # bunker front faces west (bib_berg _b_bunker +z, turned -90°)
const DEEP := ["schlucht", "schlund", "höhle", "hoehle", "spalt", "bunker", "werk", "wasserfall", "gumpen", "fall "]

var main
var _boxes: Array = []                 # [AABB] in world coordinates
var _hash := {}                        # Vector2i -> [index]
var _bt = null                         # bergtal.gd while it is loaded
var _fp_wy := -INF                     # Ferienpark: the water level (world)
var last := {}                         # the last choice (for /control "info" and tests)
var alts: Array = []                   # the next best cameras [Transform3D] (Kontaktbogen: tries them when the picture is dark/plain)


func _init(m) -> void:
	main = m


static func _lite() -> bool:
	return Engine.has_meta("lite") and bool(Engine.get_meta("lite"))


# =============================================================================================================================
# ground, water, things
# =============================================================================================================================
func _setup() -> void:
	_bt = null
	_fp_wy = -INF
	var d: Dictionary = main.scenes.data if main.scenes != null else {}
	var bt = d.get("bergtal")
	if bt != null and bt.get("tal") != null and is_instance_valid(bt.tal) and bt.tal.is_inside_tree():
		_bt = bt
	var fp = d.get("ferienpark")
	if fp != null and fp.get("park") != null and is_instance_valid(fp.park) and fp.park.is_inside_tree():
		_fp_wy = (fp.park.transform * Vector3.ZERO).y       # the lake of the park: park height 0


func water_y(x: float, z: float) -> float:
	"""the water surface at x, z (world) or -INF"""
	if _bt != null:
		var q: Vector3 = _bt.V(Vector3(x, 0, z))
		for lk in Bt.LAKES:
			if Bt._ell(Vector2(q.x, q.z), lk) < 1.02:
				return (_bt.W(Vector3(q.x, Bt.level_of(lk), q.z)) as Vector3).y
	elif _fp_wy > -INF and main.ground_y(x, z) < _fp_wy:
		return _fp_wy
	return -INF


func surf(x: float, z: float) -> float:
	return maxf(main.ground_y(x, z), water_y(x, z))


func _prep(c: Vector3, R: float) -> void:
	"""the boxes of the visible things within R of c (world)"""
	_boxes.clear()
	_hash.clear()
	var cam: Camera3D = main.view_cam
	if cam == null or cam.get_world_3d() == null:
		return
	var area := AABB(c - Vector3(R, 80.0, R), Vector3(2.0 * R, 200.0, 2.0 * R))
	var c2 := Vector2(c.x, c.z)
	for id in RenderingServer.instances_cull_aabb(area, cam.get_world_3d().scenario):
		var o = instance_from_id(id)
		if not (o is GeometryInstance3D) or (int(o.layers) & 1) == 0 or not o.is_visible_in_tree():
			continue
		if o.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:
			continue
		if o is MultiMeshInstance3D:
			var mm: MultiMesh = o.multimesh
			if mm == null or mm.mesh == null:
				continue
			var la: AABB = mm.mesh.get_aabb()
			if la.size.y < 0.6 or la.size.x > 40.0 or la.size.z > 40.0:
				continue                                     # grass, flowers - or a big flat thing
			var gt: Transform3D = o.global_transform
			var n: int = mm.instance_count if mm.visible_instance_count < 0 else mini(mm.instance_count, mm.visible_instance_count)
			for i in n:
				var t: Transform3D = gt * mm.get_instance_transform(i)
				if Vector2(t.origin.x, t.origin.z).distance_to(c2) > R:
					continue
				_add(t * la)
				if _boxes.size() > 6000:
					return
		elif o is MeshInstance3D:
			if o.mesh == null:
				continue
			var a: AABB = (o as MeshInstance3D).global_transform * (o as MeshInstance3D).get_aabb()
			var big := maxf(a.size.x, a.size.z)
			if big > 60.0 or a.size.y < 0.5 or a.size.y > 70.0 or (big > 20.0 and a.size.y < 0.2 * big):
				continue                                     # ground pieces, lakes, roads, paths (long and flat); tall rock faces
			var mat = o.material_override
			if mat is BaseMaterial3D and (mat as BaseMaterial3D).transparency != BaseMaterial3D.TRANSPARENCY_DISABLED:
				continue                                     # glass, water, smoke: one sees through
			_add(a)


func _add(a: AABB) -> void:
	var k := _boxes.size()
	_boxes.append(a)
	var x0 := int(floor(a.position.x / CELL))
	var x1 := int(floor(a.end.x / CELL))
	var z0 := int(floor(a.position.z / CELL))
	var z1 := int(floor(a.end.z / CELL))
	for x in range(x0, x1 + 1):
		for z in range(z0, z1 + 1):
			var key := Vector2i(x, z)
			if not _hash.has(key):
				_hash[key] = []
			_hash[key].append(k)


func _box_hit(a: Vector3, b: Vector3, skip_inside := true) -> float:
	"""the first thing on the segment a-b: distance from a (INF = none). Boxes round a do not count (skip_inside)."""
	var seg := Vector2(b.x - a.x, b.z - a.z)
	var n := int(ceil(seg.length() / (CELL * 0.5))) + 1
	var seen := {}
	var best := INF
	for i in n + 1:
		var f := float(i) / float(n)
		var key := Vector2i(int(floor((a.x + seg.x * f) / CELL)), int(floor((a.z + seg.y * f) / CELL)))
		for k in _hash.get(key, []):
			if seen.has(k):
				continue
			seen[k] = true
			var bx: AABB = _boxes[k]
			if skip_inside and bx.has_point(a):
				continue
			var hp = bx.intersects_segment(a, b)
			if hp != null:
				best = minf(best, a.distance_to(hp))
	return best


func _ground_hit(a: Vector3, b: Vector3, water := true) -> float:
	"""where the segment a-b goes into the ground (or water): distance from a (INF = not)"""
	var L := a.distance_to(b)
	if L < 0.01:
		return INF
	var step := clampf(L / 40.0, 0.6, 3.0)
	var t := step * 0.5
	while t <= L:
		var p := a.lerp(b, t / L)
		var h: float = main.ground_y(p.x, p.z)
		if water:
			h = maxf(h, water_y(p.x, p.z))
		if p.y < h:
			return t
		t += step
	return INF


func _hit(a: Vector3, b: Vector3) -> float:
	return minf(_ground_hit(a, b), _box_hit(a, b))


func _inside(p: Vector3, small_only := false) -> bool:
	var key := Vector2i(int(floor(p.x / CELL)), int(floor(p.z / CELL)))
	for k in _hash.get(key, []):
		var bx: AABB = _boxes[k]
		if small_only and (bx.size.x > 3.0 or bx.size.z > 3.0):
			continue                                         # (the room round the camera)
		if bx.grow(0.25).has_point(p):
			return true
	return false


# =============================================================================================================================
# the choice
# =============================================================================================================================
static func is_deep(e: Dictionary) -> bool:
	var nm := str(e.get("name", "")).to_lower() + " " + str(e.get("id", "")).to_lower()
	for w in DEEP:
		if nm.find(w) >= 0:
			return true
	return false


func pref_dir(e: Dictionary, frame) -> Vector3:
	"""the direction the place wants to be seen in (world, flat) or ZERO: Bergtal viewpoints and sleeping spots"""
	if not (frame is Transform3D):
		return Vector3.ZERO
	var a = null
	var id := str(e.get("id", ""))
	if LOOK.has(id):
		a = float(LOOK[id])
	elif id.begins_with("bergtal.aussicht."):
		for vp in Bt.VIEWPOINTS:
			if "bergtal.aussicht." + str(vp[0]) == id:
				a = float(vp[6])
	elif id.begins_with("bergtal.ort."):                    # a place on a viewpoint (Gratspitz): like the viewpoint
		for vp in Bt.VIEWPOINTS:
			var q := Vector2(float(e.get("x", 0.0)), float(e.get("z", 0.0)))
			if Bt.vp_xz(vp).distance_to(q) < 20.0 or Vector2(float(vp[3]), float(vp[4])).distance_to(q) < 20.0:
				a = float(vp[6])
	elif id.begins_with("bergtal.schlafplatz."):
		var sp = Bt.SPOTS.get(id.trim_prefix("bergtal.schlafplatz."))
		if sp is Array and sp.size() > 3:
			a = float(sp[3])
	if a == null:
		return Vector3.ZERO
	var r := deg_to_rad(float(a))                            # 0 = north (-z), 90 = east (+x)
	var w: Vector3 = (frame as Transform3D).basis * Vector3(sin(r), 0, -cos(r))
	w.y = 0.0
	return w.normalized() if w.length() > 0.01 else Vector3.ZERO


func _frust(xf: Transform3D, u: float, v: float) -> Vector3:
	var fov: float = deg_to_rad(main.view_cam.fov if main.view_cam != null else 70.0)
	var tv := tan(fov * 0.5)
	var th := tv * 16.0 / 9.0
	return (-xf.basis.z + xf.basis.x * (u * th) + xf.basis.y * (v * tv)).normalized()


const BACK := [[-0.7, 0.0], [0.0, 0.0], [0.7, 0.0], [-0.6, 0.35], [0.0, 0.35], [0.6, 0.35], [-0.5, 0.7], [0.0, 0.7], [0.5, 0.7]]
const BACK_Q := [[-0.6, 0.35], [0.0, 0.35], [0.6, 0.35]]
const FILL := [[-0.8, -0.65, 0.6], [0.0, -0.65, 0.8], [0.8, -0.65, 0.6], [-0.85, 0.0, 1.0], [-0.45, 0.0, 1.2], [0.45, 0.0, 1.2],
		[0.85, 0.0, 1.0], [-0.8, 0.6, 0.8], [0.0, 0.6, 1.0], [0.8, 0.6, 0.8], [-0.45, 0.3, 1.0], [0.45, 0.3, 1.0]]


var pref_w := 25.0


func _score(cam: Vector3, tgt: Vector3, d0: float, r: float, pref: Vector3, prev: Vector3, deep: bool, full: bool) -> Dictionary:
	var why := {}
	var s := 0.0
	var L := cam.distance_to(tgt)
	var xf := Transform3D(Basis(), cam).looking_at(tgt, Vector3.UP)
	var allow := clampf(r * 0.35, 1.5, 8.0)                  # the thing at the place itself may be hit near its centre
	# the centre: free?
	var h := _hit(cam, tgt)
	if h < L - allow:
		s += 100.0
		why["mitte"] = snappedf(h, 0.1)
	if _inside(cam):
		s += 200.0
		why["in_ding"] = true
	var wy := water_y(cam.x, cam.z)
	if wy > -INF:
		s += 12.0                                            # rather from the shore than over the water
		why["wasser"] = true
	# looking too steeply down / up
	var dir := (tgt - cam) / maxf(L, 0.01)
	var pitch := rad_to_deg(asin(clampf(dir.y, -1.0, 1.0)))
	var pmax := -55.0 if deep else -30.0                     # gorges, caves: from above is fine
	if pitch < pmax:
		s += (pmax - pitch) * 1.5
	if pitch > 8.0:
		s += (pitch - 8.0) * 2.5
	# the direction
	var fl := Vector3(dir.x, 0, dir.z).normalized()
	if pref != Vector3.ZERO:
		s += pref_w * (1.0 - fl.dot(pref)) * 0.5
	if prev != Vector3.ZERO:
		s += 3.0 * (1.0 - fl.dot(prev)) * 0.5
	s += 4.0 * absf(log(L / maxf(d0, 1.0)))                  # near the distance for the size of the place
	# the sky: no gorge, no cave of rock round the camera
	var nsky := 8 if full else 4
	var blocked := 0
	for i in nsky:
		var a := TAU * float(i) / float(nsky)
		var sd := Vector3(cos(a) * 0.906, 0.423, sin(a) * 0.906)   # 25° up
		if _ground_hit(cam, cam + sd * 35.0, false) < INF:
			blocked += 1
	var fsky := float(blocked) / float(nsky)
	s += fsky * (60.0 if deep else 30.0)
	why["himmel_zu"] = snappedf(fsky, 0.01)
	# behind the place: distance, not a hillside right behind it (the upper half of the picture)
	var far := minf(3.0 * L + 20.0, 220.0)
	var bw := 0.0
	var bn := 0.0
	for f in (BACK if full else BACK_Q):
		var rd := _frust(xf, float(f[0]), float(f[1]))
		bn += 1.0
		if _ground_hit(cam, cam + rd * far, false) < far:
			bw += 1.0
	var wall := bw / maxf(bn, 1.0)
	s += wall * 45.0
	why["wand"] = snappedf(wall, 0.01)
	if full:
		# more points of the place visible?
		var side := xf.basis.x * minf(r * 0.3, 6.0)
		for q in [tgt + side, tgt - side, tgt + Vector3(0, minf(r * 0.2, 3.0), 0)]:
			var hq := _hit(cam, q)
			if hq < cam.distance_to(q) - allow:
				s += 15.0
				why["neben"] = int(why.get("neben", 0)) + 1
		# the picture: nothing big right in front of the lens (hillside, tree, wall, water)
		var near := maxf(2.5, 0.4 * L)
		var wsum := 0.0
		var wnear := 0.0
		for f in FILL:
			var rd := _frust(xf, float(f[0]), float(f[1]))
			var hf := _hit(cam, cam + rd * near)
			wsum += float(f[2])
			if hf < near:
				wnear += float(f[2]) * (1.0 - hf / near * 0.5)
		var fill := wnear / wsum
		s += fill * 90.0
		why["voll"] = snappedf(fill, 0.01)
	return {"s": s, "xf": xf, "why": why}


func best_view(e: Dictionary, p: Vector3, d: float, prev_fwd: Vector3, frame = null) -> Dictionary:
	"""the best camera for the place e at p (world, on the ground) - {xf: Transform3D, score, why, n, ms}"""
	var t0 := Time.get_ticks_usec()
	_setup()
	var lite := _lite()
	var r := float(e.get("r", 10.0))
	var deep := is_deep(e)
	var tgt := Vector3(p.x, surf(p.x, p.z) + TGT_H, p.z)
	var in_lake := water_y(p.x, p.z) > -INF
	var pref := pref_dir(e, frame)
	var prev := Vector3(prev_fwd.x, 0, prev_fwd.z)
	prev = prev.normalized() if prev.length() > 0.01 else Vector3.ZERO
	var nyaw := 8 if lite else 12
	var a0 := atan2(prev.x, prev.z) if prev != Vector3.ZERO else 0.0
	if pref != Vector3.ZERO:
		a0 = atan2(pref.x, pref.z)
	var dists := [d, d * 0.65, d * 1.5]
	var elevs := [0.18, 0.4] if lite else [0.15, 0.35, 0.7]
	if deep:
		elevs.append(1.3)
		elevs.append(2.2)
	var aus := pref != Vector3.ZERO and (str(e.get("kind", "")) == "aussicht" or str(e.get("kind", "")) == "ort")
	if aus:                                                  # a viewpoint: just behind it, looking out like its bench
		dists = [7.0, 11.0, 16.0]
	elif LOOK.has(str(e.get("id", ""))) and pref != Vector3.ZERO:   # a front (bunker): close, in front of it
		tgt -= pref * 2.0
		dists = [10.0, 14.0, 20.0]
		elevs = [0.1, 0.25, 0.45]
	pref_w = 60.0 if (aus or LOOK.has(str(e.get("id", "")))) else 25.0
	var cands := []
	var far := 0.0
	for i in nyaw:
		var a := a0 + TAU * float(i) / float(nyaw)
		var fwd := Vector3(sin(a), 0, cos(a))                # the camera looks along fwd
		var dl: Array = dists
		if in_lake:                                          # the place is the lake: from the shore
			var t := 4.0
			while t < 320.0 and water_y(p.x - fwd.x * t, p.z - fwd.z * t) > -INF:
				t += 4.0
			dl = [t + 6.0, t + 18.0, maxf(d, t + 35.0)]
		for dd in dl:
			for ev in elevs:
				var c: Vector3 = tgt - fwd * float(dd)
				var y := tgt.y + float(dd) * float(ev)
				y = maxf(y, surf(c.x, c.z) + (EYE if water_y(c.x, c.z) == -INF else EYE + 2.5))
				c.y = y
				cands.append(c)
				far = maxf(far, float(dd))
	_prep(tgt, far + 15.0)
	var sc := []
	for c in cands:
		var q := _score(c, tgt, dists[0] if not in_lake else c.distance_to(tgt), r, pref, prev, deep, false)
		q["c"] = c
		sc.append(q)
	sc.sort_custom(func(x, y): return float(x["s"]) < float(y["s"]))
	var top: Dictionary = sc[0]
	var best_s := INF
	var fulls := []
	for q in sc.slice(0, 5 if lite else 8):
		var c: Vector3 = q["c"]
		var f := _score(c, tgt, dists[0] if not in_lake else c.distance_to(tgt), r, pref, prev, deep, true)
		f["c"] = c
		fulls.append(f)
		if float(f["s"]) < best_s:
			best_s = float(f["s"])
			top = f
	if best_s > 35.0 and not in_lake:                         # all bad (a hollow, a gorge): higher and further away
		if d * 2.5 + 15.0 > far + 15.0:
			_prep(tgt, d * 2.5 + 15.0)
		for i in nyaw:
			var a := a0 + TAU * float(i) / float(nyaw)
			var fwd := Vector3(sin(a), 0, cos(a))
			for dd in [d * 1.5, d * 2.5]:
				for ev in [0.9, 1.6]:
					var c: Vector3 = tgt - fwd * float(dd)
					c.y = maxf(tgt.y + float(dd) * float(ev), surf(c.x, c.z) + EYE)
					var f2 := _score(c, tgt, d, r, pref, prev, deep, true)
					f2["c"] = c
					fulls.append(f2)
					if float(f2["s"]) < best_s:
						best_s = float(f2["s"])
						top = f2
						top["c"] = c
	# the alternatives: the next best, and a view from high above (gorges: walls of rock are meshes the ground does not know)
	fulls.sort_custom(func(x, y): return float(x["s"]) < float(y["s"]))
	alts = []
	for f in fulls.slice(1, 5):
		if (f["c"] as Vector3).distance_to(top["c"]) > 3.0:
			alts.append(f["xf"])
	var bk := (top["c"] as Vector3) - tgt
	bk.y = 0.0
	bk = bk.normalized() if bk.length() > 0.01 else Vector3(0, 0, 1)
	for hv in [[1.2, 1.4], [1.6, 2.6], [0.0, 35.0], [0.0, 70.0]]:
		var c: Vector3 = tgt + bk * d * float(hv[0])
		var up := d * float(hv[1])
		if float(hv[0]) == 0.0:                              # from high above, a little behind (rock walls of gorges)
			up = float(hv[1])
			c = tgt + bk * up * 0.45
		c.y = maxf(tgt.y + up, surf(c.x, c.z) + EYE)
		alts.append(Transform3D(Basis(), c).looking_at(tgt, Vector3.UP))
	if aus:                                                  # a viewpoint: look out over it (its stored direction), not down at the bench
		var c: Vector3 = top["c"]
		var far_pt := tgt + pref * 80.0 + Vector3(0, -8.0, 0)
		top["xf"] = Transform3D(Basis(), c).looking_at(far_pt, Vector3.UP)
	var ms := (Time.get_ticks_usec() - t0) / 1000.0
	last = {"id": str(e.get("id", "")), "score": snappedf(float(top["s"]), 0.1), "why": top["why"], "n": cands.size(),
			"boxes": _boxes.size(), "ms": snappedf(ms, 0.1), "deep": deep, "lake": in_lake, "cam": _v(top["c"]), "tgt": _v(tgt)}
	return {"xf": top["xf"], "score": float(top["s"]), "why": top["why"], "n": cands.size(), "ms": ms}


func room_view(e: Dictionary):
	"""a room (bergtal_orte.gd INSIDE): the camera of the list, moved a little if a thing stands right in front of it.
	Transform3D or null (not a room of a loaded building)"""
	_setup()
	if _bt == null or _bt.get("orte") == null:
		return null
	var orte = _bt.orte
	for en in Orte.INSIDE:
		if str(en[0]) != str(e.get("name", "")) or not (orte._xf as Dictionary).has(str(en[1])):
			continue
		var bx: Transform3D = orte._xf[str(en[1])]
		var p: Vector3 = _bt.W(bx * Vector3(float(en[2]), float(en[3]), float(en[4])))
		var t: Vector3 = _bt.W(bx * Vector3(float(en[5]), float(en[6]), float(en[7])))
		_prep(p, 16.0)
		var fw := Vector3(t.x - p.x, 0, t.z - p.z)
		var span := fw.length()
		fw = fw.normalized() if span > 0.01 else Vector3(0, 0, -1)
		var sd := fw.cross(Vector3.UP)
		var best := INF
		var out := Transform3D(Basis(), p).looking_at(t, Vector3.UP)
		for along in [0.0, 0.5, 1.0, 1.6]:
			if along > span * 0.5:
				continue
			for side in [0.0, -0.5, 0.5, -1.0, 1.0]:
				for dy in [0.0, 0.25]:
					var c: Vector3 = p + fw * float(along) + sd * float(side) + Vector3(0, float(dy), 0)
					var xf := Transform3D(Basis(), c).looking_at(t, Vector3.UP)
					var s := absf(float(along)) * 3.0 + absf(float(side)) * 4.0 + float(dy) * 4.0
					if _inside(c, true):
						s += 100.0
					var L := c.distance_to(t)
					if _box_hit(c, t, true) < L - 1.0:
						s += 40.0
					var wsum := 0.0
					var wnear := 0.0
					for f in FILL:
						var rd := _frust(xf, float(f[0]), float(f[1]))
						var hf := _box_hit(c, c + rd * 1.3, true)
						wsum += float(f[2])
						if hf < 1.3:
							wnear += float(f[2])
					s += wnear / wsum * 80.0
					if s < best:
						best = s
						out = xf
		last = {"id": str(e.get("id", "")), "room": true, "score": snappedf(best, 0.1), "boxes": _boxes.size(), "cam": _v(out.origin)}
		return out
	return null


static func _v(p: Vector3) -> Array:
	return [snappedf(p.x, 0.01), snappedf(p.y, 0.01), snappedf(p.z, 0.01)]
