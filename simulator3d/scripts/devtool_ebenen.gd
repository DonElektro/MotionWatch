extends Node
## Entwicklertool 2 «Regler + Ebenen» (Daniel 31.10.2026): zwei Abschnitte im Fenster «Mehr → Entwickler» (devtool.gd).
## Eigene Datei, damit devtool.gd (Teil 1, Teil 3 «Notizen») nur zwei Einhänge-Zeilen braucht.
##
## Schnellregler: Uhrzeit, Wetter, Jahreszeit, Grafik-Modus. KEINE zweite Logik: jeder Regler ist ein Spiegel des normalen
##   Reglers im Bedienfeld (main.controls, gleiche id, gleiche Texte und Auswahl) und setzt über main.control_set(id, v) –
##   dasselbe wie der Steuerbefehl {"action": "set"}; das Bedienfeld zieht über _sync_ui() mit, und umgekehrt liest dieser
##   Abschnitt die Werte 2 × pro Sekunde zurück. Grafik «Hoch» (und zurück von «Hoch») startet den Simulator neu (grafik_hoch.gd).
##
## Ebenen (nur für den Bediener: main.HELPER_LAYER, die Kameras von MoveEye sehen sie nie; Linien ohne Licht und Schatten):
##   fov       Sichtfeld von MoveEye: Kegel der Kopfkamera (blau, 66° × 39°) bis zum Boden (höchstens 30 m) und getrennt die
##             Weitwinkel-Kamera (gelb, 102° × 67° Fischauge, weitwinkel.gd), wenn sie eingebaut ist
##   paths     Wege: Bergtal-Wanderwege und Strasse (bergtal.gd TRAILS / ROAD), Ferienpark-Gassen und Waldweg (ferienpark.gd),
##             die Wege des Abenteuers (bergtal_abenteuer_daten.gd CHAPTERS) und die Gehwege der Figuren (Actor target + route)
##   spawns    Startpunkte: wo jede Figur / jedes Tier erschienen ist (die letzten 60; grün Mensch, orange Tier, grau Fahrzeug)
##             und, ausserhalb Bergtal / Ferienpark, die zwei Linien, auf denen main.spawn() zufällige Besucher starten lässt
##   triggers  Auslöser: Bergtal-Erlebnisse und Ferienpark-Vignetten (Ring = ACTIVE_R 60 m: ab da bewegt sich die Szene),
##             Abenteuer-Punkte (Start, Hinweis, Gabelung, Karte lesen, Lager pro Kapitel), «PIR Zelt» (3 m um main.obj.pir);
##             Horror «Das Hospiz» (Hospiz, Hütte, 9 m-Ring der Gestalt) NUR wenn main.horror.unlocked
##   lights    Lampen (OmniLight3D / SpotLight3D im Baum): Punkt + Ring mit der Reichweite (Spot: Linie in Leuchtrichtung);
##             aus = grau
## Lite (Quality.lite()): weniger Strahlen, keine Schrift, nur nahe Linien, seltener neu gezeichnet.
## Auf der Draufsicht-Karte (DevMap): Wege, Auslöser, Sichtfeld, Startpunkte und Lampen (die drei letzten nur, wenn die Welt
## geladen ist).
## Steuerbefehl (über devtool.control): {"action": "dev", "do": "layer", "name": fov|paths|spawns|triggers|lights|all, "on": bool}
##   (ohne "on" = umschalten, ohne "name" = Liste) · {"do": "set", "time": 22, "weather": "rain", "season": "1", "quality": "lite"}
##   (oder "what"/"key" + "value"; mehrere auf einmal erlaubt) · {"do": "regler"} = die Werte.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Quality = preload("res://scripts/quality.gd")
const Bt = preload("res://scripts/bergtal.gd")
const Fp = preload("res://scripts/ferienpark.gd")
const AD = preload("res://scripts/bergtal_abenteuer_daten.gd")
const ErlBase = preload("res://scripts/bergtal_erleben_base.gd")
const Erl = preload("res://scripts/erlebniswelt.gd")
const WW = preload("res://scripts/weitwinkel.gd")
const Hoch = preload("res://scripts/grafik_hoch.gd")

const LAYERS := [["fov", "Sichtfeld von MoveEye (blau Kopfkamera, gelb Weitwinkel)"],
		["paths", "Wege und Gehwege der Figuren"],
		["spawns", "Startpunkte von Figuren und Tieren"],
		["triggers", "Auslöser (Erlebnisse, Abenteuer, PIR Zelt)"],
		["lights", "Lichtquellen (Lampen mit Reichweite)"]]
const ALIAS := {"sichtfeld": "fov", "sicht": "fov", "wege": "paths", "pfade": "paths", "path": "paths", "start": "spawns",
		"startpunkte": "spawns", "spawn": "spawns", "ausloeser": "triggers", "auslöser": "triggers", "trigger": "triggers",
		"licht": "lights", "lampen": "lights", "light": "lights"}
# quick control -> id of the normal control in the panel (main.controls)
const QUICK := [["time", "hour"], ["weather", "weather"], ["season", "season"], ["quality", "grafik_mode"]]
const SEASON_WORDS := {"winter": "1", "fruehling": "4", "frühling": "4", "spring": "4", "sommer": "7", "summer": "7",
		"herbst": "10", "autumn": "10", "fall": "10", "heute": "today"}
const HOURS := [["Morgen", 7.0], ["Mittag", 12.0], ["Abend", 19.0], ["Nacht", 23.0]]

const C_HEAD := Color(0.25, 0.6, 1.0, 0.9)
const C_WIDE := Color(1.0, 0.82, 0.25, 0.85)
const C_TRAIL := Color(0.92, 0.92, 0.92, 0.75)
const C_ROAD := Color(0.95, 0.35, 0.3, 0.8)
const C_STORY := Color(0.75, 0.5, 1.0, 0.85)
const C_WALK := Color(0.3, 0.95, 0.95, 0.9)
const C_TRIG := Color(1.0, 0.45, 0.75, 0.85)
const C_ADV := Color(0.75, 0.5, 1.0, 0.95)
const C_PIR := Color(0.3, 0.9, 0.45, 0.9)
const C_HORROR := Color(0.9, 0.15, 0.15, 0.95)
const C_LAMP := Color(1.0, 0.85, 0.4, 0.85)
const C_LAMP_OFF := Color(0.6, 0.6, 0.6, 0.45)
const C_PERSON := Color(0.3, 0.9, 0.45, 0.95)
const C_ANIMAL := Color(1.0, 0.6, 0.25, 0.95)
const C_CAR := Color(0.7, 0.72, 0.75, 0.95)
const VEHICLES := ["car", "moto", "van", "camper", "tractor", "car_park"]

var main
var dev
var on := {"fov": false, "paths": false, "spawns": false, "triggers": false, "lights": false}
var _im_slow: ImmediateMesh
var _im_fast: ImmediateMesh
var _mi_slow: MeshInstance3D
var _mi_fast: MeshInstance3D
var _labels: Array = []               # Label3D pool
var _t_slow := 0.0
var _t_fast := 0.0
var _t_ui := 0.0
var _key := ""                        # what the cached lines were made for
var _cache_paths: Array = []          # [PackedVector3Array (scene, pairs), PackedColorArray]
var _cache_trig: Array = []
var _cache_names: Array = []          # [Vector3, text, Color] for labels
var _starts := {}                     # instance id -> true
var _start_list: Array = []           # [Vector3 scene position, Color, Vector2 world position or null]
var _lights: Array = []               # [Vector3, range, on, Vector3 dir (spot) or ZERO, angle]
var fov_world: Array = []             # [PackedVector2Array head, PackedVector2Array wide] in world coordinates (the map)
var _rows := {}                       # quick id -> [widget, value label]
var _chk := {}                        # layer -> CheckBox
var _syncing := false
var stats := {"lines": 0, "us": 0}


static func _lite() -> bool:
	return Quality.lite()


static func layer_id(n: String) -> String:
	var k := n.strip_edges().to_lower()
	return str(ALIAS.get(k, k))


func any_on() -> bool:
	for k in on:
		if on[k]:
			return true
	return false


# =============================================================================================================================
# the section in the window (devtool._build: v.add_child(ebenen.section()))
# =============================================================================================================================
func section() -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(left)
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(right)
	var q := UI.sub_fold(left, T.t("Schnellregler"), false)
	_build_quick(q)
	var l := UI.sub_fold(right, T.t("Ebenen in der Ansicht"), false)
	for e in LAYERS:
		var c := CheckBox.new()
		c.text = T.t(str(e[1]))
		c.add_theme_font_size_override("font_size", 13)
		var k := str(e[0])
		c.toggled.connect(func(x):
			if not _syncing:
				set_layer(k, x))
		l.add_child(c)
		_chk[k] = c
	l.add_child(UI.small(T.t("Nur im Fenster sichtbar, nie im Bild von MoveEye. Horror-Auslöser nur, wenn «Das Hospiz» entsperrt ist.")))
	for b in [q, l]:                                        # the window gets smaller again when a part is closed
		var hdr = (b.get_meta("wrap") as Control).get_child(1)
		if hdr is Button:
			(hdr as Button).pressed.connect(_shrink)
	return row


func _shrink() -> void:
	if dev != null and dev.panel != null:
		(dev.panel as Control).call_deferred("reset_size")
		var w = dev.panel.get_parent()
		if w is Control:
			(w as Control).call_deferred("reset_size")


func _ctrl(id: String) -> Dictionary:
	for c in main.controls:
		if c.id == id:
			return c
	return {}


func _build_quick(box: VBoxContainer) -> void:
	for qd in QUICK:
		var c: Dictionary = _ctrl(str(qd[1]))
		if c.is_empty():
			continue
		var cid := str(qd[1])
		var lab := Label.new()
		lab.text = T.t(str(c.label))
		lab.add_theme_font_size_override("font_size", 13)
		box.add_child(lab)
		if c.type == "slider":
			var h := HBoxContainer.new()
			h.add_theme_constant_override("separation", 6)
			box.add_child(h)
			var s := HSlider.new()
			s.min_value = float(c.extra.get("min", 0))
			s.max_value = float(c.extra.get("max", 1))
			s.step = float(c.extra.get("step", 0.01))
			s.custom_minimum_size = Vector2(150, 24)
			s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			var vl := UI.small("", UI.TXT)
			vl.custom_minimum_size = Vector2(46, 0)
			s.value_changed.connect(func(v):
				vl.text = _fmt(cid, v)
				if not _syncing:
					main.control_set(cid, v))
			h.add_child(s)
			h.add_child(vl)
			_rows[cid] = [s, vl]
			if cid == "hour":
				var hb := HBoxContainer.new()
				hb.add_theme_constant_override("separation", 4)
				box.add_child(hb)
				for hh in HOURS:
					var b := Button.new()
					b.text = T.t(str(hh[0]))
					b.add_theme_font_size_override("font_size", 12)
					b.tooltip_text = "%02d:00" % int(hh[1])
					var hv := float(hh[1])
					b.pressed.connect(func(): main.control_set("hour", hv))
					hb.add_child(b)
		else:
			var o := OptionButton.new()
			o.custom_minimum_size = Vector2(150, 30)
			o.clip_text = true
			for op in c.extra.get("options", []):
				o.add_item(T.t(str(op[1])))
				o.set_item_metadata(o.item_count - 1, str(op[0]))
			o.item_selected.connect(func(i):
				if not _syncing:
					main.control_set(cid, str(o.get_item_metadata(i)))
					if cid == "grafik_mode":
						_paint_ui())
			if c.extra.has("tip"):
				o.tooltip_text = T.t(str(c.extra["tip"]))
			box.add_child(o)
			_rows[cid] = [o, null]
			if cid == "grafik_mode":
				box.add_child(UI.small(T.t("«Hoch» (und zurück von «Hoch») startet den Simulator neu. Automatisch, Lite und Normal wirken sofort.")))
	box.add_child(UI.small(T.t("Gleiche Regler wie im Bedienfeld (Szene · Zeit, Wetter, System · Grafik) – beide bleiben gleich.")))
	_paint_ui()


func _fmt(cid: String, v: float) -> String:
	if cid == "hour":
		var m := int(round(v * 60.0))
		return "%02d:%02d" % [int(m / 60) % 24, m % 60]
	return str(v)


func _paint_ui() -> void:
	_syncing = true
	for cid in _rows:
		var c: Dictionary = _ctrl(cid)
		if c.is_empty() or c["get"] == null:
			continue
		var w = _rows[cid][0]
		var v = c["get"].call()
		if w is HSlider:
			if not (w as HSlider).has_focus():
				(w as HSlider).value = float(v)
			(_rows[cid][1] as Label).text = _fmt(cid, float(v))
		elif w is OptionButton:
			for i in (w as OptionButton).item_count:
				if str(w.get_item_metadata(i)) == str(v):
					(w as OptionButton).select(i)
	for k in _chk:
		(_chk[k] as CheckBox).set_pressed_no_signal(bool(on[k]))
	_syncing = false


# =============================================================================================================================
# switching
# =============================================================================================================================
func set_layer(k: String, v: bool) -> void:
	if not on.has(k):
		return
	on[k] = v
	_key = ""                                               # rebuild the cached lines
	_t_slow = 0.0
	_t_fast = 0.0
	if not any_on():
		_clear()
	_paint_ui()
	if dev != null and dev._map != null:
		dev._map.queue_redraw()


func _ensure_mesh() -> void:
	if _mi_slow != null and is_instance_valid(_mi_slow):
		return
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.vertex_color_use_as_albedo = true
	m.no_depth_test = true
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_im_slow = ImmediateMesh.new()
	_im_fast = ImmediateMesh.new()
	_mi_slow = MeshInstance3D.new()
	_mi_fast = MeshInstance3D.new()
	for p in [[_mi_slow, _im_slow, "DevEbenenSlow"], [_mi_fast, _im_fast, "DevEbenenFast"]]:
		var mi: MeshInstance3D = p[0]
		mi.name = str(p[2])
		mi.mesh = p[1]
		mi.layers = main.HELPER_LAYER
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.material_override = m
		mi.extra_cull_margin = 16384.0
		main.add_child(mi)


func _clear() -> void:
	if _im_slow != null:
		_im_slow.clear_surfaces()
		_im_fast.clear_surfaces()
	for l in _labels:
		(l as Label3D).visible = false
	fov_world = []


# =============================================================================================================================
# drawing in 3D
# =============================================================================================================================
func _process(dt: float) -> void:
	_t_ui -= dt
	if _t_ui <= 0.0:
		_t_ui = 0.5
		if dev != null and dev.shown and not _rows.is_empty():
			_paint_ui()                                     # the panel (or /control set) changed a value
	if not any_on() or main == null or main.view_cam == null:
		return
	_ensure_mesh()
	var lite := _lite()
	_t_fast -= dt
	if _t_fast <= 0.0:
		_t_fast = 0.3 if lite else 0.1
		_fast()
	_t_slow -= dt
	if _t_slow <= 0.0:
		_t_slow = 2.5 if lite else 1.0
		var t0 := Time.get_ticks_usec()
		_slow()
		stats["us"] = Time.get_ticks_usec() - t0


func _scene_of(w: Vector2) -> Vector3:
	"""world coordinates of the loaded world -> scene, on the ground"""
	var f = dev.frame()
	var p := Vector3(w.x, 0, w.y)
	if f != null:
		p = (f as Transform3D) * p
	p.y = main.ground_y(p.x, p.z)
	return p


func _world_key() -> String:
	var f = dev.frame()
	var o: Vector3 = (f as Transform3D).origin if f != null else Vector3(1e9, 0, 0)
	var hz = main.get("horror")
	var hu := hz != null and bool(hz.get("unlocked"))
	return "%s|%s|%.1f,%.1f|%s|%s|%s|%s|%s" % [main.scene, dev.loaded_world(), o.x, o.z, on["paths"], on["triggers"], hu, _lite(),
			str(main.obj.get("pir", Vector3.ZERO))]


func _line_on_ground(V: PackedVector3Array, C: PackedColorArray, pts: Array, col: Color, step: float, lift := 0.4) -> void:
	"""a polyline of world points (Vector2) along the ground, cut into pieces of «step» m"""
	for i in range(pts.size() - 1):
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var n := maxi(1, int(ceil(a.distance_to(b) / step)))
		var prev := _scene_of(a) + Vector3(0, lift, 0)
		for k in range(1, n + 1):
			var q := _scene_of(a.lerp(b, float(k) / float(n))) + Vector3(0, lift, 0)
			V.append(prev)
			V.append(q)
			C.append(col)
			C.append(col)
			prev = q


func _ring(V: PackedVector3Array, C: PackedColorArray, c: Vector3, r: float, col: Color, seg: int, follow := true) -> void:
	var prev := Vector3.ZERO
	for i in range(seg + 1):
		var t := TAU * float(i) / float(seg)
		var p := c + Vector3(cos(t) * r, 0, sin(t) * r)
		p.y = (main.ground_y(p.x, p.z) + 0.3) if follow else c.y
		if i > 0:
			V.append(prev)
			V.append(p)
			C.append(col)
			C.append(col)
		prev = p


func _post(V: PackedVector3Array, C: PackedColorArray, p: Vector3, h: float, col: Color) -> void:
	V.append(p)
	V.append(p + Vector3(0, h, 0))
	for d in [Vector3(0.6, 0, 0), Vector3(0, 0, 0.6)]:
		V.append(p - d + Vector3(0, 0.05, 0))
		V.append(p + d + Vector3(0, 0.05, 0))
	for i in 6:
		C.append(col)


func _rebuild_cache() -> void:
	var lite := _lite()
	var lw: String = dev.loaded_world()
	var V := PackedVector3Array()
	var C := PackedColorArray()
	_cache_names = []
	if on["paths"]:
		var stp := 25.0 if lite else 10.0
		if lw == "bergtal":
			for tr in Bt.TRAILS:
				_line_on_ground(V, C, tr[1], C_TRAIL, stp)
			_line_on_ground(V, C, Bt.ROAD, C_ROAD, stp)
			for ch in AD.CHAPTERS:
				for s in ch.get("stages", []):
					if s.has("walk"):
						_line_on_ground(V, C, s["walk"], C_STORY, stp, 0.7)
					elif s.has("fork"):
						for op in s["fork"]:
							_line_on_ground(V, C, op[1], C_STORY, stp, 0.7)
		elif lw == "ferienpark":
			for ln in Fp.LANES:
				_line_on_ground(V, C, [Vector2(float(ln[0]), float(ln[1])), Vector2(float(ln[0]), float(ln[2]))], C_TRAIL, stp)
			_line_on_ground(V, C, Fp.FOREST_PATH, C_TRAIL, stp)
			_line_on_ground(V, C, Fp.BRIDGE_PATH, C_TRAIL, stp)
	_cache_paths = [V, C]
	var V2 := PackedVector3Array()
	var C2 := PackedColorArray()
	if on["triggers"]:
		var seg := 16 if lite else 32
		if lw == "bergtal":
			for v in Bt.VIGNETTES:
				if absf(float(v[3])) < 0.01 and absf(float(v[4])) < 0.01:
					continue                               # «at MoveEye»: no own place
				var p := _scene_of(Vector2(float(v[3]), float(v[4])))
				_ring(V2, C2, p, ErlBase.ACTIVE_R, Color(C_TRIG, 0.45), seg)
				_ring(V2, C2, p, maxf(2.0, float(v[5])), C_TRIG, 12)
				_cache_names.append([p + Vector3(0, 2.5, 0), T.t(str(v[2])), C_TRIG])
			for ch in AD.CHAPTERS:
				for e in _adventure_points(ch):
					var p2 := _scene_of(e[0])
					_post(V2, C2, p2, 4.0, C_ADV)
					_ring(V2, C2, p2, 5.0, C_ADV, 12)
					_cache_names.append([p2 + Vector3(0, 4.5, 0), e[1], C_ADV])
			var hz = main.get("horror")
			if hz != null and bool(hz.get("unlocked")):
				var hp := _scene_of(Bt.HOSPICE)
				_post(V2, C2, hp, 8.0, C_HORROR)
				_ring(V2, C2, hp, 15.0, C_HORROR, seg)
				_cache_names.append([hp + Vector3(0, 8.5, 0), T.t("Horror: Hospiz"), C_HORROR])
				var hut = hz.get("_hut")
				if hut is Node3D and is_instance_valid(hut) and (hut as Node3D).is_inside_tree():
					var up: Vector3 = (hut as Node3D).global_position
					_post(V2, C2, up, 5.0, C_HORROR)
					_ring(V2, C2, up, 4.0, C_HORROR, 12)
					_cache_names.append([up + Vector3(0, 5.5, 0), T.t("Horror: Hütte (Tür, Licht)"), C_HORROR])
		elif lw == "ferienpark":
			for v in Fp.ERLEBNIS:
				var p3 := _scene_of(Vector2(float(v[3]), float(v[4])))
				_ring(V2, C2, p3, Erl.ACTIVE_R, Color(C_TRIG, 0.45), seg)
				_ring(V2, C2, p3, maxf(2.0, float(v[5])), C_TRIG, 12)
				_cache_names.append([p3 + Vector3(0, 2.5, 0), T.t(str(v[2])), C_TRIG])
		var pir = main.obj.get("pir", Vector3.ZERO)
		if pir is Vector3 and (pir as Vector3) != Vector3.ZERO:
			var pp := Vector3(pir.x, main.ground_y(pir.x, pir.z), pir.z)
			_ring(V2, C2, pp, 3.0, C_PIR, 24)                 # main.gd / bergtal_horror PIR_DIST: a person closer than 3 m
			_cache_names.append([pp + Vector3(0, 1.5, 0), T.t("PIR Zelt (3 m)"), C_PIR])
			var hz2 = main.get("horror")
			if lw == "bergtal" and hz2 != null and bool(hz2.get("unlocked")):
				_ring(V2, C2, pp, 9.0, Color(C_HORROR, 0.7), seg)   # bergtal_horror «fig_tent»: the figure comes out of the fog 9 m away
	_cache_trig = [V2, C2]


static func _adventure_points(ch: Dictionary) -> Array:
	"""[Vector2 valley position, text] of one chapter: start, hints, forks, map reading, camp (bergtal_abenteuer_daten.gd)"""
	var out := []
	var nr := int(ch.get("id", 0))
	var cur := Vector2.ZERO
	var st = ch.get("start", null)
	if st is Array and (st as Array).size() >= 3:
		cur = Vector2(float(st[1]), float(st[2]))
		out.append([cur, T.t("K%d Start") % nr])
	for s in ch.get("stages", []):
		if s.has("walk"):
			var w: Array = s["walk"]
			if out.is_empty() and w.size() > 0:
				out.append([w[0], T.t("K%d Start") % nr])
			if w.size() > 0:
				cur = w[-1]
		elif s.has("fork"):
			out.append([cur, T.t("K%d Gabelung") % nr])
			var op0: Array = s["fork"][0][1]
			if op0.size() > 0:
				cur = op0[-1]
		elif s.has("clue"):
			out.append([cur, (T.t("K%d Begegnung") if str(s["clue"]) == "person" else T.t("K%d Hinweis")) % nr])
		elif s.has("read"):
			out.append([cur, T.t("K%d Karte lesen") % nr])
	var cp = ch.get("camp", null)
	if cp is Array and (cp as Array).size() >= 3:
		out.append([Vector2(float(cp[1]), float(cp[2])), T.t("K%d Lager") % nr])
	# the same place twice (a hint right after a fork): one marker, both names
	var merged := []
	for e in out:
		var hit := false
		for m in merged:
			if (m[0] as Vector2).distance_to(e[0]) < 3.0:
				m[1] = "%s · %s" % [m[1], e[1]]
				hit = true
		if not hit:
			merged.append([e[0], e[1]])
	return merged


func _scan_lights() -> void:
	_lights = []
	var cp: Vector3 = main.view_cam.global_position
	var far := 120.0 if _lite() else 250.0
	var found: Array = main.find_children("*", "Light3D", true, false)
	for n in found:
		if n is DirectionalLight3D or not (n as Node3D).is_inside_tree():
			continue
		var l := n as Light3D
		if (l.layers & 1) == 0 and (l.layers & 2) == 0:
			continue
		var p := l.global_position
		if p.distance_to(cp) > far:
			continue
		var lit := l.is_visible_in_tree() and l.light_energy > 0.001
		if n is OmniLight3D:
			_lights.append([p, (n as OmniLight3D).omni_range, lit, Vector3.ZERO, 0.0])
		elif n is SpotLight3D:
			_lights.append([p, (n as SpotLight3D).spot_range, lit, -l.global_transform.basis.z, deg_to_rad((n as SpotLight3D).spot_angle)])
		if _lights.size() >= 200:
			break


func _slow() -> void:
	var k := _world_key()
	if k != _key:
		_key = k
		_rebuild_cache()
	var lite := _lite()
	var cp: Vector3 = main.view_cam.global_position
	var near := 300.0 if lite else 700.0
	if on["lights"]:
		_scan_lights()
	_im_slow.clear_surfaces()
	var n := 0
	var parts: Array = []
	if on["paths"]:
		parts.append(_cache_paths)
	if on["triggers"]:
		parts.append(_cache_trig)
	var any := false
	for pc in parts:
		var V: PackedVector3Array = pc[0]
		if V.size() > 0:
			any = true
	var V3 := PackedVector3Array()
	var C3 := PackedColorArray()
	if on["lights"]:
		for e in _lights:
			var p: Vector3 = e[0]
			var col: Color = C_LAMP if bool(e[2]) else C_LAMP_OFF
			var r := minf(float(e[1]), 60.0)
			for d in [Vector3(0.3, 0, 0), Vector3(0, 0.3, 0), Vector3(0, 0, 0.3)]:
				V3.append(p - d)
				V3.append(p + d)
				C3.append(col)
				C3.append(col)
			var dir: Vector3 = e[3]
			if dir == Vector3.ZERO:
				_ring(V3, C3, p, r, Color(col, col.a * 0.6), 12 if lite else 24, false)
			else:
				var tip := p + dir * r
				V3.append(p)
				V3.append(tip)
				C3.append(col)
				C3.append(col)
				var sd := dir.cross(Vector3.UP)
				if sd.length() < 0.01:
					sd = Vector3.RIGHT
				sd = sd.normalized() * r * tan(float(e[4]))
				var up2 := dir.cross(sd).normalized() * sd.length()
				for q in [sd, -sd, up2, -up2]:
					V3.append(p)
					V3.append(tip + q)
					C3.append(Color(col, col.a * 0.5))
					C3.append(Color(col, col.a * 0.5))
	if on["spawns"]:
		for e in _start_list:
			_post(V3, C3, e[0], 1.6, e[1])
		var lw: String = dev.loaded_world()
		if lw != "bergtal" and lw != "ferienpark":
			for sd2 in [-1.0, 1.0]:                          # main.spawn(): depth 6 … 22 m, x = ± (depth × 1.6 + 6)
				var a := Vector3(-sd2 * (6.0 * 1.6 + 6.0), 0, -6.0)
				var b := Vector3(-sd2 * (22.0 * 1.6 + 6.0), 0, -22.0)
				var prev := a + Vector3(0, main.ground_y(a.x, a.z) + 0.3, 0)
				for i in range(1, 9):
					var q := a.lerp(b, float(i) / 8.0)
					q.y = main.ground_y(q.x, q.z) + 0.3
					V3.append(prev)
					V3.append(q)
					C3.append(Color(C_PERSON, 0.55))
					C3.append(Color(C_PERSON, 0.55))
					prev = q
	if V3.size() > 0:
		parts.append([V3, C3])
		any = true
	if any:
		_im_slow.surface_begin(Mesh.PRIMITIVE_LINES)
		for pc in parts:
			var V: PackedVector3Array = pc[0]
			var C: PackedColorArray = pc[1]
			var i := 0
			while i + 1 < V.size():
				var a: Vector3 = V[i]
				if a.distance_to(cp) < near or V[i + 1].distance_to(cp) < near:
					_im_slow.surface_set_color(C[i])
					_im_slow.surface_add_vertex(a)
					_im_slow.surface_set_color(C[i + 1])
					_im_slow.surface_add_vertex(V[i + 1])
					n += 2
				i += 2
		if n == 0:                                            # an empty surface is not allowed
			_im_slow.surface_add_vertex(Vector3.ZERO)
			_im_slow.surface_add_vertex(Vector3.ZERO)
		_im_slow.surface_end()
	stats["lines"] = n / 2
	_place_labels(cp, lite)


func _place_labels(cp: Vector3, lite: bool) -> void:
	var L: Array = []
	if on["triggers"]:
		for e in _cache_names:
			var d: float = (e[0] as Vector3).distance_to(cp)
			if d < (250.0 if lite else 600.0):
				L.append([d, e])
	L.sort_custom(func(a, b): return a[0] < b[0])
	var cap := 8 if lite else 24
	for i in range(maxi(cap, _labels.size())):
		if i >= _labels.size():
			if i >= cap or i >= L.size():
				break
			var lb := Label3D.new()
			lb.layers = main.HELPER_LAYER
			lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			lb.no_depth_test = true
			lb.fixed_size = true
			lb.pixel_size = 0.0009
			lb.font_size = 28
			lb.outline_size = 8
			lb.shaded = false
			main.add_child(lb)
			_labels.append(lb)
		var lb2: Label3D = _labels[i]
		if i < mini(cap, L.size()):
			var e2: Array = L[i][1]
			lb2.text = str(e2[1])
			lb2.modulate = Color(e2[2], 1.0)
			lb2.global_position = e2[0]
			lb2.visible = true
		else:
			lb2.visible = false


func _fast() -> void:
	"""every 0.1 s: the field of view and the walkways of the figures (they move)"""
	var lite := _lite()
	_im_fast.clear_surfaces()
	var V := PackedVector3Array()
	var C := PackedColorArray()
	fov_world = []
	if on["fov"] and main.cams.size() >= 2:
		var hh := deg_to_rad(main.CAM_FOV[0] * 0.5)
		var hv := atan(tan(hh) * float(main.CAM_H[0]) / float(main.CAM_W[0]))
		fov_world.append(_cone(V, C, main.cams[0], hh, hv, false, 30.0, C_HEAD, lite))
		var wt = main.get("weit")
		if wt != null and wt.has_method("installed") and wt.installed():
			var fe: bool = bool(wt.get("fisheye"))
			fov_world.append(_cone(V, C, main.cams[1], deg_to_rad(WW.FOV_H * 0.5), deg_to_rad(WW.FOV_V * 0.5), fe, 20.0, C_WIDE, lite))
	if (on["paths"] or on["spawns"]) and main.visitors != null:
		for a in main.visitors.get_children():
			if not (a is Node3D) or a.get("route") == null:
				continue
			var id: int = a.get_instance_id()
			if not _starts.has(id):
				_starts[id] = true
				var col := C_CAR if str(a.get("kind")) in VEHICLES else (C_ANIMAL if a.has_method("is_animal") and a.is_animal() else C_PERSON)
				var p0: Vector3 = (a as Node3D).global_position
				_start_list.append([p0, col, dev.to_world(p0)])
				if _start_list.size() > 60:
					_start_list.pop_front()
			if on["paths"] and not bool(a.get("done")):
				var prev: Vector3 = (a as Node3D).global_position + Vector3(0, 0.15, 0)
				var pts: Array = [a.get("target")]
				for r in a.get("route"):
					pts.append(r[0] if r is Array else r)
				for q in pts:
					if not (q is Vector3):
						continue
					var qq: Vector3 = q
					qq.y = main.ground_y(qq.x, qq.z) + 0.15
					V.append(prev)
					V.append(qq)
					C.append(C_WALK)
					C.append(C_WALK)
					prev = qq
	if _starts.size() > 400:
		_starts.clear()                                      # (the list of the last 60 stays)
	if V.size() > 0:
		_im_fast.surface_begin(Mesh.PRIMITIVE_LINES)
		for i in V.size():
			_im_fast.surface_set_color(C[i])
			_im_fast.surface_add_vertex(V[i])
		_im_fast.surface_end()


func _ray_dir(ax: float, ay: float, fisheye: bool) -> Vector3:
	"""camera-local direction for the angles ax (right) / ay (up): fisheye = equidistant (weitwinkel.gd), else straight"""
	if fisheye:
		var th := Vector2(ax, ay).length()
		if th < 0.0001:
			return Vector3(0, 0, -1)
		return Vector3(sin(th) * ax / th, sin(th) * ay / th, -cos(th))
	return Vector3(tan(ax), tan(ay), -1.0).normalized()


func _cone(V: PackedVector3Array, C: PackedColorArray, cam: Camera3D, hh: float, hv: float, fisheye: bool, L: float, col: Color, lite: bool) -> PackedVector2Array:
	"""the cone of one camera: rays from the lens to the ground (at most L m), the edge of the picture on the ground"""
	var o := cam.global_position
	var bs := cam.global_transform.basis
	var per := 1 if lite else 4                            # points per picture side
	var edge: Array = []
	for k in range(per):                                    # clockwise round the picture: top, right, bottom, left
		edge.append(Vector2(-1.0 + 2.0 * k / per, 1.0))
	for k in range(per):
		edge.append(Vector2(1.0, 1.0 - 2.0 * k / per))
	for k in range(per):
		edge.append(Vector2(1.0 - 2.0 * k / per, -1.0))
	for k in range(per):
		edge.append(Vector2(-1.0, -1.0 + 2.0 * k / per))
	var hits: Array = []
	for s in edge:
		var d: Vector3 = (bs * _ray_dir(s.x * hh, s.y * hv, fisheye)).normalized()
		var h = main.ground_hit(o, d)
		var p: Vector3 = o + d * L
		if h != null and (h as Vector3).distance_to(o) < L:
			p = h
		hits.append(p)
	var corners := [0, per, 2 * per, 3 * per]
	for i in hits.size():
		if lite or i in corners or i % 2 == 0:
			V.append(o)
			V.append(hits[i])
			C.append(Color(col, col.a * (0.9 if i in corners else 0.4)))
			C.append(Color(col, col.a * (0.9 if i in corners else 0.4)))
		V.append(hits[i])
		V.append(hits[(i + 1) % hits.size()])
		C.append(col)
		C.append(col)
	var mid: Vector3 = (bs * Vector3(0, 0, -1)).normalized()      # the middle of the picture
	var mh = main.ground_hit(o, mid)
	var me: Vector3 = mh if mh != null and (mh as Vector3).distance_to(o) < L else o + mid * L
	V.append(o)
	V.append(me)
	C.append(Color(col, 0.35))
	C.append(Color(col, 0.35))
	var out := PackedVector2Array()
	var w0 = dev.to_world(o)
	if w0 != null:
		out.append(w0)
		for p2 in hits:
			var w = dev.to_world(p2)
			if w != null:
				out.append(w)
	return out


# =============================================================================================================================
# the top view (DevMap._draw calls draw_map(self) before its markers)
# =============================================================================================================================
func draw_map(m: Control) -> void:
	if not any_on():
		return
	var w: String = dev.world
	var lite := _lite()
	var loaded: bool = dev.loaded_world() == w
	if on["paths"]:
		if w == "bergtal":
			for tr in Bt.TRAILS:
				_mpoly(m, tr[1], Color(1, 1, 1, 0.85), 1.5)
			_mpoly(m, Bt.ROAD, Color(C_ROAD, 0.95), 2.0)
			for ch in AD.CHAPTERS:
				for s in ch.get("stages", []):
					if s.has("walk"):
						_mpoly(m, s["walk"], C_STORY, 2.0)
					elif s.has("fork"):
						for op in s["fork"]:
							_mpoly(m, op[1], C_STORY, 2.0)
		elif w == "ferienpark":
			for ln in Fp.LANES:
				_mpoly(m, [Vector2(float(ln[0]), float(ln[1])), Vector2(float(ln[0]), float(ln[2]))], Color(1, 1, 1, 0.7), 1.5)
			_mpoly(m, Fp.FOREST_PATH, Color(1, 1, 1, 0.7), 1.5)
			_mpoly(m, Fp.BRIDGE_PATH, Color(1, 1, 1, 0.7), 1.5)
	if on["triggers"]:
		var sc: float = m.scale_
		if w == "bergtal":
			for v in Bt.VIGNETTES:
				if absf(float(v[3])) < 0.01 and absf(float(v[4])) < 0.01:
					continue
				m.draw_arc(m.S(Vector2(float(v[3]), float(v[4]))), maxf(2.0, ErlBase.ACTIVE_R * sc), 0.0, TAU, 24, Color(C_TRIG, 0.6), 1.0)
			for ch in AD.CHAPTERS:
				for e in _adventure_points(ch):
					var p: Vector2 = m.S(e[0])
					m.draw_rect(Rect2(p - Vector2(4, 4), Vector2(8, 8)), C_ADV, false, 2.0)
					if sc > 0.4 and not lite:
						m.draw_string(m.get_theme_default_font(), p + Vector2(6, -6), str(e[1]).left(30), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, C_ADV)
			var hz = main.get("horror")
			if hz != null and bool(hz.get("unlocked")):
				var hp: Vector2 = m.S(Bt.HOSPICE)
				m.draw_arc(hp, maxf(5.0, 15.0 * sc), 0.0, TAU, 20, C_HORROR, 2.0)
				m.draw_string(m.get_theme_default_font(), hp + Vector2(8, 14), T.t("Horror: Hospiz"), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, C_HORROR)
		elif w == "ferienpark":
			for v in Fp.ERLEBNIS:
				m.draw_arc(m.S(Vector2(float(v[3]), float(v[4]))), maxf(2.0, Erl.ACTIVE_R * sc), 0.0, TAU, 24, Color(C_TRIG, 0.6), 1.0)
		if loaded:
			var pir = main.obj.get("pir", Vector3.ZERO)
			if pir is Vector3 and (pir as Vector3) != Vector3.ZERO:
				var pw = dev.to_world(pir)
				if pw != null:
					m.draw_arc(m.S(pw), maxf(3.0, 3.0 * sc), 0.0, TAU, 16, C_PIR, 1.5)
	if not loaded:
		return
	if on["fov"]:
		for i in fov_world.size():
			var pts: PackedVector2Array = fov_world[i]
			if pts.size() >= 3:
				var sp := PackedVector2Array()
				for q in pts:
					sp.append(m.S(q))
				var col: Color = C_HEAD if i == 0 else C_WIDE
				sp.append(sp[0])
				m.draw_polyline(sp, col, 1.5)
	if on["spawns"]:
		for e in _start_list:
			if e[2] != null:
				var p2: Vector2 = m.S(e[2])
				m.draw_line(p2 - Vector2(4, 4), p2 + Vector2(4, 4), e[1], 2.0)
				m.draw_line(p2 - Vector2(4, -4), p2 + Vector2(4, -4), e[1], 2.0)
	if on["lights"]:
		for e in _lights:
			var lw2 = dev.to_world(e[0])
			if lw2 != null:
				m.draw_circle(m.S(lw2), 2.5, C_LAMP if bool(e[2]) else C_LAMP_OFF)


func _mpoly(m: Control, pts: Array, c: Color, wd: float) -> void:
	var L := PackedVector2Array()
	for q in pts:
		L.append(m.S(q))
	if L.size() >= 2:
		m.draw_polyline(L, c, wd)


# =============================================================================================================================
# /control {"action": "dev", "do": "layer" | "set" | "regler"}
# =============================================================================================================================
func values() -> Dictionary:
	var out := {}
	for qd in QUICK:
		var c: Dictionary = _ctrl(str(qd[1]))
		if not c.is_empty() and c["get"] != null:
			out[str(qd[0])] = c["get"].call()
	out["lite"] = Quality.lite()
	return out


func _norm(key: String, v) -> Array:
	"""[control id, value] for a quick key ("" = unknown)"""
	match key:
		"time", "hour", "uhrzeit", "zeit":
			var s := str(v)
			if ":" in s:
				return ["hour", float(s.get_slice(":", 0)) + float(s.get_slice(":", 1)) / 60.0]
			return ["hour", float(v)]
		"weather", "wetter":
			return ["weather", str(v).to_lower()]
		"season", "jahreszeit", "monat", "month":
			var k := str(v).to_lower()
			return ["season", str(SEASON_WORDS.get(k, k))]
		"quality", "grafik", "grafik_mode", "graphics":
			return ["grafik_mode", Quality.mode_id(v)]
	return ["", null]


func control(d: Dictionary) -> Dictionary:
	match str(d.get("do", "")):
		"layer", "layers":
			var nm := layer_id(str(d.get("name", d.get("id", ""))))
			if nm == "":
				return {"ok": true, "layers": on.duplicate(), "names": on.keys()}
			var keys: Array = on.keys() if nm == "all" else [nm]
			if nm != "all" and not on.has(nm):
				return {"ok": false, "error": "unknown layer", "names": on.keys()}
			for k in keys:
				var v = d.get("on", d.get("value", null))
				set_layer(k, (str(v).to_lower() in ["on", "true", "1"]) if v != null else not bool(on[k]))
			_t_slow = 0.0
			_t_fast = 0.0
			return {"ok": true, "layers": on.duplicate(), "lite": _lite()}
		"set":
			var done := {}
			var bad := []
			var pairs := {}
			if d.has("what") or d.has("key"):
				pairs[str(d.get("what", d.get("key", "")))] = d.get("value", "")
			for k in ["time", "hour", "weather", "season", "quality", "grafik", "uhrzeit", "wetter", "jahreszeit"]:
				if d.has(k):
					pairs[k] = d[k]
			if pairs.is_empty():
				return {"ok": false, "error": "missing value: time, weather, season or quality", "values": values()}
			for k in pairs:
				var nv := _norm(str(k).to_lower(), pairs[k])
				if nv[0] == "":
					bad.append(k)
					continue
				var c: Dictionary = _ctrl(str(nv[0]))
				if not c.is_empty() and c.type == "select":
					var ok := false
					for op in c.extra.get("options", []):
						ok = ok or str(op[0]) == str(nv[1])
					if not ok:
						bad.append(k)
						continue
				var r: Dictionary = main.control_set(str(nv[0]), nv[1])
				if bool(r.get("ok", false)):
					done[str(nv[0])] = nv[1]
				else:
					bad.append(k)
			_paint_ui()
			var res := {"ok": bad.is_empty(), "set": done, "values": values()}
			if not bad.is_empty():
				res["error"] = "unknown key or value: %s" % ", ".join(bad.map(func(x): return str(x)))
			if done.has("grafik_mode") and (str(done["grafik_mode"]) == "hoch") != Hoch.forward_plus() and not _lite():
				res["restart"] = true                         # grafik_hoch.gd: to Hoch and back = a restart (Forward+ / normal)
			return res
		"regler", "values":
			return {"ok": true, "values": values()}
	return {"ok": false, "error": "unknown do - the values: layer (name, on), set (time, weather, season, quality), regler"}


func info() -> Dictionary:
	return {"layers": on.duplicate(), "lines": stats["lines"], "slow_us": stats["us"], "starts": _start_list.size(), "lights": _lights.size()}
