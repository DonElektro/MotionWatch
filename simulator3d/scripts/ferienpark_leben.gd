extends Node
## Paket «Ferienpark: kleine Aufgaben + Tag/Nacht-Leben» (Zweig real-ferienpark-leben, 31.10.2026).
##
## A · Tag/Nacht-Leben nach Uhrzeit (Schalter «Ferienpark: Leben nach Uhrzeit», Besuch → Von selbst):
##   * Grillabend 17:45–22:35: eine Gruppe (Lite: 3, sonst 4) vor MoveEye, einer am Grill, die anderen sitzen am Tisch.
##     Rauch beim Anzünden stark, dann schwach. Die Glut steht im Wärmebild (waerme.gd «bbq_coals», danach Waerme.embers():
##     sie kühlt nach dem Grillen langsam ab - um Mitternacht ist der Grill noch deutlich warm, ein typischer Fehlalarm-Fall).
##     Eine Vignette der Erlebniswelt (erlebniswelt.gd Vig): sie ist bei Testlauf / Prüfstand / Messung weg.
##   * Nachtruhe 22:30–6:00: kaum noch jemand unterwegs (life.gd: Personen nachts ×0.08); hier dazu ab und zu ein WC-Gang
##     von einem Platz in der Nähe über die Gasse zum Sanitärgebäude, meist mit Taschenlampe (menschen.gd «m_wc»).
##   * Frühaufsteher 5:45–8:00: Jogger auf der Gasse (vor Tagesanbruch mit Stirnlampe); 6:15–7:15 einmal am Tag der
##     Bäcker-Lieferwagen (fahrzeuge.gd: Licht, Motorwärme), er hält bei MoveEye, der Fahrer bringt die Brötli an zwei Plätze.
##   Alles nur, wenn «Besucher kommen von selbst» an ist und keine Aufgabe / kein Test die Welt hat (main.busy_with).
##
## B · Kleine Aufgaben mit MoveEye (Spiel → Entdecken): die Erkennung kommt aus den echten MoveEye-Ereignissen
##   (main.mw_det: Personen-Rahmen 0..1 der Kopfkamera - wie blindmap.gd / Verstecken mit MoveEye).
##   * Verlorenes Kind: ein Kind (rote Jacke) spielt irgendwo 10–24 m um MoveEye und wechselt den Ort; die Mutter wartet
##     hinter MoveEye. Hat MoveEye einen Rahmen auf dem Kind, ist es gefunden: das Bild von MoveEyes Kamera (mit Rahmen) kommt
##     ins Entdeckungsbuch und nach user://aufgaben/. 5 Minuten Zeit.
##   * Velo-Dieb: jemand kommt, hebt dein Velo hoch und trägt es weg (szenenplus.gd «velodieb», hier getragen statt
##     geschoben; ruhig oder eilig). Gemessen: im Bild ab, von MoveEye erkannt nach …, auch mit dem Velo in den Händen,
##     Velo-Sensor; Rahmen ohne Figur darunter zählen als Fehlmeldung.
##   * Zeltplatz nachts bewachen: MoveEye beim Zelt, 23–1 Uhr im Zeitraffer (×30, 4 Min.) als kurzer Nacht-Testlauf
##     (nachtlauf.gd mit eigenem Plan): zwei WC-Gänge, Fuchs, Katze und ein Eindringling. Ergebnis: Eindringling erkannt?
##     Personen erkannt, Tiere als Person gemeldet. Den genauen Abgleich mit den Pushes macht MoveEye (Nacht-Testlauf, 579b).
##   Eine Sperre wie alle Simulator-Aufgaben: main.busy_with() meldet «Ferienpark-Aufgabe» (Zeltwache: «Nacht-Testlauf»).
##
## Lite: _lite() = Quality.lite() (quality.gd, die zentrale Abfrage) - ein Rauch statt zwei, weniger Partikel, kein
## Glut-Licht, 3 statt 4 Leute am Grill, WC-Gänge / Jogger seltener.
## Steuerung: {"action": "ferienpark", "do": "leben"} (Info) · {"do": "aufgabe", "what": "kind" | "velo" | "zelt" | "stop" | "info"}.

const T = preload("res://scripts/i18n.gd")
const Quality = preload("res://scripts/quality.gd")
const Waerme = preload("res://scripts/waerme.gd")
const EW = preload("res://scripts/erlebniswelt.gd")

const FILE := "user://ferienpark_leben.json"
static var on := true                       # «Ferienpark: Leben nach Uhrzeit»
static var _loaded := false

var m                                        # main.gd
var fp                                       # ferienpark.gd
var s                                        # scenes.gd
var ew                                       # erlebniswelt.gd (helpers for figures and parts, the vignette list)
var lite := false
var grill: Grillabend
var road: Array = []                         # the lane near MoveEye (world points, from ferienpark.gd «road_line»)
var homes: Array = []                        # pitches near MoveEye (world) - where the WC walks start, where the bread goes
var wcs: Array = []                          # the toilet blocks (world)
var _tick := 0.0
var _next_wc := 0.0
var _next_jog := 0.0
var _bread_done := false
var _wc_v = null
var van = null
var driver = null
var van_stop := Vector3.ZERO
var stats := {"wc": 0, "jog": 0, "van": 0}


static func _lite() -> bool:
	"""Lite graphics (Raspberry Pi): the one central switch (quality.gd)"""
	return Quality.lite()


# =============================================================================================================================
# ---- settings and controls (main._register_controls) ------------------------------------------------------------------------
# =============================================================================================================================
static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	if FileAccess.file_exists(FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if typeof(d) == TYPE_DICTIONARY:
			on = bool(d.get("on", true))


static func _save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"on": on}))


static func add_controls(main) -> void:
	"""main._register_controls: the three tasks (Spiel → Entdecken, ids in main.DISC_IDS) and the switch (Besuch → Von selbst)"""
	_load()
	var only := func(): return main.scene == "ferienpark"
	main.add_control("button", "fp_task_kind", "🧒 Aufgabe: Verlorenes Kind finden (mit MoveEye)", null, func(): tasks(main).start("kind"), "Spiel")
	main.controls[-1]["only"] = only
	main.add_control("button", "fp_task_velo", "🚲 Aufgabe: Velo-Dieb bemerken (mit MoveEye)", null, func(): tasks(main).start("velo"), "Spiel")
	main.controls[-1]["only"] = only
	main.add_control("button", "fp_task_zelt", "⛺ Aufgabe: Zeltplatz nachts bewachen (4 Min., mit MoveEye)", null, func(): tasks(main).start("zelt"), "Spiel")
	main.controls[-1]["only"] = only
	main.add_control("toggle", "fp_leben", "Ferienpark: Leben nach Uhrzeit (Grillabend mit Rauch und Glut, Nachtruhe mit WC-Gängen und Taschenlampe, früh Jogger und Bäcker-Lieferwagen)",
			func(): return on, func(v): set_on(main, bool(v)), "Besuch", {"sub": "Von selbst"})
	main.controls[-1]["only"] = only


static func set_on(main, v: bool) -> void:
	on = v
	_save()
	var lv = main.scenes.data.get("leben", null) if main.scenes != null else null
	if lv != null and is_instance_valid(lv):
		lv._update_on()


static func tasks(main) -> Aufgaben:
	"""the task runner: a node of main (it lives on when the park is built again - the tent task moves MoveEye to the tent)"""
	var n = main.get_node_or_null("fp_aufgaben")
	if n == null:
		n = Aufgaben.new()
		n.name = "fp_aufgaben"
		n.main = main
		main.add_child(n)
	return n


static func task_busy(main) -> String:
	"""main.busy_with: the one lock of the simulator tasks"""
	var n = main.get_node_or_null("fp_aufgaben")
	return "Ferienpark-Aufgabe" if n != null and n.locks() else ""


# =============================================================================================================================
# ---- building (ferienpark.gd _leben, after the Erlebniswelt) ----------------------------------------------------------------
# =============================================================================================================================
func setup(fp_, ew_) -> void:
	_load()
	fp = fp_
	ew = ew_
	m = fp.m
	s = fp.s
	name = "ferienpark_leben"
	lite = _lite() or str(m.quality) == "simple"
	s.root.add_child(self)
	var rl = s.data.get("road_line", null)
	if rl is PackedVector2Array:
		for v in rl:
			var q: Vector2 = v
			if q.length() < 140.0:
				road.append(Vector3(q.x, 0, q.y))
	for e in s.data.get("nachbarn", []):
		homes.append(e[1])
	var pl = s.data.get("platz", null)
	if pl is Array:
		homes.append(pl[0])
	homes.sort_custom(func(a, b): return Vector2(a.x, a.z).length() < Vector2(b.x, b.z).length())
	for pc in fp.PLACES:
		if str(pc[0]).begins_with("Sanitär"):
			wcs.append(fp.WG(float(pc[1]), float(pc[2])))
	grill = Grillabend.new(ew)
	grill.lv = self
	grill.c = _grill_place()
	grill.build()
	ew.vigs.append(grill)
	ew.by_id[grill.id] = grill
	ew._update_shown(true)
	_register()
	_update_on()
	var t: float = m.now()
	_next_wc = t + randf_range(30.0, 90.0)
	_next_jog = t + randf_range(20.0, 60.0)


func _grill_place() -> Vector3:
	"""a free place on the meadow in front of MoveEye (13–19 m, a bit to the side) - not on a way, not in the lake (park coords)"""
	for d in [15.0, 13.0, 18.0, 11.0, 21.0]:
		for az in [22.0, -22.0, 35.0, -35.0, 10.0, -10.0, 50.0, -50.0]:
			var w: Vector3 = m.pos_of(az, d)
			var q: Vector3 = fp.inv * w
			if fp.H(q.x, q.z) < 0.8 or fp._on_way(q.x, q.z, 3.5):
				continue
			var ok := true
			for o in m._ob_near(Vector2(w.x, w.z)):
				if float(m._ob_closest(o, Vector2(w.x, w.z))[1]) < 3.2:
					ok = false
					break
			if ok:
				return ew.Pg(q.x, q.z)
	var q2: Vector3 = fp.inv * m.pos_of(25.0, 14.0)
	return ew.Pg(q2.x, q2.z)


func _register() -> void:
	"""the tasks in the discovery book (found when MoveEye has done them - with its picture)"""
	var e = ew.ent()
	if e == null:
		return
	for it in [["see.aufgabe_kind", "Verlorenes Kind gefunden", "MoveEye hat das Kind mit der roten Jacke entdeckt – das Bild ist von MoveEyes Kamera.",
				"Spiel → Entdecken → «Aufgabe: Verlorenes Kind finden».", "🧒"],
			["see.aufgabe_velo", "Velo-Dieb bemerkt", "MoveEye hat gesehen, wie jemand dein Velo wegträgt.", "Spiel → Entdecken → «Aufgabe: Velo-Dieb bemerken».", "🚲"],
			["see.aufgabe_zelt", "Zeltplatz bewacht", "In der Nacht hat MoveEye den Eindringling erkannt und kein Tier für eine Person gehalten.",
				"Spiel → Entdecken → «Aufgabe: Zeltplatz nachts bewachen».", "⛺"]]:
		e.register(it[0], {"scene": "ferienpark", "title": T.t(it[1]), "short_text": T.t(it[2]), "hint": T.t(it[3]), "icon": it[4],
				"kind": "mensch", "position": Vector3(0, -50, 0), "size": Vector3.ONE, "radius": 0.5, "when": "any",
				"active": func(): return false, "los": false})
	e.register("see.grillabend", {"scene": "ferienpark", "title": T.t("Grillabend"), "short_text": T.t("Am Abend grillt eine Gruppe vor MoveEye. Im Wärmebild leuchtet die Glut noch lange nach dem Essen."),
			"hint": T.t("Am Abend riecht es vor MoveEye nach Grillwurst."), "icon": "🔥", "kind": "mensch", "position": ew.W(grill.c) + Vector3(0, 1.0, 0),
			"size": Vector3(4, 2, 4), "radius": 18.0, "when": "evening", "active": func(): return grill.party() and grill.shown})


func _update_on() -> void:
	grill.off = not on


func _quiet() -> bool:
	return not on or ew._is_quiet() or m.busy_with() != "" or not m.auto_visitors


# =============================================================================================================================
# ---- the day: WC walks at night, joggers and the bakery van in the morning --------------------------------------------------
# =============================================================================================================================
func _process(dt: float) -> void:
	if m == null or not is_inside_tree():
		return
	_tick -= dt
	if _tick > 0.0:
		return
	_tick = 0.5
	_van_tick()
	var hh: float = m.hour()
	if hh < 6.0 or hh >= 8.0:
		_bread_done = false
	if _quiet() or road.size() < 2:
		return
	var t: float = m.now()
	var h: float = m.hour()
	var k: float = (1.6 if lite else 1.0) / maxf(0.1, float(m.visit_rate))
	if m.visitors.get_child_count() + 2 > int(m.max_visitors):
		return
	if (h >= 22.5 or h < 6.0) and t > _next_wc and (_wc_v == null or not is_instance_valid(_wc_v)):
		_next_wc = t + randf_range(240.0, 540.0) * k
		_wc_walk()
	if h >= 5.75 and h < 8.0 and t > _next_jog:
		_next_jog = t + randf_range(150.0, 360.0) * k
		_jogger()
	if h >= 6.25 and h < 7.25 and not _bread_done and (van == null or not is_instance_valid(van)):
		_bread_done = true                                   # once a morning
		_bakery()


func _lane_path(a: Vector3, b: Vector3) -> Array:
	"""the lane points from the one nearest to a to the one nearest to b (world)"""
	var ia := _near_i(a)
	var ib := _near_i(b)
	var out := []
	var st := 1 if ib >= ia else -1
	var i := ia
	while true:
		out.append(road[i])
		if i == ib:
			break
		i += st
	return out


func _near_i(p: Vector3) -> int:
	var bi := 0
	var bd := 1e9
	for i in range(road.size()):
		var d := Vector2(road[i].x - p.x, road[i].z - p.z).length()
		if d < bd:
			bd = d
			bi = i
	return bi


func _wc_walk() -> void:
	"""Nachtruhe: somebody of a pitch near MoveEye goes over the lane to the toilet block and back (mostly with a torch)"""
	if homes.is_empty() or wcs.is_empty():
		return
	var home: Vector3 = homes[randi() % mini(3, homes.size())]
	var wc: Vector3 = wcs[0]
	for w in wcs:
		if (w as Vector3).distance_to(home) < wc.distance_to(home):
			wc = w
	var v = m.spawn("m_wc", home, wc)                        # menschen.gd: torch (80 %) or phone light, hood, hurries
	if v == null:
		return
	var lane := _lane_path(home, wc)
	var back := lane.duplicate()
	back.reverse()
	var r: Array = lane.slice(1)
	r.append([m.free_spot(wc, 0.4, true), randf_range(60.0, 180.0), 0.0])
	r.append_array(back)
	r.append(home)
	v.target = lane[0]
	v.route = r
	_wc_v = v
	stats["wc"] += 1


func _jogger() -> void:
	"""Frühaufsteher: a jogger along the lane (before sunrise with a headlamp)"""
	var pts := road.duplicate()
	if randf() < 0.5:
		pts.reverse()
	var v = m.spawn("jogger", pts[0], pts[1])
	if v == null:
		return
	v.route = pts.slice(2)
	if m.is_dark() and v.has_method("add_lamp"):
		v.add_lamp("head")
		v.set_night(true)
	stats["jog"] += 1


func _bakery() -> void:
	"""the bakery van: along the lane, it stops at the lane point nearest to MoveEye, the driver brings bread to two pitches"""
	var n0: int = m.visitors.get_child_count()
	m.car("van")
	if m.visitors.get_child_count() <= n0:
		return
	van = m.visitors.get_child(m.visitors.get_child_count() - 1)
	var bi := -1
	var bd := 1e9
	for i in range(van.route.size()):
		var p = van.route[i]
		if typeof(p) == TYPE_VECTOR3 and Vector2(p.x, p.z).length() < bd:
			bd = Vector2(p.x, p.z).length()
			bi = i
	if bi < 0:
		return
	van_stop = van.route[bi]
	van.route[bi] = [van_stop, 70.0, 0.0]
	van.set_meta("baecker", true)
	driver = null
	stats["van"] += 1


func _van_tick() -> void:
	if van == null or not is_instance_valid(van) or van.is_queued_for_deletion():
		van = null
		return
	if driver != null or not van.has_meta("baecker"):
		return
	if van.position.distance_to(van_stop) < 2.5 and float(van.cur_speed) < 0.3 and van.now_s() < float(van.wait_until):
		var side := 1
		var at: Vector3 = van.position + van.global_transform.basis.x * 1.3
		if m.fahrzeuge != null and m.fahrzeuge.has_method("exit_point"):
			side = m.fahrzeuge.side_towards(van, Vector3.ZERO) if m.fahrzeuge.has_method("side_towards") else 1
			at = m.fahrzeuge.exit_point(van, side)
			if m.fahrzeuge.has_method("door"):
				m.fahrzeuge.door(van, side, true)
		var stops := []
		for hp in homes.slice(0, 2):
			stops.append([m.free_spot((hp as Vector3) + Vector3(0.6, 0, 0.6), 0.4, true), 2.5, 0.5, hp])
		if stops.is_empty():
			return
		driver = m.spawn("person", at, stops[0][0])
		if driver == null:
			return
		driver.carry = true                                  # the bread box in both hands
		driver.speed = 1.5
		driver.route = stops.slice(1) + [[at, 1.0, 0.0], at]
		driver.next_idle = driver.now_s() + 1.0e5
		van.remove_meta("baecker")


# ---- control {"action": "ferienpark", "do": "leben"} ------------------------------------------------------------------------
func info() -> Dictionary:
	return {"ok": true, "on": on, "lite": lite, "hour": snappedf(m.hour(), 0.01), "grill": grill.info(), "stats": stats,
			"road": road.size(), "homes": homes.size(), "wcs": wcs.size(), "quiet": _quiet()}


# =============================================================================================================================
# ---- the evening barbecue (a vignette of the Erlebniswelt: hidden during tests, only moves when somebody is near) -----------
# =============================================================================================================================
class Grillabend extends EW.Vig:
	var lv
	var off := false
	var coal: MeshInstance3D
	var coal_m: StandardMaterial3D
	var bowl: MeshInstance3D
	var heat := -100.0
	var smokes: Array = []
	var glow: OmniLight3D
	var people: Array = []          # [actor, seat (park), "cook" | "sit"]
	var table := Vector3.ZERO
	var free_seat := Vector3.ZERO   # the cook sits there after the meal
	var here := false

	func build() -> void:
		id = "grillabend"
		var g: Vector3 = c
		var gn: Node3D = ew.node(vroot, g)
		# a kettle grill: three legs, the bowl, the coal, the grate
		for i in range(3):
			var a := TAU * i / 3.0
			ew.part(gn, ew.cylm(0.015, 0.015, 0.7, 5), Vector3(cos(a) * 0.22, 0.33, sin(a) * 0.22), Color(0.2, 0.2, 0.2), "stone", Vector3(0.18 * sin(a), 0, -0.18 * cos(a)))
		bowl = ew.part(gn, ew.cylm(0.29, 0.2, 0.22, 14), Vector3(0, 0.74, 0), Color(0.08, 0.08, 0.09), 15.0)
		coal_m = StandardMaterial3D.new()
		coal_m.albedo_color = Color(0.12, 0.1, 0.09)
		coal_m.emission_enabled = true
		coal_m.emission = Color(1.0, 0.35, 0.1)
		coal_m.emission_energy_multiplier = 0.0
		coal = ew.m.add_mesh(gn, ew.cylm(0.25, 0.25, 0.04, 12), Vector3(0, 0.84, 0), coal_m, 15.0)
		ew.part(gn, ew.cylm(0.28, 0.28, 0.01, 12), Vector3(0, 0.9, 0), Color(0.55, 0.55, 0.55), "stone")
		for i in range(3):
			ew.part(gn, ew.cylm(0.017, 0.017, 0.15, 6), Vector3(-0.1 + i * 0.1, 0.915, 0.03), Color(0.55, 0.28, 0.18), Waerme.T("sausages"), Vector3(PI / 2.0, 0, 0))
		# smoke (Lite: one, fewer particles)
		var keep: float = Quality.KEEP if ew.lite else 1.0
		for i in range(1 if ew.lite else 2):
			var p := CPUParticles3D.new()
			p.amount = maxi(4, int([16, 26][i] * keep))
			p.lifetime = 6.0
			p.position = g + Vector3(0, 1.0, 0)
			p.direction = Vector3(0, 1, 0)
			p.spread = 16.0
			p.initial_velocity_min = 0.35
			p.initial_velocity_max = 0.7
			p.gravity = Vector3(0.15 + float(ew.m.wind) * 0.02, 0.05, 0.05)
			var cv := Curve.new()
			cv.add_point(Vector2(0, 0.25))
			cv.add_point(Vector2(1, 2.6))
			p.scale_amount_curve = cv
			var sm: SphereMesh = ew.sphm(0.32, -1.0, 6)
			var mt := StandardMaterial3D.new()
			mt.albedo_color = Color(0.6 - i * 0.12, 0.6 - i * 0.12, 0.62 - i * 0.12, 0.3 + i * 0.1)
			mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			sm.material = mt
			p.mesh = sm
			p.emitting = false
			vroot.add_child(p)
			smokes.append(p)
		if not ew.lite:                                  # the glow of the embers lights the grill a little at night
			glow = OmniLight3D.new()
			glow.position = g + Vector3(0, 1.05, 0)
			glow.light_color = Color(1.0, 0.45, 0.15)
			glow.omni_range = 3.0
			glow.light_energy = 0.0
			glow.shadow_enabled = false
			vroot.add_child(glow)
		# a camping table with chairs, 2.6 m away (towards MoveEye's side)
		var to_me: Vector3 = ew.toP(ew.head_pos()) - g
		to_me.y = 0.0
		var dir := to_me.normalized() if to_me.length() > 0.5 else Vector3(0, 0, 1)
		var side := Vector3(-dir.z, 0, dir.x)
		table = ew.Pg(g.x + side.x * 2.6, g.z + side.z * 2.6)
		var tn: Node3D = ew.node(vroot, table, atan2(side.x, side.z))
		ew.part(tn, ew.boxm(1.2, 0.03, 0.7), Vector3(0, 0.72, 0), Color(0.85, 0.85, 0.82), "caravan")
		for sx in [-0.5, 0.5]:
			ew.part(tn, ew.boxm(0.03, 0.7, 0.6), Vector3(sx, 0.36, 0), Color(0.6, 0.6, 0.62), "stone")
		var seats := [Vector3(0, 0, -0.75), Vector3(0, 0, 0.75), Vector3(0.95, 0, 0), Vector3(-0.95, 0, 0)]
		var bs: Basis = tn.transform.basis
		var n_sit := 2 if ew.lite else 3
		for i in range(4):
			var sp: Vector3 = table + bs * seats[i]
			var cn: Node3D = ew.node(vroot, ew.Pg(sp.x, sp.z), atan2(sp.x - table.x, sp.z - table.z))
			ew.part(cn, ew.boxm(0.45, 0.04, 0.42), Vector3(0, 0.44, 0), Color(0.15, 0.3, 0.55), "tent")
			ew.part(cn, ew.boxm(0.45, 0.4, 0.03), Vector3(0, 0.66, 0.2), Color(0.15, 0.3, 0.55), "tent")
			if i < n_sit:
				var a = ew.actor("elderly" if i == 2 else "person", ew.Pg(sp.x, sp.z), table, 1.1, [Color(0.75, 0.2, 0.15), Color(0.2, 0.4, 0.7), Color(0.3, 0.55, 0.3)][i])
				a.sit_seat = 0.45
				actors.append(a)
				people.append([a, ew.Pg(sp.x, sp.z), "sit"])
		free_seat = ew.Pg((table + bs * seats[3]).x, (table + bs * seats[3]).z)
		var front: Vector3 = ew.Pg(g.x + dir.x * 0.8, g.z + dir.z * 0.8)
		var cook = ew.actor("person", front, g, 1.2, Color(0.9, 0.9, 0.88))
		actors.append(cook)
		people.append([cook, front, "cook"])
		_presence(false)
		go("idle")

	func when_ok() -> bool:
		return not off

	func party() -> bool:
		var h: float = ew.hour()
		return h >= 17.75 and h < 22.6 and not ew.rain()

	func set_shown(on_: bool) -> void:
		super.set_shown(on_)
		if on_:
			_presence(here)
		else:
			for p in smokes:
				p.emitting = false

	func _presence(v: bool) -> void:
		here = v
		for e in people:
			if is_instance_valid(e[0]):
				(e[0] as Node3D).visible = v and shown

	func coal_c() -> float:
		"""the surface of the coal by the hour: lit 17:45, full glow 18:15–21:15 (waerme.gd bbq_coals), then it cools
		(Waerme.embers) - still warm at midnight; cold again in the morning"""
		var h: float = ew.hour()
		var amb: float = ew.m.ambient
		var full: float = Waerme.T("bbq_coals", amb)
		if h >= 17.75 and h < 18.25:
			return amb + (full - amb) * (h - 17.75) / 0.5
		if h >= 18.25 and h < 21.25:
			return full
		var since := fposmod(h - 21.25, 24.0) * 60.0
		if since < 9.0 * 60.0:
			return Waerme.embers(since, amb)
		return amb

	func tick(dt: float) -> void:
		var h: float = ew.hour()
		var tc := coal_c()
		var k := snappedf(tc, 10.0)
		if absf(k - heat) > 0.1:
			heat = k
			ew.set_heat(coal, k)
			ew.set_heat(bowl, snappedf(ew.m.ambient + (k - ew.m.ambient) * 0.35, 5.0))     # the bowl: ~1/3 of the coal (lid open)
			var gk := clampf((k - 150.0) / 250.0, 0.0, 1.0)
			coal_m.emission_energy_multiplier = gk * (1.5 if ew.dark() else 0.5)
			if glow != null:
				glow.light_energy = gk * 0.8 if ew.dark() else 0.0
		var lv_ := 0
		if h >= 17.75 and h < 18.6:
			lv_ = 2                                    # lighting: much smoke
		elif h >= 18.6 and h < 21.25:
			lv_ = 1
		if not party():
			lv_ = 0
		for i in range(smokes.size()):
			var want := lv_ > i if smokes.size() > 1 else lv_ > 0
			if smokes[i].emitting != want:
				smokes[i].emitting = want
		var p_ := party()
		if p_ != here:
			_presence(p_)
		if not here:
			return
		for e in people:
			var a = e[0]
			if not is_instance_valid(a):
				continue
			if e[2] == "sit" or h >= 21.25:              # after the meal the cook sits down too (on the free chair)
				var seat: Vector3 = e[1] if e[2] == "sit" else free_seat
				ew.place(a, seat)
				ew.face(a, table - seat)
				ew.idle(a, "sit")
			else:
				ew.place(a, e[1])
				ew.face(a, c - (e[1] as Vector3))
				var ph := fmod(t, 14.0)
				ew.idle(a, "bend" if ph < 3.0 else ("talk" if ph > 9.0 else "look"), 1.0)

	func info() -> Dictionary:
		var d := super.info()
		d["party"] = party()
		d["coal_c"] = roundi(coal_c())
		d["smoke"] = smokes.filter(func(p): return p.emitting).size()
		d["people"] = people.size()
		d["pos"] = [snappedf(where().x, 0.1), snappedf(where().z, 0.1)]
		return d


# =============================================================================================================================
# ---- the tasks (a node of main) -----------------------------------------------------------------------------------------------
# =============================================================================================================================
class Aufgaben extends Node:
	var main
	var what := ""                  # kind | velo | zelt ("" = none)
	var st := ""
	var t0 := 0.0
	var st_t := 0.0
	var result := {}
	var last := {}
	var kid = null
	var mum = null
	var pts: Array = []             # park points where the child plays
	var pi := 0
	var play_until := 0.0
	var thief = null
	var saved := {}
	var hits := {}                  # zelt: event id -> {kind, mw, mw_t}
	var _acc := 0.0
	var _flick_prev := false
	var keep_pic: Image = null      # the last picture of MoveEye (the tent: into the book only when the night went well)

	static func fig_h(a) -> float:
		if a.kind == "person":
			return 1.75 * float(a.body_root.scale.y) * (1.0 - 0.45 * clampf(float(a.crouch), 0.0, 1.0))
		return maxf(0.25, float(a.body_h) * 1.3)


	func locks() -> bool:
		return what in ["kind", "velo"]

	func _lv():
		return main.scenes.data.get("leben", null) if main.scenes != null else null

	func _say(t: String) -> void:
		if main.mehr != null:
			main.mehr.toast(t)
		main.start_info = t

	func info() -> Dictionary:
		return {"ok": true, "what": what, "state": st, "st_t": snappedf(st_t, 0.1), "frames": Engine.get_process_frames(), "t": snappedf(main.now() - t0, 0.1) if what != "" else 0.0, "result": result, "last": last}

	func start(w: String) -> Dictionary:
		if what != "":
			_say(T.t("Es läuft schon eine Aufgabe."))
			return {"ok": false, "error": "busy", "what": what}
		var b: String = main.busy_with()
		if b != "":
			_say(main.busy_msg(b))
			return {"ok": false, "error": main.busy_msg(b)}
		keep_pic = null
		_flick_prev = false
		if w == "zelt":
			if main.scene != "ferienpark" or str(main.fp_spot) != "zelt":
				main.fp_spot = "zelt"                            # MoveEye at the tent (main.set_fp_spot without the checks)
				main._settings_dirty = true
				main.set_scene("ferienpark")
		elif main.scene != "ferienpark":
			main.set_scene("ferienpark")
		what = w
		st = "wait_build"
		t0 = main.now()
		st_t = 0.0
		result = {"task": w, "moveeye": main.now() - float(main.mw_det_t) < 5.0}
		call_deferred("_begin")
		return {"ok": true, "what": w}

	func _begin() -> void:
		await get_tree().process_frame
		await get_tree().process_frame
		var lv = _lv()
		if lv == null or not is_instance_valid(lv):
			_say(T.t("Die Aufgaben gibt es nur im Ferienpark am See (bei einem Standort im Park)."))
			_finish({"state": "error"})
			return
		match what:
			"kind":
				_kind_begin(lv)
			"velo":
				_velo_begin()
			"zelt":
				_zelt_begin()

	func stop() -> void:
		if what == "zelt" and main.nacht != null and main.nacht.running:
			main.nacht.stop(false)
		_finish({"state": "abgebrochen"})

	func _finish(extra: Dictionary) -> void:
		result.merge(extra, true)
		result["t"] = snappedf(main.now() - t0, 0.1)
		last = result.duplicate(true)
		for a in [kid, mum]:
			if a != null and is_instance_valid(a):
				a.queue_free()
		kid = null
		mum = null
		thief = null
		if saved.has("auto"):
			main.auto_visitors = bool(saved["auto"])
		saved = {}
		what = ""
		st = ""

	# ---- the picture of MoveEye's camera into the discovery book (and user://aufgaben/) ----
	func _photo(id: String, a, label: String, mark := true) -> void:
		var r := ferienpark_leben_rect(a)
		var n0: int = main.frame_no[0]
		main.want_snapshot(0)
		var tw: float = main.now()
		while main.frame_no[0] == n0 and main.now() - tw < 2.0:
			await get_tree().process_frame
		var jb: PackedByteArray = main.latest_jpg(0)
		if jb.is_empty():
			return
		var img := Image.new()
		if img.load_jpg_from_buffer(jb) != OK:
			return
		img.convert(Image.FORMAT_RGB8)
		var W := float(img.get_width())
		var H := float(img.get_height())
		if r.size.x > 0.0:                             # the frame like MoveEye draws it (green)
			var px := Rect2i(int(r.position.x * W), int(r.position.y * H), maxi(2, int(r.size.x * W)), maxi(2, int(r.size.y * H)))
			px = px.intersection(Rect2i(0, 0, int(W), int(H)))
			for k in range(2):
				img.fill_rect(Rect2i(px.position.x, px.position.y + k, px.size.x, 1), Color(0.2, 0.9, 0.3))
				img.fill_rect(Rect2i(px.position.x, px.end.y - 1 - k, px.size.x, 1), Color(0.2, 0.9, 0.3))
				img.fill_rect(Rect2i(px.position.x + k, px.position.y, 1, px.size.y), Color(0.2, 0.9, 0.3))
				img.fill_rect(Rect2i(px.end.x - 1 - k, px.position.y, 1, px.size.y), Color(0.2, 0.9, 0.3))
		DirAccess.make_dir_recursive_absolute("user://aufgaben")
		var path := "user://aufgaben/%s_%s.jpg" % [label, Time.get_datetime_string_from_system().replace(":", "-")]
		img.save_jpg(path, 0.85)
		result["pic"] = path
		var cut := img
		if r.size.x > 0.0:                             # the book: cut around the figure (16:9, with room around it)
			var cc := Vector2(r.get_center().x * W, r.get_center().y * H)
			var w := clampf(maxf(r.size.x * W * 3.0, r.size.y * H * 2.2 * 16.0 / 9.0), 192.0, W)
			var hh := minf(w * 9.0 / 16.0, H)
			cut = img.get_region(Rect2i(int(clampf(cc.x - w / 2.0, 0.0, W - w)), int(clampf(cc.y - hh / 2.0, 0.0, H - hh)), int(w), int(hh)))
		keep_pic = cut
		if mark:
			_book(id, cut)

	func _book(id: String, img: Image) -> void:
		var e = main.get("entdecken")
		if e != null and e.has_method("mark_found"):
			e.mark_found(id, "photo")
			if img != null and e.has_method("_store_pic"):
				e._store_pic(id, img)

	func _ew():
		var lv = _lv()
		return lv.ew if lv != null and is_instance_valid(lv) else null

	func ferienpark_leben_rect(a) -> Rect2:
		var ew = _ew()
		if ew == null or a == null or not is_instance_valid(a):
			return Rect2()
		return ew.mw_rect(a, fig_h(a), false)

	func _sees(a) -> bool:
		"""the one match of MoveEye's boxes with a figure: erlebniswelt.gd mw_reported (also «Verstecken mit MoveEye»)"""
		var ew = _ew()
		return ew != null and a != null and is_instance_valid(a) and ew.mw_reported(a, fig_h(a))

	func _flicker(figs: Array) -> void:
		"""a box of MoveEye where no figure is (counted once per new box) - a «Fehlmeldung»"""
		var ew = _ew()
		if ew == null:
			return
		var bx: Array = ew.mw_boxes()
		var bad := false
		for b in bx:
			var hit := false
			for a in figs:
				if a != null and is_instance_valid(a):
					var r: Rect2 = ew.mw_rect(a, fig_h(a), false)
					if r.size.x > 0.0 and (b as Rect2).grow(0.03).intersects(r):
						hit = true
						break
			if not hit:
				bad = true
		if bad and not _flick_prev:
			result["fehl"] = int(result.get("fehl", 0)) + 1
		_flick_prev = bad

	func _all_figs() -> Array:
		"""every figure that may be in the picture: visitors, the neighbours of the place, the figures of the Erlebniswelt"""
		var out: Array = main.visitors.get_children()
		var roots := []
		if main.scenes != null and main.scenes.root != null:
			roots.append(main.scenes.root)
		var lv = _lv()
		if lv != null and is_instance_valid(lv) and lv.ew != null:
			roots.append(lv.ew)
		for r in roots:
			for c in (r as Node).get_children():
				if c is Node3D and (c as Node3D).visible and c.has_meta("nachbar"):
					out.append(c)
		return out

	func _process(dt: float) -> void:
		if what == "" or st == "wait_build":
			return
		_acc += dt
		if _acc < 0.25:
			return
		var el := _acc
		_acc = 0.0
		st_t += el
		match what:
			"kind":
				_kind_tick(el)
			"velo":
				_velo_tick()
			"zelt":
				_zelt_tick()

	# ---- 1 · the lost child ----------------------------------------------------------------------------------------------
	func _kind_begin(lv) -> void:
		var ew = lv.ew
		var fp = lv.fp
		var hp: Vector3 = main.head.global_position
		var f: Vector3 = -(main.cams[0] as Camera3D).global_transform.basis.z
		var yaw := rad_to_deg(atan2(f.x, -f.z))
		pts = []
		for az in [randf_range(55.0, 140.0) * (1.0 if randf() < 0.5 else -1.0), randf_range(-22.0, 22.0), randf_range(-150.0, 150.0)]:
			for tries in range(12):
				var d := randf_range(10.0, 24.0)
				var w: Vector3 = main.free_spot(Vector3(hp.x, 0, hp.z) + main.pos_of(yaw + az + tries * 9.0, d), 0.5, true)
				var q: Vector3 = fp.inv * w
				if fp.H(q.x, q.z) > 0.6:
					pts.append(ew.Pg(q.x, q.z))
					break
		if pts.size() < 2:
			_say(T.t("Hier findet das Kind keinen Platz zum Spielen."))
			_finish({"state": "error"})
			return
		saved = {"auto": main.auto_visitors}
		main.auto_visitors = false
		kid = ew.actor("child", pts[0], pts[0] + Vector3(0, 0, 1), 1.0, Color(0.85, 0.12, 0.12))
		kid.remove_from_group("erleben_fig")                # a real find, not a vignette
		var bp: Vector3 = main.free_spot(Vector3(hp.x, 0, hp.z) + main.pos_of(yaw + 160.0, 3.5), 0.5, true)
		mum = ew.actor("person", ew.toP(bp), ew.toP(hp), 1.3, Color(0.2, 0.45, 0.75))
		pi = 0
		play_until = randf_range(25.0, 45.0)
		st = "search"
		st_t = 0.0
		_say(T.t("Ein Kind ist weg: rote Jacke, etwa 6 Jahre. Es spielt irgendwo um MoveEye – findet MoveEye es? (5 Min.)"))

	func _kind_tick(dt: float) -> void:
		var lv = _lv()
		if lv == null or kid == null or not is_instance_valid(kid) or mum == null or not is_instance_valid(mum):
			_finish({"state": "abgebrochen"})
			return
		var ew = lv.ew
		match st:
			"search":
				ew.idle(mum, "look", 1.0)
				if st_t < play_until:                         # plays: crouches in the grass, now and then stands up
					ew.stop(kid, dt)
					var ph := fmod(st_t, 11.0)
					kid.crouch = 1.0 if ph < 7.0 else 0.0
					ew.idle(kid, "bend" if ph < 7.0 else "look", 1.0)
				else:
					kid.crouch = 0.0
					ew.idle(kid, "", 0.0)
					var nxt: Vector3 = pts[(pi + 1) % pts.size()]
					if ew.walk(kid, nxt, 1.0, dt):
						pi = (pi + 1) % pts.size()
						st_t = 0.0
						play_until = randf_range(25.0, 50.0)
				if _sees(kid):
					result["found_s"] = snappedf(main.now() - t0, 0.1)
					result["state"] = "gefunden"
					kid.crouch = 0.0
					_photo("see.aufgabe_kind", kid, "kind")
					_say(T.t("MoveEye hat das Kind gefunden – nach %d s. Das Bild von MoveEye ist im Entdeckungsbuch.") % int(result["found_s"]))
					st = "found"
					st_t = 0.0
				elif main.now() - t0 > 300.0:
					result["state"] = "Zeit um"
					_say(T.t("Zeit um: MoveEye hat das Kind nicht gefunden. Tipp: Kopf schwenken lassen (Patrouille) oder näher.") )
					st = "found"
					st_t = 0.0
			"found":                                          # mum goes to the child, a hug, together away
				kid.crouch = 0.0
				ew.idle(kid, "", 0.0)
				var kp: Vector3 = ew.ppos(kid)
				if ew.walk(mum, kp + (ew.ppos(mum) - kp).normalized() * 0.7, 1.6, dt):
					if not mum.has_meta("hug"):
						mum.set_meta("hug", true)
						mum.play_emote("goal", 1.5)
						kid.play_emote("goal", 1.5)
						st = "home"
						st_t = 0.0
			"home":
				var away: Vector3 = ew.ppos(mum) + (ew.ppos(mum) - ew.toP(main.head.global_position)).normalized() * 30.0
				if st_t > 1.6:
					ew.walk(mum, away, 1.2, dt)
					ew.walk(kid, away + Vector3(0.7, 0, 0), 1.25, dt)
				if st_t > 22.0:
					_finish({})

	# ---- 2 · the bike thief ------------------------------------------------------------------------------------------------
	func _velo_begin() -> void:
		var bk = main.bike_node
		if bk == null or not is_instance_valid(bk) or not bk.visible or main.szenen == null:
			_say(T.t("Hier steht kein Velo."))
			_finish({"state": "error"})
			return
		saved = {"auto": main.auto_visitors}
		main.auto_visitors = false
		result["calm"] = randf() < 0.5
		st = "wait"
		st_t = 0.0
		_say(T.t("Velo-Dieb: gleich kommt jemand und trägt dein Velo weg. Bemerkt MoveEye es?"))

	func _velo_tick() -> void:
		match st:
			"wait":
				if st_t > 6.0:
					thief = main.spawn("velodieb")
					if thief == null:
						_finish({"state": "error"})
						return
					thief.set_meta("carry_bike", true)          # szenenplus.gd _take_bike: lifted and carried, not pushed
					if bool(result["calm"]):
						thief.speed = 1.35                     # a calm thief walks like somebody who owns it
					result["state"] = "unterwegs"
					st = "run"
					st_t = 0.0
			"run":
				var v = thief
				var t: float = main.now() - t0
				if v == null or not is_instance_valid(v) or v.is_queued_for_deletion() or v.done or st_t > 150.0:
					_velo_end()
					return
				if main.testrun.visible(v) and not result.has("vis_s"):
					result["vis_s"] = snappedf(t, 0.1)
				var bk = main.bike_node
				if not result.has("grab_s") and bk != null and is_instance_valid(bk) and not bk.visible:
					result["grab_s"] = snappedf(t, 0.1)
				if _sees(v):
					if not result.has("mw_s"):
						result["mw_s"] = snappedf(t, 0.1)
						_photo("see.aufgabe_velo", v, "velo")
					if result.has("grab_s") and not result.has("mw_carry_s"):
						result["mw_carry_s"] = snappedf(t, 0.1)
				_flicker(_all_figs())

	func _velo_end() -> void:
		var r := result
		var txt: String
		if r.has("mw_s"):
			var ref := float(r.get("vis_s", r["mw_s"]))
			txt = T.t("Velo-Dieb: MoveEye hat ihn erkannt, %.1f s nachdem er im Bild war.") % maxf(0.0, float(r["mw_s"]) - ref)
			txt += " " + (T.t("Auch mit dem Velo in den Händen erkannt.") if r.has("mw_carry_s") else T.t("Mit dem Velo in den Händen nicht mehr erkannt."))
		elif r.has("vis_s"):
			txt = T.t("Velo-Dieb: er war im Bild, aber MoveEye hat ihn nicht erkannt.")
		else:
			txt = T.t("Velo-Dieb: er war nie richtig im Bild der Kamera.")
		if int(r.get("fehl", 0)) > 0:
			txt += " " + T.t("Fehlmeldungen (Rahmen ohne Person): %d") % int(r["fehl"])
		_say(txt)
		_finish({"state": "fertig", "text": txt})

	# ---- 3 · guard the tent at night (a short night test run of nachtlauf.gd with its own plan) ------------------------------
	func _zelt_begin() -> void:
		if main.nacht == null:
			_finish({"state": "error"})
			return
		var plan := [{"kind": "wc", "at_s": 20.0, "torch": true}, {"kind": "fox", "at_s": 55.0}, {"kind": "wc", "at_s": 95.0, "torch": false},
				{"kind": "cat", "at_s": 125.0}, {"kind": "incident", "at_s": 160.0, "target": "tent"}]
		for i in range(plan.size()):
			plan[i]["id"] = i + 1
			plan[i]["at_h"] = snappedf(float(plan[i]["at_s"]) * 30.0 / 3600.0, 0.001)
		var r: Dictionary = main.nacht.start({"scene": "ferienpark", "from": 23.0, "to": 1.0, "speed": 30.0, "tempo": "schnell", "busy": "ruhig",
				"seed": 2026, "plan": plan, "by": "fp_aufgabe"})
		if not bool(r.get("ok", false)):
			_say(str(r.get("error", "")))
			_finish({"state": "error"})
			return
		hits = {}
		st = "night"
		_say(T.t("Zelt-Wache: 23–1 Uhr im Zeitraffer (4 Min.). Zwei WC-Gänge, Tiere und ein Eindringling – erkennt MoveEye den Richtigen?"))

	func _zelt_tick() -> void:
		var n = main.nacht
		if n.running:
			for id in n.active:
				var ent: Dictionary = n.active[id]
				var rec: Dictionary = ent["rec"]
				if not hits.has(id):
					hits[id] = {"kind": str(rec["kind"]), "mw": false}
				for a in ent["actors"]:
					if is_instance_valid(a) and not hits[id]["mw"] and _sees(a):
						hits[id]["mw"] = true
						hits[id]["mw_s"] = snappedf(n.elapsed(), 0.1)
						if str(rec["kind"]) == "incident":
							_photo("see.aufgabe_zelt", a, "zelt", false)
			_flicker(_all_figs())
			return
		# the night is over: the result
		var truth: Array = n.last.get("truth", [])
		var people := 0
		var people_mw := 0
		var animals_mw := 0
		var intr := false
		var intr_vis := false
		for rec in truth:
			var h: Dictionary = hits.get(int(rec["id"]), {})
			var mw: bool = bool(h.get("mw", false))
			match str(rec["cat"]):
				"people":
					if float(rec["vis_s"]) > 0.0:
						people += 1
						people_mw += 1 if mw else 0
				"animal":
					animals_mw += 1 if mw else 0
				"incident":
					intr = mw
					intr_vis = float(rec["vis_s"]) > 0.0
		result.merge({"intruder": intr, "intruder_visible": intr_vis, "people": people, "people_mw": people_mw, "animals_as_person": animals_mw}, true)
		var txt := T.t("Zelt-Wache:") + " " + (T.t("Eindringling erkannt") if intr else (T.t("Eindringling NICHT erkannt") if intr_vis else T.t("Eindringling war nicht im Bild")))
		txt += " · " + T.t("WC-Gänge erkannt %d von %d") % [people_mw, people] + " · " + T.t("Tiere als Person gemeldet: %d") % animals_mw
		if int(result.get("fehl", 0)) > 0:
			txt += " · " + T.t("Fehlmeldungen (Rahmen ohne Person): %d") % int(result["fehl"])
		if intr and animals_mw == 0:
			_book("see.aufgabe_zelt", keep_pic)
		_say(txt)
		_finish({"state": "fertig" if not bool(n.last.get("stopped", false)) else "abgebrochen", "text": txt})

	func control(d: Dictionary) -> Dictionary:
		match str(d.get("what", "info")):
			"kind", "velo", "zelt":
				return start(str(d["what"]))
			"stop":
				stop()
		return info()
