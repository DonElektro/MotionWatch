extends Node
## Abenteuer-Kit (Grossvater-Neubau «Die Karte des Grossvaters» im Uncharted-Stil, Besitzer 20.11.2026) – der Rahmen:
## eigene Spielfigur (kit_figur.gd), Kamera-Regie und Filmszenen (kit_regie.gd), schlanker Bildschirm mit Touch-Steuerung
## (kit_hud.gd), Maggie als Begleiterin (kit_maggie.gd), Parcours aus Daten (kit_parcours.gd), Musik-Zustände (klang.gd).
## Inhalt eines Kapitels = eine Daten-Datei (kit_k2_daten.gd): Texte, Parcours, Szenen. Die anderen Spiele können den
## Rahmen später übernehmen (Phase 3 «Abenteuer-Baukasten»).
## Neben dem alten Ablauf (bergtal_abenteuer.gd, Seitenspalte) – Schalter «Neuer Spielmodus (Probe)» im Kapitel-Schritt,
## bis der Besitzer den neuen freigibt.
## Steuerung: PC W A S D / Pfeile, Shift rennen, Leertaste springen / greifen, E / F Aktion, Maus ziehen umschauen, Rad Abstand,
##   Esc Pause / Film überspringen. Controller (padmap.gd liefert die Sticks; seine Geräte gehören solange dem Kit): linker
##   Stick gehen, rechter umschauen, A springen / greifen, X / B Aktion, R2 rennen, Start Pause. Handy / iPad: kit_hud.gd.
## Steuerbefehl {"action": "kit", "do": info | start (rolle, name, szene, kinder, touch, figur_test) | stop | szene (id / n) |
##   eingabe (mv [x, y] Kamera-relativ, run, sprung, aktion, vor, quer, s Sekunden) | setzen (s, q) | aktion (id) |
##   skip | pause (on) | touch (on) | kamera (art, s, q, h, blick) | musik (z) | sag (text, wer) | zustand (z)}

const T = preload("res://scripts/i18n.gd")
const Figur = preload("res://scripts/kit_figur.gd")
const Regie = preload("res://scripts/kit_regie.gd")
const Hud = preload("res://scripts/kit_hud.gd")
const Par = preload("res://scripts/kit_parcours.gd")
const Hund = preload("res://scripts/kit_maggie.gd")
const Klang = preload("res://scripts/klang.gd")
const Quality = preload("res://scripts/quality.gd")
const BUSY := "Die Karte des Grossvaters (neu)"

var main
var daten = preload("res://scripts/kit_k2_daten.gd")
var running := false
var phase := ""                      # laden | spiel | film | pause
var uhr := 0.0                       # own clock (with slow motion)
var figur
var regie
var hud
var par
var hund
var bt
var weg := PackedVector2Array()
var rolle := "enkelin"
var name_ := ""
var kinder := false
var szene_i := 0
var schritt_i := -1
var schritt := {}
var ziel_text := ""
var _ziel_p = null                   # world point of the goal (compass)
var checkpoint := Vector3.ZERO
var checkpoint_id := ""
var erledigt := {}                   # action id -> true (this run)
var funde := {}
var abzeichen := {}
var merker := {}
var film_move := Vector2.ZERO
var film_hang := false
var film_hang_p := Vector3.ZERO
var film_hang_auf := Vector3.ZERO
var nach_klettern := {}
var musik_z := "explore"
var _sub_bis := 0.0
var _saved := {}
var _layers := {}
var _spaet: Node
var _test := {}                      # tests: {"ein": {...}, "bis": uhr}
var _touch_force := -1
var _pause_vor := ""
var log_: Array = []
var fps_log: Array = []
var _fps_t := 0.0
var steuer_maggie := false
var _marker: Node3D = null
var _marker_t := 0.0
var _hinweis_i := 0
var _maggie_auto := false
var _halt_t := 0.0
var qte := {}                        # a quick press in a film: {id, text, bis}
var personen := {}                   # film figures: id -> actor (puppet)
var _person_ziel := {}               # id -> world point it walks to
var karte_an := false
var _karte := {}
var fotos := 0


const PROBE_DATEI := "res://inhalte/grossvater_probe.json"   # only in the probe package of the owner (delete before merging)


static func autostart_pruefen(m) -> void:
	"""the probe package for the owner: with res://inhalte/grossvater_probe.json ({"autostart": true}) or the start option
	--grossvater-neu (browser: …?grossvater=1) the simulator goes straight into chapter 2 of the new mode (start card first)"""
	var an := "--grossvater-neu" in (OS.get_cmdline_args() + OS.get_cmdline_user_args() + preload("res://scripts/web.gd").args())
	if not an and FileAccess.file_exists(PROBE_DATEI):
		var j = JSON.parse_string(FileAccess.get_file_as_string(PROBE_DATEI))
		an = j is Dictionary and bool(j.get("autostart", false))
	var nur_datei := not "--grossvater-neu" in (OS.get_cmdline_args() + OS.get_cmdline_user_args() + preload("res://scripts/web.gd").args())
	if not an or (nur_datei and "--no-tour" in OS.get_cmdline_user_args()):
		return                                             # (tests and CI start with --no-tour: the file alone never starts them)
	await m.get_tree().create_timer(3.0).timeout          # the start of the simulator first (scene, panel, news)
	if m.get("news") != null and m.news.has_method("close"):
		m.news.close()
	var k = ensure(m)
	if not k.running:
		k.start({"rolle": "tochter"})                       # the start card asks for the role and the name (default «Nina»)


static func ensure(m):
	if m.get("kit") == null or not is_instance_valid(m.kit):
		var k = load("res://scripts/kit_abenteuer.gd").new()
		k.main = m
		k.name = "kit_abenteuer"
		m.add_child(k)
		m.kit = k
	return m.kit


func _ready() -> void:
	process_priority = -20                                   # before the actors: the wishes of the figure
	_spaet = Node.new()
	_spaet.name = "kit_spaet"
	_spaet.process_priority = 95                             # after the actors: height, walls, the camera
	_spaet.set_script(preload("res://scripts/kit_spaet.gd"))
	_spaet.set("kit", self)
	add_child(_spaet)


func spielt() -> bool:
	return running and phase in ["spiel", "film"]


func tx(s: String) -> String:
	"""a text of the data in the current language with the placeholders of the role"""
	var d: Dictionary = daten.bezug(rolle)
	d["name"] = name_
	var bz := str(d["bezug"])
	d["bezug"] = T.t(bz)
	d["lia_bezug"] = T.t(str(d["lia_bezug"]))
	return T.t(s, d)


# =======================================================================================================================
# start / stop
# =======================================================================================================================
signal start_gewaehlt


func start(o := {}) -> void:
	if running:
		stop()
	if not o.has("name") and not bool(o.get("figur_test", false)):
		var w: Dictionary = await _start_karte(str(o.get("rolle", "tochter")), "Nina")   # the owner: «Nina» as the default name
		o = o.duplicate()
		o["rolle"] = w["rolle"]
		o["name"] = w["name"]
	rolle = str(o.get("rolle", "enkelin"))
	if not rolle in daten.ROLLEN:
		rolle = "enkelin"
	name_ = str(o.get("name", "")).strip_edges().left(16)
	if name_ == "":
		name_ = T.t(str(daten.ROLLE_NAME[rolle]))
	kinder = bool(o.get("kinder", main.get("kids_on") == true))
	if o.has("touch"):
		_touch_force = 1 if bool(o["touch"]) else 0
	running = true
	phase = "laden"
	uhr = 0.0
	erledigt = {}
	funde = {}
	merker = {}
	abzeichen = {}
	_saved = {"hour": main.hour(), "speed": main.speed, "weather": main.weather, "auto": main.auto_visitors, "bt_events": main.bt_events,
			"bt_season": main.bt_season, "bt_spot": main.bt_spot, "bt_free": (main.bt_free as Array).duplicate(), "bt_bed": main.bt_bed,
			"scene": main.scene}
	if main.maggie != null and bool(main.maggie.running):
		main.maggie.stop()
	if main.explore != null and main.explore.on:
		main.explore.set_on(false)
	if main.abenteuer != null:
		main.abenteuer.close_ab()
	if main.mehr != null:
		main.mehr.close_menu()
	main.auto_visitors = false
	main.bt_events = false
	main.bt_season = "sommer"
	main.bt_spot = "frei"
	main.bt_free = [daten.LAGER.x, daten.LAGER.y, 0.0]
	main.bt_bed = "bivy"
	_saved["bt_wall"] = main.get("bt_wall")
	if main.get("bt_wall") != null:
		main.bt_wall = false                                  # no wind wall at the camp: it filled the IR shots (polish 21.11.)
	main.set_scene("bergtal")
	await get_tree().process_frame
	await get_tree().process_frame
	if not running:
		return
	bt = main.scenes.data.get("bergtal", null) if main.scenes != null else null
	if bt == null:
		main.start_info = T.t("Das Bergtal fehlt – das Abenteuer braucht die Szene Bergtal.")
		stop()
		return
	main.weather = "clear"
	main.set_hour(10.5)
	main._set_speed(0.0)
	par = Par.new()
	if not par.binden(main, daten):
		stop()
		return
	bt.s.root.add_child(par)
	par.bauen()
	weg = par.weg_punkte()
	figur = Figur.new(self)
	figur.kinder = kinder
	var cp: Array = daten.CHECKPOINTS["start"]
	figur.bauen(rolle, par.welt(float(cp[0]), float(cp[1])), par.yaw_achse())
	figur.geh_zu("boden")
	hund = Hund.new()
	hund.main = main
	bt.s.root.add_child(hund)
	if not hund.starten(self):
		hund.queue_free()
		hund = null
	else:
		hund.setzen_welt(par.welt(float(cp[0]) - 1.5, float(cp[1]) + 1.2))
	regie = Regie.new(self)
	hud = Hud.new(self)
	add_child(hud)
	hud.set_touch(touch_an())
	_layers_aus()
	checkpoint_setzen("start")
	regie.hinter_figur()
	phase = "spiel"
	var sz := str(o.get("szene", ""))
	var n := 0
	for i in range(daten.SZENEN.size()):
		if str(daten.SZENEN[i]["id"]) == sz or str(i + 1) == sz:
			n = i
	if bool(o.get("figur_test", false)):
		szene_i = -1                                        # tests: just the figure, no scene
		ziel_text = tx("Folge dem Bach durch die Schlucht")
		return
	szene_starten(n)


var _sk_layer: CanvasLayer = null


func _start_karte(rolle0: String, name0: String) -> Dictionary:
	"""before the start: who you are (Enkelin, Enkel, Tochter, Sohn - 14–16 years) and your name"""
	var UI = preload("res://scripts/ui_style.gd")
	_sk_layer = CanvasLayer.new()
	_sk_layer.layer = 116
	add_child(_sk_layer)
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.02, 0.03, 0.05, 0.82)
	_sk_layer.add_child(bg)
	var pc := PanelContainer.new()
	pc.theme = UI.theme()
	pc.add_theme_stylebox_override("panel", UI.box(Color(0.06, 0.08, 0.11, 0.97), Color(1, 0.8, 0.45, 0.7), 16, 20, 1))
	_sk_layer.add_child(pc)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	pc.add_child(v)
	var t := Label.new()
	t.text = T.t("Die Karte des Grossvaters") + " · " + T.t("Kapitel 2") + "\n" + T.t(str(daten.TITEL))
	t.add_theme_font_size_override("font_size", 22)
	t.add_theme_color_override("font_color", Color(1, 0.88, 0.6))
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	var l := Label.new()
	l.text = T.t("Wer bist du? (14–16 Jahre)")
	v.add_child(l)
	var wahl := {"rolle": rolle0 if rolle0 in daten.ROLLEN else "tochter"}
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 8)
	v.add_child(row)
	var knoepfe := {}
	for r in daten.ROLLEN:
		var b := Button.new()
		b.text = T.t(str(daten.ROLLE_NAME[r]))
		b.toggle_mode = true
		b.custom_minimum_size = Vector2(110, 44)
		b.button_pressed = r == wahl["rolle"]
		var rr: String = r
		b.pressed.connect(func():
			wahl["rolle"] = rr
			for k2 in knoepfe:
				(knoepfe[k2] as Button).button_pressed = k2 == rr)
		row.add_child(b)
		knoepfe[r] = b
	var l2 := Label.new()
	l2.text = T.t("Dein Name")
	v.add_child(l2)
	var le := LineEdit.new()
	le.text = name0
	le.max_length = 16
	le.custom_minimum_size = Vector2(300, 44)
	v.add_child(le)
	var los := Button.new()
	los.text = T.t("Los geht's! ›")
	los.custom_minimum_size = Vector2(300, 50)
	UI.primary(los)
	los.pressed.connect(func(): start_gewaehlt.emit())
	le.text_submitted.connect(func(_t): start_gewaehlt.emit())
	v.add_child(los)
	var place := func():
		var s := get_viewport().get_visible_rect().size
		pc.size = Vector2.ZERO
		pc.position = (s - pc.get_combined_minimum_size()) * 0.5
	place.call_deferred()
	_start_karte_offen = true
	await start_gewaehlt
	_start_karte_offen = false
	wahl["name"] = le.text.strip_edges() if le.text.strip_edges() != "" else name0
	_sk_layer.queue_free()
	_sk_layer = null
	return wahl


var _start_karte_offen := false


func stop() -> void:
	if not running:
		return
	running = false
	phase = ""
	if regie != null:
		regie.zeitlupe_aus()
	Engine.time_scale = 1.0
	if figur != null:
		figur.weg()
	figur = null
	if hund != null and is_instance_valid(hund):
		hund._on_schluss()
		hund.queue_free()
	hund = null
	if par != null and is_instance_valid(par):
		par.aufraeumen()
		par.queue_free()
	par = null
	if hud != null and is_instance_valid(hud):
		hud.queue_free()
	hud = null
	_layers_zurueck()
	_ir_kegel_setzen(false)
	ir_an = false
	musik("")
	if main.has_method("_update_sky"):
		main._update_sky()                                     # the light as before (_licht())
	main.auto_visitors = bool(_saved.get("auto", true))
	main.bt_events = bool(_saved.get("bt_events", true))
	main.weather = str(_saved.get("weather", "clear"))
	main.bt_season = str(_saved.get("bt_season", "auto"))
	main.bt_spot = str(_saved.get("bt_spot", "huette"))
	main.bt_free = _saved.get("bt_free", [])
	main.bt_bed = str(_saved.get("bt_bed", "tent"))
	if _saved.get("bt_wall", null) != null:
		main.bt_wall = _saved["bt_wall"]
	main.set_hour(float(_saved.get("hour", 12.0)))
	main._set_speed(float(_saved.get("speed", 1.0)))
	var sc := str(_saved.get("scene", main.scene))
	if sc != "":
		main.set_scene(sc)


func _layers_aus() -> void:
	for n in get_tree().root.find_children("*", "CanvasLayer", true, false):
		if n == hud or not (n as CanvasLayer).visible:
			continue
		_layers[n] = true
		(n as CanvasLayer).visible = false


func _layers_zurueck() -> void:
	for n in _layers:
		if is_instance_valid(n):
			(n as CanvasLayer).visible = true
	_layers = {}


func touch_an() -> bool:
	if _touch_force >= 0:
		return _touch_force == 1
	return DisplayServer.is_touchscreen_available()


# =======================================================================================================================
# scenes and steps (data of the chapter)
# =======================================================================================================================
func szene_starten(n: int) -> void:
	if karte_an:
		karte_ende(false)
	szene_i = clampi(n, 0, daten.SZENEN.size() - 1)
	var sz: Dictionary = daten.SZENEN[szene_i]
	_log("szene:" + str(sz["id"]))
	if sz.has("start") and szene_i > 0 and (sz["start"] as Array).size() >= 2:
		var st: Array = sz["start"]
		if figur.pos().distance_to(par.welt(float(st[0]), float(st[1]))) > 8.0:   # only when far away (else: just go on)
			figur_setzen(float(st[0]), float(st[1]))
		regie.hinter_figur()
	weg = par.weg_punkte(daten.WEGE.get(str(sz["id"]), []))
	schritt_i = -1
	_naechster_schritt()


func _naechster_schritt() -> void:
	if not running:
		return
	var sz: Dictionary = daten.SZENEN[szene_i]
	var L: Array = sz["schritte"]
	schritt_i += 1
	if schritt_i >= L.size():
		if phase == "ende":
			return
		if szene_i + 1 < daten.SZENEN.size() and not bool(daten.SZENEN[szene_i + 1].get("offen", false)):
			szene_starten(szene_i + 1)
		else:
			ziel_text = tx("Ende von Kapitel 2 – Fortsetzung folgt.")
			_ziel_p = null
			schritt = {}
		return
	schritt = (L[schritt_i] as Dictionary).duplicate()
	if schritt.has("film"):
		if karte_an:
			karte_ende(false)
		phase = "film"
		figur.geh_zu("film")
		regie.spiele(schritt["film"], func(): _film_fertig())
	elif schritt.has("ziel"):
		schritt["_t0"] = uhr
		_hinweis_i = 0
		abschnitt_angebot = false
		ziel_text = tx(str(schritt["ziel"]))
		_ziel_p = _bis_ort(str(schritt.get("bis", "")))
		schritt["_ueber_i"] = 0
		_ueber_ziel()
		if str(schritt.get("bis", "")) == "aktion:maggie_spalt":
			_maggie_steuern(true)
	elif schritt.has("sag"):
		sag(tx(str(schritt["sag"])), str(schritt.get("wer", "erzaehler")))
		_naechster_schritt()
	elif schritt.has("musik"):
		musik(str(schritt["musik"]))
		_naechster_schritt()
	elif schritt.has("checkpoint"):
		checkpoint_setzen(str(schritt["checkpoint"]))
		_naechster_schritt()
	elif schritt.has("abzeichen"):
		var w := str(schritt.get("wenn", ""))
		var ok := true
		if w == "trocken":
			ok = int(figur.nass) == 0
		elif w.begins_with("nicht:"):
			ok = not merker.has(w.substr(6))
		elif w.begins_with("merker:"):
			ok = merker.has(w.substr(7))
		if ok:
			abzeichen_geben(str(schritt["abzeichen"]))
		_naechster_schritt()
	elif schritt.has("maggie"):
		if hund != null and str(schritt["maggie"]) == "riechen":
			hund.riechen(par.welt(float(schritt["s"]), float(schritt["q"])))
		_naechster_schritt()
	else:
		_naechster_schritt()


func _film_fertig() -> void:
	if not running:
		return
	film_move = Vector2.ZERO
	if phase == "film":
		phase = "spiel"
	if figur.zustand == "film":
		figur.geh_zu("haengen" if film_hang else "boden")
	if hund != null and hund.has_meta("sprung_ende"):          # Maggie jumped into the arms: back on her own feet
		hund.remove_meta("sprung_ende")
		hund.setzen_welt(figur.pos() + figur.vorne().cross(Vector3.UP) * 0.8)
	_naechster_schritt()


func _bis_ort(b: String):
	if b.begins_with("ort_tal:"):
		var pt := b.substr(8).split(",")
		return par.W(par.G(float(pt[0]), float(pt[1]), 1.0))
	if b.begins_with("ort:"):
		var p := b.substr(4).split(",")
		return par.welt(float(p[0]), float(p[1]), 1.0)
	if b.begins_with("fund:"):
		var id := b.substr(5)
		if par.dinge.has(id):
			var c: Vector2 = par.dinge[id]["c"]
			return par.welt(par.sq(c).x, par.sq(c).y)
	if b.begins_with("aktion:"):
		var ak: Dictionary = par.aktion(b.substr(7))
		if not ak.is_empty():
			var p2: Vector2 = ak["p"]
			return par.welt(par.sq(p2).x, par.sq(p2).y)
	return null


func _auf_hoehe(zp) -> bool:
	"""an «ort» goal on a ledge counts only up there, not at the foot of the wall below it (21.11.: «Klettere … hoch» was done
	at the bottom)"""
	if not (zp is Vector3):
		return true
	return absf(figur.pos().y - float(main.ground_y(zp.x, zp.z))) < 1.0


func _ueber_ziel() -> void:
	"""a step with «ueber» [[s, q, r], …]: the compass and the marker lead over these points first (the bridge head)"""
	var U: Array = schritt.get("ueber", [])
	var i := int(schritt.get("_ueber_i", 0))
	if i < U.size():
		_ziel_p = par.welt(float(U[i][0]), float(U[i][1]), 1.0)
	else:
		_ziel_p = _bis_ort(str(schritt.get("bis", "")))


const STECKEN_S := 90.0               # s without progress in one step: «Zum nächsten Abschnitt springen» in the pause menu
var abschnitt_angebot := false
var test_frei := false                # tests (kit_weg_test.gd): no steps, only walking


func _schritt_tick() -> void:
	if test_frei or schritt.is_empty() or not schritt.has("ziel") or phase != "spiel":
		return
	var U: Array = schritt.get("ueber", [])
	var ui := int(schritt.get("_ueber_i", 0))
	if ui < U.size():
		var mp: Vector2 = par.sq_von(figur.pos())
		if mp.distance_to(Vector2(float(U[ui][0]), float(U[ui][1]))) < float(U[ui][2]):
			schritt["_ueber_i"] = ui + 1
			schritt["_t0"] = uhr                          # progress: the hints and the offer start again
			_hinweis_i = 0
			_marker_t = 0.6
			_ueber_ziel()
	if not abschnitt_angebot and uhr - float(schritt.get("_t0", uhr)) > STECKEN_S:
		abschnitt_angebot = true
		_marker_t = 3.0
		sag(tx("Hängst du fest? Der leuchtende Punkt zeigt den Weg – oder im Pausenmenü: «Zum nächsten Abschnitt springen»."), "blinki")
	var b := str(schritt.get("bis", ""))
	var fertig := false
	if b.begins_with("ort:"):
		var p := b.substr(4).split(",")
		var me: Vector2 = par.sq_von(figur.pos())
		fertig = me.distance_to(Vector2(float(p[0]), float(p[1]))) < float(p[2]) and figur.zustand == "boden" and _auf_hoehe(_bis_ort(b))
	elif b.begins_with("ort_tal:"):
		var pt := b.substr(8).split(",")
		var me2: Vector2 = par.tal_von(figur.pos())
		fertig = me2.distance_to(Vector2(float(pt[0]), float(pt[1]))) < float(pt[2]) and figur.zustand == "boden" and _auf_hoehe(_bis_ort(b))
	elif b.begins_with("aktion:"):
		fertig = erledigt.has(b.substr(7))
	elif b.begins_with("fund:"):
		fertig = funde.has(b.substr(5))
	elif b.begins_with("zeit:"):
		fertig = uhr > float(schritt.get("_t0", uhr)) + float(b.substr(5))
	_hinweise_tick()
	if schritt.has("merke_halt") and par.ding_bei(figur.pos()) == str(schritt["merke_halt"]):   # stopping on the bridge
		if float(figur.a.cur_speed) < 0.3:
			_halt_t += get_process_delta_time()
			if _halt_t > 0.6:
				merke(str(schritt["merke_halt"]) + "_halt")
		else:
			_halt_t = 0.0
	if fertig:
		_naechster_schritt()


func ziel_welt():
	if steuer_maggie:
		return maggie_ziel()
	return _ziel_p


func maggie_ziel():
	"""while steering Maggie: first the window in the wall, then the bolt (the compass and the marker follow)"""
	var ak: Dictionary = par.aktion("maggie_spalt")
	if ak.is_empty() or hund == null:
		return _ziel_p
	var d: Dictionary = ak["d"]
	var hp: Vector3 = hund.ppos(hund.hund)
	var hs: Vector2 = par.sq(Vector2(hp.x, hp.z))
	if hs.x < float(d.get("hinter_wand", 37.5)) and d.has("fenster"):
		var f: Array = d["fenster"]
		return par.welt(float(f[0]), float(f[1]), float(f[2]))
	var z: Array = d["ziel"]
	return par.welt(float(z[0]), float(z[1]), 1.2)


const HINWEIS_STD := [[30.0, "Schau auf den Kompass: die gelbe Marke zeigt zum Ziel.", "blinki"], [55.0, "Folge dem leuchtenden Punkt.", "blinki"]]


func _hinweise_tick() -> void:
	"""a hint after some time without progress in a step: the step's own («hinweise» [[s, text, who]]), else two general ones"""
	if schritt.is_empty() or not schritt.has("ziel") or phase != "spiel":
		return
	var L: Array = schritt.get("hinweise", HINWEIS_STD)
	if _hinweis_i >= L.size():
		return
	var h: Array = L[_hinweis_i]
	if uhr - float(schritt.get("_t0", uhr)) > float(h[0]):
		_hinweis_i += 1
		sag(tx(str(h[1])), str(h[2]) if h.size() > 2 else "blinki")
		if _marker != null:
			_marker_t = 2.5                                      # the marker pulses stronger for a moment


# ---- the marker at the current target: a ring on the ground and a soft beam of light, pulsing --------------------------------
func _marker_tick(real_dt: float) -> void:
	var zp = ziel_welt() if phase == "spiel" else null
	if not (zp is Vector3):
		if _marker != null:
			_marker.visible = false
		return
	if _marker == null:
		_marker = Node3D.new()
		_marker.name = "kit_marker"
		add_child(_marker)
		var gm := StandardMaterial3D.new()
		gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		gm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		gm.albedo_color = Color(1.0, 0.78, 0.3, 0.55)
		gm.cull_mode = BaseMaterial3D.CULL_DISABLED
		var ring := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = 0.42
		tm.outer_radius = 0.55
		tm.rings = 24
		tm.ring_segments = 6
		ring.mesh = tm
		ring.scale = Vector3(1, 0.2, 1)
		ring.material_override = gm
		ring.name = "ring"
		_marker.add_child(ring)
		var beam := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.02
		cm.bottom_radius = 0.16
		cm.height = 3.0
		cm.radial_segments = 8
		cm.cap_top = false
		cm.cap_bottom = false
		beam.mesh = cm
		beam.position = Vector3(0, 1.5, 0)
		var bm := gm.duplicate() as StandardMaterial3D
		bm.albedo_color = Color(1.0, 0.8, 0.35, 0.22)
		beam.material_override = bm
		beam.name = "beam"
		_marker.add_child(beam)
		var dot := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.12
		sm.height = 0.24
		dot.mesh = sm
		dot.material_override = gm
		dot.name = "dot"
		_marker.add_child(dot)
	_marker.visible = true
	var p: Vector3 = zp
	var g: float = main.ground_y(p.x, p.z)
	var auf_boden: bool = absf(p.y - (g + 1.0)) < 0.2            # an «ort» goal (1 m over the ground): ring on the ground
	_marker.global_position = Vector3(p.x, g + 0.05, p.z) if auf_boden else p
	(_marker.get_node("ring") as Node3D).visible = auf_boden
	(_marker.get_node("beam") as Node3D).visible = auf_boden
	(_marker.get_node("dot") as Node3D).visible = not auf_boden
	_marker_t = maxf(0.0, _marker_t - real_dt)
	var puls := 1.0 + 0.18 * sin(uhr * 4.0) + 0.5 * _marker_t
	_marker.scale = Vector3.ONE * puls
	var near: bool = figur.pos().distance_to(p) < 1.6 and not steuer_maggie
	_marker.visible = not near


func nord_off() -> float:
	return float(bt.tal.rotation.y) if bt != null else 0.0


func tal_dir_welt(v: Vector2) -> Vector2:
	var w: Vector3 = bt.tal.transform.basis * Vector3(v.x, 0, v.y)
	return Vector2(w.x, w.z)


func checkpoint_setzen(id: String) -> void:
	var cp = daten.CHECKPOINTS.get(id, null)
	if cp == null:
		return
	checkpoint_id = id
	if cp is Dictionary:
		checkpoint = par.W(par.G(float(cp["tal"][0]), float(cp["tal"][1])))
	else:
		checkpoint = par.welt(float(cp[0]), float(cp[1]))
	_log("checkpoint:" + id)


func zurueck_zum_checkpoint() -> void:
	hud.blende(1.1)
	var cp: Vector3 = checkpoint
	get_tree().create_timer(0.5, true, false, true).timeout.connect(func():
		if not running or figur == null:
			return
		film_hang = false
		figur.setzen(cp, par.yaw_achse())
		figur.geh_zu("boden")
		if hund != null and hund.modus in ["folgen", "warten"]:
			hund.setzen_welt(cp + Vector3(1.0, 0, 1.0))
		regie.hinter_figur()
		musik("explore"))


# =======================================================================================================================
# every frame
# =======================================================================================================================
func _process(dt: float) -> void:
	if not running or phase == "laden" or figur == null or not figur.ok():
		return
	if main.scene != "bergtal":
		stop()
		return
	uhr += dt
	_fps_t += get_process_delta_time() / maxf(Engine.time_scale, 0.01)
	if _fps_t >= 1.0:
		_fps_t = 0.0
		fps_log.append(Engine.get_frames_per_second())
		if fps_log.size() > 30:
			fps_log.pop_front()
	var ein := eingabe(dt)
	set_meta("_roh_sprung", phase == "film" and (bool(ein.get("sprung", false)) or bool(ein.get("aktion", false))))
	if phase in ["pause", "ende"]:
		ein = {}
	if steuer_maggie and hund != null:
		if _maggie_auto:
			if hund.zustand_hund != "aktion":
				_maggie_ziel_pruefen(true)
		else:
			var mv: Vector2 = ein.get("mv", Vector2.ZERO)
			hund.steuern(mv, dt)
			_maggie_ziel_pruefen(bool(ein.get("aktion", false)))
		ein = {}
	_personen_tick(dt)
	if not qte.is_empty():
		if bool(ein.get("sprung", false)) or bool(ein.get("aktion", false)) or bool(get_meta("_roh_sprung", false)):
			merke(str(qte["id"]))
			figur.a.aktion("heben", 1.4)
			hud.toast(tx("Gefangen!"), 2.0)
			qte = {}
		elif uhr > float(qte["bis"]):
			qte = {}
	if karte_an:
		_karte_tick(dt, ein)
		ein = {"look": ein.get("look", Vector2.ZERO), "zoom": ein.get("zoom", 0.0)}
	if bool(ein.get("foto", false)):
		foto()
	if _figur_zug is Vector3:
		var to: Vector3 = _figur_zug - figur.pos()
		to.y = 0.0
		film_move = Vector2(to.x, to.z).normalized() * (1.0 if film_run else 0.7) if to.length() > 0.4 else Vector2.ZERO
		if to.length() <= 0.4:
			_figur_zug = null
			regie.zug_fertig("figur")
	figur.vor(dt, ein)
	set_meta("_ein", ein)
	if hud.touch != touch_an():
		hud.set_touch(touch_an())
	if _sub_bis > 0.0 and uhr > _sub_bis:
		_sub_bis = 0.0
		hud.untertitel("", "", Color.WHITE)


func spaet(dt: float, real_dt: float) -> void:
	"""after the actors (kit_spaet.gd): height, walls, actions, the camera, the HUD"""
	if not running or phase == "laden" or figur == null or not figur.ok():
		return
	var ein: Dictionary = get_meta("_ein", {})
	figur.nach(dt, ein)
	if not nach_klettern.is_empty() and figur.zustand == "boden":
		var alt := nach_klettern
		nach_klettern = {}
		if alt.has("d"):
			figur._balance_start(alt["d"])
	_schritt_tick()
	_marker_tick(real_dt)
	_licht()
	regie.tick(dt, real_dt, ein)
	hud.tick(real_dt)


# ---- input ------------------------------------------------------------------------------------------------------------------
var _k_alt := {}


func _taste(k: int) -> bool:
	return Input.is_key_pressed(k)


func _neu(key: String, on: bool) -> bool:
	var was := bool(_k_alt.get(key, false))
	_k_alt[key] = on
	return on and not was


func eingabe(dt: float) -> Dictionary:
	"""keyboard + game controller + touch → one wish; mv is in WORLD x/z, relative to the camera"""
	var f := 0.0
	var r := 0.0
	var run := false
	var sp := false
	var sp_h := false
	var akt := false
	var look := Vector2.ZERO
	var zoom := 0.0
	if not main.typing():
		if _taste(KEY_W) or _taste(KEY_UP):
			f += 1.0
		if _taste(KEY_S) or _taste(KEY_DOWN):
			f -= 1.0
		if _taste(KEY_D) or _taste(KEY_RIGHT):
			r += 1.0
		if _taste(KEY_A) or _taste(KEY_LEFT):
			r -= 1.0
		run = _taste(KEY_SHIFT)
		sp_h = _taste(KEY_SPACE)
		sp = _neu("space", sp_h)
		akt = _neu("e", _taste(KEY_E) or _taste(KEY_F))
		_foto_wunsch = _foto_wunsch or _neu("p", _taste(KEY_P))
	var k := Vector2(f, r)
	var pm = main.get("padmap")
	if pm != null:
		var ls: Vector2 = pm.stick_clean(1 if main.pad_swap else 0)
		var rs: Vector2 = pm.stick_clean(0 if main.pad_swap else 1)
		if ls.length() > 0.0:
			k += Vector2(-ls.y, ls.x)
			run = run or ls.length() > 0.97
		if rs.length() > 0.0:
			look += Vector2(rs.x * 2.4, -rs.y * 1.3 * (-1.0 if main.pad_inv_y else 1.0)) * dt
		run = run or pm.trig("r2") > 0.5
		sp_h = sp_h or pm.btn("a")
		sp = sp or pm.hit("a")
		akt = akt or pm.hit("x") or pm.hit("b")
		if pm.hit("start"):
			_pause_druck()
	if hud != null:
		var tc: Dictionary = hud.nimm_touch()
		var sv: Vector2 = tc["mv"]
		if sv.length() > 0.08:
			k += Vector2(-sv.y, sv.x)
			run = run or sv.length() > 0.96
		look += (tc["look"] as Vector2) * Vector2(0.006, 0.004)
		sp = sp or bool(tc["sprung"])
		sp_h = sp_h or bool(tc["sprung_h"])
		akt = akt or bool(tc["aktion"])
	look += _maus_look
	_maus_look = Vector2.ZERO
	zoom = _zoom
	_zoom = 0.0
	if not _test.is_empty():
		if uhr < float(_test["bis"]) or not bool(_test.get("_used", false)):
			_test["_used"] = true                         # (at least one frame, even when a frame is longer than the wish)
			var te: Dictionary = _test["ein"]
			if te.has("mv"):
				k = Vector2(float(te["mv"][0]), float(te["mv"][1]))
			run = bool(te.get("run", run))
			if bool(te.get("sprung", false)) and not bool(_test.get("_sp", false)):
				sp = true
				_test["_sp"] = true
			if bool(te.get("aktion", false)) and not bool(_test.get("_ak", false)):
				akt = true
				_test["_ak"] = true
			sp_h = sp_h or bool(te.get("halten", false))
		else:
			_test = {}
	k = k.limit_length(1.0)
	var cam: Camera3D = main.view_cam
	var fw := -cam.global_transform.basis.z
	fw.y = 0.0
	fw = fw.normalized() if fw.length() > 0.01 else Vector3(0, 0, -1)
	var rt := fw.cross(Vector3.UP).normalized()
	var mv3 := fw * k.x + rt * k.y
	if not _test.is_empty() and (_test["ein"] as Dictionary).has("ziel") and figur != null and figur.ok():
		var zw: Array = _test["ein"]["ziel"]                # tests (kit_weg_test.gd): straight to a world point
		var to := Vector3(float(zw[0]), 0, float(zw[1])) - Vector3(figur.pos().x, 0, figur.pos().z)
		mv3 = to.normalized() if to.length() > 0.05 else Vector3.ZERO
	var quer := 0.0
	if figur != null and figur.ok() and figur.zustand == "balance":
		var right_f: Vector3 = figur.vorne().cross(Vector3.UP).normalized()
		quer = mv3.dot(right_f)
	var fo := _foto_wunsch
	_foto_wunsch = false
	if hud != null and hud.tap_foto:
		fo = true
		hud.tap_foto = false
	return {"foto": fo, "mv": Vector2(mv3.x, mv3.z), "run": run, "sprung": sp, "sprung_h": sp_h, "aktion": akt, "vor": k.x,
		"quer": quer, "look": look, "zoom": zoom}


var _maus_look := Vector2.ZERO
var _foto_wunsch := false
var _zoom := 0.0


func _input(ev: InputEvent) -> void:
	if not running or phase == "laden":
		return
	if ev is InputEventKey and ev.pressed and not ev.echo:
		var kc: int = (ev as InputEventKey).keycode
		if kc == KEY_ESCAPE:
			if phase == "film":
				ueberspringen()
			else:
				_pause_druck()
			get_viewport().set_input_as_handled()
			return
		if phase == "film" and kc in [KEY_SPACE, KEY_ENTER]:
			ueberspringen()
			get_viewport().set_input_as_handled()
			return
	if ev is InputEventKey and phase != "pause" and not main.typing():
		get_viewport().set_input_as_handled()            # W A S D, Space, E … belong to the game (not the fly view)


func _unhandled_input(ev: InputEvent) -> void:
	if not running or phase in ["laden", "pause"]:
		return
	if ev is InputEventMouseMotion and (ev.button_mask & (MOUSE_BUTTON_MASK_LEFT | MOUSE_BUTTON_MASK_RIGHT)) != 0 and not (hud != null and hud.touch):
		_maus_look += Vector2(ev.relative.x * 0.006, ev.relative.y * 0.004)
		get_viewport().set_input_as_handled()
	elif ev is InputEventMouseButton and ev.pressed:
		if ev.button_index == MOUSE_BUTTON_WHEEL_UP:
			_zoom -= 0.5
		elif ev.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_zoom += 0.5
		get_viewport().set_input_as_handled()


func _pause_druck() -> void:
	pause(phase != "pause")


func pause(on: bool) -> void:
	if not running:
		return
	if on and phase != "pause":
		_pause_vor = phase
		phase = "pause"
		regie.zeitlupe_aus()
		hud.menu(true)
	elif not on and phase == "pause":
		phase = _pause_vor if _pause_vor != "" else "spiel"
		hud.menu(false)


func ueberspringen() -> void:
	if phase == "film":
		regie.ueberspringen()


func abschnitt_springen() -> void:
	"""the way out when stuck (pause menu after STECKEN_S): the goal of this step counts as reached"""
	pause(false)
	if schritt.is_empty() or not schritt.has("ziel"):
		return
	var b := str(schritt.get("bis", ""))
	_log("abschnitt_springen:" + b)
	hud.blende(1.0)
	if b.begins_with("ort:"):
		var p := b.substr(4).split(",")
		figur_setzen(float(p[0]), float(p[1]))
		figur.geh_zu("boden")
	elif b.begins_with("ort_tal:"):
		var pt := b.substr(8).split(",")
		figur.setzen(par.W(par.G(float(pt[0]), float(pt[1]))))
		figur.geh_zu("boden")
	elif b.begins_with("aktion:"):
		var id := b.substr(7)
		if id == "maggie_spalt":
			_maggie_auto = false
			_maggie_steuern(false)
		if id == "karte" and karte_an:
			karte_ende(true)
		aktion_fertig(id)
	elif b.begins_with("fund:"):
		var fid := b.substr(5)
		if par.dinge.has(fid) and bool(par.dinge[fid]["d"].get("nur_ir", false)) and not ir_an:
			ir_umschalten()
		fund(fid)
	abschnitt_angebot = false
	regie.hinter_figur()


func kinder_umschalten() -> void:
	kinder = not kinder
	figur.kinder = kinder
	hud.toast(T.t("Kindermodus an") if kinder else T.t("Kindermodus aus"))


# =======================================================================================================================
# what the parts call
# =======================================================================================================================
func sag(text: String, wer: String, d := 0.0) -> void:
	if hud == null:
		return
	if text == "":
		hud.untertitel("", "", Color.WHITE)
		_sub_bis = 0.0
		return
	var sp: Array = daten.SPRECHER.get(wer, ["", Color.WHITE])
	var nm := tx(str(sp[0])) if str(sp[0]) != "" else ""
	hud.untertitel(text, nm, sp[1])
	_sub_bis = uhr + (d if d > 0.0 else clampf(1.4 + text.length() * 0.055, 2.2, 7.0))
	if figur != null and figur.ok() and wer == "figur":
		figur.a.sprechen(minf(3.0, text.length() * 0.06))
	_log("sag:" + wer)


func ton(nm: String) -> void:
	var k = main.get("klang")
	if k != null and k.has_method("kit_ton"):
		k.kit_ton(nm)


func musik(z: String) -> void:
	musik_z = z
	var k = main.get("klang")
	if k != null and k.has_method("musik_zustand"):
		k.musik_zustand(z)


func film_eintrag(e: Dictionary, sprung: bool) -> void:
	"""film keys of the chapters beyond the camera (kit_regie.gd _eintrag hands them over)"""
	match str(e.get("k", "")):
		"bruecke_einsturz":
			par.bruecke_einsturz(float(e.get("ab_q", 0.0)))
			if not sprung:
				regie.schuetteln(0.6)
		"maggie_sprung":
			if hund != null:
				var von: Vector3 = par.welt(float(e["s"]), float(e["q"]))
				if sprung:
					hund.setzen_welt(figur.pos() + figur.vorne() * 0.8)
				else:
					hund.setzen_welt(von)
					hund.heben(von, par.VL(figur.pos() + Vector3(0, 1.1, 0) + figur.vorne() * 0.35))
					hund.set_meta("sprung_ende", true)
		"qte":
			if not sprung:
				qte = {"id": str(e["id"]), "text": tx(str(e.get("text", "Greifen!"))), "bis": uhr + float(e.get("s", 1.5))}
		"person":
			_person(str(e["id"]), e)
		"person_weg":
			var a = personen.get(str(e["id"]), null)
			if a != null and is_instance_valid(a):
				a.queue_free()
			personen.erase(str(e["id"]))
			_person_ziel.erase(str(e["id"]))
		"zeit":
			main.set_hour(float(e["h"]))
		"ir":
			if ir_an != bool(e.get("an", false)):
				ir_umschalten()
		"figur_tal":
			film_hang = false
			figur.setzen(par.W(par.G(float(e["x"]), float(e["z"]))))
			if hund != null:
				hund.setzen_welt(par.W(par.G(float(e["x"]) + 1.2, float(e["z"]) + 0.8)))
		"tier":
			if not sprung and bt != null:
				var f: Vector3 = par.G(float(e["tal"][0]), float(e["tal"][1]))
				var t: Vector3 = par.G(float(e["nach_tal"][0]), float(e["nach_tal"][1]))
				main.spawn(str(e.get("art", "fox")), par.W(f), par.W(t))
		"maggie_warnen":
			if hund != null and not sprung:
				hund.warnen(par.welt(float(e["s"]), float(e["q"])))
		"maggie_warnen_tal":
			if hund != null and not sprung:
				hund.warnen(par.W(par.G(float(e["x"]), float(e["z"]))))
		"ende":
			phase = "ende"
			ziel_text = ""
			hud.ende(tx(str(e.get("text", ""))), abzeichen.keys())
			musik("entdeckung")


func _person(id: String, e: Dictionary) -> void:
	var old = personen.get(id, null)
	if old != null and is_instance_valid(old):
		old.queue_free()
	var p: Vector2 = par.tal(float(e["s"]), float(e["q"]))
	var b: Array = e.get("blick", [float(e["s"]) + 1.0, float(e["q"])])
	var lb: Vector2 = par.tal(float(b[0]), float(b[1]))
	var jc: Array = e.get("jacke", [0.5, 0.5, 0.5])
	var a = par.actor("person", par.G(p.x, p.y), par.G(lb.x, lb.y), 1.3, Color(float(jc[0]), float(jc[1]), float(jc[2])))
	a.name = "kit_" + id
	personen[id] = a


func _personen_tick(dt: float) -> void:
	for id in _person_ziel.keys():
		var a = personen.get(id, null)
		if a == null or not is_instance_valid(a):
			_person_ziel.erase(id)
			continue
		var q: Vector3 = par.VL(_person_ziel[id])
		if par.walk(a, Vector3(q.x, 0, q.z), 2.2, dt):
			_person_ziel.erase(id)
			regie.zug_fertig(id)


func zeitlupe(f: float, s: float) -> void:
	regie.zeitlupe(f, s)


func wasser(p: Vector3) -> void:
	ton("platsch")
	merke("nass")
	sag(tx("Platsch! Nasse Füsse … zurück zum letzten Punkt."), "blinki")


func merke(id: String) -> void:
	merker[id] = true


func aktion_fertig(id: String) -> void:
	erledigt[id] = true
	if par != null:
		par.erledigt[id] = true
	_log("aktion:" + id)


func fund(id: String) -> void:
	if funde.has(id):
		return
	var fd: Dictionary = par.dinge.get(id, {}).get("d", {})
	if bool(fd.get("nur_ir", false)) and not ir_an:
		sag(tx("Hier ist nichts zu sehen … im normalen Licht."), "figur")
		return
	funde[id] = true
	aktion_fertig(id)
	par.fund_weg(id)
	figur.a.aktion("aufheben", 1.4)
	var f: Array = daten.FUNDE.get(id, [id, ""])
	hud.toast(T.t("Gefunden: %s") % tx(str(f[0])), 3.5)
	ton("fund")
	var alle := true
	for f2 in daten.FUNDE_ALLE:
		alle = alle and funde.has(f2)
	if alle:
		abzeichen_geben("alle_funde")


func abzeichen_geben(id: String) -> void:
	if abzeichen.has(id):
		return
	abzeichen[id] = true
	var a: Array = daten.ABZEICHEN.get(id, [id, ""])
	hud.toast(T.t("Abzeichen: %s") % T.t(str(a[0])), 4.0)
	ton("abzeichen")


func figur_setzen(sv: float, qv: float) -> void:
	film_hang = false
	figur.setzen(par.welt(sv, qv), par.yaw_achse())
	if hund != null and hund.modus in ["folgen", "warten"]:
		hund.setzen_welt(par.welt(sv - 1.5, qv + 1.0))


func film_haengen(sv: float, qv: float) -> void:
	"""the cold open: the figure hangs at the edge of the thing under [s, q]"""
	var id: String = par.ding_bei(par.welt(sv, qv))
	var top: float = par.top_welt(id) if id != "" else par.welt(sv, qv).y
	var me: Vector3 = par.welt(sv, qv)
	film_hang_p = Vector3(me.x, top, me.z)
	var inner: Vector3 = par.welt(sv, qv - 0.8)
	film_hang_auf = Vector3(inner.x, top, inner.z)
	film_hang = true
	figur.akt = {"griff": film_hang_p, "auf": film_hang_auf, "art": "rand", "von": {}}


func spiel_haengen() -> void:
	"""the film ends hanging: the player pulls up"""
	figur.hoch = 0.0
	figur.akt = {"griff": film_hang_p, "auf": film_hang_auf, "art": "rand", "von": {}}


func zug(wer: String, w: Vector3, sofort: bool) -> void:
	if wer == "maggie" and hund != null:
		if sofort:
			hund.setzen_welt(w)
			regie.zug_fertig("maggie")
		else:
			hund.zur_figur_laufen(w)
	elif wer == "figur":
		if sofort:
			figur.setzen(w)
			regie.zug_fertig("figur")
		else:
			_figur_zug = w
			film_run = bool(regie.film_eintrag_jetzt.get("rennen", false)) if regie.get("film_eintrag_jetzt") is Dictionary else false
	elif personen.has(wer):
		if sofort:
			var q: Vector3 = par.VL(w)
			par.place(personen[wer], Vector3(q.x, 0, q.z))
			regie.zug_fertig(wer)
		else:
			_person_ziel[wer] = w


var _figur_zug = null
var film_run := false


# ---- Maggie --------------------------------------------------------------------------------------------------------------------
func spieler_pos() -> Vector3:
	return figur.pos() if figur != null and figur.ok() else main.view_cam.global_position


func region_aktiv() -> String:
	return ""


func hund_pos() -> Vector3:
	return hund.welt() if hund != null else spieler_pos()


func hund_heading() -> float:
	return hund.heading() if hund != null else 0.0


func hund_tempo() -> float:
	return float(hund.tempo) if hund != null else 0.0


func _sperrt(id: String) -> bool:
	return par.dinge.has(id) and str(par.dinge[id]["d"]["art"]) in ["wand", "tor"] and not (par.dinge[id]["decks"] as Array).is_empty()


func maggie_frei(a: Vector2, b: Vector2) -> bool:
	"""can Maggie walk straight from a to b (valley)? Walls and closed gates stop her"""
	for id in par.dinge:
		if not _sperrt(str(id)):
			continue
		for dk in par.dinge[id]["decks"]:
			for i in range(1, 9):
				if par._in(dk, a.lerp(b, i / 8.0), 0.1):
					return false
	return true


func maggie_hoehe(v: Vector2):
	"""on a stone / step: its top (valley height), else null (the ground)"""
	var id: String = par.ding_bei(par.welt_abs(par.sq(v).x, par.sq(v).y, 0.0))
	if id == "" or _sperrt(id):
		return null
	return float(par.dinge[id]["top"])


func maggie_boden(von: Vector2, nach: Vector2, y_jetzt := -1.0e9):
	"""steering Maggie: false = blocked; else the height to keep (null = the ground). The window of a wall lets her
	through at the height of the ledge; down from a ledge she jumps; up only onto low things"""
	var sqn: Vector2 = par.sq(nach)
	var ak: Dictionary = par.aktion("maggie_spalt")
	var ziel: Array = ak["d"]["ziel"] if not ak.is_empty() else [0, 0]
	if absf(sqn.x - float(ziel[0])) > 6.0 or absf(sqn.y) > 8.5:
		return false
	var hv = maggie_hoehe(von)
	if y_jetzt > par._H(von.x, von.y) + 0.3:
		hv = y_jetzt                                         # up on a ledge / in the window: she keeps her height
	var hn_id: String = par.ding_bei(par.welt_abs(sqn.x, sqn.y, 0.0))
	if hn_id != "" and _sperrt(hn_id):
		var d: Dictionary = par.dinge[hn_id]["d"]
		var fe = d.get("fenster", null)
		if fe is Array and absf(sqn.y - float(fe[0])) < float(fe[1]) and hv != null:
			return hv                                        # through the window at ledge height
		return false
	if hn_id != "":
		var top := float(par.dinge[hn_id]["top"])
		var cur: float = hv if hv != null else bt.H(von.x, von.y)
		if top - cur > 0.6:
			return false
		return top
	if hv != null:
		var g: float = bt.H(nach.x, nach.y)
		if float(hv) - g > 0.05:
			var past_wall := true
			for id in par.dinge:
				if _sperrt(str(id)) and absf(sqn.x - par.sq(par.dinge[id]["c"]).x) < 0.7:
					past_wall = false
			if not past_wall:
				return hv                                    # still in the window
	return null


func maggie_heben(d: Dictionary) -> void:
	if hund == null:
		aktion_fertig("maggie_heben")
		return
	var na: Array = d["nach"]
	var e: Dictionary = par.dinge[str(d["ding"])]
	var t: Vector2 = par.tal(float(na[0]), float(na[1]))
	hund.heben(figur.pos() + figur.vorne() * 0.6, Vector3(t.x, float(e["top"]), t.y))
	sag(tx("Hopp!"), "figur")


func _maggie_steuern(on: bool) -> void:
	steuer_maggie = on
	_maggie_auto = false
	if on:
		figur.geh_zu("steuern")
		regie.zu_maggie(true)
		hud.toast(T.t("Du steuerst jetzt Maggie"), 3.0)
	else:
		figur.geh_zu("boden")
		regie.zu_maggie(false)
		if hund != null:
			hund.modus = "folgen"


func _maggie_ziel_pruefen(fertig_machen := false) -> void:
	"""within 1.3 m of the bolt: done (no button needed); once she is through the window and down on the far side she walks
	the last metres by herself (the owner got stuck here, 21.11.)"""
	var ak: Dictionary = par.aktion("maggie_spalt")
	if ak.is_empty() or hund == null:
		return
	var z: Array = ak["d"]["ziel"]
	var hp: Vector3 = hund.ppos(hund.hund)
	var hs: Vector2 = par.sq(Vector2(hp.x, hp.z))
	var hy: float = hund.VL(hund.hund.global_position).y
	var unten: bool = hy < par._H(hp.x, hp.z) + 0.3
	if not _maggie_auto and hs.x > float(ak["d"].get("hinter_wand", 37.5)) and unten and hs.distance_to(Vector2(float(z[0]), float(z[1]))) >= 1.3:
		_maggie_auto = true
		var zt: Vector2 = par.tal(float(z[0]), float(z[1]))
		hund.modus = "folgen"
		hund._aktion([{"t": "walk", "p": Vector3(zt.x, 0, zt.y), "spd": 2.6}])
		sag(tx("Drüben! Maggie läuft zum Riegel."), "figur")
		return
	if hs.distance_to(Vector2(float(z[0]), float(z[1]))) < 1.3 or (fertig_machen and _maggie_auto):
		_maggie_auto = false
		hund.bellen(hp, 2)
		hund.idle(hund.hund, "root", 1.2)
		_maggie_steuern(false)
		aktion_fertig("maggie_spalt")
		abzeichen_merk_maggie()


func abzeichen_merk_maggie() -> void:
	merke("maggie_riegel")


func _licht() -> void:
	"""warm stylised light and some depth in the gorge (art pass 21.11.): main._update_sky sets the light every 0.5 s,
	this sets absolute values after it every frame (nothing adds up); stop() calls main._update_sky() again"""
	if main.env == null or main.sun == null or ir_an:
		return
	var tag := clampf(float(main.sun.light_energy) / 1.4, 0.0, 1.0)
	if tag < 0.05:
		return                                               # the night stays as main makes it
	main.sun.light_color = Color(1.0, 0.86, 0.68)
	main.env.ambient_light_color = Color(0.86, 0.74, 0.62)
	main.env.fog_light_color = Color(0.93, 0.8, 0.62) * (0.15 + 0.85 * tag)
	main.env.fog_density = maxf(float(main.env.fog_density), 0.0045)


var ir_an := false


# ---- the map piece over the landscape (cairn puzzle) ------------------------------------------------------------------------
func karte_start(d: Dictionary) -> void:
	karte_an = true
	var z: Array = d["richtung_tal"]
	_karte = {"ziel": Vector2(float(z[0]), float(z[1])), "gut": 0.0}
	figur.geh_zu("steuern")
	regie.drag_t = uhr + 1000.0                             # the camera does not swing back by itself
	hud.karte(true)


func _karte_tick(dt: float, ein: Dictionary) -> void:
	var cam: Camera3D = main.view_cam
	var fw: Vector3 = bt.tal.global_transform.basis.inverse() * (-cam.global_transform.basis.z)
	var me: Vector2 = par.tal_von(figur.pos())
	var to: Vector2 = (_karte["ziel"] as Vector2) - me
	var diff := wrapf(atan2(to.x, -to.y) - atan2(fw.x, -fw.z), -PI, PI)
	hud.karte_lage(diff)
	if absf(diff) < 0.2:
		_karte["gut"] = float(_karte["gut"]) + dt
	else:
		_karte["gut"] = 0.0
	if kinder and absf(diff) < 0.5:
		_karte["gut"] = float(_karte["gut"]) + dt
	if float(_karte["gut"]) > 0.8:
		karte_ende(true)
	elif bool(ein.get("aktion", false)) and uhr - float(_karte.get("t0", -10.0)) > 0.4:
		karte_ende(false)


func karte_ende(ok: bool) -> void:
	karte_an = false
	hud.karte(false)
	figur.geh_zu("boden")
	regie.drag_t = uhr
	if ok:
		aktion_fertig("karte")
		ton("fund")


# ---- MoveEye at the camp: IR light, photo ------------------------------------------------------------------------------------
var _ir_kegel: MeshInstance3D = null


func _ir_kegel_setzen(on: bool) -> void:
	"""the IR light of MoveEye as a visible cone (in the IR view it shines), from the head towards the marked rock"""
	if _ir_kegel != null and is_instance_valid(_ir_kegel):
		_ir_kegel.queue_free()
	_ir_kegel = null
	if not on or main.head == null:
		return
	var ziel: Vector3 = par.welt_abs(0, 0, 0)
	if par.dinge.has("ir_fels"):
		var c: Vector2 = par.dinge["ir_fels"]["c"]
		ziel = par.W(par.G(c.x, c.y, 0.6))
	var von: Vector3 = (main.head as Node3D).global_position
	var L := maxf(1.0, von.distance_to(ziel) + 1.0)
	var cm := CylinderMesh.new()
	cm.top_radius = 0.06
	cm.bottom_radius = L * 0.28
	cm.height = L
	cm.radial_segments = 16
	cm.cap_bottom = false
	var mt := StandardMaterial3D.new()
	mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mt.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mt.albedo_color = Color(0.55, 0.42, 0.42, 0.16)
	mt.cull_mode = BaseMaterial3D.CULL_DISABLED
	_ir_kegel = MeshInstance3D.new()
	_ir_kegel.mesh = cm
	_ir_kegel.material_override = mt
	_ir_kegel.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_ir_kegel)
	var ax := (ziel - von).normalized()
	var side := ax.cross(Vector3.UP if absf(ax.y) < 0.95 else Vector3.RIGHT).normalized()
	_ir_kegel.global_transform = Transform3D(Basis(side, -ax, side.cross(-ax)).orthonormalized(), von + ax * L * 0.5)


func ir_umschalten() -> void:
	ir_an = not ir_an
	hud.farbe("ir" if ir_an else "")
	par.ir_sichtbar(ir_an)
	_ir_kegel_setzen(ir_an)
	if ir_an:
		aktion_fertig("ir")
		sag(tx("MoveEye: IR-Licht an."), "blinki")


func foto() -> void:
	"""photo mode: the picture of the view (without the HUD) goes to the backpack (user://grossvater/fotos)"""
	if hud == null:
		return
	hud.blitz()
	var img := get_viewport().get_texture().get_image()
	if img != null and not img.is_empty():
		DirAccess.make_dir_recursive_absolute("user://grossvater/fotos")
		fotos += 1
		img.resize(maxi(1, img.get_width() / 2), maxi(1, img.get_height() / 2))
		img.save_jpg("user://grossvater/fotos/k2_%d_%d.jpg" % [int(Time.get_unix_time_from_system()), fotos], 0.85)
	aktion_fertig("foto")
	hud.toast(tx("Foto im Rucksack (Tagebuch)"), 2.5)


func schritt_sync() -> void:
	"""after a jump of the figure (tests, screenshots, checkpoints): the step whose goal is nearest ahead becomes the current
	one - the goal line and the compass follow (no films are played)"""
	if szene_i < 0:
		return
	var me: Vector2 = par.tal_von(figur.pos())
	var me_s: float = par.sq(me).x
	var best := [-1, -1]
	var bd := 1.0e9
	for i in range(daten.SZENEN.size()):
		var L: Array = daten.SZENEN[i]["schritte"]
		for j in range(L.size()):
			if not (L[j] as Dictionary).has("ziel"):
				continue
			var p = _bis_ort(str(L[j].get("bis", "")))
			if not (p is Vector3):
				continue
			var t: Vector2 = par.tal_von(p)
			var ds: float = par.sq(t).x - me_s
			var d: float = me.distance_to(t)
			if ds < -1.0 and d > 3.0:
				continue                                      # behind (along the gorge)
			if d < bd:
				bd = d
				best = [i, j]
	if best[0] < 0:
		return
	szene_i = best[0]
	schritt_i = best[1] - 1
	_naechster_schritt()


func filmcheck() -> Array:
	"""every camera shot of every film: subject big enough, in the picture, nothing in front (kit_regie.gd pruef_shot)"""
	var out := []
	for sz in daten.SZENEN:
		var si := 0
		for st in sz["schritte"]:
			si += 1
			if not st.has("film"):
				continue
			for e in st["film"]:
				if str(e.get("k", "")) != "shot":
					continue
				var r: Dictionary = regie.pruef_shot(e)
				if bool(r.get("folge", false)):
					continue
				r["wo"] = "%s/%d t=%.1f %s" % [sz["id"], si, float(e.get("t", 0.0)), str(e.get("art", ""))]
				r.erase("kamera")
				out.append(r)
	return out


func _log(s: String) -> void:
	log_.append([snappedf(uhr, 0.01), s])
	if log_.size() > 60:
		log_.pop_front()


# =======================================================================================================================
# tests / remote control
# =======================================================================================================================
func info() -> Dictionary:
	var o := {"running": running, "phase": phase, "uhr": snappedf(uhr, 0.01), "rolle": rolle, "name": name_, "kinder": kinder,
		"szene": str(daten.SZENEN[szene_i]["id"]) if running and szene_i >= 0 else "", "schritt": schritt_i, "ziel": ziel_text,
		"checkpoint": checkpoint_id, "erledigt": erledigt.keys(), "funde": funde.keys(), "abzeichen": abzeichen.keys(),
		"merker": merker.keys(), "musik": musik_z, "touch": touch_an(), "log": log_.slice(-12), "lite": Quality.lite(),
		"steuer_maggie": steuer_maggie, "fps": fps_log.slice(-10), "time_scale": Engine.time_scale,
		"abschnitt_angebot": abschnitt_angebot, "ueber_i": int(schritt.get("_ueber_i", 0)), "weg": weg.size()}
	if running and figur != null and figur.ok():
		o["figur"] = figur.info()
		o["kamera"] = regie.info()
		o["parcours"] = par.info()
		if hund != null:
			o["maggie"] = hund.kit_info()
	return o


static func control(m, d: Dictionary) -> Dictionary:
	var k = ensure(m)
	match str(d.get("do", "info")):
		"info":
			return {"ok": true, "kit": k.info()}
		"start":
			k.start.call_deferred(d)
			return {"ok": true}
		"startwahl":                                        # tests / screenshots: confirm the start card
			if k._start_karte_offen:
				k.start_gewaehlt.emit()
			return {"ok": true}
		"stop":
			k.stop()
			return {"ok": true}
	if not k.running or k.figur == null:
		return {"ok": false, "error": "Kit läuft nicht"}
	match str(d.get("do", "")):
		"szene":
			var v := str(d.get("value", "1"))
			for i in range(k.daten.SZENEN.size()):
				if str(k.daten.SZENEN[i]["id"]) == v or str(i + 1) == v:
					if k.phase == "film":
						k.regie.film_an = false
						k.regie.balken_ziel = 0.0
						k.regie.zeitlupe_aus()
					k.hud.farbe("ir" if k.ir_an else "")       # (a jump out of the flashback: the colours back)
					for pid in k.personen.keys():
						if is_instance_valid(k.personen[pid]):
							k.personen[pid].queue_free()
					k.personen.clear()
					k._person_ziel.clear()
					k.phase = "spiel"
					k.figur.geh_zu("boden")
					k.szene_starten(i)
					return {"ok": true, "kit": k.info()}
			return {"ok": false, "error": "keine Szene " + v}
		"eingabe":
			var e := {}
			for key in ["mv", "run", "sprung", "aktion", "halten", "ziel"]:
				if d.has(key):
					e[key] = d[key]
			k._test = {"ein": e, "bis": k.uhr + float(d.get("s", 0.5))}
			return {"ok": true}
		"setzen":
			if k.steuer_maggie:
				k._maggie_steuern(false)
			if d.has("tal"):
				k.film_hang = false
				k.figur.setzen(k.par.W(k.par.G(float(d["tal"][0]), float(d["tal"][1]))))
			else:
				k.figur_setzen(float(d.get("s", 0.0)), float(d.get("q", 0.0)))
			k.figur.geh_zu("boden")
			if bool(d.get("sync", false)):
				k.schritt_sync()
			if d.has("blick"):
				k.figur.a.heading = float(d["blick"])
				k.figur.a.rotation.y = k.figur.a.heading
			k.regie.hinter_figur()
			return {"ok": true, "kit": k.info()}
		"aktion":
			k.aktion_fertig(str(d.get("id", "")))
			return {"ok": true}
		"abschnitt":                                       # «Zum nächsten Abschnitt springen» (tests: also before 90 s)
			k.abschnitt_springen()
			return {"ok": true, "kit": k.info()}
		"frei":                                            # tests: walking only, no steps
			k.test_frei = bool(d.get("on", true))
			return {"ok": true}
		"skip":
			k.ueberspringen()
			return {"ok": true}
		"pause":
			k.pause(bool(d.get("on", true)))
			return {"ok": true}
		"touch":
			k._touch_force = 1 if bool(d.get("on", true)) else 0
			return {"ok": true}
		"kamera":
			if str(d.get("art", "")) == "folge":
				k.regie.zur_folge(0.0)
				if d.has("yaw_off"):
					k.regie.yaw = float(k.figur.a.heading) + float(d["yaw_off"])
					k.regie.drag_t = k.uhr + 100.0
			else:
				k.regie.shot(d)
			return {"ok": true}
		"musik":
			k.musik(str(d.get("z", "explore")))
			return {"ok": true}
		"filmcheck":
			return {"ok": true, "shots": k.filmcheck()}
		"sag":
			k.sag(k.tx(str(d.get("text", ""))), str(d.get("wer", "erzaehler")))
			return {"ok": true}
		"maggie":
			if k.hund == null:
				return {"ok": false, "error": "keine Maggie"}
			match str(d.get("was", "")):
				"riechen":
					k.hund.riechen(k.par.welt(float(d.get("s", 20.0)), float(d.get("q", 0.0))))
				"warnen":
					k.hund.warnen(k.par.welt(float(d.get("s", 20.0)), float(d.get("q", 0.0))))
				"steuern":
					k._maggie_steuern(bool(d.get("on", true)))
			return {"ok": true, "maggie": k.hund.kit_info()}
	return {"ok": false, "error": "unbekannt"}
