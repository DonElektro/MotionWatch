extends RefCounted
## Abenteuer-Kit (Grossvater-Neubau, Besitzer 20.11.2026): die eigene Spielfigur in der dritten Person - gehen, rennen,
## springen, der Weg als sanfte Führung, und Kontext-Aktionen aus Auslöse-Bereichen (kit_parcours.gd): Hochklettern (Kante),
## Leiter, Steinsprünge, Baumstamm (Balance), Seil schwingen, Maggie hochheben. Ausrutschen → an der Kante festhalten →
## tippen oder halten zum Hochziehen, sonst zurück zum letzten Checkpoint. Niemand stirbt.
## Die Figur ist actor.gd (controlled, wie explore_person.gd / maggie_story.gd) mit anim_mensch.gd (Handlungen, Fuss-IK über
## figur.gd) und denselben Regeln wie alle Gehenden (main.ground_y, main.keep_out). Die Höhe gehört diesem Skript: vor()
## läuft vor actor.gd (Steuerung setzen), nach() danach (Höhe, Wände, Stürze, Zustände).
## Zustände (zustand): boden · luft · klettern · leiter · balance · seil · haengen · heben · steuern (Maggie) · film · zurueck
## Eingabe (kit_abenteuer.gd → ein): mv (Vector2 Welt x/z, 0..1), run, sprung (gedrückt), sprung_h (gehalten), aktion,
##   vor (−1..1, Stick vorwärts), quer (−1..1, Stick quer zur Blickrichtung der Kamera)

const ActorS = preload("res://scripts/actor.gd")
const Figur = preload("res://scripts/figur.gd")

const STUFE := 0.45                  # m: so hoch steigt man ohne Springen
const FALL_OK := 1.05                # m: so tief geht man einfach hinunter (tiefer: Rand, nur mit Sprung)
const STEIL := 1.25                  # Steigung (dh / Weg): steiler = Wand
const BODEN_SCHRITT := 0.25          # m: the ground is checked in steps of at most this (fast run: several per frame)
const GRAV := 13.0
const SPRUNG_V := 4.4
const HAENGEN_S := 4.0               # s am Rand, bis es zurück zum Checkpoint geht
const LOOKS := {"enkelin": {"col": "red", "size": "", "build": "", "hat": "", "pack": true, "hair": "long"},
		"enkel": {"col": "navy", "size": "", "build": "", "hat": "cap", "pack": true},
		"tochter": {"col": "olive", "size": "", "build": "", "hat": "", "pack": true, "hair": "long"},
		"sohn": {"col": "orange", "size": "", "build": "", "hat": "", "pack": true}}

var kit                              # kit_abenteuer.gd
var main
var par                              # kit_parcours.gd
var a: Node3D = null                 # the actor
var zustand := "film"
var y := 0.0                         # feet (world)
var vy := 0.0
var vh := Vector3.ZERO               # in the air: horizontal speed (world)
var _p0 := Vector3.ZERO              # end of the last nach()
var t := 0.0                         # time in the state
var akt := {}                        # the running action: what it needs
var nass := 0                        # how often in the water (badge «Trockene Füsse»)
var hoch := 0.0                      # pulling up: 0..1
var balance := 0.0                   # −1..1 on the log
var _bal_ph := randf() * 10.0
var _absprung := {}                  # where the last jump started: {p, top, ding}
var _coyote := 0.0
var log_: Array = []                 # the last states (tests)
var kinder := false                  # Kindermodus: helps automatically


func _init(k) -> void:
	kit = k
	main = k.main
	par = k.par


func bauen(rolle: String, at: Vector3, heading: float) -> void:
	weg()
	var ac = ActorS.new()
	ac.controlled = true
	ac.look = LOOKS.get(rolle, LOOKS["enkelin"]).duplicate()
	ac.player_color = Figur.LOOK_COLS.get(str(ac.look["col"]), Figur.LOOK_COLS["red"])
	ac.name = "kit_figur"
	kit.add_child(ac)
	ac.setup(main, "person", at, at + Vector3(-sin(heading), 0, -cos(heading)), 1.5)
	if ac.body_root != null:
		ac.body_root.scale *= 0.95                       # 14–16 years: a little smaller than the grown-ups
	a = ac
	setzen(at, heading)


func weg() -> void:
	if a != null and is_instance_valid(a):
		a.queue_free()
	a = null


func ok() -> bool:
	return a != null and is_instance_valid(a)


func pos() -> Vector3:
	return Vector3(a.global_position.x, y, a.global_position.z) if ok() else Vector3.ZERO


func vorne() -> Vector3:
	var h := float(a.heading)
	return Vector3(-sin(h), 0, -cos(h))


func setzen(p: Vector3, heading = null) -> void:
	if not ok():
		return
	var g: float = main.ground_y(p.x, p.z)
	a.position = Vector3(p.x, g, p.z)
	y = g
	vy = 0.0
	vh = Vector3.ZERO
	a.cur_speed = 0.0
	a.ctl_move = Vector2.ZERO
	if heading != null:
		a.heading = float(heading)
		a.rotation.y = a.heading
	_p0 = a.position


func geh_zu(z: String) -> void:
	if z == zustand:
		return
	log_.append([snappedf(kit.uhr, 0.01), z])
	if log_.size() > 40:
		log_.pop_front()
	zustand = z
	t = 0.0
	if ok():
		a.puppet = not z in ["boden", "steuern", "film"]
		a.frozen = z in ["steuern", "film"]
		if z in ["boden", "steuern", "film"]:
			a.ctl_move = Vector2.ZERO


# =======================================================================================================================
# before actor.gd: what the figure wants
# =======================================================================================================================
func vor(dt: float, ein: Dictionary) -> void:
	if not ok():
		return
	t += dt
	if zustand == "boden":
		var mv: Vector2 = ein.get("mv", Vector2.ZERO)
		mv = _fuehrung(mv)
		a.ctl_move = mv
		a.ctl_run = bool(ein.get("run", false))
		if bool(ein.get("aktion", false)):
			_aktion_start()
		elif bool(ein.get("sprung", false)):
			_springen(mv)
	elif zustand == "film":
		a.ctl_move = kit.film_move
		a.ctl_run = kit.film_run
	else:
		a.ctl_move = Vector2.ZERO


func _fuehrung(mv: Vector2) -> Vector2:
	"""the way as a soft guide: back into the corridor, a little along the way"""
	var pts: PackedVector2Array = kit.weg
	if pts.size() < 2:
		return mv
	var v: Vector2 = par.tal_von(a.global_position)
	var best := Vector2.ZERO
	var bd := 1.0e9
	var tan := Vector2.ZERO
	for i in range(pts.size() - 1):
		var q := Geometry2D.get_closest_point_to_segment(v, pts[i], pts[i + 1])
		var dd := v.distance_to(q)
		if dd < bd:
			bd = dd
			best = q
			tan = (pts[i + 1] - pts[i]).normalized()
	var w := float(kit.daten.WEG_BREITE)
	var to_w: Vector2 = kit.tal_dir_welt(best - v)
	var tan_w: Vector2 = kit.tal_dir_welt(tan)
	if bd > w and mv.length() > 0.05:
		var k := clampf((bd - w) / 2.5, 0.0, 1.0)
		var pull: Vector2 = to_w.normalized()
		if mv.normalized().dot(pull) < 0.0:               # going away from the way: slower and turned back a little
			mv = (mv * (1.0 - 0.7 * k) + pull * mv.length() * 0.8 * k)
	elif mv.length() > 0.2 and bd < w:
		var d := mv.normalized()
		var tw: Vector2 = tan_w.normalized() * (1.0 if d.dot(tan_w) >= 0.0 else -1.0)
		if d.dot(tw) > 0.87:                             # nearly along the way: a little onto it
			mv = d.lerp(tw, 0.2).normalized() * mv.length()
	return mv.limit_length(1.0)


# =======================================================================================================================
# after actor.gd: height, walls, falls, the actions
# =======================================================================================================================
func nach(dt: float, ein: Dictionary) -> void:
	if not ok():
		return
	match zustand:
		"boden":
			_boden(dt)
		"luft":
			_luft(dt)
		"klettern":
			_klettern(dt)
		"leiter":
			_leiter(dt, ein)
		"balance":
			_balance(dt, ein)
		"seil":
			_seil(dt, ein)
		"haengen":
			_haengen(dt, ein)
		"heben":
			_heben(dt)
		"steuern", "film":
			var g: float = main.ground_y(a.position.x, a.position.z)
			if zustand == "film" and kit.film_hang:
				_haenge_pose()
				return
			y = g if absf(g - y) < 1.2 or zustand == "film" else y
		"zurueck":
			pass
	a.position.y = y
	_p0 = a.position


func _boden(dt: float) -> void:
	"""on the ground: the move of this frame, checked in steps of at most BODEN_SCHRITT (fast run up to 40 m/s: a frame is
	0.7 m - checked at once a slope looked like a step / an edge: blocked, a mantle, flying off downhill). Slow: one step, as ever."""
	var ende: Vector3 = a.position
	var start: Vector3 = _p0
	var Lg := Vector2(ende.x - start.x, ende.z - start.z).length()
	var top: float = float(a.get("run_top")) if a.get("run_top") != null else 0.0
	if top > 0.0 and float(a.cur_speed) > 4.0:            # fast run: never more than the chosen speed in a frame
		var lim := maxf(float(a.cur_speed), top * float(a.gear_speed)) * dt + 0.001
		if Lg > lim:
			ende = Vector3(start.x + (ende.x - start.x) * lim / Lg, ende.y, start.z + (ende.z - start.z) * lim / Lg)
			a.position.x = ende.x
			a.position.z = ende.z
			Lg = lim
	var n := maxi(1, int(ceil(Lg / BODEN_SCHRITT)))
	var vh_voll := Vector3(ende.x - start.x, 0, ende.z - start.z) / maxf(dt, 0.001)
	for i in range(1, n + 1):
		var f := float(i) / float(n)
		a.position.x = lerpf(start.x, ende.x, f)
		a.position.z = lerpf(start.z, ende.z, f)
		var r := _boden_teil(dt, vh_voll)
		if r != 0:
			if r == 2:
				return                                    # in the air / a step up: another state
			break                                         # blocked: stays at the last good step
		_p0 = Vector3(a.position.x, y, a.position.z)
	var gf: Dictionary = par.gefahr_bei(a.position)
	if not gf.is_empty() and str(gf["art"]) == "wasser":
		_ins_wasser()


func _boden_teil(dt: float, vh_voll: Vector3) -> int:
	"""one step from _p0 to a.position: 0 = walked on (y on the ground), 1 = blocked (back at _p0), 2 = another state"""
	var p: Vector3 = a.position
	var g: float = main.ground_y(p.x, p.z)
	var mv := Vector2(p.x - _p0.x, p.z - _p0.z)
	var L := mv.length()
	var block := false
	if L > 0.0005:
		var rise := g - y
		if rise > STUFE or (rise > 0.08 and rise / L > STEIL * 6.0):
			block = true                                  # a wall / a step too high
		else:
			var probe := Vector3(p.x, 0, p.z) + Vector3(mv.x, 0, mv.y) / L * 0.3
			var gp: float = main.ground_y(probe.x, probe.z)
			if (gp - g) / 0.3 > STEIL and gp - g > 0.12:
				block = true                              # the gorge wall: too steep
			elif y - g > FALL_OK or y - gp > FALL_OK + 0.3:
				block = true                              # an edge: only with a jump
	if block and L > 0.0005:
		# a small step (up to 0.6 m) is stepped up by itself (21.11.) - when its top is flat a little further on
		var dir := Vector3(mv.x, 0, mv.y) / L
		var vorn := Vector3(_p0.x, 0, _p0.z) + dir * 0.6
		var g2: float = main.ground_y(vorn.x, vorn.z)
		var g3: float = main.ground_y(vorn.x + dir.x * 0.2, vorn.z + dir.z * 0.2)
		var hs := g2 - y
		if hs > 0.36 and hs <= 0.62 and absf(g3 - g2) < 0.1 and kit.phase == "spiel":
			a.position.x = _p0.x
			a.position.z = _p0.z
			_hochziehen(Vector3(vorn.x, g2, vorn.z), Vector3(_p0.x, g2, _p0.z) + dir * 0.3)
			return 2
	if block:
		a.position.x = _p0.x
		a.position.z = _p0.z
		a.cur_speed = minf(float(a.cur_speed), 0.4)
		g = main.ground_y(_p0.x, _p0.z)
	var ab_ok := maxf(0.22, L * STEIL) if not block else 0.22   # down a walkable slope (fast: a long step) - on the ground
	if y - g > ab_ok:                                     # a small step down: a short fall
		vy = 0.0
		vh = vh_voll if not block else Vector3.ZERO       # (the speed of the whole frame, not of the step)
		_absprung = {"p": _p0, "top": y, "ding": par.ding_bei(_p0)}
		geh_zu("luft")
		return 2
	y = g
	return 1 if block else 0


func _springen(mv: Vector2) -> void:
	var p := pos()
	var ziel = _stein_ziel(mv)
	_absprung = {"p": p, "top": y, "ding": par.ding_bei(p)}
	if ziel is Vector3:                                   # stepping stones: the jump lands on the next stone
		var T := 0.55
		var d: Vector3 = ziel - p
		vh = Vector3(d.x, 0, d.z) / T
		vy = (d.y + 0.5 * GRAV * T * T) / T
		a.heading = atan2(-d.x, -d.z)
		a.rotation.y = a.heading
	else:
		var spd: float = float(a.cur_speed)
		vh = vorne() * spd if spd > 0.2 else Vector3(mv.x, 0, mv.y) * 1.5
		vy = SPRUNG_V
	geh_zu("luft")
	a.aktion("sprung", 0.7)
	kit.ton("sprung")


func _stein_ziel(mv: Vector2):
	"""the next stone in front (or the bank after the last one) - null = a normal jump"""
	var st := {}
	var p := pos()
	for ak in par.aktionen:
		if str(ak["art"]) == "steine":
			var d: Dictionary = ak["d"]
			var near: bool = (ak["p"] as Vector2).distance_to(par.tal_von(p)) < float(ak["r"]) + 0.5
			for sid in d["kette"]:
				if par.ding_bei(p, 0.25) == str(sid):
					near = true
			if near:
				st = d
	if st.is_empty():
		return null
	var dir := Vector3(mv.x, 0, mv.y)
	if dir.length() < 0.2:
		dir = vorne()
	dir = dir.normalized()
	var best = null
	var bs := -1.0e9
	var kand: Array = []
	for sid in st["kette"]:
		var e: Dictionary = par.dinge[str(sid)]
		var c: Vector2 = e["c"]
		kand.append(par.welt_abs(par.sq(c).x, par.sq(c).y, float(e["top"])))
	var na: Array = st["nach"]
	kand.append(par.welt(float(na[0]), float(na[1])))
	for w in kand:
		var dd: Vector3 = w - p
		var hd := Vector2(dd.x, dd.z).length()
		if hd < 0.5 or hd > 3.4:
			continue
		var al := Vector3(dd.x, 0, dd.z).normalized().dot(dir)
		if al < 0.55:
			continue
		var sc := al * 2.0 - hd * 0.4
		if sc > bs:
			bs = sc
			best = w
	return best


func _luft(dt: float) -> void:
	t += 0.0
	vy -= GRAV * dt
	var np: Vector3 = Vector3(a.position.x, 0, a.position.z) + vh * dt
	var ny := y + vy * dt
	var g: float = main.ground_y(np.x, np.z)
	if g > ny + 0.05 and g - y > 0.5:                     # hit a wall in the air: down along it
		np = Vector3(_p0.x, 0, _p0.z)
		vh = Vector3.ZERO
		g = main.ground_y(np.x, np.z)
	a.position.x = np.x
	a.position.z = np.z
	a.cur_speed = Vector2(vh.x, vh.z).length()
	y = ny
	var gf: Dictionary = par.gefahr_bei(a.position)
	if not gf.is_empty() and str(gf["art"]) == "spalt" and float(_absprung.get("top", y)) - y > 1.0:
		_greifen_am_absprung()
		return
	if y <= g:
		y = g
		vy = 0.0
		a.cur_speed = minf(Vector2(vh.x, vh.z).length(), 2.0)
		geh_zu("boden")
		kit.ton("landen")
		if not gf.is_empty() and str(gf["art"]) == "wasser":
			_ins_wasser()


func _ins_wasser() -> void:
	nass += 1
	kit.wasser(pos())
	zurueck()


func zurueck() -> void:
	"""nobody dies: a short fade, then at the last checkpoint"""
	geh_zu("zurueck")
	kit.zurueck_zum_checkpoint()


# ---- actions ----------------------------------------------------------------------------------------------------------
func _aktion_start() -> void:
	var ak: Dictionary = par.aktion_bei(a.global_position)
	if ak.is_empty():
		return
	var d: Dictionary = ak["d"]
	match str(ak["art"]):
		"kante":
			_kante_start(str(d["ding"]))
		"leiter":
			akt = {"d": d, "e": par.dinge[str(d["ding"])]}
			var e: Dictionary = akt["e"]
			var c: Vector2 = e["c"]
			var sqc: Vector2 = par.sq(c)
			var base: Vector3 = par.welt_abs(sqc.x - 0.38, sqc.y, 0.0)
			a.position = Vector3(base.x, y, base.z)
			a.heading = par.yaw_achse()
			a.rotation.y = a.heading
			geh_zu("leiter")
		"balance":
			_balance_start(d)
		"seil":
			akt = {"d": d, "e": par.dinge[str(d["ding"])], "u": 0.0, "dir": 1.0, "rueck": false}
			geh_zu("seil")
			kit.musik("action")
		"maggie_heben":
			akt = {"d": d}
			geh_zu("heben")
			kit.maggie_heben(d)
		"fund":
			kit.fund(str(d["ding"]))
		"steine":
			kit.sag(kit.tx("Springen: von Stein zu Stein."), "blinki")
		"karte":
			kit.karte_start(d)
			kit._karte["t0"] = kit.uhr
		"ir":
			kit.ir_umschalten()
		_:
			kit.aktion_fertig(str(ak["id"]))


func prompt() -> String:
	"""what the action button would do here (the HUD shows it)"""
	if zustand == "boden":
		var ak: Dictionary = par.aktion_bei(a.global_position)
		if not ak.is_empty():
			return {"kante": "Hochklettern", "leiter": "Leiter", "balance": "Balancieren", "seil": "Seil packen",
				"maggie_heben": "Maggie hochheben", "fund": "Aufheben", "steine": "Springen!", "karte": "Kartenstück hochhalten",
				"ir": "IR-Licht ein / aus"}.get(str(ak["art"]), "Aktion")
	elif zustand == "haengen":
		return "Hochziehen!"
	elif zustand == "seil" and _seil_fenster():
		return "Jetzt springen!"
	elif zustand == "leiter":
		return "Hoch / runter"
	elif zustand == "balance":
		return "Gleichgewicht halten"
	return ""


func _kante_start(id: String) -> void:
	var e: Dictionary = par.dinge[id]
	var d: Dictionary = e["d"]
	var me: Vector2 = par.sq_von(pos())
	var bs := float(d["s"])
	var sgn := signf(bs - me.x)
	if sgn == 0.0:
		sgn = 1.0
	var ls := float(d.get("ls", 0.5))
	var ts := bs - sgn * (ls - 0.45)
	var tq := clampf(me.y, float(d["q"]) - float(d.get("lq", 0.5)) + 0.3, float(d["q"]) + float(d.get("lq", 0.5)) - 0.3)
	var ziel: Vector3 = par.welt_abs(ts, tq, float(e["top"]))
	var kante: Vector3 = par.welt_abs(bs - sgn * ls, tq, float(e["top"]))   # the edge (front face, at the top)
	_hochziehen(ziel, kante)


func _hochziehen(ziel: Vector3, kante: Vector3) -> void:
	"""over an edge (owner 21.11.: «stieg komisch hoch»): below 0.6 m a simple step up; else a mantle - walk to the wall,
	the hands on the edge, pull up, one knee on the edge, stand up and step on. The time follows the height."""
	var von := pos()
	var h := ziel.y - von.y
	var dir := Vector3(kante.x - von.x, 0, kante.z - von.z)
	if dir.length() < 0.05:
		dir = Vector3(ziel.x - von.x, 0, ziel.z - von.z)
	dir = dir.normalized() if dir.length() > 0.01 else vorne()
	a.heading = atan2(-dir.x, -dir.z)
	a.rotation.y = a.heading
	if h < 0.6:
		akt = {"art": "stufe", "von": von, "nach": ziel, "dauer": 0.55}
		geh_zu("klettern")
		a.aktion("stufe", 0.55)
		return
	var w0 := Vector3(kante.x, von.y, kante.z)
	var p1 := w0 - dir * 0.38                           # standing at the wall, hands on the edge
	if (p1 - von).dot(dir) < 0.0:
		p1 = von
	var dauer := clampf(0.8 + 0.45 * h, 1.1, 2.0)
	akt = {"art": "mantle", "von": von, "p1": p1, "p2": w0 - dir * 0.18, "p3": Vector3(kante.x, 0, kante.z) + dir * 0.28,
			"nach": ziel, "kante_y": ziel.y, "dauer": dauer}
	geh_zu("klettern")
	a.aktion("hochziehen", dauer, ziel.y)
	kit.ton("klettern")


func _klettern(dt: float) -> void:
	var f := clampf(t / float(akt["dauer"]), 0.0, 1.0)
	var von: Vector3 = akt["von"]
	var nach: Vector3 = akt["nach"]
	a.cur_speed = 0.0
	var p: Vector3
	match str(akt.get("art", "")):
		"stufe":                                           # up first, then forward (the foot on the step)
			p = von.lerp(nach, smoothstep(0.15, 1.0, f))
			y = lerpf(von.y, nach.y, smoothstep(0.0, 0.6, f))
		"mantle":
			var p1: Vector3 = akt["p1"]
			var p2: Vector3 = akt["p2"]
			var p3: Vector3 = akt["p3"]
			var top: float = akt["kante_y"]
			if f < 0.2:                                     # reach: to the wall
				p = von.lerp(p1, smoothstep(0.0, 1.0, f / 0.2))
				y = von.y
			elif f < 0.55:                                  # pull: the hips up to the edge
				var u := smoothstep(0.0, 1.0, (f - 0.2) / 0.35)
				p = p1.lerp(p2, u)
				y = lerpf(von.y, maxf(von.y, top - 0.45), u)
			elif f < 0.8:                                   # knee up: on the edge
				var u2 := smoothstep(0.0, 1.0, (f - 0.55) / 0.25)
				p = p2.lerp(p3, u2)
				y = lerpf(maxf(von.y, top - 0.45), top, u2)
			else:                                           # stand up, step on
				p = p3.lerp(nach, smoothstep(0.0, 1.0, (f - 0.8) / 0.2))
				y = top
		_:                                                  # (from the ladder: up, then forward)
			p = von.lerp(nach, smoothstep(0.5, 1.0, f))
			y = lerpf(von.y, nach.y, smoothstep(0.0, 0.65, f))
	a.position.x = p.x
	a.position.z = p.z
	if f >= 1.0:
		y = nach.y
		geh_zu("boden")


func _leiter(dt: float, ein: Dictionary) -> void:
	var e: Dictionary = akt["e"]
	var top: float = par.top_welt(str(akt["d"]["ding"]))
	var v := float(ein.get("vor", 0.0))
	if absf(v) > 0.15:
		y += v * 1.2 * dt
		if akt.get("_k", 0.0) <= kit.uhr:
			akt["_k"] = kit.uhr + 0.9
			a.aktion("klettern", 1.0)
	var lo: float = main.ground_y(a.position.x, a.position.z)
	y = maxf(y, lo)
	if y >= top - 0.05:
		var o: Array = akt["d"]["oben"]
		_kante_von_leiter(par.welt_abs(float(o[0]), float(o[1]), float(e["top"])))
	elif v < -0.15 and y <= lo + 0.01:
		geh_zu("boden")


func _kante_von_leiter(ziel: Vector3) -> void:
	"""off the top of the ladder: the hands on the edge, the knee up, stand (a short mantle)"""
	var von := pos()
	var dir := Vector3(ziel.x - von.x, 0, ziel.z - von.z)
	dir = dir.normalized() if dir.length() > 0.01 else vorne()
	akt = {"art": "mantle", "von": von, "p1": von, "p2": von + dir * 0.1, "p3": von + dir * 0.45, "nach": ziel,
			"kante_y": ziel.y, "dauer": 1.0}
	geh_zu("klettern")
	a.aktion("hochziehen", 1.0, ziel.y)


func _balance_start(d: Dictionary) -> void:
	var e: Dictionary = par.dinge[str(d["ding"])]
	var c: Vector2 = e["c"]
	var sqc: Vector2 = par.sq(c)
	var ls := float(e["d"]["ls"])
	var me: Vector2 = par.sq_von(pos())
	var sgn := 1.0 if me.x < sqc.x else -1.0
	var a0: Vector3 = par.welt_abs(sqc.x - sgn * ls, sqc.y, float(e["top"]))
	var a1: Vector3 = par.welt_abs(sqc.x + sgn * ls, sqc.y, float(e["top"]))
	akt = {"d": d, "a0": a0, "a1": a1, "u": 0.0, "ding": str(d["ding"])}
	balance = 0.0
	var dd: Vector3 = a1 - a0
	a.heading = atan2(-dd.x, -dd.z)
	a.rotation.y = a.heading
	a.position = Vector3(a0.x, a0.y, a0.z)
	y = a0.y
	geh_zu("balance")
	kit.musik("spannung")


func _balance(dt: float, ein: Dictionary) -> void:
	var a0: Vector3 = akt["a0"]
	var a1: Vector3 = akt["a1"]
	var L := a0.distance_to(a1)
	var v := maxf(0.0, float(ein.get("vor", 0.0)))
	if Vector2(ein.get("mv", Vector2.ZERO)).length() > 0.2 and v < 0.1:
		v = 0.5                                          # touch / pad: any push walks on
	akt["u"] = clampf(float(akt["u"]) + v * 0.85 * dt / L, 0.0, 1.0)
	_bal_ph += dt
	var drift := (sin(_bal_ph * 1.7) * 0.5 + sin(_bal_ph * 3.9 + 1.0) * 0.35) * (0.55 + 0.6 * v)
	balance += (drift + balance * 0.9) * dt * (0.4 if kinder else 1.0)
	balance -= float(ein.get("quer", 0.0)) * 2.4 * dt
	if kinder:
		balance = move_toward(balance, 0.0, dt * 0.5)
	var p := a0.lerp(a1, float(akt["u"]))
	a.position.x = p.x
	a.position.z = p.z
	y = p.y
	a.cur_speed = v * 0.85
	a.aktion("balance", 0.3)
	a.body_root.rotation.z = balance * 0.25
	if absf(balance) >= 1.0:
		a.body_root.rotation.z = 0.0
		var rand_ := p + vorne().cross(Vector3.UP).normalized() * signf(balance) * 0.25
		_haengen_start(Vector3(rand_.x, p.y, rand_.z), p, "balance")
		kit.sag(kit.tx("Hoppla!"), "figur")
	elif float(akt["u"]) >= 1.0:
		a.body_root.rotation.z = 0.0
		var off := (a1 - a0).normalized() * 0.6
		var ziel := a1 + Vector3(off.x, 0, off.z)
		y = main.ground_y(ziel.x, ziel.z)
		a.position = Vector3(ziel.x, y, ziel.z)
		geh_zu("boden")
		kit.musik("explore")


func _seil_fenster() -> bool:
	return zustand == "seil" and float(akt.get("dir", 1.0)) > 0.0 and float(akt.get("u", 0.0)) > 0.7 and float(akt.get("u", 0.0)) < 0.99


func _seil(dt: float, ein: Dictionary) -> void:
	var d: Dictionary = akt["d"]
	var e: Dictionary = akt["e"]
	var dd: Dictionary = e["d"]
	var von: Vector2 = par.tal(float(dd["von"][0]), float(dd["von"][1]))
	var nach: Vector2 = par.tal(float(dd["nach"][0]), float(dd["nach"][1]))
	var top: float = float(e["top"])
	akt["u"] = clampf(float(akt["u"]) + float(akt["dir"]) * dt / 1.5, 0.0, 1.0)
	var u := float(akt["u"])
	var k := (1.0 - cos(PI * u)) * 0.5
	var v: Vector2 = von.lerp(nach, k)
	var feet_tal := top + 0.15 - 1.0 * sin(PI * k)
	var w: Vector3 = par.welt_abs(par.sq(v).x, par.sq(v).y, feet_tal)
	a.position.x = w.x
	a.position.z = w.z
	y = w.y
	a.cur_speed = 0.0
	a.aktion("schwingen", 0.3)
	par.seil_zu(str(d["ding"]), v, feet_tal + 2.05)
	if (bool(ein.get("sprung", false)) or (kinder and u > 0.85)) and _seil_fenster():
		var ziel: Vector3 = par.welt_abs(float(dd["nach"][0]), float(dd["nach"][1]), top)
		_absprung = {"p": pos(), "top": y + 1.0, "ding": ""}
		var T := 0.45
		var dz: Vector3 = ziel - pos()
		vh = Vector3(dz.x, 0, dz.z) / T
		vy = (dz.y + 0.5 * GRAV * T * T) / T
		par.seil_zu(str(d["ding"]), nach, top + 1.6)
		geh_zu("luft")
		a.aktion("sprung", 0.6)
		kit.ton("sprung")
		kit.zeitlupe(0.45, 0.5)
		return
	if u >= 1.0 and float(akt["dir"]) > 0.0:
		akt["dir"] = -1.0                                 # missed: back again (no fall, no penalty)
		kit.sag(kit.tx("Zu spät – nochmals!"), "blinki")
	elif u <= 0.0 and float(akt["dir"]) < 0.0:
		var st: Vector3 = par.welt_abs(float(dd["von"][0]), float(dd["von"][1]), top)
		y = st.y
		a.position = st
		par.seil_zu(str(d["ding"]), von, top + 1.6)
		geh_zu("boden")


func _greifen_am_absprung() -> void:
	"""falling into a gap after a jump from a rim: grab the edge where the jump started"""
	var p0: Vector3 = _absprung.get("p", pos())
	var rand_ := p0 + (Vector3(a.position.x, 0, a.position.z) - Vector3(p0.x, 0, p0.z)).normalized() * 0.3
	_haengen_start(Vector3(rand_.x, float(_absprung["top"]), rand_.z), p0, "rand")


func _haengen_start(griff: Vector3, zurueck_auf: Vector3, art: String) -> void:
	akt = {"griff": griff, "auf": zurueck_auf, "art": art, "von": akt.duplicate()}
	hoch = 0.0
	geh_zu("haengen")
	kit.ton("greifen")
	kit.musik("action")
	kit.regie.schuetteln(0.25)


func _haenge_pose() -> void:
	"""hanging: hands at the edge, the body under it, facing the wall"""
	var g: Vector3 = akt.get("griff", pos()) if zustand == "haengen" else kit.film_hang_p
	var auf: Vector3 = akt.get("auf", g) if zustand == "haengen" else kit.film_hang_auf
	var to := Vector3(auf.x - g.x, 0, auf.z - g.z)
	if to.length() > 0.05:
		a.heading = atan2(-to.x, -to.z)
		a.rotation.y = a.heading
	var back := -to.normalized() * 0.28 if to.length() > 0.05 else Vector3.ZERO
	a.position.x = g.x + back.x
	a.position.z = g.z + back.z
	y = g.y - 1.95 + 0.1 * hoch
	a.position.y = y
	a.cur_speed = 0.0
	a.aktion("haengen", 0.3)


func _haengen(dt: float, ein: Dictionary) -> void:
	_haenge_pose()
	if bool(ein.get("sprung", false)) or bool(ein.get("aktion", false)):
		hoch += 0.24
	if bool(ein.get("sprung_h", false)):
		hoch += dt / 1.2
	hoch = maxf(0.0, hoch - dt * 0.12)
	if kinder:
		hoch += dt * 0.5
	var frist := HAENGEN_S * (2.0 if kinder else 1.0)
	if kit.film_hang:
		frist = 1.0e9                                    # the cold open: no way back down
	if hoch >= 1.0:
		var art := str(akt["art"])
		var auf: Vector3 = akt["auf"]
		kit.aktion_fertig("haengen")
		if art == "balance":
			var alt: Dictionary = akt["von"]
			akt = {"von": pos(), "nach": auf, "dauer": 1.0}
			geh_zu("klettern")
			a.aktion("klettern", 1.0)
			kit.nach_klettern = alt                       # back onto the log afterwards
		else:
			var g: Vector3 = akt["griff"]
			var to := Vector3(auf.x - g.x, 0, auf.z - g.z).normalized() * 0.55
			akt = {"von": pos(), "nach": Vector3(g.x + to.x, g.y, g.z + to.z), "dauer": 1.1}
			geh_zu("klettern")
			a.aktion("klettern", 1.1)
		kit.musik("explore")
	elif t > frist:
		zurueck()


func _heben(dt: float) -> void:
	a.cur_speed = 0.0
	if t > 0.05 and t < 0.1:
		a.aktion("heben", 1.6)
	if t > 1.8:
		kit.aktion_fertig("maggie_heben")
		geh_zu("boden")


func info() -> Dictionary:
	var p := pos()
	var o := {"zustand": zustand, "t": snappedf(t, 0.01), "x": snappedf(p.x, 0.01), "y": snappedf(p.y, 0.01), "z": snappedf(p.z, 0.01),
		"speed": snappedf(float(a.cur_speed), 0.01) if ok() else 0.0, "nass": nass, "hoch": snappedf(hoch, 0.01),
		"balance": snappedf(balance, 0.01), "log": log_.slice(-10)}
	if ok():
		var sqp: Vector2 = par.sq_von(p)
		o["s"] = snappedf(sqp.x, 0.01)
		o["q"] = snappedf(sqp.y, 0.01)
		o["prompt"] = prompt()
	return o
