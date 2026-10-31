extends Node
## Trailer (Daniel 31.10.2026): je ein Kino-Trailer (≈ 3 Min.) für «Die Karte des Grossvaters» und «Maggie und der Bergkristall» –
## eine geskriptete Kamerafahrt in Echtzeit im echten Bergtal (Orte, Figuren, Tiere, Wetter), mit Musik, Geräuschen,
## Texttafeln und Erzähler. Aufbau wie ein Kinotrailer: ruhiger Einstieg, Aufbau, schnellere Schnitte, Andeutung des
## Höhepunkts, Stille, Titelkarte, am Schluss «Jetzt spielen». Die Szenen stehen in trailer_buehne.gd, die Klänge in trailer_ton.gd.
##   * Start: Story-Karte unter «Spielen» (geschichten.gd), Knopf «Trailer ansehen» unter «Weiterspielen» / «Neu beginnen».
##     Esc oder ein Klick bricht ab, danach ist wieder das Fenster «Spielen» offen. Am Schluss «Jetzt spielen» (= wie
##     «Weiterspielen» bzw. der Start der Geschichte) oder «Zurück». Der Vorführmodus (maggie_vorfuehrung.gd) ist davon getrennt.
##   * Eine Sperre wie alle Simulator-Aufgaben: läuft schon etwas (main.busy_with), startet der Trailer nicht; während er läuft,
##     meldet busy_with «Trailer». Die Welt (Szene, Uhrzeit, Wetter, Schlafplatz, Jahreszeit, Bedienfeld) kommt danach zurück.
##   * Erzähler: die Sprachausgabe des Systems (abenteuer_stimme.gd), nur wenn es für die Sprache eine Stimme gibt; sonst
##     Untertitel unten im schwarzen Balken (Romanisch hat meist keine Stimme). Texte über T.t() in allen fünf Sprachen.
##   * Videodatei: werkzeuge/trailer_aufnehmen.sh startet den Simulator mit dem Godot Movie Maker (--write-movie, feste fps –
##     unabhängig vom Tempo des PCs) und diesen Startoptionen (nach «--»):
##       --trailer grossvater|maggie   --trailer-sprache de|fr|it|rm|en   --trailer-untertitel auto|an|aus
##       --trailer-cues <datei.json> (Zeiten der Erzählersätze für die Tonspur)   --trailer-ab <s>   --trailer-bis <s>
##       --trailer-bilder <ordner> (Standbilder statt Film; --trailer-zeiten 10,25.5,…)   --trailer-quit (danach beenden)
##     Im Movie-Maker-Modus spricht der Simulator nicht selbst (die Systemstimme käme nicht in die Datei); das Skript legt
##     die Sätze (espeak-ng, falls vorhanden) nach den Zeiten in der cues-Datei auf die Tonspur.
## Lite (Quality.lite()): keine Funken am Kristall, weniger Krähen; die Kamerafahrten bleiben (kosten nichts).
## /control {"action": "trailer", "do": "start" (id, sprache, untertitel, ab) | "stop" | "info"}

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Ton = preload("res://scripts/trailer_ton.gd")
const Stimme = preload("res://scripts/abenteuer_stimme.gd")
const Buehne = preload("res://scripts/trailer_buehne.gd")
const Karte = preload("res://scripts/bergtal_abenteuer_karte.gd")
const Welt = preload("res://scripts/maggie_welt.gd")
const Spieltest = preload("res://scripts/spieltest.gd")

const IDS := ["grossvater", "maggie"]
const MUSIK := ["pad_ruhig", "pad_dunkel", "pad_hell", "pulse", "ostinato"]
const KLAENGE := ["pad_ruhig", "pad_dunkel", "pad_hell", "pulse", "ostinato", "pauke", "boom", "riser", "chime", "whoosh", "wind",
		"wasser", "regen", "donner", "schritte", "rennen", "knurren", "bellen", "heulen", "grunzen", "kraehen", "zischen", "knacken",
		"rascheln", "kuhglocke", "papier", "pfiff"]

var main
var laeuft := false
var id := ""
var t := 0.0
var dauer := 0.0
var shots: Array = []
var cur := -1
var stage = null
var opts := {}
var ergebnis := ""
var _saved := {}
var _layers := {}
var _layer_t := 0.0
var _loops := {}                       # name -> {p, g, ziel, rate}
var _ones: Array = []                  # [player, stop at t]
var _geplant: Array = []               # [t, name, vol]
var _ton_i := 0
var _say_i := 0
var _blitz_i := 0
var _say_bis := -1.0
var _sub_bis := -1.0
var _cues: Array = []
var _vorlauf := 0.0
var _ende_halten := false
var _lang_vorher := ""
var _untertitel := true
var _stimme := false
var _movie := false
var _flash := 0.0
var _welt := false
var sprech_id := 0                     # the browser (MoveEye /sim/trailer) reads the narrator and the cards aloud: info «sprechen»
var sprech_text := ""                     # the world was changed (scene, clock, weather …) and must come back

# ui
var _layer: CanvasLayer = null
var _root: Control = null
var _bars: Array = []
var _black: ColorRect = null
var _tint: ColorRect = null
var _white: ColorRect = null
var _card: Label = null
var _card_sub: Label = null
var _sub: Label = null
var _papier: Control = null
var _titel: Control = null
var _ende: Control = null
var _ende_btns: Array = []
var _hinweis: Label = null
var _prep: Label = null


static func inst(m, make := true):
	if m.has_meta("trailer"):
		var n = m.get_meta("trailer")
		if n != null and is_instance_valid(n):
			return n
	if not make:
		return null
	var tr = load("res://scripts/trailer.gd").new()
	tr.name = "trailer"
	tr.main = m
	m.add_child(tr)
	m.set_meta("trailer", tr)
	return tr


static func busy(m) -> bool:
	var tr = inst(m, false)
	return tr != null and bool(tr.laeuft)


static func control(m, d: Dictionary) -> Dictionary:
	var tr = inst(m)
	match str(d.get("do", "info")):
		"start":
			if tr.laeuft:
				return {"ok": false, "error": "läuft schon", "laeuft": true, "id": tr.id}
			var tid := str(d.get("id", "grossvater"))
			if not tid in IDS:
				return {"ok": false, "error": "id: grossvater | maggie"}
			var b: String = m.busy_with()
			if b != "":
				return {"ok": false, "error": "busy: " + b}
			tr.starten.call_deferred(tid, {"sprache": str(d.get("sprache", "")), "untertitel": str(d.get("untertitel", "auto")),
					"ab": float(d.get("ab", 0.0)), "von": "steuerung"})
			return {"ok": true, "loading": true, "id": tid}
		"stop":
			tr.beenden("abgebrochen")
		"info":
			pass
		_:
			return {"ok": false, "error": "do: start (id) | stop | info"}
	return tr.info()


static func from_args(m, args: Array) -> void:
	"""Startoptionen (siehe oben): ein Trailer gleich nach dem Start - für werkzeuge/trailer_aufnehmen.sh"""
	var i := args.find("--trailer")
	if i < 0 or i + 1 >= args.size():
		return
	var o := {"von": "start", "quit": "--trailer-quit" in args}
	for k in [["--trailer-sprache", "sprache"], ["--trailer-untertitel", "untertitel"], ["--trailer-cues", "cues"], ["--trailer-ab", "ab"],
			["--trailer-bis", "ende_s"], ["--trailer-bilder", "bilder"], ["--trailer-zeiten", "zeiten"], ["--trailer-stimme", "stimme"]]:
		var j := args.find(k[0])
		if j >= 0 and j + 1 < args.size():
			o[k[1]] = args[j + 1]
	var tid := str(args[i + 1])
	m.get_tree().create_timer(1.0).timeout.connect(func() -> void:
		var r: Dictionary = await inst(m).starten(tid, o)
		if not bool(r.get("ok", false)):
			print("[Trailer] nicht gestartet: ", r.get("error", ""))
			if bool(o["quit"]):
				m.get_tree().quit(2))


static func add_controls(m) -> void:
	"""group «Entwickler» (like the Vorführung): «devwin» = not in the panel (the developer window has its own buttons on
	top); MoveEye's Simulator page shows them in its card «Entwickler» (only the owner with the Entwickler-Bereich)"""
	m.add_control("button", "trailer_grossvater", "Trailer Grossvater", null,
			func(): control(m, {"do": "start", "id": "grossvater"}), "Entwickler", {"expert": true, "devwin": true})
	m.add_control("button", "trailer_maggie", "Trailer Maggie", null,
			func(): control(m, {"do": "start", "id": "maggie"}), "Entwickler", {"expert": true, "devwin": true})


func _ready() -> void:
	process_priority = 300                      # after main (camera of the window) and the figures: the film wins
	process_mode = Node.PROCESS_MODE_ALWAYS


func titel(tid: String) -> String:
	return T.t("Die Karte des Grossvaters") if tid == "grossvater" else T.t("Maggie und der Bergkristall")


func info() -> Dictionary:
	return {"ok": true, "laeuft": laeuft, "id": id, "t": snappedf(t, 0.1), "dauer": dauer, "einstellung": cur,
			"einstellungen": shots.size(), "ergebnis": ergebnis, "ende": _ende_halten,
			"sprechen": {"id": sprech_id, "text": sprech_text, "lang": T.lang()}, "stimme": _stimme, "untertitel": _untertitel, "sprache": T.lang()}


# =======================================================================================================================
# start / end
# =======================================================================================================================
func starten(tid: String, o := {}) -> Dictionary:
	if laeuft:
		return {"ok": false, "error": "läuft schon"}
	if not tid in IDS:
		return {"ok": false, "error": "id: grossvater | maggie"}
	var b: String = main.busy_with()
	if b != "":
		if main.mehr != null:
			main.mehr.toast(T.t("Gerade läuft: %s – zuerst beenden.", [b]))
		return {"ok": false, "error": "busy: " + b}
	if main.scenes == null:
		return {"ok": false, "error": "no scenes"}
	opts = o
	id = tid
	ergebnis = ""
	_movie = "--write-movie" in OS.get_cmdline_args() or "--write-movie" in OS.get_cmdline_user_args()
	_lang_vorher = T.choice()
	var sp := str(o.get("sprache", ""))
	if sp != "" and sp in T.codes():
		T.set_lang(sp)
	laeuft = true                               # (busy_with: «Trailer» from now on)
	_ende_halten = false
	_saved = {"hour": main.hour(), "speed": main.speed, "weather": main.weather, "auto": main.auto_visitors, "bt_events": main.bt_events,
			"bt_season": main.bt_season, "bt_spot": main.bt_spot, "bt_free": (main.bt_free as Array).duplicate(), "bt_bed": main.bt_bed,
			"scene": main.scene, "panel": main.ui_root.visible if main.ui_root != null else true, "sound": main.sound_on,
			"thunder": main.thunder, "view_mode": main.view_mode, "season": main.season,
			"cull": main.view_cam.cull_mask if main.view_cam != null else 0xFFFFF}
	_ui()
	_layers_aus()
	_prep.visible = true
	if main.mehr != null:
		main.mehr.close_menu()
		if main.spielbereich != null:
			main.spielbereich.close()
		if main.mehr.get("dev") != null and main.mehr.dev.has_method("close"):
			main.mehr.dev.close()                   # (started from the developer window: it comes back afterwards)
	await get_tree().process_frame
	await get_tree().process_frame
	if not laeuft:                              # Esc while the black «wird vorbereitet»: nothing was changed yet
		return {"ok": false, "error": "abgebrochen"}
	Ton.vorbereiten(KLAENGE)
	# the world: the Bergtal (Maggie: autumn, the place of the walk; Grossvater: summer, at the Alp Tschuggen)
	_welt = true
	main.auto_visitors = false
	main.bt_events = false
	main.sound_on = false                       # the sounds of the world rest (the film has its own)
	main.thunder = false
	if main.explore != null and main.explore.on:
		main.explore.set_on(false)
	main.show_panel(false)
	main.season = "7" if tid == "grossvater" else "10"           # the sun path of the season (not of today's date)
	main._sun_cache = [-1.0, Vector2.ZERO]
	if main.view_cam != null:
		main.view_cam.cull_mask = main.view_cam.cull_mask & ~int(Welt.HELPER_LAYER)   # no labels / helpers of the window
	if tid == "maggie":
		main.bt_season = "herbst"
		main.bt_spot = "frei"
		main.bt_free = [Welt.INTRO_SPOT.x, Welt.INTRO_SPOT.y, 0.0]
	else:
		main.bt_season = "sommer"
		main.bt_spot = "huette"
	main.bt_bed = "tent"
	main.set_scene("bergtal")
	await get_tree().process_frame
	if not laeuft:
		return {"ok": false, "error": "abgebrochen"}
	stage = Buehne.new()
	stage.regie = self
	if not stage.binden(main):
		stage.free()
		stage = null
		_welt_zurueck()
		_welt = false
		_layers_zurueck()
		if _layer != null:
			_layer.visible = false
		laeuft = false
		return {"ok": false, "error": "no bergtal scene"}
	main.scenes.root.add_child(stage)
	if tid == "maggie" and main.maggie != null:
		var f: Dictionary = main.maggie.figur()
		var lk: Dictionary = f.get("look", {}) if f.get("look", {}) is Dictionary else {}
		var col := str(lk.get("col", "orange")) if not lk.is_empty() else "orange"
		var look := lk.duplicate() if not lk.is_empty() else {"col": col, "size": "", "build": "", "hat": "", "pack": true}
		look["pack"] = true
		stage.setze_held(look, preload("res://scripts/figur.gd").LOOK_COLS.get(col, Color(0.9, 0.5, 0.15)))
	main._set_speed(0.0)
	main.view_mode = 0
	shots = stage.einstellungen(tid)
	dauer = 0.0
	for sh in shots:
		dauer = maxf(dauer, float(sh["t0"]) + float(sh["d"]))
	_stimme = _stimme_da() and str(o.get("stimme", "an")) != "aus" and not _movie
	var ut := str(o.get("untertitel", "auto"))
	_untertitel = ut == "an" or (ut != "aus" and not _stimme)
	_cues = []
	_vorlauf = _movie_zeit()
	_prep.visible = false
	t = clampf(float(o.get("ab", 0.0)), 0.0, maxf(0.0, dauer - 0.5))
	cur = -1
	if t > 0.0:
		_vorspulen(t)
	Spieltest.ereignis("trailer", "start", {"einheit": titel(tid), "id": tid, "plan_min": 3})
	print("[Trailer] Start: %s (%s, %d Einstellungen, %.0f s, Stimme %s, Untertitel %s, Vorlauf %.2f s)" % [tid, T.lang(), shots.size(), dauer,
			str(_stimme), str(_untertitel), _vorlauf])
	if o.has("bilder"):
		_standbilder.call_deferred(str(o["bilder"]), str(o.get("zeiten", "")))
	return {"ok": true, "id": tid, "dauer": dauer, "einstellungen": shots.size()}


func _movie_zeit() -> float:
	"""Movie Maker: so viele Sekunden Film sind schon geschrieben (feste fps)"""
	var fps := float(ProjectSettings.get_setting("editor/movie_writer/fps", 60))
	var args := OS.get_cmdline_args()
	var k := args.find("--fixed-fps")
	if k >= 0 and k + 1 < args.size():
		fps = float(args[k + 1])
	return float(Engine.get_frames_drawn()) / maxf(1.0, fps)


func _stimme_da() -> bool:
	"""a voice of the system for exactly this language (Romansh: usually none - then subtitles)"""
	if not Stimme.an() or not Stimme.moeglich():
		return false
	return not DisplayServer.tts_get_voices_for_language(T.lang()).is_empty()


func beenden(grund := "abgebrochen") -> void:
	if not laeuft:
		return
	laeuft = false
	_ende_halten = false
	ergebnis = grund
	if _stimme:
		Stimme.stopp()
	_audio_aus()
	_cues_schreiben()
	Spieltest.ereignis("trailer", "ende", {"ergebnis": "fertig" if grund == "fertig" else "abgebrochen"})
	print("[Trailer] Ende: %s bei %.1f s" % [grund, t])
	if stage != null and is_instance_valid(stage):
		stage.aufraeumen()
		stage.queue_free()
	stage = null
	if _lang_vorher != T.choice():
		T.set_lang(_lang_vorher if _lang_vorher != "" else "auto")
	if bool(opts.get("quit", false)):
		get_tree().quit(0 if grund == "fertig" else 1)
		return
	if _welt:
		_welt_zurueck()
	_welt = false
	_layers_zurueck()
	if _layer != null:
		_layer.visible = false
	if str(opts.get("von", "")) == "karte" and grund != "spielen" and main.spielbereich != null:
		main.spielbereich.open()
	elif str(opts.get("von", "")) == "dev" and grund != "spielen" and main.mehr != null and main.mehr.get("dev") != null:
		main.mehr.dev.open()


func _welt_zurueck() -> void:
	main.auto_visitors = bool(_saved.get("auto", true))
	main.bt_events = bool(_saved.get("bt_events", true))
	main.weather = str(_saved.get("weather", "clear"))
	main.bt_season = str(_saved.get("bt_season", "auto"))
	main.bt_spot = str(_saved.get("bt_spot", "huette"))
	main.bt_free = _saved.get("bt_free", [])
	main.bt_bed = str(_saved.get("bt_bed", "tent"))
	main.sound_on = bool(_saved.get("sound", true))
	main.thunder = bool(_saved.get("thunder", false))
	main.view_mode = int(_saved.get("view_mode", 0))
	if main.rain != null:
		main.rain.visible = true
	if main.splashes != null:
		main.splashes.visible = true
	main.season = str(_saved.get("season", "today"))
	main._sun_cache = [-1.0, Vector2.ZERO]
	if main.view_cam != null:
		main.view_cam.cull_mask = int(_saved.get("cull", main.view_cam.cull_mask))
	main.set_hour(float(_saved.get("hour", 12.0)))
	main._set_speed(float(_saved.get("speed", 1.0)))
	var sc := str(_saved.get("scene", main.scene))
	if sc != "":
		main.set_scene(sc)
	if bool(_saved.get("panel", true)):
		main.show_panel(true)


func _spielen() -> void:
	"""«Jetzt spielen»: wie «Weiterspielen» auf der Karte (noch nicht begonnen: der gemeinsame Start)"""
	var tid := id
	beenden("spielen")
	var g = main.spielbereich.regal if main.spielbereich != null else null
	if g != null:
		g.weiter(tid)


# =======================================================================================================================
# every frame
# =======================================================================================================================
func _process(dt: float) -> void:
	if not laeuft or stage == null:
		return
	_layer_t -= dt
	if _layer_t <= 0.0:
		_layer_t = 1.0
		_layers_aus()
	if main.ui_layer != null and main.ui_layer.visible:
		main.ui_layer.visible = false
	if _ende_halten:
		_ui_tick(dt)
		return
	if opts.has("bilder"):
		_bild_tick(0.0)
		return
	dt = minf(dt, 0.5)                          # (a long hitch - e.g. building the valley - does not jump over shots)
	t += dt
	var bis := float(opts.get("ende_s", -1.0))
	if t >= dauer or (bis > 0.0 and t >= bis):
		if bool(opts.get("quit", false)) or bis > 0.0:
			beenden("fertig")
		else:
			_ende_halten = true                 # the end card stays with its buttons until a click / Esc
			_audio_ziel_alle(0.0, 2.0)
		return
	_bild_tick(dt)
	_audio_tick(dt)
	_ui_tick(dt)


func _index(tt: float) -> int:
	for i in range(shots.size()):
		if tt < float(shots[i]["t0"]) + float(shots[i]["d"]):
			return i
	return shots.size() - 1


func _bild_tick(dt: float) -> void:
	var i := _index(t)
	if i != cur:
		_schnitt(i)
	var sh: Dictionary = shots[cur]
	var rel := t - float(sh["t0"])
	# cues of this shot
	var tl: Array = sh.get("ton", [])
	while _ton_i < tl.size() and rel >= float(tl[_ton_i][0]):
		_ton(tl[_ton_i])
		_ton_i += 1
	var sl: Array = sh.get("say", [])
	while _say_i < sl.size() and rel >= float(sl[_say_i][0]):
		_sag(str(sl[_say_i][1]))
		_say_i += 1
	var bl: Array = sh.get("blitz", [])
	while _blitz_i < bl.size() and rel >= float(bl[_blitz_i]):
		_flash = 1.0
		if str(sh.get("art", "")) == "welt" and bool(sh.get("donner", false)) and main.has_method("lightning_strike"):
			main.lightning_strike()
		_blitz_i += 1
	if str(sh.get("art", "")) != "welt":
		return
	stage.tick(sh, rel, dt)
	var u := clampf(rel / maxf(0.01, float(sh["d"])), 0.0, 1.0)
	u = u * u * (3.0 - 2.0 * u) * 0.6 + u * 0.4               # soft, but the camera never stands still
	var cam: Dictionary = sh.get("cam", {})
	if bool(cam.get("kopf", false)) and main.head != null:
		cam = cam.duplicate()
		cam["welt"] = (main.head as Node3D).global_position - Vector3(0, float(cam.get("lh", 1.4)), 0)
	var r: Array = stage.kamera(cam, u, rel)
	if not r.is_empty():
		var vc: Camera3D = main.view_cam
		var at: Vector3 = r[0]
		var lk: Vector3 = r[1]
		if at.distance_to(lk) < 0.05:
			lk = at + Vector3(0, 0, -1)
		vc.global_transform = Transform3D(Basis.IDENTITY, at).looking_at(lk, Vector3.UP)
		vc.fov = float(r[2])
		vc.far = 7000.0
		stage.schneefall(bool(sh.get("schnee", false)), at)
	# fog and light of the shot (after main set its own values this frame)
	var nb := float(sh.get("nebel", 0.0))
	if nb > 0.0 and main.env != null:
		main.env.fog_density = maxf(main.env.fog_density, nb)
	var nm := float(sh.get("nebel_max", 0.0))
	if nm > 0.0 and main.env != null:
		main.env.fog_density = minf(main.env.fog_density, nm)
	if bool(sh.get("dunkel", false)) and main.env != null:
		main.env.ambient_light_energy *= 0.5
	var nl := float(sh.get("nachtlicht", 0.0))
	if nl > 0.0 and main.env != null and main.env.ambient_light_energy < nl:
		main.env.ambient_light_energy = nl                         # a little «day for night»: the night stays readable
		main.env.ambient_light_color = Color(0.45, 0.55, 0.8)


func _schnitt(i: int) -> void:
	cur = i
	_ton_i = 0
	_say_i = 0
	_blitz_i = 0
	var sh: Dictionary = shots[i]
	if sh.has("zeit"):
		main.set_hour(float(sh["zeit"]))
	if sh.has("wetter") or str(sh.get("art", "")) == "welt":
		var w := str(sh.get("wetter", main.weather))
		if main.rain != null:
			main.rain.visible = w == "rain"                        # no drops of the last shot in the next one
		if main.splashes != null:
			main.splashes.visible = w == "rain"
		main.weather = w
		main.thunder = bool(sh.get("donner", false))
	if str(sh.get("art", "")) == "welt":
		main._update_sky()
	if str(sh.get("art", "")) == "welt":
		stage.aufbau(sh)
	Spieltest.ereignis("trailer", "abschnitt", {"name": "%d %s" % [i + 1, str(sh.get("auf", sh.get("art", "")))]})
	_ui_schnitt(sh)


func _vorspulen(bis: float) -> void:
	"""--trailer-ab: the loops as they would be at this time (one-shots and words are skipped)"""
	for sh in shots:
		if float(sh["t0"]) >= bis:
			break
		for c in sh.get("ton", []):
			if float(sh["t0"]) + float(c[0]) > bis:
				break
			if str(c[1]) in ["loop", "stop", "stille"]:
				_ton(c, true)


# =======================================================================================================================
# sound: loops with a volume that glides, one-shots, the narrator
# =======================================================================================================================
func _player(snd: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.stream = Ton.get_snd(snd)
	add_child(p)
	return p


func _ton(c: Array, sofort := false) -> void:
	match str(c[1]):
		"loop":
			var nm := str(c[2])
			if not _loops.has(nm):
				var p := _player(nm)
				p.volume_db = -80.0
				p.play()
				_loops[nm] = {"p": p, "g": 0.0, "ziel": 0.0, "rate": 1.0}
			var L: Dictionary = _loops[nm]
			L["ziel"] = db_to_linear(float(c[3]))
			var f := float(c[4]) if c.size() > 4 else 1.0
			L["rate"] = 1.0 / maxf(0.05, f)
			if sofort:
				L["g"] = L["ziel"]
		"stop":
			var nm2 := str(c[2])
			if _loops.has(nm2):
				_loops[nm2]["ziel"] = 0.0
				_loops[nm2]["rate"] = 1.0 / maxf(0.05, float(c[3]) if c.size() > 3 else 1.0)
				if sofort:
					_loops[nm2]["g"] = 0.0
		"stille":
			_audio_ziel_alle(0.0, float(c[2]) if c.size() > 2 else 0.1)
			for o in _ones:
				if is_instance_valid(o[0]):
					(o[0] as AudioStreamPlayer).stop()
					(o[0] as AudioStreamPlayer).queue_free()
			_ones = []
			_geplant = []
		"one":
			if sofort:
				return
			var dl := float(c[4]) if c.size() > 4 else 0.0
			if dl > 0.0:
				_geplant.append([t + dl, str(c[2]), float(c[3])])
			else:
				_eins(str(c[2]), float(c[3]))


func _eins(nm: String, vol: float) -> void:
	var p := _player(nm)
	p.volume_db = vol
	p.play()
	_ones.append([p, t + p.stream.get_length() + 0.2])


func _audio_ziel_alle(g: float, f: float) -> void:
	for nm in _loops:
		_loops[nm]["ziel"] = g
		_loops[nm]["rate"] = 1.0 / maxf(0.05, f)


func _audio_tick(dt: float) -> void:
	var duck := 0.6 if t < _say_bis else 1.0
	for nm in _loops:
		var L: Dictionary = _loops[nm]
		var ziel := float(L["ziel"])
		L["g"] = move_toward(float(L["g"]), ziel, dt * float(L["rate"]) * maxf(0.05, maxf(ziel, float(L["g"]))))
		var g := float(L["g"]) * (duck if nm in MUSIK else 1.0)
		(L["p"] as AudioStreamPlayer).volume_db = linear_to_db(maxf(g, 0.00001))
	for i in range(_geplant.size() - 1, -1, -1):
		if t >= float(_geplant[i][0]):
			_eins(str(_geplant[i][1]), float(_geplant[i][2]))
			_geplant.remove_at(i)
	for i in range(_ones.size() - 1, -1, -1):
		if t > float(_ones[i][1]) or not is_instance_valid(_ones[i][0]):
			if is_instance_valid(_ones[i][0]):
				(_ones[i][0] as AudioStreamPlayer).queue_free()
			_ones.remove_at(i)


func _audio_aus() -> void:
	for nm in _loops:
		if is_instance_valid(_loops[nm]["p"]):
			(_loops[nm]["p"] as AudioStreamPlayer).queue_free()
	_loops = {}
	for o in _ones:
		if is_instance_valid(o[0]):
			(o[0] as AudioStreamPlayer).queue_free()
	_ones = []
	_geplant = []


func _sag(text: String) -> void:
	"""a sentence of the narrator: the voice of the system (if there is one for this language), else / also the subtitle"""
	var secs := 0.6 + text.length() * 0.068
	_say_bis = t + secs
	_vorlesen(text)
	_cues.append({"t": snappedf(_vorlauf + t, 0.01), "rel": snappedf(t, 0.01), "text": text.replace("«", "").replace("»", ""), "dauer": snappedf(secs, 0.01)})
	if _stimme:
		var tt := text.replace("«", "").replace("»", "").strip_edges()
		var ids := DisplayServer.tts_get_voices_for_language(T.lang())
		if not ids.is_empty():
			DisplayServer.tts_speak(tt, ids[0], 85, 0.86, 0.9, 0, true)
	if _untertitel and _sub != null and str(shots[cur].get("art", "")) != "ende":
		_sub.text = text
		_sub_bis = t + secs + 0.4


func _vorlesen(text: String) -> void:
	var tx := text.replace("«", "").replace("»", "").replace("\n", " ").strip_edges()
	if tx != "":
		sprech_id += 1
		sprech_text = tx


func _cues_schreiben() -> void:
	var p := str(opts.get("cues", ""))
	if p == "":
		return
	var f := FileAccess.open(p, FileAccess.WRITE)
	if f == null:
		print("[Trailer] cues-Datei nicht schreibbar: ", p)
		return
	f.store_string(JSON.stringify({"id": id, "sprache": T.lang(), "vorlauf": snappedf(_vorlauf, 0.001), "dauer": dauer,
			"untertitel": _untertitel, "ab": float(opts.get("ab", 0.0)), "saetze": _cues}, "  "))


# =======================================================================================================================
# keys and clicks: Esc or a click = back to the card (the buttons of the end card work)
# =======================================================================================================================
func _input(ev: InputEvent) -> void:
	if not laeuft or _movie:
		return
	var weg := false
	if ev is InputEventKey and (ev as InputEventKey).pressed and not (ev as InputEventKey).echo:
		weg = (ev as InputEventKey).keycode == KEY_ESCAPE
	elif ev is InputEventMouseButton and (ev as InputEventMouseButton).pressed:
		var mb := ev as InputEventMouseButton
		if mb.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			get_viewport().set_input_as_handled()
			return
		for b in _ende_btns:
			if is_instance_valid(b) and (b as Control).is_visible_in_tree() and (b as Control).get_global_rect().has_point(mb.position):
				return                                         # the end card: «Jetzt spielen» / «Zurück» get the click
		weg = true
	elif ev is InputEventJoypadButton and (ev as InputEventJoypadButton).pressed:
		weg = (ev as InputEventJoypadButton).button_index in [JOY_BUTTON_B, JOY_BUTTON_START, JOY_BUTTON_BACK]
	if ev is InputEventKey or ev is InputEventMouseButton or ev is InputEventJoypadButton:
		get_viewport().set_input_as_handled()
	if weg:
		beenden("abgebrochen" if not _ende_halten else "fertig")


# =======================================================================================================================
# still pictures (tests, Daniel: «Bilder ausgewählter Momente»)
# =======================================================================================================================
func _standbilder(dir: String, zeiten: String) -> void:
	var ts: Array = []
	for z in zeiten.split(",", false):
		ts.append(float(z))
	if ts.is_empty():
		for sh in shots:                                # the middle of every shot
			ts.append(float(sh["t0"]) + float(sh["d"]) * 0.55)
	DirAccess.make_dir_recursive_absolute(dir)
	for tt in ts:
		if not laeuft:
			return
		t = float(tt)
		cur = -1
		_bild_tick(0.016)
		_ui_tick(0.0)
		for k in range(6):
			await get_tree().process_frame
			t = float(tt) + k * 0.016
			_bild_tick(0.016)
			_ui_tick(0.016)
		_flash = 0.0                                        # (the still picture without the white of a cut)
		_white.color.a = 0.0
		await get_tree().process_frame
		var img := get_viewport().get_texture().get_image()
		var fn := dir.path_join("%s_%s_%05.1f.png" % [id, T.lang(), float(tt)])
		img.save_png(fn)
		print("[Trailer] Bild: ", fn)
	beenden("fertig")


# =======================================================================================================================
# the other layers (panel, windows, toolbar, Maggie's bar …) are hidden while the film runs
# =======================================================================================================================
func _layers_aus() -> void:
	for n in get_tree().root.find_children("*", "CanvasLayer", true, false):
		if n == _layer or not (n as CanvasLayer).visible:
			continue
		if not _layers.has(n):
			_layers[n] = true
		(n as CanvasLayer).visible = false


func _layers_zurueck() -> void:
	for n in _layers:
		if is_instance_valid(n):
			(n as CanvasLayer).visible = true
	_layers = {}


# =======================================================================================================================
# the picture on top: black bars (cinema), cards, subtitles, the old letter, title and end card
# =======================================================================================================================
func _vh() -> float:
	return get_viewport().get_visible_rect().size.y


func _fs(px: float) -> int:
	"""font size relative to 720 px picture height"""
	return int(round(px * _vh() / 720.0))


func _lbl(sz: float, col := Color(0.92, 0.94, 0.97)) -> Label:
	var l := Label.new()
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_override("font", UI.heading_font())
	l.add_theme_font_size_override("font_size", _fs(sz))
	l.add_theme_color_override("font_color", col)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _full(c: Control) -> Control:
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


func _ui() -> void:
	if _layer != null:
		_layer.visible = true
		for c in _root.get_children():
			c.queue_free()
	else:
		_layer = CanvasLayer.new()
		_layer.layer = 120
		add_child(_layer)
		_root = _full(Control.new())
		_root.theme = UI.theme()
		_layer.add_child(_root)
	_tint = _full(ColorRect.new()) as ColorRect
	_tint.color = Color(0, 0, 0, 0)
	_root.add_child(_tint)
	_white = _full(ColorRect.new()) as ColorRect
	_white.color = Color(1, 1, 1, 0)
	_root.add_child(_white)
	_bars = []
	for top in [true, false]:
		var b := ColorRect.new()
		b.color = Color.BLACK
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.anchor_left = 0.0
		b.anchor_right = 1.0
		b.anchor_top = 0.0 if top else 1.0
		b.anchor_bottom = 0.0 if top else 1.0
		_root.add_child(b)
		_bars.append(b)
	_black = _full(ColorRect.new()) as ColorRect
	_black.color = Color.BLACK
	_root.add_child(_black)
	_card = _full(_lbl(30.0)) as Label
	_card.modulate.a = 0.0
	_root.add_child(_card)
	_card_sub = _lbl(16.0, Color(0.7, 0.74, 0.8))
	_card_sub.anchor_left = 0.0
	_card_sub.anchor_right = 1.0
	_card_sub.anchor_top = 0.62
	_card_sub.anchor_bottom = 0.7
	_root.add_child(_card_sub)
	_papier = _full(Brief.new())
	_papier.visible = false
	_root.add_child(_papier)
	_titel = _full(Titel.new())
	_titel.visible = false
	_root.add_child(_titel)
	_ende = _full(Control.new())
	_ende.visible = false
	_root.add_child(_ende)
	_sub = _lbl(19.0, Color(0.96, 0.96, 0.92))
	_sub.anchor_left = 0.08
	_sub.anchor_right = 0.92
	_sub.anchor_top = 1.0
	_sub.anchor_bottom = 1.0
	_sub.add_theme_constant_override("outline_size", _fs(4.0))
	_sub.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_sub.modulate.a = 0.0
	_root.add_child(_sub)
	_hinweis = UI.small(T.t("Esc oder Klick = zurück"), Color(0.6, 0.64, 0.7))
	_hinweis.anchor_left = 1.0
	_hinweis.anchor_right = 1.0
	_hinweis.offset_left = -260
	_hinweis.offset_right = -14
	_hinweis.offset_top = 8
	_hinweis.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_hinweis.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hinweis.visible = not _movie
	_root.add_child(_hinweis)
	_prep = _full(_lbl(15.0, Color(0.6, 0.64, 0.7))) as Label
	_prep.text = T.t("Trailer wird vorbereitet …")
	_root.add_child(_prep)
	_layout()


func _layout() -> void:
	var vs := get_viewport().get_visible_rect().size
	var bar := maxf(0.0, (vs.y - vs.x / 2.2) / 2.0)             # cinema picture 2.2 : 1
	(_bars[0] as ColorRect).offset_top = 0
	(_bars[0] as ColorRect).offset_bottom = bar
	(_bars[1] as ColorRect).offset_top = -bar
	(_bars[1] as ColorRect).offset_bottom = 0
	_sub.offset_top = -bar + 4.0
	_sub.offset_bottom = -4.0
	if bar < _fs(40.0):
		_sub.offset_top = -_fs(70.0)
		_sub.offset_bottom = -_fs(10.0)


func _ui_schnitt(sh: Dictionary) -> void:
	var art := str(sh.get("art", "welt"))
	_card.modulate.a = 0.0
	_card_sub.text = ""
	_papier.visible = art == "papier"
	_titel.visible = art == "titel"
	_ende.visible = art == "ende"
	_black.color.a = 0.0 if art == "welt" else 1.0
	var tc: Color = sh.get("tint", Color(0, 0, 0, 0))
	_tint.color = tc
	if art in ["tafel", "titel"]:
		_vorlesen(str(sh.get("text", "")))
	if art == "tafel":
		_card.text = str(sh.get("text", ""))
		_card.add_theme_font_size_override("font_size", _fs(20.0 if bool(sh.get("klein", false)) else 32.0))
	if art == "papier":
		(_papier as Brief).setup(T.t("«Die Karte gehört jetzt dir – lies sie mit der Sonne.»"), T.t("Dein Grossvater"))
	if art == "titel":
		(_titel as Titel).setup(str(sh.get("text", "")), str(sh.get("sub", "")), bool(sh.get("kristall", false)))
	if art == "ende":
		_ende_bauen(sh)


func _ende_bauen(sh: Dictionary) -> void:
	for c in _ende.get_children():
		c.queue_free()
	_ende_btns = []
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_CENTER)
	v.grow_horizontal = Control.GROW_DIRECTION_BOTH
	v.grow_vertical = Control.GROW_DIRECTION_BOTH
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", _fs(18.0))
	_ende.add_child(v)
	var tl := _lbl(30.0)
	tl.text = str(sh.get("text", ""))
	tl.custom_minimum_size = Vector2(get_viewport().get_visible_rect().size.x * 0.8, 0)
	v.add_child(tl)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", _fs(12.0))
	v.add_child(row)
	var b := Button.new()
	b.text = T.t("Jetzt spielen")
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(_fs(220.0), _fs(48.0))
	b.add_theme_font_size_override("font_size", _fs(20.0))
	UI.primary(b)
	b.pressed.connect(_spielen)
	row.add_child(b)
	_ende_btns.append(b)
	if not _movie and not bool(opts.get("quit", false)):
		var z := Button.new()
		z.text = T.t("Zurück")
		z.focus_mode = Control.FOCUS_NONE
		z.custom_minimum_size = Vector2(_fs(140.0), _fs(48.0))
		z.add_theme_font_size_override("font_size", _fs(17.0))
		z.pressed.connect(func(): beenden("fertig"))
		row.add_child(z)
		_ende_btns.append(z)
	var hl := _lbl(14.0, Color(0.6, 0.64, 0.7))
	hl.text = T.t("MoveEye Sim · Spielen → Geschichten")
	v.add_child(hl)
	_ende.modulate.a = 0.0


func _ui_tick(dt: float) -> void:
	if cur < 0 or cur >= shots.size():
		return
	var sh: Dictionary = shots[cur]
	var art := str(sh.get("art", "welt"))
	var rel := t - float(sh["t0"])
	var d := float(sh["d"])
	if art == "welt":
		var fi := float(sh.get("fade_in", 0.0))
		_black.color.a = 1.0 - clampf(rel / fi, 0.0, 1.0) if fi > 0.0 else 0.0
	elif art == "tafel":
		_card.modulate.a = clampf(rel / 0.6, 0.0, 1.0) * clampf((d - rel) / 0.5, 0.0, 1.0)
		_card.scale = Vector2.ONE * (1.0 + 0.02 * rel / d)
		_card.pivot_offset = _card.size / 2.0
	elif art == "papier":
		(_papier as Brief).k = rel / d
		_papier.modulate.a = clampf(rel / 0.8, 0.0, 1.0) * clampf((d - rel) / 0.6, 0.0, 1.0)
		_papier.queue_redraw()
	elif art == "titel":
		(_titel as Titel).k = rel / d
		_titel.modulate.a = clampf(rel / 0.25, 0.0, 1.0) * clampf((d - rel) / 0.8, 0.0, 1.0)
		_titel.queue_redraw()
	elif art == "ende":
		_ende.modulate.a = clampf(rel / 0.8, 0.0, 1.0)
	_flash = maxf(0.0, _flash - dt * 7.0)
	_white.color.a = _flash * 0.85
	if t > _sub_bis:
		_sub.modulate.a = move_toward(_sub.modulate.a, 0.0, dt * 4.0)
	else:
		_sub.modulate.a = move_toward(_sub.modulate.a, 1.0, dt * 6.0)
	if _hinweis != null:
		var bare: bool = main.padview != null and main.now() - float(main.padview.bare_t) < 3.0   # (MoveEye's browser view)
		_hinweis.modulate.a = clampf(1.0 - (t - 4.0) / 2.0, 0.0, 1.0) if not _ende_halten and not bare else 0.0


# =======================================================================================================================
# drawn cards
# =======================================================================================================================
class Brief extends Control:
	## the grandfather's letter and the first piece of the old map (only piece 1: no goal of the map, no secret)
	var k := 0.0
	var text := ""
	var unterschrift := ""
	var _karte: Control = null

	func setup(tx: String, us: String) -> void:
		text = tx
		unterschrift = us
		if _karte == null:
			_karte = load("res://scripts/bergtal_abenteuer_karte.gd").new()
			_karte.pieces = [0]
			_karte.compass = true
			_karte.mouse_filter = Control.MOUSE_FILTER_IGNORE
			add_child(_karte)

	func _draw() -> void:
		var vs := size
		draw_rect(Rect2(Vector2.ZERO, vs), Color(0.05, 0.04, 0.03))
		var z := 1.0 + 0.07 * k
		var w := vs.y * 0.78 * z
		var c := vs / 2.0 + Vector2(-vs.x * 0.02 * k, 0)
		# the letter (left) and the map piece (right)
		var lr := Rect2(c + Vector2(-w * 1.05, -w * 0.48), Vector2(w * 0.9, w * 0.96))
		draw_rect(lr, Color(0.88, 0.82, 0.68))
		draw_rect(lr, Color(0.55, 0.45, 0.3), false, 2.0)
		var f := get_theme_default_font()
		var fsz := int(vs.y * 0.034)
		var y := lr.position.y + lr.size.y * 0.22
		for line in _wrap(f, text, fsz, lr.size.x * 0.82):
			draw_string(f, Vector2(lr.position.x + lr.size.x * 0.09, y), line, HORIZONTAL_ALIGNMENT_LEFT, -1, fsz, Color(0.25, 0.16, 0.08))
			y += fsz * 1.5
		draw_string(f, Vector2(lr.position.x + lr.size.x * 0.45, lr.end.y - lr.size.y * 0.16), unterschrift, HORIZONTAL_ALIGNMENT_LEFT, -1,
				int(fsz * 0.9), Color(0.3, 0.2, 0.1))
		var seal := lr.position + Vector2(lr.size.x * 0.82, lr.size.y * 0.86)          # the wax seal
		draw_circle(seal, w * 0.06, Color(0.55, 0.06, 0.05))
		draw_circle(seal, w * 0.042, Color(0.68, 0.1, 0.08))
		if _karte != null:
			_karte.position = c + Vector2(w * 0.12, -w * 0.48)
			_karte.size = Vector2(w * 0.96, w * 0.96)
			_karte.modulate.a = clampf((k - 0.25) / 0.2, 0.0, 1.0)

	func _wrap(f: Font, s: String, fsz: int, maxw: float) -> Array:
		var out := []
		var line := ""
		for wd in s.split(" "):
			var tst := (line + " " + wd).strip_edges()
			if f.get_string_size(tst, HORIZONTAL_ALIGNMENT_LEFT, -1, fsz).x > maxw and line != "":
				out.append(line)
				line = wd
			else:
				line = tst
		if line != "":
			out.append(line)
		return out


class Titel extends Control:
	## the title card: big letters, a thin line, the small line below; Maggie: the glow of the crystal behind
	var k := 0.0
	var text := ""
	var sub := ""
	var kristall := false

	func setup(tx: String, sb: String, kr: bool) -> void:
		text = tx
		sub = sb
		kristall = kr

	func _draw() -> void:
		var vs := size
		draw_rect(Rect2(Vector2.ZERO, vs), Color.BLACK)
		var c := vs / 2.0
		if kristall:
			for i in range(14):
				var r := vs.y * (0.5 - i * 0.032) * (0.9 + 0.1 * k)
				draw_circle(c, r, Color(0.45, 0.7, 1.0, 0.018 + i * 0.004))
		var f: Font = load("res://scripts/ui_style.gd").heading_font()
		var fsz := int(vs.y * 0.075 * (1.0 + 0.04 * k))
		var tw := f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fsz).x
		if tw > vs.x * 0.9:
			fsz = int(fsz * vs.x * 0.9 / tw)
			tw = f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fsz).x
		draw_string(f, Vector2(c.x - tw / 2.0, c.y), text, HORIZONTAL_ALIGNMENT_LEFT, -1, fsz, Color(0.95, 0.93, 0.88))
		var lw := tw * clampf(k * 3.0, 0.0, 1.0) * 0.6
		draw_line(Vector2(c.x - lw / 2.0, c.y + fsz * 0.45), Vector2(c.x + lw / 2.0, c.y + fsz * 0.45), Color(0.8, 0.7, 0.45, 0.8), 2.0)
		var ssz := int(vs.y * 0.028)
		var sw := f.get_string_size(sub, HORIZONTAL_ALIGNMENT_LEFT, -1, ssz).x
		draw_string(f, Vector2(c.x - sw / 2.0, c.y + fsz * 0.45 + ssz * 2.2), sub, HORIZONTAL_ALIGNMENT_LEFT, -1, ssz,
				Color(0.7, 0.72, 0.76, clampf((k - 0.2) * 3.0, 0.0, 1.0)))
