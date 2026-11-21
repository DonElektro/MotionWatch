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
	cam.fov = float(_shot.get("fov", 62.0)) if art == "shot" else 62.0
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
			want = _maggie_xform(dt)
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


func _maggie_xform(dt: float) -> Transform3D:
	"""steering Maggie: the camera behind her, looking past her to the next target (window, then bolt) - both in the picture"""
	var hp: Vector3 = kit.hund_pos() + Vector3(0, 0.35, 0)
	var z = kit.ziel_welt()
	if not (z is Vector3):
		return _folge_xform(hp, 2.6, dt, kit.hund_heading())
	var to: Vector3 = (z as Vector3) - hp
	to.y = 0.0
	var dir := to.normalized() if to.length() > 0.3 else Vector3(-sin(kit.hund_heading()), 0, -cos(kit.hund_heading()))
	var mid := hp.lerp(z, 0.35)
	var want := hp - dir * 3.2 + Vector3(0, 2.0, 0)
	want = frei_ziehen(want, mid)
	var tr := Transform3D(Basis.IDENTITY, want).looking_at(mid, Vector3.UP)
	return cam.global_transform.interpolate_with(tr, clampf(dt * 4.0, 0.0, 1.0)) if _blend <= 0.0 else tr


func _dist_fuer_zustand() -> float:
	match str(kit.figur.zustand):
		"haengen":
			return 3.0
		"balance", "seil":
			return 4.8
		"leiter", "klettern":
			return 3.6
	return dist


# ---- the follow camera (Besitzer 21.11.: «folgt und dreht schlecht»): springs instead of lerps -------------------------
#   * the point it looks at follows the figure on a critically damped spring, a little ahead in the direction of movement
#   * when the figure moves and nobody turned the camera for AUTO_NACH s, it swings behind it - softly (a spring on the angle,
#     its strength fades in), and not when the figure walks towards the camera (no wild half turns)
#   * mouse / right stick / swipe take over at once; afterwards it comes back smoothly
#   * the spring arm: shorter at once when rock is in the way, longer again only after the way was free for a moment
#     (no jitter between two lengths)
#   * distance and height per state: climbing / ladder / hanging closer and higher, on the log and the rope further away
const AUTO_NACH := 1.4
const VORLAUF := 0.55                 # s of movement the camera looks ahead
var _tp := Vector3.ZERO               # the smoothed point it looks at
var _tp_v := Vector3.ZERO
var _tp_ok := false
var _yaw_v := 0.0
var _vor := Vector3.ZERO              # the smoothed look-ahead
var _arm := 1.0                       # the free part of the spring arm (0.35..1)
var _arm_frei_t := 0.0
var _pit_ist := 0.32
var _p_alt := Vector3.ZERO


static func feder3(x: Vector3, v: Vector3, ziel: Vector3, w: float, dt: float) -> Array:
	"""critically damped spring (no overshoot): [x, v] after dt; w = stiffness (1/s)"""
	var f := 1.0 + 2.0 * dt * w
	var dtw2 := dt * w * w
	var det := f + dt * dtw2
	var v2 := (v + (ziel - x) * dtw2) / det
	return [x + v2 * dt, v2]


static func feder1(x: float, v: float, ziel: float, w: float, dt: float) -> Array:
	var f := 1.0 + 2.0 * dt * w
	var dtw2 := dt * w * w
	var det := f + dt * dtw2
	var v2 := (v + (ziel - x) * dtw2) / det
	return [x + v2 * dt, v2]


func _kugeln_nah(tp: Vector3, want: Vector3) -> Array:
	"""the rock details (kit_schlucht.gd kugeln: boulders, chunks, slabs - not in main.ground_y) near the arm"""
	var sch = kit.par.schlucht if kit.par != null else null
	if sch == null:
		return []
	var out := []
	var mid := (tp + want) * 0.5
	var r0 := tp.distance_to(want) * 0.5 + 3.0
	for k in sch.kugeln_welt(Callable(kit.par, "W")):
		if (k[0] as Vector3).distance_to(mid) < r0 + float(k[1]):
			out.append(k)
	return out


func _arm_frei(tp: Vector3, want: Vector3) -> float:
	"""how much of the arm from tp to want is free of ground, rock and the rock details (1 = all) - 21.11.: the camera went
	into a boulder at the bridge head (the lower half of the picture blurred grey-green)"""
	var L := tp.distance_to(want)
	var n := clampi(int(ceil(L / (0.3 if Quality.lite() else 0.2))), 6, 30)   # thin walls (0.6 m) are not jumped over
	var ks := _kugeln_nah(tp, want)
	for i in range(1, n + 1):
		var f := float(i) / float(n)
		if f * L < 0.7:
			continue                                       # right at the figure (a step, the log it stands on) does not count
		var q := tp.lerp(want, f)
		# clearance: 0.35 m at the ends, up to 0.9 m in the middle - a wall top just under the line filled the lower half of the
		# picture (21.11., bridge head: the top of the waterfall wall 0.6 m under the camera's line of sight)
		var luft := 0.35 + 0.55 * sin(clampf(f, 0.0, 1.0) * PI)
		var zu: bool = main.ground_y(q.x, q.z) + luft > q.y
		if not zu:
			for k in ks:
				if q.distance_to(k[0]) < float(k[1]) + 0.35:   # + the near plane of the camera
					zu = true
					break
		if zu:
			return maxf(0.1, f - 1.0 / float(n))
	# walls of buildings (Kapitel 1: inside the hut) are obstacles of main, not ground: the arm ends in front of them
	var o: Dictionary = main.line_blocker(tp, want)
	if not o.is_empty() and int(o.get("id", -1)) >= 0 and main.has_method("_seg_hits"):
		var t: float = main._seg_hits(o, Vector2(tp.x, tp.z), Vector2(want.x, want.z))
		if t >= 0.0:
			return clampf(t - 0.35 / maxf(L, 0.5), 0.1, 1.0)
	return 1.0


func _folge_xform(tp: Vector3, d0: float, dt: float, heading: float) -> Transform3D:
	dt = clampf(dt, 0.0, 0.1)
	var steuer := art == "folge"
	var speed: float = float(kit.figur.a.cur_speed) if steuer else kit.hund_tempo()
	var moving := speed > 0.3
	var zst := str(kit.figur.zustand) if steuer else ""
	# the look-ahead: from the real movement (not from the input), smoothed
	var vel := Vector3.ZERO
	if dt > 0.0 and _tp_ok:
		vel = (tp - _p_alt) / dt
		vel.y = 0.0
		if vel.length() > 8.0:
			vel = Vector3.ZERO                             # a jump of the figure (checkpoint, setzen)
	_p_alt = tp
	var vor_ziel := vel * VORLAUF if moving and zst in ["boden", "luft", ""] else Vector3.ZERO
	_vor = _vor.lerp(vor_ziel.limit_length(1.4), clampf(dt * 2.0, 0.0, 1.0))
	if not _tp_ok or _tp.distance_to(tp) > 6.0:
		_tp = tp
		_tp_v = Vector3.ZERO
		_tp_ok = true
	var r := feder3(_tp, _tp_v, tp + _vor, 9.0 if zst in ["klettern", "leiter", "haengen"] else 6.5, dt)
	_tp = r[0]
	_tp_v = r[1]
	# auto-rotate behind the figure
	var frei_seit: float = kit.uhr - drag_t
	if moving and frei_seit > AUTO_NACH:
		var diff := wrapf(heading - yaw, -PI, PI)
		var gegen := absf(diff) > 2.4                     # walking towards the camera: leave it (no half turn)
		if not gegen:
			var kraft := clampf((frei_seit - AUTO_NACH) / 1.0, 0.0, 1.0) * clampf(speed / 1.5, 0.4, 1.4)
			var ry := feder1(0.0, _yaw_v, diff, 2.2 * kraft + 0.01, dt)
			_yaw_v = ry[1]
			yaw = wrapf(yaw + float(ry[0]), -PI, PI)
	else:
		_yaw_v = lerpf(_yaw_v, 0.0, clampf(dt * 6.0, 0.0, 1.0))
	# height (pitch) per state, softly
	var pit := pitch
	if steuer and zst in ["seil", "haengen", "leiter", "klettern"]:
		pit = maxf(pitch, 0.62)                             # over a gap / at a wall: from higher up (never from inside the rock)
	elif steuer and zst == "balance":
		pit = maxf(pitch, 0.45)
	_pit_ist = lerpf(_pit_ist, pit, clampf(dt * 3.0, 0.0, 1.0))
	var back := Vector3(sin(yaw), 0, cos(yaw))
	var want := _tp + back * d0 * cos(_pit_ist) + Vector3(0, d0 * sin(_pit_ist), 0)
	# the spring arm with hysteresis; very close to a wall behind the figure: from higher up instead (over the wall)
	var frei := _arm_frei(_tp, want)
	if frei < 0.45:
		var pit_hoch := maxf(_pit_ist, 1.0)
		var want2 := _tp + back * d0 * cos(pit_hoch) + Vector3(0, d0 * sin(pit_hoch), 0)
		var frei2 := _arm_frei(_tp, want2)
		if frei2 > frei + 0.2:
			_pit_ist = lerpf(_pit_ist, pit_hoch, clampf(dt * 4.0, 0.0, 1.0))
			want = _tp + back * d0 * cos(_pit_ist) + Vector3(0, d0 * sin(_pit_ist), 0)
			frei = _arm_frei(_tp, want)
	if frei < _arm - 0.02:
		_arm = lerpf(_arm, frei, clampf(dt * 14.0, 0.0, 1.0))
		_arm_frei_t = 0.0
	else:
		_arm_frei_t += dt
		if _arm_frei_t > 0.35:
			_arm = lerpf(_arm, frei, clampf(dt * 1.8, 0.0, 1.0))
	dist_ist = d0 * _arm
	var at := _tp + back * dist_ist * cos(_pit_ist) + Vector3(0, dist_ist * sin(_pit_ist), 0)
	at.y = maxf(at.y, main.ground_y(at.x, at.z) + 0.4)
	var decke: float = kit.decke_bei(at, kit.figur.pos().y) if steuer else INF   # inside a building: under its ceiling
	if decke < INF:
		at.y = minf(at.y, decke - 0.2)
	for k in _kugeln_nah(_tp, at):                          # near-clip guard: never inside a rock detail
		var dk: Vector3 = at - (k[0] as Vector3)
		var rr: float = float(k[1]) + 0.3
		if dk.length() < rr:
			at = (k[0] as Vector3) + (dk.normalized() if dk.length() > 0.01 else Vector3.UP) * rr
	cam.near = 0.05
	var tr := Transform3D(Basis.IDENTITY, at).looking_at(_tp, Vector3.UP)
	return tr


func hinter_figur() -> void:
	"""snap the follow camera behind the figure"""
	if kit.figur.ok():
		yaw = float(kit.figur.a.heading)
	art = "folge"
	_blend = 0.0
	dist_ist = dist
	_tp_ok = false
	_arm = 1.0
	_yaw_v = 0.0
	_vor = Vector3.ZERO
	_pit_ist = pitch
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
			var rr := float(sh.get("r", 1.1))
			at = c + Vector3(sin(ang) * rr, 0.45 * rr / 1.1, cos(ang) * rr)
			lk = c
		"maggie":
			return _folge_xform(kit.hund_pos() + Vector3(0, 0.5, 0), 2.4, dt, kit.hund_heading())
		_:                                                  # fix
			at = _p(sh)
			lk = _blick(sh)
	at = frei_ziehen(at, lk)
	return Transform3D(Basis.IDENTITY, at).looking_at(lk, Vector3.UP)


func _blocker(at: Vector3, lk: Vector3, n: int) -> float:
	var last := -1.0
	var L := at.distance_to(lk)
	var ks := _kugeln_nah(at, lk)
	for i in range(1, n):
		var f := float(i) / float(n)
		if (1.0 - f) * L < 0.45:
			continue                                       # right at the subject (a thing lying on the ground) does not count
		var q := at.lerp(lk, f)
		if main.ground_y(q.x, q.z) + 0.2 > q.y:
			last = f
			continue
		for k in ks:                                       # the rock details (boulders, chunks, slabs) hide too
			if q.distance_to(k[0]) < float(k[1]):
				last = f
				break
	return last


func frei_ziehen(at: Vector3, lk: Vector3) -> Vector3:
	"""no rock between the camera and what it looks at: pull the camera in front of the last blocker (and above ground)"""
	at.y = maxf(at.y, main.ground_y(at.x, at.z) + 0.35)
	var n := 8 if Quality.lite() else 16
	var last := _blocker(at, lk, n)
	var up := 0.0
	while last > 0.0 and up < 4.0:                         # first: a little higher (keeps the framing)
		up += 1.0
		last = _blocker(at + Vector3(0, up, 0), lk, n)
	if last <= 0.0:
		return at + Vector3(0, up, 0)
	last = _blocker(at, lk, n)
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


var film_eintrag_jetzt := {}


func _eintrag(e: Dictionary, sprung: bool) -> void:
	film_eintrag_jetzt = e
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


# ---- the automatic check of the film shots (Koordinator 21.11.: subject >= 15 % of the picture height, nothing in front) ----
const PRUEF_ANTEIL := 0.15


func pruef_shot(sh: Dictionary, aspect := 16.0 / 9.0) -> Dictionary:
	"""where this shot puts the camera (half way through) and how it sees its subject: «ziel» [s, q, h] / «ziel_tal» [x, z, h]
	(default: the point it looks at), «groesse» = height of the subject (m, default 1.7 = a person). Returns {anteil, im_bild,
	frei, ok} - follow shots (schulter / maggie) move with the figure and are not checked."""
	var art_ := str(sh.get("art", "fix"))
	if art_ in ["schulter", "maggie"]:
		return {"ok": true, "folge": true}
	var alt := _shot
	var alt_t := _shot_t
	_shot = sh
	_shot_t = float(sh.get("d", 3.0)) * 0.5
	var tr := _shot_xform(0.0)
	_shot = alt
	_shot_t = alt_t
	var ziel: Vector3
	if sh.get("ziel_tal", null) is Array:
		var zt: Array = sh["ziel_tal"]
		ziel = kit.par.W(kit.par.G(float(zt[0]), float(zt[1]), float(zt[2])))
	elif sh.get("ziel", null) is Array:
		var z: Array = sh["ziel"]
		ziel = kit.par.welt(float(z[0]), float(z[1]), float(z[2]))
	else:
		ziel = _blick(sh)
	var gr := float(sh.get("groesse", 1.7))
	var mitte := ziel + Vector3(0, gr * 0.5, 0) if sh.has("ziel") or sh.has("ziel_tal") else ziel
	var v := mitte - tr.origin
	var fw := -tr.basis.z
	var zt2 := v.dot(fw)
	var th := tan(deg_to_rad(float(sh.get("fov", 62.0)) * 0.5))
	var anteil := gr / maxf(0.01, 2.0 * zt2 * th) if zt2 > 0.1 else 0.0
	var x := v.dot(tr.basis.x) / maxf(0.01, zt2 * th * aspect)
	var y := v.dot(tr.basis.y) / maxf(0.01, zt2 * th)
	var im_bild := zt2 > 0.1 and absf(x) < 0.9 and absf(y) < 0.9
	var frei := _blocker(tr.origin, mitte, 24) <= 0.0
	return {"anteil": snappedf(anteil, 0.01), "im_bild": im_bild, "frei": frei, "ok": im_bild and frei and anteil >= PRUEF_ANTEIL,
		"kamera": tr.origin, "abstand": snappedf(zt2, 0.1)}


func info() -> Dictionary:
	return {"art": art, "yaw": snappedf(yaw, 0.01), "pitch": snappedf(pitch, 0.01), "dist": snappedf(dist_ist, 0.01),
		"balken": snappedf(balken, 0.01), "film": film_an, "film_t": snappedf(film_t, 0.01), "film_i": film_i,
		"time_scale": Engine.time_scale, "shot": str(_shot.get("art", "")) if art == "shot" else ""}
