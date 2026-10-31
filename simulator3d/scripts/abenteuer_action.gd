extends Node
## Action-Teile im Bergtal-Abenteuer (Daniel 31.10.2026, bestätigt) - ein Teil von abenteuer_geheim.gd («hub», TEILE), das
## die Einhänge-Punkte dort weitergibt. Nicht geheim: Pfeile (Leicht) und Blinki-Tipps (Mittel, wie A3) helfen.
## Je Kapitel ein Teil (etwa +3–5 Minuten):
##   Kapitel 1  J Kuhherde: auf dem Weg zu den Weiden steht eine unruhige Herde (Kühe aus actor.gd). Ruhig mit Abstand im
##              Bogen = durch; mitten durch / zu nah = die Kühe kommen nach und stupsen (zurück zum Wegrand, niemand
##              verletzt), dann nochmals. Zu zweit: wer näher als 9 m kommt oder in 20 m Nähe rennt, wird verfolgt.
##   Kapitel 2  L Seilbahn: an der Gabelung beim Tüfelsschlund eine dritte Möglichkeit, eine alte Materialseilbahn über die
##              Schlucht. Mittendrin bleibt sie hängen: am Rad nachkurbeln (Knopf mehrmals; Leicht 4×, Mittel 6×, Schwer 8×).
##              Zu zweit kurbelt Spieler 2 (H / R2 halten), Spieler 1 fährt. Leichtes Schaukeln der Ansicht (Lite: weniger, ohne
##              Blickwinkel-Wackeln).
##   Kapitel 3  Der Steg trägt nicht: ein alter Holzsteg über den Moorbach (gleich am Anfang - nicht der Riedmoos-Steg von A3,
##              dessen Flicken mit dem Ersatzteil bleibt unverändert). Mitten drauf knackt es (Geräusch, die Ansicht wackelt).
##              Langsam = durch; rennen = ein Brett bricht, man steht wieder am Anfang und nimmt den Umweg bachaufwärts.
##              Zu zweit gibt es keine Frage: drückt einer «rennen» (Shift / H / R2), bricht es für beide.
##   Kapitel 4  O Hebel und Schleuse: an der alten Wasserfassung bei der Sennerei ist die Furt überschwemmt. Zwei Schieber
##              (links und rechts) stauen den Bach. Allein: einen ziehen, hinüberrennen, den zweiten ziehen, bevor der erste
##              zurückfällt (Leicht 14 s, Mittel 9 s, Schwer 6 s). Zu zweit: beide gleichzeitig (Shift und H bzw. R2).
##   Kapitel 5  P Spiegel am Fels: bei der Lücke im Grat eine dunkle Nische mit einem eingeritzten Zeichen. Mit dem Glas des
##              Feldstechers die Sonne hineinlenken - man muss wissen, wo sie gerade steht (Sonnenstand / Taschenuhr). Nachts,
##              bei Nebel oder Regen: «Du brauchst Sonne». Dann öffnet sich ein Spalt, durch den man den See hinter dem Grat
##              sieht (beim Karte-Lesen danach ist die richtige Antwort markiert).
## Spielstand: der Lauf in R["gh"]["act"]; was erledigt ist in R["events_done"] («gh_<teil>»).
## Steuerbefehl: über {"action": "abenteuer", "do": "choose", "value": …} wie jede Frage; {"do": "geheim", "was": "act"} = Zustand.

const T = preload("res://scripts/i18n.gd")
const Bt = preload("res://scripts/bergtal.gd")
const D = preload("res://scripts/bergtal_abenteuer_daten.gd")

const KUEHE := {"ch": 1, "stage": 3, "f": 0.52, "herd_f": 0.62}
const STEG := {"ch": 3, "stage": 0, "bach": 2}
const SEIL := {"ch": 2, "stage": 2, "a": Vector2(54, -132), "b": Vector2(8, -140)}
const SEIL_WEITER := [Vector2(8, -140), Vector2(-5, -175), Vector2(-40, -230)]
const SCHLEUSE := {"ch": 4, "stage": 0, "bach": 2}
const SPIEGEL := {"ch": 5, "stage": 3}
const KURBEL := {"leicht": 4, "normal": 6, "schwer": 8}
const FENSTER := {"leicht": 14.0, "normal": 9.0, "schwer": 6.0}      # s (echte Sekunden): so lange hält ein Schieber allein
const LAUF_S := 3.0
const RIDE_S := 5.0

var hub
var ab
var main
var _cows: Array = []
var _cow_free_t := -1.0
var _steg_brett: Node3D = null
var _cab: Node3D = null
var _seil_top := [Vector3.ZERO, Vector3.ZERO]
var _wasser: Node3D = null
var _spalt: Node3D = null
var _ride_cam := false
var _k_t := 0.0


func A() -> Dictionary:
	var r: Dictionary = hub.RR()
	if r.is_empty():
		return {}
	if not r.has("act"):
		r["act"] = {}
	return r["act"]


func _done(id: String) -> bool:
	return ab.R["events_done"].has("gh_" + id)


func _mark(id: String) -> void:
	ab.R["events_done"]["gh_" + id] = true


func _now() -> float:
	return Time.get_ticks_msec() / 1000.0


func _arrow(t: String) -> String:
	return ("→ " + t) if hub.hilfe() == "leicht" else t


func on_start() -> void:
	_free_cows()
	_ride_cam = false


func _stop(lg: Dictionary, fs: float, id: String) -> void:
	lg["f"] = fs
	ab.R["pos"] = ab._along(lg["pts"], fs)
	main.set_hour(float(lg["h0"]) + float(lg["t_h"]) * fs)
	_mark(id)
	hub.hold(id)


func _bach_x(pts: Array, bach: int) -> Array:
	return hub.cross_pt(pts, Bt.STREAMS[bach][0])


func leg_stop(lg: Dictionary, f0: float, f: float) -> bool:
	if ab.R.is_empty() or bool(lg.get("detour", false)) or bool(lg.get("gh_umweg", false)):
		return false
	var c: int = hub.ch()
	var i := int(lg.get("i", -1))
	if c == KUEHE["ch"] and i == KUEHE["stage"] and not _done("kuehe") and f0 < float(KUEHE["f"]) and f >= float(KUEHE["f"]):
		_stop(lg, float(KUEHE["f"]), "kuehe")
		_kuehe_start(lg)
		return true
	for part in [["steg", STEG, 3.0], ["schleuse", SCHLEUSE, 7.0]]:
		var P: Dictionary = part[1]
		if c != int(P["ch"]) or i != int(P["stage"]) or _done(part[0]):
			continue
		var x := _bach_x(lg["pts"], int(P["bach"]))
		if x.is_empty():
			continue
		var fs := maxf(0.0, float(x[1]) - float(part[2]) / maxf(1.0, hub.path_len(lg["pts"])))
		if f0 < fs and f >= fs:
			_stop(lg, fs, part[0])
			if part[0] == "steg":
				_steg_start(lg, x)
			else:
				_schl_start(lg, x)
			return true
	return false


# =======================================================================================================================
# J: the herd of cows
# =======================================================================================================================
func _herd_c() -> Vector2:
	var st: Dictionary = D.CHAPTERS[0]["stages"][KUEHE["stage"]]
	return ab._along(st["walk"], float(KUEHE["herd_f"]))


func _kuehe_start(_lg: Dictionary) -> void:
	_free_cows()
	var hc := _herd_c()
	var r := RandomNumberGenerator.new()
	r.seed = int(ab.R.get("seed", 1)) + 31
	for k in range(5 if not hub._lite() else 3):
		var q := hc + Vector2(r.randf_range(-7, 7), r.randf_range(-6, 6))
		var p: Vector3 = hub.wg(q)
		var v = main.spawn("cow", p, p + Vector3(r.randf_range(-1, 1), 0, r.randf_range(-1, 1)))
		if v is Node:
			v.route = [[p, 900.0, 0.0]]
			v.set_meta("gh_kuh", true)
			_cows.append(v)
	A()["kuehe"] = {"gejagt": 0, "last": -100.0}
	hub.snd("muh", hub.wg(hc, 1.2), -20.0)
	_kuehe_ask(T.t("Eine unruhige Herde steht mitten auf dem Weg. Die Kühe stampfen und schauen dich an - eine hat ein Kalb dabei."))


func _kuehe_ask(tx: String, again := false) -> void:
	var opts := [["bogen", _arrow(T.t("Ruhig und mit Abstand im weiten Bogen um die Herde (5 Min.)"))]]
	if not again:
		opts.append(["durch", T.t("Schnell mitten durch")])
	opts.append(["warten", T.t("Warten, bis sie weiterziehen (20 Min.)")])
	if hub.zweit_on():
		tx += "\n" + T.t("Zu zweit: wer zu nah kommt oder rennt, wird von den Kühen verfolgt.")
	hub.ask("gh_kuehe", T.t("Kühe auf dem Weg"), tx, opts)
	# Schweizer Wanderwege / BUL «Weidetiere»: Abstand halten (20–50 m), ruhig bleiben, nicht rennen, Kälber nie anfassen
	hub.tip(T.t("Kühe mit Kälbern beschützen sie. Ruhig bleiben, 20 bis 50 Meter Abstand halten, nicht rennen."))


func _chase(target: Vector2, who := "") -> void:
	var tp: Vector3 = hub.wg(target)
	for v in _cows:
		if is_instance_valid(v):
			v.speed = 1.6
			v.route = [[tp + Vector3(randf_range(-2, 2), 0, randf_range(-2, 2)), 4.0, 0.0], [v.position, 900.0, 0.0]]
	hub.snd("muh", tp + Vector3(0, 1.2, 0), -18.0)
	hub.shake(0.5, 0.05)
	var a: Dictionary = A().get("kuehe", {})
	a["gejagt"] = int(a.get("gejagt", 0)) + 1
	a["last"] = _now()
	main.set_hour(main.hour() + 0.08)
	ab._diary("gh_kuehe", T.t("Die Kühe kommen nach"), (who + ": " if who != "" else "") + T.t("Die Herde setzt sich in Bewegung, die Kühe kommen nach und stupsen mit der Nase. Zurück an den Wegrand - nichts passiert, nur der Schreck."))


func _kuehe_choose(v: String) -> void:
	var hc := _herd_c()
	match v:
		"bogen":
			main.set_hour(main.hour() + 0.08)
			ab._diary("gh_kuehe", T.t("Kühe auf dem Weg"), T.t("Ruhig, mit gut 30 Metern Abstand, im Bogen um die Herde. Die Kühe schauen kurz auf und fressen weiter."))
			if int(A().get("kuehe", {}).get("gejagt", 0)) == 0:
				hub.add_xp(15)
			_cow_free_t = _now() + 25.0
			hub.release()
		"durch":
			_chase(ab.R["pos"])
			_kuehe_ask(T.t("Zurück am Wegrand. Die Kühe stehen wieder auf dem Weg und schauen dich an."), true)
		"warten":
			main.set_hour(main.hour() + 0.33)
			for c in _cows:
				if is_instance_valid(c):
					c.route = [hub.wg(hc + Vector2(randf_range(-60, -30), randf_range(20, 50)))]
			ab._diary("gh_kuehe", T.t("Kühe auf dem Weg"), T.t("Nach zwanzig Minuten zieht die Herde langsam weiter den Hang hinauf."))
			_cow_free_t = _now() + 25.0
			hub.release()


func _kuehe_tick() -> void:
	var pe: Dictionary = ab.R.get("pending", {})
	if str(pe.get("kind", "")) != "gh_kuehe":
		return
	var a: Dictionary = A().get("kuehe", {})
	if _now() - float(a.get("last", -100.0)) < 5.0:
		return
	var hc := _herd_c()
	for p in hub.players():
		var d: float = (p["pos"] as Vector2).distance_to(hc)
		if d < 9.0 or (bool(p["run"]) and d < 20.0):
			_chase(p["pos"], str(p["name"]))
			var z = ab.zweit
			z.pl[int(p["i"])]["off"] = Vector2(-1.6 if int(p["i"]) == 0 else 1.6, 2.0)    # back to the group at the edge of the path
			z._say(T.t("%s: zu nah - die Kühe kommen!") % str(p["name"]))
			ab._changed()
			return


func _free_cows() -> void:
	for v in _cows:
		if is_instance_valid(v):
			v.queue_free()
	_cows = []
	_cow_free_t = -1.0


# =======================================================================================================================
# the old footbridge over the Moorbach
# =======================================================================================================================
func _steg_start(lg: Dictionary, x: Array) -> void:
	A()["steg"] = {"x": [x[0].x, x[0].y], "f": x[1], "t0": _now(), "auto": hub.zweit_on() and not ab.replaying}
	hub.snd("knarr", hub.wg(x[0], 0.5), -24.0)
	hub.shake(0.7, 0.07)
	var tx := T.t("Ein alter Holzsteg über den Moorbach. Mitten drauf knackt es laut - die Bretter geben unter den Füssen nach.")
	if bool(A()["steg"]["auto"]):
		hub.ask("gh_steg_zweit", T.t("Der alte Holzsteg"), tx + "\n" + T.t("Es knackt unter euren Füssen …"), [])
	else:
		hub.ask("gh_steg", T.t("Der alte Holzsteg"), tx, [["langsam", _arrow(T.t("Ganz langsam weiter, Schritt für Schritt"))], ["rennen", T.t("Schnell hinüberrennen")]])
		hub.tip(T.t("Altes Holz trägt, wenn man das Gewicht langsam verlagert. Wer rennt oder springt, drückt viel stärker auf ein einzelnes Brett."))


func _steg_tick() -> void:
	var s: Dictionary = A().get("steg", {})
	if s.is_empty() or not bool(s.get("auto", false)) or s.has("ende"):
		return
	if str(ab.R.get("pending", {}).get("kind", "")) != "gh_steg_zweit":
		return
	if hub.any_run():
		ab.choices.append([int(ab.R["stage"]), "gh_steg", "rennen"])
		_steg_choose("rennen")
	elif _now() - float(s["t0"]) > (0.4 if ab.fast else 3.5):
		ab.choices.append([int(ab.R["stage"]), "gh_steg", "langsam"])
		_steg_choose("langsam")


func _steg_choose(v: String) -> void:
	var s: Dictionary = A()["steg"]
	s["ende"] = v
	var X := Vector2(float(s["x"][0]), float(s["x"][1]))
	if v == "langsam":
		main.set_hour(main.hour() + 0.05)
		hub.snd("knarr", hub.wg(X, 0.5), -26.0)
		ab._diary("gh_steg", T.t("Der alte Holzsteg"), T.t("Schritt für Schritt, ganz langsam. Es knackt noch zweimal - dann bist du drüben."))
		hub.add_xp(10)
		hub.release()
		return
	hub.snd("bruch", hub.wg(X, 0.3), -14.0)
	hub.shake(0.9, 0.14)
	if _steg_brett != null and is_instance_valid(_steg_brett):
		_steg_brett.visible = false
	ab._diary("gh_steg", T.t("Krach!"), T.t("Ein Brett bricht durch - mit einem Bein im Leeren hältst du dich am Geländer. Niemand ist verletzt, du stehst wieder am Anfang des Stegs. Über das Loch geht es nicht: also der Umweg bachaufwärts."))
	var lg: Dictionary = ab.leg
	var pts: Array = lg.get("pts", [])
	var S: Vector2 = ab.R["pos"]
	var line: Array = Bt.STREAMS[int(STEG["bach"])][0]
	var up := Vector2(-1, 0)
	var best := INF
	for j in range(line.size() - 1):
		var cp := Geometry2D.get_closest_point_to_segment(X, line[j], line[j + 1])
		if cp.distance_to(X) < best:
			best = cp.distance_to(X)
			up = ((line[j] as Vector2) - (line[j + 1] as Vector2)).normalized()   # the streams run from the source: index 0 = upstream
	var dir := (X - S).normalized()
	var npts := [S, S + up * 30.0, X + up * 30.0 + dir * 5.0, X + dir * 12.0]
	var acc := 0.0
	var tot: float = hub.path_len(pts)
	for k in range(pts.size() - 1):
		acc += (pts[k] as Vector2).distance_to(pts[k + 1])
		if acc / maxf(1.0, tot) > float(s["f"]) + 12.0 / maxf(1.0, tot):
			npts.append(pts[k + 1])
	if (npts[-1] as Vector2).distance_to(pts[-1]) > 0.5:
		npts.append(pts[-1])
	(ab.R["walked"] as Array).append(S)
	var flags: Array = lg.get("flags", [])
	var nm := T.t("Umweg bachaufwärts")
	hub.release()
	ab._start_leg(int(lg.get("i", 0)), npts, flags, nm)
	ab.leg["gh_umweg"] = true


# =======================================================================================================================
# L: the old cable way over the gorge
# =======================================================================================================================
func _seil_ask() -> void:
	var s: Dictionary = A()["seil"]
	var need: int = int(KURBEL.get(hub.hilfe(), 6))
	var tx := T.t("Mitten über der Schlucht ruckt es - und die Kiste bleibt hängen. Sie schaukelt leise. Unten rauscht der Bach. Am Rad in der Kiste kann man nachkurbeln.")
	if hub.zweit_on():
		var z = ab.zweit
		tx += "\n" + T.t("Zu zweit: %s kurbelt (H bzw. R2 gedrückt halten), %s fährt.") % [str(z.names[1]), str(z.names[0])]
	hub.ask("gh_seil", T.t("Die alte Seilbahn"), tx, [["kurbeln", _arrow(T.t("Am Rad kurbeln (%d von %d)") % [int(s.get("n", 0)), need])]])
	hub.tip(T.t("Einfach weiterkurbeln - jede Umdrehung zieht die Kiste ein Stück weiter."))


func _seil_start() -> void:
	ab.R["fork_%d" % int(SEIL["stage"])] = 0
	ab._diary("fork", T.t("Weggabelung"), T.t("Mit der alten Materialseilbahn über den Tüfelsschlund"))
	ab.R["pos"] = SEIL["a"]
	ab.R["walking"] = false
	_mark("seil")
	A()["seil"] = {"k": 0.0, "phase": "fahrt1", "n": 0}
	main.set_hour(main.hour() + 0.05)
	hub.snd("knarr", hub.wg(SEIL["a"], 3.0), -22.0)
	hub.ask("gh_seil_fahrt", T.t("Die alte Seilbahn"), T.t("Du steigst in die Holzkiste. Ein Ruck - und es geht über die Schlucht."), [])
	_ride_cam = true


func _seil_kurbel() -> void:
	var s: Dictionary = A()["seil"]
	var need: int = int(KURBEL.get(hub.hilfe(), 6))
	s["n"] = int(s["n"]) + 1
	hub.snd("kurbel", _cab.global_position if _cab != null and is_instance_valid(_cab) else hub.wg(SEIL["a"], 3.0), -24.0)
	s["k"] = 0.5 + 0.06 * float(s["n"]) / float(need)
	if int(s["n"]) >= need:
		s["phase"] = "fahrt2"
		hub.ask("gh_seil_fahrt", T.t("Die alte Seilbahn"), T.t("Es ruckt wieder - die Kiste fährt weiter."), [])
	else:
		_seil_ask()


func _seil_tick(dt: float) -> void:
	var s: Dictionary = A().get("seil", {})
	if s.is_empty() or str(s.get("phase", "")) == "fertig":
		return
	var ride: float = 0.3 if ab.fast else RIDE_S
	match str(s["phase"]):
		"fahrt1":
			s["k"] = minf(0.5, float(s["k"]) + dt / ride)
			if float(s["k"]) >= 0.5:
				s["phase"] = "haengt"
				hub.snd("knarr", hub.wg(SEIL["a"].lerp(SEIL["b"], 0.5), 3.0), -18.0)
				hub.shake(0.6, 0.08)
				_seil_ask()
		"haengt":
			if hub.zweit_on():                                 # zu zweit: player 2 holds «rennen» = turns the wheel
				if bool(ab.zweit._input_of(1).get("run", false)):
					_k_t += dt
					if _k_t >= 0.6:
						_k_t = 0.0
						ab.choices.append([int(ab.R["stage"]), "gh_seil", "kurbeln"])
						_seil_kurbel()
		"fahrt2":
			s["k"] = minf(1.0, float(s["k"]) + dt / ride)
			if float(s["k"]) >= 1.0:
				s["phase"] = "fertig"
				_ride_cam = false
				main.view_cam.fov = 70.0
				main.set_hour(main.hour() + 0.1)
				ab._diary("gh_seil", T.t("Drüben!"), T.t("Die Kiste schlägt sanft an der Bergstation an. Ein bisschen weich in den Knien - aber über die Schlucht."))
				hub.add_xp(15)
				ab.R["pending"] = {}
				ab._start_leg(int(SEIL["stage"]), SEIL_WEITER, [], T.t("Von der Bergstation weiter"))
				ab.leg["gh_umweg"] = true
	var k: float = s["k"]
	ab.R["pos"] = (SEIL["a"] as Vector2).lerp(SEIL["b"], k)
	if _cab != null and is_instance_valid(_cab):
		_cab.global_position = _seil_top[0].lerp(_seil_top[1], k) + Vector3(0, -1.6 - 2.2 * sin(PI * k), 0)
		_cab.rotation.z = 0.05 * sin(main.now() * 1.7) if not hub._lite() else 0.0
	if _ride_cam and not ab.fast and DisplayServer.get_name() != "headless" and _cab != null and is_instance_valid(_cab):
		main._to_free_view()
		if main.fly_tw != null:
			main.fly_tw.kill()
		var d: Vector3 = (_seil_top[1] - _seil_top[0]).normalized()
		var eye: Vector3 = _cab.global_position + Vector3(0, 1.3, 0) - d * 0.3
		main.view_cam.global_position = eye
		main.view_cam.look_at(eye + d * 10.0 + Vector3(0, -2.5, 0), Vector3.UP)
		if not hub._lite():                                    # «Schwindel»: gentle sway and a little breathing of the view angle
			main.view_cam.rotate_object_local(Vector3(0, 0, 1), 0.035 * sin(main.now() * 1.3))
			main.view_cam.fov = 70.0 + 2.5 * sin(main.now() * 0.9)


# =======================================================================================================================
# O: two levers at the old water intake
# =======================================================================================================================
func _schl_start(_lg: Dictionary, x: Array) -> void:
	A()["schl"] = {"x": [x[0].x, x[0].y], "f": x[1], "zuerst": "", "t": -1.0, "lauf": -1.0, "bei": "", "both": [-100.0, -100.0]}
	hub.snd("wasser", hub.wg(x[0], 0.3), -22.0)
	_schl_ask(T.t("Der Bach hat die Furt überschwemmt. Daneben eine alte Wasserfassung mit zwei Schiebern - links und rechts, gut 20 Meter auseinander. Zieht man beide, staut sich das Wasser in der Fassung und die Furt wird frei. Ein Schieber allein fällt nach ein paar Sekunden zurück."))


func _schl_ask(tx: String) -> void:
	var s: Dictionary = A()["schl"]
	var opts := []
	if str(s["zuerst"]) == "":
		opts = [["links", _arrow(T.t("Linken Schieber ziehen"))], ["rechts", T.t("Rechten Schieber ziehen")], ["umweg", T.t("Lieber der Umweg bachaufwärts (25 Min.)")]]
	elif float(s["lauf"]) < 0.0:
		opts = [["lauf", _arrow(T.t("Sofort hinüber zum anderen Schieber rennen"))]]
	if hub.zweit_on():
		tx += "\n" + T.t("Zu zweit: beide gleichzeitig ziehen - Spieler 1 Shift, Spieler 2 H (oder beide R2).")
	hub.ask("gh_schleuse", T.t("Die alte Wasserfassung"), tx, opts)
	hub.tip(T.t("Zieh einen Schieber und renn sofort zum anderen - er hält nur kurz."))


func _fenster() -> float:
	var f: float = float(FENSTER.get(hub.hilfe(), 9.0))
	return f


func _schl_choose(v: String) -> void:
	var s: Dictionary = A()["schl"]
	var X := Vector2(float(s["x"][0]), float(s["x"][1]))
	match v:
		"links", "rechts":
			if str(s["zuerst"]) == "":
				s["zuerst"] = v
				s["t"] = _now()
				hub.snd("knarr", hub.wg(X, 0.5), -22.0)
				_schl_ask(T.t("Der %s Schieber ist unten - %d Sekunden, dann fällt er zurück!") % [T.t("linke") if v == "links" else T.t("rechte"), int(_fenster())])
			elif v != str(s["zuerst"]) and str(s["bei"]) == v:
				_schl_ok()
		"lauf":
			s["lauf"] = _now()
			hub.ask("gh_schleuse_lauf", T.t("Die alte Wasserfassung"), T.t("Du rennst über die nassen Steine …"), [])
		"umweg":
			_umweg(X, int(SCHLEUSE["bach"]), 0.42, float(s["f"]))


func _schl_ok() -> void:
	var s: Dictionary = A()["schl"]
	s["ok"] = true
	main.set_hour(main.hour() + 0.08)
	if _wasser != null and is_instance_valid(_wasser):
		var tw := create_tween()
		tw.tween_property(_wasser, "position:y", _wasser.position.y - 0.35, 1.5)
	hub.snd("wasser", hub.wg(Vector2(float(s["x"][0]), float(s["x"][1])), 0.3), -26.0)
	ab._diary("gh_schleuse", T.t("Die Furt ist frei"), T.t("Beide Schieber sind unten. Das Wasser staut sich in der alten Fassung, und in der Furt bleiben nur nasse Steine. Trockenen Fusses hinüber."))
	hub.add_xp(15)
	hub.release()


func _schl_tick() -> void:
	var s: Dictionary = A().get("schl", {})
	if s.is_empty() or bool(s.get("ok", false)) or not str(ab.R.get("pending", {}).get("kind", "")).begins_with("gh_schleuse"):
		return
	if hub.zweit_on():                                         # zu zweit: both at the same time
		var z = ab.zweit
		var both: Array = s["both"]
		for i in range(2):
			if bool(z._input_of(i).get("run", false)):
				both[i] = _now()
		if absf(float(both[0]) - float(both[1])) < 1.2 and _now() - minf(float(both[0]), float(both[1])) < 1.5:
			for cv in ["links", "lauf", "rechts"]:              # (so «genau gleich nochmals» plays it alone)
				ab.choices.append([int(ab.R["stage"]), "gh_schleuse", cv])
			_schl_ok()
			return
	if str(s["zuerst"]) == "":
		return
	var lauf_s: float = 0.2 if ab.fast else LAUF_S
	if float(s["lauf"]) >= 0.0 and str(s["bei"]) == "" and _now() - float(s["lauf"]) >= lauf_s:
		var other := "rechts" if str(s["zuerst"]) == "links" else "links"
		s["bei"] = other
		hub.ask("gh_schleuse", T.t("Die alte Wasserfassung"), T.t("Du bist beim anderen Schieber - schnell!"),
				[[other, _arrow(T.t("Rechten Schieber ziehen") if other == "rechts" else T.t("Linken Schieber ziehen"))]])
		return
	if _now() - float(s["t"]) > _fenster():
		s["zuerst"] = ""
		s["lauf"] = -1.0
		s["bei"] = ""
		hub.snd("knack", hub.wg(Vector2(float(s["x"][0]), float(s["x"][1])), 0.5), -20.0)
		ab._diary("gh_schleuse", T.t("Zurückgefallen"), T.t("Klack - der erste Schieber ist zurückgefallen. Nochmals!"))
		_schl_ask(T.t("Klack - der erste Schieber ist zurückgefallen. Nochmals: einen ziehen, dann schnell hinüber."))


func _umweg(X: Vector2, bach: int, h: float, fx: float) -> void:
	"""around upstream (time + strength), then on along the rest of the leg"""
	var lg: Dictionary = ab.leg
	var pts: Array = lg.get("pts", [])
	var S: Vector2 = ab.R["pos"]
	var line: Array = Bt.STREAMS[bach][0]
	var up := Vector2(-1, 0)
	var best := INF
	for j in range(line.size() - 1):
		var cp := Geometry2D.get_closest_point_to_segment(X, line[j], line[j + 1])
		if cp.distance_to(X) < best:
			best = cp.distance_to(X)
			up = ((line[j] as Vector2) - (line[j + 1] as Vector2)).normalized()
	var dir := (X - S).normalized()
	var npts := [S, S + up * 60.0, X + up * 60.0 + dir * 8.0, X + dir * 14.0]
	var acc := 0.0
	var tot: float = hub.path_len(pts)
	for k in range(pts.size() - 1):
		acc += (pts[k] as Vector2).distance_to(pts[k + 1])
		if acc / maxf(1.0, tot) > fx + 14.0 / maxf(1.0, tot):
			npts.append(pts[k + 1])
	if pts.size() > 0 and (npts[-1] as Vector2).distance_to(pts[-1]) > 0.5:
		npts.append(pts[-1])
	main.set_hour(main.hour() + h * 0.4)
	ab._diary("gh_umweg", T.t("Umweg bachaufwärts"), T.t("Bachaufwärts gibt es eine Stelle mit Steinen, auf denen man trocken hinüberkommt."))
	var flags: Array = lg.get("flags", [])
	hub.release()
	ab._start_leg(int(lg.get("i", 0)), npts, flags, T.t("Umweg bachaufwärts"))
	ab.leg["gh_umweg"] = true


# =======================================================================================================================
# P: the mirror at the rock (the glass of the binoculars)
# =======================================================================================================================
func _sonne_da() -> bool:
	return not main.is_dark() and main.sun_el() > 2.0 and not str(main.weather) in ["fog", "rain", "snow"]


static func _dir4(az: float) -> String:
	return ["Norden", "Osten", "Süden", "Westen"][int(round(fposmod(az, 360.0) / 90.0)) % 4]


func _spiegel_ask(lead := "") -> void:
	var tx := (lead + "\n" if lead != "" else "") + T.t("Neben der Lücke im Grat ist eine dunkle Felsnische. Ganz hinten ist etwas eingeritzt - aber dort ist es zu dunkel, um es zu erkennen.")
	if not ab.has("feldstecher"):
		hub.ask("gh_spiegel", T.t("Die Felsnische"), tx + "\n" + T.t("Mit einem Stück Glas könnte man Sonnenlicht hineinlenken - du hast keins dabei."), [["weiter", T.t("Weiter")]])
		return
	if not _sonne_da():
		var opts := [["weiter", T.t("Weiter")]]
		if not main.is_dark() and main.sun_el() > 2.0:
			opts.insert(0, ["warten", T.t("Warten, bis die Sonne durchkommt (30 Min.)")])
		hub.ask("gh_spiegel", T.t("Die Felsnische"), tx + "\n" + T.t("Du brauchst Sonne."), opts)
		return
	tx += "\n" + T.t("Das Glas des Feldstechers als Spiegel: von wo kommt die Sonne gerade?")
	if hub.zweit_on():
		tx += " " + T.t("(Zu zweit: einer hält das Glas, der andere sagt, wohin.)")
	if ab.has("taschenuhr") and ab.raetsel != null:
		tx += "\n" + ab.raetsel._watch_text(true)
	var right := _dir4(main.sun_pos().y)
	var opts2 := []
	for dw in ["Osten", "Süden", "Westen", "Norden"]:
		opts2.append([dw, (_arrow(T.t("Die Sonne steht im %s") % T.t(dw))) if dw == right else T.t("Die Sonne steht im %s") % T.t(dw)])
	opts2.append(["weiter", T.t("Lassen und weitergehen")])
	hub.ask("gh_spiegel", T.t("Die Felsnische"), tx, opts2)
	hub.tip(T.t("Schau auf die Schatten: sie zeigen von der Sonne weg. Am Nachmittag steht die Sonne im Südwesten bis Westen."))


func _spiegel_choose(v: String) -> void:
	match v:
		"weiter":
			ab.R["stage"] = int(ab.R["stage"]) + 1
			ab._advance()
		"warten":
			main.set_hour(main.hour() + 0.5)
			main.weather = "clear"
			_spiegel_ask()
		_:
			if v == _dir4(main.sun_pos().y) and _sonne_da():
				A()["spiegel_ok"] = true
				hub.add_xp(20)
				if _spalt != null and is_instance_valid(_spalt):
					_spalt.visible = true
				hub.snd("knack", hub.wg(_niche_xz(), 1.0), -20.0)
				ab._diary("gh_spiegel", T.t("Ein Spalt im Fels"), T.t("Der Lichtfleck tanzt über die Wand und trifft das eingeritzte Zeichen: ein Kreuz, wie auf dem letzten Kartenstück. Mit einem Knirschen gibt eine lose Steinplatte nach - ein schmaler Spalt. Durch ihn siehst du hinter den Grat: ein kleiner See glitzert."))
				ab._ask("info", T.t("Ein Spalt im Fels"), T.t("Durch den Spalt siehst du hinter den Grat: ein kleiner See glitzert."), [["ok", T.t("Weiter")]])
			else:
				A()["spiegel_falsch"] = int(A().get("spiegel_falsch", 0)) + 1
				_spiegel_ask(T.t("Der Lichtfleck landet irgendwo am Fels - nicht in der Nische. Die Sonne steht woanders."))
				if hub.hilfe() == "normal" and ab.raetsel != null:
					ab.raetsel.RR()["ask_t"] = -1000.0


func _niche_xz() -> Vector2:
	var st: Dictionary = D.CHAPTERS[4]["stages"][2]
	return (st["fork"][0][1][-1] as Vector2) + Vector2(9, -4)


# =======================================================================================================================
# hooks (abenteuer_geheim.gd)
# =======================================================================================================================
func on_ask(pe: Dictionary) -> void:
	if ab.R.is_empty():
		return
	var c: int = hub.ch()
	var si := int(ab.R.get("stage", 0))
	var kind := str(pe.get("kind", ""))
	if kind == "fork" and c == SEIL["ch"] and si == SEIL["stage"] and not _done("seil"):
		var li: Dictionary = ab.leg_info([SEIL["a"], SEIL["b"]] + SEIL_WEITER.slice(1), [])
		pe["options"].append(["gh_seil", T.t("Mit der alten Materialseilbahn über den Tüfelsschlund") + "\n" + ab.leg_text(li) + " · " + T.t("am Rad kurbeln")])
	if kind == "info" and c == SPIEGEL["ch"] and si == SPIEGEL["stage"] and str(D.CHAPTERS[4]["stages"][si].get("clue", "")) == "terrain" \
			and not _done("spiegel") and not pe.has("then_leg") and not pe.has("post"):
		pe["options"].append(["gh_spiegel", T.t("Die dunkle Felsnische daneben ansehen")])
	if kind == "read" and c == SPIEGEL["ch"] and bool(A().get("spiegel_ok", false)):
		var rd: Dictionary = D.CHAPTERS[4]["stages"][si].get("read", {})
		if not rd.is_empty():
			for o in pe["options"]:
				if bool(rd["options"][int(o[0])][1]) and not str(o[1]).begins_with("✓"):
					o[1] = "✓ " + str(o[1]).trim_prefix("→ ")
			pe["text"] = str(pe["text"]) + "\n" + T.t("Durch den Spalt im Fels hast du den See hinter dem Grat schon gesehen.")


func choose(pe: Dictionary, v: String) -> bool:
	var kind := str(pe.get("kind", ""))
	match kind:
		"gh_kuehe":
			_kuehe_choose(v)
			return true
		"gh_steg", "gh_steg_zweit":
			_steg_choose(v)
			return true
		"gh_seil":
			_seil_kurbel()
			return true
		"gh_schleuse", "gh_schleuse_lauf":
			_schl_choose(v)
			return true
		"gh_spiegel":
			_spiegel_choose(v)
			return true
		"fork":
			if v == "gh_seil":
				_seil_start()
				return true
		"info":
			if v == "gh_spiegel":
				_mark("spiegel")
				_spiegel_ask()
				return true
	return false


func tick(dt: float) -> void:
	if ab.R.is_empty():
		if not _cows.is_empty():
			_free_cows()
		return
	_kuehe_tick()
	_steg_tick()
	_seil_tick(dt)
	_schl_tick()
	if _cow_free_t > 0.0 and _now() > _cow_free_t:
		_free_cows()


func paint_pending(g: Control, pe: Dictionary) -> void:
	var kind := str(pe.get("kind", ""))
	if kind == "gh_schleuse":
		var s: Dictionary = A().get("schl", {})
		if str(s.get("zuerst", "")) != "" and not bool(s.get("ok", false)):
			var left := maxf(0.0, _fenster() - (_now() - float(s["t"])))
			g.add_child(ab._lab(T.t("Der Schieber hält noch %d s") % int(ceil(left)), 14, ab.ORG))
	elif kind == "gh_seil":
		var s2: Dictionary = A().get("seil", {})
		ab._bar(g, T.t("Kurbeln"), float(s2.get("n", 0)), float(KURBEL.get(hub.hilfe(), 6)), ab.ACC)


# =======================================================================================================================
# 3D (built by the hub when the chapter's run starts / the scene is built again)
# =======================================================================================================================
func build(root: Node3D, c: int) -> void:
	_steg_brett = null
	_cab = null
	_wasser = null
	_spalt = null
	match c:
		3:
			_build_steg(root)
		2:
			_build_seil(root)
		4:
			_build_schleuse(root)
		5:
			_build_nische(root)


func _build_steg(root: Node3D) -> void:
	var pts: Array = D.CHAPTERS[2]["stages"][0]["walk"]
	var x := _bach_x(pts, int(STEG["bach"]))
	if x.is_empty():
		return
	var X: Vector2 = x[0]
	var dir := ((pts[2] as Vector2) - (pts[1] as Vector2)).normalized()
	var n := Node3D.new()
	root.add_child(n)
	n.global_position = hub.wg(X, 0.35)
	n.rotation.y = atan2(dir.x, dir.y) + float(ab.bt().tal.rotation.y)
	var wood := Color(0.42, 0.31, 0.2)
	for sd in [-0.45, 0.45]:
		hub.mesh(n, hub.box(0.12, 0.12, 5.0), wood.darkened(0.2), Vector3(sd, 0.0, 0))
		hub.mesh(n, hub.box(0.06, 0.8, 0.06), wood.darkened(0.3), Vector3(sd, 0.45, -2.3))
		hub.mesh(n, hub.box(0.06, 0.8, 0.06), wood.darkened(0.3), Vector3(sd, 0.45, 2.3))
		hub.mesh(n, hub.box(0.05, 0.05, 4.8), wood.darkened(0.25), Vector3(sd, 0.85, 0))
	for k in range(12 if not hub._lite() else 6):
		var z := -2.3 + k * (4.6 / (11.0 if not hub._lite() else 5.0))
		var pl: MeshInstance3D = hub.mesh(n, hub.box(1.05, 0.05, 0.3 if not hub._lite() else 0.7), wood.lightened(0.05 * (k % 3)), Vector3(0, 0.08, z), Vector3(0, 0, 0.02 * (k % 2)))
		if k == (6 if not hub._lite() else 3):
			_steg_brett = pl
	if bool(A().get("steg", {}).get("ende", "") == "rennen") and _steg_brett != null:
		_steg_brett.visible = false


func _build_seil(root: Node3D) -> void:
	var a: Vector3 = hub.wg(SEIL["a"], 0.0)
	var b: Vector3 = hub.wg(SEIL["b"], 0.0)
	var wood := Color(0.36, 0.27, 0.18)
	for p in [a, b]:
		hub.mesh(root, hub.box(0.3, 6.0, 0.3), wood, p + Vector3(0, 3.0, 0))
		hub.mesh(root, hub.box(1.6, 0.25, 0.3), wood, p + Vector3(0, 5.9, 0))
	_seil_top = [a + Vector3(0, 5.8, 0), b + Vector3(0, 5.8, 0)]
	var segs := 8 if not hub._lite() else 3
	for k in range(segs):
		var p0: Vector3 = _seil_top[0].lerp(_seil_top[1], float(k) / segs) + Vector3(0, -2.2 * sin(PI * float(k) / segs), 0)
		var p1: Vector3 = _seil_top[0].lerp(_seil_top[1], float(k + 1) / segs) + Vector3(0, -2.2 * sin(PI * float(k + 1) / segs), 0)
		var L := p0.distance_to(p1)
		var mi: MeshInstance3D = hub.mesh(root, hub.box(0.04, 0.04, L), Color(0.2, 0.2, 0.2), (p0 + p1) / 2.0)
		mi.look_at_from_position((p0 + p1) / 2.0, p1, Vector3.UP)
	_cab = Node3D.new()
	root.add_child(_cab)
	_cab.global_position = _seil_top[0] + Vector3(0, -1.6, 0)
	_cab.look_at_from_position(_cab.global_position, _cab.global_position + (_seil_top[1] - _seil_top[0]).normalized(), Vector3.UP)
	hub.mesh(_cab, hub.box(1.3, 0.9, 1.6), Color(0.5, 0.38, 0.24), Vector3(0, -0.2, 0))
	hub.mesh(_cab, hub.box(0.05, 1.4, 0.05), Color(0.25, 0.25, 0.25), Vector3(0, 0.9, 0))
	hub.mesh(_cab, CylinderMesh.new(), Color(0.3, 0.3, 0.3), Vector3(0.7, 0.2, 0), Vector3(0, 0, PI / 2.0), Vector3(0.4, 0.05, 0.4))
	var s: Dictionary = A().get("seil", {})
	if not s.is_empty():
		var k2: float = float(s.get("k", 0.0))
		_cab.global_position = _seil_top[0].lerp(_seil_top[1], k2) + Vector3(0, -1.6 - 2.2 * sin(PI * k2), 0)


func _build_schleuse(root: Node3D) -> void:
	var pts: Array = D.CHAPTERS[3]["stages"][0]["walk"]
	var x := _bach_x(pts, int(SCHLEUSE["bach"]))
	if x.is_empty():
		return
	var X: Vector2 = x[0]
	var line: Array = Bt.STREAMS[int(SCHLEUSE["bach"])][0]
	var up := ((line[0] as Vector2) - (line[1] as Vector2)).normalized()
	var W: Vector2 = X + up * 12.0                                  # the intake a bit upstream of the ford
	var side := Vector2(-up.y, up.x)
	var conc := Color(0.62, 0.6, 0.56)
	var n := Node3D.new()
	root.add_child(n)
	n.global_position = hub.wg(W, 0.0)
	n.rotation.y = atan2(side.x, side.y) + float(ab.bt().tal.rotation.y)
	hub.mesh(n, hub.box(0.5, 1.0, 7.0), conc, Vector3(0, 0.3, 0))
	for sd in [-1.0, 1.0]:
		var hp := Vector3(0.6, 0.0, sd * 10.0)
		hub.mesh(n, hub.box(0.15, 1.3, 0.15), Color(0.3, 0.3, 0.32), hp + Vector3(0, 0.65, 0))
		hub.mesh(n, hub.box(0.07, 0.9, 0.07), Color(0.75, 0.2, 0.15), hp + Vector3(0.2, 1.25, 0), Vector3(0, 0, -0.5))
		hub.mesh(n, hub.box(0.3, 0.6, 0.9), conc.darkened(0.15), Vector3(-0.1, 0.4, sd * 2.0))
	_wasser = Node3D.new()
	root.add_child(_wasser)
	_wasser.global_position = hub.wg(X, 0.25)
	var wm: MeshInstance3D = hub.mesh(_wasser, hub.box(6.0, 0.05, 4.0), Color(0.35, 0.5, 0.62, 0.8), Vector3.ZERO)
	(wm.material_override as StandardMaterial3D).transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	if bool(A().get("schl", {}).get("ok", false)):
		_wasser.position.y -= 0.35


func _build_nische(root: Node3D) -> void:
	var q := _niche_xz()
	var n := Node3D.new()
	root.add_child(n)
	n.global_position = hub.wg(q, 0.0)
	var rock := Color(0.4, 0.39, 0.38)
	hub.mesh(n, hub.box(3.0, 2.6, 0.6), rock, Vector3(0, 1.3, -0.9))
	for sd in [-1.0, 1.0]:
		hub.mesh(n, hub.box(0.6, 2.6, 1.6), rock.darkened(0.1), Vector3(sd * 1.2, 1.3, 0))
	hub.mesh(n, hub.box(1.8, 0.4, 1.6), rock.darkened(0.15), Vector3(0, 2.5, 0))
	hub.mesh(n, hub.box(0.5, 0.06, 0.02), Color(0.2, 0.19, 0.18), Vector3(0, 1.3, -0.59))
	hub.mesh(n, hub.box(0.06, 0.5, 0.02), Color(0.2, 0.19, 0.18), Vector3(0, 1.3, -0.59))
	_spalt = Node3D.new()
	n.add_child(_spalt)
	hub.mesh(_spalt, hub.box(0.4, 0.4, 0.03), Color(1.0, 0.95, 0.75), Vector3(0, 1.3, -0.57), Vector3.ZERO, Vector3.ONE, true)
	hub.mesh(_spalt, hub.box(0.15, 1.8, 0.05), Color(0.05, 0.05, 0.06), Vector3(0.9, 1.2, -0.58))
	_spalt.visible = bool(A().get("spiegel_ok", false))


# =======================================================================================================================
func orte() -> Array:
	return orte_static()


static func orte_static() -> Array:
	var out := []
	var hc: Vector2 = Vector2(178, -61)
	out.append(["action_kuhherde", "Kuhherde auf dem Weg (Kapitel 1)", hc.x, hc.y, false])
	out.append(["action_seilbahn_tal", "Alte Seilbahn über den Tüfelsschlund (Kapitel 2)", float(SEIL["a"].x), float(SEIL["a"].y), false])
	var p3: Array = D.CHAPTERS[2]["stages"][0]["walk"]
	var x3: Array = preload("res://scripts/abenteuer_geheim.gd").cross_pt(p3, Bt.STREAMS[2][0])
	if not x3.is_empty():
		out.append(["action_steg_moorbach", "Alter Holzsteg am Moorbach (Kapitel 3)", x3[0].x, x3[0].y, false])
	var p4: Array = D.CHAPTERS[3]["stages"][0]["walk"]
	var x4: Array = preload("res://scripts/abenteuer_geheim.gd").cross_pt(p4, Bt.STREAMS[2][0])
	if not x4.is_empty():
		out.append(["action_wasserfassung", "Alte Wasserfassung mit zwei Schiebern (Kapitel 4)", x4[0].x, x4[0].y, false])
	var st: Dictionary = D.CHAPTERS[4]["stages"][2]
	var q: Vector2 = (st["fork"][0][1][-1] as Vector2) + Vector2(9, -4)
	out.append(["action_felsnische", "Felsnische mit Zeichen (Kapitel 5)", q.x, q.y, false])
	return out


func op(d: Dictionary) -> Dictionary:
	if str(d.get("was", "")) == "act":
		return {"ok": true, "act": A()}
	return {}


func state() -> Dictionary:
	return {"act": A().duplicate(true) if not ab.R.is_empty() else {}, "kuehe": _cows.size()}
