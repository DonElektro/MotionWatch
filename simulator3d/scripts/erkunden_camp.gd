extends Node
## «Camp aufstellen» beim Frei erkunden (Fragebogen des Besitzers 22.11.2026, 13:10–13:16). Ein Kind von explore_person.gd
## («person.camp»); die Regeln und das Feuer als Daten: erkunden_camp_daten.gd.
##   1. Aufstellen nur, was im Rucksack ist: Schlafplatz (Kuppelzelt, Einmannzelt, Tarp, Biwaksack, Isomatte + Schlafsack),
##      Feuerstelle (mit Zündhölzern) und Kocher, Kleines (Rucksack, Stirnlampe als Licht, Sitzkissen, Campingstuhl,
##      Wäscheleine) und MoveEye auf dem Mini-Stativ - dann bewacht MoveEye das Camp wie sonst mit der Kopfkamera.
##   2. Vorschau durchsichtig vor der Figur, drehen (Q / E, Knöpfe ⟲ ⟳), grün = passt, rot = zu steil / zu nah / im Wasser;
##      «Aufstellen» (Enter / Knopf): die Figur kniet ein paar Sekunden, das Ding wächst. Tab / Knopf «Camp» = das Menü.
##   3. Feuer: anzünden, Holz nachlegen, brennt herunter zur Glut, löschen; kochen und wärmen (wirkt nur mit «Echt»);
##      Hinweis bei Feuerverbot (Wald, Schutzgebiet, Trockenheit); der «Glut-Wächter» von MoveEye prüft mit dem Wärmebild,
##      ob das Feuer aus ist (mit Bild aus dem Wärmebild von MoveEye, sonst aus der Temperatur der Feuerstelle).
##   4. Hinlegen am eigenen Schlafplatz: «Nacht spulen» (MoveEye wacht, am Morgen ein Bericht) oder «Live».
##   5. Aufstellen darf man überall, mit Hinweisen (Wildruhezone - Haken unten, steil, Bach, Steinschlag).
##   6. Einpacken: ein Ding antippen → einpacken, oder «Alles einpacken»; das Feuer muss zuerst aus sein. Beim Verlassen
##      von «Frei erkunden» (Esc) die Frage «Camp stehen lassen oder einpacken?»; ein stehen gelassenes Camp merkt den Ort
##      (Ort merken) und steht beim nächsten Mal wieder da (user://erkunden_camp.json).
##   7. Die lose blaue Zeltplane (simreal.gd, Fehlalarm-Probe): beim Frei erkunden nur, wenn ein Tarp im Rucksack ist.
## Haken für die Wildruhezonen (Zweig «wildcamp-karte»): bergtal.gd wrz_at(x, z), wenn es sie gibt, und zonen_haken
## (Callable(welt_pos: Vector3) -> {name, z}) für andere Welten. Nichts davon ist Pflicht.
## Steuerbefehl {"action": "explore", "camp": {...}} → steuern() (für Tests und Fernsteuerung); Zustand in info().

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const D = preload("res://scripts/erkunden_camp_daten.gd")
const RS = preload("res://scripts/erkunden_rucksack.gd")
const Welt = preload("res://scripts/erkunden_welt.gd")
const Bt = preload("res://scripts/bergtal.gd")
const BibBerg = preload("res://scripts/bib_berg.gd")

const DATEI := "user://erkunden_camp.json"
const BAU_S := {"kuppelzelt": 4.0, "einmannzelt": 3.5, "tarp": 3.5, "biwaksack": 2.5, "isomatte": 2.0, "feuerstelle": 3.0}
const BAU_KLEIN_S := 1.5
const SCHLAF_NAH := 2.6              # m: so nah am eigenen Schlafplatz zählt «hinlegen» als «schlafen gehen»
const WAERME_NAH := 3.5              # m: so nah am Feuer wird es warm («Echt»)

var person
var main
var datei := DATEI                   # (tests: another file)
var zonen_haken: Callable            # another world: Callable(Vector3) -> {name, z} = a Wildruhezone there ({} = none)
var stehen: Array = []               # [{id, x, y, z, yaw, node}] - world positions
var feuer := D.feuer_neu()
var vorschau := ""                   # the id being placed ("" = none)
var dreh := 0.0                      # rad: turned by the player
var platz := {}                      # the last check of the preview place: pruefen() + {p, y, hinweise}
var bau := {}                        # building now: {id, p, y, yaw, t0, dauer, node}
var glut := {}                       # Glut-Wächter: {status, temp, quelle, t}
var nacht_bericht: Array = []        # the lines of the last morning report
var trotz_verbot := false            # the player confirmed lighting despite a ban
var _root: Node3D = null
var _ghost: Node3D = null
var _ghost_id := ""
var _ghost_mat: StandardMaterial3D
var _fl: Dictionary = {}             # the fire: {flammen: Node3D, glut: MeshInstance3D, licht: OmniLight3D, th: MeshInstance3D, temp}
var _mw_alt := {}                    # MoveEye before it went on the mini tripod: {pos, rot, mast, chassis}
var _layer: CanvasLayer
var knopf: Button                    # «Camp» (all devices)
var _panel: PanelContainer
var _box: VBoxContainer
var _leiste: PanelContainer          # the bar while placing
var _leiste_text: Label
var _leiste_hinweis: Label
var _dlg: PanelContainer
var _dlg_box: VBoxContainer
var dialog := ""                     # "" | nacht | ende | morgen | verbot
var _war_liegen := false
var _geladen_fuer := ""              # scene for which the saved camp was looked at
var _check_t := 0.0
var _eval_p := Vector2(INF, INF)
var _eval := {}
var _glut_t := 0.0
var _tarp_soll := -1                 # what the loose tarp of simreal.gd should show (-1 = not touched)
var _ende_danach: Callable
var _szene := ""                     # the world of the camp (a scene change saves it under its own world)


# ---- building the screen -----------------------------------------------------------------------------------------------
func _ready() -> void:
	process_priority = 98
	_layer = CanvasLayer.new()
	_layer.layer = 9
	add_child(_layer)
	knopf = Button.new()
	knopf.name = "camp_knopf"
	knopf.focus_mode = Control.FOCUS_NONE
	knopf.custom_minimum_size = Vector2(96, 48)
	knopf.add_theme_font_size_override("font_size", 16)
	knopf.pressed.connect(func(): menu(not _panel.visible))
	knopf.visible = false
	_layer.add_child(knopf)
	_panel = PanelContainer.new()
	_panel.name = "camp_menu"
	_panel.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL.r, UI.PANEL.g, UI.PANEL.b, 0.96), UI.LINE, 12, 10, 1))
	_panel.visible = false
	_layer.add_child(_panel)
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sc.name = "scroll"
	_panel.add_child(sc)
	_box = VBoxContainer.new()
	_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_box.add_theme_constant_override("separation", 6)
	sc.add_child(_box)
	_leiste = PanelContainer.new()
	_leiste.name = "camp_leiste"
	_leiste.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL.r, UI.PANEL.g, UI.PANEL.b, 0.92), UI.LINE, 12, 8, 1))
	_leiste.visible = false
	_layer.add_child(_leiste)
	var lv := VBoxContainer.new()
	lv.add_theme_constant_override("separation", 4)
	_leiste.add_child(lv)
	_leiste_text = Label.new()
	_leiste_text.add_theme_font_size_override("font_size", 16)
	_leiste_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_leiste_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lv.add_child(_leiste_text)
	_leiste_hinweis = Label.new()
	_leiste_hinweis.add_theme_font_size_override("font_size", 13)
	_leiste_hinweis.add_theme_color_override("font_color", UI.ORG)
	_leiste_hinweis.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_leiste_hinweis.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lv.add_child(_leiste_hinweis)
	var hb := HBoxContainer.new()
	hb.alignment = BoxContainer.ALIGNMENT_CENTER
	hb.add_theme_constant_override("separation", 8)
	lv.add_child(hb)
	for e in [["links", "⟲"], ["rechts", "⟳"], ["auf", "Aufstellen"], ["weg", "Abbrechen"]]:
		var b := Button.new()
		b.name = str(e[0])
		b.set_meta("t", str(e[1]))
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(56 if str(e[0]) in ["links", "rechts"] else 110, 52)
		b.add_theme_font_size_override("font_size", 20 if str(e[0]) in ["links", "rechts"] else 16)
		var id := str(e[0])
		b.pressed.connect(func(): _leiste_knopf(id))
		if id == "auf":
			UI.primary(b)
		hb.add_child(b)
	_dlg = PanelContainer.new()
	_dlg.name = "camp_dialog"
	_dlg.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL.r, UI.PANEL.g, UI.PANEL.b, 0.97), UI.ACC, 14, 14, 2))
	_dlg.visible = false
	_layer.add_child(_dlg)
	_dlg_box = VBoxContainer.new()
	_dlg_box.add_theme_constant_override("separation", 8)
	_dlg.add_child(_dlg_box)
	_ghost_mat = StandardMaterial3D.new()
	_ghost_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_ghost_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_ghost_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_ghost_mat.no_depth_test = false
	_ghost_mat.albedo_color = Color(0.3, 1.0, 0.45, 0.42)


func _an() -> bool:
	return person != null and person.ok() and bool(person.active) and person.ex != null and bool(person.ex.on)


func rs() -> Dictionary:
	return RS.norm(main.get("ex_rucksack"))


func echt() -> bool:
	return bool(main.get("ex_kraft_echt"))


func sag(text: String, secs := 3.0) -> void:
	if person != null and person.sachen != null:
		person.sachen.sag(text, secs)
	else:
		main.start_info = text


func _root_node() -> Node3D:
	if _root == null or not is_instance_valid(_root):
		_root = Node3D.new()
		_root.name = "erkunden_camp"
		main.add_child(_root)
	return _root


func _bib(holder: Node3D):
	return BibBerg.new(main, main.scenes, holder, holder.global_transform if holder.is_inside_tree() else Transform3D())


# ---- the place in the world -------------------------------------------------------------------------------------------------
func _bt():
	if str(main.scene) != "bergtal" or main.scenes == null:
		return null
	var b = main.scenes.data.get("bergtal", null)
	return b if b != null and b.get("tal") != null else null


func steil(p: Vector3, r := 1.0) -> float:
	"""degrees: the steepest of five points round p (like bergtal.gd ground_slope, for every world: main.ground_y)"""
	var mx := 0.0
	for o in [Vector2.ZERO, Vector2(r, 0), Vector2(-r, 0), Vector2(0, r), Vector2(0, -r)]:
		var c := Vector2(p.x, p.z) + (o as Vector2)
		var d := maxf(0.6, r * 0.8)
		var gx: float = (float(main.ground_y(c.x + d, c.y)) - float(main.ground_y(c.x - d, c.y))) / (2.0 * d)
		var gz: float = (float(main.ground_y(c.x, c.y + d)) - float(main.ground_y(c.x, c.y - d))) / (2.0 * d)
		mx = maxf(mx, rad_to_deg(atan(Vector2(gx, gz).length())))
	return mx


func im_wasser(p: Vector3, r := 0.6) -> bool:
	for o in [Vector2.ZERO, Vector2(r, 0), Vector2(-r, 0), Vector2(0, r), Vector2(0, -r)]:
		if not Welt.wasser(main, p + Vector3((o as Vector2).x, 0, (o as Vector2).y)).is_empty():
			return true
	return false


func wildruhezone(p: Vector3) -> Dictionary:
	"""the hook for the Wildruhezonen: bergtal.gd wrz_at() (branch «wildcamp-karte», when it is there) or zonen_haken"""
	if zonen_haken.is_valid():
		var r = zonen_haken.call(p)
		if r is Dictionary and not (r as Dictionary).is_empty():
			return r
	var b = _bt()
	if b != null:
		var bts = load("res://scripts/bergtal.gd")
		for m in bts.get_script_method_list():
			if str(m.get("name", "")) == "wrz_at":
				var v: Vector3 = b.V(p)
				var r2 = bts.call("wrz_at", v.x, v.z)
				return r2 if r2 is Dictionary else {}
	return {}


func umgebung(p: Vector3) -> Dictionary:
	"""what the notices need: {bach_m, steinschlag, wildruhezone, wald, schutz, trocken, tiere, leute, wind}"""
	var w := {"bach_m": INF, "steinschlag": 0.0, "wildruhezone": wildruhezone(p), "wald": false, "schutz": false, "trocken": trocken(),
			"tiere": 0.5, "leute": 0.3, "wind": 0.4}
	var b = _bt()
	if b != null:
		var v: Vector3 = b.V(p)
		var q := Vector2(v.x, v.z)
		for st in Bt.STREAMS:
			var pts: Array = st[0]
			for i in range(pts.size() - 1):
				w["bach_m"] = minf(float(w["bach_m"]), maxf(0.0, Bt._seg_t(q, pts[i], pts[i + 1]).y - float(st[1]) * 0.5))
		w["wald"] = Bt.forest_k(q.x, q.y, Bt.H(q.x, q.y)) > 0.35
		if q.distance_to(_eval_p) > 4.0 or _eval.is_empty():           # the evaluation is slow: only after moving 4 m
			_eval_p = q
			_eval = b.evaluate(q.x, q.y) if b.has_method("evaluate") else {}
		w["steinschlag"] = float(_eval.get("rockfall", 0.0))
		w["tiere"] = float(_eval.get("animals", 0.5))
		w["leute"] = float(_eval.get("strangers", 0.3))
		w["wind"] = float(_eval.get("wind", 0.4))
	else:
		w["wald"] = str(main.scene) in ["forest", "pfadilager", "wildlife"]
	if main.has_meta("erkunden_camp_umgebung"):                       # (tests: a place with a stream, a ban …)
		var u = main.get_meta("erkunden_camp_umgebung")
		if u is Dictionary:
			for k in u:
				w[k] = u[k]
	return w


func trocken() -> bool:
	"""drought: a hot, dry summer day (July / August, clear, ≥ 25 °C)"""
	var doy: int = int(main.day_of_year()) if main.has_method("day_of_year") else 180
	return doy >= 170 and doy <= 250 and str(main.weather) == "clear" and float(main.ambient) >= 25.0


# ---- placing --------------------------------------------------------------------------------------------------------------
func vorschau_start(id: String) -> bool:
	if not _an():
		return false
	var why := D.verfuegbar(rs(), id)
	if why != "":
		sag(why)
		return false
	for e in stehen:
		if str(e["id"]) == id:
			sag(T.t("Steht schon im Camp"))
			return false
	if not bau.is_empty():
		return false
	vorschau = id
	dreh = 0.0
	_panel.visible = false
	_ghost_bauen(id)
	_vorschau_tick(0.0, true)
	return true


func vorschau_ende() -> void:
	vorschau = ""
	platz = {}
	if _ghost != null and is_instance_valid(_ghost):
		_ghost.queue_free()
	_ghost = null
	_ghost_id = ""
	_leiste.visible = false


func drehen(k: float) -> void:
	dreh = wrapf(dreh + k, -PI, PI)


func _vorschau_ort() -> Dictionary:
	"""where the preview stands: in front of the figure, on the ground"""
	var d := D.ding(vorschau)
	var p: Vector3 = person.figur.pos() + person.figur.vorne() * float(d.get("weit", 2.0))
	var y: float = main.ground_y(p.x, p.z)
	return {"p": Vector3(p.x, y, p.z), "yaw": float(person.actor.heading) + PI + dreh}


func _stehen_daten() -> Array:
	return stehen.map(func(e): return {"id": e["id"], "x": e["x"], "z": e["z"]})


func pruefe_platz(id: String, p: Vector3) -> Dictionary:
	var d := D.ding(id)
	var sl := steil(p, maxf(0.6, float(d.get("r", 0.5))))
	var r := D.pruefen(id, Vector2(p.x, p.z), sl, im_wasser(p, minf(0.8, float(d.get("r", 0.5)))), _stehen_daten())
	r["hinweise"] = D.hinweise(id, sl, umgebung(p))
	r["steil"] = snappedf(sl, 0.1)
	return r


func _vorschau_tick(_dt: float, sofort := false) -> void:
	if vorschau == "" or not person.ok():
		return
	var o := _vorschau_ort()
	var p: Vector3 = o["p"]
	if _ghost != null and is_instance_valid(_ghost):
		_ghost.global_position = p
		_ghost.rotation.y = float(o["yaw"])
	if sofort or main.now() - _check_t > 0.2:
		_check_t = main.now()
		platz = pruefe_platz(vorschau, p)
		platz["p"] = p
		platz["yaw"] = float(o["yaw"])
		var gut := bool(platz["ok"])
		_ghost_mat.albedo_color = Color(0.3, 1.0, 0.45, 0.42) if gut else Color(1.0, 0.25, 0.2, 0.45)
		_leiste_text.text = T.t(str(D.ding(vorschau)["name"])) + " · " + (T.t("Passt hier") if gut else str(platz["grund"]))
		_leiste_text.add_theme_color_override("font_color", UI.GRN if gut else UI.RED)
		var hw: Array = platz["hinweise"]
		_leiste_hinweis.text = "⚠ " + " · ".join(hw) if not hw.is_empty() else ""
		_leiste_hinweis.visible = not hw.is_empty()
		for b in _leiste.find_children("*", "Button", true, false):
			(b as Button).text = T.t(str(b.get_meta("t")))
			if b.name == "auf":
				(b as Button).disabled = not gut
	_leiste.visible = true


func aufstellen() -> bool:
	"""«Aufstellen»: the figure kneels, the thing grows (a few seconds)"""
	if vorschau == "":
		return false
	_vorschau_tick(0.0, true)
	if not bool(platz.get("ok", false)):
		sag(str(platz.get("grund", "")))
		return false
	var id := vorschau
	var p: Vector3 = platz["p"]
	var yaw: float = platz["yaw"]
	var hw: Array = platz.get("hinweise", [])
	vorschau_ende()
	var n := _ding_bauen(id, p, yaw)
	n.scale = Vector3.ONE * 0.05
	bau = {"id": id, "p": p, "yaw": yaw, "t0": main.now(), "dauer": float(BAU_S.get(id, BAU_KLEIN_S)), "node": n}
	person.set_haltung("geduckt")                                    # kneeling down to build
	person.actor.frozen = true
	sag(T.t("Aufbauen …") + ("  ⚠ " + str(hw[0]) if not hw.is_empty() else ""), float(bau["dauer"]) + 1.0)
	return true


func _bau_tick() -> void:
	if bau.is_empty():
		return
	var k := clampf((main.now() - float(bau["t0"])) / maxf(0.1, float(bau["dauer"])), 0.0, 1.0)
	var n: Node3D = bau["node"]
	if is_instance_valid(n):
		n.scale = Vector3.ONE * lerpf(0.05, 1.0, smoothstep(0.0, 1.0, k))
	if k >= 1.0:
		bau_fertig()


func bau_fertig() -> void:
	"""(also for tests: finishes the building at once)"""
	if bau.is_empty():
		return
	var n: Node3D = bau["node"]
	if is_instance_valid(n):
		n.scale = Vector3.ONE
	var p: Vector3 = bau["p"]
	stehen.append(_eintrag(str(bau["id"]), p, float(bau["yaw"]), n))
	if str(bau["id"]) == "moveeye":
		_moveeye_hin(p, float(bau["yaw"]))
	if str(bau["id"]) == "feuerstelle":
		feuer = D.feuer_neu()
	sag(T.t("%s steht") % T.t(str(D.ding(str(bau["id"]))["name"])), 2.0)
	bau = {}
	if person.ok():
		person.actor.frozen = not bool(person.active)
		person.set_haltung("stehen")
	if _panel.visible:
		_menu_bauen()


func _eintrag(id: String, p: Vector3, yaw: float, n: Node3D) -> Dictionary:
	"""one standing thing; in the Bergtal also in valley metres (the valley turns with the chosen spot)"""
	_szene = str(main.scene)
	var b = _bt()
	var v: Vector3 = b.V(p) if b != null else p
	return {"id": id, "x": p.x, "y": p.y, "z": p.z, "yaw": yaw, "node": n, "v": v, "tal": b != null}


func setzen(id: String, p: Vector3, yaw := 0.0) -> bool:
	"""tests / the control command: set up at once at p (same checks as the preview)"""
	if D.verfuegbar(rs(), id) != "":
		return false
	for e in stehen:
		if str(e["id"]) == id:
			return false
	var y: float = main.ground_y(p.x, p.z)
	var q := Vector3(p.x, y, p.z)
	var r := pruefe_platz(id, q)
	if not bool(r["ok"]):
		platz = r
		return false
	bau = {"id": id, "p": q, "yaw": yaw, "t0": main.now(), "dauer": 0.0, "node": _ding_bauen(id, q, yaw)}
	bau_fertig()
	return true


func _ding_bauen(id: String, p: Vector3, yaw: float) -> Node3D:
	var h := Node3D.new()
	h.name = "camp_" + id
	_root_node().add_child(h)
	h.global_position = p
	h.rotation.y = yaw
	var d := D.ding(id)
	var art := str(d.get("art", ""))
	match id:
		"kuppelzelt":
			_bib_art(h, art, {"col": "e86a1a"})
		"einmannzelt":
			_bib_art(h, art, {"col": "3a7a3a"})
		"tarp":
			_bib_art(h, art, {"col": "2a4a8a"})
		"biwaksack", "isomatte", "rucksack":
			_bib_art(h, art, {})
		"kocher":
			_bib_art(h, art, {"hot": false})
		"feuerstelle":
			_bib_art(h, "campfire", {"fire": false, "benches": false})
			_feuer_teile(h)
		"moveeye":
			var t := Node3D.new()
			t.scale = Vector3(0.4, 0.4, 0.4)
			h.add_child(t)
			_bib_art(t, "tripod", {"h": 0.9})
		"stirnlampe":
			_lampe(h)
		"sitzkissen":
			main.add_mesh(h, main.box(0.4, 0.07, 0.4), Vector3(0, 0.035, 0), _mat(Color(0.2, 0.55, 0.75)), "tent")
		"stuhl":
			_stuhl(h)
		"waescheleine":
			_leine(h)
	return h


func _bib_art(h: Node3D, art: String, q: Dictionary) -> void:
	var bib = _bib(h)
	var dd: Dictionary = bib.make(art, q)
	if dd.is_empty():
		return
	bib._node_thing(dd, Transform3D.IDENTITY, art)


func _mat(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = 0.85
	return m


func _lampe(h: Node3D) -> void:
	main.add_mesh(h, main.box(0.05, 0.6, 0.05), Vector3(0, 0.3, 0), _mat(Color(0.35, 0.35, 0.37)), "metal")
	var lm := StandardMaterial3D.new()
	lm.albedo_color = Color(1.0, 0.95, 0.8)
	lm.emission_enabled = true
	lm.emission = Color(1.0, 0.9, 0.7)
	lm.emission_energy_multiplier = 2.5
	main.add_mesh(h, main.box(0.09, 0.07, 0.07), Vector3(0, 0.62, 0), lm, 40.0)
	var l := OmniLight3D.new()
	l.name = "licht"
	l.position = Vector3(0, 0.65, 0)
	l.omni_range = 5.0
	l.light_color = Color(1.0, 0.92, 0.78)
	l.light_energy = 1.2
	h.add_child(l)


func _stuhl(h: Node3D) -> void:
	var stoff := _mat(Color(0.75, 0.3, 0.15))
	var stange := _mat(Color(0.2, 0.2, 0.22))
	main.add_mesh(h, main.box(0.48, 0.04, 0.45), Vector3(0, 0.42, 0), stoff, "tent")
	main.add_mesh(h, main.box(0.48, 0.5, 0.04), Vector3(0, 0.68, 0.22), stoff, "tent", Vector3(-0.2, 0, 0))
	for x in [-0.22, 0.22]:
		for z in [-0.2, 0.2]:
			main.add_mesh(h, main.box(0.025, 0.44, 0.025), Vector3(x, 0.21, z), stange, "metal")


func _leine(h: Node3D) -> void:
	var holz := _mat(Color(0.45, 0.32, 0.2))
	for x in [-1.2, 1.2]:
		main.add_mesh(h, main.box(0.05, 1.5, 0.05), Vector3(x, 0.75, 0), holz, "tree")
	main.add_mesh(h, main.box(2.4, 0.01, 0.01), Vector3(0, 1.45, 0), _mat(Color(0.9, 0.9, 0.85)), "tent")
	var farben := [Color(0.85, 0.2, 0.2), Color(0.25, 0.45, 0.85), Color(0.95, 0.85, 0.3)]
	for i in range(3):
		main.add_mesh(h, main.box(0.35, 0.45, 0.01), Vector3(-0.7 + 0.7 * i, 1.22, 0), _mat(farben[i]), "tent")


func _feuer_teile(h: Node3D) -> void:
	"""the flames, the embers, the light and the warm spot for the thermal camera (state: _feuer_bild)"""
	var fl := Node3D.new()
	fl.name = "flammen"
	h.add_child(fl)
	var fm := StandardMaterial3D.new()
	fm.albedo_color = Color(1.0, 0.55, 0.12)
	fm.emission_enabled = true
	fm.emission = Color(1.0, 0.5, 0.1)
	fm.emission_energy_multiplier = 4.0
	fm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for e in [[Vector3(0, 0.35, 0), 0.22, 0.7], [Vector3(0.12, 0.28, 0.08), 0.14, 0.5], [Vector3(-0.1, 0.26, -0.06), 0.12, 0.45]]:
		var c := CylinderMesh.new()
		c.top_radius = 0.0
		c.bottom_radius = float(e[1])
		c.height = float(e[2])
		var mi := MeshInstance3D.new()
		mi.mesh = c
		mi.material_override = fm
		mi.position = e[0]
		mi.layers = 1
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		fl.add_child(mi)
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(0.9, 0.25, 0.05)
	gm.emission_enabled = true
	gm.emission = Color(1.0, 0.3, 0.05)
	gm.emission_energy_multiplier = 2.0
	var gc := CylinderMesh.new()
	gc.top_radius = 0.38
	gc.bottom_radius = 0.42
	gc.height = 0.06
	var gl := MeshInstance3D.new()
	gl.mesh = gc
	gl.material_override = gm
	gl.position = Vector3(0, 0.1, 0)
	gl.layers = 1
	h.add_child(gl)
	var th := MeshInstance3D.new()                                    # the warm spot (thermal layer)
	var tc := CylinderMesh.new()
	tc.top_radius = 0.3
	tc.bottom_radius = 0.45
	tc.height = 0.5
	th.mesh = tc
	th.position = Vector3(0, 0.28, 0)
	th.layers = 2
	th.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	h.add_child(th)
	var l := OmniLight3D.new()
	l.position = Vector3(0, 0.7, 0)
	l.light_color = Color(1.0, 0.55, 0.2)
	l.omni_range = 9.0
	l.shadow_enabled = false
	h.add_child(l)
	_fl = {"flammen": fl, "glut": gl, "licht": l, "th": th, "temp": -999.0}
	_feuer_bild()


func _feuer_bild() -> void:
	if _fl.is_empty() or not is_instance_valid(_fl["flammen"]):
		return
	var ph := str(feuer["phase"])
	var fl: Node3D = _fl["flammen"]
	fl.visible = ph == "brennt"
	if fl.visible:
		var k := clampf(float(feuer["holz"]) / 2.0, 0.45, 1.3)
		fl.scale = Vector3(k, k * (1.0 + 0.12 * sin(main.now() * 9.0)), k)
	var gl: MeshInstance3D = _fl["glut"]
	gl.visible = ph in ["brennt", "glut"]
	if gl.visible:
		(gl.material_override as StandardMaterial3D).emission_energy_multiplier = 2.0 if ph == "brennt" else lerpf(0.2, 1.6, float(feuer["glut"]))
	var l: OmniLight3D = _fl["licht"]
	l.light_energy = (2.2 + 0.35 * sin(main.now() * 11.0)) if ph == "brennt" else (0.5 * float(feuer["glut"]) if ph == "glut" else 0.0)
	var tp := snappedf(D.temp(feuer, float(main.ambient)), 5.0)
	if tp != float(_fl["temp"]):
		_fl["temp"] = tp
		(_fl["th"] as MeshInstance3D).material_override = main.tmat_fixed(tp)


func _ghost_bauen(id: String) -> void:
	if _ghost != null and is_instance_valid(_ghost):
		_ghost.queue_free()
	_ghost = _ding_bauen(id, person.figur.pos(), 0.0)
	_ghost.name = "camp_vorschau"
	_ghost_id = id
	for gi in _ghost.find_children("*", "GeometryInstance3D", true, false):
		if (gi as GeometryInstance3D).layers & 1:
			(gi as GeometryInstance3D).material_override = _ghost_mat
			(gi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		else:
			gi.queue_free()                                          # no thermal twin, no light: only a picture
	for l in _ghost.find_children("*", "Light3D", true, false):
		l.queue_free()
	if _fl.has("flammen") and _fl["flammen"] != null and is_instance_valid(_fl["flammen"]) and _ghost.is_ancestor_of(_fl["flammen"]):
		_fl = {}
		for e in stehen:                                              # the real fire place again
			if str(e["id"]) == "feuerstelle" and is_instance_valid(e["node"]):
				_fl_finden(e["node"])


func _fl_finden(h: Node3D) -> void:
	var fl := h.find_child("flammen", false, false)
	if fl == null:
		return
	var gl: MeshInstance3D = null
	var th: MeshInstance3D = null
	var l: OmniLight3D = null
	for c in h.get_children():
		if c is MeshInstance3D and (c as MeshInstance3D).mesh is CylinderMesh:
			if (c as MeshInstance3D).layers == 2:
				th = c
			else:
				gl = c
		elif c is OmniLight3D:
			l = c
	_fl = {"flammen": fl, "glut": gl, "licht": l, "th": th, "temp": -999.0}


# ---- MoveEye on the mini tripod ----------------------------------------------------------------------------------------------
func _moveeye_hin(p: Vector3, yaw: float) -> void:
	if _mw_alt.is_empty():
		_mw_alt = {"pos": main.rig.position, "rot": main.rig.rotation.y, "mast": float(main.mast_h),
				"chassis": main.chassis.visible if main.chassis != null else false}
	var f := _ding_pos("feuerstelle")
	var to: Vector3 = (f - p) if f != Vector3.INF else Vector3(-sin(yaw), 0, -cos(yaw)) * -1.0
	main.rig.position = p
	main.rig.rotation.y = atan2(-to.x, -to.z) if f != Vector3.INF else yaw + PI   # looking at the fire (Glut-Wächter), else away from the tripod's back
	main.set_mast(D.MINI_STATIV)
	if main.chassis != null:
		main.chassis.visible = false                                   # on the tripod, not on the mover
	if not RS.hat(rs(), "powerbank"):
		sag(T.t("MoveEye steht – ohne Powerbank hält der Akku nicht bis zum Morgen"), 3.5)
	else:
		sag(T.t("MoveEye bewacht jetzt das Camp"), 2.5)


func _moveeye_weg() -> void:
	if _mw_alt.is_empty():
		return
	main.rig.position = _mw_alt["pos"]
	main.rig.rotation.y = float(_mw_alt["rot"])
	main.set_mast(float(_mw_alt["mast"]))
	if main.chassis != null:
		main.chassis.visible = bool(_mw_alt["chassis"])
	_mw_alt = {}


func _ding_pos(id: String) -> Vector3:
	for e in stehen:
		if str(e["id"]) == id:
			return Vector3(float(e["x"]), float(e["y"]), float(e["z"]))
	return Vector3.INF


func hat(id: String) -> bool:
	return _ding_pos(id) != Vector3.INF


func schlafplatz() -> Dictionary:
	for e in stehen:
		if str(e["id"]) in D.SCHLAFPLAETZE:
			return e
	return {}


# ---- the fire ---------------------------------------------------------------------------------------------------------------
func verbot_hier() -> Array:
	var p := _ding_pos("feuerstelle")
	return D.feuer_verbot(umgebung(p)) if p != Vector3.INF else []


func anzuenden(trotzdem := false) -> bool:
	if not hat("feuerstelle"):
		sag(T.t("Zuerst eine Feuerstelle aufstellen"))
		return false
	if not RS.hat(rs(), "zuendhoelzer"):
		sag(T.t("Keine Zündhölzer im Rucksack"))
		return false
	var vb := verbot_hier()
	if not vb.is_empty() and not (trotzdem or trotz_verbot):
		_dialog_verbot(vb)
		return false
	var r := D.anzuenden(feuer)
	if not bool(r["ok"]):
		sag(str(r["grund"]))
		return false
	feuer = r["f"]
	glut = {}
	_feuer_bild()
	sag(T.t("Das Feuer brennt – Holz gesammelt und angezündet"), 2.5)
	return true


func nachlegen() -> bool:
	if not hat("feuerstelle"):
		return false
	if str(feuer["phase"]) in ["aus", "geloescht"]:
		sag(T.t("Das Feuer ist aus – zuerst anzünden"))
		return false
	var r := D.nachlegen(feuer)
	if not bool(r["ok"]):
		sag(str(r["grund"]))
		return false
	feuer = r["f"]
	_feuer_bild()
	sag(T.t("Holz nachgelegt"), 1.5)
	return true


func loeschen() -> bool:
	var r := D.loeschen(feuer)
	if not bool(r["ok"]):
		sag(str(r["grund"]))
		return false
	feuer = r["f"]
	_feuer_bild()
	sag(T.t("Feuer gelöscht – es zischt und dampft"), 2.5)
	return true


func kochen() -> bool:
	"""at the burning fire or on the stove: warm food - only with «Echt» it gives strength and warmth"""
	var am_feuer := hat("feuerstelle") and str(feuer["phase"]) in ["brennt", "glut"]
	if not (am_feuer or hat("kocher")):
		sag(T.t("Zum Kochen braucht es ein Feuer oder den Kocher"))
		return false
	var sa = person.sachen
	if not RS.hat(rs(), "essen"):
		sag(T.t("Kein Proviant mehr"))
		return false
	if not echt():
		sag(T.t("Fein gekocht! (Kraft und Wärme zählen nur mit «Echt»)"), 2.5)
		return true
	sa._nimm("essen")
	sa.hunger = 100.0
	sa.kraft = minf(100.0, sa.kraft + 35.0)
	sa.waerme = minf(100.0, sa.waerme + 35.0)
	sag(T.t("Warm gegessen – das tut gut"), 2.0)
	return true


func _feuer_tick(dt: float) -> void:
	if not hat("feuerstelle"):
		return
	var alt := str(feuer["phase"])
	feuer = D.ticken(feuer, dt, float(main.hour()))
	if alt != str(feuer["phase"]):
		if str(feuer["phase"]) == "glut":
			sag(T.t("Das Feuer ist heruntergebrannt – nur noch Glut"), 2.5)
	_feuer_bild()
	# warmth at the fire («Echt»)
	if echt() and person != null and person.ok() and person.sachen != null and str(feuer["phase"]) in ["brennt", "glut"]:
		var d: float = Vector2(person.figur.pos().x, person.figur.pos().z).distance_to(Vector2(float(_ding_pos("feuerstelle").x), float(_ding_pos("feuerstelle").z)))
		if d < WAERME_NAH:
			person.sachen.waerme = minf(100.0, float(person.sachen.waerme) + (1.2 if str(feuer["phase"]) == "brennt" else 0.4) * dt)


# ---- the Glut-Wächter (MoveEye's thermal camera checks the fire place) --------------------------------------------------------
func glut_pruefen() -> Dictionary:
	"""{status: aus | glut | brennt | sieht_nicht | kein_moveeye, temp, quelle: waermebild | feuerstelle}"""
	if not hat("moveeye"):
		glut = {"status": "kein_moveeye", "temp": 0.0, "quelle": "", "t": main.now()}
		return glut
	var f := _ding_pos("feuerstelle")
	if f == Vector3.INF:
		glut = {}
		return glut
	var ziel := f + Vector3(0, 0.25, 0)
	var cam: Camera3D = main.cams[2] if main.cams.size() > 2 else null
	var kopf: Vector3 = main.head.global_position if main.head != null else main.rig.global_position + Vector3(0, D.MINI_STATIV, 0)
	if kopf.distance_to(ziel) > 25.0 or not main.line_free(kopf + Vector3(0, 0.05, 0), ziel + Vector3(0, 0.3, 0)):
		glut = {"status": "sieht_nicht", "temp": 0.0, "quelle": "", "t": main.now()}
		return glut
	var t := D.temp(feuer, float(main.ambient))
	var quelle := "feuerstelle"
	var th: PackedFloat32Array = main.thermal
	if cam != null and th.size() == main.TH_W * main.TH_H and not cam.is_position_behind(ziel) and cam.is_position_in_frustum(ziel) \
			and main.now() - float(main.get("_th_asked")) < 3.0:
		var vp: Vector2 = Vector2(main.vps[2].size)
		var sp := cam.unproject_position(ziel) / vp
		var mx := -100.0
		for dy in range(-1, 2):
			for dx in range(-1, 2):
				var ix := clampi(int(sp.x * main.TH_W) + dx, 0, main.TH_W - 1)
				var iy := clampi(int(sp.y * main.TH_H) + dy, 0, main.TH_H - 1)
				mx = maxf(mx, th[iy * main.TH_W + ix])
		t = mx
		quelle = "waermebild"
	var st := "aus" if t < D.T_AUS else (("brennt" if t > 450.0 else "glut") if str(feuer["phase"]) != "geloescht" else "glut")
	glut = {"status": st, "temp": snappedf(t, 0.1), "quelle": quelle, "t": main.now()}
	return glut


func glut_text() -> String:
	if glut.is_empty():
		return ""
	match str(glut["status"]):
		"kein_moveeye":
			return T.t("Glut-Wächter: MoveEye auf dem Mini-Stativ aufstellen")
		"sieht_nicht":
			return T.t("Glut-Wächter: MoveEye sieht die Feuerstelle nicht")
		"aus":
			return T.t("Glut-Wächter: Feuer aus (%d °C) – sicher") % int(glut["temp"])
		"glut":
			return T.t("Glut-Wächter: noch Glut (%d °C) – nicht weggehen") % int(glut["temp"])
		"brennt":
			return T.t("Glut-Wächter: das Feuer brennt (%d °C)") % int(glut["temp"])
	return ""


# ---- packing up ---------------------------------------------------------------------------------------------------------------
func einpacken(id: String) -> bool:
	"""one thing back into the pack ('*' = everything); the fire place only when the fire is out"""
	var why := D.darf_einpacken(id, _stehen_daten(), feuer)
	if why != "":
		sag(why)
		return false
	var rest := []
	var n := 0
	for e in stehen:
		if id == "*" or str(e["id"]) == id:
			if is_instance_valid(e["node"]):
				(e["node"] as Node3D).queue_free()
			if str(e["id"]) == "moveeye":
				_moveeye_weg()
			if str(e["id"]) == "feuerstelle":
				_fl = {}
				feuer = D.feuer_neu()
				glut = {}
			n += 1
		else:
			rest.append(e)
	stehen = rest
	if n == 0:
		return false
	if stehen.is_empty():
		_datei_weg()
	sag(T.t("Alles eingepackt") if id == "*" else T.t("Eingepackt: %s") % T.t(str(D.ding(id)["name"])), 2.0)
	if _panel.visible:
		_menu_bauen()
	return true


func _alles_weg() -> void:
	"""the nodes go (the figure leaves the world) - the list is kept for saving"""
	if not bau.is_empty():
		bau_fertig()
	vorschau_ende()
	for e in stehen:
		if is_instance_valid(e["node"]):
			(e["node"] as Node3D).queue_free()
	_moveeye_weg()
	_fl = {}
	if _root != null and is_instance_valid(_root):
		_root.queue_free()
	_root = null


# ---- saving / restoring a camp left standing ----------------------------------------------------------------------------------
func _als_daten() -> Dictionary:
	var st := []
	var tal := false
	for e in stehen:
		var p: Vector3 = e["v"]                                         # (Bergtal: valley metres, else world)
		tal = bool(e.get("tal", false))
		st.append({"id": e["id"], "x": snappedf(p.x, 0.01), "y": snappedf(p.y, 0.01), "z": snappedf(p.z, 0.01), "yaw": snappedf(float(e["yaw"]), 0.001)})
	return {"scene": _szene if _szene != "" else str(main.scene), "tal": tal, "stehen": st, "feuer": feuer, "uhr": float(main.hour()),
			"zeit": Time.get_unix_time_from_system()}


func speichern() -> bool:
	if stehen.is_empty():
		return false
	var f := FileAccess.open(datei, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(_als_daten()))
	f.close()
	return true


func gespeichert() -> Dictionary:
	if not FileAccess.file_exists(datei):
		return {}
	var f := FileAccess.open(datei, FileAccess.READ)
	if f == null:
		return {}
	var d = JSON.parse_string(f.get_as_text())
	f.close()
	var c := D.camp_norm(d)
	if not c.is_empty() and d is Dictionary:
		c["tal"] = bool(d.get("tal", false))
		c["zeit"] = float(d.get("zeit", 0.0))
	return c


func _datei_weg() -> void:
	if FileAccess.file_exists(datei):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(datei))


func laden() -> bool:
	"""the camp left standing in this world: built again where it was (the fire went on burning meanwhile)"""
	var c := gespeichert()
	_geladen_fuer = str(main.scene)
	if c.is_empty() or str(c["scene"]) != str(main.scene) or not stehen.is_empty():
		return false
	var b = _bt()
	for e in c["stehen"]:
		var p := Vector3(float(e["x"]), float(e["y"]), float(e["z"]))
		if bool(c.get("tal", false)) and b != null:
			p = b.W(p)
		p.y = main.ground_y(p.x, p.z)
		var n := _ding_bauen(str(e["id"]), p, float(e["yaw"]))
		stehen.append(_eintrag(str(e["id"]), p, float(e["yaw"]), n))
		if str(e["id"]) == "moveeye":
			_moveeye_hin(p, float(e["yaw"]))
	feuer = c["feuer"]
	var weg_s := maxf(0.0, Time.get_unix_time_from_system() - float(c.get("zeit", 0.0)))
	if weg_s > 0.0 and float(c.get("zeit", 0.0)) > 0.0:
		feuer = D.ticken(feuer, weg_s, float(main.hour()))
	if hat("feuerstelle"):
		for e in stehen:
			if str(e["id"]) == "feuerstelle":
				_fl_finden(e["node"])
		_feuer_bild()
	sag(T.t("Dein Camp steht noch da"), 3.0)
	return true


func ende() -> void:
	"""Frei erkunden ends (explore_person.remove): a camp still standing is left standing (saved, place remembered)"""
	if dialog != "":
		_dlg_zu()
	_panel.visible = false
	if not stehen.is_empty():
		speichern()
	_alles_weg()
	stehen = []
	feuer = D.feuer_neu()
	glut = {}
	_geladen_fuer = ""
	_szene = ""
	_zeltplane(-1)


func frage_beim_ende(danach: Callable) -> bool:
	"""Esc / «Beenden»: with a camp standing first the question «Camp stehen lassen oder einpacken?» (true = asked)"""
	if stehen.is_empty() or not _an():
		return false
	_ende_danach = danach
	_dialog_ende()
	return true


func stehen_lassen() -> void:
	if person != null and person.extras != null and person.ok():
		var sp: Dictionary = schlafplatz()
		if not sp.is_empty():                                         # Ort merken: at the sleeping place
			person.place(Vector3(float(sp["x"]) + 1.6, 0, float(sp["z"]) + 1.6))
		person.extras.ort_merken()
	speichern()


# ---- the loose tarp of simreal.gd (Fehlalarm-Probe) ---------------------------------------------------------------------------
func _zeltplane(v: int) -> void:
	"""1 / 0: shown / hidden while exploring; -1: back as it was (everywhere else unchanged)"""
	if v == _tarp_soll:
		return
	_tarp_soll = v
	var sr = main.get("simreal")
	if sr != null and sr.has_method("zeltplane_zeigen"):
		sr.zeltplane_zeigen(v != 0)


func zeltplane_soll() -> bool:
	return RS.hat_eins(rs(), ["tarp", "ultratarp"])


# ---- the night ----------------------------------------------------------------------------------------------------------------
func schlafen_waehlen() -> void:
	if schlafplatz().is_empty():
		sag(T.t("Zuerst einen Schlafplatz aufstellen"))
		return
	if not RS.hat_eins(rs(), RS.SCHLAF) and str(schlafplatz()["id"]) != "isomatte":
		sag(T.t("Dafür braucht es einen Schlafsack"))
		return
	_dialog_nacht()


func nacht_spulen() -> Array:
	"""MoveEye watches, the night passes in a moment, in the morning the report (also: the fire burns down, the strength)"""
	_dlg_zu()
	var sp := schlafplatz()
	var h0 := float(main.hour())
	var bis := 7.0
	var stunden := fposmod(bis - h0, 24.0)
	if stunden < 1.0:
		stunden += 24.0
	var w := umgebung(Vector3(float(sp.get("x", 0.0)), 0, float(sp.get("z", 0.0)))) if not sp.is_empty() else {}
	var seed_ := int(absf(float(sp.get("x", 0.0))) * 13.0 + absf(float(sp.get("z", 0.0))) * 7.0) + int(Time.get_unix_time_from_system() / 86400.0)
	var plan := D.nacht_plan(seed_, w)
	var mw := hat("moveeye")
	var mw_yaw := 0.0
	if mw:
		var mp := _ding_pos("moveeye")
		var c := Vector3(float(sp.get("x", mp.x)), 0, float(sp.get("z", mp.z)))
		mw_yaw = atan2(c.x - mp.x, c.z - mp.z)
	var zeilen := []
	if not mw:
		zeilen.append(T.t("MoveEye war nicht aufgestellt – niemand hat gewacht."))
	elif not RS.hat(rs(), "powerbank"):
		zeilen.append(T.t("Ohne Powerbank: der Akku von MoveEye war um 02:30 leer."))
	for ev in plan:
		var akku: bool = RS.hat(rs(), "powerbank") or fposmod(float(ev["uhr"]) - 22.0, 24.0) < 4.5    # (without a power bank: empty at 02:30)
		var gesehen := D.gesehen(ev, mw and akku, mw_yaw)
		var txt := _nacht_text(str(ev["art"]))
		if mw:
			zeilen.append("%s  %s – %s" % [D.uhr_text(float(ev["uhr"])), txt, T.t("MoveEye: gesehen") if gesehen else T.t("MoveEye: nicht im Bild")])
		elif str(ev["art"]) in ["fuchs", "marder", "wanderer"]:
			zeilen.append(T.t("Am Morgen: Spuren beim Camp (%s)") % txt)
	# the fire over night
	if hat("feuerstelle"):
		var vor := str(feuer["phase"])
		feuer = D.ticken(feuer, stunden * 3600.0, h0)
		_feuer_bild()
		if vor in ["brennt", "glut", "geloescht"]:
			var aus_h := float(feuer.get("aus_seit", -1.0))
			if mw:
				zeilen.append(T.t("Glut-Wächter: Feuer um %s aus (Wärmebild unter %d °C)") % [D.uhr_text(aus_h if aus_h >= 0.0 else h0 + 0.5), int(D.T_AUS)])
			else:
				zeilen.append(T.t("Das Feuer war am Morgen aus."))
	if plan.is_empty():
		zeilen.append(T.t("Eine ruhige Nacht – nichts los."))
	# sleep (like erkunden_sachen.uebernachten): strength back, cold without a mat / in winter
	var sa = person.sachen
	var r := rs()
	var kalt: bool = not (RS.hat(r, "isomatte") or str(sp.get("id", "")) == "isomatte") or (sa._winter() and not RS.hat_eins(r, ["winterschlafsack", "daunenschlafsack"]))
	main.set_hour(bis)
	if sa != null:
		sa.kraft = 100.0
		sa.hunger = maxf(30.0, sa.hunger - 25.0)
		sa.durst = maxf(30.0, sa.durst - 25.0)
		sa.waerme = 55.0 if kalt and echt() else 100.0
	if kalt and echt():
		zeilen.append(T.t("Kalt geschlafen – mit Isomatte / Winterschlafsack wäre es wärmer"))
	nacht_bericht = zeilen
	_dialog_morgen(zeilen)
	return zeilen


func _nacht_text(art: String) -> String:
	match art:
		"fuchs":
			return T.t("Ein Fuchs schnüffelt am Camp")
		"reh":
			return T.t("Ein Reh zieht vorbei")
		"marder":
			return T.t("Ein Marder am Rucksack")
		"igel":
			return T.t("Ein Igel raschelt im Gras")
		"wanderer":
			return T.t("Jemand mit Stirnlampe geht vorbei")
		"wind":
			return T.t("Windböe – die Zeltplane flattert")
		"eule":
			return T.t("Eine Eule ruft")
	return art


func nacht_live() -> void:
	_dlg_zu()
	sag(T.t("Live: die Nacht läuft in echter Zeit, MoveEye wacht wie sonst. Aufstehen: Z oder der Knopf"), 5.0)


# ---- the dialogs --------------------------------------------------------------------------------------------------------------
func _dlg_neu(titel: String, text: String) -> void:
	for c in _dlg_box.get_children():
		c.queue_free()
	var ti := Label.new()
	ti.text = titel
	ti.add_theme_font_override("font", UI.heading_font())
	ti.add_theme_font_size_override("font_size", 18)
	ti.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_dlg_box.add_child(ti)
	if text != "":
		var l := Label.new()
		l.text = text
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.add_theme_font_size_override("font_size", 15)
		_dlg_box.add_child(l)
	_dlg.visible = true
	_panel.visible = false


func _dlg_knopf(text: String, f: Callable, haupt := false, aus := false) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(0, 50)
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	b.disabled = aus
	b.add_theme_font_size_override("font_size", 16)
	if haupt:
		UI.primary(b)
	b.pressed.connect(f)
	_dlg_box.add_child(b)
	return b


func _dlg_zu() -> void:
	_dlg.visible = false
	dialog = ""


func _dialog_nacht() -> void:
	dialog = "nacht"
	var mw := hat("moveeye")
	_dlg_neu(T.t("Gute Nacht!"), T.t("Wie soll die Nacht laufen?") + "\n" + (T.t("MoveEye wacht auf dem Mini-Stativ.") if mw else T.t("MoveEye ist nicht aufgestellt – niemand wacht.")))
	_dlg_knopf(T.t("⏩ Nacht spulen – am Morgen der Bericht"), func(): nacht_spulen(), true)
	_dlg_knopf(T.t("● Live – die Nacht in echter Zeit"), func(): nacht_live())
	_dlg_knopf(T.t("Nur kurz ausruhen"), func(): _dlg_zu())


func _dialog_morgen(zeilen: Array) -> void:
	dialog = "morgen"
	_dlg_neu(T.t("Guten Morgen! Was in der Nacht los war:"), "\n".join(zeilen))
	_dlg_knopf(T.t("Aufstehen"), func(): _dlg_zu(); person.set_haltung("stehen"), true)


func _dialog_verbot(vb: Array) -> void:
	dialog = "verbot"
	_dlg_neu(T.t("Achtung: Feuerverbot"), "\n".join(vb))
	_dlg_knopf(T.t("Kein Feuer machen"), func(): _dlg_zu(), true)
	_dlg_knopf(T.t("Trotzdem anzünden (nur im Spiel)"), func(): _dlg_zu(); trotz_verbot = true; anzuenden(true))


func _dialog_ende() -> void:
	dialog = "ende"
	var brennt := not D.ist_aus(feuer, float(main.ambient)) and hat("feuerstelle")
	_dlg_neu(T.t("Camp stehen lassen oder einpacken?"),
			(T.t("Das Feuer brennt noch!") + "\n" if brennt else "") + T.t("Ein stehen gelassenes Camp ist beim nächsten Mal wieder da (der Ort wird gemerkt)."))
	if brennt:
		_dlg_knopf(T.t("Feuer löschen"), func(): loeschen(); feuer = D.ticken(feuer, D.GELOESCHT_S + 1.0); _dialog_ende(), true)
	_dlg_knopf(T.t("Camp stehen lassen"), func(): _dlg_zu(); stehen_lassen(); _ende_fertig(), not brennt)
	_dlg_knopf(T.t("Alles einpacken"), func(): _dlg_zu(); einpacken("*"); _ende_fertig(), false, brennt)
	_dlg_knopf(T.t("Weiter erkunden"), func(): _dlg_zu())


func _ende_fertig() -> void:
	if _ende_danach.is_valid():
		var f := _ende_danach
		_ende_danach = Callable()
		f.call()


# ---- the menu «Camp» ----------------------------------------------------------------------------------------------------------
func menu(v: bool) -> void:
	if v and not _an():
		return
	_panel.visible = v
	if v:
		if vorschau != "":
			vorschau_ende()
		if hat("moveeye") and hat("feuerstelle"):
			glut_pruefen()
		_menu_bauen()


func menu_offen() -> bool:
	return _panel.visible


func _knopf(parent: Control, text: String, f: Callable, aus := false, tip := "") -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.disabled = aus
	b.tooltip_text = tip
	b.custom_minimum_size = Vector2(150, 44)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	b.pressed.connect(f)
	parent.add_child(b)
	return b


func _menu_bauen() -> void:
	for c in _box.get_children():
		c.queue_free()
	var kopf := HBoxContainer.new()
	_box.add_child(kopf)
	var ti := Label.new()
	ti.text = T.t("Camp")
	ti.add_theme_font_override("font", UI.heading_font())
	ti.add_theme_font_size_override("font_size", 17)
	ti.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	kopf.add_child(ti)
	var zu := Button.new()
	zu.text = T.t("Zu")
	zu.focus_mode = Control.FOCUS_NONE
	zu.custom_minimum_size = Vector2(60, 40)
	zu.pressed.connect(func(): menu(false))
	kopf.add_child(zu)
	var r := rs()
	# set up: only what is in the pack
	_box.add_child(UI.small(T.t("Aufstellen (nur was im Rucksack ist):"), UI.MUT))
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 6)
	g.add_theme_constant_override("v_separation", 6)
	_box.add_child(g)
	var da := {}
	for e in stehen:
		da[str(e["id"])] = true
	var n_auf := 0
	for id in D.ORDER:
		if da.has(id):
			continue
		var why := D.verfuegbar(r, id)
		if why != "" and why == T.t("Nicht im Rucksack"):
			continue                                                     # not in the pack: not offered
		var iid: String = id
		_knopf(g, T.t(str(D.ding(id)["name"])), func(): vorschau_start(iid), why != "", why)
		n_auf += 1
	if n_auf == 0:
		_box.add_child(UI.small(T.t("Nichts mehr im Rucksack zum Aufstellen."), UI.MUT))
	# the fire
	if hat("feuerstelle"):
		var ph := str(feuer["phase"])
		var zustand: String = {"brennt": T.t("brennt"), "glut": T.t("Glut"), "geloescht": T.t("gelöscht, dampft noch"), "aus": T.t("aus")}.get(ph, ph)
		_box.add_child(UI.small(T.t("Feuer: %s") % zustand, UI.ORG if ph in ["brennt", "glut"] else UI.MUT))
		var fg := GridContainer.new()
		fg.columns = 2
		fg.add_theme_constant_override("h_separation", 6)
		fg.add_theme_constant_override("v_separation", 6)
		_box.add_child(fg)
		_knopf(fg, T.t("Anzünden"), func(): anzuenden(); _menu_bauen(), ph == "brennt" or not RS.hat(r, "zuendhoelzer"), T.t("Keine Zündhölzer im Rucksack"))
		_knopf(fg, T.t("Holz nachlegen"), func(): nachlegen(); _menu_bauen(), not ph in ["brennt", "glut"])
		_knopf(fg, T.t("Löschen"), func(): loeschen(); _menu_bauen(), not ph in ["brennt", "glut"])
		_knopf(fg, T.t("Kochen"), func(): kochen(), not (ph in ["brennt", "glut"] or hat("kocher")))
		var vb := verbot_hier()
		if not vb.is_empty():
			_box.add_child(UI.small("⚠ " + " · ".join(vb), UI.ORG))
	elif hat("kocher"):
		_knopf(_box, T.t("Kochen"), func(): kochen())
	if hat("moveeye") and hat("feuerstelle"):
		var gt := glut_text()
		if gt != "":
			_box.add_child(UI.small(gt, UI.GRN if str(glut.get("status", "")) == "aus" else UI.ORG))
		_knopf(_box, T.t("Glut-Wächter: jetzt prüfen"), func(): glut_pruefen(); _menu_bauen())
	if not schlafplatz().is_empty():
		_knopf(_box, T.t("Schlafen gehen …"), func(): schlafen_waehlen())
	# packing up
	if not stehen.is_empty():
		_box.add_child(UI.small(T.t("Im Camp (antippen = einpacken):"), UI.MUT))
		var pg := GridContainer.new()
		pg.columns = 2
		pg.add_theme_constant_override("h_separation", 6)
		pg.add_theme_constant_override("v_separation", 6)
		_box.add_child(pg)
		for e in stehen:
			var eid := str(e["id"])
			var w := D.darf_einpacken(eid, _stehen_daten(), feuer)
			_knopf(pg, "↩ " + T.t(str(D.ding(eid)["name"])), func(): einpacken(eid), w != "", w)
		var wa := D.darf_einpacken("*", _stehen_daten(), feuer)
		_knopf(_box, T.t("Alles einpacken"), func(): einpacken("*"), wa != "", wa)
		if wa != "":
			_box.add_child(UI.small(wa, UI.ORG))
	_box.add_child(UI.small(T.t("PC: Tab Camp · Q / E drehen · Enter aufstellen · Esc abbrechen"), UI.MUT))


func _leiste_knopf(id: String) -> void:
	match id:
		"links":
			drehen(-PI / 8.0)
		"rechts":
			drehen(PI / 8.0)
		"auf":
			aufstellen()
		"weg":
			vorschau_ende()


# ---- input ------------------------------------------------------------------------------------------------------------------
func _input(ev: InputEvent) -> void:
	if not (ev is InputEventKey) or not ev.pressed or ev.echo or not _an() or main.typing():
		return
	var k: int = ev.keycode
	if dialog != "":
		if k == KEY_ESCAPE:
			_dlg_zu()
			get_viewport().set_input_as_handled()
		return
	if vorschau != "":
		match k:
			KEY_Q:
				drehen(-PI / 8.0)
			KEY_E:
				drehen(PI / 8.0)
			KEY_ENTER, KEY_KP_ENTER:
				aufstellen()
			KEY_ESCAPE:
				vorschau_ende()
			_:
				return
		get_viewport().set_input_as_handled()
		return
	if k == KEY_TAB:
		menu(not _panel.visible)
		get_viewport().set_input_as_handled()
	elif k == KEY_ESCAPE and _panel.visible:
		menu(false)
		get_viewport().set_input_as_handled()


# ---- every frame --------------------------------------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if person == null or main == null:
		return
	var an := _an()
	knopf.visible = an and not person.ruhig() and not (person.gestalten != null and person.gestalten.offen)
	if not an:
		if _panel.visible:
			_panel.visible = false
		if vorschau != "":
			vorschau_ende()
		if bau.size() > 0:
			bau_fertig()
		if dialog != "" and dialog != "ende":
			_dlg_zu()
		_feuer_tick(dt)
		return
	if _geladen_fuer != str(main.scene):
		laden()
	_zeltplane(1 if zeltplane_soll() else 0)
	_bau_tick()
	_vorschau_tick(dt)
	_feuer_tick(dt)
	if hat("moveeye") and hat("feuerstelle") and main.now() - _glut_t > 2.0:
		_glut_t = main.now()
		var vor := str(glut.get("status", ""))
		glut_pruefen()
		if vor in ["glut", "brennt"] and str(glut["status"]) == "aus":
			sag(T.t("Glut-Wächter: das Feuer ist aus"), 3.0)
	# lying down at the own sleeping place = going to sleep: the choice of the night
	var liegt: bool = str(person.haltung) == "liegen"
	if liegt and not _war_liegen and dialog == "" and bau.is_empty():
		var sp := schlafplatz()
		if not sp.is_empty() and Vector2(person.figur.pos().x, person.figur.pos().z).distance_to(Vector2(float(sp["x"]), float(sp["z"]))) < SCHLAF_NAH:
			_dialog_nacht()
	_war_liegen = liegt
	_layout()


func _layout() -> void:
	var s: Vector2 = get_viewport().get_visible_rect().size
	var schmal := s.x < 600.0
	knopf.text = "⛺ " + T.t("Camp") if not schmal else T.t("Camp")
	var kg := knopf.get_combined_minimum_size()
	knopf.size = kg
	var oben := 8.0
	var ruhe = person.get("ruhe")
	if ruhe != null and ruhe.has_method("knopf_unten"):
		oben = float(ruhe.knopf_unten()) + 6.0
	var sp: Vector2 = ruhe.spalte() if ruhe != null and ruhe.has_method("spalte") else Vector2(-1, -1)
	if sp.x >= 0.0:
		knopf.position = Vector2(sp.x, sp.y - kg.y - 8.0)               # phone: above the edge buttons
	else:
		knopf.position = Vector2(s.x - kg.x - (8.0 if schmal else 10.0), oben)
	if _panel.visible:
		var mw := minf(460.0, s.x - 16.0)
		_panel.custom_minimum_size = Vector2(mw, 0)
		_panel.size = Vector2(mw, minf(s.y * 0.7, 560.0))
		(_panel.get_node("scroll") as ScrollContainer).custom_minimum_size = Vector2(mw - 24.0, minf(s.y * 0.7, 560.0) - 24.0)
		_panel.position = Vector2((s.x - mw) * 0.5, maxf(oben + 56.0, s.y * 0.12))
	if _leiste.visible:
		var lw := minf(520.0, s.x - 16.0)
		_leiste.custom_minimum_size = Vector2(lw, 0)
		_leiste.size = Vector2(lw, 0)
		_leiste.position = Vector2((s.x - lw) * 0.5, s.y - _leiste.get_combined_minimum_size().y - (s.y * 0.2 if schmal else 24.0))
	if _dlg.visible:
		var dw := minf(460.0, s.x - 24.0)
		_dlg.custom_minimum_size = Vector2(dw, 0)
		_dlg.size = Vector2(dw, 0)
		_dlg.position = Vector2((s.x - dw) * 0.5, maxf(40.0, (s.y - _dlg.get_combined_minimum_size().y) * 0.4))


# ---- the control command and the state -----------------------------------------------------------------------------------------
func steuern(d: Dictionary) -> Dictionary:
	"""{"do": vorschau id | drehen k | aufstellen | abbrechen | fertig | setzen id x z [yaw] | anzuenden | nachlegen | loeschen |
	kochen | ticken s | glut | einpacken id | schlafen | spulen | live | speichern | laden | ende | menu bool}"""
	var w := str(d.get("do", ""))
	var ok := true
	match w:
		"vorschau":
			ok = vorschau_start(str(d.get("id", "")))
		"drehen":
			drehen(float(d.get("k", PI / 8.0)))
		"aufstellen":
			ok = aufstellen()
		"abbrechen":
			vorschau_ende()
		"fertig":
			bau_fertig()
		"setzen":
			ok = setzen(str(d.get("id", "")), Vector3(float(d.get("x", 0.0)), 0, float(d.get("z", 0.0))), float(d.get("yaw", 0.0)))
		"anzuenden":
			ok = anzuenden(bool(d.get("trotzdem", false)))
		"nachlegen":
			ok = nachlegen()
		"loeschen":
			ok = loeschen()
		"kochen":
			ok = kochen()
		"ticken":
			_feuer_tick(float(d.get("s", 1.0)))
		"glut":
			glut_pruefen()
		"einpacken":
			ok = einpacken(str(d.get("id", "*")))
		"schlafen":
			schlafen_waehlen()
		"spulen":
			nacht_spulen()
		"live":
			nacht_live()
		"speichern":
			ok = speichern()
		"laden":
			ok = laden()
		"ende":
			ende()
		"menu":
			menu(bool(d.get("an", true)))
	return {"ok": ok, "camp": info()}


func info() -> Dictionary:
	return {"stehen": stehen.map(func(e): return {"id": e["id"], "x": snappedf(float(e["x"]), 0.01), "z": snappedf(float(e["z"]), 0.01)}),
			"feuer": feuer, "vorschau": vorschau, "platz": {"ok": platz.get("ok", false), "grund": platz.get("grund", ""), "farbe": platz.get("farbe", ""),
			"hinweise": platz.get("hinweise", [])} if not platz.is_empty() else {}, "bau": str(bau.get("id", "")), "glut": glut, "dialog": dialog,
			"menu": _panel.visible, "knopf": knopf.visible, "moeglich": D.moeglich(rs(), _stehen_daten()), "bericht": nacht_bericht,
			"zeltplane": _tarp_soll, "moveeye": not _mw_alt.is_empty()}
