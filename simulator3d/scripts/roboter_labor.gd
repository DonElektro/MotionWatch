extends Node
## «Roboter-Labor» (Besitzer 22.11.2026, Fragebogen 15:36–15:40): eine eigene kleine 3D-Welt für den Segment-Roboter des
## Besitzers (eigenes Projekt, erst im Simulator entwickeln, später vielleicht für MoveEye). Öffnen: Mehr → «Roboter»,
## /control {"action": "roboter", "do": "open"}. Vorerst nur am PC (Maus + Tasten); alles liegt in einem eigenen
## Fenster mit eigener Welt (eigene Physik, die Szene von MoveEye bleibt, wie sie ist), damit es später auch auf Handy /
## Pad / Kiosk gehen kann (nichts hier hängt an einer Bildschirmgrösse, das Bedienfeld scrollt).
##   Teile: roboter_modell.gd (Form, Körper, Servos, Physik, Kupplung, Kollision rot), roboter_bewegung.gd (Bein-Rechnung,
##   Posen; Stufe 2: Abläufe, Gangarten), roboter_gelaende.gd (Boden mit Raster, Rampe, Stufe, Kies, Graben).
## Physik: eigene World3D (SubViewport own_world_3d) mit 24 Löser-Durchgängen; solange das Labor offen ist, rechnet die
## Physik mit 120 Schritten pro Sekunde (sonst 30, beim Schliessen zurück).
## Bedienfeld rechts: Form · Gelenke · Posen · Physik · Ansicht. Tasten: 1 frei · 2 Seite · 3 oben · 4 Roboter-Kamera ·
## R neu aufstellen · P Physik anhalten · F festhalten · K Kamerabild klein · I Info-Feld · H Bedienfeld · + / − zoomen ·
## Esc schliessen. Besitzer 23.11.2026: Kamerabild und Info-Feld lassen sich ausblenden (✕ am Feld, Knöpfe «Kamera» /
## «Info» / «Bedienfeld» in der Leiste unten, K / I), je Variante gespeichert; auf schmalen Bildschirmen und Touch ist das
## Kamerabild kleiner, die Leiste bricht um und zeigt Touch-Hinweise (ein Finger dreht, zwei Finger zoomen / verschieben).
## Maus in der 3D-Ansicht: ziehen = drehen, rechts / Mitte ziehen = verschieben, Rad = zoomen.
## /control {"action": "roboter", "do": open | close | info | pose (name, snap) | set (id, value) | param (key, value) |
##           view (frei | seite | oben | roboter) | pause (on) | reset | hold (on) | tab (name) | pip (on) |
##           gang (name, drive, turn) | ablauf (name) | goal (pos [x, y, z]) | stop | ring (drive, turn) |
##           gelaende (name | [names], ring) | anpassen (on)}   gang also takes strafe (+ links) and turn (+ links)

const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
const MODELL = preload("res://scripts/roboter_modell.gd")
const BEWEGUNG = preload("res://scripts/roboter_bewegung.gd")
const GELAENDE = preload("res://scripts/roboter_gelaende.gd")
const ANZEIGE = preload("res://scripts/roboter_anzeige.gd")
const STEUERUNG = preload("res://scripts/roboter_steuerung.gd")
const STICK = preload("res://scripts/roboter_stick.gd")   # Tastatur, Controller, Maus, Körper verschieben (28.11.2026)
const KI = preload("res://scripts/roboter_ki_gang.gd")
const KI_LERNEN := "res://scripts/roboter_ki_lernen.gd"   # Stufe 3 (Helfer B), nur wenn vorhanden
const TICKS := 120
# Zwei Varianten (Besitzer 22.11.2026 21:33): «8 Segmente» (Ring 8 × 45°) und «4 Segmente» (Ring 4 × 90°, die 45°-Schrägen
# liegen flach aneinander). Jede Variante hat ihre eigenen Regler, Pose und Gang-Werte (user://roboter_labor.json).
# Einstieg von aussen (z. B. ?roboter=4 der Startseite): control({"do": "open", "variante": "4"}) - variante_aus() deutet den Wert.
const VARIANTEN := [["8", "8 Segmente"], ["6", "6 Segmente"], ["4", "4 Segmente"], ["3", "3 Segmente"], ["2", "2 Segmente"]]   # 6er: Besitzer 21:54 (Ring 6 × 60°)
# 3 und 2 Segmente (Besitzer 28.11.2026 14:40): 6 bzw. 4 Beine, gleiche Masse wie der 8er; kein Ring (Gelenke ±90°:
# 3 × 120° / 2 × 180° gehen nicht) - Ring-Knöpfe, Pose «Ring», «Einrollen» und «Rund rollen» sind dort gesperrt, der Riegel bleibt offen.
const FEST := ["6", "4", "3", "2"]     # Varianten mit fester Segmentzahl (alle ausser dem 8er)
const RING_HINWEIS := "Ring braucht mindestens 4 Segmente"
const SPEICHER := "user://roboter_labor.json"
const BEW_KEYS := ["hoehe", "spreiz", "tempo", "schritt_laenge", "schritt_hoehe", "anpassen", "ring_methode", "ring_hoehe", "spur_rollen"]
# Start-Werte fürs Rollen je Variante (gemessen 22.11.2026, je 3 Versuche über eine ganze Drehung, Median):
#   8er: C «Füsse passen sich an», Höhe 0, Spur 24.7 cm: Mitte ± 0.5 cm, Tempo ± 12 %, immer ≥ 3 Bodenkontakte
#        (Nur stossen: ± 0.45 cm, Tempo ± 24 %, Kontakte min 1) → C ist deutlich besser (Wertung mit Kontakt-Abzug)
#   4er: nur C rollt mit Höhe 13.9 cm / Spur 33.6 cm sicher (3/3, ± 1 cm, Tempo ± 10 %, aber Kontakte Ø 2.5 / min 1,
#        72 cm/s schnell); A (Höhe 0) ± 0.8 cm, aber zeitweise ohne Bodenkontakt; Nur stossen und B kommen nicht herum
#   6er: C, Höhe 7.1 cm, Spur 24.7 cm: ± 0.6 cm, Tempo ± 6 %, Kontakte min 2 / Ø 3.5 (60 cm/s); Höhe 0: ± 0.6 … 0.9 cm,
#        Tempo ± 11 … 22 % (zwei Messreihen - die Streuung ist gross); Nur stossen ± 0.4 cm, aber Tempo ± 39 %, min 1
#   B (Speichen) rollt bei keiner Variante ganz herum (zu langsam); A ist beim 6er / 8er unruhig (± 2.4 … 3.4 cm)
const RUND_START := {"8": {"ring_methode": "c", "ring_hoehe": 0.0, "spur_rollen": 0.247},
		"4": {"ring_methode": "c", "ring_hoehe": 0.139, "spur_rollen": 0.336},
		"6": {"ring_methode": "c", "ring_hoehe": 0.071, "spur_rollen": 0.247}}
const RUND_VERSUCHE := 3
const RUND_MAX := 40.0                 # s for one full turn, else «zu langsam»
const PANEL_W := 380.0
# Menü aufgeräumt (Besitzer, Fragebogen 28.11.2026 14:49): 5 Reiter statt 9, darin aufklappbare Gruppen wie im Simulator
# (Suchfeld, «Alle zuklappen · Nur Gruppen · Alle aufklappen»); nichts entfernt, nur umsortiert. [id, Name, Symbol]
const TABS := [["fahren", "Fahren"], ["haltung", "Haltung"], ["bauen", "Labor|Bauen"], ["welt", "Welt"], ["messen", "Messen"]]
# die früheren 9 Reiter (/control «tab», ältere Tests, Haken anderer Zweige) -> [neuer Reiter, Gruppe]
const TAB_ALT := {"form": ["bauen", "form"], "gelenke": ["bauen", "gelenke"], "posen": ["haltung", "posen"],
		"bewegen": ["fahren", "gang"], "anzeigen": ["messen", "anzeigen"], "rund": ["messen", "rund"],
		"gelaende": ["welt", "gelaende"], "physik": ["welt", "physik"], "ansicht": ["welt", "ansicht"],
		"ki": ["fahren", "ki"]}
# die Gruppen in den Reitern, in dieser Reihenfolge: [id, Titel, Reiter]
const GRUPPEN := [["gang", "Gangart", "fahren"], ["richtung", "Richtung", "fahren"], ["tempo", "Tempo und Schritt", "fahren"],
		["ring", "Im Ring rollen", "fahren"], ["ki", "Gang-KI", "fahren"], ["steuerung", "Steuerung", "fahren"],
		["posen", "Posen", "haltung"], ["ablaeufe", "Ganze Abläufe", "haltung"], ["koerper", "Körper verschieben", "haltung"],
		["form", "Form", "bauen"], ["gelenke", "Gelenke", "bauen"],
		["gelaende", "Gelände", "welt"], ["physik", "Physik", "welt"], ["ansicht", "Ansicht", "welt"],
		["anzeigen", "Anzeigen", "messen"], ["rund", "Rund rollen", "messen"]]
# Auswahlliste «Modell»: die Reihenfolge; was (noch) nicht in VARIANTEN steht, ist grau
const MODELLE := [["8", "8 Segmente"], ["6", "6 Segmente"], ["4", "4 Segmente"], ["3", "3 Segmente"], ["2", "2 Segmente"],
		["vier", "Vierbeiner"], ["sechs", "Sechsbeiner"]]
const AKZENT := Color("#ef9f27")       # Kopf und Logo: Orange wie die Kupplung (roboter_modell.gd FARBE["kupplung"])
const VIEWS := [["frei", "Frei"], ["seite", "Seite"], ["oben", "Oben"], ["roboter", "Roboter-Kamera"]]
const FORM := [   # [key, name, unit, step]
	["segmente", "Segmente", "", 1.0], ["halbe_breite", "Halbe Breite", "E", 0.01], ["halbe_breite_spitze", "Halbe Breite Spitze", "E", 0.01],
	["laenge_mittelteil", "Länge Mittelteil", "E", 0.01], ["abstand_gelenk", "Abstand im Gelenk", "E", 0.01],
	["oberschenkel", "Oberschenkel", "E", 0.01], ["unterschenkel", "Unterschenkel", "E", 0.01], ["mast_hoehe", "Mast der Kamera", "E", 0.01],
	["massstab", "Massstab (Meter pro Einheit)", "m", 0.005], ["masse_segment", "Masse je Segment", "kg", 0.01],
	["masse_bein", "Masse je Bein", "kg", 0.01]]
const PHYSIK := [["moment_koerper", "Servo-Moment Segmentgelenk", "N·m", 0.1], ["moment_bein", "Servo-Moment Bein", "N·m", 0.05],
	["tempo_servo", "Servo-Tempo", "°/s", 10.0], ["reibung", "Reibung am Boden", "", 0.05]]

var main
var mehr
var layer: CanvasLayer
var win: Control = null
var vpc: SubViewportContainer
var vp: SubViewport
var world: Node3D
var cam: Camera3D
var pip_vp: SubViewport
var pip_cam: Camera3D
var pip_box: Control
var model                              # roboter_modell.gd
var bew                                # roboter_bewegung.gd
var anz                                # roboter_anzeige.gd
var steu                               # roboter_steuerung.gd
var ki                                 # roboter_ki_gang.gd (Gang-KI Stufe 1 + 2)
var ki_lernen = null                   # roboter_ki_lernen.gd (Stufe 3), null wenn es die Datei nicht gibt
var manual := Vector3.ZERO             # Bewegen: x = seitwärts (+ links), y = vor / zurück, z = drehen / Kurve (+ links)
var speed := 0.0                       # measured, m/s (smooth)
var _last_com := Vector3.ZERO
var _press := Vector2.ZERO
var _anz_t := 0.0
var rund_jobs := []                   # Rund rollen: queue [{methode, hoehe, spur, versuch}]
var rund_job := {}                     # the running one (+ phase, t)
var rund_rows := {}                    # key -> [results]
var rund_best := ""
var auto_best := true
var terrain := {}                      # Gelände-Test: {name, ring, t, best, last_t, queue}; empty = none running
var terrain_results := {}              # name -> [ok, text]
const TERRAIN_MAX := 150.0             # s
const TERRAIN_STILL := 15.0            # s without 3 cm progress = stuck
var starts := {}                       # lane -> Transform3D (roboter_gelaende.gd)
var view := "frei"
var tab := "fahren"
var paused := false
var pip := true
var info_on := true                    # the info field top left (status lines)
var touch := false                     # touch screen (or --touch for tests / pictures): touch hints, two-finger gestures
var _touches := {}                     # finger index -> position
var _pinch := 0.0
var follow := true
var gravity := 9.81
var yaw := -35.0
var pitch := 22.0
var dist := 1.9
var target := Vector3(-0.5, 0.1, 0)
var last_pose := "gerade"
var variante := "8"
var _store := {}
var _store_loaded := false
var _dirty_t := -1.0
var _old_ticks := 30
var _old_3d := false
var _w := {}                           # widgets
var _sl := {}                          # servo id -> {sl, val}
var _drag := 0
var _rebuild_t := -1.0
var _ui_t := 0.0
var _panel_on := true
var _gruppen := {}                     # group id -> body (UI.fold_card)
var _panel_w := PANEL_W                # the widest tab (set in _build_ui)
var _such := ""                        # the text in the search field (lower case)


func is_open() -> bool:
	return win != null and is_instance_valid(win)


static func variante_aus(v) -> String:
	"""«6» / «4» / «3» / «2» → so viele Segmente, alles andere («1», «8», leer) → 8 Segmente"""
	var t := str(v).strip_edges()
	return t if t in FEST else "8"


func open() -> void:
	if is_open():
		return
	_load_store()
	if mehr != null:
		mehr.close_window()
		mehr.close_menu()
	layer = CanvasLayer.new()
	layer.layer = 62
	add_child(layer)
	_old_ticks = Engine.physics_ticks_per_second
	Engine.physics_ticks_per_second = TICKS
	touch = DisplayServer.is_touchscreen_available() or "--touch" in OS.get_cmdline_user_args()
	_old_3d = get_viewport().disable_3d
	get_viewport().disable_3d = true                  # the window shows only the lab: the world of MoveEye is not drawn meanwhile
	_build_world()
	steu = STEUERUNG.new()
	steu.lab = self
	steu.laden()
	_build_ui()
	steu.build(_w["area"])
	_start_physics()
	set_view(view)
	set_tab(tab)


func close() -> void:
	if not is_open():
		return
	if steu != null:
		steu.close()
		steu = null
	layer.queue_free()
	layer = null
	win = null
	_save_store()
	model = null
	_sl = {}
	_w = {}
	Engine.physics_ticks_per_second = _old_ticks
	get_viewport().disable_3d = _old_3d


# ---- die Welt ------------------------------------------------------------------------------------------------------------
func _build_world() -> void:
	vp = SubViewport.new()
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_2X
	vp.positional_shadow_atlas_size = 2048
	world = Node3D.new()
	world.name = "roboter_labor"
	vp.add_child(world)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color("#c9d3dc")
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color("#b8c4d0")
	e.ambient_light_energy = 0.45
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.environment = e
	world.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55, -35, 0)
	sun.light_energy = 0.85
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 25.0
	world.add_child(sun)
	starts = GELAENDE.build(world)
	cam = Camera3D.new()
	cam.current = true
	cam.near = 0.02
	cam.far = 120.0
	world.add_child(cam)
	model = MODELL.new()
	model.name = "segmentroboter"
	var sp: Dictionary = (_store.get(variante, {}) as Dictionary).get("p", {})
	for k in sp:
		if MODELL.START.has(k):
			model.p[k] = sp[k]
	if variante in FEST:
		model.p["segmente"] = int(variante)
	elif str(int(model.p["segmente"])) in FEST:
		model.p["segmente"] = 8
	last_pose = str((_store.get(variante, {}) as Dictionary).get("pose", "gerade"))
	var an: Dictionary = (_store.get(variante, {}) as Dictionary).get("ansicht", {})
	pip = bool(an.get("pip", true))
	info_on = bool(an.get("info", true))
	world.add_child(model)
	bew = BEWEGUNG.new()
	bew.m = model
	var rs0: Dictionary = RUND_START.get(variante, {})
	for k in rs0:
		bew.set(k, rs0[k])
	var sb: Dictionary = (_store.get(variante, {}) as Dictionary).get("bew", {})
	for k in BEW_KEYS:
		if sb.has(k):
			bew.set(k, sb[k])
	anz = ANZEIGE.new()
	anz.name = "anzeige"
	anz.m = model
	world.add_child(anz)
	ki = KI.new()
	ki.m = model
	ki.bew = bew
	ki.anz = anz
	ki.labor = self
	bew.ki = ki
	if ResourceLoader.exists(KI_LERNEN):
		ki_lernen = load(KI_LERNEN).new()
		ki_lernen.set("ki", ki)
		ki_lernen.set("labor", self)
		ki.lernen = ki_lernen


func _load_store() -> void:
	if _store_loaded:
		return
	_store_loaded = true
	if FileAccess.file_exists(SPEICHER):
		var d = JSON.parse_string(FileAccess.get_file_as_string(SPEICHER))
		if typeof(d) == TYPE_DICTIONARY:
			_store = d
	variante = variante_aus(_store.get("aktiv", "8"))


func _save_store() -> void:
	if model == null:
		return
	var b := {}
	for k in BEW_KEYS:
		b[k] = bew.get(k)
	var old: Dictionary = _store.get(variante, {})
	_store[variante] = {"p": model.p.duplicate(), "pose": last_pose, "bew": b, "ansicht": {"pip": pip, "info": info_on}, "rund": rund_summary() if not rund_rows.is_empty() else old.get("rund", []),
			"rund_best": rund_best if rund_best != "" else str(old.get("rund_best", ""))}
	_store["aktiv"] = variante
	var f := FileAccess.open(SPEICHER, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(_store, " "))
	_dirty_t = -1.0


func mark_dirty() -> void:
	_dirty_t = 2.0


func set_variante(v: String) -> void:
	"""switch 8 ↔ 4 segments: the current values are kept for later, the other variant comes with its own"""
	v = variante_aus(v)
	if v == variante and is_open():
		return
	var was_open := is_open()
	if was_open:
		_save_store()
		close()
	rund_rows = {}                                   # the measurements belong to their variant (saved above)
	rund_best = ""
	rund_jobs = []
	rund_job = {}
	variante = v
	_store["aktiv"] = v
	if was_open:
		open()


func _start_physics() -> void:
	"""once the viewport is in the tree (joints need node paths): own space settings, then the robot"""
	var sp: RID = vp.find_world_3d().space
	model.space_rid = sp
	PhysicsServer3D.space_set_param(sp, PhysicsServer3D.SPACE_PARAM_SOLVER_ITERATIONS, MODELL.LOESER)
	PhysicsServer3D.area_set_param(sp, PhysicsServer3D.AREA_PARAM_GRAVITY, gravity)
	_rebuild(true)


func _rebuild(new_pose: bool) -> void:
	"""after a change of the shape: build again, the robot stands at the start in the last pose"""
	var keep: Dictionary = {} if new_pose else model.targets()
	model.build(starts.get("start", Transform3D()), {})
	if new_pose or keep.is_empty() or keep.size() != model.servos.size():
		bew.apply(bew.pose(last_pose))
	else:
		bew.apply(keep)
	model.place(true)
	_fill_servo_sliders()
	_paint_ring()


func _physics_process(dt: float) -> void:
	if not is_open() or model == null or paused:
		return
	# keyboard, controller and mouse joystick (roboter_steuerung.gd): smooth [strafe + links, forward, turn + links]
	var wasd: Vector3 = steu.tick(dt) if steu != null else Vector3.ZERO
	if steu != null and steu.koerper:
		steu.koerper_step(dt)                            # «Körper verschieben»: the feet stand, the body moves
	else:
		if wasd != Vector3.ZERO and bew.mode not in ["gang", "ring"]:
			if model.latch["state"] == "locked":
				bew.start_ring()
			else:
				bew.start_gang(bew.gang)
		var c := wasd if wasd != Vector3.ZERO else manual
		bew.cmd = c
		bew.keys = Vector2(clampf(c.z + c.x, -1.0, 1.0), c.y)       # in the ring: A / D and Q / E both steer
		ki.setze_befehl(Vector3(c.y, c.x, c.z))                  # Gang-KI: the drive command (also from the stick / controller)
		ki.step(dt)
		if ki_lernen != null:
			ki_lernen.tick(dt)
		bew.step(dt)
		ki.vorne_neigen()
	model.step(dt)
	if not terrain.is_empty():
		_terrain_step(dt)
	if not rund_job.is_empty() or not rund_jobs.is_empty():
		_rund_step(dt)


func _process(dt: float) -> void:
	if not is_open():
		return
	if _dirty_t > 0.0:
		_dirty_t -= dt
		if _dirty_t <= 0.0:
			_save_store()
	if _rebuild_t > 0.0:
		_rebuild_t -= dt
		if _rebuild_t <= 0.0:
			_rebuild(false)
			_refresh_form_info()
	_camera(dt)
	_layout_overlay()
	if steu != null:
		steu.process(dt)
	_anz_t -= dt
	if _anz_t <= 0.0 and anz != null:
		_anz_t = 0.1
		anz.goal = bew.goal if bew.mode == "gang" and not bew.goal_reached else null
		anz.update_all()
		var c: Vector3 = model.com()
		var dv := Vector2(c.x - _last_com.x, c.z - _last_com.z).length() / 0.1
		speed = lerpf(speed, dv, 0.3) if dv < 3.0 else speed
		_last_com = c
	_ui_t -= dt
	if _ui_t <= 0.0:
		_ui_t = 0.2
		_refresh()


# ---- Kamera ---------------------------------------------------------------------------------------------------------------
func set_view(v: String) -> void:
	view = v if v in VIEWS.map(func(x): return x[0]) else "frei"
	for x in VIEWS:
		var b: Button = _w.get("view_" + x[0])
		if b != null:
			_paint_btn(b, x[0] == view)
	if is_inside_tree():
		for n in get_tree().get_nodes_in_group("roboter_schild"):
			(n as Node3D).visible = view in ["frei", "roboter"]
	_paint_chips()
	if pip_box != null:
		pip_box.visible = pip and view != "roboter"
		pip_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS if pip_box.visible else SubViewport.UPDATE_DISABLED


func _camera(dt: float) -> void:
	if model == null or not model.built_ok:
		return
	var c: Vector3 = model.com()
	if follow:
		target = target.lerp(Vector3(c.x, maxf(0.05, c.y), c.z), clampf(dt * 3.0, 0.0, 1.0))
	var length: float = model.pitch_len() * model.n()
	match view:
		"seite":
			cam.projection = Camera3D.PROJECTION_ORTHOGONAL
			cam.size = maxf(0.4, length * 1.3) * dist / 1.9
			cam.global_transform = Transform3D(Basis(), target + Vector3(0, 0.25, 1.2))   # close: the other lanes lie behind the camera
			cam.look_at(target + Vector3(0, 0.25, 0), Vector3.UP)
		"oben":
			cam.projection = Camera3D.PROJECTION_ORTHOGONAL
			cam.size = maxf(0.4, length * 1.4) * dist / 1.9
			cam.global_transform = Transform3D(Basis(), target + Vector3(0, 9.0, 0.001))
			cam.look_at(target, Vector3.FORWARD)
		"roboter":
			cam.projection = Camera3D.PROJECTION_PERSPECTIVE
			cam.fov = 70.0
			if model.robot_cam != null:
				cam.global_transform = model.robot_cam.global_transform
		_:
			cam.projection = Camera3D.PROJECTION_PERSPECTIVE
			cam.fov = 50.0
			var r := deg_to_rad(yaw)
			var pt := deg_to_rad(pitch)
			var off := Vector3(cos(pt) * sin(r), sin(pt), cos(pt) * cos(r)) * dist
			cam.global_transform = Transform3D(Basis(), target + off)
			cam.look_at(target, Vector3.UP)
	if pip_cam != null and model.robot_cam != null:
		pip_cam.global_transform = model.robot_cam.global_transform


func _view_input(ev: InputEvent) -> void:
	if ev is InputEventScreenTouch:                      # two fingers: pinch = zoom, move = pan (one finger = the mouse)
		var tch := ev as InputEventScreenTouch
		if tch.pressed:
			_touches[tch.index] = tch.position
		else:
			_touches.erase(tch.index)
		_pinch = 0.0
		if _touches.size() >= 2:
			_drag = 0
		return
	if ev is InputEventScreenDrag and _touches.size() >= 2:
		var dr := ev as InputEventScreenDrag
		var old_mid: Vector2 = (_touches.values()[0] + _touches.values()[1]) * 0.5
		_touches[dr.index] = dr.position
		var p: Array = _touches.values()
		var dd: float = (p[0] as Vector2).distance_to(p[1])
		if _pinch > 0.0 and dd > 1.0:
			dist = clampf(dist * _pinch / dd, 0.3, 25.0)
		_pinch = dd
		var mid: Vector2 = ((p[0] as Vector2) + (p[1] as Vector2)) * 0.5
		var rel := mid - old_mid
		follow = false
		target -= (cam.global_transform.basis.x * rel.x - cam.global_transform.basis.y * rel.y) * dist * 0.0016
		return
	if _touches.size() >= 2 and (ev is InputEventMouseMotion or ev is InputEventMouseButton):
		return                                           # the emulated mouse of the first finger does not turn meanwhile
	if ev is InputEventMouseButton:
		var mb := ev as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom(1)
		elif mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom(-1)
		elif mb.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE]:
			_drag = mb.button_index if mb.pressed else 0
			if mb.button_index == MOUSE_BUTTON_LEFT:
				if mb.pressed:
					_press = mb.position
				elif mb.position.distance_to(_press) < 5.0 and view != "roboter":
					click_goal(mb.position)
	elif ev is InputEventMouseMotion and _drag != 0:
		var rel := (ev as InputEventMouseMotion).relative
		if _drag == MOUSE_BUTTON_LEFT and view == "frei":
			yaw -= rel.x * 0.35
			pitch = clampf(pitch + rel.y * 0.3, -5.0, 88.0)
		elif _drag != MOUSE_BUTTON_LEFT or view in ["seite", "oben"]:
			follow = false
			_paint_toggles()
			var k := dist * 0.0016
			var right := cam.global_transform.basis.x
			var upv := cam.global_transform.basis.y
			target -= (right * rel.x - upv * rel.y) * k
			if view == "oben":
				target.y = maxf(target.y, 0.0)


func click_goal(pos: Vector2) -> void:
	"""a short click in the 3D view: the point on the floor becomes the goal of the automatic walk"""
	var o := cam.project_ray_origin(pos)
	var d := cam.project_ray_normal(pos)
	var hit = world.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(o, o + d * 60.0, 1))
	var p: Vector3
	if not hit.is_empty():
		p = hit["position"]
	elif absf(d.y) > 1e-4 and -o.y / d.y > 0.0:
		p = o + d * (-o.y / d.y)
	else:
		return
	set_goal(p)


func set_goal(p: Vector3) -> void:
	bew.set_goal(p)
	_paint_gang()


func zoom(dir: int) -> void:
	dist = clampf(dist * (0.88 if dir > 0 else 1.0 / 0.88), 0.3, 25.0)


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and steu != null:
		steu.loslassen()                                 # nothing stays held when the window loses the focus


func _input(ev: InputEvent) -> void:
	if is_open() and steu != null and steu.input(ev):    # bindings of the profile (roboter_steuerung.gd) first
		get_viewport().set_input_as_handled()
		return
	if not is_open() or not (ev is InputEventKey):
		return
	var k := ev as InputEventKey
	get_viewport().set_input_as_handled()            # the lab has the keyboard while it is open
	if not k.pressed or k.echo or k.ctrl_pressed or k.alt_pressed or k.meta_pressed:
		return
	match k.keycode:
		KEY_ESCAPE:
			close()
		KEY_1:
			set_view("frei")
		KEY_2:
			set_view("seite")
		KEY_3:
			set_view("oben")
		KEY_4:
			set_view("roboter")
		KEY_G:
			if bew.mode == "gang":
				stop_all()
			else:
				bew.start_gang(bew.gang)
				_paint_gang()
		KEY_P:
			set_paused(not paused)
		KEY_F:
			set_hold(not model.hold)
		KEY_K:
			set_pip(not pip)
		KEY_H:
			set_panel(not _panel_on)
		KEY_I:
			set_info(not info_on)
		KEY_PLUS, KEY_KP_ADD, KEY_EQUAL:
			zoom(1)
		KEY_MINUS, KEY_KP_SUBTRACT:
			zoom(-1)


# ---- Aktionen -------------------------------------------------------------------------------------------------------------
func set_paused(on: bool) -> void:
	paused = on
	if model != null and model.space_rid.is_valid():
		PhysicsServer3D.space_set_active(model.space_rid, not on)
	_paint_toggles()


func set_hold(on: bool) -> void:
	model.set_hold(on)
	_paint_toggles()


func set_info(on: bool) -> void:
	info_on = on
	var ip: Control = _w.get("info_box")
	if ip != null:
		ip.visible = on
	_paint_chips()
	_paint_toggles()
	mark_dirty()


func set_panel(on: bool) -> void:
	_panel_on = on
	var p: Control = _w.get("panel")
	if p != null:
		p.visible = on
	_paint_chips()


func set_pip(on: bool) -> void:
	mark_dirty()
	pip = on
	set_view(view)
	_paint_toggles()


func stop_all() -> void:
	bew.stop()
	manual = Vector3.ZERO
	var ts: Dictionary = _w.get("turn_sl", {})
	if not ts.is_empty():
		(ts["sl"] as HSlider).set_value_no_signal(0.0)
	_paint_gang()
	_sync_servo_sliders()


func start_gang(g: String) -> void:
	bew.start_gang(g)
	if manual.y == 0.0 and bew.goal == null:
		manual.y = 1.0
	_paint_gang()


func start_ablauf(name: String) -> void:
	bew.start_ablauf(name)
	_paint_gang()


func reset() -> void:
	bew.stop()
	manual = Vector3.ZERO
	model.place(true)
	follow = true
	_paint_toggles()


func ring_ok() -> bool:
	return model != null and model.ring_ok()


func apply_pose(name: String, snap := false) -> void:
	if name == "ring" and not ring_ok():
		return                                       # 2 / 3 Segmente: kein Ring
	if name != "ring" and not snap and model.latch["state"] != "open":
		ring_oeffnen(name)                                 # never straighten against the closed latch: open it first
		return
	if name == "ring":
		bew.latch_restore()
	last_pose = name
	mark_dirty()
	bew.mode = ""
	bew.goal = null
	bew.apply(bew.pose(name))
	if snap:
		model.place(true)
	_sync_servo_sliders()


func ring_oeffnen(to := "gerade") -> void:
	"""Knopf «Ring öffnen (gerade)» (Besitzer 28.11.2026): Bewegung stoppen, Riegel auf, in 4.5 s weich in die Haltung `to`;
	«Riegel darf schliessen (Ring)» gilt wieder, sobald die Enden weit genug auseinander sind (roboter_bewegung.gd)"""
	manual = Vector3.ZERO
	var ts: Dictionary = _w.get("turn_sl", {})
	if not ts.is_empty():
		(ts["sl"] as HSlider).set_value_no_signal(0.0)
	last_pose = to
	mark_dirty()
	bew.start_oeffnen(to)
	_paint_gang()
	_sync_servo_sliders()


func set_gravity(g: float) -> void:
	gravity = clampf(g, 0.0, 30.0)
	if model != null and model.space_rid.is_valid():
		PhysicsServer3D.area_set_param(model.space_rid, PhysicsServer3D.AREA_PARAM_GRAVITY, gravity)


func set_shape(key: String, v: float) -> void:
	if key == "segmente" and variante in FEST:
		v = float(variante)                          # the 6-, 4-, 3- and 2-segment variants keep their number
	model.set_param(key, v)
	mark_dirty()
	var d: Dictionary = _w.get("form_" + key, {})
	if not d.is_empty() and not is_equal_approx((d["sl"] as HSlider).value, float(model.p[key])):
		(d["sl"] as HSlider).set_value_no_signal(float(model.p[key]))
		(d["val"] as Label).text = (d["fmt"] as Callable).call(float(model.p[key])).strip_edges()
	if key in ["reibung"]:
		for b in model.bodies:
			((b["rb"] as RigidBody3D).physics_material_override as PhysicsMaterial).friction = float(model.p["reibung"])
	elif key in ["moment_koerper", "moment_bein", "tempo_servo"]:
		pass                                         # read every physics step
	else:
		_rebuild_t = 0.4                             # build again when the slider rests
	_refresh_form_info()


# ---- Bedienfeld -----------------------------------------------------------------------------------------------------------
func _build_ui() -> void:
	win = Control.new()
	win.set_anchors_preset(Control.PRESET_FULL_RECT)
	win.theme = main.ui_root.theme if main != null and main.ui_root != null else UI.theme()
	layer.add_child(win)
	var bg := ColorRect.new()
	bg.color = UI.BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	win.add_child(bg)
	var row := HBoxContainer.new()
	row.set_anchors_preset(Control.PRESET_FULL_RECT)
	row.add_theme_constant_override("separation", 0)
	win.add_child(row)
	# 3D view (the overlays are siblings above the container)
	var area := Control.new()
	area.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	area.size_flags_vertical = Control.SIZE_EXPAND_FILL
	area.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(area)
	_w["area"] = area
	vpc = SubViewportContainer.new()
	vpc.stretch = true
	vpc.set_anchors_preset(Control.PRESET_FULL_RECT)
	vpc.mouse_filter = Control.MOUSE_FILTER_STOP
	vpc.gui_input.connect(_view_input)
	vpc.set_meta("rad_zoom", "roboter")
	area.add_child(vpc)
	vpc.add_child(vp)
	_overlay(area)
	# panel
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(PANEL_W, 0)
	panel.add_theme_stylebox_override("panel", UI.box(UI.PANEL, UI.LINE, 0, 10, 1))
	row.add_child(panel)
	_w["panel"] = panel
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 8)
	panel.add_child(pv)
	# Kopf (Besitzer 28.11.2026): eigenes Roboter-Symbol und Name in Orange (wie die Kupplung), rechts die Nummer des Simulators
	var hd := HBoxContainer.new()
	hd.add_theme_constant_override("separation", 8)
	pv.add_child(hd)
	var logo := _icon("roboter", AKZENT, Vector2(26, 26))
	logo.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hd.add_child(logo)
	var tl := Label.new()
	tl.text = T.t("Roboter-Labor")
	tl.add_theme_font_override("font", UI.heading_font())
	tl.add_theme_font_size_override("font_size", 17)
	tl.add_theme_color_override("font_color", AKZENT)
	tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hd.add_child(tl)
	_w["titel"] = tl
	var ver := UI.small(T.t("Sim %s") % sim_version())
	ver.autowrap_mode = TextServer.AUTOWRAP_OFF
	ver.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hd.add_child(ver)
	_w["version"] = ver
	var x := _close_btn(UI.TXT, T.t("Schliessen (Esc)"), close)
	x.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hd.add_child(x)
	var akz := ColorRect.new()                        # a thin orange line under the head: the lab at a glance
	akz.color = AKZENT
	akz.custom_minimum_size = Vector2(0, 2)
	pv.add_child(akz)
	var sub := UI.small(T.t("Segment-Roboter – Form, Gelenke und Physik ausprobieren"))
	pv.add_child(sub)
	# Modell: one list with a small picture of each model (before: 3 buttons)
	var mr := HBoxContainer.new()
	mr.add_theme_constant_override("separation", 8)
	pv.add_child(mr)
	var ml := Label.new()
	ml.text = T.t("Modell")
	mr.add_child(ml)
	var ob := OptionButton.new()
	ob.focus_mode = Control.FOCUS_NONE
	ob.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ob.custom_minimum_size = Vector2(0, 36)
	ob.expand_icon = false
	var ids := VARIANTEN.map(func(x): return x[0])
	var liste := []
	for mm in MODELLE:
		liste.append(mm)
	for vv in VARIANTEN:                              # a variant that MODELLE does not know yet comes at the end
		if not MODELLE.any(func(x): return x[0] == vv[0]):
			liste.append(vv)
	for i in liste.size():
		var mid: String = liste[i][0]
		ob.add_icon_item(modell_bild(mid), T.t(liste[i][1]), i)
		ob.set_item_metadata(i, mid)
		ob.set_item_disabled(i, not mid in ids)
		if mid == variante:
			ob.select(i)
	ob.item_selected.connect(func(i: int): set_variante.call_deferred(str(ob.get_item_metadata(i))))
	mr.add_child(ob)
	_w["modell"] = ob
	# 5 tabs, each with a drawn symbol (the font has no emoji)
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 4)
	pv.add_child(tabs)
	for tb in TABS:
		var b := Button.new()
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(0, 50)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.tooltip_text = tx(tb[1])
		b.pressed.connect(set_tab.bind(tb[0]))
		var bv := VBoxContainer.new()
		bv.set_anchors_preset(Control.PRESET_FULL_RECT)
		bv.alignment = BoxContainer.ALIGNMENT_CENTER
		bv.add_theme_constant_override("separation", 1)
		bv.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.add_child(bv)
		var ic := _icon("tab_" + tb[0], UI.TXT, Vector2(22, 22))
		ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		bv.add_child(ic)
		var lb := Label.new()
		lb.text = tx(tb[1])
		lb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lb.add_theme_font_size_override("font_size", 12)
		lb.mouse_filter = Control.MOUSE_FILTER_IGNORE
		bv.add_child(lb)
		b.set_meta("icon", ic)
		b.set_meta("label", lb)
		tabs.add_child(b)
		_w["tab_" + tb[0]] = b
	# search and the three fold buttons, the same parts as in the menu of the simulator (ui_style.gd)
	var tbar := HBoxContainer.new()
	tbar.add_theme_constant_override("separation", 4)
	pv.add_child(tbar)
	var se := UI.search_field(T.t("Einstellung suchen …"))
	se.custom_minimum_size = Vector2(0, 36)
	se.text_changed.connect(suche)
	tbar.add_child(se)
	_w["suche"] = se
	for fk in [["close", "Alle zuklappen"], ["groups", "Nur Gruppen"], ["open", "Alle aufklappen"]]:
		var how: String = fk[0]
		var fb := UI.icon_button(how, T.t(fk[1]))
		fb.custom_minimum_size = Vector2(36, 36)
		fb.pressed.connect(func(): fold_all(how))
		tbar.add_child(fb)
		_w["fold_" + how] = fb
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sc.set_meta("rad_scroll", true)
	pv.add_child(sc)
	_w["scroll"] = sc
	var body := VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 8)
	sc.add_child(body)
	var none := UI.small(T.t("Kein Treffer"))
	none.visible = false
	body.add_child(none)
	_w["kein_treffer"] = none
	for tb in TABS:
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 8)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		body.add_child(v)
		_w["page_" + tb[0]] = v
	_gruppen = {}
	for g in GRUPPEN:
		gruppe(g[0], g[1], g[2])
	_page_bewegen(gruppe("gang"))
	_page_posen(gruppe("posen"))
	_page_form(gruppe("form"))
	_page_gelenke(gruppe("gelenke"))
	_page_gelaende(gruppe("gelaende"))
	_page_physik(gruppe("physik"))
	_page_ansicht(gruppe("ansicht"))
	_page_anzeigen(gruppe("anzeigen"))
	_page_rund(gruppe("rund"))
	_page_steuerung()
	ki.baue_seite(gruppe("ki"), self)                  # Gang-KI (sim-gang-ki-a / -b): group «Gang-KI» in Fahren
	_paint_ring()
	for tb in TABS:                                   # one width for all tabs (the widest), the panel does not jump
		(_w["page_" + tb[0]] as Control).visible = true
	_panel_w = maxf(PANEL_W, panel.get_combined_minimum_size().x)
	var keys := UI.small(T.t("W / S vor / zurück · A / D seitwärts · Q / E drehen · Leertaste Stopp · G Gehen · 1 – 4 Ansicht · R neu aufstellen · P anhalten · F festhalten · K Kamerabild · I Info · H Bedienfeld · Esc schliessen"))
	pv.add_child(keys)


func _overlay(area: Control) -> void:
	var sp := PanelContainer.new()
	sp.position = Vector2(10, 8)
	sp.add_theme_stylebox_override("panel", UI.box(Color(1, 1, 1, 0.72), Color(1, 1, 1, 0.0), 8, 8, 0))
	sp.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.add_child(sp)
	_w["info_box"] = sp
	var sh := HBoxContainer.new()
	sh.add_theme_constant_override("separation", 6)
	sp.add_child(sh)
	var st := Label.new()
	st.add_theme_font_size_override("font_size", 14)
	st.add_theme_color_override("font_color", Color("#16202c"))
	st.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sh.add_child(st)
	_w["status"] = st
	var sx := _close_btn(Color("#16202c"), T.t("Info ausblenden (I)"), func(): set_info(false))
	sx.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	sh.add_child(sx)
	sp.visible = info_on
	# the bar at the bottom: views, show / hide, hints - it wraps on narrow screens
	var vb := HFlowContainer.new()
	vb.add_theme_constant_override("h_separation", 4)
	vb.add_theme_constant_override("v_separation", 4)
	vb.anchor_left = 0.0
	vb.anchor_right = 1.0
	vb.anchor_top = 1.0
	vb.anchor_bottom = 1.0
	vb.offset_left = 12
	vb.offset_right = -12
	vb.offset_top = -10
	vb.offset_bottom = -10
	vb.grow_vertical = Control.GROW_DIRECTION_BEGIN
	vb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.add_child(vb)
	_w["viewbar"] = vb
	for v in VIEWS:
		var b := Button.new()
		b.text = T.t(v[1])
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(set_view.bind(v[0]))
		b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		vb.add_child(b)
		_w["view_" + v[0]] = b
	for c in [["chip_pip", "Kamera", "Kamerabild ein / aus (K)", func(): set_pip(not pip)],
			["chip_info", "Info", "Info-Feld ein / aus (I)", func(): set_info(not info_on)],
			["chip_panel", "Bedienfeld", "Bedienfeld ein / aus (H)", func(): set_panel(not _panel_on)]]:
		var b := Button.new()
		b.text = T.t(c[1])
		b.tooltip_text = T.t(c[2])
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(c[3])
		b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		vb.add_child(b)
		_w[c[0]] = b
	var hint := UI.small(T.t("1 Finger: drehen · 2 Finger: zoomen, verschieben") if touch
			else T.t("ziehen = drehen · rechts ziehen = verschieben · Rad = zoomen"), Color("#2a3644"))
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint.custom_minimum_size = Vector2(160, 0)
	hint.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hint.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	vb.add_child(hint)
	_w["hint"] = hint
	# the picture of the front camera (bottom right of the view, smaller on narrow screens)
	pip_vp = SubViewport.new()
	pip_vp.size = Vector2i(320, 200)
	pip_vp.world_3d = vp.find_world_3d()
	pip_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	pip_cam = Camera3D.new()
	pip_cam.fov = 70.0
	pip_cam.near = 0.01
	pip_cam.current = true
	pip_vp.add_child(pip_cam)
	add_child_pip()
	var box := PanelContainer.new()
	box.add_theme_stylebox_override("panel", UI.box(UI.PANEL, UI.ACC, 8, 4, 2))
	box.anchor_left = 1.0
	box.anchor_right = 1.0
	box.anchor_top = 1.0
	box.anchor_bottom = 1.0
	box.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	box.grow_vertical = Control.GROW_DIRECTION_BEGIN
	box.offset_right = -12
	box.offset_left = -12
	box.offset_bottom = -60
	box.offset_top = -60
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.add_child(box)
	var bv := VBoxContainer.new()
	box.add_child(bv)
	var ch := HBoxContainer.new()
	bv.add_child(ch)
	var cl := UI.small(T.t("Roboter-Kamera"), UI.TXT)
	cl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ch.add_child(cl)
	ch.add_child(_close_btn(UI.TXT, T.t("Kamerabild ausblenden (K)"), func(): set_pip(false)))
	var tr := TextureRect.new()
	tr.texture = pip_vp.get_texture()
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_SCALE
	tr.custom_minimum_size = Vector2(320, 200)
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bv.add_child(tr)
	_w["pip_tex"] = tr
	pip_box = box


func _close_btn(col: Color, tip: String, cb: Callable) -> Button:
	"""a small drawn cross to hide a field (the font has no «✕»; bigger for a finger on touch screens)"""
	var b := Button.new()
	b.flat = true
	b.tooltip_text = tip
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_filter = Control.MOUSE_FILTER_STOP
	b.custom_minimum_size = Vector2(36, 32) if touch else Vector2(22, 20)
	var d := _icon("kreuz", col, Vector2.ZERO)
	d.set_anchors_preset(Control.PRESET_FULL_RECT)
	b.add_child(d)
	b.pressed.connect(cb)
	return b


static func tx(de: String) -> String:
	"""T.t with a context for a word that means something else elsewhere: «Labor|Bauen» = «Bauen» here (en «Build»,
	not «Build yourself» of Mehr → Bauen); in German the part before «|» is dropped"""
	var s := T.t(de)
	return s.substr(s.find("|") + 1) if s.begins_with("Labor|") else s


func sim_version() -> String:
	"""the number of the simulator (main.gd VERSION) for the head of the lab"""
	var s: Script = main.get_script() if main != null else null
	if s == null:
		s = load("res://scripts/main.gd")
	return str(s.get_script_constant_map().get("VERSION", "")) if s != null else ""


func _icon(kind: String, col: Color, sz: Vector2) -> Control:
	"""a drawn symbol (no font needed - the same on every PC); col in meta «col», redraw after a change"""
	var d := Control.new()
	d.custom_minimum_size = sz
	d.mouse_filter = Control.MOUSE_FILTER_IGNORE
	d.set_meta("col", col)
	d.draw.connect(func(): draw_icon(d, kind, d.get_meta("col")))
	return d


static func draw_icon(d: Control, kind: String, col: Color) -> void:
	var c := d.size / 2.0
	var s := minf(d.size.x, d.size.y) / 22.0              # drawn for 22 px
	var w := 2.0 * maxf(0.8, s)
	match kind:
		"roboter":                                       # the logo: head with two eyes and an antenna, the body as a segment chain
			d.draw_rect(Rect2(c + Vector2(-7, -6) * s, Vector2(14, 9) * s), col, false, w)
			d.draw_circle(c + Vector2(-3, -1.5) * s, 1.6 * s, col)
			d.draw_circle(c + Vector2(3, -1.5) * s, 1.6 * s, col)
			d.draw_line(c + Vector2(0, -6) * s, c + Vector2(0, -9.5) * s, col, w)
			d.draw_circle(c + Vector2(0, -10) * s, 1.5 * s, col)
			for i in 3:
				d.draw_rect(Rect2(c + Vector2(-8.5 + i * 6.0, 5) * s, Vector2(5, 4) * s), col)
			d.draw_line(c + Vector2(-9, 9) * s, c + Vector2(-10.5, 11) * s, col, w * 0.7)
			d.draw_line(c + Vector2(9, 9) * s, c + Vector2(10.5, 11) * s, col, w * 0.7)
		"kreuz":
			d.draw_line(c + Vector2(-4, -4) * s, c + Vector2(4, 4) * s, col, w, true)
			d.draw_line(c + Vector2(-4, 4) * s, c + Vector2(4, -4) * s, col, w, true)
		"tab_fahren":                                    # joystick: base, stick, knob
			d.draw_rect(Rect2(c + Vector2(-8, 5) * s, Vector2(16, 4) * s), col, false, w)
			d.draw_line(c + Vector2(0, 5) * s, c + Vector2(2.5, -3) * s, col, w)
			d.draw_circle(c + Vector2(3, -5) * s, 3.2 * s, col)
		"tab_haltung":                                   # a standing person
			d.draw_circle(c + Vector2(0, -7.5) * s, 2.6 * s, col)
			d.draw_line(c + Vector2(0, -4) * s, c + Vector2(0, 3) * s, col, w)
			d.draw_line(c + Vector2(-6, -1.5) * s, c + Vector2(6, -1.5) * s, col, w)
			d.draw_line(c + Vector2(0, 3) * s, c + Vector2(-4, 10) * s, col, w)
			d.draw_line(c + Vector2(0, 3) * s, c + Vector2(4, 10) * s, col, w)
		"tab_bauen":                                     # a wrench
			d.draw_line(c + Vector2(-7, 7) * s, c + Vector2(2, -2) * s, col, w * 1.5, true)
			d.draw_arc(c + Vector2(4.5, -4.5) * s, 4.4 * s, -PI / 4.0 + 0.95, -PI / 4.0 + TAU - 0.95, 16, col, w * 1.1, true)
		"tab_welt":                                      # a globe
			d.draw_arc(c, 8.5 * s, 0, TAU, 32, col, w, true)
			d.draw_line(c + Vector2(-8.5, 0) * s, c + Vector2(8.5, 0) * s, col, w * 0.7)
			var pts := PackedVector2Array()
			for i in 17:
				var a := -PI / 2.0 + PI * i / 16.0
				pts.append(c + Vector2(cos(a) * 4.0, sin(a) * 8.5) * s)
			d.draw_polyline(pts, col, w * 0.7, true)
			var pts2 := PackedVector2Array()
			for p in pts:
				pts2.append(Vector2(2.0 * c.x - p.x, p.y))
			d.draw_polyline(pts2, col, w * 0.7, true)
		"tab_messen":                                    # bar chart
			d.draw_line(c + Vector2(-9, 9) * s, c + Vector2(9, 9) * s, col, w * 0.7)
			for e in [[-7.0, 6.0], [-2.0, 11.0], [3.0, 16.0]]:
				d.draw_rect(Rect2(c + Vector2(e[0], 8.0 - e[1]) * s, Vector2(4, e[1]) * s), col)
		"stopp":
			d.draw_rect(Rect2(c - Vector2(5, 5) * s, Vector2(10, 10) * s), col)
		"dreh_l", "dreh_r":                              # turn on the spot: an arc with an arrow head (clockwise = right)
			var mx := -1.0 if kind == "dreh_l" else 1.0          # left = the mirror picture
			var pts := PackedVector2Array()
			var a0 := -PI * 0.85
			var a1 := PI * 0.45
			for k in 21:
				var a := lerpf(a0, a1, k / 20.0)
				pts.append(c + Vector2(cos(a) * mx, sin(a)) * 6.5 * s)
			d.draw_polyline(pts, col, w, true)
			var endp := c + Vector2(cos(a1) * mx, sin(a1)) * 6.5 * s
			var tang := Vector2(-sin(a1) * mx, cos(a1))
			var nrm := Vector2(-tang.y, tang.x)
			d.draw_colored_polygon(PackedVector2Array([endp + tang * 4.0 * s, endp + nrm * 3.2 * s, endp - nrm * 3.2 * s]), col)
		_:
			if kind.begins_with("pfeil"):                # «pfeil<grad>»: 0 = up, 90 = right ...
				var a := deg_to_rad(float(kind.substr(5)))
				var dir := Vector2(sin(a), -cos(a))
				var nrm := Vector2(-dir.y, dir.x)
				d.draw_line(c - dir * 6.5 * s, c + dir * 2.0 * s, col, w, true)
				d.draw_colored_polygon(PackedVector2Array([c + dir * 7.5 * s, c + dir * 1.0 * s + nrm * 5.0 * s,
						c + dir * 1.0 * s - nrm * 5.0 * s]), col)


static func modell_bild(id: String) -> ImageTexture:
	"""a small picture of a model for the list «Modell» (seen from above: segments in orange, legs grey)"""
	var w := 44
	var h := 22
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var seg := Color("#ef9f27")
	var leg := Color("#8a9bb0")
	if id.is_valid_int():
		var n := int(id)
		var sw := mini(9, int(floor(40.0 / n)) - 1)
		var x0 := int((w - n * (sw + 1)) / 2.0)
		for i in n:
			var x := x0 + i * (sw + 1)
			img.fill_rect(Rect2i(x + int(sw / 2.0), 2, 1, 4), leg)
			img.fill_rect(Rect2i(x + int(sw / 2.0), h - 6, 1, 4), leg)
			img.fill_rect(Rect2i(x, 6, sw, h - 12), seg)
	else:
		var legs := 3 if id == "sechs" else 2
		img.fill_rect(Rect2i(8, 7, 28, 8), seg)
		img.fill_rect(Rect2i(34, 8, 6, 6), seg.darkened(0.25))   # head
		for i in legs:
			var x := 11 + int(i * 20.0 / maxf(1.0, legs - 1))
			img.fill_rect(Rect2i(x, 1, 2, 6), leg)
			img.fill_rect(Rect2i(x, h - 7, 2, 6), leg)
	return ImageTexture.create_from_image(img)


func gruppe(id: String, title := "", tab_id := "") -> VBoxContainer:
	"""the body of a group (a fold card like in the simulator); made the first time with title and tab"""
	if _gruppen.has(id):
		return _gruppen[id]
	if tab_id == "":
		for g in GRUPPEN:
			if g[0] == id:
				title = g[1]
				tab_id = g[2]
		if tab_id == "":
			tab_id = "fahren"
	var pg: VBoxContainer = _w["page_" + tab_id]
	var b := UI.fold_card(pg, T.t(title if title != "" else id), true)
	b.set_meta("gruppe", id)
	b.set_meta("reiter", tab_id)
	_gruppen[id] = b
	return b


func gruppe_reiter(id: String) -> String:
	var b: Control = _gruppen.get(id)
	return str(b.get_meta("reiter", "")) if b != null else ""


func fold_all(how: String) -> void:
	"""«close» = all groups shut, «groups» = groups open and their parts shut, «open» = everything open (as in the simulator)"""
	for id in _gruppen:
		var b: Control = _gruppen[id]
		UI.set_open(b, how != "close")
		for sb in _sub_folds(b):
			UI.set_sub_open(sb, how == "open")


func _sub_folds(n: Node) -> Array:
	var out := []
	for ch in n.get_children():
		if ch is Control and (ch as Control).has_meta("fold") and (ch as Control).has_meta("paint"):
			out.append(ch)
		out.append_array(_sub_folds(ch))
	return out


static func texte(n: Node) -> String:
	"""every visible word inside a node (labels, buttons, switches, tooltips) - for the search"""
	var t := ""
	if n is Label:
		t += (n as Label).text + " "
	elif n is Button:
		t += (n as Button).text + " "
	if n is Control:
		t += (n as Control).tooltip_text + " "
	for ch in n.get_children():
		t += texte(ch)
	return t


func suche(q: String) -> void:
	"""type into the search field: the matching rows of every tab stay, their groups open; empty = as before"""
	q = q.strip_edges().to_lower()
	_such = q
	var any := false
	for id in _gruppen:
		var b: Control = _gruppen[id]
		var card: Control = b.get_meta("card")
		var title_hit := q != "" and str(b.get_meta("title", "")).to_lower().contains(q)
		var hit := false
		for row in b.get_children():
			if not row is Control:
				continue
			var r := row as Control
			if q == "":
				if r.has_meta("such_aus"):
					r.visible = true
					r.remove_meta("such_aus")
				continue
			var ok := title_hit or texte(r).to_lower().contains(q)
			if ok:
				hit = true
				if r.has_meta("such_aus"):
					r.visible = true
					r.remove_meta("such_aus")
				for sb in _sub_folds(r):
					if texte(sb).to_lower().contains(q):
						UI.set_sub_open(sb, true)
			elif r.visible:
				r.visible = false
				r.set_meta("such_aus", true)
		card.visible = q == "" or hit
		if hit:
			any = true
			UI.set_open(b, true)
	var none: Control = _w.get("kein_treffer")
	if none != null:
		none.visible = q != "" and not any
	set_tab(tab)


func compact() -> bool:
	"""narrow screen (phone across) or touch: the camera picture smaller"""
	var a: Control = _w.get("area")
	return touch or (a != null and a.size.x < 900.0) or get_viewport().get_visible_rect().size.y < 600.0


func _layout_overlay() -> void:
	"""every frame (cheap): the size of the camera picture and its place above the bar"""
	var tr: TextureRect = _w.get("pip_tex")
	var vb: Control = _w.get("viewbar")
	if tr == null or vb == null or pip_box == null:
		return
	var p: Control = _w.get("panel")
	if p != null:                                     # phone across: a narrower panel, more of the view
		var pw := 320.0 if get_viewport().get_visible_rect().size.x < 1000.0 else _panel_w
		if p.custom_minimum_size.x != pw:
			p.custom_minimum_size = Vector2(pw, 0)
	var sz := Vector2(176, 110) if compact() else Vector2(320, 200)
	if tr.custom_minimum_size != sz:
		tr.custom_minimum_size = sz
		pip_box.reset_size()
	var up: float = steu.lift() if steu != null else 0.0      # above the drive bar (roboter_steuerung.gd)
	if vb.offset_bottom != -10.0 - up:
		vb.offset_bottom = -10.0 - up
		vb.offset_top = -10.0 - up
	pip_box.offset_bottom = -(vb.size.y + 18.0 + up)
	pip_box.offset_top = pip_box.offset_bottom
	pip_box.offset_left = pip_box.offset_right


func _paint_chips() -> void:
	for c in [["chip_pip", pip], ["chip_info", info_on], ["chip_panel", _panel_on]]:
		var b: Button = _w.get(c[0])
		if b != null:
			_paint_btn(b, bool(c[1]))


func add_child_pip() -> void:
	layer.add_child(pip_vp)                          # not inside a container: it renders by itself


func set_tab(t: String) -> void:
	"""one of the 5 tabs; an old name (form, posen, bewegen …) opens its new tab and its group"""
	var grp := ""
	if TAB_ALT.has(t):
		grp = TAB_ALT[t][1]
		t = TAB_ALT[t][0]
	tab = t if t in TABS.map(func(x): return x[0]) else "fahren"
	for tb in TABS:
		var pg: Control = _w.get("page_" + tb[0])
		if pg != null:
			pg.visible = tb[0] == tab or _such != ""      # while searching: the hits of every tab
		var b: Button = _w.get("tab_" + tb[0])
		if b != null:
			_paint_tab(b, tb[0] == tab and _such == "")
	if grp != "" and _gruppen.has(grp):
		UI.set_open(_gruppen[grp], true)
	_sync_servo_sliders()


func _paint_tab(b: Button, on: bool) -> void:
	"""a tab: blue when active (like the active states in the simulator), symbol and name white"""
	_paint_btn(b, on)
	var col := Color.WHITE if on else UI.TXT
	var ic: Control = b.get_meta("icon", null)
	if ic != null:
		ic.set_meta("col", col)
		ic.queue_redraw()
	var lb: Label = b.get_meta("label", null)
	if lb != null:
		lb.add_theme_color_override("font_color", col)


func _ring_need(c: Control) -> void:
	"""a control that needs the ring (≥ 4 segments): greyed out with a short hint at 2 / 3 segments"""
	if not _w.has("ring_need"):
		_w["ring_need"] = []
	_w["ring_need"].append(c)


func _ring_hint(pg: Control) -> void:
	var l := UI.small(T.t("Ring braucht mindestens 4 Segmente"), UI.ORG)
	pg.add_child(l)
	if not _w.has("ring_hints"):
		_w["ring_hints"] = []
	_w["ring_hints"].append(l)


func _paint_ring() -> void:
	"""Ring-Knöpfe nach der Segmentzahl sperren / freigeben, Namen der Gangarten (4 Beine: Trab)"""
	var ok := ring_ok()
	for c in _w.get("ring_need", []):
		if not is_instance_valid(c):
			continue
		if c is BaseButton:
			(c as BaseButton).disabled = not ok
		elif c is Range:
			(c as Range).editable = ok
		if not (c as Control).has_meta("tip0"):
			(c as Control).set_meta("tip0", (c as Control).tooltip_text)     # keep an own tooltip (e.g. «Ring öffnen»)
		(c as Control).tooltip_text = str((c as Control).get_meta("tip0")) if ok else T.t("Ring braucht mindestens 4 Segmente")
	for l in _w.get("ring_hints", []):
		if is_instance_valid(l):
			(l as Control).visible = not ok
	var tr: CheckButton = _w.get("terrain_ring")
	if tr != null and not ok:
		tr.set_pressed_no_signal(false)
	for g in BEWEGUNG.GAENGE:
		var b: Button = _w.get("gang_" + g[0])
		if b != null:
			b.text = gang_name(g[0])


func gang_name(g: String) -> String:
	"""shown name of a gait: with 4 legs (2 segments) the «Dreifuss» is a trot"""
	if g == "dreifuss" and model != null and model.n() == 2:
		return T.t("Trab (diagonal)")
	for e in BEWEGUNG.GAENGE:
		if e[0] == g:
			return T.t(e[1])
	return g


func _paint_btn(b: Button, on: bool) -> void:
	for st in ["normal", "hover", "pressed", "focus"]:
		b.add_theme_stylebox_override(st, UI.box(UI.ACC if on else UI.FIELD, UI.ACC if on else UI.LINE, 8, 6, 1))
	b.add_theme_color_override("font_color", Color.WHITE if on else UI.TXT)


func _slider(parent: Control, title: String, lo: float, hi: float, stp: float, val: float, unit: String, cb: Callable) -> Dictionary:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 0)
	parent.add_child(v)
	var h := HBoxContainer.new()
	v.add_child(h)
	var l := Label.new()
	l.text = title
	l.add_theme_font_size_override("font_size", 13)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.clip_text = true
	h.add_child(l)
	var vl := Label.new()
	vl.add_theme_font_size_override("font_size", 13)
	vl.add_theme_color_override("font_color", UI.MUT)
	h.add_child(vl)
	var sl := HSlider.new()
	sl.min_value = lo
	sl.max_value = hi
	sl.step = stp
	sl.value = val
	sl.focus_mode = Control.FOCUS_NONE
	v.add_child(sl)
	var fmt := func(x: float) -> String:
		if stp >= 1.0:
			return "%d %s" % [int(round(x)), unit]
		return ("%.3f %s" if stp < 0.01 else "%.2f %s") % [x, unit]
	vl.text = fmt.call(val).strip_edges()
	sl.value_changed.connect(func(x: float):
		vl.text = fmt.call(x).strip_edges()
		cb.call(x))
	return {"sl": sl, "val": vl, "box": v, "fmt": fmt, "title": l}


func _toggle(parent: Control, title: String, on: bool, cb: Callable) -> CheckButton:
	var c := CheckButton.new()
	c.text = title
	c.button_pressed = on
	c.focus_mode = Control.FOCUS_NONE
	c.toggled.connect(cb)
	parent.add_child(c)
	return c


func _button(parent: Control, title: String, cb: Callable, primary := false) -> Button:
	var b := Button.new()
	b.text = title
	b.focus_mode = Control.FOCUS_NONE
	b.pressed.connect(cb)
	if primary:
		UI.primary(b)
	parent.add_child(b)
	return b


func _page_form(pg: VBoxContainer) -> void:
	pg.add_child(UI.small(T.t("Startwerte aus modell.json (Einheiten der Vorlage, «E»). Nach einer Änderung baut das Labor den Roboter neu auf.")))
	for f in FORM:
		var g: Array = MODELL.GRENZEN[f[0]]
		var key: String = f[0]
		_w["form_" + key] = _slider(pg, T.t(f[1]), g[0], g[1], f[3], float(model.p[key]), f[2], func(x: float): set_shape(key, x))
		if key == "segmente" and variante in FEST:
			(_w["form_" + key]["sl"] as HSlider).editable = false
			(_w["form_" + key]["title"] as Label).text = T.t("Segmente (fest bei dieser Variante)")
	var info := UI.small("", UI.TXT)
	pg.add_child(info)
	_w["form_info"] = info
	_button(pg, T.t("Startwerte (modell.json)"), func():
		for k in MODELL.START:
			model.p[k] = MODELL.START[k]
		if variante in FEST:
			model.p["segmente"] = int(variante)
		for f in FORM:
			(_w["form_" + f[0]]["sl"] as HSlider).set_value_no_signal(float(model.p[f[0]]))
			(_w["form_" + f[0]]["val"] as Label).text = (_w["form_" + f[0]]["fmt"] as Callable).call(float(model.p[f[0]])).strip_edges()
		_rebuild(true)
		_refresh_form_info())
	_refresh_form_info()


func _refresh_form_info() -> void:
	var l: Label = _w.get("form_info")
	if l == null or model == null:
		return
	var N: int = model.n()
	var length: float = model.pitch_len() * N
	var legs: float = model.u("oberschenkel") + model.u("unterschenkel")
	var mass: float = float(model.p["masse_segment"]) * N + float(model.p["masse_bein"]) * 2 * N
	l.text = T.t("Länge %.2f m · Breite %.2f m · Bein %.2f m · Masse %.2f kg · %d Antriebe") % [length, model.u("halbe_breite") * 2,
			legs, mass, model.actuator_count()]


func _page_gelenke(pg: VBoxContainer) -> void:
	pg.add_child(UI.small(T.t("Jedes Gelenk von Hand: Soll (Regler) und Ist (Zahl rechts). Rot = Servo überlastet.")))
	_w["servo_box"] = pg


func _fill_servo_sliders() -> void:
	var rh: Dictionary = _w.get("rund_h", {})
	if not rh.is_empty() and model.built_ok:               # the reachable ride height is known only once the robot is built
		(rh["sl"] as HSlider).max_value = maxf(0.5, bew.ring_height_max() * 100.0)
	var pg: VBoxContainer = _w.get("servo_box")
	if pg == null:
		return
	for c in pg.get_children():
		if c.has_meta("servo_ui"):
			pg.remove_child(c)
			c.queue_free()
	_sl = {}
	var top := VBoxContainer.new()
	top.set_meta("servo_ui", true)
	pg.add_child(top)
	_servo_slider(top, "pan", T.t("Kamera schwenken"))
	var lt := _toggle(top, T.t("Riegel darf schliessen (Ring)"), model.latch_wanted if not bew.latch_wait else bew.latch_back, func(on: bool):
		if bew.latch_wait:
			bew.latch_back = on                            # the ring is opening: the switch counts once the ends are apart
		else:
			model.latch_wanted = on)
	_w["latch_ok"] = lt
	var N: int = model.n()
	for i in range(N - 1):
		var b := UI.sub_fold(pg, T.t("Segmentgelenk %d (zwischen Segment %d und %d)") % [i + 1, i + 1, i + 2], i == 0)
		(b.get_meta("wrap") as Control).set_meta("servo_ui", true)
		_servo_slider(b, "sp%d" % i, T.t("hoch / runter"))
		_servo_slider(b, "sy%d" % i, T.t("links / rechts"))
	for i in range(N):
		var b := UI.sub_fold(pg, T.t("Beine an Segment %d") % (i + 1), false)
		(b.get_meta("wrap") as Control).set_meta("servo_ui", true)
		for sd in ["l", "r"]:
			var side := T.t("links") if sd == "l" else T.t("rechts")
			_servo_slider(b, "hy%d%s" % [i, sd], "%s · %s" % [side, T.t("Hüfte vor / zurück")])
			_servo_slider(b, "hp%d%s" % [i, sd], "%s · %s" % [side, T.t("Hüfte hoch / runter")])
			_servo_slider(b, "kn%d%s" % [i, sd], "%s · %s" % [side, T.t("Knie")])


func _servo_slider(parent: Control, id: String, title: String) -> void:
	var si: int = model.servo_index(id)
	if si < 0:
		return
	var sv: Dictionary = model.servos[si]
	var d := _slider(parent, title, float(sv["min"]), float(sv["max"]), 1.0, float(sv["target"]), "°", func(x: float):
		model.set_target(id, x)
		bew.mode = ""
		last_pose = "")
	_sl[id] = d


func _sync_servo_sliders() -> void:
	if model == null:
		return
	for id in _sl:
		var si: int = model.servo_index(id)
		if si >= 0:
			(_sl[id]["sl"] as HSlider).set_value_no_signal(float(model.servos[si]["target"]))


func _page_posen(pg: VBoxContainer) -> void:
	pg.add_child(UI.small(T.t("Fertige Posen: die Servos fahren mit ihrem Tempo hin (die Physik rechnet mit). «Sofort» setzt den Roboter ohne Weg in die Pose.")))
	var snap := CheckButton.new()
	snap.text = T.t("Sofort (ohne Weg)")
	snap.focus_mode = Control.FOCUS_NONE
	var gr := GridContainer.new()
	gr.columns = 2
	gr.add_theme_constant_override("h_separation", 6)
	gr.add_theme_constant_override("v_separation", 6)
	pg.add_child(gr)
	for ps in BEWEGUNG.POSEN:
		var pname: String = ps[0]
		var b := _button(gr, T.t(ps[1]), func(): apply_pose(pname, snap.button_pressed))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_w["pose_" + pname] = b
		if pname == "ring":
			_ring_need(b)
	_ring_hint(pg)
	pg.add_child(snap)
	_w["snap"] = snap
	var ob := _button(pg, T.t("Ring öffnen (gerade)"), func(): ring_oeffnen("gerade"))
	ob.tooltip_text = T.t("Der Ring rollt den Riegel nach oben, öffnet ihn und streckt sich weich in die Haltung «Gerade». Bei geschlossenem Ring nehmen alle Haltungen ausser «Ring» diesen Weg.")
	_w["oeffnen_btn_posen"] = ob
	_ring_need(ob)
	_slider(pg, T.t("Körperhöhe über dem Boden"), 0.3, 1.8, 0.05, bew.hoehe, "E", func(x: float):
		bew.hoehe = x
		if last_pose in ["gerade", "kurve_links", "kurve_rechts", "bogen"]:
			apply_pose(last_pose))
	_slider(pg, T.t("Füsse seitlich"), 0.3, 2.0, 0.05, bew.spreiz, "E", func(x: float):
		bew.spreiz = x
		if last_pose in ["gerade", "kurve_links", "kurve_rechts", "bogen"]:
			apply_pose(last_pose))
	_button(pg, T.t("Neu aufstellen (R)"), reset)


func _page_bewegen(pg: VBoxContainer) -> void:
	"""the former tab «Bewegen», now in groups: Gangart · Richtung · Tempo und Schritt · Im Ring rollen (Fahren) and Ganze
	Abläufe (Haltung); pg = the group «Gangart»"""
	var gab := gruppe("ablaeufe")
	var ga := GridContainer.new()
	ga.columns = 2
	ga.add_theme_constant_override("h_separation", 6)
	ga.add_theme_constant_override("v_separation", 6)
	gab.add_child(ga)
	for a in BEWEGUNG.ABLAEUFE:
		var an: String = a[0]
		var b := _button(ga, T.t(a[1]), func(): start_ablauf(an))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_w["ab_" + an] = b
		if an == "einrollen":
			_ring_need(b)
	pg.add_child(UI.small(T.t("Gangarten – mit Körperhöhe, Tempo und Kurven (vorwärts + Regler «Kurve» oder Q / E). Ein kurzer Klick in die Welt setzt ein Ziel: der Roboter plant selbst – Kurve, seitwärts bei kleinem Versatz, an Ort drehen, wenn das Ziel hinten liegt.")))
	var gg := GridContainer.new()
	gg.columns = 2
	gg.add_theme_constant_override("h_separation", 6)
	gg.add_theme_constant_override("v_separation", 6)
	pg.add_child(gg)
	for g in BEWEGUNG.GAENGE:
		var gn: String = g[0]
		var b := _button(gg, gang_name(gn), func(): start_gang(gn))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_w["gang_" + gn] = b
	_toggle(pg, T.t("Körper passt sich dem Untergrund an"), bew.anpassen, func(on: bool): bew.anpassen = on)
	var gi := UI.small("", UI.TXT)
	pg.add_child(gi)
	_w["gang_info"] = gi
	var gr := gruppe("richtung")
	# Besitzer 28.11.2026 14:47: ein virtueller Stick statt der Richtungsknöpfe (roboter_stick.gd, wie in der Leiste unten)
	gr.add_child(UI.small(T.t("Stick ziehen: hoch = vorwärts, zur Seite = seitwärts, schräg geht auch; der Regler daneben dreht an Ort. Loslassen = Stopp. Tasten: W A S D, Q / E.")))
	gr.add_child(steu.sticks())
	var gring := gruppe("ring")
	var rb := _button(gring, T.t("Im Ring rollen (die Füsse stossen, Kurve = Ring neigen)"), func():
		if model.latch["state"] != "locked":
			apply_pose("ring", true)
		bew.start_ring()
		_paint_gang())
	_w["ring_btn"] = rb
	_ring_need(rb)
	var ob := _button(gring, T.t("Ring öffnen (gerade)"), func(): ring_oeffnen("gerade"))
	ob.tooltip_text = T.t("Der Ring rollt den Riegel nach oben, öffnet ihn und streckt sich weich in die Haltung «Gerade». Bei geschlossenem Ring nehmen alle Haltungen ausser «Ring» diesen Weg.")
	_w["oeffnen_btn"] = ob
	_ring_need(ob)
	_ring_hint(gring)
	_w["turn_sl"] = _slider(gr, T.t("Kurve (− rechts, + links)"), -1.0, 1.0, 0.05, 0.0, "", func(x: float): manual.z = x)
	var gt := gruppe("tempo")
	_slider(gt, T.t("Tempo"), 0.01, 0.25, 0.01, bew.tempo, "m/s", func(x: float):
		bew.tempo = x
		mark_dirty())
	_slider(gt, T.t("Körperhöhe über dem Boden"), 0.3, 1.8, 0.05, bew.hoehe, "E", func(x: float):
		bew.hoehe = x
		mark_dirty())
	_slider(gt, T.t("Spurbreite beim Gehen (Fuss links bis Fuss rechts)"), model.u("halbe_breite") * 200.0 + 2.0,
			(model.u("halbe_breite") + (model.u("oberschenkel") + model.u("unterschenkel")) * 0.95) * 200.0, 0.5, bew.spur_gehen() * 100.0, "cm",
			func(x: float):
		bew.set_spur_gehen(x / 100.0)
		mark_dirty())
	_slider(gt, T.t("Schrittlänge"), 0.2, 1.4, 0.05, bew.schritt_laenge, "E", func(x: float):
		bew.schritt_laenge = x
		mark_dirty())
	_slider(gt, T.t("Schritthöhe"), 0.1, 0.9, 0.05, bew.schritt_hoehe, "E", func(x: float):
		bew.schritt_hoehe = x
		mark_dirty())


func _page_steuerung() -> void:
	"""sim-robo-steuerung in the panel: «Steuerung» (Fahren: drive bar, key / controller map) and «Körper verschieben» (Haltung);
	the drive bar under the view stays as it is"""
	if steu == null:
		return
	var gs := gruppe("steuerung")
	_w["t_leiste"] = _toggle(gs, T.t("Untere Leiste mit Steuerung ein / aus"), steu.leiste, func(on: bool): steu.set_leiste(on))
	var bl := _button(gs, T.t("Belegung …"), func(): steu.open_map())
	bl.tooltip_text = T.t("Tasten und Controller frei belegen, Profile")
	var gk := gruppe("koerper")
	gk.add_child(UI.small(T.t("Auf der Stelle stehen, die Fahr-Eingaben verschieben den Körper (V / Back)")))
	var kb := _button(gk, T.t("Körper verschieben"), func(): steu.aktion("koerper"))
	_w["koerper_btn"] = kb
	_w["t_zur_mitte"] = _toggle(gk, T.t("Loslassen = zur Mitte"), steu.zur_mitte, func(on: bool):
		steu.zur_mitte = on
		steu.speichern())


func drive_dir(c: Vector3) -> void:
	"""pad / buttons: walk in this direction (x = seitwärts + links, y = vor, z = drehen + links); all 0 = stop"""
	if c == Vector3.ZERO:
		stop_all()
		return
	manual = c
	bew.goal = null
	var ts: Dictionary = _w.get("turn_sl", {})
	if not ts.is_empty():
		(ts["sl"] as HSlider).set_value_no_signal(c.z)
	if bew.mode not in ["gang", "ring"]:
		if model.latch["state"] == "locked":
			bew.start_ring()
		else:
			bew.start_gang(bew.gang)
	_paint_gang()


func _paint_gang() -> void:
	for g in BEWEGUNG.GAENGE:
		var b: Button = _w.get("gang_" + g[0])
		if b != null:
			_paint_btn(b, bew.mode == "gang" and bew.gang == g[0])
	for a in BEWEGUNG.ABLAEUFE:
		var b: Button = _w.get("ab_" + a[0])
		if b != null:
			_paint_btn(b, bew.mode == "ablauf" and bew.seq_name == a[0])
	var r: Button = _w.get("ring_btn")
	if r != null:
		_paint_btn(r, bew.mode == "ring")
	for k in ["oeffnen_btn", "oeffnen_btn_posen"]:
		var o: Button = _w.get(k)
		if o != null:
			_paint_btn(o, bew.mode == "ablauf" and bew.seq_name == "oeffnen")


func _page_anzeigen(pg: VBoxContainer) -> void:
	_toggle(pg, T.t("Servo-Last an den Gelenken (grün bis rot)"), anz.show_load, func(on: bool): anz.show_load = on)
	_toggle(pg, T.t("Schwerpunkt und Stützfläche"), anz.show_support, func(on: bool): anz.show_support = on)
	var tip := Label.new()
	tip.add_theme_font_size_override("font_size", 14)
	pg.add_child(tip)
	_w["tip"] = tip
	var cur := UI.small("", UI.TXT)
	pg.add_child(cur)
	_w["cur"] = cur
	pg.add_child(UI.small(T.t("Die meistbelasteten Servos (Last = nötiges Moment / Servo-Moment):")))
	var bars := VBoxContainer.new()
	bars.add_theme_constant_override("separation", 2)
	pg.add_child(bars)
	_w["bars"] = []
	for i in range(10):
		var h := HBoxContainer.new()
		bars.add_child(h)
		var l := Label.new()
		l.custom_minimum_size = Vector2(150, 0)
		l.add_theme_font_size_override("font_size", 12)
		h.add_child(l)
		var pb := ProgressBar.new()
		pb.max_value = 1.5
		pb.show_percentage = false
		pb.custom_minimum_size = Vector2(0, 12)
		pb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		pb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(pb)
		_w["bars"].append([l, pb])
	pg.add_child(UI.small(T.t("Strom: Schätzung je Servo = Ruhestrom + Blockierstrom × Last (Regler unter «Physik»). Kipp-Reserve: Abstand des Schwerpunkt-Lots vom Rand der Stützfläche (alle Bodenkontakte).")))


# ---- Rund rollen (Besitzer 22.11.2026 21:33 – 21:40) -----------------------------------------------------------------------
func _page_rund(pg: VBoxContainer) -> void:
	_ring_hint(pg)
	pg.add_child(UI.small(T.t("Wie rund rollt der Ring? Gemessen über eine ganze Drehung: Schwankung der Mittenhöhe, des Tempos, Zahl der Bodenkontakte (Ziel: immer mindestens 3) und Kipp-Reserve. Je Einstellung 3 Versuche.")))
	var gm := GridContainer.new()
	gm.columns = 1
	gm.add_theme_constant_override("v_separation", 4)
	pg.add_child(gm)
	for rm in bew.ring_methods():
		var mn: String = rm[0]
		var b := _button(gm, T.t(rm[1]), func():
			bew.ring_methode = mn
			mark_dirty()
			_paint_rund())
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_w["rm_" + mn] = b
		_ring_need(b)
	var hmax: float = bew.ring_height_max() * 100.0 if model.built_ok else 30.0
	_w["rund_h"] = _slider(pg, T.t("Höhe über Boden (0 = auf den Ecken, mehr = auf Stelzen)"), 0.0, maxf(0.5, hmax), 0.5,
			clampf(bew.ring_hoehe * 100.0, 0.0, hmax), "cm", func(x: float):
		bew.ring_hoehe = x / 100.0
		mark_dirty())
	_ring_need(_w["rund_h"]["sl"])
	var reach: float = model.u("oberschenkel") + model.u("unterschenkel")
	var smin: float = model.u("halbe_breite") * 200.0
	var smax: float = (model.u("halbe_breite") + reach * 0.6) * 200.0
	_w["rund_s"] = _slider(pg, T.t("Spurbreite beim Rollen (Fuss links bis Fuss rechts)"), smin, smax, 0.5,
			clampf(bew.spur_rollen * 100.0, smin, smax), "cm", func(x: float):
		bew.spur_rollen = x / 100.0
		mark_dirty())
	_ring_need(_w["rund_s"]["sl"])
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	pg.add_child(row)
	var go := _button(row, T.t("Im Ring rollen"), func():
		if model.latch["state"] != "locked":
			apply_pose("ring", true)
		bew.start_ring()
		manual = Vector3(0.0, 1.0, 0.0)
		_paint_gang())
	go.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_ring_need(go)
	var st := _button(row, T.t("Stopp"), func():
		rund_jobs = []
		rund_job = {}
		stop_all())
	st.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var live := UI.small("", UI.TXT)
	pg.add_child(live)
	_w["rund_live"] = live
	var gb := GridContainer.new()
	gb.columns = 2
	gb.add_theme_constant_override("h_separation", 6)
	gb.add_theme_constant_override("v_separation", 6)
	pg.add_child(gb)
	for e in [["Messen (diese Methode)", "eine"], ["Alle Methoden vergleichen", "alle"], ["Reihe Höhe (C)", "hoehe"], ["Reihe Spurbreite (C)", "spur"]]:
		var what: String = e[1]
		var b := _button(gb, T.t(e[0]), func(): rund_start(what))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_ring_need(b)
	var ab := _toggle(pg, T.t("Beste Methode als Standard übernehmen"), auto_best, func(on: bool): auto_best = on)
	_w["rund_auto"] = ab
	_ring_need(ab)
	var res := UI.small("", UI.TXT)
	res.add_theme_font_override("font", UI.heading_font())
	pg.add_child(res)
	_w["rund_res"] = res


func _paint_rund() -> void:
	for rm in BEWEGUNG.RING_METHODEN:
		var b: Button = _w.get("rm_" + rm[0])
		if b != null:
			_paint_btn(b, bew.ring_methode == rm[0])


func rund_start(what: String) -> void:
	"""queue measurements: eine | alle | hoehe | spur (3 trials each)"""
	if not ring_ok():
		return
	var cfgs := []
	var h: float = bew.ring_hoehe
	var sp: float = bew.spur_rollen
	match what:
		"eine":
			cfgs = [[bew.ring_methode, h, sp]]
		"alle":
			for rm in bew.ring_methods():
				cfgs.append([rm[0], h, sp])
		"hoehe":
			var hm: float = bew.ring_height_max()
			for k in [0.0, 0.5, 1.0]:
				cfgs.append(["c", hm * k, sp])
		"spur":
			var w: float = model.u("halbe_breite")
			var reach: float = model.u("oberschenkel") + model.u("unterschenkel")
			for k in [0.15, 0.35, 0.55]:
				cfgs.append(["c", h, 2.0 * (w + reach * k)])
	rund_jobs = []
	for c in cfgs:
		for v in range(RUND_VERSUCHE):
			rund_jobs.append({"methode": c[0], "hoehe": c[1], "spur": c[2], "versuch": v})
	rund_job = {}
	terrain = {}


static func rund_key(methode: String, hoehe: float, spur: float) -> String:
	return "%s|%.1f|%.1f" % [methode, hoehe * 100.0, spur * 100.0]


func _rund_step(dt: float) -> void:
	if rund_job.is_empty():
		if rund_jobs.is_empty():
			return
		rund_job = rund_jobs.pop_front()
		bew.stop()
		manual = Vector3.ZERO
		bew.ring_methode = rund_job["methode"]
		bew.ring_hoehe = rund_job["hoehe"]
		bew.spur_rollen = rund_job["spur"]
		model.root_xf = starts.get("start", Transform3D())
		apply_pose("ring", true)
		rund_job["phase"] = "settle"
		rund_job["t"] = 0.0
		return
	rund_job["t"] = float(rund_job["t"]) + dt
	var t: float = rund_job["t"]
	match rund_job["phase"]:
		"settle":
			if t > 1.5 + 0.25 * float(rund_job["versuch"]):
				bew.start_ring()
				manual = Vector3(0.0, 1.0, 0.0)
				rund_job["phase"] = "go"
				rund_job["t"] = 0.0
		"go":
			if t > 1.0:
				bew.start_ring_measure()
				rund_job["phase"] = "measure"
				rund_job["t"] = 0.0
		"measure":
			var r: Dictionary = bew.ring_result
			var fell: bool = model.latch["state"] != "locked" or absf(bew.ring_lean) > 50.0 or _tipped_ring()
			if r.is_empty() and not fell and t < RUND_MAX:
				return
			var row := r.duplicate() if not r.is_empty() else {"ok": false, "grund": "umgefallen" if fell else "zu langsam"}
			if not r.is_empty() and fell:
				row["ok"] = false
				row["grund"] = "umgefallen"
			var key := rund_key(rund_job["methode"], rund_job["hoehe"], rund_job["spur"])
			if not rund_rows.has(key) or int(rund_job["versuch"]) == 0:
				rund_rows[key] = []
			(rund_rows[key] as Array).append(row)
			rund_job = {}
			if rund_jobs.is_empty():
				bew.stop()
				manual = Vector3.ZERO
				_rund_pick_best()


func _tipped_ring() -> bool:
	return absf(bew.ring_lean) > 50.0


static func _median(a: Array) -> float:
	if a.is_empty():
		return 0.0
	var b := a.duplicate()
	b.sort()
	return float(b[b.size() / 2])


func rund_summary() -> Array:
	"""one line per setting: [key, methode, hoehe cm, spur cm, ok/n, dh, dv, v, kmin, kavg, kipp, unter3]"""
	var out := []
	for key in rund_rows:
		var rows: Array = rund_rows[key]
		var parts: Array = key.split("|")
		var oks := rows.filter(func(r): return bool(r.get("ok", false)))
		var line := {"key": key, "methode": parts[0], "hoehe": float(parts[1]), "spur": float(parts[2]), "ok": oks.size(), "n": rows.size()}
		if not oks.is_empty():
			line["dh"] = _median(oks.map(func(r): return float(r["dh"])))
			line["dv"] = _median(oks.map(func(r): return float(r["dv"])))
			line["v"] = _median(oks.map(func(r): return float(r["v"])))
			line["kmin"] = oks.map(func(r): return int(r["kmin"])).min()
			line["kavg"] = _median(oks.map(func(r): return float(r["kavg"])))
			line["kipp"] = oks.map(func(r): return float(r.get("kipp", 0.0))).min()
			line["unter3"] = oks[0].get("unter3", [])
		else:
			line["grund"] = str(rows[0].get("grund", ""))
		out.append(line)
	return out


static func rund_score(l: Dictionary) -> float:
	"""smaller = better: centre-height swing (cm) + speed swing + a penalty for fewer than 3 ground contacts"""
	return float(l["dh"]) + 0.02 * float(l["dv"]) + maxf(0.0, 3.0 - float(l["kavg"])) + 0.5 * maxf(0.0, 3.0 - float(l["kmin"]))


func _rund_pick_best() -> void:
	"""roundest = all trials made it, best score; becomes the default of this variant if clearly better (≤ 80 %)"""
	var lines := rund_summary().filter(func(l): return int(l["ok"]) == int(l["n"]) and int(l["n"]) > 0)
	lines.sort_custom(func(a, b): return rund_score(a) < rund_score(b))
	rund_best = ""
	if lines.is_empty():
		return
	var best: Dictionary = lines[0]
	var clearly: bool = lines.size() == 1 or rund_score(best) <= 0.8 * rund_score(lines[1])
	mark_dirty()
	rund_best = str(best["key"])
	if auto_best and clearly:
		bew.ring_methode = best["methode"]
		bew.ring_hoehe = float(best["hoehe"]) / 100.0
		bew.spur_rollen = float(best["spur"]) / 100.0
		mark_dirty()


func _rund_text() -> String:
	var names := {}
	for rm in BEWEGUNG.RING_METHODEN:
		names[rm[0]] = T.t(rm[1])
	var t := ""
	for l in rund_summary():
		t += (T.t("Beste") + " · " if l["key"] == rund_best else "") + str(names.get(l["methode"], l["methode"])) + "  ·  " + T.t("Höhe %.1f cm · Spur %.1f cm") % [l["hoehe"], l["spur"]] + "\n"
		if int(l["ok"]) == 0:
			var gr := {"umgefallen": T.t("umgefallen"), "zu langsam": T.t("zu langsam")}
			t += "   " + T.t("nicht geschafft") + " (" + str(gr.get(str(l.get("grund", "")), "")) + ")\n"
			continue
		t += "   " + T.t("%d/%d geschafft · Mitte ± %.1f cm · Tempo %.0f cm/s ± %.0f %% · Kontakte min %d / Ø %.1f · Kipp-Reserve %.1f cm") % [
				l["ok"], l["n"], float(l["dh"]) * 0.5, l["v"], l["dv"], l["kmin"], l["kavg"], l["kipp"]] + "\n"
		if int(l["kmin"]) < 3 and not (l["unter3"] as Array).is_empty():
			var zs := []
			for z in l["unter3"]:
				zs.append("%d–%d°" % [z[0], z[1]])
			t += "   " + T.t("unter 3 Kontakten bei: %s") % ", ".join(zs) + "\n"
	# the variants side by side (the best measured setting of each, saved)
	var side := ""
	for vv in VARIANTEN:
		var sv: Dictionary = _store.get(vv[0], {})
		var lines: Array = rund_summary() if vv[0] == variante and not rund_rows.is_empty() else sv.get("rund", [])
		var bk: String = rund_best if vv[0] == variante and rund_best != "" else str(sv.get("rund_best", ""))
		for l in lines:
			if l["key"] == bk and int(l["ok"]) > 0:
				side += "%s: %s · " % [T.t(vv[1]), names.get(l["methode"], l["methode"])] + T.t("Mitte ± %.1f cm · Tempo ± %.0f %% · Kontakte min %d / Ø %.1f") % [
						float(l["dh"]) * 0.5, l["dv"], l["kmin"], l["kavg"]] + "\n"
	if side != "":
		t += "\n" + T.t("Vergleich 8 / 6 / 4 (jeweils die beste Messung):") + "\n" + side
	if not rund_jobs.is_empty() or not rund_job.is_empty():
		t += T.t("Messung läuft … noch %d") % (rund_jobs.size() + (0 if rund_job.is_empty() else 1)) + "\n"
	return t


func _page_gelaende(pg: VBoxContainer) -> void:
	pg.add_child(UI.small(T.t("Gelände-Test: der Roboter startet vor der Prüfstrecke und geht mit der automatischen Gangart (oder rollt im Ring) hinüber. Geschafft = das hinterste Segment ist darüber. «Automatisch» hebt die Füsse und den Körper, wenn er nicht vorwärts kommt.")))
	var ring := CheckButton.new()
	ring.text = T.t("Im Ring rollen statt gehen")
	ring.focus_mode = Control.FOCUS_NONE
	pg.add_child(ring)
	_w["terrain_ring"] = ring
	_ring_need(ring)
	_ring_hint(pg)
	var mit_ki := CheckButton.new()
	mit_ki.text = T.t("Mit der Gang-KI gehen")
	mit_ki.focus_mode = Control.FOCUS_NONE
	pg.add_child(mit_ki)
	_w["terrain_ki"] = mit_ki
	for t in GELAENDE.NAMEN:
		var tn: String = t[0]
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 8)
		pg.add_child(h)
		var b := _button(h, T.t(t[1]), func(): terrain_start([tn], ring.button_pressed))
		b.custom_minimum_size = Vector2(130, 0)
		var l := UI.small("–", UI.MUT)
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(l)
		_w["terrain_" + tn] = l
	_button(pg, T.t("Alle nacheinander"), func(): terrain_start(GELAENDE.NAMEN.map(func(x): return x[0]), ring.button_pressed), true)
	_button(pg, T.t("Abbrechen"), func():
		terrain = {}
		stop_all())


func terrain_start(names: Array, ring := false, mit_ki := false) -> void:
	if names.is_empty():
		return
	var tn: String = names[0]
	ring = ring and ring_ok()
	stop_all()
	ki.neu_start()
	bew.angepasst = false
	bew.hoehe = 0.9
	bew.schritt_hoehe = 0.35
	model.root_xf = starts.get(tn, starts.get("start", Transform3D()))
	apply_pose("ring" if ring else "gerade", true)
	terrain = {"name": tn, "ring": ring, "t": 0.0, "best": -1e9, "last_t": 0.0, "queue": names.slice(1)}
	terrain_results[tn] = [false, T.t("läuft …")]
	follow = true
	if ring:
		bew.start_ring()
		manual = Vector3(0.0, 1.0, 0.0)
	else:
		var tk: CheckButton = _w.get("terrain_ki")
		mit_ki = mit_ki or (tk != null and tk.button_pressed)
		terrain["ki"] = mit_ki
		bew.start_gang("ki" if mit_ki else "auto")
		manual = Vector3(0.0, 1.0, 0.0)
	_paint_gang()


func _terrain_x() -> float:
	if terrain.get("ring", false):
		return (bew.ring_state()["c"] as Vector3).x
	return model.segment_xf(model.n() - 1).origin.x


func _terrain_step(dt: float) -> void:
	terrain["t"] = float(terrain["t"]) + dt
	var tn: String = terrain["name"]
	var x := _terrain_x()
	if x > float(terrain["best"]) + 0.03:
		terrain["best"] = x
		terrain["last_t"] = terrain["t"]
	var t: float = terrain["t"]
	var res := []
	if x >= float(GELAENDE.ENDE[tn]):
		res = [true, T.t("geschafft in %d s") % int(round(t)) + (" · " + T.t("Füsse höher") if bew.angepasst else "")]
	elif terrain.get("ring", false) and (model.latch["state"] != "locked" or absf(bew.ring_lean) > 60.0):
		res = [false, T.t("umgefallen nach %d s") % int(round(t))]
	elif not terrain.get("ring", false) and _tipped():
		res = [false, T.t("gekippt nach %d s") % int(round(t))]
	elif t - float(terrain["last_t"]) > TERRAIN_STILL:
		res = [false, T.t("steckt fest (%d s ohne Fortschritt)") % int(TERRAIN_STILL)]
	elif t > TERRAIN_MAX:
		res = [false, T.t("zu langsam (über %d s)") % int(TERRAIN_MAX)]
	if res.is_empty():
		return
	terrain_results[tn] = res
	var q: Array = terrain["queue"]
	var ring: bool = terrain["ring"]
	var mit_ki: bool = terrain.get("ki", false)
	terrain = {}
	bew.stop()
	manual = Vector3.ZERO
	if not q.is_empty():
		terrain_start(q, ring, mit_ki)


func _tipped() -> bool:
	for i in range(model.n()):
		if model.segment_xf(i).basis.y.y < 0.2:
			return true
	return false


func servo_name(id: String) -> String:
	"""sy3 -> «Gelenk 4 links/rechts», hp2l -> «Bein 3 links Hüfte hoch/runter»"""
	var k := id.substr(0, 2)
	if k in ["sy", "sp"]:
		return T.t("Gelenk %d") % (int(id.substr(2)) + 1) + " " + (T.t("links / rechts") if k == "sy" else T.t("hoch / runter"))
	if k in ["hy", "hp", "kn"]:
		var side := T.t("links") if id.ends_with("l") else T.t("rechts")
		var what: String = {"hy": T.t("Hüfte vor / zurück"), "hp": T.t("Hüfte hoch / runter"), "kn": T.t("Knie")}[k]
		return T.t("Bein %d") % (int(id.substr(2, id.length() - 3)) + 1) + " " + side + " " + what
	return id


func _page_physik(pg: VBoxContainer) -> void:
	pg.add_child(UI.small(T.t("Schwerkraft, Reibung und Servo-Grenzen. Die Servos halten höchstens ihr Moment – mehr Last = sie geben nach (rot).")))
	_slider(pg, T.t("Schwerkraft"), 0.0, 20.0, 0.1, gravity, "m/s²", set_gravity)
	for f in PHYSIK:
		var g: Array = MODELL.GRENZEN[f[0]]
		var key: String = f[0]
		_w["form_" + key] = _slider(pg, T.t(f[1]), g[0], g[1], f[3], float(model.p[key]), f[2], func(x: float): set_shape(key, x))
	_w["t_pause"] = _toggle(pg, T.t("Physik anhalten (P)"), paused, set_paused)
	_w["t_hold"] = _toggle(pg, T.t("Festhalten: mittleres Segment in der Luft (F)"), false, set_hold)
	var info := UI.small("", UI.TXT)
	pg.add_child(info)
	_w["phys_info"] = info


func _page_ansicht(pg: VBoxContainer) -> void:
	var gr := GridContainer.new()
	gr.columns = 2
	gr.add_theme_constant_override("h_separation", 6)
	gr.add_theme_constant_override("v_separation", 6)
	pg.add_child(gr)
	for v in VIEWS:
		var b := _button(gr, T.t(v[1]), set_view.bind(v[0]))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_w["t_pip"] = _toggle(pg, T.t("Kamerabild klein einblenden (K)"), pip, set_pip)
	_w["t_info"] = _toggle(pg, T.t("Info-Feld oben links einblenden (I)"), info_on, set_info)
	_w["t_follow"] = _toggle(pg, T.t("Ansicht folgt dem Roboter"), follow, func(on: bool):
		follow = on)
	pg.add_child(UI.small(T.t("Rot = Teile des Roboters, die sich berühren oder durchdringen (z. B. Knie am Körper).")))


func _paint_toggles() -> void:
	for k in [["t_pause", paused], ["t_hold", model != null and model.hold], ["t_pip", pip], ["t_info", info_on], ["t_follow", follow]]:
		var c: CheckButton = _w.get(k[0])
		if c != null:
			c.set_pressed_no_signal(bool(k[1]))


func _refresh() -> void:
	if model == null or not model.built_ok:
		return
	var lstate := {"open": T.t("Kupplung offen"), "grip": T.t("Kupplung greift"), "locked": T.t("Ring verriegelt")}
	var red: int = model.collide.size()
	var over: Array = model.overloaded()
	var lines := [T.t("Roboter-Labor") + " · " + (T.t("Physik angehalten") if paused else T.t("Physik läuft")) + (" · " + T.t("festgehalten") if model.hold else ""),
			str(lstate.get(model.latch["state"], "")) + " · " + (T.t("%d Teile berühren sich (rot)") % red if red > 0 else T.t("keine Kollision")),
			T.t("Servos: %d · überlastet: %d · Strom ca. %.1f A") % [model.actuator_count(), over.size(), model.total_current],
			(T.t("KIPPGEFAHR") + " · " if anz.tipping else "") + T.t("Kipp-Reserve %.1f cm") % (anz.margin * 100.0) + " · " + _move_text()]
	(_w["status"] as Label).text = "\n".join(lines)
	for k in ["oeffnen_btn", "oeffnen_btn_posen"]:                 # «Ring öffnen» blue while it opens, then off again
		var o: Button = _w.get(k)
		if o != null:
			_paint_btn(o, bew.mode == "ablauf" and bew.seq_name == "oeffnen")
	var kb: Button = _w.get("koerper_btn")
	if kb != null and steu != null:
		_paint_btn(kb, bool(steu.koerper))
	var tlb: CheckButton = _w.get("t_leiste")
	if tlb != null and steu != null and tlb.button_pressed != bool(steu.leiste):
		tlb.set_pressed_no_signal(bool(steu.leiste))
	var pi: Label = _w.get("phys_info")
	if pi != null and pi.is_visible_in_tree():
		var c: Vector3 = model.com()
		pi.text = T.t("Masse %.2f kg · Schwerpunkt %.0f cm über dem Boden · Strom ca. %.1f A") % [model.total_mass, c.y * 100.0, model.total_current] \
				+ ("\n" + T.t("Überlastet: %s") % ", ".join(over) if not over.is_empty() else "")
	if _sichtbar("tip"):
		var tl: Label = _w["tip"]
		tl.text = (T.t("KIPPGEFAHR") + " – " if anz.tipping else "") + T.t("Kipp-Reserve %.1f cm") % (anz.margin * 100.0)
		tl.add_theme_color_override("font_color", UI.RED if anz.tipping else UI.GRN)
		var cs: Dictionary = anz.currents()
		(_w["cur"] as Label).text = T.t("Strom ca. %.1f A (Körper %.1f A · Beine %.1f A · Kamera und Riegel %.2f A)") % [cs["total"], cs["koerper"], cs["beine"], cs["rest"]]
		var tops: Array = anz.top_loads(10)
		for i in range(10):
			var pr: Array = _w["bars"][i]
			if i < tops.size():
				(pr[0] as Label).text = "%s  %.2f N·m" % [servo_name(tops[i][0]), absf(tops[i][2])]
				(pr[1] as ProgressBar).value = minf(1.5, tops[i][1])
				(pr[1] as ProgressBar).modulate = ANZEIGE.load_color(tops[i][1])
	if _sichtbar("rund_res"):
		_paint_rund()
		var rs: Dictionary = bew.ring_state() if model.latch["state"] == "locked" else {}
		(_w["rund_live"] as Label).text = (T.t("Mitte %.1f cm über Boden · %d Kontakte · Neigung %d° · %.1f cm/s") % [
				((rs["c"] as Vector3).y - float(rs["gy"])) * 100.0, model.ground_contacts(), int(round(bew.ring_lean)), absf(bew._ring_v) * 100.0]) if not rs.is_empty() else T.t("Ring nicht verriegelt")
		(_w["rund_res"] as Label).text = _rund_text()
	if _sichtbar("terrain_ring"):
		for t in GELAENDE.NAMEN:
			var l: Label = _w.get("terrain_" + t[0])
			var r: Array = terrain_results.get(t[0], [])
			if l != null and not r.is_empty():
				l.text = str(r[1])
				l.add_theme_color_override("font_color", UI.GRN if r[0] else (UI.TXT if str(r[1]) == T.t("läuft …") else UI.RED))
	if _gruppen.has("ki") and (_gruppen["ki"] as Control).is_visible_in_tree():
		ki.auffrischen()
	if _sichtbar("gang_info") or _sichtbar("ring_btn"):
		(_w["gang_info"] as Label).text = _move_text()
		_paint_gang()
	if _sichtbar("latch_ok"):
		for id in _sl:
			var si: int = model.servo_index(id)
			if si < 0:
				continue
			var sv: Dictionary = model.servos[si]
			var d: Dictionary = _sl[id]
			(d["val"] as Label).text = "%d° · %d°" % [int(round(sv["target"])), int(round(sv["angle"]))]
			(d["val"] as Label).add_theme_color_override("font_color", UI.RED if float(sv["load"]) > 1.0 else (UI.ORG if float(sv["load"]) > 0.7 else UI.MUT))


func _sichtbar(key: String) -> bool:
	"""a widget of the panel is on the screen (its tab shown, its group open): only then the panel refreshes it"""
	var c = _w.get(key)
	return c is Control and is_instance_valid(c) and (c as Control).is_visible_in_tree()


func _move_text() -> String:
	var names := {}
	for g in BEWEGUNG.GAENGE:
		names[g[0]] = gang_name(g[0])
	for a in BEWEGUNG.ABLAEUFE:
		names[a[0]] = T.t(a[1])
	names["oeffnen"] = T.t("Ring öffnen")
	var t := T.t("steht")
	if bew.mode == "gang":
		t = str(names.get(bew.gang_now, bew.gang_now)) + (" (" + T.t("automatisch") + ")" if bew.gang == "auto" else "")
		if bew.goal != null:
			var pn := {"kurve": T.t("Kurve"), "seitwaerts": T.t("seitwärts"), "drehen": T.t("an Ort drehen")}
			t += " · " + (T.t("Ziel erreicht") if bew.goal_reached else T.t("zum Ziel") + " (" + str(pn.get(bew.plan, "")) + ")")
		elif bew.mode == "gang" and bew.cmd != Vector3.ZERO:
			t += " · " + _dir_text(bew.cmd)
	elif bew.mode == "ring":
		t = T.t("Im Ring rollen") + " · " + T.t("Neigung %d°") % int(round(bew.ring_lean))
		if model.latch["state"] != "locked":
			t += " · " + T.t("Ring nicht verriegelt")
		if bew.goal != null:
			t += " · " + (T.t("Ziel erreicht") if bew.goal_reached else T.t("zum Ziel"))
	elif bew.mode == "ablauf":
		t = T.t("Ablauf") + ": " + str(names.get(bew.seq_name, bew.seq_name))
	return t + " · " + T.t("%.1f cm/s") % (speed * 100.0)


func _dir_text(c: Vector3) -> String:
	var parts := []
	if c.y > 0.1:
		parts.append(T.t("vor"))
	elif c.y < -0.1:
		parts.append(T.t("zurück"))
	if c.x > 0.1:
		parts.append(T.t("links"))
	elif c.x < -0.1:
		parts.append(T.t("rechts"))
	if absf(c.z) > 0.05:
		parts.append(T.t("Kurve") if absf(c.y) > 0.25 and absf(c.x) < 0.15 else T.t("an Ort drehen"))
	return " + ".join(parts)


# ---- /control «roboter» -----------------------------------------------------------------------------------------------------
func info() -> Dictionary:
	var d := {"ok": true, "open": is_open()}
	if is_open() and model != null and model.built_ok:
		d.merge({"segments": model.n(), "ring_ok": ring_ok(), "servos": model.servos.size(), "actuators": model.actuator_count(), "view": view, "tab": tab,
				"paused": paused, "hold": model.hold, "latch": model.latch["state"], "latch_wanted": model.latch_wanted, "latch_wait": bew.latch_wait, "com": [model.com().x, model.com().y, model.com().z],
				"mass": model.total_mass, "current": model.total_current, "overloaded": model.overloaded(),
				"collide": model.colliding_names(), "pose": last_pose, "ticks": Engine.physics_ticks_per_second,
				"mode": bew.mode, "gait": bew.gang_now, "sequence": bew.seq_name, "speed": speed, "tip_margin": anz.margin,
				"tipping": anz.tipping, "goal_reached": bew.goal_reached, "ring_lean": bew.ring_lean,
				"terrain": terrain.get("name", ""), "terrain_results": terrain_results, "adapted": bew.angepasst,
				"plan": bew.plan, "anpassen": bew.anpassen, "variante": variante, "pip": pip, "info_on": info_on, "panel": _panel_on, "compact": compact() if is_open() else false, "touch": touch, "ring_methode": bew.ring_methode,
				"rund": rund_summary(), "rund_best": rund_best, "ki": ki.info(), "rund_laeuft": not rund_jobs.is_empty() or not rund_job.is_empty()})
		if steu != null:
			d["steuerung"] = steu.info()
	return d


func control(d: Dictionary) -> Dictionary:
	var do := str(d.get("do", "info"))
	if d.has("variante"):
		_load_store()
		set_variante(str(d["variante"]))
	if do == "open":
		open()
	elif do == "close":
		close()
		return info()
	if not is_open():
		return info() if do == "info" else {"ok": false, "error": "not open"}
	match do:
		"pose":
			apply_pose(str(d.get("name", "gerade")), bool(d.get("snap", false)))
		"oeffnen":
			ring_oeffnen(str(d.get("name", "gerade")))
		"set":
			model.set_target(str(d.get("id", "")), float(d.get("value", 0.0)))
			_sync_servo_sliders()
		"param":
			set_shape(str(d.get("key", "")), float(d.get("value", 0.0)))
		"view":
			set_view(str(d.get("value", "frei")))
		"pause":
			set_paused(bool(d.get("on", true)))
		"reset":
			reset()
		"hold":
			set_hold(bool(d.get("on", true)))
		"tab":
			set_tab(str(d.get("value", "form")))
		"pip":
			set_pip(bool(d.get("on", true)))
		"info":
			set_info(bool(d.get("on", true)))
		"panel":
			set_panel(bool(d.get("on", true)))
		"gang":
			start_gang(str(d.get("name", "auto")))
			if d.has("drive"):
				manual.y = float(d["drive"])
			if d.has("turn"):
				manual.z = float(d["turn"])
			if d.has("strafe"):
				manual.x = float(d["strafe"])
		"ablauf":
			start_ablauf(str(d.get("name", "")))
		"goal":
			var g: Array = d.get("pos", [0, 0, 0])
			set_goal(Vector3(float(g[0]), float(g[1]), float(g[2])))
		"stop":
			stop_all()
		"ring":
			if not ring_ok():
				var r := info()
				r["ok"] = false
				r["error"] = RING_HINWEIS
				return r
			if model.latch["state"] != "locked":
				apply_pose("ring", true)
			bew.start_ring()
			manual = Vector3(0.0, float(d.get("drive", 0.0)), float(d.get("turn", 0.0)))
		"anpassen":
			bew.anpassen = bool(d.get("on", true))
		"rund":
			if d.has("methode"):
				bew.ring_methode = str(d["methode"])
			if d.has("hoehe"):
				bew.ring_hoehe = float(d["hoehe"])
			if d.has("spur"):
				bew.spur_rollen = float(d["spur"])
			if d.has("messen"):
				rund_start(str(d["messen"]))
		"koerper", "steuerung":
			steu.control(d)
		"gelaende":
			var names = d.get("name", "stufe")
			terrain_start(names if names is Array else [str(names)], bool(d.get("ring", false)), bool(d.get("ki", false)))
		"ki":
			ki.steuern(d)
	return info()
