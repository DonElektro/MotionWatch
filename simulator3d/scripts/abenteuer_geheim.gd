extends Node
## Paket «Die Karte des Grossvaters: Geheimnisse und Nacht» (Daniel 31.10.2026, bestätigt) - ein Kind von bergtal_abenteuer.gd
## («ab»), dort nur kleine Einhänge-Punkte (Suche nach «geheim.»). Die Action-Teile (Steg, Kuhherde, Seilbahn, Schleuse,
## Spiegel) stehen in abenteuer_action.gd und hängen hier ein (act.*).
##
## Geheim (kein Pfeil, kein Tipp, auch nicht auf «Leicht»; Blinki und das Entdeckungsbuch sagen vorher nichts):
##   4 Steinmännchen: in jedem Kapitel steht abseits des Weges (18–40 m neben einem Wegstück, vom Weg aus sichtbar) ein
##     kleines Steinmännchen mit einem eingeritzten Zeichen. Gefunden: in der Fensteransicht anklicken (bis 90 m, mit dem
##     Feldstecher weiter) oder zu zweit mit der eigenen Figur hingehen (3,5 m). Alle fünf = geheimes Abzeichen
##     (main.entdecken: erst beim Verdienen angemeldet, «active» nie) und in der Überraschung eine Zeile mit dem Wort.
##   5 Doppelter Boden im Biwak: mit «Feldstecher: hier durchschauen» im Biwak ganz nah auf den Boden schauen.
##   6 Licht auf der MoveEye-Aufnahme: in einer Nacht (Kapitel 2–4) leuchtet an einem Ort, der auf keiner Karte steht, ein
##     schwaches Licht. Die Aufnahme kommt wie bei A1 über die echte Erkennung (ab.a1._mw_meldet / _mw_da / _bild / _box);
##     am Morgen steht sie ohne Erklärung da («Bewegung, kein Tier»). Wer das Licht auf dem Bild antippt, kann am nächsten Tag
##     in der Nähe einen Abstecher machen und findet ein Tagebuchblatt (der Reflektor eines alten Kästchens hat das
##     Infrarot-Licht von MoveEye zurückgeworfen).
## Nicht geheim:
##   9 Nacht mit Geräuschen: in einer Lagernacht (zuerst ab Kapitel 2, danach selten) raschelt und knackt es ringsum (erzeugte
##     Töne, Lautstärke = «Lautstärke am PC» von mikrofon.gd, aus mit main.sound_on / pc_on; das Mikrofon von MoveEye hört
##     es über main.add_sound). Ein Dachs schnüffelt am Rucksack; MoveEye nimmt ihn auf; am Morgen: wer war es?
## Keine neuen Fakten über den Grossvater: die Texte wiederholen nur, was Brief, Karte und Kapitel schon sagen.
##
## EINHÄNGE-PUNKTE für spätere Teile (Daniel: «weitere Teile folgen»): ein neues Teil ist eine Datei wie abenteuer_action.gd
## mit denselben Funktionen (alle optional) und wird in TEILE eingetragen:
##   on_start() · build(root: Node3D, ch) · leg_stop(leg, f0, f) -> bool · on_ask(pe) · choose(pe, v) -> bool · tick(dt) ·
##   plan_extra(out, sp, speed) · register_kinds(n) · morning(res) · paint_hud(body) · paint_pending(g, pe) ·
##   paint_camp(body) · paint_night(body) · paint_morning(body) · paint_finale(g) · op(d) -> Dictionary · state() · orte()
##   hub-Helfer: hold(id) / release() (Wegstück anhalten), ask(kind, title, text, opts), mesh(), snd(), shake(), wg(), S(), RR().
## Spielstand: P["gh_geheim"] (pro Spielstand-Platz, spielstand.gd), der Lauf in R["gh"].
## Steuerbefehl: {"action": "abenteuer", "do": "geheim", "was": state | stein_test (ch) | klick (x, y) | fernglas |
##   boden_test | licht_klick (rx, ry) | abstecher | dachs_rate (value) | steg / kuehe / seil / schleuse / spiegel … (act.op)}
## Lite (Quality.lite()): weniger Steine, keine Schatten, kein Licht-Schein (nur leuchtende Kugel), Töne mit halber Rate.

const T = preload("res://scripts/i18n.gd")
const Bt = preload("res://scripts/bergtal.gd")
const D = preload("res://scripts/bergtal_abenteuer_daten.gd")
const Quality = preload("res://scripts/quality.gd")

const TEILE := ["res://scripts/abenteuer_action.gd"]

# ---- die Steinmännchen: Kapitel -> [Wegstück (Stufe mit «walk»), Anteil entlang, Zeichen] ------------------------------------
const STEIN := {1: [3, 0.42, "S"], 2: [5, 0.45, "E"], 3: [5, 0.5, "E"], 4: [0, 0.55, "L"], 5: [0, 0.5, "I"]}
const WORT := "SEELI"
const STEIN_KLICK_M := 90.0             # so weit darf die Ansicht weg sein (mit dem Feldstecher 8×: weiter)
const STEIN_NAH_M := 3.5                # zu zweit: so nah muss die Figur hin
const BIWAK := Vector2(-520.0, 560.0)   # bergtal_orte.gd B_BIV
const BADGES := {"steine": ["Geheimes Abzeichen: Die fünf Zeichen", "Alle fünf versteckten Steinmännchen abseits des Weges gefunden."]}
const LICHT_KAP := [2, 3, 4]

var ab
var main
var act: Array = []                     # the parts (abenteuer_action.gd …)
var _root: Node3D = null                # our 3D things of this run
var _root_key := ""
var _stein: Node3D = null
var _refl: Node3D = null
var _press = null
var _t := 0.0
var _fz := {}                           # the binoculars «hier durchschauen»: {until, cams: [[cam, fov0]]}
var _licht: Node3D = null
var _licht_t := 0.0
var _licht_vis := 0.0
var _dachs = null
var _snd_t := 0.0
var _snd_cache := {}
var _tex := {}
var _hold_h := 0.0


func setup(a) -> void:
	ab = a
	main = a.main
	for p in TEILE:
		var sc = load(p)
		if sc != null:
			var o = sc.new()
			o.hub = self
			o.ab = ab
			o.main = main
			act.append(o)
			if o is Node:
				add_child(o)


static func _lite() -> bool:
	return Quality.lite()


# =======================================================================================================================
# saved (P) and run (R)
# =======================================================================================================================
func S() -> Dictionary:
	if not ab.P.has("gh_geheim") or not ab.P["gh_geheim"] is Dictionary:
		ab.P["gh_geheim"] = {}
	var s: Dictionary = ab.P["gh_geheim"]
	for k in [["steine", {}], ["badges", {}], ["licht", {}], ["boden", false], ["ger", 0], ["blatt", false]]:
		if not s.has(k[0]):
			s[k[0]] = k[1].duplicate() if k[1] is Dictionary else k[1]
	return s


func RR() -> Dictionary:
	if ab.R.is_empty():
		return {}
	if not ab.R.has("gh"):
		ab.R["gh"] = {"xp": 0, "hold": "", "neu": []}
	return ab.R["gh"]


func _call(fn: String, args := []) -> Variant:
	"""a hook into every part; the first true (for the bool hooks) wins"""
	var out = null
	for o in act:
		if o.has_method(fn):
			var r = o.callv(fn, args)
			if r == true:
				return true
			if r is Dictionary and out == null:
				out = r
	return out


# =======================================================================================================================
# helpers for the parts
# =======================================================================================================================
func bt():
	return ab.bt()


func ch() -> int:
	return int(ab.R.get("chapter", ab.W["chapter"]))


func wg(q: Vector2, dy := 0.0) -> Vector3:
	var b = bt()
	return b.WG(q.x, q.y, dy) if b != null else Vector3(q.x, dy, q.y)


func hilfe() -> String:
	return ab.hilfe_stufe()


func ask(kind: String, title: String, text: String, opts: Array, extra := {}) -> void:
	ab._ask(kind, title, text, opts, extra)


func tip(t: String) -> void:
	"""a tip for the not-secret parts: shown like the A3 tips (Mittel after a while / on request, Leicht at once)"""
	if ab.raetsel != null:
		var r: Dictionary = ab.raetsel.RR()
		if not r.is_empty():
			r["tip"] = t
			if hilfe() == "leicht":
				r["ask_t"] = -1000.0


func hold(id: String) -> void:
	"""stop the leg being walked (ab._tick_leg waits); the panel shows the question of the part"""
	var r := RR()
	r["hold"] = id
	ab.R["walking"] = false
	if not ab.leg.is_empty():
		_hold_h = float(ab.leg["h0"]) + float(ab.leg["t_h"]) * float(ab.leg["f"])
	ab._changed()


func release() -> void:
	"""go on walking: the time spent meanwhile (pauses, the part) stays"""
	var r := RR()
	r["hold"] = ""
	if not ab.leg.is_empty():
		ab.leg["h0"] = float(ab.leg["h0"]) + (main.hour() - _hold_h)
		ab.leg["s0"] = float(ab.R["stamina"]) + float(ab.leg["cost"]) * float(ab.leg["f"])
		ab.R["walking"] = true
	ab.R["pending"] = {}
	ab._changed()


func holds_leg() -> bool:
	return not ab.R.is_empty() and str(RR().get("hold", "")) != ""


func add_xp(n: int) -> void:
	var r := RR()
	if not r.is_empty():
		r["xp"] = int(r["xp"]) + n


func zweit_on() -> bool:
	return ab.zweit != null and bool(ab.zweit.on)


func players() -> Array:
	"""zu zweit: [{i, name, pos (valley), run}] of the walking players (Rollen: only player 1 walks)"""
	var out := []
	if not zweit_on():
		return out
	var z = ab.zweit
	for i in range(1 if str(z.mode) == "rollen" else 2):
		var inp: Dictionary = z._input_of(i)
		out.append({"i": i, "name": str(z.names[i]), "pos": z.pl[i]["pos"], "run": bool(inp.get("run", false))})
	return out


func any_run() -> bool:
	"""zu zweit: one of the two presses «rennen» (Shift / H / R2) right now"""
	if not zweit_on():
		return false
	var z = ab.zweit
	for i in range(2):
		if bool(z._input_of(i).get("run", false)):
			return true
	return false


func mat(c: Color, unshaded := false) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = 0.9
	if unshaded:
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return m


func mesh(parent: Node3D, m: Mesh, c: Color, pos: Vector3, rot := Vector3.ZERO, sc := Vector3.ONE, unshaded := false) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = m
	mi.material_override = mat(c, unshaded)
	mi.position = pos
	mi.rotation = rot
	mi.scale = sc
	if _lite():
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


static func box(x: float, y: float, z: float) -> BoxMesh:
	var b := BoxMesh.new()
	b.size = Vector3(x, y, z)
	return b


static func ball(r: float) -> SphereMesh:
	var s := SphereMesh.new()
	s.radius = r
	s.height = r * 2.0
	s.radial_segments = 8 if _lite() else 12
	s.rings = 4 if _lite() else 6
	return s


static func poly_d(q: Vector2, pts: Array) -> float:
	var best := INF
	for i in range(pts.size() - 1):
		best = minf(best, q.distance_to(Geometry2D.get_closest_point_to_segment(q, pts[i], pts[i + 1])))
	return best


static func cross_pt(pts: Array, line: Array) -> Array:
	"""the first crossing of the path pts with the polyline line: [point, fraction along pts] or []"""
	var total := 0.0
	for i in range(pts.size() - 1):
		total += (pts[i] as Vector2).distance_to(pts[i + 1])
	var acc := 0.0
	for i in range(pts.size() - 1):
		for j in range(line.size() - 1):
			var x = Geometry2D.segment_intersects_segment(pts[i], pts[i + 1], line[j], line[j + 1])
			if x != null:
				return [x, (acc + (pts[i] as Vector2).distance_to(x)) / maxf(1.0, total)]
		acc += (pts[i] as Vector2).distance_to(pts[i + 1])
	return []


static func path_len(pts: Array) -> float:
	var t := 0.0
	for i in range(pts.size() - 1):
		t += (pts[i] as Vector2).distance_to(pts[i + 1])
	return t


func shake(secs := 0.6, amp := 0.06) -> void:
	"""a small shake of the window view (and the two views zu zweit) - Lite: half as strong"""
	if ab.fast or DisplayServer.get_name() == "headless":
		return
	var cams: Array = [main.view_cam]
	if zweit_on():
		for p in ab.zweit.pl:
			if p["cam"] != null:
				cams.append(p["cam"])
	var a := amp * (0.5 if _lite() else 1.0)
	var t0: float = main.now()
	var last := {}
	main.anims.append(func(_dt, _tt):
		var k: float = (main.now() - t0) / secs
		for c in cams:
			if not is_instance_valid(c):
				continue
			var o: Vector3 = last.get(c.get_instance_id(), Vector3.ZERO)
			c.global_position -= o
			var n := Vector3.ZERO
			if k < 1.0:
				n = Vector3(randf_range(-a, a), randf_range(-a, a), randf_range(-a, a)) * (1.0 - k)
			c.global_position += n
			last[c.get_instance_id()] = n
		return k >= 1.0)


# ---- sounds: small generated noises (no files) ------------------------------------------------------------------------------
func snd(kind: String, at: Vector3, db1m := -30.0, gain_db := 0.0) -> void:
	"""raschel | knack | knarr | bruch | kurbel | muh | wasser - MoveEye's microphone hears it (main.add_sound), the PC speakers
	play it only with «Geräusche» on (main.sound_on) and «Am PC hören» (mikrofon.gd pc_on), with «Lautstärke am PC»"""
	var dur: float = {"raschel": 0.9, "knack": 0.12, "knarr": 0.8, "bruch": 0.7, "kurbel": 0.45, "muh": 1.1, "wasser": 1.2}.get(kind, 0.5)
	main.add_sound(db1m, at, dur, "noise" if kind != "muh" else "cows")
	if not bool(main.sound_on) or DisplayServer.get_name() == "headless":
		return
	var mk = main.get("mikro")
	var vol := 40.0
	if mk != null:
		if not bool(mk.get("pc_on")):
			return
		vol = float(mk.get("pc_vol"))
	if vol <= 0.5:
		return
	if not _snd_cache.has(kind):
		_snd_cache[kind] = _synth(kind, dur)
	var pl
	if _lite():
		pl = AudioStreamPlayer.new()
	else:
		pl = AudioStreamPlayer3D.new()
		pl.unit_size = 6.0
		pl.max_distance = 80.0
	pl.stream = _snd_cache[kind]
	pl.volume_db = clampf(linear_to_db(vol / 100.0) + gain_db, -60.0, 6.0)
	add_child(pl)
	if pl is AudioStreamPlayer3D:
		pl.global_position = at
	pl.finished.connect(pl.queue_free)
	pl.play()


func _synth(kind: String, dur: float) -> AudioStreamWAV:
	var rate := 11025 if _lite() else 22050
	var n := int(dur * rate)
	var pcm := PackedByteArray()
	pcm.resize(n * 2)
	var lp := 0.0
	var r := RandomNumberGenerator.new()
	r.seed = hash(kind)
	for i in range(n):
		var t := float(i) / rate
		var k := t / dur
		var v := 0.0
		var nz := r.randf() * 2.0 - 1.0
		match kind:
			"raschel":                                    # leaves / grass: soft noise in little bursts
				lp = lerpf(lp, nz, 0.35)
				v = lp * (0.5 + 0.5 * sin(t * TAU * 7.0 + sin(t * 23.0))) * sin(PI * k) * 0.6
			"knack":                                      # a twig
				v = nz * exp(-t * 60.0) * 1.4
			"knarr":                                      # old wood: a low, rough tone that wanders
				var f := 95.0 + 40.0 * sin(t * 5.0)
				v = (signf(sin(TAU * f * t)) * 0.35 + nz * 0.25) * sin(PI * k) * (0.6 + 0.4 * sin(t * TAU * 11.0))
			"bruch":                                      # a board breaks: crack + thud
				v = nz * exp(-t * 18.0) * 1.3 + sin(TAU * 70.0 * t) * exp(-t * 9.0) * 0.6
			"kurbel":                                     # the ratchet of the winch
				v = nz * (1.0 if fmod(t, 0.075) < 0.008 else 0.0) * 1.2
			"muh":
				var ph := TAU * (110.0 - 25.0 * k) * t
				v = (sin(ph) + 0.6 * sin(2.0 * ph) + 0.4 * sin(3.0 * ph)) * sin(PI * k) * 0.35
			"wasser":
				lp = lerpf(lp, nz, 0.2)
				v = lp * 0.5 * sin(PI * k)
		pcm.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 26000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = rate
	w.data = pcm
	return w


# =======================================================================================================================
# the stone men (Steinmännchen)
# =======================================================================================================================
static func _walk_pts(c: int) -> Array:
	var st: Array = D.CHAPTERS[c - 1]["stages"]
	var si: int = int(STEIN[c][0])
	if si < st.size() and (st[si] as Dictionary).has("walk"):
		return st[si]["walk"]
	return []


static func _ok_spot(q: Vector2, path: Array) -> bool:
	if absf(q.x) > 990.0 or absf(q.y) > 990.0:
		return false
	if Bt.slope_deg(q.x, q.y, 2.0) > 30.0:
		return false
	for lk in Bt.LAKES:
		if Bt._ell(q, lk) < 1.15:
			return false
	for s in Bt.STREAMS:
		if poly_d(q, s[0]) < 8.0:
			return false
	if poly_d(q, path) < 12.0:
		return false
	return true


static func _los(a: Vector2, ah: float, q: Vector2, qh: float) -> bool:
	var ya := Bt.H(a.x, a.y) + ah
	var yq := Bt.H(q.x, q.y) + qh
	for k in range(1, 16):
		var x := a.lerp(q, k / 16.0)
		if Bt.H(x.x, x.y) > lerpf(ya, yq, k / 16.0) - 0.15:
			return false
	return true


static func stein_xz(c: int) -> Vector2:
	"""where the stone man of chapter c stands (valley): beside the path, off it, seen from it (fixed, no randomness)"""
	var pts := _walk_pts(c)
	if pts.size() < 2 or Bt._hm.size() < Bt.N * Bt.N:
		return Vector2.ZERO                                # (the valley has not been built yet: no height map)
	var tot := path_len(pts)
	var want := tot * float(STEIN[c][1])
	var p: Vector2 = pts[0]
	var d := Vector2(0, -1)
	for i in range(pts.size() - 1):
		var L: float = (pts[i] as Vector2).distance_to(pts[i + 1])
		if want <= L or i == pts.size() - 2:
			d = ((pts[i + 1] as Vector2) - (pts[i] as Vector2)).normalized()
			p = (pts[i] as Vector2).lerp(pts[i + 1], clampf(want / maxf(0.01, L), 0.0, 1.0))
			break
		want -= L
	var side := Vector2(-d.y, d.x)
	for dist in [26.0, 20.0, 32.0, 38.0, 18.0]:
		for sd in [1.0, -1.0]:
			for fw in [6.0, 0.0, 12.0]:
				var q: Vector2 = p + side * sd * dist + d * fw
				if _ok_spot(q, pts) and _los(p, 1.7, q, 0.7):
					return q
	return p + side * 24.0


func _build_stein(root: Node3D, c: int) -> void:
	var q := stein_xz(c)
	if q == Vector2.ZERO:
		return
	var n := Node3D.new()
	n.name = "gh_stein"
	root.add_child(n)
	n.global_position = wg(q, 0.0)
	var rs := [0.32, 0.25, 0.2, 0.15, 0.11] if not _lite() else [0.3, 0.22, 0.13]
	var y := 0.0
	var cols := [Color(0.52, 0.5, 0.47), Color(0.6, 0.58, 0.55), Color(0.47, 0.46, 0.44), Color(0.56, 0.55, 0.5), Color(0.62, 0.6, 0.57)]
	for i in range(rs.size()):
		var r: float = rs[i]
		var h := r * 0.55
		y += h
		mesh(n, ball(r), cols[i % cols.size()], Vector3(0, y - h * 0.1, 0), Vector3(0, i * 0.9, 0.05 * (i % 2)), Vector3(1.15, 0.55, 0.95))
		y += h * 0.8
	_stein = n
	n.set_meta("gh_ch", c)


func found_stein(c: int, how: String, who := "") -> bool:
	var st: Dictionary = S()["steine"]
	if st.has(str(c)):
		return false
	st[str(c)] = str(STEIN[c][2])
	add_xp(15)
	RR()["neu"].append("stein%d" % c)
	var z := str(STEIN[c][2])
	var tx := T.t("Abseits des Weges, zwischen Gras und Steinen: ein kleines Steinmännchen, kaum kniehoch. In den obersten Stein ist ein Zeichen geritzt: «%s».") % z
	if who != "":
		tx = who + ": " + tx
	ab._diary("gh_stein", T.t("Ein kleines Steinmännchen"), tx)
	main.start_info = T.t("Ein kleines Steinmännchen mit dem Zeichen «%s» (%d von 5)") % [z, st.size()]
	if _stein != null and is_instance_valid(_stein):
		var tw := create_tween()
		tw.tween_property(_stein, "scale", Vector3(1.15, 1.15, 1.15), 0.2)
		tw.tween_property(_stein, "scale", Vector3.ONE, 0.25)
	if st.size() >= 5:
		badge("steine")
	ab._save()
	ab._changed()
	return true


func zeichen() -> String:
	"""the signs found so far, in the order of the chapters (· = not yet)"""
	var st: Dictionary = S()["steine"]
	var out := []
	for c in range(1, 6):
		out.append(str(st.get(str(c), "·")))
	return " ".join(out)


func badge(id: String) -> void:
	var b: Dictionary = S()["badges"]
	if b.has(id) or not BADGES.has(id):
		return
	b[id] = Time.get_datetime_string_from_system().substr(0, 16)
	add_xp(50)
	var bd: Array = BADGES[id]
	var ed = main.get("entdecken")
	var eid := "berg.abenteuer.geheim." + id
	if ed != null and ed.has_method("register"):
		# only now: before, the book does not show a «???» for it (it is a secret); never «possible» = no Blinki hint
		ed.register(eid, {"scene": "bergtal", "title": T.t(str(bd[0])), "short_text": T.t(str(bd[1])), "hint": "", "icon": "🗿",
				"position": Vector3.ZERO, "radius": 1.0, "kind": "szene", "los": false, "active": func(): return false})
		ed.mark_found(eid, "api")
	main.start_info = "🏅 " + T.t(str(bd[0]))
	ab._diary("gh_badge", T.t(str(bd[0])), T.t(str(bd[1])))


func _click(p: Vector2) -> void:
	"""a click into the window view (nothing else is changed: main.gd gets the click too)"""
	if ab.R.is_empty() or main.scene != "bergtal" or _stein == null or not is_instance_valid(_stein):
		return
	var cam: Camera3D = get_viewport().get_camera_3d()
	if cam == null:
		return
	var c := int(_stein.get_meta("gh_ch"))
	if S()["steine"].has(str(c)):
		return
	var wp: Vector3 = _stein.global_position + Vector3(0, 0.45, 0)
	if cam.is_position_behind(wp):
		return
	var d := cam.global_position.distance_to(wp)
	var mx := STEIN_KLICK_M * clampf(70.0 / maxf(1.0, cam.fov), 1.0, 8.0)
	if d > mx:
		return
	var sp := cam.unproject_position(wp)
	var vp := get_viewport().get_visible_rect().size
	var px := 0.9 / (2.0 * d * tan(deg_to_rad(cam.fov) / 2.0)) * vp.y
	if sp.distance_to(p) > maxf(18.0, px):
		return
	var b = bt()
	if b != null:
		for k in range(1, 12):
			var x := cam.global_position.lerp(wp, k / 12.0)
			if b.gy(x.x, x.z) > x.y + 0.1:
				return
	found_stein(c, "klick")


func stein_test(c: int) -> Dictionary:
	"""tests without a picture: the view goes 15 m from the stone man, looks at it, then the real click code"""
	if c != ch() or _stein == null or not is_instance_valid(_stein):
		return {"ok": false, "error": "kein Steinmännchen in diesem Kapitel gebaut", "chapter": ch()}
	var wp: Vector3 = _stein.global_position + Vector3(0, 0.45, 0)
	main._to_free_view()
	if main.fly_tw != null:
		main.fly_tw.kill()
	var b = bt()
	var dir := Vector3(1, 0, 0.3).normalized()
	var eye := wp + dir * 14.0 + Vector3(0, 3.0, 0)
	if b != null:
		eye.y = maxf(eye.y, b.gy(eye.x, eye.z) + 2.0)
	main.view_cam.global_position = eye
	main.view_cam.look_at(wp, Vector3.UP)
	main.view_cam.fov = 70.0
	var sp: Vector2 = main.view_cam.unproject_position(wp)
	_click(sp)
	return {"ok": S()["steine"].has(str(c)), "screen": [snappedf(sp.x, 0.1), snappedf(sp.y, 0.1)], "steine": S()["steine"]}


# =======================================================================================================================
# the double floor of the bivouac (binoculars close to the floor)
# =======================================================================================================================
func fernglas() -> Dictionary:
	"""«Feldstecher: hier durchschauen» - 8× in the direction the view looks (also zu zweit: the two views)"""
	if not ab.has("feldstecher"):
		return {"ok": false, "error": "kein Feldstecher"}
	if not _fz.is_empty():
		_fz_off()
		return {"ok": true, "zoom": false}
	var cams: Array = [main.view_cam]
	if zweit_on():
		for p in ab.zweit.pl:
			if p["cam"] != null and (p["cam"] as Camera3D).current:
				cams.append(p["cam"])
	_fz = {"until": main.now() + (1.0 if ab.fast else 8.0), "cams": cams.map(func(c): return [c, c.fov])}
	for c in cams:
		c.fov = maxf(4.0, c.fov / 8.0)
	var hit := false
	for c in cams:
		if _boden_blick(c):
			hit = true
	if hit and not bool(S()["boden"]):
		_boden_found()
	else:
		main.start_info = T.t("Feldstecher (8×): alles ganz nah.")
	ab._changed()
	return {"ok": true, "zoom": true, "boden": bool(S()["boden"])}


func _fz_off() -> void:
	for e in _fz.get("cams", []):
		if is_instance_valid(e[0]):
			(e[0] as Camera3D).fov = float(e[1])
	_fz = {}


func _boden_blick(c: Camera3D) -> bool:
	"""inside the bivouac (≤ 2.6 m from the middle, ≤ 3 m above the floor), looking steeply down onto the floor plate"""
	var b = bt()
	if b == null or c == null:
		return false
	var p: Vector3 = b.V(c.global_position)
	if Vector2(p.x, p.z).distance_to(BIWAK) > 2.6:
		return false
	var fy: float = b.gy(c.global_position.x, c.global_position.z)
	var hh: float = c.global_position.y - fy
	if hh < 0.2 or hh > 3.0:
		return false
	var f := -c.global_transform.basis.z
	if f.y > -0.45:
		return false
	var t := hh / -f.y
	if t > 3.5:
		return false
	var hp: Vector3 = b.V(c.global_position + f * t)
	return Vector2(hp.x, hp.z).distance_to(BIWAK) < 1.7


func _boden_found() -> void:
	S()["boden"] = true
	add_xp(30)
	RR()["neu"].append("boden")
	ab._diary("gh_boden", T.t("Ein doppelter Boden"), T.t("Durch den Feldstecher siehst du die Bodenplatte riesig nah: eine feine Fuge, die nicht zur Maserung passt. Die Platte lässt sich anheben - darunter ein flaches Fach. Darin, in Wachstuch gewickelt wie die Kartenstücke: eine alte Münze und der Rest einer Tagebuchseite. Darauf steht nur noch: «… lies sie mit der Sonne.»"))
	main.start_info = T.t("Ein doppelter Boden im Biwak!")
	ab._save()


func boden_test() -> Dictionary:
	"""tests: the view inside the bivouac, 1.4 m above the floor, looking down - then «hier durchschauen»"""
	var b = bt()
	if b == null:
		return {"ok": false, "error": "not bergtal"}
	main._to_free_view()
	if main.fly_tw != null:
		main.fly_tw.kill()
	var c: Vector3 = b.WG(BIWAK.x, BIWAK.y, 0.0)
	c.y = b.gy(c.x, c.z) + 1.4
	main.view_cam.global_position = c + Vector3(0.3, 0, 0.2)
	main.view_cam.look_at(c + Vector3(0.1, -1.4, -0.05), Vector3.FORWARD)
	if not _fz.is_empty():
		_fz_off()
	var r := fernglas()
	r["floor_y"] = snappedf(b.gy(c.x, c.z), 0.01)
	return r


# =======================================================================================================================
# the light on the night picture and the page at the light
# =======================================================================================================================
func _licht_spot(cam: Camera3D) -> Vector3:
	"""a point on the ground the head camera sees (in the picture, no hill between), 60–220 m away, far from every named place"""
	var b = bt()
	var o := cam.global_position
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	var places: Array = Bt.all_places()
	for sp in Bt.SPOTS:
		places.append([sp, float(Bt.SPOTS[sp][1]), float(Bt.SPOTS[sp][2])])
	for ang in [0.3, -0.3, 0.18, -0.18, 0.38, -0.38, 0.05]:
		var dir := f.rotated(Vector3.UP, ang)
		for s in range(220, 59, -12):
			var q := o + dir * float(s)
			q.y = b.gy(q.x, q.z) + 0.6
			if not cam.is_position_in_frustum(q):
				continue
			var v: Vector3 = b.V(q)
			var vq := Vector2(v.x, v.z)
			var far := true
			for pl in places:
				if vq.distance_to(Vector2(float(pl[1]), float(pl[2]))) < 90.0:
					far = false
					break
			if not far or not _ok_spot(vq, []):
				continue
			var free := true
			for k in range(1, 20):
				var x := o.lerp(q, k / 20.0)
				if b.gy(x.x, x.z) > x.y - 0.3:
					free = false
					break
			if free:
				return q
	return Vector3.ZERO


func _licht_an() -> void:
	var r := RR()
	var b = bt()
	if b == null or main.cams.is_empty():
		r["licht"] = {"kein": true}
		return
	var cam: Camera3D = main.cams[0]
	var p := _licht_spot(cam)
	if p == Vector3.ZERO:
		r["licht"] = {"kein": true}
		return
	_licht = Node3D.new()
	b.s.root.add_child(_licht)
	_licht.global_position = p
	var d := cam.global_position.distance_to(p)
	var gl := mesh(_licht, ball(clampf(d * 0.004, 0.25, 0.8)), Color(1.0, 0.92, 0.7), Vector3.ZERO, Vector3.ZERO, Vector3.ONE, true)
	gl.name = "glow"
	gl.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if not _lite():
		var ol := OmniLight3D.new()
		ol.light_color = Color(1.0, 0.9, 0.7)
		ol.light_energy = 0.4
		ol.omni_range = 6.0
		_licht.add_child(ol)
	var v: Vector3 = b.V(p)
	r["licht"] = {"x": snappedf(v.x, 0.1), "z": snappedf(v.z, 0.1), "ch": ch(), "an": true}
	_licht_t = 0.0
	_licht_vis = 0.0


func _licht_aus() -> void:
	if _licht != null and is_instance_valid(_licht):
		_licht.queue_free()
	_licht = null


func _licht_tick(n, dt: float) -> void:
	var on := false
	for id in n.active:
		if str(n.active[id]["rec"]["kind"]) == "gh_licht":
			on = true
	var r := RR()
	if on and _licht == null and not r.has("licht"):
		_licht_an()
	elif not on and _licht != null:
		_licht_foto(true)                                 # (the end: MoveEye's time-lapse picture, if nothing reported it)
		_licht_aus()
	if _licht == null:
		return
	_licht_t += dt
	var gl = _licht.get_node_or_null("glow")
	if gl != null:
		gl.visible = fmod(_licht_t, 2.2) < 1.6 or fmod(_licht_t, 0.37) < 0.2   # faint, flickering (grass in front of it)
	var cam: Camera3D = main.cams[0]
	if gl == null or not gl.visible or not cam.is_position_in_frustum(_licht.global_position):
		return
	_licht_vis += dt
	_licht_foto(false)


func _licht_foto(last: bool) -> void:
	var r := RR()
	var li: Dictionary = r.get("licht", {})
	if li.is_empty() or li.has("bild_da") or _licht == null or ab.a1 == null:
		return
	var da: bool = ab.a1._mw_da()
	var meldet: bool = ab.a1._mw_meldet()
	if not ((da and meldet) or (not da and _licht_vis >= 2.0) or (last and _licht_vis > 0.5)):
		return
	var cam: Camera3D = main.cams[0]
	var f := {"id": "%s_gh_licht" % str(ab.R["id"]), "box": ab.a1._box(cam, _licht.global_position, 2.5)}
	ab.a1._bild(f)
	li["bild_da"] = true
	li["bild"] = str(f.get("bild", ""))
	li["box"] = f["box"]
	li["h"] = snappedf(main.hour(), 0.01)
	li["mw"] = da and meldet
	li["quelle"] = "moveeye" if da and meldet else ("zeitraffer" if da else "schaetzung")
	var s := S()
	if not bool(s["blatt"]):
		s["licht"] = {"ch": li["ch"], "x": li["x"], "z": li["z"], "bild": li["bild"], "box": li["box"], "h": li["h"], "mw": li["mw"],
				"quelle": li["quelle"], "gesehen": false}
		ab._save()


func licht_klick(rx: float, ry: float) -> Dictionary:
	"""a tap on the night picture (0 … 1): on the light = you have noticed it"""
	var li: Dictionary = S()["licht"]
	if li.is_empty() or not li.has("box"):
		return {"ok": false, "error": "keine Aufnahme"}
	var bx: Array = li["box"]
	var m := 0.05
	var hit: bool = rx >= float(bx[0]) - m and rx <= float(bx[0]) + float(bx[2]) + m and ry >= float(bx[1]) - m and ry <= float(bx[1]) + float(bx[3]) + m
	if hit and not bool(li.get("gesehen", false)):
		li["gesehen"] = true
		var camp: Vector2 = ab.R.get("camp_xz", Vector2(float(li["x"]), float(li["z"]))) if not ab.R.is_empty() else Vector2(float(li["x"]), float(li["z"]))
		var dd := Vector2(float(li["x"]), float(li["z"])) - camp
		li["richtung"] = _richtung(dd)
		ab._diary("gh_licht", T.t("Ein Licht auf der Aufnahme"), T.t("Auf der Nachtaufnahme von MoveEye leuchtet ganz schwach ein Licht - im %s, wo auf keiner Karte etwas steht.") % T.t(str(li["richtung"])))
		main.start_info = T.t("Da ist ein schwaches Licht auf der Aufnahme!")
		ab._save()
		ab._changed()
	elif not hit:
		main.start_info = T.t("Hier ist nichts Besonderes.")
	return {"ok": true, "hit": hit, "gesehen": bool(li.get("gesehen", false))}


static func _richtung(dd: Vector2) -> String:
	var a := fposmod(rad_to_deg(atan2(dd.x, -dd.y)), 360.0)
	return ["Norden", "Nordosten", "Osten", "Südosten", "Süden", "Südwesten", "Westen", "Nordwesten"][int(round(a / 45.0)) % 8]


func _licht_xz() -> Vector2:
	var li: Dictionary = S()["licht"]
	return Vector2(float(li.get("x", 0.0)), float(li.get("z", 0.0)))


func abstecher_moeglich() -> bool:
	var li: Dictionary = S()["licht"]
	if ab.R.is_empty() or int(ab.step) != 4 or bool(S()["blatt"]) or not bool(li.get("gesehen", false)) or bool(ab.R.get("walking", false)):
		return false
	if str((ab.R.get("pending", {}) as Dictionary).get("kind", "")).begins_with("gh_") or holds_leg():
		return false
	return (ab.R["pos"] as Vector2).distance_to(_licht_xz()) < 260.0


func abstecher() -> Dictionary:
	"""the detour to the light (there and back; the question of the way waits meanwhile)"""
	if not abstecher_moeglich():
		return {"ok": false, "error": "nicht hier"}
	var p: Vector2 = ab.R["pos"]
	var q := _licht_xz()
	var li: Dictionary = ab.leg_info([p, q, p], [])
	main.set_hour(main.hour() + float(li["t_h"]) * (1.3 if main.is_dark() and not ab.has("stirnlampe") else 1.0))
	ab.R["stamina"] = maxf(0.0, float(ab.R["stamina"]) - float(li["cost"]))
	if not ab.fast and bt() != null:
		main.fly_to(wg(q, 1.0), 6.0)
	_blatt_found("")
	return {"ok": true, "t_h": li["t_h"]}


func _blatt_found(who: String) -> void:
	S()["blatt"] = true
	add_xp(40)
	RR()["neu"].append("blatt")
	var tx := T.t("Dort, wo das Licht war, steht ein flacher Stein. Darunter ein altes Blechkästchen mit einem Katzenauge (Reflektor) - es hat in der Nacht das Infrarot-Licht von MoveEye zurückgeworfen. Im Kästchen, in Wachstuch gewickelt wie die Kartenstücke: ein Tagebuchblatt. Darauf die fünf Zeichen der Kartenstücke - Glocke, Wellen, Sonne, Steinmann, See - und darunter der Satz aus dem Brief: «Die Karte gehört jetzt dir - lies sie mit der Sonne.»")
	if who != "":
		tx = who + ": " + tx
	ab._diary("gh_blatt", T.t("Ein verstecktes Tagebuchblatt"), tx)
	main.start_info = T.t("Ein verstecktes Tagebuchblatt!")
	var prev: Dictionary = (ab.R.get("pending", {}) as Dictionary).duplicate(true)
	ab._ask("gh_blatt", T.t("Ein verstecktes Tagebuchblatt"), tx, [["ok", T.t("Einpacken und zurück zum Weg")]], {"gh_prev": prev})
	if _refl != null and is_instance_valid(_refl):
		_refl.queue_free()
	ab._save()


func _build_refl(root: Node3D) -> void:
	var li: Dictionary = S()["licht"]
	if bool(S()["blatt"]) or not li.has("x"):
		return
	var n := Node3D.new()
	root.add_child(n)
	n.global_position = wg(_licht_xz(), 0.0)
	mesh(n, ball(0.45), Color(0.5, 0.48, 0.45), Vector3(0, 0.12, 0), Vector3.ZERO, Vector3(1.3, 0.4, 1.0))
	mesh(n, box(0.22, 0.12, 0.16), Color(0.45, 0.42, 0.36), Vector3(0.35, 0.06, 0.2))
	mesh(n, ball(0.035), Color(0.9, 0.15, 0.1), Vector3(0.35, 0.08, 0.29))
	_refl = n


# =======================================================================================================================
# the night with sounds (a badger at the backpack)
# =======================================================================================================================
func _dachs_spawn(_ev) -> Array:
	var b = bt()
	if b == null or main.cams.is_empty():
		return []
	var cam: Camera3D = main.cams[0]
	var o := cam.global_position
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	f = f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)
	var side := 1.0 if randf() < 0.5 else -1.0
	var a := o + f.rotated(Vector3.UP, side * 0.9) * 16.0         # out of the picture first: rustling round about
	a.y = b.gy(a.x, a.z)
	var m := o + f.rotated(Vector3.UP, side * 0.3) * 9.0
	m.y = b.gy(m.x, m.z)
	var at: Vector3 = o + f * 3.0
	var fn: Node3D = b._food_node
	if fn != null and is_instance_valid(fn):
		at = fn.global_position + Vector3(0.6, 0, 0.4)
	at.y = b.gy(at.x, at.z)
	var away := o + f.rotated(Vector3.UP, -side * 0.8) * 22.0
	away.y = b.gy(away.x, away.z)
	var v = main.spawn("badger", a, m)
	if not v is Node:
		return []
	v.speed = 0.7
	v.route = [[m, 4.0, 0.0], [at, 9.0, 0.0], away]                 # (Dachs: ~2–3 km/h unterwegs, am Rucksack schnüffeln)
	v.set_meta("gh_dachs", true)
	_dachs = v
	RR()["dachs"] = {"da": true, "geraten": ""}
	_snd_t = 1.0
	return [v]


func _dachs_tick(dt: float) -> void:
	if _dachs == null or not is_instance_valid(_dachs) or _dachs.is_queued_for_deletion():
		_dachs = null
		return
	var r := RR()
	var dd: Dictionary = r.get("dachs", {})
	_snd_t -= dt
	if _snd_t <= 0.0:
		_snd_t = randf_range(1.6, 3.2) * (1.6 if _lite() else 1.0)
		var p: Vector3 = _dachs.global_position
		snd("raschel" if randf() < 0.75 else "knack", p + Vector3(randf_range(-1, 1), 0.2, randf_range(-1, 1)), -38.0)
		dd["laut"] = int(dd.get("laut", 0)) + 1
	if dd.has("bild_da") or ab.a1 == null:
		return
	var vis: bool = main.testrun.visible(_dachs) or main.testrun.thermal_visible(_dachs)
	if not vis:
		return
	dd["vis"] = float(dd.get("vis", 0.0)) + dt
	var da: bool = ab.a1._mw_da()
	if (da and ab.a1._mw_meldet()) or (not da and float(dd["vis"]) >= 1.5):
		var cam: Camera3D = main.cams[0]
		var f := {"id": "%s_gh_dachs" % str(ab.R["id"]), "box": ab.a1._box(cam, _dachs.global_position, 0.5)}
		ab.a1._bild(f)
		dd["bild_da"] = true
		dd["bild"] = str(f.get("bild", ""))
		dd["h"] = snappedf(main.hour(), 0.01)
		dd["mw"] = da
		ab._diary("gh_dachs", T.t("MoveEye nimmt etwas auf"), T.t("Es raschelt und knackt ums Lager - MoveEye zeichnet eine Bewegung auf."))


# =======================================================================================================================
# hooks from bergtal_abenteuer.gd
# =======================================================================================================================
func on_start() -> void:
	ab.R.erase("gh")
	RR()
	_root_key = ""
	_licht_aus()
	_fz_off()
	_call("on_start")


func leg_stop(lg: Dictionary, f0: float, f: float) -> bool:
	return _call("leg_stop", [lg, f0, f]) == true


func on_ask() -> void:
	var pe: Dictionary = ab.R.get("pending", {})
	if pe.is_empty():
		return
	_call("on_ask", [pe])


func choose(pe: Dictionary, v: String) -> bool:
	var kind := str(pe.get("kind", ""))
	if kind == "gh_blatt":
		var prev: Dictionary = pe.get("gh_prev", {})
		ab.R["pending"] = prev                              # the question of the way that was open before the detour
		if not ab.choices.is_empty() and str(ab.choices[-1][1]) == "gh_blatt":
			ab.choices.pop_back()                           # (a detour of the player, not part of «genau gleich nochmals»)
		return true
	return _call("choose", [pe, v]) == true


func register_kinds() -> void:
	var n = main.nacht
	if n == null:
		return
	n.register_kind("gh_dachs", _dachs_spawn, "animal", "badger")
	n.register_kind("gh_licht", func(_e): return [], "weather", "light")
	_call("register_kinds", [n])


func plan_extra(out: Array, sp: float, speed: float) -> void:
	"""night_plan: own random numbers (the seed of the night + 4242) - the other events stay as they were"""
	var r := RandomNumberGenerator.new()
	r.seed = int(ab.R.get("night_seed", 1)) + 4242
	var s := S()
	var c := ch()
	var gr := RR()
	gr.erase("dachs")
	gr.erase("licht")
	if c >= 2 and (int(s["ger"]) == 0 or r.randf() < 0.25):
		out.append({"kind": "gh_dachs", "at_h": r.randf_range(0.25, 0.55) * sp})
	if c in LICHT_KAP and not bool(s["blatt"]) and not bool((s["licht"] as Dictionary).get("gesehen", false)):
		out.append({"kind": "gh_licht", "at_h": r.randf_range(0.6, 0.85) * sp, "dur_h": 45.0 * speed / 3600.0})
	_call("plan_extra", [out, sp, speed])


static func kind_name(k: String) -> String:
	return {"gh_dachs": "Raschelnde Geräusche", "gh_licht": "Licht"}.get(k, k)


func morning(res: Dictionary) -> void:
	var r := RR()
	if r.is_empty():
		return
	var s := S()
	if (r.get("dachs", {}) as Dictionary).has("da"):
		s["ger"] = int(s["ger"]) + 1
	_call("morning", [res])
	if bool(res.get("finale", false)) and (s["steine"] as Dictionary).size() >= 5:
		ab._diary("gh_wort", T.t("Die fünf Zeichen"), _wort_text())
	var xp := int(r.get("xp", 0))
	ab.P["xp"] = int(ab.P.get("xp", 0)) + xp
	res["xp"] = int(res["xp"]) + xp
	res["level"] = ab.level()
	res["gh"] = {"xp": xp, "neu": r.get("neu", [])}
	ab._save()


func _wort_text() -> String:
	return T.t("Und die Zeichen der fünf Steinmännchen? Der Reihe nach gelegt ergeben sie ein Wort: %s - genau der kleine See, an dem du jetzt stehst.") % " · ".join(WORT.split(""))


# ---- painting ---------------------------------------------------------------------------------------------------------------
func paint_hud(body: Control) -> void:
	_call("paint_hud", [body])
	var show_fg: bool = ab.has("feldstecher") and not ab.R.is_empty()
	var show_ab := abstecher_moeglich()
	if not show_fg and not show_ab:
		return
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 8)
	body.add_child(row)
	if show_fg:
		ab._btn(row, T.t("Feldstecher aus") if not _fz.is_empty() else T.t("Feldstecher: hier durchschauen"), func(): ab.op({"do": "geheim", "was": "fernglas"}))
	if show_ab:
		ab._btn(row, T.t("Abstecher: dorthin, wo auf der Aufnahme das Licht war"), func(): ab.op({"do": "geheim", "was": "abstecher"}))


func paint_pending(g: Control, pe: Dictionary) -> void:
	_call("paint_pending", [g, pe])


func paint_camp(body: Control) -> void:
	_call("paint_camp", [body])
	if ab.has("feldstecher"):
		ab._btn(body, T.t("Feldstecher aus") if not _fz.is_empty() else T.t("Feldstecher: hier durchschauen"), func(): ab.op({"do": "geheim", "was": "fernglas"}))


func paint_night(body: Control) -> void:
	_call("paint_night", [body])
	var dd: Dictionary = RR().get("dachs", {})
	if int(dd.get("laut", 0)) > 0:
		body.add_child(ab._lab(T.t("Es raschelt und knackt rund ums Lager …"), 13, Color(0.75, 0.8, 0.86)))


func _pic(path: String, sz: Vector2, on_click := Callable()) -> Control:
	var tr := TextureRect.new()
	tr.custom_minimum_size = sz
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_SCALE
	if path != "":
		if not _tex.has(path) and FileAccess.file_exists(path):
			var img := Image.load_from_file(ProjectSettings.globalize_path(path))
			if img != null and not img.is_empty():
				_tex[path] = ImageTexture.create_from_image(img)
		tr.texture = _tex.get(path, null)
	if tr.texture == null:
		var cr := ColorRect.new()
		cr.color = Color(0.05, 0.06, 0.08)
		cr.custom_minimum_size = sz
		cr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		tr.add_child(cr)
	if on_click.is_valid():
		tr.mouse_filter = Control.MOUSE_FILTER_STOP
		tr.gui_input.connect(func(ev):
			if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
				on_click.call(ev.position / tr.size))
	return tr


func paint_morning(body: Control) -> void:
	var r := RR()
	if r.is_empty():
		return
	# the night picture with the light (no explanation - only who taps the light knows)
	var li: Dictionary = r.get("licht", {})
	var sl: Dictionary = S()["licht"]
	if li.has("bild_da") and sl.has("box"):
		var g: VBoxContainer = ab._group(T.t("Nachtaufnahme von MoveEye, %s Uhr") % ab.hm(float(li.get("h", 0.0))), body)
		g.add_child(ab._lab(T.t("MoveEye: Bewegung erkannt - kein Tier."), 12, Color(0.75, 0.8, 0.86)))
		g.add_child(_pic(str(sl.get("bild", "")), Vector2(320, 180), func(q: Vector2): ab.op({"do": "geheim", "was": "licht_klick", "rx": q.x, "ry": q.y})))
		if bool(sl.get("gesehen", false)):
			g.add_child(ab._lab(T.t("Da ist ein schwaches Licht - im %s, wo auf keiner Karte etwas steht.") % T.t(str(sl.get("richtung", ""))), 13, Color(0.95, 0.85, 0.6)))
	# who rustled?
	var dd: Dictionary = r.get("dachs", {})
	if dd.has("da"):
		var g2: VBoxContainer = ab._group(T.t("Wer hat in der Nacht geraschelt?"), body)
		if str(dd.get("geraten", "")) == "":
			g2.add_child(ab._lab(T.t("Die ganze Nacht hat es ums Lager geraschelt und geknackt. Was meinst du - wer war das?"), 13))
			var row := HFlowContainer.new()
			row.add_theme_constant_override("h_separation", 8)
			g2.add_child(row)
			for o in [["fuchs", "Ein Fuchs"], ["dachs", "Ein Dachs"], ["gaemse", "Gämsen"]]:
				var k: String = o[0]
				ab._btn(row, T.t(str(o[1])), func(): ab.op({"do": "geheim", "was": "dachs_rate", "value": k}))
		else:
			if dd.has("bild_da"):
				g2.add_child(_pic(str(dd.get("bild", "")), Vector2(320, 180)))
			var ok := str(dd["geraten"]) == "dachs"
			g2.add_child(ab._lab((T.t("Richtig!") if ok else T.t("Fast!")) + " " + T.t("Auf der Aufnahme von MoveEye sieht man es: ein Dachs. Er hat am Rucksack geschnüffelt und ist dann weitergezogen. Dachse sind nachts unterwegs und suchen Würmer, Wurzeln und Beeren - für Menschen ganz harmlos."), 13, ab.GRN if ok else Color(0.95, 0.85, 0.6)))
			if not dd.has("bild_da"):
				g2.add_child(ab._lab(T.t("(MoveEye hat ihn nur gehört - im Bild war er nicht.)"), 12, ab.ORG))
	_call("paint_morning", [body])
	var neu: Array = r.get("neu", [])
	if not neu.is_empty() or int(r.get("xp", 0)) > 0:
		body.add_child(ab._lab(T.t("+%d Erfahrung aus Abenteuer-Teilen und Geheimnissen") % int(r.get("xp", 0)), 12, Color(0.75, 0.8, 0.86)))


func paint_finale(g: Control) -> void:
	if (S()["steine"] as Dictionary).size() < 5:
		return
	g.add_child(ab._lab(ab.kurz(_wort_text()), 15, Color(0.97, 0.9, 0.7)))
	g.add_child(_wort_bild())


func _wort_bild() -> Control:
	"""the five stones with their signs side by side (drawn - Lite too)"""
	var c := Control.new()
	c.custom_minimum_size = Vector2(300, 70)
	c.draw.connect(func():
		var font := c.get_theme_default_font()
		for i in range(5):
			var x := 30.0 + i * 58.0
			c.draw_circle(Vector2(x, 44), 22.0, Color(0.55, 0.53, 0.5))
			c.draw_circle(Vector2(x, 26), 13.0, Color(0.62, 0.6, 0.56))
			c.draw_string(font, Vector2(x - 8, 54), WORT[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color(0.2, 0.17, 0.12)))
	return c


func paint_chapter(parent: Control) -> void:
	var s := S()
	var n := (s["steine"] as Dictionary).size()
	_call("paint_chapter", [parent])
	if n == 0 and not bool(s["boden"]) and not bool(s["blatt"]):
		return                                            # nothing found yet: no word about secrets
	var t := T.t("Geheimnisse") + ": "
	var parts := []
	if n > 0:
		parts.append(T.t("Zeichen %s") % zeichen())
	if bool(s["boden"]):
		parts.append(T.t("doppelter Boden"))
	if bool(s["blatt"]):
		parts.append(T.t("Tagebuchblatt beim Licht"))
	parent.add_child(ab._lab(t + " · ".join(parts), 12, Color(0.95, 0.85, 0.6)))


# =======================================================================================================================
# the frame: our 3D things, the zoom, the night, the walkers zu zweit
# =======================================================================================================================
func _process(dt: float) -> void:
	if ab == null or main == null:
		return
	if not _fz.is_empty() and main.now() > float(_fz["until"]):
		_fz_off()
		ab._changed()
	var n = main.nacht
	if n != null and n.running and str(n.opts.get("by", "")) == "abenteuer" and not ab.R.is_empty() and int(ab.step) == 6:
		_licht_tick(n, dt)
		_dachs_tick(dt)
	elif _licht != null:
		_licht_aus()
	_call("tick", [dt])
	_t -= dt
	if _t > 0.0:
		return
	_t = 0.5
	var b = bt()
	if ab.R.is_empty() or b == null or main.scene != "bergtal":
		return
	var key := "%s|%d|%d" % [str(ab.R["id"]), ch(), b.s.root.get_instance_id()]
	if key != _root_key or _root == null or not is_instance_valid(_root) or not _root.is_inside_tree():
		_root_key = key
		if _root != null and is_instance_valid(_root):
			_root.queue_free()
		_root = Node3D.new()
		_root.name = "gh_geheim"
		b.s.root.add_child(_root)
		_stein = null
		_refl = null
		if not S()["steine"].has(str(ch())):
			_build_stein(_root, ch())
		_build_refl(_root)
		_call("build", [_root, ch()])
	# zu zweit: walking to the stone man / to the light
	for p in players():
		var q: Vector2 = p["pos"]
		if _stein != null and is_instance_valid(_stein) and q.distance_to(stein_xz(ch())) < STEIN_NAH_M:
			found_stein(ch(), "zweit", str(p["name"]))
		if _refl != null and is_instance_valid(_refl) and not bool(S()["blatt"]) and q.distance_to(_licht_xz()) < 4.0 \
				and (ab.R.get("pending", {}) as Dictionary).get("kind", "") != "gh_blatt":
			_blatt_found(str(p["name"]))


func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		if ev.pressed:
			_press = ev.position
		elif _press != null:
			if (ev.position as Vector2).distance_to(_press) < 6.0:
				_click(ev.position)
			_press = null


# =======================================================================================================================
# places for the developer window / Kontaktbogen (devtool.gd alle_orte): [id, name, x, z, geheim]
# =======================================================================================================================
static func orte(m = null) -> Array:
	var out := []
	for c in range(1, 6):
		var q := stein_xz(c)
		if q != Vector2.ZERO:
			out.append(["geheim_steinmaennchen_%d" % c, "Steinmännchen %d (Zeichen %s)" % [c, STEIN[c][2]], q.x, q.y, true])
	out.append(["geheim_biwak_boden", "Biwak: doppelter Boden", BIWAK.x, BIWAK.y, true])
	var g = m.abenteuer.get("geheim") if m != null and m.get("abenteuer") != null else null
	if g != null:
		var li: Dictionary = g.S()["licht"]
		if li.has("x"):
			out.append(["geheim_licht", "Licht der Nachtaufnahme (Tagebuchblatt)", float(li["x"]), float(li["z"]), true])
		for o in g.act:
			if o.has_method("orte"):
				out.append_array(o.orte())
	else:
		var A = load(TEILE[0])
		if A != null and A.has_method("orte_static"):
			out.append_array(A.orte_static())
	return out


func op(d: Dictionary) -> Dictionary:
	var w := str(d.get("was", d.get("what", "state")))
	var out := {"ok": true}
	match w:
		"stein_test":
			out = stein_test(int(d.get("value", ch())))
		"stein_pos":
			var q := stein_xz(int(d.get("value", ch())))
			out = {"ok": true, "x": q.x, "z": q.y}
		"klick":
			_click(Vector2(float(d.get("x", 0.0)), float(d.get("y", 0.0))))
		"fernglas":
			out = fernglas()
		"boden_test":
			out = boden_test()
		"licht_klick":
			out = licht_klick(float(d.get("rx", 0.0)), float(d.get("ry", 0.0)))
		"licht_test":                                        # tests: tap the middle of the light's box
			var bx: Array = (S()["licht"] as Dictionary).get("box", [])
			out = licht_klick(float(bx[0]) + float(bx[2]) / 2.0, float(bx[1]) + float(bx[3]) / 2.0) if bx.size() == 4 else {"ok": false, "error": "keine Aufnahme"}
		"abstecher":
			out = abstecher()
		"dachs_rate":
			var dd: Dictionary = RR().get("dachs", {})
			if dd.has("da") and str(dd.get("geraten", "")) == "":
				dd["geraten"] = str(d.get("value", ""))
				if dd["geraten"] == "dachs":
					add_xp(10)
				ab._changed()
			out = {"ok": dd.has("da"), "dachs": dd}
		_:
			var r = _call("op", [d])
			if r is Dictionary:
				out = r
	out["gh"] = state()
	return out


func state() -> Dictionary:
	var s := S()
	var out := {"steine": s["steine"], "zeichen": zeichen(), "badges": s["badges"], "boden": s["boden"], "blatt": s["blatt"],
			"licht": (s["licht"] as Dictionary).duplicate(), "ger": s["ger"], "zoom": not _fz.is_empty(), "abstecher": abstecher_moeglich()}
	if not ab.R.is_empty():
		var r := RR()
		out["run"] = {"xp": r.get("xp", 0), "hold": r.get("hold", ""), "neu": r.get("neu", []), "dachs": r.get("dachs", {}), "licht": r.get("licht", {}),
				"stein_gebaut": _stein != null and is_instance_valid(_stein)}
	var teile := {}
	for o in act:
		if o.has_method("state"):
			teile.merge(o.state())
	out["teile"] = teile
	return out
