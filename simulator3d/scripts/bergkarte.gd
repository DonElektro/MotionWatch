extends Node
## «Bergtal-Karte» (Besitzer 21.11.2026): die Karte des Bergtals in MoveEye (/karte, Schalter «Schweiz / Bergtal», Teil
## 639zzzzzt) - hier der Teil des Simulators. Ein Kind von main (main.bkarte), ohne eigenes Bild.
##   * Daten für das Kartenpaket (werkzeuge/bergkarte/export.gd ruft die statischen Funktionen): alle Orte mit Art (Symbol),
##     die Wanderwege (gelb / rot / blau), Bäche, Seen, Strasse und die GEHEIMEN Orte (Abenteuer-Funde und Spoiler: die
##     versteckten Dinge aus VIGNETTES, der geheime See mit seinem Pfad, die Ziele der 5 Kapitel von «Die Karte des
##     Grossvaters»). Jeder geheime Ort nennt die Einträge des Entdeckungsbuchs (entdecken.gd) bzw. «abenteuer.kapitel.N»
##     (Kapitel erledigt, bergtal_abenteuer.gd P), die ihn «gefunden» machen. Das Ei des Bergtals (bergtal_ei.gd) steht nie
##     auf der Karte.
##   * world_reply «bkarte» (nur im Bergtal, sonst null) -> MoveEye 639zzzzzt: wo MoveEye steht und wohin der Kopf schaut,
##     die eigene Figur (Erkunden als Person) und der Mover, was MoveEye gerade erkennt (Tiere / Personen als Punkte: im Bild
##     der Kopfkamera UND von MoveEye gemeldet), welche geheimen Orte gefunden sind, die laufende Tour. Alles in Tal-Metern
##     (x = Osten, z = Süden, Mitte des Tals = 0 / 0) - nie echte Koordinaten.
##   * Steuerung {"action": "bkarte", "do": "info | tour | stop", "pts": [[x, z] …] (Tal-Meter), "name", "who": auto |
##     person | mover}: «Tour im Sim nachlaufen» - die Figur (Erkunden als Person; sonst der Mover) geht die Tour ab. Die
##     Figur startet am ersten Punkt; der Mover fährt nur innerhalb seines Bereichs (main._drive: ± 180 m um MoveEye) und hält
##     am Rand an. Eine Taste / ein Stick des Spielers beendet die Tour (er übernimmt), ebenso «Erkunden» beenden.
## Test: werkzeuge/bergkarte_test.gd (Paket = Simulator: Zahl der Orte, Höhen an Stichproben, geheime Orte, Steuerung).

const Bt = preload("res://scripts/bergtal.gd")
const T = preload("res://scripts/i18n.gd")
const AbD = preload("res://scripts/bergtal_abenteuer_daten.gd")

const VERSION := 1                          # the format of reply() / export (MoveEye 639zzzzzt BK_FORMAT)
# VIGNETTES that are no secret (the varied zones 17–28 are ordinary places; 2 has no own position)
const OPEN_VIGNETTES := [2, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
# vignette id -> the discovery ids (entdecken.gd) that make it «found»; default: «berg.» + id
const FOUND_IDS := {"flaschenpost_laterne": ["berg.flaschenpost", "berg.laterne"], "schmuggler": ["berg.schmugglerroute", "berg.schmugglerversteck"],
		"steinmann_wald": ["berg.steinmann_augen"], "sennerei": ["berg.sennerei_kaese"]}
const SECRET_TRAILS := {"Pfad zum geheimen See": ["berg.geheimer_see"]}   # trail name -> found ids
const SECRET_LAKES := {3: ["berg.geheimer_see"]}                          # index in Bt.LAKES -> found ids
const PERSON := ["person", "child", "jogger"]
const NOT_SEEN := ["car", "bike", "drone"]
const REACH := 2.2                          # m: a point of the tour counts as reached
const STUCK_S := 9.0                        # s without 1 m progress: on to the next point
const MAX_PTS := 600

# ---- the data of the map (static, also headless) -------------------------------------------------------------------------
static func kind_of(name: String) -> String:
	"""the symbol of a place (like the Swiss map): from its name"""
	var n := name.to_lower().replace("ü", "ue").replace("ä", "ae").replace("ö", "oe")   # (rules in ASCII: no texts to translate)
	var rules := [["innen", "innen"], ["biwak", "biwak"], ["hospiz", "hospiz"], ["kapelle", "kapelle"], ["fort ", "bunker"], ["bunker", "bunker"],
			["infanteriewerk", "bunker"], ["baracke", "ruine"], ["ruine", "ruine"], ["altstafel", "ruine"], ["seilbahn", "seilbahn"], ["parkplatz", "parkplatz"],
			["bruecke", "bruecke"], ["holzsteg", "bruecke"], ["wasserfall", "wasserfall"], ["fall", "wasserfall"], ["gletschertor", "gletscher"],
			["gletscher", "gletscher"], ["seeli", "see"], ["see", "see"], ["gumpen", "see"], ["moos", "moor"], ["moor", "moor"], ["pass", "pass"],
			["huette", "huette"], ["alp ", "huette"], ["sennerei", "huette"], ["gipfel", "gipfel"], ["spitz", "gipfel"], ["stock", "gipfel"],
			["horn", "gipfel"], ["zahn", "gipfel"], ["grat", "grat"], ["klettersteig", "klettersteig"], ["wald", "wald"], ["lichtung", "wald"],
			["hoehle", "hoehle"], ["saeumerweg", "weg"], ["kehren", "weg"], ["aussicht", "aussicht"], ["chanzle", "aussicht"]]
	for r in rules:
		if n.find(r[0]) >= 0:
			return r[1]
	return "ort"


static func places() -> Array:
	"""every place of the map: {name, x, z, kind, vp (viewpoint), spot (sleeping spot)} - all_places() without the rooms
	(«… (innen)» stand in their building) and the suggested sleeping spots; one entry per name"""
	var out := []
	var seen := {}
	var vps := {}
	for vp in Bt.VIEWPOINTS:
		vps[str(vp[1])] = str(vp[2])
	for p in Bt.all_places():
		var nm := str(p[0])
		if nm.ends_with("(innen)") or seen.has(nm):
			continue
		seen[nm] = true
		var k := "aussicht" if vps.has(nm) else kind_of(nm)
		if vps.get(nm, "") == "gipfel":
			k = "gipfel"
		out.append({"name": nm, "x": snappedf(float(p[1]), 0.1), "z": snappedf(float(p[2]), 0.1), "kind": k, "vp": vps.has(nm)})
	for key in Bt.SPOT_ORDER:
		if Bt.SPOTS.has(key) and not seen.has(str(Bt.SPOTS[key][0])):
			var sp: Array = Bt.SPOTS[key]
			seen[str(sp[0])] = true
			out.append({"name": str(sp[0]), "x": float(sp[1]), "z": float(sp[2]), "kind": "schlafplatz", "spot": key})
	return out


static func secrets() -> Array:
	"""the secret places: {id, name, x, z, kind, found: [discovery ids]} - hidden on the map until one of them is found"""
	var out := []
	for v in Bt.VIGNETTES:
		if int(v[0]) in OPEN_VIGNETTES:
			continue
		var vid := str(v[1])
		out.append({"id": "v." + vid, "name": str(v[2]), "x": float(v[3]), "z": float(v[4]), "kind": "geheim",
				"found": FOUND_IDS.get(vid, ["berg." + vid])})
	# «Die Karte des Grossvaters»: the goal of each chapter (where the next piece of the map lies) - found = chapter done
	for ch in AbD.CHAPTERS:
		var last := Vector2.INF
		for stg in ch["stages"]:
			if (stg as Dictionary).has("walk"):
				last = (stg["walk"] as Array)[-1]
		if last != Vector2.INF:
			out.append({"id": "ab.%d" % int(ch["id"]), "name": str(ch["title"]), "x": last.x, "z": last.y, "kind": "schatz",
					"found": ["abenteuer.kapitel.%d" % int(ch["id"])]})
	return out


func _chapter_done(n: int) -> bool:
	var ab = main.get("abenteuer") if main != null else null
	if ab == null or not (ab.get("P") is Dictionary):
		return false
	var P: Dictionary = ab.P
	return int(P.get("chapter", 1)) > n or (n >= 5 and bool(P.get("finale", false)))


static func trails() -> Array:
	"""{name, level 0 gelb / 1 rot / 2 blau, pts [[x, z] …], secret (found ids or [])}"""
	var out := []
	for tr in Bt.TRAILS:
		var pts := []
		for q in tr[1]:
			pts.append([snappedf((q as Vector2).x, 0.1), snappedf((q as Vector2).y, 0.1)])
		out.append({"name": str(tr[0]), "level": int(tr[2]), "pts": pts, "secret": SECRET_TRAILS.get(str(tr[0]), [])})
	return out


static func lakes() -> Array:
	"""{c [x, z], a, b, rot, level (height of the water), secret}"""
	var out := []
	for i in range(Bt.LAKES.size()):
		var lk: Array = Bt.LAKES[i]
		out.append({"c": [(lk[0] as Vector2).x, (lk[0] as Vector2).y], "a": float(lk[1]), "b": float(lk[2]), "rot": float(lk[3]),
				"level": snappedf(Bt.level_of(lk), 0.01), "secret": SECRET_LAKES.get(i, [])})
	return out


static func streams() -> Array:
	var out := []
	for st in Bt.STREAMS:
		var pts := []
		for q in Bt.dense(st[0], 8.0):
			pts.append([snappedf(q.x, 0.1), snappedf(q.y, 0.1)])
		out.append({"w": float(st[1]), "pts": pts})
	return out


static func road() -> Array:
	var src: Array = Array(Bt.road_pts) if not Bt.road_pts.is_empty() else Bt.ROAD
	var pts := []
	var last := Vector2.INF
	for q in src:
		if (q as Vector2).distance_to(last) >= 6.0:
			pts.append([snappedf((q as Vector2).x, 0.1), snappedf((q as Vector2).y, 0.1)])
			last = q
	return pts


static func land_class(x: float, z: float) -> int:
	"""0 meadow · 1 forest · 2 rock · 3 scree · 4 glacier · 5 lake · 6 moor · 7 pasture (Swiss map colours in MoveEye)"""
	var zn := Bt.zone(x, z)
	if zn == "lake":
		return 5
	if zn == "glacier":
		return 4
	if zn == "moor":
		return 6
	var h := Bt.H(x, z)
	if Bt.slope_deg(x, z, 2.0) > 42.0:
		return 2
	if zn == "scree" or zn == "boulders" or Bt.cone_at(x, z) > 0.35:
		return 3
	if Bt.forest_k(x, z, h) > 0.45:
		return 1
	if zn == "pasture":
		return 7
	return 0


# ---- live: what MoveEye shows on its map ----------------------------------------------------------------------------------
var main
var tour := {}                               # {"name", "pts": [Vector2 …], "i", "who", "t_prog", "best", "len", "done", "why"}
var _seen_t := 0.0
var _seen := []


func _bt():
	if main == null or str(main.scene) != "bergtal" or main.scenes == null:
		return null
	return main.scenes.data.get("bergtal", null)


func _vxz(b, wp: Vector3) -> Array:
	var q: Vector3 = b.V(wp)
	return [snappedf(q.x, 0.1), snappedf(q.z, 0.1)]


func _az(b, fwd_world: Vector3) -> float:
	"""degrees from north (valley -z) clockwise, of a direction in the world"""
	var v: Vector3 = b.inv.basis * fwd_world
	return snappedf(fposmod(rad_to_deg(atan2(v.x, -v.z)), 360.0), 0.1)


func reply():
	"""world_reply «bkarte» (MoveEye 639zzzzzt) - null outside the Bergtal"""
	var b = _bt()
	if b == null:
		return null
	var o := {"v": VERSION}
	var cam: Camera3D = main.cams[0] if main.cams.size() > 0 else null
	if cam != null:
		o["me"] = _vxz(b, cam.global_position) + [_az(b, -cam.global_transform.basis.z), snappedf(cam.fov, 0.1)]
	var ex = main.explore
	if ex != null and ex.person != null and ex.person.actor != null and is_instance_valid(ex.person.actor):
		var a: Node3D = ex.person.actor
		o["fig"] = _vxz(b, a.global_position) + [_az(b, -a.global_transform.basis.z)]
	if main.mover_on or (ex != null and ex.on and not ex.person_on()):
		o["mover"] = _vxz(b, main.rig.global_position) + [_az(b, -main.rig.global_transform.basis.z)]
	o["seen"] = _seen_now(b)
	o["found"] = found_ids()
	o["tour"] = tour_state()
	return o


func found_ids() -> Array:
	"""the found-ids (of secrets(), SECRET_TRAILS, SECRET_LAKES) that are found: the discovery book, the chapters of the story"""
	var e = main.get("entdecken")
	var ids := []
	for s in secrets():
		ids.append_array(s["found"])
	for fl in SECRET_TRAILS.values() + SECRET_LAKES.values():
		ids.append_array(fl)
	var out := []
	for fid in ids:
		var f := str(fid)
		if f in out:
			continue
		var ok := false
		if f.begins_with("abenteuer.kapitel."):
			ok = _chapter_done(int(f.get_slice(".", 2)))
		elif e != null and e.has_method("is_found"):
			ok = e.is_found(f)
		if ok:
			out.append(f)
	return out


func _seen_now(b) -> Array:
	"""animals / persons MoveEye reports right now: in the picture of the head camera and MoveEye says so (person boxes on
	the figure; animals: MoveEye reports an animal or motion) - at most 4 × per second, at most 24 points"""
	if main.now() - _seen_t < 0.25:
		return _seen
	_seen_t = main.now()
	_seen = []
	if main.now() - float(main.mw_det_t) > 1.5 or main.cams.is_empty() or main.visitors == null:
		return _seen
	var det: Dictionary = main.mw_det
	var boxes := []
	var bx = det.get("boxes", null)
	if typeof(bx) == TYPE_ARRAY:
		for q in bx:
			if typeof(q) == TYPE_ARRAY and (q as Array).size() >= 4:
				boxes.append(Rect2(float(q[0]), float(q[1]), float(q[2]), float(q[3])).grow(0.02))
	var persons := int(det.get("persons", 0)) > 0
	var pres: Array = det.get("present", []) if typeof(det.get("present", [])) == TYPE_ARRAY else []
	var animal := "animal" in pres or "motion" in pres or "warm" in pres
	var cam: Camera3D = main.cams[0]
	var vs := Vector2(main.CAM_W[0], main.CAM_H[0])
	for v in main.visitors.get_children():
		if _seen.size() >= 24:
			break
		var k := str(v.get("kind")) if v.get("kind") != null else ""
		if k == "" or k in NOT_SEEN or bool(v.get("done") if v.get("done") != null else false) or not (v is Node3D):
			continue
		var p: Vector3 = (v as Node3D).global_position
		if cam.is_position_behind(p) or cam.global_position.distance_to(p) > 60.0:
			continue
		var lo := cam.unproject_position(p) / vs
		var hi := cam.unproject_position(p + Vector3(0, 1.6 if k in PERSON else 0.6, 0)) / vs
		var w := absf(lo.y - hi.y) * 0.4 + 0.01
		var r := Rect2(minf(lo.x, hi.x) - w / 2.0, minf(lo.y, hi.y), w + absf(lo.x - hi.x), absf(lo.y - hi.y) + 0.01)
		if r.end.x < 0.0 or r.position.x > 1.0 or r.end.y < 0.0 or r.position.y > 1.0:
			continue
		var hit := false
		if k in PERSON:
			if boxes.is_empty():
				hit = persons
			for q2 in boxes:
				if (q2 as Rect2).intersects(r):
					hit = true
					break
		else:
			hit = animal
		if hit:
			_seen.append(["p" if k in PERSON else "a"] + _vxz(b, p))
	return _seen


# ---- «Tour im Sim nachlaufen» --------------------------------------------------------------------------------------------
func control(d: Dictionary) -> Dictionary:
	var a := str(d.get("do", "info"))
	if a == "tour":
		return start_tour(d.get("pts", []), str(d.get("name", "")).substr(0, 120), str(d.get("who", "auto")))
	if a == "stop":
		stop_tour("stop")
		return {"ok": true, "tour": tour_state()}
	return {"ok": true, "bergtal": _bt() != null, "tour": tour_state(), "places": places().size(), "secrets": secrets().size()}


func start_tour(raw, name: String, who: String) -> Dictionary:
	var b = _bt()
	if b == null:
		return {"ok": false, "error": "only in the Bergtal"}
	var pts := []
	if typeof(raw) == TYPE_ARRAY:
		for q in raw:
			if typeof(q) == TYPE_ARRAY and (q as Array).size() >= 2 and pts.size() < MAX_PTS:
				var x := float(q[0])
				var z := float(q[1])
				if is_finite(x) and is_finite(z) and absf(x) <= -Bt.LO and absf(z) <= -Bt.LO:
					pts.append(Vector2(x, z))
	if pts.size() < 2:
		return {"ok": false, "error": "A route needs at least two points."}
	var ex = main.explore
	if ex == null:
		return {"ok": false, "error": "no explore"}
	if not ex.on:
		ex.set_on(true)
	var use_person: bool = who != "mover" and ex.person_ok()
	if who == "person" and not use_person:
		return {"ok": false, "error": ex.person.why_not(main) if ex.person != null else "no person"}
	if use_person:
		if not ex.person_on():
			ex.set_person(true)
		var w0: Vector3 = b.WG(pts[0].x, pts[0].y, 0.0)
		ex.person.place(w0)
	elif ex.person_on():
		ex.set_person(false)
	var L := 0.0
	for i in range(1, pts.size()):
		L += (pts[i] as Vector2).distance_to(pts[i - 1])
	tour = {"name": name, "pts": pts, "i": 1 if use_person else 0, "who": "person" if use_person else "mover", "t_prog": main.now(),
			"best": INF, "len": L, "done": false, "why": ""}
	main.start_info = "🥾 %s %s" % [T.t("Tour im Sim:"), name if name != "" else "%d m" % int(L)]
	return {"ok": true, "tour": tour_state()}


func stop_tour(why: String) -> void:
	if tour.is_empty() or tour.get("done", false):
		return
	tour["done"] = true
	tour["why"] = why
	var ex = main.explore
	if ex != null:
		ex.test_until = 0.0
		if ex.person != null:
			ex.person._test = {}


func tour_state():
	if tour.is_empty():
		return null
	var b = _bt()
	var left := 0.0
	var pts: Array = tour["pts"]
	var at = _walker_xz(b) if b != null else null
	var i := int(tour["i"])
	if at != null and i < pts.size():
		left = (at as Vector2).distance_to(pts[i])
		for k in range(i + 1, pts.size()):
			left += (pts[k] as Vector2).distance_to(pts[k - 1])
	return {"name": tour["name"], "who": tour["who"], "i": i, "n": pts.size(), "len": snappedf(float(tour["len"]), 1.0), "left": snappedf(left, 1.0),
			"done": tour["done"], "why": tour["why"]}


func _walker_xz(b):
	var ex = main.explore
	if ex == null or b == null:
		return null
	var wp: Vector3
	if tour.get("who", "") == "person":
		if ex.person == null or ex.person.actor == null or not is_instance_valid(ex.person.actor):
			return null
		wp = ex.person.actor.global_position
	else:
		wp = main.rig.global_position
	var q: Vector3 = b.V(wp)
	return Vector2(q.x, q.z)


func _process(_dt: float) -> void:
	if tour.is_empty() or tour.get("done", false):
		return
	var b = _bt()
	var ex = main.explore
	if b == null or ex == null or not ex.on:
		stop_tour("explore")
		return
	var person: bool = tour["who"] == "person"
	if person and not ex.person_on():
		stop_tour("person")
		return
	if person and ex.person.cmd != Vector2.ZERO:            # the player takes over (keys, sticks)
		stop_tour("player")
		return
	if not person and not main.typing() and (Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_A)
			or Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_DOWN)
			or (main.padmap != null and main.padmap.drive_cmd() != Vector2.ZERO)):
		stop_tour("player")
		return
	var pts: Array = tour["pts"]
	var at = _walker_xz(b)
	if at == null:
		stop_tour("walker")
		return
	var i := int(tour["i"])
	while i < pts.size() and (at as Vector2).distance_to(pts[i]) < REACH:
		i += 1
		tour["best"] = INF
		tour["t_prog"] = main.now()
	tour["i"] = i
	if i >= pts.size():
		stop_tour("finish")
		main.start_info = "🏁 " + T.t("Tour im Sim: am Ziel")
		return
	var d := (at as Vector2).distance_to(pts[i])
	if d < float(tour["best"]) - 1.0:
		tour["best"] = d
		tour["t_prog"] = main.now()
	elif main.now() - float(tour["t_prog"]) > STUCK_S:
		if person:                                           # stuck at an obstacle: on to the next point
			ex.person.place(b.WG(pts[i].x, pts[i].y, 0.0))
			tour["t_prog"] = main.now()
		else:
			stop_tour("edge")                                # the mover stays in its area (± 180 m)
			main.start_info = T.t("Tour im Sim: der Mover kommt hier nicht weiter")
			return
	# where to go: valley direction -> world yaw (forward = (-sin yaw, -cos yaw))
	var tw: Vector3 = b.WG(pts[i].x, pts[i].y, 0.0)
	if person:
		var ap: Vector3 = ex.person.actor.global_position
		ex.person.yaw = atan2(-(tw.x - ap.x), -(tw.z - ap.z))
		ex.person.test_walk(Vector2(1.0, 0.0), 0.4, false)
	else:
		var rp: Vector3 = main.rig.global_position
		var want := atan2(-(tw.x - rp.x), -(tw.z - rp.z))
		var err := wrapf(want - float(main.rig.rotation.y), -PI, PI)
		var turn := clampf(-err * 1.6, -1.0, 1.0)            # turn right = positive (main._drive: rotation.y -= om)
		var fwd := clampf(1.0 - absf(err) / 1.2, 0.0, 1.0)
		ex.test_drive = Vector2(fwd, turn)
		ex.test_until = main.now() + 0.4
