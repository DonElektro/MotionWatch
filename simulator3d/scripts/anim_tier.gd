extends RefCounted
## «Animationen verbessern» (Daniel 31.10.2026): Tiere von actor.gd - eine Ergänzung NACH der Grund-Animation (wie
## anim_mensch.gd, actor.anim). Die Aussehen bleiben (auch Maggie aus 3.15.0), nur Gelenke und kurze Zustände.
##   9  Reh        äsen mit kurzem Kopfheben und Kauen, Ohren drehen (zucken, beim Sichern zum Geräusch), Flucht: Sprünge
##                 (actor.gd «leap») mit hochgehaltenem Kopf
##   10 Fuchs/Dachs schnüffeln (actor.gd), schleichen (tief, Kopf vor, langsam), innehalten («halt»: Vorderpfote hoch)
##   11 Kuh        kauen, Schwanz schlagen, liegen und wiederkäuen (idle «lie» lang; nicht in der Herde des Abenteuers)
##   13-15 Hund / Maggie: Nase am Boden auf der Spur (Meta «anim_spur_bis»), graben mit den Vorderpfoten (Erde fliegt),
##                 sitzen (Hinterbeine gefaltet), liegen, Kopf schief («schief»), schütteln («schuetteln», Tropfen),
##                 ducken beim Knurren («knurren»)
## 12 (Vögel fliegen auf): fauna.gd, auch vor Spielern / Figuren der Gruppe «anim_figur».
## Leistung: weit weg nichts (LOD wie anim_mensch.gd), Teilchen nicht in Lite.

const Quality = preload("res://scripts/quality.gd")
const Spuren = preload("res://scripts/anim_spuren.gd")
const NAH := 30.0
const WEIT := 70.0

var a
var main
var lod := 0
var _lod_t := 0.0
var _t := 0.0
var _seed := randf() * 100.0
var _idle_alt := ""
var _until_alt := 0.0
var _ohren: Array = []            # [mesh, rest rotation]
var _ohr_scan := false
var _ohr_next := 0.0
var _ohr_bis := 0.0
var _ohr_s := 1.0
var _hebe_next := 0.0
var _hebe_bis := 0.0
var _schw_next := 0.0
var _schw_bis := 0.0
var _erde: CPUParticles3D = null
var _tropfen: CPUParticles3D = null
var _tritt_s := 0.0
var _off := {}


func _init(actor) -> void:
	a = actor
	main = actor.main
	_ohr_next = randf_range(0.5, 3.0)
	_schw_next = randf_range(1.0, 5.0)
	_hebe_next = randf_range(2.0, 5.0)


static func neu(actor):
	if not actor.is_animal() or actor.preview:
		return null
	return load("res://scripts/anim_tier.gd").new(actor)


func info() -> Dictionary:
	var now: float = a.now_s()
	return {"lod": lod, "idle": a.idle_kind if now < a.idle_until else "", "ohren": _ohren.size(),
			"spur": float(a.get_meta("anim_spur_bis", 0.0)) > now, "erde": _erde != null and _erde.emitting,
			"tropfen": _tropfen != null and _tropfen.emitting, "schwanz": now < _schw_bis}


func _lod_tick(dt: float) -> void:
	_lod_t -= dt
	if _lod_t > 0.0:
		return
	_lod_t = 0.5 + randf() * 0.2
	var p: Vector3 = a.global_position
	var d := 1.0e9
	if main.head != null:
		d = p.distance_to(main.head.global_position)
	if main.view_cam != null and main.view_cam.is_inside_tree():
		d = minf(d, p.distance_to(main.view_cam.global_position))
	lod = 0 if d < (NAH * 0.6 if Quality.lite() else NAH) else (1 if d < WEIT else 2)
	if main.has_method("measuring") and main.measuring():
		lod = 2


func vorher() -> void:
	for k in _off:
		var e: Array = _off[k]
		if is_instance_valid(e[0]):
			(e[0] as Node3D).set_indexed(e[1], float((e[0] as Node3D).get_indexed(e[1])) - float(e[2]))
	_off.clear()


func _add(n, path: String, dv: float) -> void:
	if n == null or dv == 0.0:
		return
	var nd := n as Node3D
	var key := "%d|%s" % [nd.get_instance_id(), path]
	nd.set_indexed(path, float(nd.get_indexed(path)) + dv)
	if _off.has(key):
		_off[key][2] = float(_off[key][2]) + dv
	else:
		_off[key] = [nd, path, dv]


func _put(n, path: String, v: float) -> void:
	if n != null:
		_add(n, path, v - float((n as Node3D).get_indexed(path)))


func vor_sync(_dt: float) -> void:
	pass


func nach_sync(_dt: float) -> void:
	pass


# ---- every frame (end of actor._animate) -----------------------------------------------------------------------------
func post(dt: float, spd: float, now: float, idle: String) -> void:
	_t += dt
	_lod_tick(dt)
	if (a.controlled or a.puppet) and not a.is_in_group("anim_figur"):
		a.add_to_group("anim_figur")
	_wahl(now, idle)
	idle = a.idle_kind if now < a.idle_until else ""
	if lod >= 2 or a.stars != null:
		_teilchen(false, false)
		return
	match a.kind:
		"deer", "chamois", "ibex":
			_reh(dt, spd, now, idle)
		"fox", "badger":
			_fuchs(dt, spd, now, idle)
		"cow":
			_kuh(dt, spd, now, idle)
		"dog":
			_hund(dt, spd, now, idle)
	if a.kind != "dog":
		_teilchen(false, false)
	if lod == 0 and spd > 0.3 and a.legs.size() >= 4 and not Quality.lite():
		var s := sin(float(a.phase))
		if (s >= 0.0) != (_tritt_s >= 0.0):
			var lg: Node3D = a.legs[0 if s >= 0.0 else 3][0]
			Spuren.tritt(main, lg.global_transform * Vector3(0, -lg.position.y, 0), float(a.heading), true, spd)
		_tritt_s = s


func _wahl(now: float, idle: String) -> void:
	"""a new idle was picked by actor.gd: now and then make it one of the new ones"""
	if idle == _idle_alt and is_equal_approx(float(a.idle_until), _until_alt):
		return
	_idle_alt = idle
	_until_alt = a.idle_until
	if idle == "" or a.fled or a.puppet or a.leader != null or (main.has_method("measuring") and main.measuring()):
		return
	match a.kind:
		"fox", "badger":
			if idle == "look" or (idle == "sniff" and randf() < 0.3):
				_neu("halt", randf_range(1.5, 3.5))
		"cow":
			if a.has_meta("gh_kuh"):
				return
			if idle == "look" and randf() < 0.45:
				_neu("lie", randf_range(25.0, 60.0))         # lies down and chews the cud
			elif idle == "look":
				_neu("kauen", randf_range(4.0, 9.0))
		"dog":
			if idle == "sit" and randf() < 0.25:
				_neu("schief", randf_range(1.5, 3.0))


func _neu(k: String, s: float) -> void:
	a.idle_kind = k
	a.idle_until = a.now_s() + s
	_idle_alt = k
	_until_alt = a.idle_until


# ---- 9 Reh -------------------------------------------------------------------------------------------------------------
func _reh(dt: float, spd: float, now: float, idle: String) -> void:
	if not _ohr_scan:
		_ohr_scan = true
		for c in a.head.get_children():
			if c is MeshInstance3D and (c as MeshInstance3D).mesh is PrismMesh:
				var pm := (c as MeshInstance3D).mesh as PrismMesh
				if pm.size.y > pm.size.x and pm.size.z < 0.05:
					_ohren.append([c, (c as Node3D).rotation])
	if now >= _ohr_next:
		_ohr_next = now + randf_range(0.8, 3.5)
		_ohr_bis = now + 0.35
		_ohr_s = 1.0 if randf() < 0.5 else -1.0
	var alert: bool = idle in ["alert", "stare"]
	for e in _ohren:
		var mi: Node3D = e[0]
		if not is_instance_valid(mi):
			continue
		var r0: Vector3 = e[1]
		var side := 1.0 if mi.position.x > 0.0 else -1.0
		var tw := 0.0
		if now < _ohr_bis and (side == _ohr_s or randf() < 0.02):
			tw = 0.45 * sin((_ohr_bis - now) / 0.35 * PI)
		var yaw := (0.5 * side if alert else 0.0)            # alert: the ears forward (to the noise)
		mi.rotation = r0 + Vector3(-0.25 if alert else 0.0, yaw, tw * side)
	if idle == "graze":                                        # grazing: the head comes up now and then, chewing, looking
		if now >= _hebe_next:
			_hebe_next = now + randf_range(3.0, 7.0)
			_hebe_bis = now + randf_range(1.2, 2.2)
		if now < _hebe_bis:
			var u := sin(clampf((_hebe_bis - now) / 1.6, 0.0, 1.0) * PI)
			_put(a.head, "rotation:x", lerpf(a.head.rotation.x, 0.35, u))
			_add(a.head, "rotation:z", 0.04 * sin(_t * 8.0) * u)
			_ohr_bis = maxf(_ohr_bis, now + 0.1)
	if a.fled and spd > 2.0:                                   # flight: the head up high, the ears back
		_put(a.head, "rotation:x", lerpf(a.head.rotation.x, 0.3, 0.7))


# ---- 10 Fuchs und Dachs ------------------------------------------------------------------------------------------------
func _fuchs(dt: float, spd: float, now: float, idle: String) -> void:
	var hb: float = (a.legs[0][0] as Node3D).position.y * a.body_root.scale.y
	if spd > 0.05 and spd < 1.1 and not a.fled:              # sneaking: low, the head forward, the tail low
		var low := clampf(1.0 - spd / 1.1, 0.3, 1.0)
		_add(a.body_root, "position:y", -0.12 * hb * low)
		_put(a.head, "rotation:x", lerpf(a.head.rotation.x, -0.3, low))
		if a.tail != null:
			_add(a.tail, "rotation:x", -0.25 * low)
	if idle == "halt":                                        # freezing: one front paw up, the head high, quite still
		var w := clampf((a.idle_until - now) * 3.0, 0.0, 1.0) * clampf((now - (a.idle_until - 3.5)) * 3.0, 0.0, 1.0)
		w = maxf(w, 0.6)
		_put(a.legs[0][0], "rotation:x", lerpf((a.legs[0][0] as Node3D).rotation.x, 0.75, w))
		_put(a.head, "rotation:x", lerpf(a.head.rotation.x, 0.3, w))
		if main.head != null:
			var to_c: Vector3 = main.head.global_position - a.global_position
			_put(a.head, "rotation:y", lerpf(a.head.rotation.y, clampf(wrapf(atan2(-to_c.x, -to_c.z) - float(a.heading), -PI, PI), -1.0, 1.0), w))
		if a.tail != null:
			_put(a.tail, "rotation:y", 0.0)


# ---- 11 Kuh ------------------------------------------------------------------------------------------------------------
func _kuh(dt: float, spd: float, now: float, idle: String) -> void:
	if idle in ["", "kauen", "lie", "look"] and spd < 0.2:     # chewing (the jaw goes round): a small turn of the head
		_add(a.head, "rotation:z", 0.05 * sin(_t * 6.5 + _seed))
		_add(a.head, "rotation:x", 0.02 * sin(_t * 13.0 + _seed))
	if idle == "kauen":
		_put(a.head, "rotation:x", lerpf(a.head.rotation.x, -0.15, 0.8))
	if now >= _schw_next:
		_schw_next = now + randf_range(2.5, 8.0)
		_schw_bis = now + randf_range(0.6, 1.2)
	if a.tail != null and now < _schw_bis:                    # the tail swishes at the flies
		_add(a.tail, "rotation:z", 0.75 * sin(_t * 10.0))
		_add(a.tail, "rotation:x", 0.25 * absf(sin(_t * 10.0)))


# ---- 13-15 Hund / Maggie -----------------------------------------------------------------------------------------------
func _hund(dt: float, spd: float, now: float, idle: String) -> void:
	var hb: float = (a.legs[0][0] as Node3D).position.y * a.body_root.scale.y if a.legs.size() >= 4 else 0.3
	if a.legs.size() < 4:
		return
	var spur: bool = float(a.get_meta("anim_spur_bis", 0.0)) > now
	var grab := idle == "root"
	var nass := idle == "schuetteln"
	if spur and spd > 0.15 and idle == "":                     # 13: the nose on the ground, on the track
		_put(a.head, "rotation:x", -0.8 + 0.06 * sin(_t * 15.0))
		_put(a.head, "rotation:y", 0.28 * sin(_t * 2.3 + _seed))
		if a.tail != null:
			_add(a.tail, "rotation:x", -0.35)
	match idle:
		"root":                                               # 14: digging with the front paws, the earth flies back
			_put(a.body_root, "rotation:x", -0.2)
			_add(a.body_root, "position:y", -0.05 * hb)
			for i in range(2):
				_put(a.legs[i][0], "rotation:x", 0.55 + 0.75 * sin(_t * 15.0 + PI * i))
			_put(a.legs[2][0], "rotation:x", -0.25)
			_put(a.legs[3][0], "rotation:x", -0.25)
			_put(a.head, "rotation:x", -0.75)
			if a.tail != null:
				_add(a.tail, "rotation:x", -0.4)
		"sit":                                                # 15: sitting - the hind legs folded, the front legs straight
			_add(a.body_root, "position:y", -0.1 * hb)
			_put(a.legs[0][0], "rotation:x", -0.4)
			_put(a.legs[1][0], "rotation:x", -0.4)
			_put(a.legs[2][0], "rotation:x", 1.25)
			_put(a.legs[3][0], "rotation:x", 1.25)
		"schief":                                             # the head tilted, listening
			_add(a.body_root, "position:y", -0.1 * hb)
			_put(a.body_root, "rotation:x", 0.4)
			for i in range(4):
				_put(a.legs[i][0], "rotation:x", -0.4 if i < 2 else 1.25)
			_put(a.head, "rotation:z", 0.42 * (1.0 if fmod(_seed, 2.0) < 1.0 else -1.0))
			_put(a.head, "rotation:x", 0.15)
		"schuetteln":                                         # shaking off the water: from the head to the tail
			var env := clampf((a.idle_until - now) / 1.2, 0.0, 1.0)
			_put(a.body_root, "rotation:z", 0.38 * sin(_t * 30.0) * env)
			_put(a.head, "rotation:z", 0.5 * sin(_t * 30.0 - 0.6) * env)
			if a.tail != null:
				_add(a.tail, "rotation:y", 0.6 * sin(_t * 30.0 - 1.2) * env)
		"knurren":                                            # ducking when growling: low, the head forward, the tail down
			_add(a.body_root, "position:y", -0.12 * hb)
			_put(a.body_root, "rotation:x", -0.12)
			_put(a.head, "rotation:x", -0.28)
			for i in range(4):
				_put(a.legs[i][0], "rotation:x", 0.25 if i < 2 else -0.3)
			if a.tail != null:
				_put(a.tail, "rotation:y", 0.0)
				_add(a.tail, "rotation:x", -0.6)
	_teilchen(grab and lod == 0, nass and lod == 0)


func _teilchen(erde: bool, tropfen: bool) -> void:
	if Quality.lite() and not erde:
		tropfen = false
	if erde and _erde == null:
		_erde = _wolke(Color(0.36, 0.27, 0.18) if not _winter() else Color(0.93, 0.95, 0.98), Vector3(0, 0.9, 1.0), 0.03, 14 if not Quality.lite() else 5)
		_erde.position = Vector3(0, (a.legs[0][0] as Node3D).position.y * 0.3, -0.25)
	if tropfen and _tropfen == null:
		_tropfen = _wolke(Color(0.75, 0.85, 1.0, 0.7), Vector3(0, 0.4, 0), 0.012, 24)
		_tropfen.spread = 180.0
		_tropfen.position = Vector3(0, (a.legs[0][0] as Node3D).position.y, 0)
	if _erde != null:
		_erde.emitting = erde
	if _tropfen != null:
		_tropfen.emitting = tropfen


func _winter() -> bool:
	return Spuren.anzahl(main) > 0 or str(main.weather) == "snow"


func _wolke(col: Color, d: Vector3, r: float, n: int) -> CPUParticles3D:
	var c := CPUParticles3D.new()
	c.amount = n
	c.lifetime = 0.7
	c.direction = d
	c.spread = 25.0
	c.initial_velocity_min = 1.2
	c.initial_velocity_max = 2.4
	c.gravity = Vector3(0, -9.8, 0)
	c.local_coords = false
	var sm := SphereMesh.new()
	sm.radius = r
	sm.height = r * 2.0
	sm.radial_segments = 5
	sm.rings = 3
	c.mesh = sm
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	if col.a < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	c.material_override = m
	c.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	c.emitting = false
	a.body_root.add_child(c)
	return c
