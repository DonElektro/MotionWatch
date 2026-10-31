extends RefCounted
## «Bergtal · Aussichtspunkte» (Daniel 31.10.2026 03:07/03:10, alles gewählt): was die 8 Aussichtspunkte des Bergtals
## (bergtal.gd VIEWPOINTS: Bank + Gipfelkreuz, Münzfernrohr, Panoramatafel, wild mit Steinmann) bewirken.
##   * Ankommen (Ansicht, Rover oder Schlafplatz dort): zählt als Entdeckung «berg.aussicht.<id>» (main.entdecken) mit einem
##     Panoramafoto (Objektiv wie MoveEyes Kopfkamera, 66°), deckt auf der Karte auf, was man von dort sieht (Sichtfeld).
##   * Münzfernrohr (25×) bzw. Feldstecher (8×) an den anderen Punkten: Zoom-Ansicht; Fernrohr-Funde (nur von dort zählbar);
##     andere beobachten (Wanderer, Fremde, Tiere – die Ansicht folgt ihnen); Wetter früh sehen (Gewitter-/Nebelwand am
##     Horizont, Warnung an den Schlafplatz).
##   * Panoramatafel / Gipfel: Bergnamen über den fernen Gipfeln (nur im Fenster).
##   * Stimmungen: Alpenglühen am Morgen, Abendrot mit langen Schatten, Nebelmeer (bergtal.fogsea), Milchstrasse (sky.gdshader
##     «milky») – nutzen den Himmel / Nebel des Simulators, Lite: ohne Milchstrasse und lange Schatten.
##   * Morgenbewertung: Aussicht +1 für einen Aussichtspunkt, +1 für eine gesehene Stimmung; Gipfel/Grat: Wind und Kälte
##     (gefühlte Temperatur gegen den Schlafsack) senken Sicherheit/Ruhe.
##   * Abzeichen «Alle Gipfel», «Sonnenaufgang auf dem Grat», «Nebelmeer gesehen».
##   * MoveEye-Reichweite: Kegel auf dem Gelände (nur im Fenster), wie weit MoveEye vom Schlafplatz aus erkennt – mit den
##     Standardwerten von MoveEye (proc_width 480, min_area 1500, Wärmebild 0,5 %), Gelände verdeckt.
## Lite: _lite() (Engine-Meta «lite», wie Bib.lite()) – der Koordinator verbindet es mit Quality.lite().
## Steuerung: {"action": "bergtal", "do": "aussicht", "what": info | scope | observe | pano | weather (value storm|fog) |
##   cone (value) | moods (value) | reveal (value) | badges | visit (id) | reset}

const T = preload("res://scripts/i18n.gd")
const SAVE := "user://bergtal_aussicht.json"
const PANO_DIR := "user://bergtal_panorama"
const SUMMITS := ["gipfel", "grat"]
# Münzfernrohr: 25-fache Vergrösserung (Herstellerangabe Tower Optical «Tower Viewer», das übliche Münzfernrohr an
# Aussichtspunkten); an den übrigen Punkten ein Feldstecher 8× (typisch 8 × 42). Sichtfeld = 2·atan(tan(70°/2) / V).
const MAG_SCOPE := 25.0
const MAG_BINO := 8.0
const SCOPE_SECS := 120.0                  # eine Münze = 2 Minuten (wie bei vielen Münzfernrohren)
# Fernrohr-Funde: [Aussichtspunkt, id, bib-Art, Titel, Text, Richtung (° zur Blickrichtung), Abstand (m)]
const FINDS := [["vp_kanzel", "gleitschirm", "paraglider", "Gleitschirm am Gegenhang",
			"Durchs Fernrohr: drüben im Hang liegt ein Gleitschirm. Der Pilot ist zum Glück schon weg.", 18.0, 620.0],
		["vp_kanzel", "fremdes_zelt", "bed_tent1", "Ein zweites Zelt weit hinten",
			"Ganz hinten steht noch ein Zelt – du bist doch nicht ganz allein im Tal.", -28.0, 820.0],
		["vp_pass", "rucksack", "backpack", "Vergessener Rucksack",
			"Ein roter Rucksack weit unten neben dem Weg – jemand hat ihn bei der Pause vergessen.", -14.0, 520.0],
		["vp_pass", "picknick", "picnic_set", "Picknick ohne Leute",
			"Eine rot-weisse Picknickdecke mit Korb auf der Weide – aber niemand weit und breit.", 16.0, 760.0]]
const BADGES := [["alle_gipfel", "Abzeichen: Alle Gipfel", "Du warst auf allen Gipfeln und Graten des Bergtals."],
		["sonnenaufgang_grat", "Abzeichen: Sonnenaufgang auf dem Grat", "Die Sonne ging auf, und du standest oben auf dem Grat."],
		["nebelmeer", "Abzeichen: Nebelmeer gesehen", "Unten das Tal im Nebel, oben du in der klaren Luft."]]
const MOODS := [["alpengluehen", "Alpenglühen", "Die Gipfel leuchten rosa, bevor die Sonne ins Tal kommt."],
		["abendrot", "Abendrot", "Rotes Licht und lange Schatten über dem Tal."],
		["nebelmeer", "Nebelmeer von oben", "Ein weisses Meer aus Nebel, die Gipfel schauen heraus wie Inseln."],
		["milchstrasse", "Milchstrasse", "Klare Bergnacht: die Milchstrasse spannt sich über den Himmel."]]
# MoveEye-Reichweite (Standardwerte von MoveEye, quelle/020_einstellungen.py): Bewegung auf proc_width 480 px, min_area 1500 px²
# × (1 − sensitivity/200), Zusatzkamera mit 320 px (440_zusatzkameras.py), KI-Person ab ≈ 15 px Höhe (Annahme: übliche Grenze
# kleiner Objekte bei YOLO-Modellen), Wärmebild 80 × 62 px, thermal_min_area 0,5 % des Bildes (230_waermebild.py).
const PROC_W := [480.0, 320.0]
const MIN_AREA := 1500.0
const SENS := 50.0
const AI_MIN_PX := 15.0
const TH_MIN_PCT := 0.5
const PERSON := Vector2(0.45, 1.7)        # breit, hoch (m)

static var st := {}
static var _views := {}                    # vp id -> PackedByteArray 128 × 128: von dort sichtbar (Kartenaufdeckung)

var wb: WeakRef                            # bergtal.gd (schwach: bergtal hält dieses Objekt)
var m
var s
var vps: Array = []                        # {id, name, kind, furn, c (Vector2 Tal), look, y}
var finds: Array = []                      # {id, vp, title, text, p (Vector3 Tal), seen_t}
var lite := false
var info := {}
var _obs := {}                             # wer steht gerade an welchem Aussichtspunkt
var _zoom := {}                            # Fernrohr / Feldstecher / Beobachten
var _overlay: CanvasLayer
var _ov_mat: ShaderMaterial
var _ov_label: Label
var _peak_labels: Array = []
var _cone: MeshInstance3D
var _cone_labels: Array = []
var _cone_yaw := 999.0
var _plan := {}                            # Wetter, das kommt: {k, t0, t1, warned, nodes}
var _mood := {}                            # was heute schon geloggt ist
var _shadow0 := -1.0
var _milky := -1.0
var _pano_busy := false
var _pano_vp: SubViewport
var _start_t := 0.0
var _gust_t := 0.0


static func _lite() -> bool:
	return Engine.has_meta("lite") and bool(Engine.get_meta("lite"))


# ---- gespeicherter Stand ---------------------------------------------------------------------------------------------------
static func state() -> Dictionary:
	if st.is_empty():
		st = {"seen": [], "badges": {}, "moods": true, "reveal": true, "cone": false, "pano": {}, "finds": [], "mood_seen": [], "wind0": null}
		if FileAccess.file_exists(SAVE):
			var f := FileAccess.open(SAVE, FileAccess.READ)
			var d = JSON.parse_string(f.get_as_text()) if f != null else null
			if d is Dictionary:
				st.merge(d, true)
	return st


static func save_state() -> void:
	var f := FileAccess.open(SAVE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(st, " "))


static func add_controls(main) -> void:
	"""die Bedienelemente (Gruppe Szene wie die anderen Bergtal-Schalter; Wetter → Mehr Wetter)"""
	main.add_control("button", "bt_aus_scope", "Durchs Fernrohr schauen (Bergtal: an einem Aussichtspunkt)", null, func(): _do(main, "scope"), "Szene")
	main.add_control("button", "bt_aus_pano", "Panoramafoto mit MoveEyes Kamera (Bergtal)", null, func(): _do(main, "pano"), "Szene")
	main.add_control("button", "bt_aus_observe", "Andere beobachten (Bergtal: vom Aussichtspunkt aus)", null, func(): _do(main, "observe"), "Szene", {"expert": true})
	main.add_control("toggle", "bt_aus_cone", "MoveEye-Reichweite auf der Landschaft zeigen (Bergtal)", func(): return bool(state()["cone"]),
			func(v): _set_opt(main, "cone", bool(v)), "Szene", {"expert": true})
	main.add_control("toggle", "bt_aus_moods", "Bergstimmungen (Alpenglühen, Abendrot, Milchstrasse)", func(): return bool(state()["moods"]),
			func(v): _set_opt(main, "moods", bool(v)), "Szene", {"expert": true})
	main.add_control("toggle", "bt_aus_reveal", "Karte nach und nach aufdecken (Bergtal: Aussichtspunkte decken auf)", func(): return bool(state()["reveal"]),
			func(v): _set_opt(main, "reveal", bool(v)), "Szene", {"expert": true})
	main.add_control("button", "bt_aus_badges", "Abzeichen und Aussichtspunkte im Bergtal zeigen", null, func(): _do(main, "badges"), "Szene", {"expert": true})
	main.add_control("button", "bt_aus_storm", "Gewitter kommt von weitem (Bergtal: zuerst am Horizont)", null, func(): _do(main, "weather", "storm"), "Wetter", {"sub": "Mehr Wetter"})
	main.add_control("button", "bt_aus_fog", "Nebel steigt von weitem auf (Bergtal)", null, func(): _do(main, "weather", "fog"), "Wetter", {"sub": "Mehr Wetter"})


static func _mod(main):
	var bt = main.scenes.data.get("bergtal", null) if main.scenes != null else null
	return bt.aussicht if bt != null and bt.get("aussicht") != null else null


static func _do(main, what: String, value = null) -> Dictionary:
	var a = _mod(main)
	if a == null:
		main.start_info = T.t("Das geht nur in der Szene Bergtal.")
		return {"ok": false, "error": "not bergtal"}
	return a.control({"what": what, "value": value})


static func _set_opt(main, key: String, v: bool) -> void:
	state()[key] = v
	save_state()
	var a = _mod(main)
	if a != null:
		a.apply_settings()


# ---- Aufbau ------------------------------------------------------------------------------------------------------------------
func _init(bt) -> void:
	wb = weakref(bt)
	m = bt.m
	s = bt.s
	lite = _lite() or bt.lite


func B():
	return wb.get_ref()


func pieces() -> void:
	"""während des Aufbaus (vor bib.finish): die Fernrohr-Funde – weit weg, vom Fernrohr aus frei sichtbar"""
	var b = B()
	vps.clear()
	for vp in b.VIEWPOINTS:
		var c: Vector2 = b.vp_xz(vp)
		vps.append({"id": str(vp[0]), "name": str(vp[1]), "kind": str(vp[2]), "furn": str(vp[5]), "c": c, "look": float(vp[6]), "y": b.H(c.x, c.y)})
	finds.clear()
	for f in FINDS:
		var vp: Dictionary = _vp(str(f[0]))
		if vp.is_empty():
			continue
		var eye := Vector3(vp.c.x, float(vp.y) + 1.4, vp.c.y)
		var best = null
		for da in [0.0, 4.0, -4.0, 8.0, -8.0, 12.0, -12.0]:            # a free, not too steep place near the wanted one
			for dd in [0.0, -60.0, 60.0, -120.0, 120.0]:
				var az := deg_to_rad(float(vp.look) + float(f[5]) + da)
				var q: Vector2 = vp.c + Vector2(sin(az), -cos(az)) * (float(f[6]) + dd)
				if absf(q.x) > 1000.0 or absf(q.y) > 1000.0 or b.zone(q.x, q.y) == "lake" or b.slope_deg(q.x, q.y) > 28.0:
					continue
				if _los_v(eye, Vector3(q.x, b.H(q.x, q.y) + 0.5, q.y)):
					best = q
					break
			if best != null:
				break
		if best == null:
			continue
		var bq: Vector2 = best
		b.bib.add(str(f[2]), b.P(bq.x, bq.y), randf() * TAU)
		finds.append({"id": "berg.aussicht.fernrohr." + str(f[1]), "vp": str(f[0]), "title": str(f[3]), "text": str(f[4]), "kind": str(f[2]),
				"p": Vector3(bq.x, b.H(bq.x, bq.y) + 0.5, bq.y), "seen_t": 0.0})


func start() -> void:
	"""nach dem Aufbau: Entdeckungen anmelden, Karte, Bergnamen, Gipfel-Risiko, Reichweite"""
	var b = B()
	_start_t = m.now()
	state()
	if st.get("wind0") != null and not _summit_spot():
		m.wind = float(st["wind0"])                    # vom letzten Gipfel-Schlafplatz zurück
		st["wind0"] = null
		save_state()
	_register()
	_summit_risk()
	_peak_label_nodes()
	reveal_update()
	apply_settings()
	var vp := _spot_vp()
	if not vp.is_empty() and not vp.id in st["seen"]:
		_arrive(vp, "spot")
	info["viewpoints"] = vps.size()
	info["finds"] = finds.map(func(f): return {"id": f.id, "vp": f.vp, "world": b.W(f.p)})


func cleanup() -> void:
	"""die Szene geht (bergtal.gd PREDELETE): Ansicht, Überlagerung, Schatten, Wind zurück"""
	scope_off()
	if _overlay != null and is_instance_valid(_overlay):
		_overlay.queue_free()
	if _pano_vp != null and is_instance_valid(_pano_vp):
		_pano_vp.queue_free()
	if m != null and is_instance_valid(m):
		if _shadow0 > 0.0:
			m.sun.directional_shadow_max_distance = _shadow0
		if m.sky_mat != null:
			m.sky_mat.set_shader_parameter("milky", 0.0)
		m.scenes.data.erase("map_fog")


func _vp(id: String) -> Dictionary:
	for v in vps:
		if v.id == id:
			return v
	return {}


func _short(id: String) -> String:
	return id.trim_prefix("vp_")


func _spot_vp() -> Dictionary:
	var b = B()
	return _vp(str(b.spot)) if str(b.spot).begins_with("vp_") else {}


func _summit_spot() -> bool:
	var v := _spot_vp()
	return not v.is_empty() and str(v.kind) in SUMMITS


func _register() -> void:
	var ed = m.get("entdecken")
	if ed == null or not ed.has_method("register"):
		return
	var b = B()
	for v in vps:
		ed.register("berg.aussicht." + _short(v.id), {"scene": "bergtal", "title": T.t("Aussichtspunkt: %s") % T.t(v.name),
				"short_text": T.t(_vp_text(v)), "hint": T.t("Folge den Wegweisern nach oben – dort ist die Aussicht weit."), "icon": "⛰",
				"position": b.WG(v.c.x, v.c.y, 1.5), "size": Vector3(4, 3, 4), "radius": 30.0, "kind": "ort"})
	var never := func(): return false
	for f in finds:
		var vp_id: String = f.vp
		ed.register(f.id, {"scene": "bergtal", "title": T.t(f.title), "short_text": T.t(f.text), "hint": T.t("Nur durchs Münzfernrohr zu sehen."),
				"icon": "🔭", "position": b.W(f.p), "size": Vector3(2, 1.5, 2), "radius": 1200.0, "kind": "ort",
				"active": func(): return _zoom.get("vp", "") == vp_id})
	for md in MOODS:
		ed.register("berg.aussicht.stimmung." + str(md[0]), {"scene": "bergtal", "title": T.t(str(md[1])), "short_text": T.t(str(md[2])),
				"hint": T.t("An einem Aussichtspunkt, zur richtigen Zeit."), "icon": "🌄", "position": b.WG(vps[0].c.x, vps[0].c.y, 2.0),
				"radius": 1.0, "kind": "szene", "los": false, "active": never, "when": "morning" if md[0] == "alpengluehen" else ("evening" if md[0] == "abendrot" else ("night" if md[0] == "milchstrasse" else "any"))})
	for bd in BADGES:
		ed.register("berg.aussicht.abzeichen." + str(bd[0]), {"scene": "bergtal", "title": T.t(str(bd[1])), "short_text": T.t(str(bd[2])),
				"hint": T.t("Ein Abzeichen der Aussichtspunkte."), "icon": "🏅", "position": b.WG(vps[0].c.x, vps[0].c.y, 2.0), "radius": 1.0,
				"kind": "szene", "los": false, "active": never})


func _vp_text(v: Dictionary) -> String:
	match str(v.kind):
		"gipfel":
			return "Ein Gipfel mit Rundumsicht – ausgesetzt und windig."
		"grat":
			return "Oben auf dem Grat: Sicht nach beiden Seiten, viel Wind."
		"kanzel":
			return "Eine Felskanzel hoch über dem Tal."
		"see":
			return "Hoch über dem See – die Berge spiegeln sich im Wasser."
	return "Der Blick auf den Gletscher mit seinen Spalten."


func _found(id: String, how := "api") -> bool:
	var ed = m.get("entdecken")
	if ed != null and ed.has_method("mark_found"):
		return bool(ed.mark_found(id, how))
	return false


# ---- jeden Frame / 4 × pro Sekunde (von bergtal._tick) --------------------------------------------------------------------------
func frame(dt: float) -> void:
	_moods_frame(dt)
	_plan_frame(dt)
	if not _zoom.is_empty() and _ov_label != null:
		var left: float = float(_zoom.get("until", 0.0)) - m.now()
		var tx := "%s %d×" % [T.t("Münzfernrohr") if _zoom.mag >= MAG_SCOPE else T.t("Feldstecher"), int(_zoom.mag)]
		if _zoom.mag >= MAG_SCOPE:
			tx += "  ·  %s %d:%02d" % [T.t("noch"), int(left) / 60, int(left) % 60]
		var tg = _zoom.get("target")
		if tg != null and is_instance_valid(tg):
			tx += "  ·  %s %s, %d m" % [T.t("beobachtet:"), T.t(_kind_name(tg)), int(tg.global_position.distance_to(_zoom.eye))]
		_ov_label.text = tx + "  ·  " + T.t("Maus: schauen · nochmals drücken: beenden")


func slow() -> void:
	"""4 × pro Sekunde"""
	var b = B()
	_obs = observer()
	if not _obs.is_empty() and _obs.who != "spot" and not _obs.vp.id in st["seen"]:
		_arrive(_obs.vp, str(_obs.who))
	_peaks_visible()
	_moods_log()
	_plan_slow()
	_scope_slow()
	_summit_night()
	if bool(st["cone"]):
		_cone_update()
	if not _zoom.is_empty():
		if m.view_mode != 0 or (float(_zoom.get("until", 0.0)) > 0.0 and m.now() > float(_zoom["until"])):
			scope_off()
			m.start_info = T.t("Die Zeit im Münzfernrohr ist um.")
	b.info["aussicht"] = info_dict()


func observer() -> Dictionary:
	"""wer steht an einem Aussichtspunkt: die Ansicht (frei), der Rover (Erkunden) oder MoveEye selbst (Schlafplatz dort)"""
	var b = B()
	var cands := []
	if m.view_mode == 0 and _zoom.is_empty():
		cands.append(["view", m.view_cam.global_position])
	if (m.mover_on or (m.explore != null and m.explore.on)) and m.rig.global_position.length() > 2.0:
		cands.append(["rover", m.rig.global_position + Vector3(0, 1.5, 0)])
	for c in cands:
		var q: Vector3 = b.V(c[1])
		for v in vps:
			if Vector2(q.x, q.z).distance_to(v.c) < 45.0 and q.y - b.H(q.x, q.z) < 40.0:
				return {"vp": v, "who": c[0], "pos": c[1]}
	if not _zoom.is_empty():
		var zv := _vp(str(_zoom.vp))
		if not zv.is_empty():
			return {"vp": zv, "who": "scope", "pos": _zoom.eye}
	var sv := _spot_vp()
	if not sv.is_empty():
		return {"vp": sv, "who": "spot", "pos": m.head.global_position}
	return {}


func _arrive(v: Dictionary, who: String) -> void:
	var b = B()
	st["seen"].append(v.id)
	save_state()
	reveal_update()
	var n_sum := vps.filter(func(x): return str(x.kind) in SUMMITS).size()
	var got_sum := vps.filter(func(x): return str(x.kind) in SUMMITS and x.id in st["seen"]).size()
	m.start_info = "%s %s (%s %d %s %d) – %s" % [T.t("Aussichtspunkt entdeckt:"), T.t(v.name), T.t("Aussichtspunkte"), st["seen"].size(), T.t("von"), vps.size(),
			T.t("die Karte zeigt jetzt, was man von hier sieht.")]
	if str(v.kind) in SUMMITS:
		m.start_info += " · %s %d/%d" % [T.t("Gipfel"), got_sum, n_sum]
	if not str(b.spot) == v.id:
		b.night_log.append({"k": "vp_visit", "t": m.hour(), "text": "Aussichtspunkt besucht"})
	_found("berg.aussicht." + _short(v.id), "view")
	if got_sum >= n_sum and str(v.kind) in SUMMITS:
		badge("alle_gipfel")
	# the panorama photo for the book (the lens of MoveEye's head camera, at the viewpoint)
	var full := str(v.kind) in SUMMITS
	var eye: Vector3 = b.WG(v.c.x, v.c.y, 1.6)
	if who == "spot":
		eye = m.head.global_position
	panorama(eye, float(v.look), full, v.id, 2.5 if who == "spot" else 0.4)


func badge(id: String) -> void:
	if st["badges"].has(id):
		return
	st["badges"][id] = Time.get_datetime_string_from_system().substr(0, 16)
	save_state()
	for bd in BADGES:
		if bd[0] == id:
			m.start_info = "🏅 " + T.t(str(bd[1]))
			m._say(T.t(str(bd[1])), m.view_cam.global_position + (-m.view_cam.global_transform.basis.z) * 6.0, Color("#ffd166"), m.HELPER_LAYER)
	_found("berg.aussicht.abzeichen." + id)


func info_dict() -> Dictionary:
	var out := info.duplicate()
	out.merge({"seen": st["seen"], "badges": st["badges"], "observer": {} if _obs.is_empty() else {"vp": _obs.vp.id, "who": _obs.who},
			"zoom": {} if _zoom.is_empty() else {"vp": _zoom.vp, "mag": _zoom.mag, "fov": snappedf(float(_zoom.fov), 0.01), "observing": _zoom.get("target") != null},
			"forecast": {} if _plan.is_empty() else {"k": _plan.k, "eta_s": int(float(_plan.t1) - m.now()), "warned": _plan.warned},
			"moods": _mood, "milky": snappedf(_milky, 0.01), "settings": {"moods": st["moods"], "reveal": st["reveal"], "cone": st["cone"]},
			"panoramas": st["pano"], "finds_found": st["finds"]}, true)
	return out


# ---- Bergnamen über den fernen Gipfeln (Panoramatafel, Gipfel) --------------------------------------------------------------------
func _peak_label_nodes() -> void:
	var b = B()
	_peak_labels.clear()
	for pk in b.PEAKS:
		var az := deg_to_rad(float(pk[1]))
		_peak_labels.append(_label("%s\n%d m" % [str(pk[0]), int(float(pk[2]) + b.ALT0 + 300.0)], Vector3(sin(az) * 3900.0, float(pk[2]) + 120.0, -cos(az) * 3900.0)))
	for v in vps:
		if str(v.kind) in SUMMITS:
			_peak_labels.append(_label("%s\n%d m" % [T.t(v.name), int(float(v.y) + b.ALT0)], Vector3(v.c.x, float(v.y) + 25.0, v.c.y)))


func _label(tx: String, p: Vector3) -> Label3D:
	var l := Label3D.new()
	l.text = tx
	l.position = p
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.fixed_size = true
	l.pixel_size = 0.0009
	l.font_size = 40
	l.no_depth_test = true
	l.modulate = Color(1.0, 1.0, 0.95)
	l.outline_size = 10
	l.outline_modulate = Color(0.1, 0.12, 0.15)
	l.layers = m.HELPER_LAYER
	l.visible = false
	B().tal.add_child(l)
	return l


func _peaks_visible() -> void:
	var on: bool = not _obs.is_empty() and _obs.who != "spot" and (str(_obs.vp.furn) == "tafel" or str(_obs.vp.kind) in SUMMITS or _obs.who == "scope")
	for l in _peak_labels:
		if is_instance_valid(l):
			l.visible = on and (l.global_position - m.view_cam.global_position).length() > 60.0


# ---- Fernrohr, Feldstecher, andere beobachten -------------------------------------------------------------------------------------
func scope(mode := "fernrohr") -> Dictionary:
	var b = B()
	if not _zoom.is_empty() and mode == "fernrohr":
		scope_off()
		return {"ok": true, "zoom": false}
	var ob := observer()
	if ob.is_empty():
		m.start_info = T.t("Zuerst zu einem Aussichtspunkt gehen (Schnellreise oder hinfliegen) – dort gibt es Fernrohr oder Feldstecher.")
		return {"ok": false, "error": "not at a viewpoint"}
	var v: Dictionary = ob.vp
	var mag := MAG_SCOPE if str(v.furn) == "fernrohr" else MAG_BINO
	var eye: Vector3 = b.WG(v.c.x, v.c.y, 1.35 if mag >= MAG_SCOPE else 1.65)
	if ob.who == "spot" and mag < MAG_SCOPE:
		eye = m.head.global_position + Vector3(0, 0.1, 0)
	var fov := rad_to_deg(2.0 * atan(tan(deg_to_rad(35.0)) / mag))
	if m.has_method("_to_free_view"):
		m._to_free_view()
	if m.fly_tw != null:
		m.fly_tw.kill()
	var az := deg_to_rad(float(v.look))
	var dir: Vector3 = b.tal.basis * Vector3(sin(az), -0.04, -cos(az))
	m.view_cam.global_position = eye
	m.view_cam.look_at(eye + dir, Vector3.UP)
	_zoom = {"vp": v.id, "mag": mag, "fov": fov, "eye": eye, "until": m.now() + SCOPE_SECS if mag >= MAG_SCOPE else 0.0, "target": null, "ti": -1}
	if not RenderingServer.frame_pre_draw.is_connected(_pre_draw):
		RenderingServer.frame_pre_draw.connect(_pre_draw)
	_overlay_show(true, mag < MAG_SCOPE)
	m.start_info = T.t("Münzfernrohr: eine Münze, 2 Minuten. Schau mit der Maus herum – in der Ferne gibt es Dinge, die man nur von hier sieht.") if mag >= MAG_SCOPE \
			else T.t("Feldstecher (8×): schau mit der Maus herum.")
	return {"ok": true, "zoom": true, "vp": v.id, "mag": mag, "fov": snappedf(fov, 0.01), "eye": eye}


func scope_off() -> void:
	if _zoom.is_empty():
		return
	var tg = _zoom.get("marker")
	if tg != null and is_instance_valid(tg):
		tg.queue_free()
	_zoom = {}
	if RenderingServer.frame_pre_draw.is_connected(_pre_draw):
		RenderingServer.frame_pre_draw.disconnect(_pre_draw)
	_overlay_show(false, false)
	if m != null and is_instance_valid(m):
		m.view_cam.fov = 70.0


func _pre_draw() -> void:
	"""after main._fly (which sets fov 70 and moves with W A S D): the view stays at the eyepiece, zoomed; observing: it follows"""
	if _zoom.is_empty() or m == null or not is_instance_valid(m):
		return
	m.view_cam.global_position = _zoom.eye
	m.view_cam.fov = float(_zoom.fov)
	var tg = _zoom.get("target")
	if tg != null:
		if not is_instance_valid(tg) or tg.done:
			_zoom["target"] = null
		else:
			var tp: Vector3 = tg.global_position + Vector3(0, 0.8, 0)
			var cur: Vector3 = -m.view_cam.global_transform.basis.z
			var want: Vector3 = (tp - _zoom.eye).normalized()
			m.view_cam.look_at(_zoom.eye + cur.slerp(want, 0.15), Vector3.UP)
			var mk = _zoom.get("marker")
			if mk != null and is_instance_valid(mk):
				mk.global_position = tg.global_position + Vector3(0, 2.6, 0)


func observe() -> Dictionary:
	"""andere beobachten: die Ansicht (Feldstecher oder Fernrohr) folgt dem nächsten Wanderer / Fremden / Tier, das man von hier sieht"""
	if _zoom.is_empty():
		var r := scope("beobachten")
		if not bool(r.get("ok", false)):
			return r
	var eye: Vector3 = _zoom.eye
	var lst := []
	for v in m.visitors.get_children():
		if v.done:
			continue
		var d: float = v.global_position.distance_to(eye)
		if d < 1800.0 and d > 3.0 and _los_w(eye, v.global_position + Vector3(0, 0.8, 0)):
			lst.append([d, v])
	lst.sort_custom(func(a, c): return a[0] < c[0])
	if lst.is_empty():
		m.start_info = T.t("Von hier siehst du gerade niemanden – warte etwas oder schau später nochmals.")
		return {"ok": true, "targets": 0}
	var i := (int(_zoom.get("ti", -1)) + 1) % lst.size()
	_zoom["ti"] = i
	var tg = lst[i][1]
	_zoom["target"] = tg
	var mk = _zoom.get("marker")
	if mk == null or not is_instance_valid(mk):
		mk = Label3D.new()
		mk.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		mk.fixed_size = true
		mk.pixel_size = 0.0008
		mk.font_size = 36
		mk.no_depth_test = true
		mk.modulate = Color("#ffd166")
		mk.outline_size = 8
		mk.layers = m.HELPER_LAYER
		s.root.add_child(mk)
		_zoom["marker"] = mk
	mk.text = "▼ %s" % T.t(_kind_name(tg))
	m.start_info = "%s %s, %d m (%d %s %d)" % [T.t("Du beobachtest:"), T.t(_kind_name(tg)), int(lst[i][0]), i + 1, T.t("von"), lst.size()]
	return {"ok": true, "targets": lst.size(), "kind": str(tg.kind), "dist": snappedf(float(lst[i][0]), 0.1)}


func _kind_name(v) -> String:
	var k := str(v.kind)
	if k == "person":
		return "Fremder" if str(v.get_meta("bt", "")) == "berg_stranger" else "Wanderer"
	return {"cow": "Kuh", "sheep": "Schaf", "fox": "Fuchs", "deer": "Hirsch", "chamois": "Gämse", "ibex": "Steinbock", "marmot": "Murmeltier",
			"hare": "Schneehase", "car": "Auto", "dog": "Hund"}.get(k, "Tier")


func _scope_slow() -> void:
	"""Fernrohr-Funde: in der Mitte des Fernrohrs, frei sichtbar, eine Weile angeschaut"""
	if _zoom.is_empty():
		return
	var b = B()
	var fwd: Vector3 = -m.view_cam.global_transform.basis.z
	for f in finds:
		if f.vp != _zoom.vp or f.id in st["finds"]:
			continue
		var wp: Vector3 = b.W(f.p)
		var ang := rad_to_deg(fwd.angle_to((wp - _zoom.eye).normalized()))
		if ang < float(_zoom.fov) * 0.3:
			f.seen_t += 0.25
			if f.seen_t >= 0.75:
				st["finds"].append(f.id)
				save_state()
				_found(f.id, "view")
				m.start_info = "🔭 %s – %s" % [T.t(f.title), T.t(f.text)]
		else:
			f.seen_t = 0.0


func _overlay_show(on: bool, bino: bool) -> void:
	if not on:
		if _overlay != null and is_instance_valid(_overlay):
			_overlay.visible = false
		return
	if _overlay == null or not is_instance_valid(_overlay):
		_overlay = CanvasLayer.new()
		_overlay.layer = 4
		var cr := ColorRect.new()
		cr.set_anchors_preset(Control.PRESET_FULL_RECT)
		cr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var sh := Shader.new()
		sh.code = """shader_type canvas_item;
uniform vec2 res = vec2(1280.0, 720.0);
uniform float bino = 0.0;
void fragment() {
	vec2 p = (UV - 0.5) * vec2(res.x / res.y, 1.0);
	float d = bino > 0.5 ? min(length(p - vec2(-0.21, 0.0)), length(p - vec2(0.21, 0.0))) - 0.36 : length(p) - 0.46;
	COLOR = vec4(0.0, 0.0, 0.0, smoothstep(-0.012, 0.012, d) * 0.97);
}"""
		_ov_mat = ShaderMaterial.new()
		_ov_mat.shader = sh
		cr.material = _ov_mat
		_overlay.add_child(cr)
		_ov_label = Label.new()
		_ov_label.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
		_ov_label.position = Vector2(-360, -46)
		_ov_label.size = Vector2(720, 30)
		_ov_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_ov_label.add_theme_color_override("font_color", Color(0.95, 0.95, 0.9))
		_ov_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_overlay.add_child(_ov_label)
		m.add_child(_overlay)
	_overlay.visible = true
	_ov_mat.set_shader_parameter("res", m.get_viewport().get_visible_rect().size)
	_ov_mat.set_shader_parameter("bino", 1.0 if bino else 0.0)


# ---- Panoramafoto (Objektiv wie MoveEyes Kopfkamera) ---------------------------------------------------------------------------
func panorama(eye: Vector3, look_deg: float, full: bool, vp_id: String, delay := 0.0) -> Dictionary:
	"""6 Bilder rundum (Gipfel, Grat, Knopf) oder 3 in Blickrichtung (66° wie MoveEyes Kamera 0), aneinandergesetzt"""
	if _pano_busy:
		return {"ok": false, "error": "busy"}
	_pano_busy = true
	_pano_run(eye, look_deg, full, vp_id, delay)
	return {"ok": true, "shots": 6 if full else 3}


func _pano_run(eye: Vector3, look_deg: float, full: bool, vp_id: String, delay: float) -> void:
	if delay > 0.0:
		await m.get_tree().create_timer(delay).timeout
	var b = B()
	if b == null or not is_instance_valid(m):
		_pano_busy = false
		return
	var w := 320 if lite else 480
	var h := w * 9 / 16
	if _pano_vp == null or not is_instance_valid(_pano_vp):
		_pano_vp = SubViewport.new()
		_pano_vp.size = Vector2i(w, h)
		_pano_vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		var cam := Camera3D.new()
		cam.keep_aspect = Camera3D.KEEP_WIDTH
		cam.fov = float(m.CAM_FOV[0])                    # MoveEye's head camera (Camera Module 3 NoIR, 66°)
		cam.near = 0.1
		cam.far = 7000.0                                 # (a photo: the far mountains too; MoveEye's own pictures end at 2000 m)
		cam.cull_mask = 1                                # what MoveEye sees: no helper marks
		_pano_vp.add_child(cam)
		m.add_child(_pano_vp)
	var cam: Camera3D = _pano_vp.get_child(0)
	cam.current = true
	var n := 6 if full else 3
	var step := 60.0                                     # 66° lens: 6° overlap, the middle 60° of each picture are used
	var cw := int(w * step / float(m.CAM_FOV[0]))
	var out := Image.create(cw * n, h, false, Image.FORMAT_RGB8)
	for k in range(n):
		var az := deg_to_rad(look_deg + (k - (n - 1) / 2.0) * step if not full else look_deg - 180.0 + (k + 0.5) * step)
		var dir: Vector3 = b.tal.basis * Vector3(sin(az), -0.05, -cos(az))
		cam.global_position = eye
		cam.look_at(eye + dir, Vector3.UP)
		_pano_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		await RenderingServer.frame_post_draw
		if not is_instance_valid(_pano_vp):
			_pano_busy = false
			return
		var img := _pano_vp.get_texture().get_image()
		if img == null or img.is_empty():
			continue
		img.convert(Image.FORMAT_RGB8)
		out.blit_rect(img, Rect2i((w - cw) / 2, 0, cw, h), Vector2i(k * cw, 0))
	if m.is_dark():
		out.adjust_bcs(1.8, 1.1, 0.9)                    # the book: night pictures a little lighter
	DirAccess.make_dir_recursive_absolute(PANO_DIR)
	var path := "%s/%s.jpg" % [PANO_DIR, vp_id.validate_filename()]
	out.save_jpg(path, 0.85)
	st["pano"][vp_id] = path
	save_state()
	info["last_pano"] = {"path": path, "size": [out.get_width(), out.get_height()], "vp": vp_id}
	var ed = m.get("entdecken")
	var bid := "berg.aussicht." + _short(vp_id)
	if ed != null and ed.has_method("_store_pic") and ed.has_method("is_found") and ed.is_found(bid):
		var th := Image.create(192, 108, false, Image.FORMAT_RGB8)       # the panorama as a strip in the book's small picture
		th.fill(Color(0.08, 0.09, 0.1))
		var pv := out.duplicate()
		pv.resize(192, maxi(8, int(192.0 * out.get_height() / out.get_width())), Image.INTERPOLATE_BILINEAR)
		th.blit_rect(pv, Rect2i(Vector2i.ZERO, pv.get_size()), Vector2i(0, (108 - pv.get_height()) / 2))
		ed._store_pic(bid, th)
	_pano_busy = false
	if is_instance_valid(_pano_vp):
		_pano_vp.queue_free()
		_pano_vp = null
	m.start_info = "%s %s" % [T.t("Panoramafoto gespeichert:"), path]


# ---- Kartenaufdeckung ---------------------------------------------------------------------------------------------------------------
func _viewshed(v: Dictionary) -> PackedByteArray:
	"""what one sees from a viewpoint: rays every 1.5°, 12 m steps, up to 1600 m (128 × 128 cells of 16 m)"""
	if _views.has(v.id):
		return _views[v.id]
	var b = B()
	var g := PackedByteArray()
	g.resize(128 * 128)
	var h0: float = float(v.y) + 1.7
	for k in range(240):
		var a := TAU * k / 240.0
		var d := Vector2(sin(a), -cos(a))
		var best := -INF
		var r := 8.0
		while r < 1600.0:
			var q: Vector2 = v.c + d * r
			if absf(q.x) > 1023.0 or absf(q.y) > 1023.0:
				break
			var t: float = (b.H(q.x, q.y) - h0) / r
			if t >= best - 0.004 or r < 60.0:
				g[int((q.y + 1024.0) / 16.0) * 128 + int((q.x + 1024.0) / 16.0)] = 1
			best = maxf(best, t)
			r += 12.0
	_views[v.id] = g
	return g


func reveal_update() -> void:
	var b = B()
	if not bool(st["reveal"]):
		s.data.erase("map_fog")
		return
	var t0 := Time.get_ticks_msec()
	var g := PackedByteArray()
	g.resize(128 * 128)
	var circles := [[b.spot_xz, 300.0]]                      # around the sleeping spot (as «visited»)
	for pl in b.all_places():
		if str(pl[0]) in m.bt_visited:
			circles.append([Vector2(pl[1], pl[2]), 120.0])
	for c in circles:
		var cc: Vector2 = c[0]
		var rr: float = c[1]
		for j in range(maxi(0, int((cc.y - rr + 1024.0) / 16.0)), mini(128, int((cc.y + rr + 1024.0) / 16.0) + 1)):
			for i in range(maxi(0, int((cc.x - rr + 1024.0) / 16.0)), mini(128, int((cc.x + rr + 1024.0) / 16.0) + 1)):
				if Vector2(-1024.0 + i * 16.0 + 8.0, -1024.0 + j * 16.0 + 8.0).distance_to(cc) < rr:
					g[j * 128 + i] = 1
	for v in vps:
		if v.id in st["seen"]:
			var vs := _viewshed(v)
			for k in range(g.size()):
				g[k] = g[k] | vs[k]
	var img := Image.create(128, 128, false, Image.FORMAT_RGBA8)
	var veil := Color(0.2, 0.24, 0.22, 0.78)                    # not yet seen: dark (contours shine through a little)
	var n := 0
	for j in range(128):
		for i in range(128):
			if g[j * 128 + i] == 0:
				img.set_pixel(i, j, veil)
			else:
				n += 1
	var px := func(u: float, w: float): return b.W(Vector3(-1024.0 + u * 16.0, 0, -1024.0 + w * 16.0))
	s.data["map_fog"] = [ImageTexture.create_from_image(img), px.call(0.0, 0.0), px.call(128.0, 0.0), px.call(0.0, 128.0), 128.0]
	info["map_revealed_pct"] = snappedf(100.0 * n / 16384.0, 0.1)
	info["map_reveal_ms"] = Time.get_ticks_msec() - t0


# ---- Stimmungen ---------------------------------------------------------------------------------------------------------------
func _moods_frame(_dt: float) -> void:
	"""absolute values (main._update_sky resets the sun every 0.5 s, before the scene animations)"""
	var on := bool(st["moods"])
	var el: float = m.sun_el()
	var hr: float = m.hour()
	var cl: float = m.clouds()
	var k := 0.0
	var col := Color(1, 1, 1)
	if on and el > -5.0 and el < 7.0 and m.weather in ["clear", "cloudy"]:
		k = clampf(1.0 - absf(el - 1.0) / 6.0, 0.0, 1.0) * (1.0 - 0.8 * cl)
		col = Color(1.0, 0.5, 0.6) if hr < 12.0 else Color(1.0, 0.4, 0.18)     # alpenglow (pink) / evening red
		var dusk: float = maxf(0.0, 1.0 - absf(el - 2.0) / 10.0)
		var base := Color(1.0, 0.95, 0.88).lerp(Color(1.0, 0.6, 0.35), dusk)
		m.sun.light_color = base.lerp(col, k * 0.8)
		if el < 0.0 and el > -4.5 and hr < 12.0:
			m.sun.light_energy = maxf(m.sun.light_energy, 0.12 * k)           # the light on the high peaks before sunrise
	_mood["glow"] = snappedf(k, 0.01)
	# long shadows in the evening at a viewpoint (not Lite)
	var want_long := on and not lite and k > 0.3 and hr > 12.0 and not _obs.is_empty()
	if want_long and _shadow0 < 0.0:
		_shadow0 = m.sun.directional_shadow_max_distance
		m.sun.directional_shadow_max_distance = 320.0
	elif not want_long and _shadow0 > 0.0:
		m.sun.directional_shadow_max_distance = _shadow0
		_shadow0 = -1.0
	# the Milky Way: a clear, dark night, a wide sky (sky.gdshader «milky»)
	var mk := 0.0
	if on and not lite and m.weather == "clear":
		var b = B()
		var sky_k: float = 0.9 if (not _obs.is_empty() and _obs.who != "spot") else float(b.rating.get("stars", 0.5))
		mk = clampf((-el - 10.0) / 6.0, 0.0, 1.0) * smoothstep(0.4, 0.8, sky_k) * (1.0 - 0.7 * float(m.moon))
	if absf(mk - _milky) > 0.01 and m.sky_mat != null:
		_milky = mk
		m.sky_mat.set_shader_parameter("milky", mk)


func _moods_log() -> void:
	"""a mood seen at a viewpoint (or at the sleeping spot with a view): discovery, night log (morning: Aussicht), badges"""
	var b = B()
	var el: float = m.sun_el()
	var hr: float = m.hour()
	var good: bool = not _obs.is_empty() or float(b.rating.get("view", 0.0)) > 0.55
	if not good or not bool(st["moods"]):
		return
	var day := Time.get_date_string_from_system() + ("m" if hr < 12.0 else "a")
	var seen := []
	if m.weather in ["clear", "cloudy"] and el > -4.5 and el < 3.0:
		seen.append("alpengluehen" if hr < 12.0 else "abendrot")
	if m.env.fog_height_density > 0.005:
		var oy: float = (b.V(_obs.pos) if not _obs.is_empty() else b.V(m.head.global_position)).y
		if oy > b.V(Vector3(0, m.env.fog_height, 0)).y + 25.0:
			seen.append("nebelmeer")
	if _milky > 0.5:
		seen.append("milchstrasse")
	for md in seen:
		var key: String = md + day
		if _mood.has(key):
			continue
		_mood[key] = true
		b.night_log.append({"k": "mood_" + md, "t": hr, "text": {"alpengluehen": "Alpenglühen", "abendrot": "Abendrot", "nebelmeer": "Nebelmeer von oben", "milchstrasse": "Milchstrasse"}[md]})
		if not _obs.is_empty():
			if not md in st["mood_seen"]:
				st["mood_seen"].append(md)
				save_state()
			_found("berg.aussicht.stimmung." + md, "view")
			if md == "nebelmeer":
				badge("nebelmeer")
			if md == "alpengluehen" and str(_obs.vp.kind) in SUMMITS and el > -1.5:
				badge("sonnenaufgang_grat")


func morning_adjust() -> Array:
	"""bergtal.morning(): [Sicherheit, Aussicht, Ruhe, Zeilen] dazu"""
	var b = B()
	var add := [0, 0, 0, []]
	if not _spot_vp().is_empty():
		add[1] += 1
		add[3].append("Aussichtspunkt")
	if b.night_log.any(func(e): return str(e["k"]).begins_with("mood_")):
		add[1] += 1
	if b.night_log.any(func(e): return e["k"] == "cold"):
		add[0] -= 1
		add[2] -= 1
	if b.night_log.filter(func(e): return e["k"] == "gust").size() >= 2:
		add[2] -= 1
	if b.night_log.any(func(e): return e["k"] == "warn"):
		add[3].append("Wetter früh gesehen")
	return add


# ---- Gipfel-Schlafplatz: Wind und Kälte -----------------------------------------------------------------------------------------
static func wind_chill(t_c: float, v_kmh: float) -> float:
	"""gefühlte Temperatur (JAG/TI-Formel, Environment Canada / NWS 2001; gilt ≤ 10 °C und ≥ 4,8 km/h)"""
	if t_c > 10.0 or v_kmh < 4.8:
		return t_c
	var p := pow(v_kmh, 0.16)
	return 13.12 + 0.6215 * t_c - 11.37 * p + 0.3965 * t_c * p


func _summit_risk() -> void:
	var b = B()
	var r: Dictionary = b.rating
	var alt := float(r.get("alt_m", 1500))
	var lapse: float = -(alt - b.ALT0) * 0.0065                 # 0,65 K pro 100 m (ICAO-Standardatmosphäre, ISO 2533)
	var night_c: float = float(m.ambient) - 4.0 + lapse + float(r.get("cold_c", 0.0))   # (−4: die klare Nacht kühlt ab)
	var summit := _summit_spot() or float(r.get("lightning", 0.0)) > 0.6
	var wind := float(m.wind)
	if summit:
		wind = maxf(wind, 22.0 + 35.0 * float(r.get("wind", 0.5)))   # Gipfel/Grat: kaum Schutz, nachts kein Talwind-Schutz
		if wind > m.wind + 0.5:
			if st.get("wind0") == null:
				st["wind0"] = float(m.wind)
				save_state()
			m.wind = wind
	var felt := wind_chill(night_c, wind * (1.0 - b._shelter_k() * 0.6))
	var comfort := 10.0 if str(m.get("bt_bag")) != "winter" else -8.0   # Komfortwert typisch (ISO 23537): Sommer ≈ +10 °C, Winter ≈ −8 °C
	var cold := summit and felt < comfort - 4.0
	info["summit"] = {"summit": summit, "night_air_c": snappedf(night_c, 0.1), "lapse_c": snappedf(lapse, 0.1), "wind_kmh": snappedf(wind, 0.1),
			"felt_c": snappedf(felt, 0.1), "bag_comfort_c": comfort, "too_cold": cold}
	var ex: Dictionary = s.data.get("exposure", {})
	ex.merge({"summit": summit, "night_air_c": snappedf(night_c, 0.1), "felt_c": snappedf(felt, 0.1), "too_cold": cold}, true)
	m.set_meta("platz_exposure", ex)
	if summit:
		var tx := "%s %d km/h, %s %d °C" % [T.t("Gipfel-Schlafplatz: schöne Aussicht, aber viel Wind –"), int(wind), T.t("nachts gefühlt"), int(round(felt))]
		if cold:
			tx += " – " + T.t("zu kalt für den Sommerschlafsack: Winterschlafsack, Zelt und Windschutzmauer!")
		var notes: Array = r.get("notes", [])
		if not notes.has(tx):
			notes.append(tx)
		m.start_info = tx


func _summit_night() -> void:
	var b = B()
	var sm: Dictionary = info.get("summit", {})
	if not bool(sm.get("summit", false)) or not m.is_dark():
		return
	if bool(sm.get("too_cold", false)) and not b.night_log.any(func(e): return e["k"] == "cold"):
		b.night_log.append({"k": "cold", "t": m.hour(), "text": "Kalte Nacht am Gipfel"})
	_gust_t -= 0.25
	if _gust_t <= 0.0:
		_gust_t = randf_range(40.0, 110.0)
		b.night_log.append({"k": "gust", "t": m.hour(), "text": "Sturmböe"})
		m.add_sound(-12.0, m.head.global_position + Vector3(3, 1, 0), 2.5)     # the wind tears at the tent (≈ 70 dB at 1 m)


# ---- Wetter früh sehen ------------------------------------------------------------------------------------------------------------
func plan_weather(k: String, lead := -1.0) -> Dictionary:
	"""Gewitter / Nebel kommt: zuerst am Horizont (Wolkenturm im Westen bzw. Nebel steigt im unteren Tal), dann am Schlafplatz.
	Vorlauf ≈ 45 Minuten Uhrzeit (Gewitterzellen ziehen mit 20–40 km/h), im Zeitraffer gekürzt: 90 … 360 s"""
	var b = B()
	if not _plan.is_empty():
		_plan_clear()
	if lead < 0.0:
		lead = clampf(2700.0 / maxf(1.0, float(m.speed)), 90.0, 360.0)
	_plan = {"k": k, "t0": m.now(), "t1": m.now() + lead, "warned": false, "nodes": []}
	if k == "storm":
		var mt := StandardMaterial3D.new()
		mt.albedo_color = Color(0.3, 0.31, 0.35)
		mt.roughness = 1.0
		mt.emission_enabled = true
		mt.emission = Color(0.8, 0.85, 1.0)
		mt.emission_energy_multiplier = 0.0
		_plan["mat"] = mt
		var az0 := deg_to_rad(250.0 + randf_range(-20.0, 20.0))     # the weather comes from W / SW
		for i in range(4 if lite else 7):
			var az := az0 + randf_range(-0.18, 0.18)
			var r := randf_range(4300.0, 5200.0)
			var mi := MeshInstance3D.new()
			var sp := SphereMesh.new()
			sp.radius = 1.0
			sp.height = 2.0
			sp.radial_segments = 16
			sp.rings = 8
			mi.mesh = sp
			mi.material_override = mt
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.position = Vector3(sin(az) * r, randf_range(1300.0, 2000.0), -cos(az) * r)
			mi.set_meta("sc", Vector3(randf_range(500, 800), randf_range(900, 1500), randf_range(500, 800)))
			mi.scale = Vector3.ONE * 10.0
			b.tal.add_child(mi)
			_plan["nodes"].append(mi)
	return {"ok": true, "k": k, "lead_s": snappedf(lead, 0.1)}


func _plan_frame(dt: float) -> void:
	if _plan.is_empty():
		return
	var f: float = clampf((m.now() - float(_plan.t0)) / maxf(1.0, float(_plan.t1) - float(_plan.t0)), 0.0, 1.0)
	if _plan.k == "storm":
		for n in _plan.nodes:
			if is_instance_valid(n):
				n.scale = (n.get_meta("sc") as Vector3) * (0.35 + 0.65 * f)
		var mt: StandardMaterial3D = _plan.mat
		mt.emission_energy_multiplier = maxf(0.0, mt.emission_energy_multiplier - dt * 6.0)
		if randf() < dt * (0.1 + 0.5 * f):
			mt.emission_energy_multiplier = 1.5                  # far lightning in the cloud (no thunder: too far)
	else:
		var b = B()                                              # fog rises out of the lower valley (height fog)
		m.env.fog_height = b.W(Vector3(0, lerpf(-40.0, 70.0, f), 0)).y
		m.env.fog_height_density = maxf(m.env.fog_height_density, 0.004 + 0.03 * f)


func _plan_slow() -> void:
	if _plan.is_empty():
		return
	var b = B()
	var eta: float = float(_plan.t1) - m.now()
	if not _plan.warned and not _obs.is_empty():
		_plan.warned = true
		var mins := maxi(1, int(round(eta * maxf(1.0, float(m.speed)) / 60.0)))
		var what := T.t("Gewitterwolken im Westen") if _plan.k == "storm" else T.t("Nebel steigt aus dem Tal")
		var tx := "%s %s – %s %d %s" % [T.t("Vom Aussichtspunkt siehst du:"), what, T.t("in etwa"), mins, T.t("Minuten am Schlafplatz.")]
		if _plan.k == "storm" and float(b.rating.get("lightning", 0.0)) > 0.4:
			tx += " " + T.t("Der Schlafplatz ist ausgesetzt – jetzt runter vom Grat!")
		m.start_info = tx
		m._say(T.t("Wetter kommt!"), m.head.global_position + Vector3(0, 1.6, 0), Color("#ffb347"), m.HELPER_LAYER)
		b.night_log.append({"k": "warn", "t": m.hour(), "text": "Wetter früh gesehen"})
	s.data["bt_forecast"] = {"k": _plan.k, "eta_s": int(eta), "warned": _plan.warned}
	if eta <= 0.0:
		var k: String = _plan.k
		_plan_clear()
		if k == "storm":
			b.storm()
		else:
			b.fog_roll()


func _plan_clear() -> void:
	for n in _plan.get("nodes", []):
		if is_instance_valid(n):
			n.queue_free()
	_plan = {}
	s.data.erase("bt_forecast")


# ---- MoveEye-Reichweite (Kegel auf dem Gelände) -------------------------------------------------------------------------------------
func ranges() -> Dictionary:
	"""bis wohin MoveEye eine stehende Person erkennt (Standardwerte von MoveEye, siehe oben)"""
	var out := {}
	var amin := MIN_AREA * (1.0 - SENS / 200.0)
	for i in range(2):
		var f: float = float(PROC_W[i]) / 2.0 / tan(deg_to_rad(float(m.CAM_FOV[i]) / 2.0))    # px per radian in the working picture
		var a: float = amin * pow(float(PROC_W[i]) / 480.0, 2.0)
		out["motion_%d" % i] = snappedf(sqrt(PERSON.x * PERSON.y * f * f / a), 0.1)
		out["ai_%d" % i] = snappedf(PERSON.y * f / AI_MIN_PX, 0.1)
	var ft := (float(m.TH_W) / 2.0) / tan(deg_to_rad(float(m.TH_FOV) / 2.0))
	out["thermal"] = snappedf(sqrt(PERSON.x * PERSON.y * ft * ft / (TH_MIN_PCT / 100.0 * m.TH_W * m.TH_H)), 0.1)
	out["ir"] = float(m.ir_range)
	return out


func _cone_update() -> void:
	var yaw: float = m.cams[0].global_rotation.y
	var dark: bool = m.is_dark()
	var key := yaw + (100.0 if dark else 0.0)
	if absf(key - _cone_yaw) < deg_to_rad(2.0) and _cone != null and is_instance_valid(_cone):
		return
	_cone_yaw = key
	var rg := ranges()
	var st2 := SurfaceTool.new()
	st2.begin(Mesh.PRIMITIVE_TRIANGLES)
	var area := 0.0
	var fans := [[m.cams[0], float(m.CAM_FOV[0]), float(rg["motion_0"]), Color(1.0, 0.45, 0.1, 0.42)],
			[m.cams[0], float(m.CAM_FOV[0]), minf(float(rg["ai_0"]), float(rg["ir"])) if dark else float(rg["ai_0"]), Color(1.0, 0.75, 0.2, 0.22)],
			[m.cams[1], float(m.CAM_FOV[1]), float(rg["ai_1"]), Color(0.4, 0.7, 1.0, 0.2)],
			[m.cams[2], float(m.TH_FOV), float(rg["thermal"]), Color(1.0, 0.2, 0.3, 0.35)]]
	for fan in fans:
		area += _fan(st2, fan[0], fan[1], fan[2], fan[3])
	if _cone == null or not is_instance_valid(_cone):
		_cone = MeshInstance3D.new()
		var mt := StandardMaterial3D.new()
		mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mt.vertex_color_use_as_albedo = true
		mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mt.cull_mode = BaseMaterial3D.CULL_DISABLED
		mt.no_depth_test = false
		mt.render_priority = 2
		_cone.material_override = mt
		_cone.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_cone.layers = m.HELPER_LAYER
		s.root.add_child(_cone)
	_cone.mesh = st2.commit()
	for l in _cone_labels:
		if is_instance_valid(l):
			l.queue_free()
	_cone_labels.clear()
	var fwd: Vector3 = -m.cams[0].global_transform.basis.z
	fwd.y = 0.0
	fwd = fwd.normalized()
	var items := [[float(rg["motion_0"]), "Bewegung: Person bis %d m"], [minf(float(rg["ai_0"]), float(rg["ir"])) if dark else float(rg["ai_0"]), "KI-Person bis %d m" if not dark else "Infrarot: bis %d m"],
			[float(rg["thermal"]), "Wärmebild: Person bis %d m"]]
	for i in range(items.size()):
		var p: Vector3 = fwd * float(items[i][0]) + fwd.cross(Vector3.UP) * (i - 1) * 2.0
		var l := Label3D.new()
		l.text = T.t(str(items[i][1])) % int(items[i][0])
		l.position = Vector3(p.x, m.ground_y(p.x, p.z) + 1.2, p.z)
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.font_size = 40
		l.pixel_size = 0.01
		l.outline_size = 8
		l.layers = m.HELPER_LAYER
		s.root.add_child(l)
		_cone_labels.append(l)
	info["cone"] = {"ranges_m": rg, "visible_m2": int(area), "dark": dark}


func _fan(st2: SurfaceTool, cam: Camera3D, fov: float, reach: float, col: Color) -> float:
	"""a fan on the ground from the head: only where the ground is seen (terrain in between hides it)"""
	var o: Vector3 = m.head.global_position
	var f: Vector3 = -cam.global_transform.basis.z
	var a0 := atan2(f.x, -f.z)
	var nr := int(fov / 3.0) + 2
	var rows := []
	var rs := []
	var r := 1.0
	while r <= reach:
		rs.append(r)
		r += 1.0 if r < 20.0 else 2.5
	rs.append(reach)
	for i in range(nr):
		var a := a0 + deg_to_rad(-fov / 2.0 + fov * i / (nr - 1))
		var d := Vector2(sin(a), -cos(a))
		var best := -INF
		var row := []
		for rr in rs:
			var x: float = d.x * rr
			var z: float = d.y * rr
			var gy: float = m.ground_y(x, z)
			var t: float = (gy - o.y) / rr
			row.append([Vector3(x, gy + 0.25, z), t >= best - 0.002])
			best = maxf(best, t)
		rows.append(row)
	var area := 0.0
	for i in range(nr - 1):
		for j in range(rs.size() - 1):
			var a: Array = rows[i][j]
			var bq: Array = rows[i + 1][j]
			var c: Array = rows[i][j + 1]
			var dq: Array = rows[i + 1][j + 1]
			if a[1] and bq[1] and c[1] and dq[1]:
				for v in [a[0], c[0], bq[0], bq[0], c[0], dq[0]]:
					st2.set_color(col)
					st2.add_vertex(v)
				area += (float(rs[j + 1]) - float(rs[j])) * float(rs[j]) * deg_to_rad(fov / (nr - 1))
	return area


func apply_settings() -> void:
	if not bool(st["cone"]):
		if _cone != null and is_instance_valid(_cone):
			_cone.queue_free()
		_cone = null
		for l in _cone_labels:
			if is_instance_valid(l):
				l.queue_free()
		_cone_labels.clear()
		_cone_yaw = 999.0
		info.erase("cone")
	reveal_update()
	if not bool(st["moods"]) and m.sky_mat != null:
		m.sky_mat.set_shader_parameter("milky", 0.0)
		_milky = 0.0


# ---- Sichtlinie ------------------------------------------------------------------------------------------------------------------------
func _los_v(a: Vector3, c: Vector3) -> bool:
	"""valley coordinates: nothing of the ground in between"""
	var b = B()
	var d := a.distance_to(c)
	var n := int(d / 10.0) + 2
	for i in range(1, n):
		var p := a.lerp(c, float(i) / n)
		if b.H(p.x, p.z) > p.y + 0.3:
			return false
	return true


func _los_w(a: Vector3, c: Vector3) -> bool:
	var b = B()
	return _los_v(b.V(a), b.V(c))


# ---- Steuerung ------------------------------------------------------------------------------------------------------------------------
func control(d: Dictionary) -> Dictionary:
	var b = B()
	var what := str(d.get("what", "info"))
	match what:
		"scope":
			return scope("fernrohr")
		"observe":
			return observe()
		"pano":
			var sv := _spot_vp()
			var look := rad_to_deg(-(m.cams[0].global_rotation.y - b.tal.rotation.y))
			var id: String = sv.id if not sv.is_empty() else "platz_%s" % str(b.spot)
			return panorama(m.head.global_position, look, true, id)
		"weather":
			var k := str(d.get("value", "storm"))
			return plan_weather("fog" if k == "fog" else "storm", float(d.get("lead", -1.0)))
		"cone", "moods", "reveal":
			st[what] = bool(d.get("value", true))
			save_state()
			apply_settings()
			return {"ok": true, what: st[what]}
		"badges":
			var lines := []
			for bd in BADGES:
				lines.append(("✓ " if st["badges"].has(bd[0]) else "· ") + T.t(str(bd[1])).trim_prefix(T.t("Abzeichen: ")))
			var txt := "%s %d %s %d · %s" % [T.t("Aussichtspunkte"), st["seen"].size(), T.t("von"), vps.size(), " · ".join(lines)]
			m.start_info = txt
			return {"ok": true, "text": txt, "badges": st["badges"], "seen": st["seen"]}
		"visit":                                             # tests: the view flies to a viewpoint («spot»: above the sleeping spot)
			if str(d.get("value", "")) == "spot":
				if m.has_method("_to_free_view"):
					m._to_free_view()
				var hp: Vector3 = m.head.global_position
				m.view_cam.global_position = hp + Vector3(0, float(d.get("up", 30.0)), float(d.get("back", 22.0)))
				m.view_cam.look_at(hp + Vector3(0, 0, -10.0), Vector3.UP)
				return {"ok": true}
			var v := _vp(str(d.get("value", "")))
			if v.is_empty():
				return {"ok": false, "error": "unknown viewpoint", "ids": vps.map(func(x): return x.id)}
			if m.fly_tw != null:
				m.fly_tw.kill()
			if m.has_method("_to_free_view"):
				m._to_free_view()
			var eye: Vector3 = b.WG(v.c.x, v.c.y, 1.7)
			var az := deg_to_rad(float(v.look))
			m.view_cam.global_position = eye
			m.view_cam.look_at(eye + b.tal.basis * Vector3(sin(az), -0.12, -cos(az)), Vector3.UP)
			return {"ok": true, "vp": v.id, "eye": eye}
		"look":                                              # tests: turn the view (degrees, 0 = north of the valley)
			var az2 := deg_to_rad(float(d.get("value", 0.0)))
			var e2: Vector3 = m.view_cam.global_position
			m.view_cam.look_at(e2 + b.tal.basis * Vector3(sin(az2), float(d.get("down", -0.05)), -cos(az2)), Vector3.UP)
			return {"ok": true}
		"map":                                               # tests: the overview map big and wide (shows the uncovered parts)
			if m.minimap != null:
				m.set_map(true)
				m.minimap.span = float(d.get("value", 1800.0))
				m.minimap.size_px = float(d.get("px", 420.0))
				m.minimap._apply_size()
			return {"ok": true}
		"reset":
			st.clear()
			DirAccess.remove_absolute(SAVE)
			state()
			reveal_update()
			return {"ok": true}
	return {"ok": true, "aussicht": info_dict(), "ranges": ranges()}
