extends RefCounted
## «Animationen verbessern» (Daniel 31.10.2026): mehr Leben für die Menschen von actor.gd - eine Ergänzung NACH der
## Grund-Animation (actor._animate). Jede Figur «person» bekommt ein Objekt dieser Klasse (actor.anim). Es verändert nur die
## Gelenke (hips, torso, head, arms, legs), die actor.gd ohnehin bewegt - figur.gd (Ringe) und figur_paket.gd (Quaternius)
## übernehmen sie wie bisher. Für das Figuren-Paket: actor.anim_arme (Arme aus den Gelenken) / actor.anim_voll (alles).
##   1 Leerlauf    atmen, Gewicht verlagern, umschauen, Arme verschränken, Hände in den Taschen - zufällig je Figur
##   2 Übergänge   auf der Stelle drehen mit kleinen Schritten (Anlaufen / Abbremsen: actor.gd lean_acc, Tempo-Rampe)
##   3 Gelände     bergauf vorlehnen und langsamer (kürzere Schritte), bergab zurücklehnen und bremsen; Füsse auf Stufen /
##                 Steinen: Gruppe «anim_stufe» (Node3D mit Meta «stufe» = Vector3 Grösse, Oberkante = Knoten-y + Grösse.y)
##                 oder echte Kollisionen (Strahl nach unten); figur.gd setzt dann den Fuss mit seinem Zwei-Knochen-IK auf
##   4 Blick       Kopf zu Geräuschen (main.sounds), Tieren, der MoveEye-Kamera, Mitspielern - höchstens ±63° / ±20°
##   5 Handlungen  aktion(art): aufheben · klettern · kurbeln · hebel · highfive · winken · freude · schreck
##   6 Wetter      Kälte: zittern, Hände reiben · Regen: Kopf einziehen · Wind: Haare, Mantel, Schirm flattern
##   7 Gesicht     blinzeln, Mund beim Sprechen (sprechen(s), Gespräch «talk»), Freude, Schreck (Figuren aus Ringen / Formen)
##   8 Statisten   Gespräch mit Gesten (beide Hände, nicken), Kinder hüpfen / rennen kurz (nur Statisten), «grillen», «zelt»
## Leistung: Blick, Gesicht, Wetter, Spuren nur bei hoher Qualität (hoch()); weit weg (LOD) nur die Grund-Animation.
## In Lite höchstens ein paar Vergleiche pro Bild. Bei Messungen (main.measuring()) nur die Handlungen.
## Test: /control {"action": "anim", "do": "info" | "aktion" (art, s) | "sprechen" (s) | "stufe" (x, z, h)} - anim_test.gd.

const Quality = preload("res://scripts/quality.gd")
const Spuren = preload("res://scripts/anim_spuren.gd")

const ARTEN := ["aufheben", "klettern", "kurbeln", "hebel", "highfive", "winken", "freude", "schreck"]
const LEER := ["", "verschr", "taschen", "umschau", "gewicht"]
const BLICK_YAW := 1.1
const BLICK_PITCH := 0.35
const NAH := 25.0                  # m: volle Animation (Lite: NAH_LITE)
const NAH_LITE := 14.0
const WEIT := 60.0                 # m: weiter weg nur die Grund-Animation

var a                              # the actor
var main
var lod := 0                       # 0 voll · 1 einfach · 2 nur Grund-Animation
var _lod_t := 0.0
var _hoch := true
var _t := 0.0                      # own clock
var _seed := randf() * 100.0
# 1 Leerlauf
var leer := ""
var _leer_bis := 0.0
var _steh := 0.0
var _w_leer := 0.0
var _gew_s := 1.0
# 2 drehen
var _h_alt := 0.0
var _dreh := 0.0
var _dreh_ph := 0.0
var dreht := false
# 3 Gelände
var tempo_k := 1.0                 # actor._step: wanted speed × this
var _neig := 0.0
var _neig_t := 0.0
var stufe_nah := false
var _stufe_t := 0.0
var _y_stufe := 0.0
# 4 Blick
var _blick := Vector2.ZERO         # yaw, pitch (relative)
var _blick_s := Vector2.ZERO
var _blick_w := 0.0
var _blick_bis := 0.0
var _blick_next := 0.0
var _blick_ziel = null             # Vector3
# 5 Handlungen
var akt := ""
var _akt_t0 := 0.0
var _akt_bis := 0.0
var _akt_ziel = null
var _w_akt := 0.0
# 6 Wetter
var _zitter_bis := 0.0
var _zitter_next := 0.0
var _flatter: Array = []           # [node, rest rotation]
var _flat_scan := false
var _schirm := -1                  # umbrella: -1 not looked yet, 0 no, 1 yes
# 7 Gesicht
var _augen: Array = []             # eye whites and pupils
var _brauen: Array = []            # [node, rest y]
var _mund: MeshInstance3D = null
var _mund_eigen := false
var _gesicht_scan := false
var _blinz_next := 0.0
var _blinz_bis := 0.0
var sprech_bis := 0.0
var gefuehl := ""
var _gefuehl_bis := 0.0
# 8 Statisten
var _kind_bis := 0.0
var _kind_next := 0.0
var _kind_art := ""
var _kind_v0 := 0.0
# Spuren
var _tritt_n := 0


func _init(actor) -> void:
	a = actor
	main = actor.main
	_blinz_next = randf_range(0.5, 4.0)
	_kind_next = randf_range(3.0, 9.0)
	_zitter_next = randf_range(1.0, 6.0)


static func neu(actor):
	if actor.kind != "person" or actor.preview:
		return null
	return load("res://scripts/anim_mensch.gd").new(actor)


static func hoch(m) -> bool:
	"""Blick, Gesicht, Wetter, Spuren, Kamerawippen: nur bei hoher Qualität (nicht Lite, Grafik-Details «schön» / «ultra»)"""
	return not Quality.lite() and str(m.quality) in ["nice", "ultra"]


func _lod_tick(dt: float) -> void:
	_lod_t -= dt
	if _lod_t > 0.0:
		return
	_lod_t = 0.5 + randf() * 0.2
	_hoch = hoch(main)
	var d := 1.0e9
	var p: Vector3 = a.global_position
	if main.head != null:
		d = p.distance_to(main.head.global_position)
	if main.view_cam != null and main.view_cam.is_inside_tree():
		d = minf(d, p.distance_to(main.view_cam.global_position))
	var nah := NAH_LITE if Quality.lite() else NAH
	lod = 0 if d < nah else (1 if d < WEIT else 2)
	if main.has_method("measuring") and main.measuring():
		lod = maxi(lod, 2)                                     # Messung: wie bisher (nur Handlungen)
	if (a.controlled or a.puppet) and not a.is_in_group("anim_figur"):
		a.add_to_group("anim_figur")                           # fauna.gd: Vögel fliegen auch vor Spielern und Figuren auf


# ---- public ----------------------------------------------------------------------------------------------------------
func aktion(art: String, secs := -1.0, ziel = null) -> bool:
	if not art in ARTEN:
		return false
	var dauer: float = {"aufheben": 1.6, "klettern": 2.4, "kurbeln": 2.0, "hebel": 1.4, "highfive": 1.3, "winken": 2.2,
			"freude": 1.6, "schreck": 1.1}[art]
	akt = art
	_akt_t0 = a.now_s()
	_akt_bis = _akt_t0 + (secs if secs > 0.0 else dauer)
	_akt_ziel = ziel
	if art == "schreck":
		a.startle_until = maxf(a.startle_until, _akt_t0 + 0.5)
		gefuehl_zeigen("schreck", 1.4)
	elif art in ["freude", "highfive"]:
		gefuehl_zeigen("freude", 2.2)
	return true


func sprechen(secs: float) -> void:
	sprech_bis = maxf(sprech_bis, a.now_s() + clampf(secs, 0.3, 30.0))


func gefuehl_zeigen(art: String, secs := 2.0) -> void:
	gefuehl = art
	_gefuehl_bis = a.now_s() + secs


func info() -> Dictionary:
	var now: float = a.now_s()
	return {"lod": lod, "hoch": _hoch, "leer": leer, "akt": akt if now < _akt_bis else "", "dreht": dreht,
			"tempo_k": snappedf(tempo_k, 0.01), "neigung": snappedf(_neig, 0.01), "stufe_nah": stufe_nah,
			"blick": [snappedf(_blick.x, 0.01), snappedf(_blick.y, 0.01)], "blick_w": snappedf(_blick_w, 0.01),
			"spricht": now < sprech_bis, "gefuehl": gefuehl if now < _gefuehl_bis else "", "augen": _augen.size(),
			"mund": _mund != null, "zittert": now < _zitter_bis, "kind": _kind_art if now < _kind_bis else "",
			"voll": bool(a.anim_voll), "arme": bool(a.anim_arme)}


# ---- every frame (end of actor._animate) -----------------------------------------------------------------------------
func post(dt: float, spd: float, now: float, idle: String) -> void:
	_t += dt
	_frame = true
	_lod_tick(dt)
	a.anim_voll = false
	a.anim_arme = false
	if a.variant in ["cyclist", "escooter", "wheelchair"] or a.hips == null or a.stars != null:
		return
	var aktiv: bool = now < _akt_bis
	if not aktiv and _w_akt <= 0.0 and lod >= 2:
		tempo_k = 1.0
		return
	var k: float = clampf(dt * 10.0, 0.0, 1.0)
	var pr: float = clampf(a.prone, 0.0, 1.0)
	var em: String = a.emote if now < a.emote_until else ""
	var frei: bool = pr < 0.1 and a.crouch < 0.1 and a._sit_k < 0.05 and em == "" and now >= a.startle_until
	var steht: bool = spd < 0.05 and frei and idle in ["", "look"] and not a.carry and not a.phone_out and a.variant != "stroller" \
			and a.arm_hold.is_empty() and not (now < a.wait_until and a._at_door())
	_steh = _steh + dt if steht else 0.0
	if lod < 2:
		_gelaende(dt, spd)
		_drehen(dt, spd, frei)
		_leerlauf(dt, now, steht, k)
		_statist(dt, now, idle, spd, k)
		if _hoch and lod == 0:
			_wetter(dt, now, steht, k, idle)
			_blick_tick(dt, now, idle)
			_gesicht(dt, now, idle)
			_spuren(dt, spd)
	_handlung(dt, now, k)


# ---- 1 Leerlauf --------------------------------------------------------------------------------------------------------
func _leerlauf(dt: float, now: float, steht: bool, k: float) -> void:
	if steht and _steh > 1.5:
		if now >= _leer_bis:
			var w := {"": 2.0, "verschr": 1.0, "taschen": 1.0 if a.variant != "child" else 0.2, "umschau": 1.2, "gewicht": 1.5}
			if a.controlled:
				w["umschau"] = 0.4
			if main.ambient < 4.0:
				w["taschen"] = 2.5                              # in the cold the hands go into the pockets
			leer = _wahl(w)
			_leer_bis = now + randf_range(3.0, 9.0)
			_gew_s = 1.0 if randf() < 0.5 else -1.0
	else:
		leer = ""
		_leer_bis = 0.0
	_w_leer = move_toward(_w_leer, 1.0 if leer != "" and steht else 0.0, dt * 2.2)
	if _w_leer <= 0.0:
		return
	var w2 := smoothstep(0.0, 1.0, _w_leer)
	var br: float = sin(_t * 1.5 + _seed)                         # breathing: the chest rises, the shoulders a little
	_add(a.torso, ^"rotation:x", 0.012 * br * w2)
	match leer:
		"verschr":
			a.anim_arme = true
			for i in range(2):
				var s: int = a.arms[i][1]
				_arm(i, 0.32, -0.12 * s, 1.85 + (0.12 if s > 0 else 0.0), w2, 1.05 * s)   # the upper arm turned in: forearms across
		"taschen":
			a.anim_arme = true
			for i in range(2):
				var s2: int = a.arms[i][1]
				_arm(i, -0.14, 0.16 * s2, 0.32, w2)
		"umschau":
			var yaw := sin((_t + _seed) * 0.55) * 0.95 * w2
			_put(a.head, ^"rotation:y", lerpf(a.head.rotation.y, yaw, 1.0))
			_add(a.torso, ^"rotation:y", yaw * 0.15)
		"gewicht":                                              # the weight on one leg, the other knee relaxed
			_put(a.hips, ^"rotation:z", lerpf(a.hips.rotation.z, 0.07 * _gew_s, w2))
			_add(a.body_root, ^"position:x", 0.03 * _gew_s * w2)
			for l in a.legs:
				if int(l[1]) != int(_gew_s):
					_put(l[2], ^"rotation:x", lerpf((l[2] as Node3D).rotation.x, -0.22, w2))
					_put(l[0], ^"rotation:x", lerpf((l[0] as Node3D).rotation.x, 0.08, w2))
			_put(a.torso, ^"rotation:z", lerpf(a.torso.rotation.z, -0.03 * _gew_s, w2))


# ---- 2 auf der Stelle drehen ------------------------------------------------------------------------------------------
func _drehen(dt: float, spd: float, frei: bool) -> void:
	var dh: float = wrapf(float(a.heading) - _h_alt, -PI, PI)
	_h_alt = a.heading
	_dreh = lerpf(_dreh, absf(dh) / maxf(dt, 0.001), clampf(dt * 8.0, 0.0, 1.0))
	dreht = not a.controlled and spd < 0.15 and frei and _dreh > 0.5
	if not dreht:
		return
	_dreh_ph += dt * PI * 3.2                                    # small steps, ~1.6 per second
	for l in a.legs:
		var lift: float = maxf(0.0, sin(_dreh_ph + (0.0 if int(l[1]) > 0 else PI)))
		_add(l[0], ^"rotation:x", 0.22 * lift)
		_add(l[2], ^"rotation:x", -(0.42 * lift))
	_add(a.body_root, ^"position:y", 0.012 * absf(sin(_dreh_ph)))


# ---- 3 Gelände ---------------------------------------------------------------------------------------------------------
func _gelaende(dt: float, spd: float) -> void:
	_neig_t -= dt
	if _neig_t <= 0.0:
		_neig_t = 0.2
		var s := 0.0
		if main.hilly() and not a.puppet:
			var fw := Vector3(-sin(a.heading), 0, -cos(a.heading))
			var p: Vector3 = a.global_position
			s = (main.ground_y(p.x + fw.x * 0.6, p.z + fw.z * 0.6) - main.ground_y(p.x - fw.x * 0.6, p.z - fw.z * 0.6)) / 1.2
		_neig = clampf(s, -0.7, 0.7)
		tempo_k = 1.0 - (0.85 * _neig if _neig > 0.0 else 0.55 * -_neig)   # uphill shorter steps, downhill braking
		tempo_k = clampf(tempo_k, 0.55, 1.0)
		_stufe_t -= 0.2
		if _stufe_t <= 0.0:
			_stufe_t = 0.4
			stufe_nah = _stufen_nah()
	if spd > 0.1 and absf(_neig) > 0.04 and a.prone < 0.1:
		var lean := -0.5 * _neig if _neig > 0.0 else 0.22 * -_neig
		_add(a.torso, ^"rotation:x", lean)
		if _neig < 0.0:
			for l in a.legs:
				_add(l[2], ^"rotation:x", -(0.25 * -_neig))      # downhill: the knees bend more (braking)


func _stufen_nah() -> bool:
	if not a.is_inside_tree():
		return false
	var p: Vector3 = a.global_position
	for n in a.get_tree().get_nodes_in_group("anim_stufe"):
		if n is Node3D and (n as Node3D).global_position.distance_to(p) < 3.0:
			return true
	return false


func boden(x: float, z: float, g: float) -> float:
	"""figur.gd: the ground under a foot - the highest step / stone there (or a real collider), else g"""
	var out := g
	if not a.is_inside_tree():
		return out
	for n in a.get_tree().get_nodes_in_group("anim_stufe"):
		if not n is Node3D:
			continue
		var nd := n as Node3D
		var sz: Vector3 = nd.get_meta("stufe", Vector3(0.5, 0.2, 0.5))
		var q := nd.global_transform.affine_inverse() * Vector3(x, nd.global_position.y, z)
		if absf(q.x) <= sz.x * 0.5 and absf(q.z) <= sz.z * 0.5:
			out = maxf(out, nd.global_position.y + sz.y)
	var w = a.get_world_3d()
	if w != null and w.direct_space_state != null:
		var rq := PhysicsRayQueryParameters3D.create(Vector3(x, g + 1.2, z), Vector3(x, g - 0.3, z))
		var hit: Dictionary = w.direct_space_state.intersect_ray(rq)
		if not hit.is_empty():
			out = maxf(out, float((hit["position"] as Vector3).y))
	return out


func vor_sync(dt: float) -> void:
	"""before figur.sync: on a step the whole figure goes up a little (the feet are put down by the IK of figur.gd)"""
	if not _frame:
		return
	if not stufe_nah:
		_y_stufe = move_toward(_y_stufe, 0.0, dt * 1.5)
		if _y_stufe > 0.0:
			_add(a.body_root, ^"position:y", _y_stufe)
		return
	var p: Vector3 = a.global_position
	var h := boden(p.x, p.z, p.y) - p.y
	_y_stufe = lerpf(_y_stufe, clampf(h, 0.0, 0.5), clampf(dt * 8.0, 0.0, 1.0))
	_add(a.body_root, ^"position:y", _y_stufe)


func nach_sync(_dt: float) -> void:
	"""after the figure from the pack: it plays its own clip - the lean on a slope goes onto the whole body"""
	var fr := _frame
	_frame = false
	if not fr or a.fig == null or not a.fig.has_method("_choose") or lod >= 2:
		return
	if absf(_neig) > 0.04 and a.cur_speed > 0.1:
		_add(a.body_root, ^"rotation:x", (-0.18 * _neig if _neig > 0.0 else 0.08 * -_neig))


# ---- 4 Blick -----------------------------------------------------------------------------------------------------------
func _blick_tick(dt: float, now: float, idle: String) -> void:
	if a.controlled or not idle in ["", "look", "talk"] or a.prone > 0.3:
		_blick_w = move_toward(_blick_w, 0.0, dt * 3.0)
		return
	if now >= _blick_next:
		_blick_next = now + randf_range(1.2, 3.5)
		_blick_ziel = _blick_suchen()
		_blick_bis = now + randf_range(1.0, 2.8)
	var on: bool = _blick_ziel != null and now < _blick_bis
	_blick_w = move_toward(_blick_w, 1.0 if on else 0.0, dt * 2.5)
	if _blick_w <= 0.0:
		return
	if on:
		var hp: Vector3 = a.head.global_position
		var d: Vector3 = (_blick_ziel as Vector3) - hp
		var yaw := wrapf(atan2(-d.x, -d.z) - float(a.heading), -PI, PI)
		var flat := Vector2(d.x, d.z).length()
		var pit := atan2(d.y, maxf(flat, 0.1))
		_blick = Vector2(clampf(yaw, -BLICK_YAW, BLICK_YAW), clampf(pit, -BLICK_PITCH, BLICK_PITCH))
		if absf(yaw) > BLICK_YAW + 0.8:                       # far behind: do not twist the neck
			_blick_bis = now
	_blick_s = _blick_s.lerp(_blick, clampf(dt * 4.0, 0.0, 1.0))
	var kk := smoothstep(0.0, 1.0, _blick_w)
	_put(a.head, ^"rotation:y", lerpf(a.head.rotation.y, _blick_s.x, kk))
	_put(a.head, ^"rotation:x", lerpf(a.head.rotation.x, _blick_s.y, kk))


func _blick_suchen():
	"""what catches the eye now: a sound, an animal, a player, the MoveEye camera (or nothing)"""
	var p: Vector3 = a.global_position
	var best = null
	var bw := 0.0
	var t: float = main.now()
	for s in main.sounds:                                     # [dB at 1 m, position, until, kind]
		if s.size() < 3 or float(s[2]) < t:
			continue
		var sp: Vector3 = s[1]
		var dd := sp.distance_to(p)
		var w := (float(s[0]) + 60.0) / 60.0 * 30.0 / maxf(dd, 1.0)
		if dd < 30.0 and dd > 0.5 and w > bw:
			bw = w
			best = sp + Vector3(0, 0.3, 0)
	if main.visitors != null:
		var n := 0
		for v in main.visitors.get_children():
			n += 1
			if n > 40:
				break
			if v == a or not v.has_method("is_animal") or v.done:
				continue
			var dv: float = (v as Node3D).global_position.distance_to(p)
			var w2 := 0.0
			if v.is_animal() and dv < 12.0:
				w2 = 2.0 / maxf(dv, 1.0)
			elif v.controlled and dv < 9.0:
				w2 = 1.6 / maxf(dv, 1.0)
			if w2 > bw:
				bw = w2
				best = (v as Node3D).global_position + Vector3(0, float(v.body_h) * 0.9, 0)
	for f in a.get_tree().get_nodes_in_group("anim_figur"):
		if f == a or not f is Node3D:
			continue
		var df: float = (f as Node3D).global_position.distance_to(p)
		if df < 9.0 and 1.5 / maxf(df, 1.0) > bw:
			bw = 1.5 / maxf(df, 1.0)
			best = (f as Node3D).global_position + Vector3(0, 1.0, 0)
	if main.head != null:
		var dc: float = main.head.global_position.distance_to(p)
		var wc := (0.9 if a.variant != "burglar" else 2.5) / maxf(dc, 1.0) if dc < 14.0 else 0.0
		if wc > bw and randf() < 0.6:
			best = main.head.global_position
	return best


# ---- 5 Handlungen ------------------------------------------------------------------------------------------------------
func _handlung(dt: float, now: float, k: float) -> void:
	var aktiv: bool = now < _akt_bis
	_w_akt = move_toward(_w_akt, 1.0 if aktiv else 0.0, dt * 4.0)
	if _w_akt <= 0.0:
		if not aktiv:
			akt = ""
		return
	a.anim_voll = true
	var w := smoothstep(0.0, 1.0, _w_akt)
	var dur := maxf(0.1, _akt_bis - _akt_t0)
	var f := clampf((now - _akt_t0) / dur, 0.0, 1.0)
	var e := now - _akt_t0
	var sc: float = a.body_root.scale.y
	if _akt_ziel is Vector3 and akt in ["highfive", "winken", "hebel", "kurbeln"]:
		var d: Vector3 = (_akt_ziel as Vector3) - a.global_position
		if Vector2(d.x, d.z).length() > 0.2:
			a.heading = lerp_angle(a.heading, atan2(-d.x, -d.z), clampf(dt * 6.0, 0.0, 1.0))
			a.rotation.y = a.heading
	match akt:
		"aufheben":                                          # bend down (knees and back), the right hand to the ground, up
			var b := sin(f * PI)
			_lean(-1.0 * b, w)
			for i in range(2):
				_leg(i, 0.65 * b, -1.1 * b, w)
			_arm(1, 1.0 * b, 0.08, 0.15, w)
			_arm(0, 0.45 * b, -0.05, 0.4, w)
			_add(a.body_root, ^"position:y", -(0.22 * b * sc * w))
			_put(a.head, ^"rotation:x", lerpf(a.head.rotation.x, -0.4 * b, w))
		"klettern":                                          # hand over hand, knee up in turn (ladder / rock)
			var c := e * TAU * 0.9
			for i in range(2):
				var s := 0.0 if i == 0 else PI
				var up := 0.5 + 0.5 * sin(c + s)
				_arm(i, lerpf(1.9, 2.9, up), 0.12 * a.arms[i][1], lerpf(0.9, 0.2, up), w)
				_leg(i, lerpf(0.15, 1.15, 1.0 - up), lerpf(-0.25, -1.5, 1.0 - up), w)
			_lean(-0.18, w)
			_put(a.head, ^"rotation:x", lerpf(a.head.rotation.x, 0.45, w))
		"kurbeln":                                           # the right hand goes round, the left holds
			var c2 := e * TAU * 1.1
			_arm(1, 0.95 + 0.38 * sin(c2), 0.1, 0.95 + 0.45 * cos(c2), w)
			_arm(0, 0.8, -0.08, 0.7, w)
			_lean(-0.22 + 0.06 * sin(c2), w)
			_add(a.torso, ^"rotation:y", 0.08 * sin(c2) * w)
		"hebel":                                             # reach up, pull down with the weight of the body
			var reach := 1.0 - smoothstep(0.2, 0.7, f)
			for i in range(2):
				_arm(i, lerpf(0.35, 1.75, reach), 0.1 * a.arms[i][1], lerpf(1.25, 0.2, reach), w)
				_leg(i, 0.25 * (1.0 - reach), -0.45 * (1.0 - reach), w)
			_lean(lerpf(0.14, -0.05, reach), w)
			_add(a.body_root, ^"position:y", -(0.08 * (1.0 - reach) * sc * w))
		"highfive":                                          # the right hand up and against the partner's, then cheering
			var up2 := smoothstep(0.0, 0.35, f) * (1.0 - smoothstep(0.75, 1.0, f))
			_arm(1, lerpf(0.2, 2.65, up2), 0.18, lerpf(0.6, 0.15, up2), w)
			if f > 0.45 and f < 0.55:
				_add(a.body_root, ^"position:y", 0.05 * sc * w)
		"winken":
			_arm(1, 2.55, 0.3 + 0.22 * sin(e * 8.0), 0.55 + 0.35 * sin(e * 8.0), w)
		"freude":                                            # a little jump, both arms up
			_add(a.body_root, ^"position:y", absf(sin(e * 7.0)) * 0.14 * sc * w)
			for i in range(2):
				_arm(i, 2.85 + 0.2 * sin(e * 10.0 + i), 0.32 * a.arms[i][1], 0.2, w)
		"schreck":                                           # back a step, hands up in front, the head away
			var b2 := sin(minf(1.0, f * 2.5) * PI * 0.5) * (1.0 - smoothstep(0.7, 1.0, f))
			for i in range(2):
				_arm(i, 1.5 * b2, -0.1 * a.arms[i][1], 1.6 * b2, w)
			_lean(0.18 * b2, w)
			_put(a.head, ^"rotation:x", lerpf(a.head.rotation.x, 0.2 * b2, w))
			_add(a.body_root, ^"position:z", 0.12 * b2 * w)


# ---- 6 Wetter ----------------------------------------------------------------------------------------------------------
func _wetter(dt: float, now: float, steht: bool, k: float, idle: String) -> void:
	var cold: bool = float(main.ambient) < 4.0
	if cold and now >= _zitter_next:
		_zitter_next = now + randf_range(5.0, 12.0)
		_zitter_bis = now + randf_range(0.8, 1.8)
	if cold and now < _zitter_bis:
		var z := sin(_t * 41.0 + _seed) * 0.018
		_add(a.torso, ^"rotation:z", z)
		_put(a.head, ^"rotation:z", z * 0.8)
		for i in range(2):
			_add(a.arms[i][0], ^"rotation:z", -(0.04 * a.arms[i][1]))   # arms close to the body
	if cold and steht and leer in ["", "gewicht"] and idle == "" and _steh > 3.0 and fmod(_t + _seed, 14.0) < 3.0:
		a.anim_arme = true                                    # rubbing the hands
		for i in range(2):
			_arm(i, 0.6, -0.12 * a.arms[i][1], 1.55 + 0.13 * sin(_t * 15.0 + i * PI), 0.9, 0.8 * a.arms[i][1])
	if _schirm < 0:
		_schirm = 0
		for c in a.torso.get_children():
			if c is MeshInstance3D and (c as MeshInstance3D).mesh is CylinderMesh and ((c as MeshInstance3D).mesh as CylinderMesh).bottom_radius > 0.5:
				_schirm = 1
				break
	var umbrella := _schirm == 1
	if str(main.weather) == "rain" and not umbrella and a.prone < 0.1:
		_add(a.head, ^"rotation:x", -0.22)                    # the head drawn in, shoulders up
		_add(a.torso, ^"rotation:x", -(0.05))
		for i in range(2):
			_add(a.arms[i][0], ^"rotation:z", -(0.05 * a.arms[i][1]))
	var wind: float = float(main.wind)
	if wind > 14.0:
		if not _flat_scan:
			_flat_scan = true
			_flatter_suchen()
		var st := clampf((wind - 14.0) / 30.0, 0.0, 1.0)
		for f in _flatter:
			var n: Node3D = f[0]
			if is_instance_valid(n):
				var r0: Vector3 = f[1]
				n.rotation = r0 + Vector3(0.12 * st * sin(_t * 7.0 + float(f[2])), 0, 0.08 * st * sin(_t * 9.3 + float(f[2])))
		_add(a.torso, ^"rotation:z", 0.012 * st * sin(_t * 1.3 + _seed))


func _flatter_suchen() -> void:
	"""coat (hips), long hair / ponytail (head), umbrella (torso): they move in the wind (figure from rings / shapes)"""
	for par in [a.hips, a.head, a.torso]:
		if par == null:
			continue
		for c in (par as Node3D).get_children():
			if not c is MeshInstance3D:
				continue
			var mi := c as MeshInstance3D
			var ok := false
			if par == a.hips and mi.mesh is CylinderMesh and (mi.mesh as CylinderMesh).height > 0.5:
				ok = true
			elif par == a.head and mi.mesh is CapsuleMesh and mi.position.z > 0.06:
				ok = true
			elif par == a.torso and mi.mesh is CylinderMesh and (mi.mesh as CylinderMesh).bottom_radius > 0.5:
				ok = true
			if ok:
				_flatter.append([mi, mi.rotation, randf() * TAU])


# ---- 7 Gesicht ---------------------------------------------------------------------------------------------------------
func _gesicht_suchen() -> void:
	_gesicht_scan = true
	for c in a.head.get_children():
		if not c is MeshInstance3D or (c as MeshInstance3D).layers != 1:
			continue
		var mi := c as MeshInstance3D
		if mi.mesh is SphereMesh and mi.position.z < -0.07 and mi.position.y > 0.15 and mi.position.y < 0.2 and absf(mi.position.x) > 0.02:
			_augen.append(mi)                                   # eye white and pupil (figur.gd / old shapes)
		elif mi.mesh is BoxMesh and mi.position.y > 0.2 and mi.position.z < -0.07 and absf(mi.position.x) > 0.03:
			_brauen.append([mi, mi.position.y])
		elif mi.mesh is BoxMesh and mi.position.y < 0.13 and mi.position.z < -0.1 and absf(mi.position.x) < 0.01:
			_mund = mi                                          # the mouth of the old shapes
	if _mund == null and a.fig != null and not a.fig.has_method("_choose") and not _augen.is_empty():
		var bm := BoxMesh.new()                               # figur.gd: the lips are in the skin - a dark mouth opening on top
		bm.size = Vector3(0.03, 0.012, 0.008)
		_mund = MeshInstance3D.new()
		_mund.mesh = bm
		_mund.position = Vector3(0, 0.092, -0.093)
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.22, 0.07, 0.07)
		_mund.material_override = m
		_mund.layers = 1
		_mund.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_mund.visible = false
		a.head.add_child(_mund)
		_mund_eigen = true


func _gesicht(dt: float, now: float, idle: String) -> void:
	if not _gesicht_scan:
		_gesicht_suchen()
	if _augen.is_empty() and _mund == null:
		return
	var gf: String = gefuehl if now < _gefuehl_bis else ""
	if gf == "" and now < a.startle_until:
		gf = "schreck"
	if now >= _blinz_next:
		_blinz_next = now + randf_range(2.0, 6.0) * (0.6 if gf == "schreck" else 1.0)
		_blinz_bis = now + 0.13
	var zu: bool = now < _blinz_bis
	var ey := 0.12 if zu else (1.3 if gf == "schreck" else (0.75 if gf == "freude" else 1.0))
	for e in _augen:
		if is_instance_valid(e):
			(e as Node3D).scale = Vector3(1.0, ey, 1.0)
	for b in _brauen:
		if is_instance_valid(b[0]):
			(b[0] as Node3D).position.y = float(b[1]) + (0.012 if gf != "" else 0.0)
	if _mund == null:
		return
	var talk: bool = now < sprech_bis or (idle == "talk" and fmod(_t * 0.4 + _seed, 2.0) < 1.0)
	var open := 0.0
	if talk:
		open = clampf(0.5 + 0.5 * sin(_t * 15.0 + 3.0 * sin(_t * 4.1)), 0.0, 1.0)
	if gf == "schreck":
		open = 1.0
	elif gf == "freude":
		open = maxf(open, 0.55)
	var wx := 1.35 if gf == "freude" else 1.0
	if _mund_eigen:
		_mund.visible = open > 0.08
		_mund.scale = Vector3(wx, 0.4 + 1.6 * open, 1.0)
	else:
		_mund.scale = Vector3(wx, 1.0 + 3.0 * open, 1.0)


# ---- 8 Statisten -------------------------------------------------------------------------------------------------------
func _statist(dt: float, now: float, idle: String, spd: float, k: float) -> void:
	match idle:
		"talk":                                              # both hands, a nod now and then
			a.anim_arme = true
			var g := sin(_t * 1.7 + _seed)
			if g > 0.2:
				_arm(0, 0.4 + 0.2 * sin(_t * 2.6), -0.05, 1.25 + 0.3 * sin(_t * 3.3 + 1.0), 0.6)
			_add(a.head, ^"rotation:x", 0.07 * maxf(0.0, sin(_t * 3.0 + _seed * 2.0)) * (1.0 if fmod(_t + _seed, 5.0) < 1.2 else 0.0))
		"grillen":                                           # at the grill: the tongs in the right hand, turning now and then
			a.anim_voll = true
			var flip := maxf(0.0, sin(_t * 1.4 + _seed))
			_arm(1, 0.85 + 0.25 * flip, 0.1, 0.9 + 0.5 * flip, 1.0)
			_arm(0, 0.35, -0.05, 1.3, 1.0)
			_lean(-0.18, 1.0)
			_put(a.head, ^"rotation:x", lerpf(a.head.rotation.x, -0.4, 1.0))
		"zelt":                                              # pitching a tent: crouched, hammering in a peg
			a.anim_voll = true
			var hit := absf(sin(_t * 4.2 + _seed))
			for i in range(2):
				_leg(i, 1.0, -1.75, 1.0)
			_add(a.body_root, ^"position:y", -(0.38 * a.body_root.scale.y))
			_lean(-0.55, 1.0)
			_arm(1, 0.6 + 1.2 * hit, 0.1, 0.6 + 0.6 * (1.0 - hit), 1.0)
			_arm(0, 1.0, -0.1, 0.3, 1.0)
			_put(a.head, ^"rotation:x", lerpf(a.head.rotation.x, -0.2, 1.0))
	if a.variant != "child" or not a.has_meta("st_statist") or lod >= 2:
		return
	if now >= _kind_next and now >= _kind_bis:                # children: hop, run a bit, play
		_kind_next = now + randf_range(6.0, 16.0)
		if spd < 0.05 and idle in ["", "look"]:
			_kind_art = "huepfen"
			_kind_bis = now + randf_range(2.0, 4.0)
		elif spd > 0.3 and randf() < 0.5:
			_kind_art = "rennen"
			_kind_bis = now + randf_range(2.0, 3.5)
			_kind_v0 = a.speed
			a.speed = minf(a.speed * 2.2, 3.2)
	if now >= _kind_bis:
		if _kind_art == "rennen" and _kind_v0 > 0.0:
			a.speed = _kind_v0
			_kind_v0 = 0.0
		_kind_art = ""
		return
	if _kind_art == "huepfen":
		a.anim_voll = true
		var j := absf(sin(_t * 6.5))
		_add(a.body_root, ^"position:y", j * 0.16 * a.body_root.scale.y)
		for i in range(2):
			_arm(i, 0.4 + 1.6 * j, 0.35 * a.arms[i][1], 0.3, 1.0)
			_leg(i, 0.25 * (1.0 - j), -0.5 * (1.0 - j), 1.0)


# ---- Spuren ------------------------------------------------------------------------------------------------------------
func _spuren(dt: float, spd: float) -> void:
	if spd < 0.25 or a.prone > 0.3 or a.legs.size() < 2:
		return
	var n := int(floor(float(a.phase) / PI))                  # every half step cycle one foot is down (also at low fps)
	if n != _tritt_n:
		_tritt_n = n
		var kn: Node3D = a.legs[posmod(n, 2)][2]
		var fp := kn.global_transform * Vector3(0, -0.44, -0.04)
		fp.y = a.global_position.y
		Spuren.tritt(main, fp, float(a.heading), false, spd)


# ---- helpers: every change is remembered and taken back before the next frame of actor._animate (vorher), so the
# ---- base animation always works on its own pose and this layer never piles up (independent of the frame rate) -------
var _frame := false                # post ran in this frame (vor_sync / nach_sync only then)
const PIDX := {^"rotation:x": 0, ^"rotation:y": 1, ^"rotation:z": 2, ^"position:x": 3, ^"position:y": 4, ^"position:z": 5}
var _off := {}                     # "id|path" -> [node, path, delta]


func vorher() -> void:
	"""start of actor._animate: undo the changes of the last frame"""
	if _off.is_empty():
		return
	for k in _off:
		var e: Array = _off[k]
		var n = e[0]
		if is_instance_valid(n):
			(n as Node3D).set_indexed(e[1], float((n as Node3D).get_indexed(e[1])) - float(e[2]))
	_off.clear()


func _add(n, path: NodePath, dv: float) -> void:
	if n == null or dv == 0.0:
		return
	var nd := n as Node3D
	var key: int = nd.get_instance_id() * 8 + int(PIDX[path])
	nd.set_indexed(path, float(nd.get_indexed(path)) + dv)
	if _off.has(key):
		_off[key][2] = float(_off[key][2]) + dv
	else:
		_off[key] = [nd, path, dv]


func _put(n, path: NodePath, v: float) -> void:
	if n == null:
		return
	_add(n, path, v - float((n as Node3D).get_indexed(path)))


func _arm(i: int, sx: float, sz: float, ex: float, w: float, sy := 0.0) -> void:
	var A: Array = a.arms[i]
	var sh: Node3D = A[0]
	_put(sh, ^"rotation:x", lerpf(sh.rotation.x, sx, w))
	_put(sh, ^"rotation:z", lerpf(sh.rotation.z, sz, w))
	if sy != 0.0 or sh.rotation.y != 0.0:
		_put(sh, ^"rotation:y", lerpf(sh.rotation.y, sy, w))
	if A.size() > 2 and A[2] != null:
		_put(A[2], ^"rotation:x", lerpf((A[2] as Node3D).rotation.x, ex, w))


func _leg(i: int, hx: float, kx: float, w: float) -> void:
	var L: Array = a.legs[i]
	_put(L[0], ^"rotation:x", lerpf((L[0] as Node3D).rotation.x, hx, w))
	if L.size() > 2 and L[2] != null:
		_put(L[2], ^"rotation:x", lerpf((L[2] as Node3D).rotation.x, kx, w))


func _lean(x: float, w: float) -> void:
	_put(a.torso, ^"rotation:x", lerpf(a.torso.rotation.x, x, w))


static func _wahl(w: Dictionary) -> String:
	var tot := 0.0
	for k in w:
		tot += float(w[k])
	var r := randf() * tot
	for k in w:
		r -= float(w[k])
		if r <= 0.0:
			return str(k)
	return ""


# ---- /control {"action": "anim"} (tests) -----------------------------------------------------------------------------
static func op(m, d: Dictionary) -> Dictionary:
	var what := str(d.get("do", "info"))
	var list := []
	for v in m.visitors.get_children():
		if v.get("anim") != null:
			list.append(v)
	if m.is_inside_tree():
		for v2 in m.get_tree().get_nodes_in_group("anim_figur"):
			if not v2 in list and v2.get("anim") != null:
				list.append(v2)
	var who = null
	var best := 1.0e9
	var at: Vector3 = m.head.global_position if m.head != null else Vector3.ZERO
	for v3 in list:
		if v3.kind != "person" and what in ["aktion", "sprechen"]:
			continue
		var dd: float = (v3 as Node3D).global_position.distance_to(at)
		if dd < best:
			best = dd
			who = v3
	match what:
		"info":
			var out := []
			for v4 in list:
				out.append({"kind": v4.kind, "variant": v4.variant, "anim": v4.anim.info()})
			return {"ok": true, "n": list.size(), "hoch": hoch(m), "figuren": out, "spuren": Spuren.anzahl(m)}
		"aktion":
			if who == null:
				return {"ok": false, "error": "keine Figur"}
			return {"ok": who.anim.aktion(str(d.get("art", "winken")), float(d.get("s", -1.0))), "arten": ARTEN}
		"sprechen":
			if who == null:
				return {"ok": false, "error": "keine Figur"}
			who.anim.sprechen(float(d.get("s", 3.0)))
			return {"ok": true}
		"stufe":
			var n := Node3D.new()
			n.set_meta("stufe", Vector3(float(d.get("sx", 0.6)), float(d.get("h", 0.2)), float(d.get("sz", 0.6))))
			n.add_to_group("anim_stufe")
			m.add_child(n)
			n.global_position = Vector3(float(d.get("x", 0.0)), m.ground_y(float(d.get("x", 0.0)), float(d.get("z", 0.0))), float(d.get("z", 0.0)))
			return {"ok": true}
	return {"ok": false, "error": "do: info | aktion (art, s) | sprechen (s) | stufe (x, z, h)"}
