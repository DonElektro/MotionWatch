extends RefCounted
## Abenteuer-Kit (Grossvater-Neubau, Besitzer 20.11.2026): die Kamera-Regie. Baut auf der Kamera-Mathematik der Trailer-Bühne
## auf (trailer_buehne.gd kamera(): fahrt / folge / kreis, Boden-Abstand) und ergänzt sie fürs Spielen:
##   * Folgekamera hinter der Figur wie an einem Federarm: weich nachziehen, dreht sich beim Gehen selbst hinter die Figur
##     (Handy/iPad: «Kamera folgt selbst»), Wischen / Maus / rechter Stick schaut um; Kollision mit Gelände und Parcours
##     (main.ground_y entlang der Linie: der Arm wird kürzer, die Kamera bleibt nie im Fels).
##   * Einstellungen (Shots): establish (weit, hoch, langsames Treiben) · schulter (über die Schulter, Blick voraus) ·
##     reveal (tief und nah, dann hoch und weit auf das Ziel) · nah (ganz nah an einem Ding) · fix (fester Punkt) ·
##     maggie (folgt Maggie, wenn man sie steuert). Schnitt = sofort, Blende = weich (d s).
##   * Kino-Balken (Letterbox), kurze Zeitlupe (Engine.time_scale, immer zurück), Rütteln.
##   * Filmszenen: spiele(liste, fertig) – eine einfache Zeitleiste {t, k, …}: shot, sag (Untertitel), zug (Figur / Maggie
##     geht), ton, musik, zeitlupe, balken, wetter, blende, farbe (Rückblende), figur_setzen, figur_haengen, tor_auf,
##     spiel_haengen (Film endet in einer Spielszene) … Überspringen (Esc / Leertaste / Aktion / Knopf) = alles bis zum Ende
##     auf einmal anwenden (Endpositionen, Wetter, Musik), dann weiter.
## Lite: kein Kamera-Wippen, der Federarm prüft nur 6 Punkte statt 12.

const AnimKamera = preload("res://scripts/anim_kamera.gd")
const Quality = preload("res://scripts/quality.gd")

var kit
var main
var cam: Camera3D
var art := "folge"                   # folge | shot | maggie
var yaw := 0.0                       # follow: the camera stands behind at this heading (like actor.heading)
var pitch := 0.32
var dist := 4.2
var dist_ist := 4.2
var drag_t := -100.0                 # when the player looked round last (the camera then waits before it follows)
var balken := 0.0                    # 0..1 letterbox (HUD draws it)
var balken_ziel := 0.0
var _shot := {}
var _shot_t := 0.0
var _von := Transform3D()            # blend start
var _blend := 0.0
var _rueck := 0.0
var _zl_bis := -1.0                  # slow motion until (real time, s)
var _zl_f := 1.0
# film
var film: Array = []
var film_t := 0.0
var film_i := 0
var film_fertig: Callable
var film_an := false
var _zuege: Array = []               # [wer, ziel world, done]


func _init(k) -> void:
	kit = k
	main = k.main
	cam = main.view_cam


func ziel_figur() -> Vector3:
	var f = kit.figur
	if str(f.zustand) == "haengen" and f.akt.get("griff", null) is Vector3:
		return (f.akt["griff"] as Vector3) + Vector3(0, 0.25, 0)   # hanging: look at the hands on the edge (not under it)
	return f.pos() + Vector3(0, 1.45, 0)


# =======================================================================================================================
# every frame (after the figure)
# =======================================================================================================================
func tick(dt: float, real_dt: float, ein: Dictionary) -> void:
	cam = main.view_cam
	if cam == null:
		return
	AnimKamera.weg(cam)
	main.view_mode = 0
	cam.fov = 62.0
	cam.far = 7000.0
	_zeitlupe_tick(real_dt)
	balken = move_toward(balken, balken_ziel, real_dt * 2.5)
	if film_an:
		_film_tick(dt)
	var look: Vector2 = ein.get("look", Vector2.ZERO)
	if look != Vector2.ZERO:
		yaw -= look.x
		pitch = clampf(pitch + look.y, -0.25, 1.15)
		drag_t = kit.uhr
	if float(ein.get("zoom", 0.0)) != 0.0:
		dist = clampf(dist + float(ein["zoom"]), 2.2, 9.0)
	var want: Transform3D
	match art:
		"shot":
			want = _shot_xform(dt)
		"maggie":
			want = _folge_xform(kit.hund_pos() + Vector3(0, 0.5, 0), 2.6, dt, kit.hund_heading())
		_:
			want = _folge_xform(ziel_figur(), _dist_fuer_zustand(), dt, float(kit.figur.a.heading))
	if _blend > 0.0:
		_rueck = minf(1.0, _rueck + dt / _blend)
		var k := smoothstep(0.0, 1.0, _rueck)
		cam.global_transform = _von.interpolate_with(want, k)
		if _rueck >= 1.0:
			_blend = 0.0
	else:
		cam.global_transform = want
	_schuetteln_tick(dt)
	if art == "folge" and not Quality.lite():
		AnimKamera.wippen(main, cam, kit.figur.a, dt)


func _dist_fuer_zustand() -> float:
	match str(kit.figur.zustand):
		"haengen":
			return 3.0
		"balance", "seil":
			return 4.8
		"leiter", "klettern":
			return 3.6
	return dist


func _folge_xform(tp: Vector3, d0: float, dt: float, heading: float) -> Transform3D:
	var moving: bool = float(kit.figur.a.cur_speed) > 0.3 if art == "folge" else kit.hund_tempo() > 0.3
	if moving and kit.uhr - drag_t > 1.2:                  # the camera follows by itself (phone, iPad, pad and PC alike)
		yaw = lerp_angle(yaw, heading, clampf(dt * 1.1, 0.0, 1.0))
	var pit := pitch
	if art == "folge" and str(kit.figur.zustand) in ["seil", "haengen", "leiter"]:
		pit = maxf(pitch, 0.62)                             # over a gap / at a wall: look from higher up (never from inside the rock)
	var back := Vector3(sin(yaw), 0, cos(yaw))
	var want := tp + back * d0 * cos(pit) + Vector3(0, d0 * sin(pit), 0)
	# the spring arm: shorter where the ground / the course is in the way
	var n := 6 if Quality.lite() else 12
	var frac := 1.0
	var L := tp.distance_to(want)
	for i in range(1, n + 1):
		var f := float(i) / float(n)
		if f * L < 0.7:
			continue                                       # right at the figure (a step, the log it stands on) does not count
		var q := tp.lerp(want, f)
		if main.ground_y(q.x, q.z) + 0.35 > q.y:
			frac = maxf(0.4, f - 1.0 / float(n))
			break
	var dz := d0 * frac
	dist_ist = lerpf(dist_ist, dz, clampf(dt * (12.0 if dz < dist_ist else 2.5), 0.0, 1.0))
	var at := tp + back * dist_ist * cos(pit) + Vector3(0, dist_ist * sin(pit), 0)
	at.y = maxf(at.y, main.ground_y(at.x, at.z) + 0.4)
	var cur := cam.global_transform
	var tr := Transform3D(Basis.IDENTITY, at).looking_at(tp, Vector3.UP)
	return cur.interpolate_with(tr, clampf(dt * 7.0, 0.0, 1.0)) if _blend <= 0.0 else tr


func hinter_figur() -> void:
	"""snap the follow camera behind the figure"""
	if kit.figur.ok():
		yaw = float(kit.figur.a.heading)
	art = "folge"
	_blend = 0.0
	dist_ist = dist
	var tp := ziel_figur()
	var back := Vector3(sin(yaw), 0, cos(yaw))
	var at := tp + back * dist * cos(pitch) + Vector3(0, dist * sin(pitch), 0)
	at.y = maxf(at.y, main.ground_y(at.x, at.z) + 0.4)
	main.view_cam.global_transform = Transform3D(Basis.IDENTITY, at).looking_at(tp, Vector3.UP)


func zur_folge(blend := 0.8) -> void:
	_von = main.view_cam.global_transform
	_blend = blend
	_rueck = 0.0
	if kit.figur.ok():
		yaw = float(kit.figur.a.heading)
	art = "folge"


func zu_maggie(on: bool) -> void:
	_von = main.view_cam.global_transform
	_blend = 0.6
	_rueck = 0.0
	art = "maggie" if on else "folge"


# ---- shots ----------------------------------------------------------------------------------------------------------------
func shot(sh: Dictionary, schnitt := true) -> void:
	"""a shot of a film (or for photos): establish | schulter | reveal | nah | fix"""
	_von = main.view_cam.global_transform
	_shot = sh
	_shot_t = 0.0
	art = "shot"
	_blend = 0.0 if schnitt else float(sh.get("blende", 0.8))
	_rueck = 0.0


func _p(sh: Dictionary, key_s := "s", key_q := "q", key_h := "h") -> Vector3:
	if sh.has("tal"):
		return kit.par.W(kit.par.G(float(sh["tal"][0]), float(sh["tal"][1]), float(sh.get(key_h, 0.0))))
	return kit.par.welt(float(sh.get(key_s, 0.0)), float(sh.get(key_q, 0.0)), float(sh.get(key_h, 0.0)))


func _blick(sh: Dictionary) -> Vector3:
	var bt_ = sh.get("blick_tal", null)
	if bt_ is Array:
		return kit.par.W(kit.par.G(float(bt_[0]), float(bt_[1]), float(bt_[2])))
	var b = sh.get("blick", null)
	if b is Array:
		return kit.par.welt(float(b[0]), float(b[1]), float(b[2]))
	return ziel_figur()


func _shot_xform(dt: float) -> Transform3D:
	_shot_t += dt
	var sh := _shot
	var d := maxf(0.1, float(sh.get("d", 3.0)))
	var u := smoothstep(0.0, 1.0, clampf(_shot_t / d, 0.0, 1.0))
	var at: Vector3
	var lk: Vector3
	match str(sh.get("art", "fix")):
		"establish":                                       # wide and high, drifting slowly sideways and down
			var p0 := _p(sh)
			var b0 := _blick(sh)
			var side := (b0 - p0).cross(Vector3.UP).normalized()
			at = p0 + side * (u * 3.0) - Vector3(0, u * 1.5, 0)
			lk = b0
		"schulter":                                         # over the right shoulder, looking ahead
			var fp: Vector3 = kit.figur.pos()
			var fw: Vector3 = kit.figur.vorne()
			var rt := fw.cross(Vector3.UP).normalized()
			at = fp + rt * 0.55 + Vector3(0, 1.7, 0) - fw * (1.6 - 0.3 * u)
			lk = sh.get("_blick_w", null) if sh.get("_blick_w", null) is Vector3 else (_blick(sh) if sh.has("blick") else fp + fw * 8.0 + Vector3(0, 1.2, 0))
		"reveal":                                           # low and close, then up and wide onto the goal
			var p0 := _p(sh)
			var b0 := _blick(sh)
			var to := (b0 - p0)
			to.y = 0.0
			at = p0.lerp(p0 - to.normalized() * 2.5 + Vector3(0, 3.2, 0), u)
			lk = (p0 + to.normalized() * 2.0 + Vector3(0, 0.2, 0)).lerp(b0, smoothstep(0.0, 0.8, u))
		"nah", "nah_tal":
			var c := _p(sh)
			var ang := u * 0.7
			at = c + Vector3(sin(ang) * 1.1, 0.45, cos(ang) * 1.1)
			lk = c
		"maggie":
			return _folge_xform(kit.hund_pos() + Vector3(0, 0.5, 0), 2.4, dt, kit.hund_heading())
		_:                                                  # fix
			at = _p(sh)
			lk = _blick(sh)
	at = frei_ziehen(at, lk)
	return Transform3D(Basis.IDENTITY, at).looking_at(lk, Vector3.UP)


func frei_ziehen(at: Vector3, lk: Vector3) -> Vector3:
	"""no rock between the camera and what it looks at: pull the camera in front of the last blocker (and above ground)"""
	at.y = maxf(at.y, main.ground_y(at.x, at.z) + 0.35)
	var n := 8 if Quality.lite() else 16
	var last := -1.0
	for i in range(1, n):
		var f := float(i) / float(n)
		var q := at.lerp(lk, f)
		if main.ground_y(q.x, q.z) + 0.2 > q.y:
			last = f
	if last > 0.0:
		at = at.lerp(lk, minf(last + 1.5 / maxf(at.distance_to(lk), 0.5), 0.9))
		at.y = maxf(at.y, main.ground_y(at.x, at.z) + 0.35)
	return at


# ---- slow motion, shake ---------------------------------------------------------------------------------------------------
func zeitlupe(f: float, secs: float) -> void:
	_zl_f = clampf(f, 0.1, 1.0)
	_zl_bis = secs
	Engine.time_scale = _zl_f


func _zeitlupe_tick(real_dt: float) -> void:
	if _zl_bis < 0.0:
		return
	_zl_bis -= real_dt
	if _zl_bis <= 0.0:
		_zl_bis = -1.0
		Engine.time_scale = 1.0


func zeitlupe_aus() -> void:
	if _zl_bis >= 0.0 or Engine.time_scale != 1.0:
		_zl_bis = -1.0
		Engine.time_scale = 1.0


var _sch := 0.0


func schuetteln(st: float) -> void:
	_sch = maxf(_sch, st)


func _schuetteln_tick(dt: float) -> void:
	if _sch <= 0.0:
		return
	if main.has_method("motion_reduced") and main.motion_reduced():
		_sch = 0.0
		return
	_sch = maxf(0.0, _sch - dt * 0.8)
	var k := _sch * 0.06
	cam.global_transform.origin += Vector3(randf_range(-k, k), randf_range(-k, k), randf_range(-k, k))


# =======================================================================================================================
# the film timeline
# =======================================================================================================================
func spiele(liste: Array, fertig: Callable) -> void:
	film = liste.duplicate(true)
	film.sort_custom(func(x, y): return float(x.get("t", 0.0)) < float(y.get("t", 0.0)))
	film_t = 0.0
	film_i = 0
	film_fertig = fertig
	film_an = true
	_zuege.clear()
	balken_ziel = 1.0


func film_dauer() -> float:
	var d := 0.0
	for e in film:
		d = maxf(d, float(e.get("t", 0.0)) + float(e.get("d", e.get("s", 0.0) if str(e.get("k", "")) in ["zeitlupe", "blende"] else 0.0)))
	return d + 1.2


func _film_tick(dt: float) -> void:
	film_t += dt
	while film_i < film.size() and float(film[film_i].get("t", 0.0)) <= film_t:
		var e: Dictionary = film[film_i]
		film_i += 1
		_eintrag(e, false)
		if not film_an:
			return
	var offen := false
	for z in _zuege:
		if not bool(z[2]):
			offen = true
	if film_i >= film.size() and film_t >= film_dauer() and not offen:
		_film_ende()


func _eintrag(e: Dictionary, sprung: bool) -> void:
	match str(e.get("k", "")):
		"shot":
			if not sprung:
				shot(e, not e.has("blende"))
		"sag":
			if not sprung:
				kit.sag(kit.tx(str(e["text"])), str(e.get("wer", "erzaehler")), float(e.get("d", 0.0)))
		"zug":
			var w: Vector3 = kit.par.welt(float(e["s"]), float(e["q"]))
			_zuege.append([str(e.get("wer", "figur")), w, sprung])
			kit.zug(str(e.get("wer", "figur")), w, sprung)
		"ton":
			if not sprung:
				kit.ton(str(e["name"]))
		"musik":
			kit.musik(str(e["z"]))
		"zeitlupe":
			if not sprung:
				zeitlupe(float(e.get("f", 0.35)), float(e.get("s", 1.0)))
		"balken":
			balken_ziel = 1.0 if bool(e.get("an", true)) else 0.0
		"wetter":
			main.weather = str(e["w"])
		"blende":
			if not sprung:
				kit.hud.blende(float(e.get("s", 1.0)))
		"farbe":
			kit.hud.farbe(str(e.get("art", "")))
		"figur_setzen":
			kit.figur_setzen(float(e["s"]), float(e["q"]))
		"figur_haengen":
			kit.film_haengen(float(e["s"]), float(e["q"]))
		"spiel_haengen":
			kit.spiel_haengen()
		"tor_auf":
			kit.par.tor_auf(str(e["ding"]))
		"abzeichen_merken":
			kit.merke(str(e["id"]))
		_:
			kit.film_eintrag(e, sprung)


func zug_fertig(wer: String) -> void:
	for z in _zuege:
		if str(z[0]) == wer:
			z[2] = true


func ueberspringen() -> void:
	"""skip: everything left of the film at once (end positions, weather, music), then go on"""
	if not film_an:
		return
	zeitlupe_aus()
	for i in range(film_i, film.size()):
		_eintrag(film[i], true)
	film_i = film.size()
	for z in _zuege:
		if not bool(z[2]):
			kit.zug(str(z[0]), z[1], true)
			z[2] = true
	kit.hud.blende_aus()
	_film_ende()


func _film_ende() -> void:
	if not film_an:
		return
	film_an = false
	balken_ziel = 0.0
	zeitlupe_aus()
	kit.sag("", "")
	zur_folge(0.7)
	if film_fertig.is_valid():
		var cb := film_fertig
		film_fertig = Callable()
		cb.call()


func info() -> Dictionary:
	return {"art": art, "yaw": snappedf(yaw, 0.01), "pitch": snappedf(pitch, 0.01), "dist": snappedf(dist_ist, 0.01),
		"balken": snappedf(balken, 0.01), "film": film_an, "film_t": snappedf(film_t, 0.01), "film_i": film_i,
		"time_scale": Engine.time_scale, "shot": str(_shot.get("art", "")) if art == "shot" else ""}
