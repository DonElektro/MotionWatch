extends Node
## Vorführmodus «Maggie und der Bergkristall» (Daniel, 31.10.2026): eine Simulation spielt die ganze Geschichte, man schaut
## nur zu – wie ein Film, am PC im Simulator oder live im Browser (MoveEye: Simulator-Seite → Entwickler → «Vorführung ansehen»).
## Nur für den Besitzer: Start im Fenster «Mehr → Entwickler → Vorführung» (devtool_vorfuehrung.gd) oder von MoveEye
## (Steuerbefehl `vorfuehrung`, net.gd: nur dieser PC / das verbundene MoveEye, wie werk reset).
##
## Länge: «ganz» (alle 4 Jahreszeiten + Finale, so wie ein Spieler; der Autopilot ist schneller als ein Kind, etwa 1–2 h) oder
##   «kurz» (etwa 15–20 Min.): je Jahreszeit die Höhepunkte – eine Station mit einer Fähigkeit von Maggie, das Schutzding und die
##   Begegnung mit dem bösen Tier, das Tor –, dazwischen Schnitte («Etwas später …»); Einstieg und Finale ganz.
## Autopilot: spielt mit denselben Funktionen wie ein Spieler – geht (actor.ctl_move wie W A S D), drückt die Knöpfe der Karten
##   (maggie_story._press_primary, Auswahl der Jahreszeit = _start_region wie der Knopf), Maggies Knöpfe (maggie_hund.befehl),
##   das Schutzding (maggie_gefahr.benutze, wie Taste B), schaut in den Kristall (look_into_crystal, wie K), geht zu Rastplätzen,
##   Toren und in die Bergkapelle. Absichtliche Fehler, damit es spannend bleibt: einmal falsch abgebogen (Herbst, Gabelung),
##   einmal erwischt (Winter: vergisst die Fackel), einmal der falsche Maggie-Knopf (Frühling). Nur in der Kurzfassung werden
##   übersprungene Stationen beim Schnitt gelöst (maggie_hund._fertig) – das steht im Protokoll als «Schnitt».
## Kommt der Autopilot nicht weiter (Fortschritt bleibt aus, Weg versperrt): Umweg, dann «BLOCKIERT» im Protokoll und in der
##   Info, danach ein Sprung ans Ziel, damit der Film weiterläuft – so ist jede Vorführung auch ein automatischer Durchspiel-Test.
## Spielstand: maggie_story.demo = true -> eigene Datei user://maggie/vorfuehrung.json; maggie_gefahr ohne eigene Datei,
##   geschichten.gd macht kein Kartenbild und kein «zuletzt gespielt», geschichten_faden.gd merkt nichts, der Spieltest zählt
##   keine Runde (Engine-Meta «vorfuehrung», spieltest.gd ereignis). Daniels Spielstände (spielstand.gd) bleiben unberührt.
## Kamera wie im Film: Verfolgung (hinter der Figur), Nahaufnahme Maggie, Totale (hoch und weit), Kamerafahrt (Kreis), von vorne;
##   harte Schnitte alle 7–12 s, bei Ereignissen passend (Station = Maggie nah, Gefahr = Totale, Tor = Fahrt). Die eigenen Filme
##   der Geschichte (Zukunftsbilder, Finale) laufen wie sie sind.
## Untertitel: die Texte der Geschichte (Karten, Tipps unten, MoveEye-Sätze links unten) bleiben im Bild, die Knöpfe sind weg.
##   Erzählerstimme (abenteuer_stimme.gd, Sprachausgabe des Systems), wenn an: Karten, Tipps und MoveEye-Sätze.
## Zuschauen: Vollbild ohne Bedienelemente (nur beim Start am PC), kleine Leiste unten (Pause / Weiter / Kapitel / Beenden), die
##   nach 4 s ohne Maus verschwindet; Tasten: Esc = beenden, Leertaste = Pause / Weiter, Bild auf/ab bzw. ← → = Kapitel.
##   Im Browser (MoveEye 639m, Bild mit bare=1): die Leiste ist im Bild nie zu sehen, die Seite hat eigene Knöpfe.
## Kapitel: 0 Einstieg · 1–4 die Jahreszeiten (Reihenfolge Herbst, Winter, Frühling, Sommer) · 5 Finale am Gipfel.
## Protokoll: user://maggie/vorfuehrung_protokoll.txt (und print «[Vorführung] …»), in der Info die letzten Zeilen.
## Lite: _lite() (Quality.lite()) – keine Kamerafahrt mit weichem Übergang (nur harte Schnitte), seltener Kamerawechsel.
## /control {"action": "vorfuehrung", "do": "start" (len: kurz | ganz, tempo 1–4 = nur für Tests schneller, stimme, vollbild, knoepfe = Spiel-Knöpfe zeigen)
##   | "pause" | "weiter" | "kapitel" (n) | "stop" | "info"}

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Quality = preload("res://scripts/quality.gd")
const Welt = preload("res://scripts/maggie_welt.gd")
const Stimme = preload("res://scripts/abenteuer_stimme.gd")

const PROTOKOLL := "user://maggie/vorfuehrung_protokoll.txt"
const EINST := "user://maggie/vorfuehrung_einstellung.json"
const WALK := ["intro_walk", "region", "finale_walk"]
const FAEHIG := ["riechen", "graben", "schluepfen"]
const FEHLER_ABBIEGEN := "herbst"       # einmal falsch abgebogen (erste Gabelung)
const FEHLER_ERWISCHT := "winter"       # einmal erwischt (vergisst die Fackel)
const FEHLER_KNOPF := "fruehling"       # einmal der falsche Maggie-Knopf
# when the Schutzding helps (m, Welt): maggie_gefahr.gd benutze() – Wasser 8 m, Fackel 14 m, Glocke 40 m, Stock 6 m
const NAH := {"herbst": 7.5, "winter": 11.0, "fruehling": 26.0, "sommer": 4.5}
const SICHT := {"herbst": 24.0, "winter": 26.0, "fruehling": 34.0, "sommer": 8.0}

var main
var story                               # maggie_story.gd
var laeuft := false
var laenge := "kurz"                    # kurz | ganz
var pausiert := false
var ergebnis := ""                      # "" (läuft) | fertig | abgebrochen | unterbrochen
var tempo := 1.0
var stimme := true
var knoepfe := false                   # Daniel (Entwicklung): «Spiel-Knöpfe zeigen» – the normal buttons stay, a press lights up
var vollbild := false

# the autopilot
var _ziel = null                        # Vector3 (Welt) or null = stand still
var _stop_r := 1.2
var _rennen := false
var _ap := {"art": "frei", "t": 0.0}    # frei | station | gabel | helfer | erwischen | begegnung | schnitt | warten
var _plan: Array = []                   # Kurzfassung: the steps of the region [{art, id}]
var _plan_region := ""
var _fehler := {}                       # what was done already: abbiegen / erwischt / knopf
var _benutzt_t := -100.0
var _k_region := {}                     # region -> the crystal was looked into
var _fort_sig := ""
var _fort_t := 0.0
var _stuck_d := 1e9
var _stuck_t := 0.0
var _stuck_n := 0
var _stuck_goal = null
var _umweg_t := 0.0
var _umweg_s := 1.0
var _loese_art := {}                    # station id -> gespielt | Schnitt | erzwungen
var _regionen := {}                     # region -> {gespielt, schnitt, erzwungen, offen, schutz, erwischt}
var blockaden: Array = []               # [{t, wo, was}]
var _zeilen: Array = []
var _t0 := 0.0                          # real start (s)
var _t_spiel := 0.0                     # game time (s, scaled, without pause)
var _abspann := false
var _start_kap := 0
var _hund_ok := false

# cards (the narration)
var _karte_id := 0
var _karte_t := 0.0
var _karte_lese := 4.0

# camera
var _cam_art := "folge"
var _cam_bis := 0.0
var _cam_snap := true
var _cam_ang := 0.0
var _cam_grund := ""

# ui
var _layer: CanvasLayer = null
var _bar: PanelContainer = null
var _bar_lbl: Label = null
var _pause_btn: Button = null
var _kap_menu: MenuButton = null
var _schwarz: ColorRect = null
var _schwarz_lbl: Label = null
var _ende: PanelContainer = null
var _maus_t := -100.0
var _saved_ui := true
var _saved_mode := -1
var _last_tipp := ""
var _last_me := ""


static func _lite() -> bool:
	"""the central question «Lite?» (quality.gd)"""
	return Quality.lite()


# =======================================================================================================================
# the instance (one, under main.maggie) and /control
# =======================================================================================================================
static func inst(m, make := true):
	var mg = m.get("maggie")
	if mg == null:
		return null
	if mg.get("vf") != null and is_instance_valid(mg.vf):
		return mg.vf
	var n = mg.get_node_or_null("vorfuehrung")
	if n == null and make:
		n = load("res://scripts/maggie_vorfuehrung.gd").new()
		n.name = "vorfuehrung"
		n.main = m
		n.story = mg
		mg.add_child(n)
	return n


static func control(m, d: Dictionary) -> Dictionary:
	var v = inst(m)
	if v == null:
		return {"ok": false, "error": "no maggie"}
	match str(d.get("do", "info")):
		"start":
			var ln := str(d.get("len", d.get("laenge", "kurz"))).to_lower()
			ln = "ganz" if ln in ["ganz", "voll", "full", "lang", "long"] else "kurz"
			if d.has("knoepfe"):
				v.set_knoepfe(bool(d["knoepfe"]))
			v.starten(ln, {"tempo": float(d.get("tempo", 1.0)), "stimme": d.get("stimme", null), "vollbild": bool(d.get("vollbild", false)),
					"kapitel": int(d.get("kapitel", 0))})
		"pause":
			v.pause(true)
		"weiter":
			v.pause(false)
		"kapitel":
			if not v.laeuft:
				return {"ok": false, "error": "not running"}
			v.kapitel(int(d.get("n", d.get("value", 0))))
		"stop":
			v.beenden("abgebrochen")
		"info":
			pass
		_:
			return {"ok": false, "error": "do: start (len) | pause | weiter | kapitel (n) | stop | info"}
	return v.info()


static func add_controls(m) -> void:
	"""group «Entwickler» like the Spieltest: «devwin» = not in the panel (own tab «Vorführung» in the window); MoveEye's
	Simulator page shows them in its card «Entwickler» (only with the Entwickler-Bereich = the owner)"""
	m.add_control("button", "vorfuehrung_kurz", "Vorführung «Maggie»: Kurzfassung ansehen (15–20 Min.)", null,
			func(): control(m, {"do": "start", "len": "kurz"}), "Entwickler", {"expert": true, "devwin": true})
	m.add_control("button", "vorfuehrung_ganz", "Vorführung «Maggie»: ganze Geschichte ansehen", null,
			func(): control(m, {"do": "start", "len": "ganz"}), "Entwickler", {"expert": true, "devwin": true})
	m.add_control("button", "vorfuehrung_stop", "Vorführung beenden", null,
			func(): control(m, {"do": "stop"}), "Entwickler", {"expert": true, "devwin": true})
	m.controls[-1]["ro"] = func():
		var v = inst(m, false)
		return v == null or not v.laeuft


func _ready() -> void:
	process_priority = 100                  # after maggie_story (50) and its modules: the buttons they show are hidden again
	process_mode = Node.PROCESS_MODE_ALWAYS
	if story != null:
		story.vf = self
	var d = _json(EINST)
	if d is Dictionary:
		stimme = bool(d.get("stimme", true))
		knoepfe = bool(d.get("knoepfe", false))


static func _json(p: String):
	if not FileAccess.file_exists(p):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(p))


func set_stimme(v: bool) -> void:
	stimme = v
	_einst_schreiben()
	if not v:
		Stimme.stopp()


func set_knoepfe(v: bool) -> void:
	knoepfe = v
	_einst_schreiben()
	if laeuft and not v:
		_hide_controls()


func _einst_schreiben() -> void:
	DirAccess.make_dir_recursive_absolute(EINST.get_base_dir())
	var f := FileAccess.open(EINST, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"stimme": stimme, "knoepfe": knoepfe}))


func _aufleuchten(b) -> void:
	"""«Spiel-Knöpfe zeigen»: the button the autopilot presses lights up briefly, like a real press"""
	if not knoepfe or b == null or not is_instance_valid(b) or not (b is Control):
		return
	var c := b as Control
	c.modulate = Color(1.9, 1.75, 1.0)
	c.scale = Vector2(1.08, 1.08)
	c.pivot_offset = c.size / 2.0
	var tw := c.create_tween()
	tw.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tw.tween_property(c, "modulate", Color.WHITE, 0.6)
	tw.parallel().tween_property(c, "scale", Vector2.ONE, 0.35)


# =======================================================================================================================
# start / end
# =======================================================================================================================
func starten(ln: String, opt := {}) -> void:
	if laeuft:
		beenden("restart")
	if story.running:
		_log("Eine laufende Geschichte wurde verlassen (ihr Fortschritt bleibt gespeichert).")
		story.stop()
	var fig: Dictionary = story.figur()           # (the figure of the active Spielstand, only read)
	laenge = ln
	tempo = clampf(float(opt.get("tempo", 1.0)), 0.25, 4.0)
	if opt.get("stimme", null) != null:
		stimme = bool(opt["stimme"])
	vollbild = bool(opt.get("vollbild", false))
	laeuft = true
	pausiert = false
	ergebnis = ""
	_abspann = false
	_fehler = {}
	_k_region = {}
	_loese_art = {}
	_regionen = {}
	blockaden = []
	_zeilen = []
	_plan = []
	_plan_region = ""
	_hund_ok = false
	_t0 = Time.get_ticks_msec() / 1000.0
	_t_spiel = 0.0
	_ap = {"art": "frei", "t": 0.0}
	_ziel = null
	_fort_t = 0.0
	_fort_sig = ""
	_karte_id = 0
	_last_tipp = ""
	_last_me = ""
	Engine.time_scale = tempo
	Engine.set_meta("vorfuehrung", true)
	story.demo = true
	story.vf = self
	var nm := str(fig.get("name", ""))
	var lk: Dictionary = fig.get("look", {}) if fig.get("look", {}) is Dictionary else {}
	story.S = {"name": nm if nm != "" else T.t("Mia"), "look": lk if not lk.is_empty() else {"col": "orange", "size": "", "build": "", "hat": "", "pack": true},
			"started": int(main.now()), "vorfuehrung": ln}
	story._save()
	_ui()
	_saved_ui = main.ui_layer.visible if main.ui_layer != null else true
	if vollbild and DisplayServer.get_name() != "headless":
		_saved_mode = DisplayServer.window_get_mode()
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	if main.mehr != null:
		main.mehr.close_menu()
	if main.mehr != null and main.mehr.get("dev") != null and main.mehr.dev.has_method("close"):
		main.mehr.dev.close()
	_log("Start: %s (Tempo %s, Stimme %s, Lite %s)" % ["Kurzfassung" if ln == "kurz" else "ganze Geschichte", str(tempo), "an" if _stimme_ok() else "aus", str(_lite())])
	story._ensure_ui()
	story._start()
	_maus_t = _jetzt()
	var k := int(opt.get("kapitel", 0))
	if k > 0:
		kapitel(k)
	else:
		story._start_intro()


func beenden(grund := "abgebrochen") -> void:
	if not laeuft:
		return
	laeuft = false
	ergebnis = grund
	pausiert = false
	Engine.time_scale = 1.0
	Stimme.stopp()
	_log("Ende: %s nach %s (Spielzeit %s). Blockaden: %d." % [grund, _min(_jetzt() - _t0), _min(_t_spiel), blockaden.size()])
	_zusammenfassung()
	_schreiben()
	if story.running:
		story.stop()
	story.demo = false
	if Engine.has_meta("vorfuehrung"):
		Engine.remove_meta("vorfuehrung")
	story._load()                               # back to the state of Daniel's Spielstand
	if main.ui_layer != null:
		main.ui_layer.visible = _saved_ui
	if _saved_mode >= 0 and DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(_saved_mode)
	_saved_mode = -1
	if _bar != null:
		_bar.visible = false
	if _schwarz != null:
		_schwarz.color.a = 0.0
		_schwarz_lbl.modulate.a = 0.0
	_end_card()


func pause(on: bool) -> void:
	if not laeuft or on == pausiert:
		return
	pausiert = on
	Engine.time_scale = 0.0 if on else tempo     # everything stands still (figures, animals, films, timers)
	if story.has_method("_modules_pause"):
		story._modules_pause(on)
	if _stimme_ok():
		if on:
			DisplayServer.tts_pause()
		else:
			DisplayServer.tts_resume()
	_log("Pause" if on else "Weiter")
	_maus_t = _jetzt()
	_paint_bar()


# =======================================================================================================================
# chapters: 0 Einstieg · 1–4 Jahreszeiten · 5 Finale
# =======================================================================================================================
func kapitel_namen() -> Array:
	var a := [T.t("Einstieg: Maggie findet den Kristall")]
	for id in Welt.ORDER:
		a.append(T.t(str(Welt.REG[id]["name"])))
	a.append(T.t("Finale am Gipfel"))
	return a


func kapitel_jetzt() -> int:
	if story == null or not story.running:
		return -1
	var rg := str(story.region)
	if rg != "" and rg in Welt.ORDER:
		return Welt.ORDER.find(rg) + 1
	if str(story.S.get("region", "")) == "finale" or str(story.phase) in ["finale", "finale_walk", "finale_cut", "ende", "abspann"]:
		return 5
	if not bool(story.S.get("intro", false)):
		return 0
	var done: Array = story.S.get("done", [])
	return mini(5, done.size() + 1)


func kapitel(n: int) -> void:
	if not laeuft:
		return
	n = clampi(n, 0, 5)
	if pausiert:
		pause(false)
	_log("Kapitel %d: %s" % [n, kapitel_namen()[n]])
	# what runs now: away (like «Zur Auswahl» of the pause card; old timers stop with the next stage)
	if str(story.region) != "":
		story.region_beendet.emit(story.region)
		story.region = ""
	story._seq += 1
	story._close_cards()
	story._shots.clear()
	story._shot_cb = Callable()
	if story._zk_fx != null:
		story._zk_fx.visible = false
		story._zk_lbl.visible = false
	if story._credits != null and is_instance_valid(story._credits):
		story._credits.queue_free()
		story._credits = null
	if story._fade != null:
		story._fade.color.a = 0.0
		story._fade_lbl.modulate.a = 0.0
	if story._crystal != null and is_instance_valid(story._crystal):
		story._crystal.queue_free()
	story._crystal = null
	story._crystal_on_player = false
	story._clear_stage_things()
	_abspann = false
	_ap = {"art": "frei", "t": 0.0}
	_plan = []
	_plan_region = ""
	_ziel = null
	_fort_t = 0.0
	var done := []
	for i in range(mini(n - 1, 4)):
		done.append(Welt.ORDER[i])
	if n == 5:
		done = Welt.ORDER.duplicate()
	story.S["done"] = done
	story.S["intro"] = n > 0
	story.S["region"] = ""
	story.S["rest"] = 0
	story.S.erase("finale")
	_module_zuruecksetzen(done)
	story._save()
	if n == 0:
		story.has_crystal = false
		story._start_intro()
	elif n <= 4:
		story.has_crystal = true
		story._start_region(Welt.ORDER[n - 1], 0)
	else:
		story.has_crystal = true
		story._start_finale()


func _module_zuruecksetzen(done: Array) -> void:
	"""a chapter again: what Maggie solved and the Schutzding of the regions not done yet are forgotten"""
	var pre := {"herbst": "h_", "winter": "w_", "fruehling": "f_", "sommer": "s_"}
	var h = _hund()
	if h != null:
		for id in (h.geloest as Dictionary).keys():
			var keep := false
			for r in done:
				keep = keep or str(id).begins_with(pre[r])
			if not keep:
				h.geloest.erase(id)
		for r in (h.fertig as Dictionary).keys():
			if not r in done:
				h.fertig.erase(r)
		h.region = ""
	var g = _gef()
	if g != null:
		for r in Welt.ORDER:
			if not r in done:
				(g.schutz as Dictionary).erase(str(g.SCHUTZ[r]))


# =======================================================================================================================
# every frame
# =======================================================================================================================
func _jetzt() -> float:
	return Time.get_ticks_msec() / 1000.0


func _process(dt: float) -> void:
	if not laeuft:
		return
	_hide_controls()
	_ui_tick()
	if pausiert:
		return
	if not story.running:
		beenden("unterbrochen")
		return
	_t_spiel += dt
	_sprich_neu()
	var ph := str(story.phase)
	if ph == "abspann":
		_abspann = true
	var card = story._card
	if card != null and is_instance_valid(card) and ph not in ["film"]:
		_karte(card, ph, dt)
	else:
		_karte_id = 0
	match ph:
		"intro_walk":
			_lauf_ziel(story._next_goal())
			_ziel_tick(dt)
		"region":
			if card == null or not is_instance_valid(card):
				_region(dt)
				_ziel_tick(dt)
				_fortschritt(dt)
		"finale_walk":
			_finale()
			_ziel_tick(dt)
			_fortschritt(dt)
		"ende":
			pass
		_:
			_ziel = null


func _hide_controls() -> void:
	"""no buttons in the film: Maggie's bar, the Schutzding button, the panel of the simulator (the texts stay)"""
	if main.ui_layer != null and main.ui_layer.visible:
		main.ui_layer.visible = false
	if knoepfe:                                     # «Spiel-Knöpfe zeigen»: the game buttons stay (only the panel goes)
		return
	var h = _hund()
	if h != null and h.get("_bar") != null and is_instance_valid(h._bar):
		h._bar.visible = false
	var g = _gef()
	if g != null and g.get("_box_btn") != null and is_instance_valid(g._box_btn):
		g._box_btn.visible = false
	if story._kbtn != null:
		story._kbtn.visible = false
	var card = story._card
	if card != null and is_instance_valid(card):
		for b in card.find_children("*", "Button", true, false):
			(b as Button).visible = false


func _hund():
	return story.get_node_or_null("maggie_hund") if story != null else null


func _gef():
	return story.get_node_or_null("maggie_gefahr") if story != null else null


# ---- the cards: read (and hear) them, then the button a player would press ---------------------------------------------
func _karte(card: Control, ph: String, dt: float) -> void:
	var cid := card.get_instance_id()
	if cid != _karte_id:
		_karte_id = cid
		_karte_t = 0.0
		var txt := []
		for l in card.find_children("*", "Label", true, false):
			if (l as Label).text != "":
				txt.append((l as Label).text)
		var all := " ".join(txt)
		_karte_lese = clampf(2.5 + all.length() * (0.045 if laenge == "kurz" else 0.06), 3.0, 16.0)
		if ph == "reise":
			_karte_lese = 1e9                     # «Unterwegs …»: goes away by itself
		_sprich(all, true)
		_cam_set("fahrt", 30.0, "card")
		return
	_karte_t += dt
	if _karte_t < _karte_lese or (_stimme_ok() and DisplayServer.tts_is_speaking() and _karte_t < _karte_lese + 25.0):
		return
	_karte_t = -1e9                               # once
	match ph:
		"auswahl":
			var done: Array = story.S.get("done", [])
			for id in Welt.ORDER:
				if not id in done:
					_log("Wählt: %s" % T.t(str(Welt.REG[id]["name"])))
					if await _knopf_zeigen(card, T.t(str(Welt.REG[id]["name"]))):
						story._start_region(id, 0)
					return
			_log("Wählt: Zum Gipfel")
			if await _knopf_zeigen(card, T.t("Zum Gipfel")):
				story._start_finale()
		"ende":
			if _abspann:
				beenden("fertig")
			elif await _knopf_zeigen(card, ""):
				story._press_primary()
		_:
			if await _knopf_zeigen(card, ""):
				story._press_primary()


func _knopf_zeigen(card: Control, text: String) -> bool:
	"""«Spiel-Knöpfe zeigen»: the button of the card lights up, a moment later it is pressed (false = card gone meanwhile)"""
	if not knoepfe:
		return true
	var b: Button = null
	for n in card.find_children("*", "Button", true, false):
		var bt := n as Button
		if not bt.visible or bt.disabled:
			continue
		if text != "" and bt.text.find(text) >= 0:
			b = bt
			break
		if text == "" and bt.has_theme_stylebox_override("normal") and bt.get_theme_stylebox("normal").bg_color == UI.ACC:
			b = bt
			break
	if b == null:
		return true
	_aufleuchten(b)
	await get_tree().create_timer(0.45, true).timeout
	return laeuft and is_instance_valid(card) and story._card == card


# =======================================================================================================================
# the autopilot: walking
# =======================================================================================================================
func steuern(a, dt: float) -> void:
	"""maggie_story._steer: the figure walks like with W A S D (ctl_move = direction in the world)"""
	if not laeuft or pausiert or _ziel == null or str(story.phase) not in WALK:
		a.ctl_move = Vector2.ZERO
		a.ctl_run = false
		return
	var p: Vector3 = a.global_position
	var z: Vector3 = _ziel
	var d := Vector2(z.x - p.x, z.z - p.z)
	if d.length() < _stop_r:
		a.ctl_move = Vector2.ZERO
		a.ctl_run = false
		return
	var dir := d.normalized()
	if _umweg_t > 0.0:
		_umweg_t -= dt
		dir = dir.rotated(_umweg_s * 1.25)
	a.ctl_move = dir * (1.0 if d.length() > 2.5 else 0.6)
	a.ctl_run = _rennen and d.length() > 3.0


func _lauf_ziel(g: Array, r := 1.2) -> void:
	if g.is_empty():
		_ziel = null
		return
	_ziel = g[0]
	_stop_r = r


func _ziel_tick(dt: float) -> void:
	"""not getting closer: a detour; four times on the same goal = BLOCKIERT (protocol) and a jump to the goal"""
	if _ziel == null:
		_stuck_t = 0.0
		return
	var z: Vector3 = _ziel
	var sg: Vector3 = _stuck_goal if _stuck_goal != null else Vector3(1e9, 0, 1e9)
	if sg.distance_to(z) > 3.0:
		_stuck_goal = z
		_stuck_n = 0
		_stuck_t = 0.0
		_stuck_d = 1e9
	var p: Vector3 = story.spieler_pos()
	var d := Vector2(z.x - p.x, z.z - p.z).length()
	if d <= _stop_r + 0.3:
		_stuck_t = 0.0
		_stuck_d = d
		return
	_stuck_t += dt
	if _stuck_t < 4.0:
		return
	_stuck_t = 0.0
	if _stuck_d - d < 1.0:
		_stuck_n += 1
		if _stuck_n >= 4:
			log_line("Weg versperrt – %d m vor dem Ziel" % int(d))
			var back := Vector3(p.x - z.x, 0, p.z - z.z)
			back = back.normalized() if back.length() > 0.1 else Vector3(1, 0, 0)
			story.spieler_setzen(z + back * maxf(1.0, _stop_r * 0.5))
			_cam_snap = true
			_stuck_n = 0
		else:
			_umweg_s = -_umweg_s
			_umweg_t = 2.5
	_stuck_d = d


func log_line(was: String) -> void:
	var wo := str(story.region) if str(story.region) != "" else str(story.phase)
	blockaden.append({"t": _min(_t_spiel), "wo": wo, "was": was})
	_log("BLOCKIERT (%s): %s" % [wo, was])


func _fortschritt(dt: float) -> void:
	"""nothing new for a long time (tasks, rest places, gate): BLOCKIERT and the next step is forced"""
	var n := 0
	for id in story._tasks:
		n += 1 if bool(story._tasks[id]["done"]) else 0
	var r := 0
	for e in story._rests:
		r += 1 if bool(e["reached"]) else 0
	var sig := "%s|%d|%d|%s|%s|%s" % [story.region, n, r, str(story._tor_open), str(story.phase), str(_ap.get("art", ""))]
	if sig != _fort_sig:
		_fort_sig = sig
		_fort_t = 0.0
		return
	_fort_t += dt
	if _fort_t < (240.0 if laenge == "kurz" else 480.0):
		return
	_fort_t = 0.0
	var h = _hund()
	var st: Dictionary = h.aktuell() if h != null else {}
	if not st.is_empty():
		log_line("kein Fortschritt bei der Station «%s»" % str(st["id"]))
		_loese(st, "erzwungen")
	elif _ziel != null:
		log_line("kein Fortschritt auf dem Weg")
		story.spieler_setzen(_ziel)
	_ap = {"art": "frei", "t": 0.0}


# ---- a region ------------------------------------------------------------------------------------------------------------
func _region(dt: float) -> void:
	var rg := str(story.region)
	if rg == "":
		return
	_hund_verbinden()
	if not _regionen.has(rg):
		_regionen[rg] = {"gespielt": 0, "schnitt": 0, "erzwungen": 0, "offen": 0, "schutz": false, "erwischt": 0}
	_ap["t"] = float(_ap.get("t", 0.0)) + dt
	var h = _hund()
	var g = _gef()
	if laenge == "kurz" and _plan_region != rg and h != null and not (h.stationen as Array).is_empty() and str(h.region) == rg:
		_plan_bauen(rg, h)
	_rennen = false
	if _gefahr(rg, g):
		return
	# looking into the crystal (K) once per region, a little after the start
	if not _k_region.has(rg) and float(_ap.get("t", 0.0)) > 3.0 and _t_seit_region() > (25.0 if laenge == "kurz" else 50.0) \
			and str(_ap.get("art", "")) == "frei" and story.main.now() >= float(story._zk_ready_at):
		_k_region[rg] = true
		_log("Schaut in den Kristall (K)")
		_aufleuchten(story._kbtn)
		story.look_into_crystal()
		return
	match str(_ap.get("art", "frei")):
		"frei":
			if laenge == "kurz" and not _plan.is_empty():
				_plan_schritt(rg, h, g)
				return
			_frei(h)
		"station":
			_station(h)
		"gabel":
			_gabel(h)
		"helfer":
			_helfer(h)
		"erwischen":
			_erwischen(g)
		"begegnung":
			_begegnung(rg, g)
		"hin":
			_hin(h)
		"schnitt", "warten":
			_ziel = null


func _t_seit_region() -> float:
	return story.main.now() - float(story._region_t0)


func _frei(h) -> void:
	"""follow the arrow of the story (_next_goal: stations in order, rest places, the Schutzding, the gate)"""
	var g: Array = story._next_goal()
	_lauf_ziel(g, 1.0)
	_station_nah(h)


func _station_nah(h) -> bool:
	"""close to the current station of Maggie: solve it like a player"""
	if h == null:
		return false
	var st: Dictionary = h.aktuell()
	if st.is_empty() or (h.geloest as Dictionary).has(str(st["id"])):
		return false
	var d := _tal_d(h, st["p"])
	var f := str(st["f"])
	if f in FAEHIG and d < 4.5:
		_ap = {"art": "station", "t": 0.0, "id": str(st["id"]), "n": 0}
		_ziel = null
		_cam_set("nah", 14.0, "station")
		return true
	if f == "warnen" and d < 3.5:
		_ap = {"art": "gabel", "t": 0.0, "id": str(st["id"]), "falsch": str(story.region) == FEHLER_ABBIEGEN and not _fehler.has("abbiegen")}
		_cam_set("totale", 10.0, "fork")
		return true
	if f == "helfer" and d < 5.0:
		_ap = {"art": "helfer", "t": 0.0, "id": str(st["id"])}
		_ziel = null
		_cam_set("totale", 14.0, "ibex")
		return true
	_ziel = story.tal_punkt((st["p"] as Vector3).x, (st["p"] as Vector3).z) if _ziel == null else _ziel
	return false


func _tal_d(h, tp: Vector3) -> float:
	var sp: Vector3 = h.VL(story.spieler_pos())
	return Vector2(sp.x - tp.x, sp.z - tp.z).length()


func _welt(tp: Vector3) -> Vector3:
	return story.tal_punkt(tp.x, tp.z)


func _station(h) -> void:
	_ziel = null
	var st: Dictionary = h.aktuell() if h != null else {}
	if st.is_empty() or str(st["id"]) != str(_ap.get("id", "")) or (h.geloest as Dictionary).has(str(_ap.get("id", ""))):
		_ap = {"art": "frei", "t": 0.0}
		return
	var t := float(_ap["t"])
	var f := str(st["f"])
	var n := int(_ap.get("n", 0))
	if n == 0 and t > 1.6:
		_ap["n"] = 1
		if str(story.region) == FEHLER_KNOPF and not _fehler.has("knopf"):
			_fehler["knopf"] = true
			var falsch := "riechen" if f != "riechen" else "graben"
			_log("Fehler (Absicht): falscher Maggie-Knopf «%s» bei «%s»" % [falsch, str(st["id"])])
			h.befehl(falsch)
			_ap["n"] = 2
			_ap["t"] = -2.5                       # a moment to see that it did not work
			return
		_druecke(h, f, st)
	elif n == 2 and t > 1.0:
		_ap["n"] = 1
		_druecke(h, f, st)
	elif n == 1 and t > 30.0:
		var frei: bool = str(h.zustand_hund) == "folgen"     # (Maggie still busy: the trail can take a minute)
		if int(_ap.get("tries", 0)) < 2 and frei and t > 35.0:
			_ap["tries"] = int(_ap.get("tries", 0)) + 1
			_ap["t"] = 0.0
			_druecke(h, f, st)
		elif t > 150.0 or (frei and int(_ap.get("tries", 0)) >= 2 and t > 60.0):
			log_line("Station «%s» löst sich nicht" % str(st["id"]))
			_loese(st, "erzwungen")
			_ap = {"art": "frei", "t": 0.0}


func _druecke(h, f: String, st: Dictionary) -> void:
	var r: Dictionary = h.befehl(f)
	if str(r.get("error", "")) != "busy" and h.get("_knoepfe") is Dictionary:
		_aufleuchten((h._knoepfe as Dictionary).get(f))
	if str(r.get("error", "")) == "busy":           # Maggie is still busy (barks, sniffs): a moment later again
		_ap["n"] = 2
		_ap["t"] = -1.5
		return
	_log("Maggie-Knopf «%s» bei «%s»: %s" % [f, str(st["id"]), "löst" if str(r.get("loest", "")) != "" else str(r.get("error", "nichts"))])


func _gabel(h) -> void:
	var st: Dictionary = h.aktuell() if h != null else {}
	if st.is_empty() or str(st["id"]) != str(_ap.get("id", "")) or (h.geloest as Dictionary).has(str(_ap.get("id", ""))):
		_ap = {"art": "frei", "t": 0.0}
		return
	var t := float(_ap["t"])
	if bool(_ap.get("falsch", false)):
		_lauf_ziel([_welt(st["boese_p"])], 2.5)
		if _tal_d(h, st["boese_p"]) < 3.6 or t > 9.0:
			_fehler["abbiegen"] = true
			_log("Fehler (Absicht): falsch abgebogen bei «%s» – Maggie bellt" % str(st["id"]))
			_ap["falsch"] = false
			_ap["t"] = -2.0
			_ziel = null
			_cam_set("nah", 6.0, "bark")
		return
	if t < 0.0:
		_ziel = null
		return
	_lauf_ziel([_welt(st["gut_p"])], 0.8)
	if t > 45.0:
		log_line("Gabelung «%s»: der gute Weg wird nicht erreicht" % str(st["id"]))
		_loese(st, "erzwungen")
		_ap = {"art": "frei", "t": 0.0}


func _helfer(h) -> void:
	_ziel = null
	var st: Dictionary = h.aktuell() if h != null else {}
	if st.is_empty() or (h.geloest as Dictionary).has(str(_ap.get("id", ""))):
		_ap = {"art": "frei", "t": 0.0}
		return
	if float(_ap["t"]) > 45.0:
		log_line("der Steinbock kommt nicht («%s»)" % str(st["id"]))
		_loese(st, "erzwungen")
		_ap = {"art": "frei", "t": 0.0}


func _loese(st: Dictionary, art: String) -> void:
	var h = _hund()
	if h == null or (h.geloest as Dictionary).has(str(st["id"])):
		return
	_loese_art[str(st["id"])] = art
	h._fertig(st)


func _hund_verbinden() -> void:
	var h = _hund()
	if h == null or _hund_ok:
		return
	if h.has_signal("raetsel_geloest") and not h.is_connected("raetsel_geloest", _geloest):
		h.raetsel_geloest.connect(_geloest)
	var g = _gef()
	if g != null and g.has_signal("erwischt_von") and not g.is_connected("erwischt_von", _erwischt_von):
		g.erwischt_von.connect(_erwischt_von)
	if g != null and g.has_signal("schutz_gefunden") and not g.is_connected("schutz_gefunden", _schutz):
		g.schutz_gefunden.connect(_schutz)
	if story.has_signal("region_beendet") and not story.is_connected("region_beendet", _region_ende):
		story.region_beendet.connect(_region_ende)
	_hund_ok = true


func _geloest(rg: String, id: String) -> void:
	var art := str(_loese_art.get(id, "gespielt"))
	if _regionen.has(rg):
		_regionen[rg][art if art in ["gespielt", "schnitt", "erzwungen"] else "gespielt"] += 1
	_log("Station «%s» gelöst (%s)" % [id, art])


func _erwischt_von(art: String) -> void:
	var rg := str(story.region)
	if rg == FEHLER_ERWISCHT:
		_fehler["erwischt"] = true                  # (caught anyway: the planned mistake is done)
	if str(_ap.get("art", "")) == "erwischen":
		_ap["gefangen"] = art
	if _regionen.has(rg):
		_regionen[rg]["erwischt"] += 1
	_log("Erwischt von: %s – zurück zum Rastplatz" % art)


func _schutz(id: String) -> void:
	var rg := str(story.region)
	if _regionen.has(rg):
		_regionen[rg]["schutz"] = true
	_log("Schutzding gefunden: %s" % id)


func _region_ende(id: String) -> void:
	if not laeuft or not _regionen.has(id):
		return
	var offen := 0
	for k in story._tasks:
		offen += 0 if bool(story._tasks[k]["done"]) else 1
	_regionen[id]["offen"] = offen
	var r: Dictionary = _regionen[id]
	_log("Region %s zu Ende: gespielt %d, Schnitt %d, erzwungen %d, offen %d, Schutzding %s, erwischt %d" % [id, r["gespielt"], r["schnitt"],
			r["erzwungen"], offen, "ja" if r["schutz"] else "nein", r["erwischt"]])
	_schreiben()


# ---- danger: the Schutzding like key B (and the planned mistake) ----------------------------------------------------------
func _gefahr(rg: String, g) -> bool:
	"""true = this tick belongs to the danger (the mistake «erwischt» walks towards it)"""
	if g == null or not NAH.has(rg):
		return false
	if str(_ap.get("art", "")) in ["erwischen", "schnitt"]:
		return false
	var ng: Dictionary = g.naechste_gefahr()
	var d := float(ng.get("dist", 9999.0))
	var schutz_id := str(g.SCHUTZ[rg])
	var hat: bool = g.schutz_hat(schutz_id)
	if d < SICHT[rg]:
		_rennen = not hat
		if _cam_grund != "danger":
			_cam_set("totale", 8.0, "danger")
	if not hat or d > NAH[rg]:
		return false
	if rg == FEHLER_ERWISCHT and not _fehler.has("erwischt") and str(_ap.get("art", "")) in ["frei", "begegnung"]:
		_fehler["erwischt"] = true
		_log("Fehler (Absicht): vergisst die %s – das Tier kommt nah" % T.t(str(g.SCHUTZ_NAME[schutz_id])))
		_ap = {"art": "erwischen", "t": 0.0, "n0": int(story.S.get("erwischt", 0))}
		return true
	if story.main.now() - _benutzt_t < (1.2 if rg == "winter" else 2.5):
		return false
	_benutzt_t = story.main.now()
	if g.get("_box_btn") != null:
		_aufleuchten(g._box_btn)
	var r: Dictionary = g.benutze()
	if int(r.get("vertrieben", 0)) > 0 or r.has("fackel"):
		_log("Schutzding benutzt: %s" % ("Fackel an" if r.has("fackel") else "%d vertrieben" % int(r["vertrieben"])))
		if str(_ap.get("art", "")) == "begegnung" and int(r.get("vertrieben", 0)) > 0:
			_ap["vertrieben"] = true
	return false


func _erwischen(g) -> void:
	var t := float(_ap["t"])
	if int(story.S.get("erwischt", 0)) > int(_ap.get("n0", 0)):    # caught (the fright ran): the planned mistake is done
		t = 99.0
	elif str(story.phase) != "region":
		return
	if g != null:
		var ng: Dictionary = g.naechste_gefahr()
		if float(ng.get("dist", 9999.0)) < 200.0:
			_lauf_ziel([ng["pos"]], 0.3)
	if _ap.has("gefangen") and t > 1.0 and str(story.phase) != "schreck":
		story._safe_until = 0.0                     # the animal caught the figure during the short rest after a cut: show the fright now
		story.erwischt(str(_ap["gefangen"]))
		_ap.erase("gefangen")
		t = 99.0
	if t > 25.0 and t < 99.0 and str(story.phase) == "region":
		_log("Das Tier kommt nicht – erwischt von Hand (story.erwischt)")
		story.erwischt(str(g.TIER[str(story.region)]["art"]) if g != null else "wolf")
		t = 99.0
	if t >= 99.0 or t > 30.0:
		_ap = {"art": "warten", "t": 0.0}
		if laenge == "kurz":
			_plan.push_front({"art": "begegnung"})     # once more - this time with the Schutzding
		await get_tree().create_timer(6.0).timeout
		if laeuft and str(_ap.get("art", "")) == "warten":
			_ap = {"art": "frei", "t": 0.0}


# =======================================================================================================================
# the short version: the highlights of a region, cuts in between
# =======================================================================================================================
func _plan_bauen(rg: String, h) -> void:
	_plan_region = rg
	_plan = []
	var sts: Array = h.stationen
	var erst := ""
	for st in sts:
		if str(st["f"]) in FAEHIG and not (h.geloest as Dictionary).has(str(st["id"])):
			erst = str(st["id"])
			break
	if erst != "":
		_plan.append({"art": "station", "id": erst})
	if rg == FEHLER_ABBIEGEN:
		for st in sts:
			if str(st["f"]) == "warnen" and not (h.geloest as Dictionary).has(str(st["id"])):
				_plan.append({"art": "station", "id": str(st["id"])})
				break
	if rg == "sommer":
		for st in sts:                                  # the Steinbock is a highlight of the summer
			if str(st["f"]) == "helfer" and not (h.geloest as Dictionary).has(str(st["id"])):
				_plan.append({"art": "station", "id": str(st["id"])})
				break
	_plan.sort_custom(func(a, b): return _st_i(h, str(a["id"])) < _st_i(h, str(b["id"])))
	_plan.append({"art": "schutz"})
	_plan.append({"art": "begegnung"})
	_plan.append({"art": "tor"})
	var names := []
	for s in _plan:
		names.append(str(s["art"]) + ("·" + str(s["id"]) if s.has("id") else ""))
	_log("Kurzfassung %s: %s" % [rg, ", ".join(names)])


func _st_i(h, id: String) -> int:
	var sts: Array = h.stationen
	for i in range(sts.size()):
		if str(sts[i]["id"]) == id:
			return i
	return 99


func _plan_schritt(rg: String, h, g) -> void:
	var s: Dictionary = _plan[0]
	match str(s["art"]):
		"station":
			var i := _st_i(h, str(s["id"]))
			for k in range(mini(i, (h.stationen as Array).size())):     # the stations before it: solved «in the cut»
				var sk: Dictionary = h.stationen[k]
				if not (h.geloest as Dictionary).has(str(sk["id"])):
					_loese(sk, "cut")
			var st: Dictionary = h.aktuell()
			if st.is_empty() or str(st["id"]) != str(s["id"]):
				_plan.pop_front()
				return
			_plan.pop_front()
			_schnitt(_welt(st["p"]), 22.0, {"art": "hin", "t": 0.0, "id": str(st["id"])})
		"schutz":
			_plan.pop_front()
			if g == null or g.schutz_hat(str(g.SCHUTZ[rg])):
				return
			_schnitt(g.schutz_ort(rg), 15.0, {"art": "hin", "t": 0.0, "schutz": true})
		"begegnung":
			_plan.pop_front()
			if g == null:
				return
			var ng: Dictionary = g.naechste_gefahr()
			var z: Vector3 = ng["pos"] if float(ng.get("dist", 9999.0)) < 600.0 else g.zukunft_ziel()
			z.y = story.main.ground_y(z.x, z.z)
			_schnitt(z, 9.0 if rg == "sommer" else 32.0, {"art": "begegnung", "t": 0.0, "z": z})
		"tor":
			_plan.pop_front()
			for st2 in h.stationen:                    # what is left: solved in the cut
				if not (h.geloest as Dictionary).has(str(st2["id"])):
					_loese(st2, "cut")
			_schnitt(story._tor_p, 20.0, {"art": "frei", "t": 0.0})


func _hin(h) -> void:
	"""after a cut: walk the last metres to the station / the Schutzding (the station itself like a player)"""
	if bool(_ap.get("schutz", false)):
		var g = _gef()
		if g == null or g.schutz_hat(str(g.SCHUTZ[str(story.region)])) or float(_ap["t"]) > 40.0:
			if float(_ap["t"]) > 40.0:
				log_line("Schutzding nicht erreicht")
			_ap = {"art": "frei", "t": 0.0}
			return
		_lauf_ziel([g.schutz_ort(str(story.region))], 0.6)
		return
	if not _station_nah(h):
		var st: Dictionary = h.aktuell() if h != null else {}
		if st.is_empty() or (h.geloest as Dictionary).has(str(_ap.get("id", ""))):
			_ap = {"art": "frei", "t": 0.0}
			return
		_lauf_ziel([_welt(st["p"])], 1.0)
		if float(_ap["t"]) > 50.0:
			log_line("Station «%s» nach dem Schnitt nicht erreicht" % str(st["id"]))
			_loese(st, "erzwungen")
			_ap = {"art": "frei", "t": 0.0}


func _begegnung(rg: String, g) -> void:
	if g == null or bool(_ap.get("vertrieben", false)) or float(_ap["t"]) > 35.0:
		if float(_ap["t"]) > 35.0 and not bool(_ap.get("vertrieben", false)):
			_log("Begegnung ohne Vertreiben zu Ende (das Tier kam nicht nah)")
		_ap = {"art": "warten", "t": 0.0}
		_weiter_nach(3.0)
		return
	var ng: Dictionary = g.naechste_gefahr()
	var z: Vector3 = ng["pos"] if float(ng.get("dist", 9999.0)) < 120.0 else _ap["z"]
	_lauf_ziel([z], NAH[rg] * 0.5)


func _weiter_nach(s: float) -> void:
	await get_tree().create_timer(s).timeout
	if laeuft and str(_ap.get("art", "")) == "warten":
		_ap = {"art": "frei", "t": 0.0}


func _schnitt(ziel: Vector3, abstand: float, danach: Dictionary) -> void:
	"""a cut: black, «Etwas später …», the figure a little before the goal, light again"""
	_ap = {"art": "schnitt", "t": 0.0}
	_ziel = null
	var sq: int = story._seq
	var tw := create_tween()
	tw.tween_property(_schwarz, "color:a", 1.0, 0.45)
	tw.parallel().tween_property(_schwarz_lbl, "modulate:a", 1.0, 0.45)
	_schwarz_lbl.text = [T.t("Etwas später …"), T.t("Ein Stück weiter …"), T.t("Kurz darauf …")][randi() % 3]
	await tw.finished
	if not laeuft or sq != story._seq or str(story.phase) != "region":
		_schwarz.color.a = 0.0
		_schwarz_lbl.modulate.a = 0.0
		return
	var p: Vector3 = story.spieler_pos()
	var dir := Vector3(p.x - ziel.x, 0, p.z - ziel.z)
	dir = dir.normalized() if dir.length() > 0.5 else Vector3(1, 0, 0)
	var at := ziel + dir * abstand
	story._safe_until = maxf(float(story._safe_until), story.main.now() + 3.0)
	story.spieler_setzen(at)
	var h = _hund()
	if h != null and h.hund != null and is_instance_valid(h.hund):
		var tp: Vector3 = h.VL(at + dir.cross(Vector3.UP) * 1.2)
		h.place(h.hund, tp)
	_cam_snap = true
	_cam_set("folge", 9.0, "cut")
	await get_tree().create_timer(0.7).timeout
	var tw2 := create_tween()
	tw2.tween_property(_schwarz, "color:a", 0.0, 0.6)
	tw2.parallel().tween_property(_schwarz_lbl, "modulate:a", 0.0, 0.4)
	if laeuft and sq == story._seq:
		_ap = danach


# ---- the summit -----------------------------------------------------------------------------------------------------------
func _finale() -> void:
	var ch = story._chapel
	if ch == null or not is_instance_valid(ch):
		_lauf_ziel(story._next_goal())
		return
	var lp: Vector3 = (ch as Node3D).to_local(story.spieler_pos())
	var hl := Welt.CH_L / 2.0
	if laenge == "kurz" and not _fehler.has("finale_schnitt") and lp.length() > 45.0:
		_fehler["finale_schnitt"] = true
		_finale_schnitt(ch)
		return
	if str(_ap.get("art", "")) == "schnitt":
		return
	_cam_set("folge" if lp.z > hl + 6.0 else "fahrt", 8.0, "chapel")
	if lp.z > hl + 0.2 and absf(lp.x) > 0.45:
		_lauf_ziel([(ch as Node3D).to_global(Vector3(0, 0, hl + 1.4))], 0.4)
	elif lp.z > hl - 0.6:
		_lauf_ziel([(ch as Node3D).to_global(Vector3(0, 0, hl - 1.2))], 0.3)
	else:
		_lauf_ziel([(ch as Node3D).to_global(Welt.ALTAR + Vector3(0, 0, 0.75))], 0.25)


func _finale_schnitt(ch) -> void:
	_ap = {"art": "schnitt", "t": 0.0}
	var tw := create_tween()
	_schwarz_lbl.text = T.t("Der Weg hinauf …")
	tw.tween_property(_schwarz, "color:a", 1.0, 0.45)
	tw.parallel().tween_property(_schwarz_lbl, "modulate:a", 1.0, 0.45)
	await tw.finished
	if laeuft and str(story.phase) == "finale_walk":
		story.spieler_setzen((ch as Node3D).to_global(Vector3(0, 0, Welt.CH_L / 2.0 + 24.0)))
		_cam_snap = true
	await get_tree().create_timer(0.6).timeout
	var tw2 := create_tween()
	tw2.tween_property(_schwarz, "color:a", 0.0, 0.6)
	tw2.parallel().tween_property(_schwarz_lbl, "modulate:a", 0.0, 0.4)
	_ap = {"art": "frei", "t": 0.0}


# =======================================================================================================================
# the camera of the film
# =======================================================================================================================
func _cam_set(art: String, secs: float, grund: String) -> void:
	if art != _cam_art:
		_cam_snap = true
	_cam_art = art
	_cam_bis = _t_spiel + secs
	_cam_grund = grund


func kamera(cam: Camera3D, dt: float) -> bool:
	"""maggie_story._cam: true = the film has the camera"""
	if not laeuft:
		return false
	var a = story.spieler()
	if a == null:
		return false
	if _t_spiel > _cam_bis:                          # a new shot (hard cut)
		var arten := ["folge", "nah", "totale", "fahrt", "vorne"] if not _lite() else ["folge", "nah", "totale"]
		var neu := _cam_art
		while neu == _cam_art:
			neu = arten[randi() % arten.size()]
		_cam_set(neu, randf_range(7.0, 12.0) * (1.4 if _lite() else 1.0), "")
	var p: Vector3 = a.global_position
	var hd := float(a.heading)
	var fw := Vector3(-sin(hd), 0, -cos(hd))
	var rt := fw.cross(Vector3.UP)
	var at := p
	var look := p + Vector3(0, 1.2, 0)
	match _cam_art:
		"folge":
			at = p - fw * 6.5 + Vector3(0, 3.0, 0)
			look = p + fw * 4.0 + Vector3(0, 1.1, 0)
		"nah":
			var mp := p
			var h = _hund()
			if h != null and h.hund != null and is_instance_valid(h.hund):
				mp = (h.hund as Node3D).global_position
			var side := (mp - p)
			side.y = 0
			side = side.normalized().cross(Vector3.UP) if side.length() > 0.2 else rt
			at = mp + side * 2.4 + Vector3(0, 0.9, 0) - fw * 0.6
			look = mp.lerp(p, 0.3) + Vector3(0, 0.45, 0)
		"totale":
			at = p - fw * 20.0 + rt * 8.0 + Vector3(0, 13.0, 0)
			look = p + fw * 8.0
		"fahrt":
			_cam_ang += dt * 0.16
			at = p + Vector3(cos(_cam_ang) * 9.0, 3.6, sin(_cam_ang) * 9.0)
			look = p + Vector3(0, 1.1, 0)
		"vorne":
			at = p + fw * 6.0 + rt * 1.5 + Vector3(0, 1.7, 0)
			look = p + Vector3(0, 1.3, 0)
	at.y = maxf(at.y, main.ground_y(at.x, at.z) + 0.7)
	if at.distance_to(look) < 0.5:
		look = at + fw
	var want := Transform3D(Basis.IDENTITY, at).looking_at(look, Vector3.UP)
	if _cam_snap or _lite():
		cam.global_transform = want
		_cam_snap = false
	else:
		cam.global_transform = cam.global_transform.interpolate_with(want, clampf(dt * 2.2, 0.0, 1.0))
	return true


# =======================================================================================================================
# keys (maggie_story._unhandled_input asks first)
# =======================================================================================================================
func taste(ev: InputEvent) -> bool:
	if not laeuft:
		return false
	if ev is InputEventMouseMotion:
		_maus_t = _jetzt()
		return true
	if ev is InputEventKey and ev.pressed and not ev.echo:
		_maus_t = _jetzt()
		match ev.keycode:
			KEY_ESCAPE:
				beenden("abgebrochen")
			KEY_SPACE, KEY_P:
				pause(not pausiert)
			KEY_RIGHT, KEY_PAGEDOWN:
				kapitel(maxi(0, kapitel_jetzt()) + 1)
			KEY_LEFT, KEY_PAGEUP:
				kapitel(maxi(0, kapitel_jetzt() - 1))
	return ev is InputEventKey or ev is InputEventMouseButton or ev is InputEventJoypadButton


# =======================================================================================================================
# voice (abenteuer_stimme.gd: the speech of the system) – cards, tips, MoveEye
# =======================================================================================================================
func _stimme_ok() -> bool:
	return stimme and Stimme.moeglich()


func _sprich(text: String, vorne := false) -> void:
	if not _stimme_ok():
		return
	var t := text.replace("«", "").replace("»", "").replace("\n", " ").strip_edges()
	if t == "":
		return
	if vorne:
		DisplayServer.tts_stop()
	DisplayServer.tts_speak(t, Stimme._pick(), 80, 1.0, 1.0, 0, false)


func _sprich_neu() -> void:
	if story._tipp != null and story._tipp.visible and story._tipp.text != _last_tipp:
		_last_tipp = story._tipp.text
		_sprich(_last_tipp)
	if story._me_box != null and story._me_box.visible and story._me_lbl.text != _last_me:
		_last_me = story._me_lbl.text
		_sprich(_last_me)


# =======================================================================================================================
# the small bar (Pause / Weiter / Kapitel / Beenden), the black of a cut, the end card
# =======================================================================================================================
func _ui() -> void:
	if _layer != null:
		_bar.visible = true
		if _ende != null and is_instance_valid(_ende):
			_ende.queue_free()
			_ende = null
		_paint_bar()
		return
	_layer = CanvasLayer.new()
	_layer.layer = 75
	add_child(_layer)
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = UI.theme()
	_layer.add_child(root)
	_schwarz = ColorRect.new()
	_schwarz.color = Color(0, 0, 0, 0)
	_schwarz.set_anchors_preset(Control.PRESET_FULL_RECT)
	_schwarz.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_schwarz)
	_schwarz_lbl = Label.new()
	_schwarz_lbl.set_anchors_preset(Control.PRESET_CENTER)
	_schwarz_lbl.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_schwarz_lbl.grow_vertical = Control.GROW_DIRECTION_BOTH
	_schwarz_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_schwarz_lbl.add_theme_font_size_override("font_size", 26)
	_schwarz_lbl.add_theme_color_override("font_color", Color(0.85, 0.88, 0.94))
	_schwarz_lbl.modulate.a = 0.0
	root.add_child(_schwarz_lbl)
	_bar = PanelContainer.new()
	_bar.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.86), UI.LINE, 12, 8))
	_bar.anchor_left = 0.5
	_bar.anchor_right = 0.5
	_bar.anchor_top = 1.0
	_bar.anchor_bottom = 1.0
	_bar.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_bar.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_bar.offset_bottom = -14
	root.add_child(_bar)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	_bar.add_child(v)
	_bar_lbl = Label.new()
	_bar_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_bar_lbl.add_theme_font_size_override("font_size", 13)
	_bar_lbl.add_theme_color_override("font_color", UI.MUT)
	v.add_child(_bar_lbl)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 6)
	hb.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(hb)
	_pause_btn = _btn(hb, T.t("Pause"), func(): pause(not pausiert))
	_btn(hb, T.t("Kapitel zurück"), func(): kapitel(maxi(0, kapitel_jetzt() - 1)))
	_kap_menu = MenuButton.new()
	_kap_menu.text = T.t("Kapitel …")
	_kap_menu.flat = false
	_kap_menu.focus_mode = Control.FOCUS_NONE
	_kap_menu.get_popup().id_pressed.connect(func(i): kapitel(i))
	hb.add_child(_kap_menu)
	_btn(hb, T.t("Nächstes Kapitel"), func(): kapitel(maxi(0, kapitel_jetzt()) + 1))
	_btn(hb, T.t("Beenden (Esc)"), func(): beenden("abgebrochen"))
	_paint_bar()


func _btn(p: Control, t: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = t
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(0, 34)
	b.pressed.connect(cb)
	p.add_child(b)
	return b


func _paint_bar() -> void:
	if _bar == null:
		return
	_pause_btn.text = T.t("Weiter") if pausiert else T.t("Pause")
	var pp := _kap_menu.get_popup()
	pp.clear()
	var nm := kapitel_namen()
	for i in range(nm.size()):
		pp.add_item("%d · %s" % [i, nm[i]], i)


func _ui_tick() -> void:
	if _bar == null:
		return
	var k := kapitel_jetzt()
	var nm := kapitel_namen()
	_bar_lbl.text = T.t("Vorführung «Maggie und der Bergkristall» · %s · Kapitel %d von 6: %s · %s",
			[T.t("Kurzfassung") if laenge == "kurz" else T.t("ganze Geschichte"), maxi(0, k) + 1, nm[clampi(k, 0, 5)], _min(_t_spiel)]) \
			+ ("  ·  " + T.t("Pause") if pausiert else "")
	var bare: bool = main.padview != null and main.now() - float(main.padview.bare_t) < 3.0
	var want := laeuft and not bare and (pausiert or _jetzt() - _maus_t < 4.0)
	if _bar.visible != want:
		_bar.visible = want


func _end_card() -> void:
	if _layer == null:
		return
	if _ende != null and is_instance_valid(_ende):
		_ende.queue_free()
	_ende = PanelContainer.new()
	_ende.add_theme_stylebox_override("panel", UI.box(Color(UI.BG, 0.95), UI.ACC, 16, 18, 2))
	_ende.set_anchors_preset(Control.PRESET_CENTER)
	_ende.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_ende.grow_vertical = Control.GROW_DIRECTION_BOTH
	_layer.get_child(0).add_child(_ende)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	v.custom_minimum_size = Vector2(520, 0)
	_ende.add_child(v)
	var h := Label.new()
	h.text = T.t("Ende der Vorführung") if ergebnis == "fertig" else T.t("Vorführung beendet")
	h.add_theme_font_size_override("font_size", 22)
	v.add_child(h)
	var l := Label.new()
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.text = ergebnis_text()
	v.add_child(l)
	var b := Button.new()
	b.text = T.t("Schliessen")
	UI.primary(b)
	b.pressed.connect(func():
		if _ende != null and is_instance_valid(_ende):
			_ende.queue_free()
			_ende = null)
	v.add_child(b)
	var e := _ende
	get_tree().create_timer(25.0, true, false, true).timeout.connect(func():
		if is_instance_valid(e):
			e.queue_free())


func ergebnis_text() -> String:
	var g := 0
	var s := 0
	var f := 0
	var o := 0
	for r in _regionen:
		g += int(_regionen[r]["gespielt"])
		s += int(_regionen[r]["schnitt"])
		f += int(_regionen[r]["erzwungen"])
		o += int(_regionen[r]["offen"])
	var t := T.t("Dauer: %s · Jahreszeiten geschafft: %d von 4 · Finale: %s", [_min(_jetzt() - _t0), (story.S.get("done", []) as Array).size() if story.demo else _done_n,
			T.t("ja") if _finale_ok else T.t("nein")])
	t += "\n" + T.t("Stationen: %d gespielt, %d im Schnitt, %d erzwungen, %d offen", [g, s, f, o])
	t += "\n" + (T.t("Der Autopilot kam überall weiter.") if blockaden.is_empty() else T.t("BLOCKIERT: %d Mal – siehe Protokoll.", [blockaden.size()]))
	return t


var _done_n := 0
var _finale_ok := false


func _zusammenfassung() -> void:
	_done_n = (story.S.get("done", []) as Array).size()
	_finale_ok = bool(story.S.get("finale", false)) or _abspann


# =======================================================================================================================
# protocol and info
# =======================================================================================================================
static func _min(s: float) -> String:
	return "%d:%02d" % [int(s / 60.0), int(s) % 60]


func _log(text: String) -> void:
	var line := "[%s] %s" % [_min(_t_spiel), text]
	_zeilen.append(line)
	if _zeilen.size() > 600:
		_zeilen = _zeilen.slice(-500)
	print("[Vorführung] " + line)


func _schreiben() -> void:
	DirAccess.make_dir_recursive_absolute(PROTOKOLL.get_base_dir())
	var f := FileAccess.open(PROTOKOLL, FileAccess.WRITE)
	if f == null:
		return
	f.store_string("Vorführung «Maggie und der Bergkristall» – %s – %s\n" % [laenge, Time.get_datetime_string_from_system(false, true)])
	f.store_string("\n".join(_zeilen) + "\n")
	if not blockaden.is_empty():
		f.store_string("\nBLOCKIERT:\n")
		for b in blockaden:
			f.store_string("  %s  %s: %s\n" % [b["t"], b["wo"], b["was"]])


func info() -> Dictionary:
	var k := kapitel_jetzt()
	var out := {"ok": true, "laeuft": laeuft, "laenge": laenge, "pause": pausiert, "ergebnis": ergebnis, "kapitel": k,
			"kapitel_name": kapitel_namen()[clampi(k, 0, 5)] if k >= 0 else "", "kapitel_namen": kapitel_namen(),
			"phase": str(story.phase) if story != null else "", "region": str(story.region) if story != null else "",
			"autopilot": str(_ap.get("art", "")), "zeit": _min(_jetzt() - _t0) if laeuft or ergebnis != "" else "", "spielzeit": _min(_t_spiel),
			"tempo": tempo, "stimme": stimme, "knoepfe": knoepfe, "stimme_moeglich": Stimme.moeglich(), "regionen": _regionen, "blockiert": blockaden.size(),
			"blockaden": blockaden, "fehler": _fehler.keys(), "protokoll": _zeilen.slice(-14), "lite": _lite(),
			"datei": ProjectSettings.globalize_path(PROTOKOLL)}
	if story != null and story.running and story.demo:
		out["fertig_regionen"] = story.S.get("done", [])
		var tasks := []
		for id in story._task_order:
			tasks.append([str(id), bool(story._tasks[id]["done"])])
		out["aufgaben"] = tasks
		out["ziel"] = story._goal_info()
	elif ergebnis != "":
		out["fertig_regionen_n"] = _done_n
		out["finale"] = _finale_ok
		out["text"] = ergebnis_text()
	return out
