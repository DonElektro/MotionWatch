extends Node
## Spieltest-Assistent (Daniel 31.10.2026, Paket «Spieltest-Assistent»): beobachtet die Spielmodi, notiert, was passiert, und
## macht daraus Vorschläge (feste, verständliche Regeln) – im Fenster «Mehr → Entwickler → Spieltest» (devtool_spieltest.gd).
##   * Ein / aus nur im Entwickler-Fenster (nur der Besitzer, devtool.is_owner) oder Entwickler → «Spieltest-Assistent».
##     Er läuft, bis er ausgeschaltet wird – auch über Neustarts (user://spieltest/einstellung.json). Solange er läuft, steht
##     unten links ein kleines gezeichnetes Notizblock-Symbol (Klick = Fenster öffnen).
##   * Beobachtet (ohne Änderungen in den Spielen, nur Lesen 1 × pro Sekunde):
##       abenteuer    Bergtal-Abenteuer (bergtal_abenteuer.gd R / step / pending, A1–A5 über das Tagebuch R.log, A3-Tipps)
##       spielbereich Spielbereich (Haken in spielbereich.start_adventure, Entdeckungen aus entdecken.found)
##       horror       Horror «Das Hospiz» (NUR wenn schon entsperrt: running / phase / chapter; Tipp / falscher Code über den
##                    Haken in horror_raetsel.gd) – nie Passwort, Hash oder Datei des Horror-Modus
##       ferienpark   Ferienpark-Aufgaben (Knoten «fp_aufgaben»: what / last)
##       erlebniswelt Erlebniswelt im Ferienpark (Besuch der Szene, Entdeckungen «see.…», Blinki-Hinweise)
##       spiel        Spiel (Wächter usw.) und Rangliste (game.gd round_state, erwischt, Ziel, Bestenliste)
##       maggie …     später «Maggie und der Bergkristall» – nur über den Haken unten
##   * HAKEN für neue Spiele (eine Zeile, kostet nichts, wenn der Assistent aus ist):
##       const Spieltest = preload("res://scripts/spieltest.gd")
##       Spieltest.ereignis("maggie", "start", {"einheit": "Kapitel 1", "plan_min": 15})
##       Spieltest.ereignis("maggie", "ort", {"name": "Region Winter"})       # Region / Ort für die folgenden Ereignisse
##       Spieltest.ereignis("maggie", "erwischt", {"von": "Wolf"})
##       Spieltest.ereignis("maggie", "tipp", {"raetsel": "Eisbrücke"})       # auch: hilfe, falsch, umweg, neustart, fortschritt
##       Spieltest.ereignis("maggie", "abschnitt", {"name": "Schritt 2"})     # Dauer pro Schritt
##       Spieltest.ereignis("maggie", "pos", {"x": 12.0, "z": -40.0})       # freiwillig: Position (Welt) für «im Kreis»
##       Spieltest.ereignis("maggie", "ende", {"ergebnis": "fertig"})       # fertig | abgebrochen | verloren
##   * Notiert pro Runde: Dauer (nur aktive Zeit – ohne Pause, ohne 3 Min. ohne Eingabe bei den Lauf-Modi), Dauer pro
##     Abschnitt, Tipps / Hilfe, falsche Antworten, Umwege, lange ohne Fortschritt, im Kreis, erwischt, Neustarts, Abbruch
##     (Spiel verlassen, Programm zu), Ruckeln (Bildrate unter FPS_MIN, mit Ort), am Ende «Wie hat es dir gefallen?».
##   * Ablage: user://spieltest/runden/<id>.json (eine Datei pro Runde). Keine Passwörter, keine Spielernamen, keine
##     Einstellungen, keine Pfade. Nur auf diesem PC; «ZIP für Claude» packt Rohdaten + Bericht (Markdown).
##   * Push aufs Handy: world_reply «spieltest» (schnittstelle.json) -> MoveEye Teil 635a schickt die kurze Meldung über
##     seine Push-Einstellung, nur wenn dort «Spieltest-Meldungen» an ist (Zustand «spieltest» kommt zurück).
## Lite: _lite() = Quality.lite() – nichts pro Bild: ein Timer 1 × pro Sekunde (Bildrate als Stichprobe), Position alle 2 s
## nur in den Lauf-Modi; in Lite Position alle 4 s und kein Kreis-Test.
## /control {"action": "dev", "do": "spieltest", "what": info | on (value) | summary | report | export | end | feedback
##   (smiley 1–3, text) | ereignis (modus, art, daten) | clear}

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Quality = preload("res://scripts/quality.gd")
const Dev = preload("res://scripts/devtool.gd")
const Scenes = preload("res://scripts/scenes.gd")
const Ar = preload("res://scripts/abenteuer_raetsel.gd")

const DIR := "user://spieltest"
const RUNDEN := "user://spieltest/runden"
const EXPORT_DIR := "user://spieltest/export"
const SETTINGS := "user://spieltest/einstellung.json"
const FPS_MIN := 20.0                    # Bilder/s: darunter zählt es als Ruckeln (normale PCs schaffen 30–60)
const STUCK_S := 300.0                   # Lauf-Modi: so lange (aktiv) nichts Neues gefunden = «lange ohne Fortschritt»
const ASK_STUCK_S := 120.0               # eine Frage / ein Rätsel so lange offen = «lange ohne Antwort»
const IDLE_S := 180.0                    # so lange keine Eingabe: die Zeit zählt nicht (Simulator offen gelassen)
const MAX_EV := 400                      # Ereignisse pro Runde (mehr wird nur gezählt)
const MAX_ROUNDS := 400                  # so viele Runden liest die Auswertung (die neuesten)
const MODI := {"abenteuer": "Bergtal-Abenteuer", "spielbereich": "Spielbereich", "horror": "Horror «Das Hospiz»",
		"ferienpark": "Ferienpark-Aufgaben", "erlebniswelt": "Erlebniswelt", "spiel": "Spiel (Wächter, Rangliste)",
		"maggie": "Maggie und der Bergkristall"}
const KURZ := {"abenteuer": "Abenteuer", "spielbereich": "Spielbereich", "horror": "Horror", "ferienpark": "Ferienpark",
		"erlebniswelt": "Erlebniswelt", "spiel": "Spiel", "maggie": "Maggie"}
const WALK := ["spielbereich", "erlebniswelt", "maggie"]     # Lauf-Modi: Feststecken / im Kreis aus der Position
# geplante Dauer (Minuten) - nur wo das Spiel selbst eine Zeit vorgibt (Quelle im Kommentar); sonst Vergleich mit den
# anderen Einheiten desselben Modus
const PLAN := {"ferienpark|Aufgabe: Verlorenes Kind": 5.0,          # ferienpark_leben.gd: «5 Minuten Zeit»
		"ferienpark|Aufgabe: Velo-Dieb": 5.0,                        # ferienpark_leben.gd: «5 Minuten Zeit»
		"ferienpark|Aufgabe: Zeltplatz nachts": 4.0,                 # ferienpark_leben.gd: «4 Min.»
		"horror|*": 6.0}                                             # bergtal_horror.gd NIGHT_SECS = 360 s pro Nacht
const GAME_MODES := {"mw": "Gegen MoveEye", "guard": "Wächter", "seek": "Verstecken", "free": "Zonen-Check", "jaeger": "Fehlalarm-Jäger",
		"camera": "Alle gegen die Kamera", "mwhand": "Team gegen MoveEye", "patrol": "Patrouille"}
const TASKS := {"kind": "Aufgabe: Verlorenes Kind", "velo": "Aufgabe: Velo-Dieb", "zelt": "Aufgabe: Zeltplatz nachts"}
const SMILEY := {1: "🙁", 2: "😐", 3: "😀"}
const SMILEY_WORD := {1: "nicht so", 2: "geht so", 3: "super"}

static var inst = null                   # the running assistant (for the hook ereignis())

var main
var on := false
var seit := ""
var rounds := {}                         # modus -> the running round (Dictionary)
var _last_end := {}                      # modus -> {einheit, ergebnis, t} (for «Neustart»)
var push_log: Array = []                 # [{id, t, text, status}] the last messages (newest last)
var _timer: Timer
var _tick_n := 0
var _last_input := 0.0
var _places := {}                        # world -> [[name, x, z]]
# what the polls saw last time
var _ab := {"id": "", "done": false, "key": "", "key_t": 0.0, "tips": {}, "detour": {}, "wrong": 0, "log": 0, "fest": {}, "step": -1}
var _hz := {"run": false, "ch": 0, "done": false, "rk": "", "rk_t": 0.0, "fest": {}}
var _fp := {"what": ""}
var _gm := {"rs": "lobby", "caught": 0, "goal": 0}
var _scene := ""
var _scene_n := 0
var _hint := ""
var ui                                   # devtool_spieltest.gd (the tab in the window) - set by it
var _layer: CanvasLayer
var _icon: Control
var _fb: PanelContainer = null
var _fb_queue: Array = []                # ended rounds waiting for «Wie hat es dir gefallen?»
var _fb_round := {}
var _fb_text: LineEdit
var _fb_t := 0.0


static func _lite() -> bool:
	"""the central question «Lite?» (quality.gd, 3D-4.30)"""
	return Quality.lite()


static func ereignis(modus: String, art: String, daten := {}) -> void:
	"""THE hook for the games (see the head of the file) - nothing happens while the assistant is off"""
	if inst != null and is_instance_valid(inst) and inst.on:
		inst.ext(modus, art, daten)


# =============================================================================================================================
# on / off (saved, lives on over restarts)
# =============================================================================================================================
func _ready() -> void:
	name = "spieltest"
	inst = self
	_timer = Timer.new()
	_timer.wait_time = 1.0
	_timer.timeout.connect(_tick)
	add_child(_timer)
	var d = JSON.parse_string(FileAccess.get_file_as_string(SETTINGS)) if FileAccess.file_exists(SETTINGS) else null
	if d is Dictionary and bool(d.get("on", false)):
		seit = str(d.get("seit", ""))
		_recover()
		set_on(true, false)
	call_deferred("_late")


func _late() -> void:
	if main != null and main.entdecken != null and not main.entdecken.found.is_connected(_on_found):
		main.entdecken.found.connect(_on_found)


func set_on(v: bool, save := true) -> void:
	if v == on:
		_paint_icon()
		return
	if not v:
		for m in rounds.keys():
			_end(str(m), "aus")
	on = v
	if v and (seit == "" or save):
		seit = Time.get_datetime_string_from_system(false, true)
	if v:
		_reset_polls()
		_timer.start()
	else:
		_timer.stop()
	if save:
		DirAccess.make_dir_recursive_absolute(DIR)
		var f := FileAccess.open(SETTINGS, FileAccess.WRITE)
		if f != null:
			f.store_string(JSON.stringify({"on": on, "seit": seit}))
			f.close()
	_paint_icon()
	if ui != null:
		ui.paint()


func _reset_polls() -> void:
	"""what runs when the assistant is switched on is the starting point (a running adventure is taken from here on)"""
	_ab = {"id": "", "done": false, "key": "", "key_t": 0.0, "tips": {}, "detour": {}, "wrong": 0, "log": 0, "fest": {}, "step": -1}
	_hz = {"run": false, "ch": 0, "done": false, "rk": "", "rk_t": 0.0, "fest": {}}
	_fp = {"what": ""}
	_gm = {"rs": "lobby", "caught": 0, "goal": 0}
	_scene = ""
	_scene_n = 0
	_hint = ""
	_last_input = _now()


func _recover() -> void:
	"""a round that was still running when the program stopped (crash, power off): «Programm zu»"""
	var d := DirAccess.open(RUNDEN)
	if d == null:
		return
	for f in d.get_files():
		if not f.ends_with(".json"):
			continue
		var r = JSON.parse_string(FileAccess.get_file_as_string(RUNDEN + "/" + f))
		if r is Dictionary and bool(r.get("laeuft", false)):
			r["laeuft"] = false
			r["ergebnis"] = "programm_zu"
			r["ende"] = str(r.get("zuletzt", r.get("start", "")))
			_ev(r, "programm_zu", {"wie": "unerwartet (beim nächsten Start bemerkt)"})
			_write(r)


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		_close_all()


func _exit_tree() -> void:
	_close_all()


func _close_all() -> void:
	if not on:
		return
	for m in rounds.keys():
		_end(str(m), "programm_zu")


func _input(ev: InputEvent) -> void:
	if on and (ev is InputEventKey or ev is InputEventMouseButton or ev is InputEventJoypadButton or ev is InputEventScreenTouch
			or (ev is InputEventMouseMotion and (ev as InputEventMouseMotion).relative.length() > 2.0)):
		_last_input = _now()


static func _now() -> float:
	return Time.get_unix_time_from_system()


# =============================================================================================================================
# rounds
# =============================================================================================================================
func _start(modus: String, einheit: String, extra := {}) -> Dictionary:
	if rounds.has(modus):
		_end(modus, "abgebrochen")
	var t := _now()
	var id := "%s_%s_%03d" % [Time.get_datetime_string_from_system().replace(":", "").replace("-", "").replace("T", "_"), modus, randi() % 1000]
	var r := {"v": 1, "id": id, "modus": modus, "name": str(MODI.get(modus, modus)), "einheit": einheit,
			"kurz": str(extra.get("kurz", einheit)), "titel": str(extra.get("titel", "")),
			"start": Time.get_datetime_string_from_system(false, true), "t0": int(t), "zuletzt": "", "ende": "", "ergebnis": "",
			"laeuft": true, "aktiv_s": 0.0, "pause_s": 0.0, "szene": str(main.scene) if main != null else "",
			"version": str(main.VERSION) if main != null else "", "lite": _lite(), "plan_min": float(extra.get("plan_min", _plan(modus, einheit))),
			"meta": extra.get("meta", {}), "abschnitte": [], "ort": "", "zaehler": {"tipp": 0, "hilfe": 0, "falsch": 0, "umweg": 0,
				"erwischt": 0, "neustart": 0, "kreis": 0, "fest": 0, "fortschritt": 0}, "raetsel": {}, "orte_erwischt": {},
			"ruckeln": {}, "fps": {"n": 0, "sum": 0.0, "min": 999.0}, "ereignisse": [], "ev_mehr": 0, "bewertung": null,
			"_pos": [], "_last_prog": t, "_kreis_t": 0.0, "_fest_on": false, "_w": 0.0}
	var le: Dictionary = _last_end.get(modus, {})
	if not le.is_empty() and str(le.get("einheit", "")) == einheit and str(le.get("ergebnis", "")) != "fertig" and t - float(le.get("t", 0.0)) < 900.0:
		r["zaehler"]["neustart"] = 1
		_ev(r, "neustart", {"vorher": str(le.get("ergebnis", ""))})
	rounds[modus] = r
	_ev(r, "start", {"einheit": einheit})
	_write(r)
	if ui != null:
		ui.paint()
	return r


static func _plan(modus: String, einheit: String) -> float:
	return float(PLAN.get(modus + "|" + einheit, PLAN.get(modus + "|*", 0.0)))


func _end(modus: String, ergebnis: String) -> void:
	if not rounds.has(modus):
		return
	var r: Dictionary = rounds[modus]
	rounds.erase(modus)
	r["laeuft"] = false
	r["ergebnis"] = ergebnis
	r["ende"] = Time.get_datetime_string_from_system(false, true)
	r["aktiv_s"] = snappedf(float(r["aktiv_s"]), 1.0)
	r["pause_s"] = snappedf(float(r["pause_s"]), 1.0)
	_ev(r, "ende", {"ergebnis": ergebnis})
	_last_end[modus] = {"einheit": r["einheit"], "ergebnis": ergebnis, "t": _now()}
	var short_visit: bool = modus == "erlebniswelt" and float(r["aktiv_s"]) < 60.0 and int(r["zaehler"]["fortschritt"]) == 0
	if short_visit:                                  # just passing through the park: not a round
		_delete(r)
		return
	_write(r)
	if ergebnis in ["programm_zu", "aus"]:
		return
	_fb_queue.append(r)
	if _fb == null or not _fb.visible:
		_next_feedback()
	if ui != null:
		ui.paint()


func _ev(r: Dictionary, art: String, daten := {}) -> void:
	var ev: Array = r["ereignisse"]
	if ev.size() >= MAX_EV:
		r["ev_mehr"] = int(r["ev_mehr"]) + 1
		return
	var e := {"t": snappedf(float(r.get("aktiv_s", 0.0)), 1.0), "art": art}
	if str(r.get("ort", "")) != "" and not daten.has("ort"):
		e["ort"] = r["ort"]
	for k in daten:
		var v = daten[k]
		e[str(k)] = str(v).left(120) if v is String else v
	ev.append(e)


func _count(r: Dictionary, art: String, daten := {}) -> void:
	"""one observation: counter + event (+ per puzzle / per place)"""
	var z: Dictionary = r["zaehler"]
	if z.has(art):
		z[art] = int(z[art]) + 1
	var key := str(daten.get("raetsel", ""))
	if key != "" and art in ["tipp", "hilfe", "falsch", "fest"]:
		var rz: Dictionary = r["raetsel"]
		if not rz.has(key):
			rz[key] = {"tipp": false, "falsch": 0, "fest": false}
		match art:
			"tipp", "hilfe":
				rz[key]["tipp"] = true
			"falsch":
				rz[key]["falsch"] = int(rz[key]["falsch"]) + 1
			"fest":
				rz[key]["fest"] = true
	if art == "erwischt":
		var o := str(daten.get("ort", r.get("ort", "")))
		if o == "":
			o = Scenes.name_of(str(r.get("szene", "")))
		r["orte_erwischt"][o] = int(r["orte_erwischt"].get(o, 0)) + 1
	if art == "fortschritt":
		r["_last_prog"] = _now()
		r["_w"] = 0.0
		r["_fest_on"] = false
	_ev(r, art, daten)


func _section(r: Dictionary, nm: String) -> void:
	var a: Array = r["abschnitte"]
	if not a.is_empty() and str(a[-1]["name"]) == nm:
		return
	a.append({"name": nm, "s": 0.0})
	_ev(r, "abschnitt", {"name": nm})


func _write(r: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(RUNDEN)
	r["zuletzt"] = Time.get_datetime_string_from_system(false, true)
	var out := {}
	for k in r:
		if not str(k).begins_with("_"):
			out[k] = r[k]
	var f := FileAccess.open("%s/%s.json" % [RUNDEN, r["id"]], FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(out, " "))
		f.close()


func _delete(r: Dictionary) -> void:
	var p := "%s/%s.json" % [RUNDEN, r["id"]]
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)


func ext(modus: String, art: String, daten := {}) -> void:
	"""the hook (Spieltest.ereignis): a game reports itself"""
	modus = modus.strip_edges().to_lower().left(30)
	if modus == "":
		return
	match art:
		"start":
			var e := str(daten.get("einheit", "Runde"))
			_start(modus, e, {"kurz": str(daten.get("kurz", e)), "titel": str(daten.get("titel", "")), "plan_min": float(daten.get("plan_min", _plan(modus, e))),
					"meta": {"id": str(daten.get("id", ""))}})
			if daten.has("szene"):
				rounds[modus]["szene"] = str(daten["szene"])
				if modus == "spielbereich" and str(daten["szene"]) == "ferienpark" and rounds.has("erlebniswelt"):
					_end("erlebniswelt", "verlassen")
				rounds[modus]["meta"]["test"] = _devtest()
			return
		"ende":
			_end(modus, str(daten.get("ergebnis", "fertig")))
			return
	if not rounds.has(modus):
		return
	var r: Dictionary = rounds[modus]
	match art:
		"ort":
			r["ort"] = str(daten.get("name", "")).left(60)
		"abschnitt":
			_section(r, str(daten.get("name", "")).left(60))
		"pos":
			_pos_add(r, Vector2(float(daten.get("x", 0.0)), float(daten.get("z", 0.0))))
		_:
			_count(r, art, daten)


# =============================================================================================================================
# the tick (1 × per second): the polls of the modes, the active time, the frame rate
# =============================================================================================================================
func _tick() -> void:
	if not on or main == null:
		return
	_tick_n += 1
	_poll_abenteuer()
	_poll_horror()
	_poll_ferienpark()
	_poll_spiel()
	_poll_walk()
	var t := _now()
	var idle: bool = t - _last_input > IDLE_S
	var fps := Engine.get_frames_per_second()
	var fps_ok: bool = DisplayServer.window_is_focused() and not idle and (Engine.max_fps <= 0 or Engine.max_fps >= FPS_MIN + 5.0) \
			and DisplayServer.get_name() != "headless"
	for m in rounds:
		var r: Dictionary = rounds[m]
		var paused: bool = (str(m) in WALK and idle) or (str(m) == "horror" and main.horror != null and bool(main.horror.paused)) \
				or (str(m) == "erlebniswelt" and rounds.has("ferienpark"))
		if paused:
			r["pause_s"] = float(r["pause_s"]) + 1.0
			continue
		r["aktiv_s"] = float(r["aktiv_s"]) + 1.0
		var a: Array = r["abschnitte"]
		if not a.is_empty():
			a[-1]["s"] = float(a[-1]["s"]) + 1.0
		if fps_ok:
			var fp: Dictionary = r["fps"]
			fp["n"] = int(fp["n"]) + 1
			fp["sum"] = float(fp["sum"]) + fps
			fp["min"] = minf(float(fp["min"]), fps)
			if fps < FPS_MIN:
				var o := _ort_now(r)
				var rk: Dictionary = r["ruckeln"]
				if not rk.has(o):
					rk[o] = {"s": 0, "min": 999.0}
					_ev(r, "ruckeln", {"ort": o, "fps": int(fps)})
				rk[o]["s"] = int(rk[o]["s"]) + 1
				rk[o]["min"] = minf(float(rk[o]["min"]), fps)
		if str(m) in WALK:
			r["_w"] = float(r["_w"]) + 1.0
			if float(r["_w"]) >= STUCK_S and not bool(r["_fest_on"]):
				r["_fest_on"] = true
				_count(r, "fest", {"ort": _ort_now(r), "s": int(STUCK_S)})
		if _tick_n % 60 == 0:
			_write(r)                            # a checkpoint (a crash later shows «Programm zu»)
	_paint_icon()


# ---- Bergtal-Abenteuer (bergtal_abenteuer.gd + A1–A5) ---------------------------------------------------------------------
func _poll_abenteuer() -> void:
	var ab = main.abenteuer
	if ab == null:
		return
	var R: Dictionary = ab.R
	var rid := str(R.get("id", "")) if not R.is_empty() else ""
	if rid != str(_ab["id"]):
		if str(_ab["id"]) != "" and rounds.has("abenteuer") and not bool(_ab["done"]):
			_end("abenteuer", "abgebrochen")
		_ab = {"id": rid, "done": false, "key": "", "key_t": 0.0, "tips": {}, "detour": {}, "wrong": 0, "log": 0, "fest": {}, "step": -1}
		if rid != "":
			var ch := int(R.get("chapter", 1))
			var tit := ""
			if ch >= 1 and ch <= ab.D.CHAPTERS.size():
				tit = str(ab.D.CHAPTERS[ch - 1].get("title", ""))
			_start("abenteuer", "Kapitel %d" % ch, {"kurz": "Kap. %d" % ch, "titel": tit, "meta": {"stimmung": str(R.get("mood", "")),
					"stufe": str(R.get("level", "")), "ziel": str(R.get("goal", "")), "jahreszeit": str(R.get("season", "")),
					"hilfe": str(ab.hilfe_stufe()) if ab.has_method("hilfe_stufe") else "", "seed": int(R.get("seed", 0)), "test": _devtest()}})
			_ab["log"] = (R.get("log", []) as Array).size()
	if rid == "" or not rounds.has("abenteuer"):
		return
	var r: Dictionary = rounds["abenteuer"]
	if int(ab.step) != int(_ab["step"]):
		_ab["step"] = int(ab.step)
		if int(ab.step) >= 0 and int(ab.step) < ab.STEPS.size():
			_section(r, str(ab.STEPS[int(ab.step)]))
	var si := int(R.get("stage", 0))
	var stages: Array = ab.chapter().get("stages", []) if ab.has_method("chapter") else []
	if si >= 0 and si < stages.size():
		var snm := str(stages[si].get("name", ""))
		r["ort"] = snm if snm != "" else "Abschnitt %d" % (si + 1)
	# the questions / puzzles of the run: tip seen, detour, long open, wrong answers
	var pe: Dictionary = R.get("pending", {})
	var key := ""
	if not pe.is_empty():
		key = "%s · %s" % [r["kurz"], str(pe.get("title", pe.get("kind", "")))]
	var a3: Dictionary = R.get("a3", {})
	var wrong := int(a3.get("wrong", 0)) + int(R.get("reads_wrong", 0))
	if wrong > int(_ab["wrong"]):
		for i in range(wrong - int(_ab["wrong"])):
			_count(r, "falsch", {"raetsel": str(_ab["key"]) if str(_ab["key"]) != "" else key})
	_ab["wrong"] = wrong
	if key != str(_ab["key"]):
		if key != "" and str(_ab["key"]) != "":
			_count(r, "fortschritt", {"was": "Frage beantwortet"})
		_ab["key"] = key
		_ab["key_t"] = float(r["aktiv_s"])
	if key != "":
		var tip := str(a3.get("tip", ""))
		var hs := str(ab.hilfe_stufe()) if ab.has_method("hilfe_stufe") else "normal"
		if tip != "" and hs != "schwer" and _now() - float(a3.get("ask_t", _now())) >= Ar.TIP_S and not _ab["tips"].has(key):
			_ab["tips"][key] = true
			_count(r, "tipp", {"raetsel": key, "stufe": hs})
		if bool(pe.get("detour", false)) and not _ab["detour"].has(key):
			_ab["detour"][key] = true
			_count(r, "umweg", {"raetsel": key})
		if float(r["aktiv_s"]) - float(_ab["key_t"]) >= ASK_STUCK_S and not _ab["fest"].has(key):
			_ab["fest"][key] = true
			_count(r, "fest", {"raetsel": key, "s": int(ASK_STUCK_S)})
	# A1–A5 (MoveEye am Lager, Figuren, Rätsel, Rucksack, zu zweit): every new diary entry is an event
	var lg: Array = R.get("log", [])
	for i in range(int(_ab["log"]), lg.size()):
		var e = lg[i]
		if e is Dictionary:
			_ev(r, "tagebuch", {"k": str(e.get("k", "")), "titel": str(e.get("title", "")).left(60)})
	_ab["log"] = lg.size()
	if int(ab.step) == 7 and not bool(_ab["done"]):               # «Morgen»: the chapter is done
		_ab["done"] = true
		r["meta"]["sterne"] = int(R.get("result", {}).get("stars", -1)) if R.get("result", {}) is Dictionary else -1
		r["meta"]["angekommen"] = bool(R.get("arrived", false))
		_end("abenteuer", "fertig")


# ---- Horror «Das Hospiz» (only when it is unlocked - never the password) ----------------------------------------------------
func _poll_horror() -> void:
	var h = main.horror
	if h == null or not bool(h.unlocked):
		if rounds.has("horror"):
			_end("horror", "abgebrochen")
		return
	var run: bool = bool(h.running) and int(h.chapter) > 0
	var ch := int(h.chapter)
	if run and (not bool(_hz["run"]) or ch != int(_hz["ch"])):
		if rounds.has("horror") and not bool(_hz["done"]):
			_end("horror", "abgebrochen")
		_hz = {"run": true, "ch": ch, "done": false, "rk": "", "rk_t": 0.0, "fest": {}}
		_start("horror", "Nacht %d" % ch, {"kurz": "Nacht %d" % ch, "meta": {"schreck": snappedf(float(h.strength), 0.05), "test": _devtest()}})
	_hz["run"] = run
	if not rounds.has("horror"):
		return
	var r: Dictionary = rounds["horror"]
	var ph := str(h.phase)
	if ph != "":
		_section(r, {"intro": "Einleitung", "night": "Nacht", "morning": "Morgen", "ending": "Ende", "clips": "Aufnahmen"}.get(ph, ph))
	var rk := ""
	if h.raetsel != null:
		rk = str(h.raetsel.active)
	var key := ("%s · Rätsel %s" % [r["kurz"], rk]) if rk != "" else ""
	if key != str(_hz["rk"]):
		if str(_hz["rk"]) != "":
			_count(r, "fortschritt", {"was": "Rätsel weiter"})
		_hz["rk"] = key
		_hz["rk_t"] = float(r["aktiv_s"])
	elif key != "" and float(r["aktiv_s"]) - float(_hz["rk_t"]) >= ASK_STUCK_S and not _hz["fest"].has(key):
		_hz["fest"][key] = true
		_count(r, "fest", {"raetsel": key, "s": int(ASK_STUCK_S)})
	if ph in ["morning", "ending"] and not bool(_hz["done"]):
		_hz["done"] = true
		_end("horror", "fertig")
	elif not run and not bool(_hz["done"]):
		_end("horror", "abgebrochen")


func raetsel_key_horror() -> String:
	"""the key of the horror riddle on the screen (for the hook in horror_raetsel.gd)"""
	if not rounds.has("horror") or main.horror == null or main.horror.raetsel == null:
		return ""
	return "%s · Rätsel %s" % [rounds["horror"]["kurz"], str(main.horror.raetsel.active)]


# ---- Ferienpark-Aufgaben (ferienpark_leben.gd, node «fp_aufgaben») ----------------------------------------------------------
func _poll_ferienpark() -> void:
	var n = main.get_node_or_null("fp_aufgaben")
	if n == null:
		return
	var w := str(n.what)
	if w != str(_fp["what"]):
		if str(_fp["what"]) != "" and rounds.has("ferienpark"):
			var last: Dictionary = n.last if n.last is Dictionary else {}
			var st := str(last.get("state", ""))
			rounds["ferienpark"]["meta"]["ergebnis_spiel"] = st
			rounds["ferienpark"]["meta"]["moveeye"] = bool(last.get("moveeye", false))
			_end("ferienpark", "abgebrochen" if st in ["abgebrochen", "error", ""] else "fertig")
		if w != "":
			var nm := str(TASKS.get(w, w))
			_start("ferienpark", nm, {"kurz": nm.trim_prefix("Aufgabe: ")})
		_fp["what"] = w
	if w != "" and rounds.has("ferienpark"):
		_section(rounds["ferienpark"], str(n.st))


# ---- Spiel (game.gd: Wächter und die anderen Spielarten, Rangliste) --------------------------------------------------------
func _poll_spiel() -> void:
	var g = main.game
	if g == null:
		return
	var rs := str(g.round_state)
	var play: bool = rs in ["countdown", "play"]
	if play and not rounds.has("spiel"):
		var gm := str(main.game_mode)
		var e := "%s · %s" % [str(GAME_MODES.get(gm, gm)), Scenes.name_of(str(main.scene))]
		var runners := 0
		for p in g.players:
			if p != null and str(p.get("role", "")) == "runner":
				runners += 1
		_start("spiel", e, {"kurz": str(GAME_MODES.get(gm, gm)), "meta": {"spielart": gm, "spieler": g.count(), "laeufer": runners,
				"minuten": float(main.game_minutes) if main.get("game_minutes") != null else 0.0}})
		_gm = {"rs": rs, "caught": _sum(g, "caught"), "goal": _goals(g)}
	if rounds.has("spiel"):
		var r: Dictionary = rounds["spiel"]
		_section(r, {"countdown": "Countdown", "play": "Runde"}.get(rs, rs))
		var c := _sum(g, "caught")
		if c > int(_gm["caught"]):
			for i in range(c - int(_gm["caught"])):
				_count(r, "erwischt", {"ort": Scenes.name_of(str(main.scene))})
		_gm["caught"] = c
		var gl := _goals(g)
		if gl > int(_gm["goal"]):
			for i in range(gl - int(_gm["goal"])):
				_count(r, "fortschritt", {"was": "Ziel erreicht"})
		_gm["goal"] = gl
		if not play:
			var res: Array = g.results
			var best := 0
			for x in res:
				best = maxi(best, int(x.get("score", 0)))
			r["meta"]["ergebnisse"] = res.size()
			r["meta"]["beste_punkte"] = best
			r["meta"]["rangliste"] = (g.board as Dictionary).size()     # only how many entries - no names
			_ev(r, "rangliste", {"eintraege": (g.board as Dictionary).size()})
			_end("spiel", "fertig" if not res.is_empty() else "abgebrochen")
	_gm["rs"] = rs


static func _sum(g, k: String) -> int:
	var n := 0
	for p in g.players:
		if p != null:
			n += int(p.get(k, 0))
	return n


static func _goals(g) -> int:
	var n := 0
	for p in g.players:
		if p != null and str(p.get("state", "")) == "goal":
			n += 1
	return n


# ---- the walking modes: Spielbereich (started by its hook) and Erlebniswelt (the park) ---------------------------------------
func _poll_walk() -> void:
	var sc := str(main.scene)
	if sc != _scene:
		_scene_n += 1
		if _scene_n >= 2:                         # the same scene for 2 s (set_scene may take a moment)
			if rounds.has("spielbereich") and str(rounds["spielbereich"]["szene"]) != sc:
				var r: Dictionary = rounds["spielbereich"]
				var ent = main.entdecken
				var half: bool = ent != null and int(ent.total(str(r["szene"]))) > 0 and int(ent.count(str(r["szene"]))) * 2 >= int(ent.total(str(r["szene"])))
				r["meta"]["gefunden"] = int(ent.count(str(r["szene"]))) if ent != null else 0
				r["meta"]["total"] = int(ent.total(str(r["szene"]))) if ent != null else 0
				_end("spielbereich", "fertig" if half else "verlassen")
			if rounds.has("erlebniswelt") and sc != "ferienpark":
				_end("erlebniswelt", "verlassen")
			_scene = sc
			_scene_n = 0
	else:
		_scene_n = 0
	var ew = main.scenes.data.get("erleben", null) if main.scenes != null else null
	var in_park: bool = sc == "ferienpark" and ew != null and is_instance_valid(ew)
	if in_park and not rounds.has("erlebniswelt") and not (rounds.has("spielbereich") and str(rounds["spielbereich"]["szene"]) == "ferienpark"):
		_start("erlebniswelt", "Ferienpark am See", {"kurz": "Ferienpark"})
	# the Blinki hint of the discovery book = a tip
	var ent2 = main.entdecken
	var hid := str(ent2.hint_id) if ent2 != null else ""
	if hid != _hint and hid != "":
		for m in ["spielbereich", "erlebniswelt"]:
			if rounds.has(m):
				_count(rounds[m], "tipp", {"raetsel": "Entdecken · Blinki-Hinweis", "ziel": hid})
	_hint = hid
	# where the view is (every 2 s, Lite: 4 s) - for «im Kreis» and the place of the events
	var every := 4 if _lite() else 2
	if _tick_n % every == 0:
		for m in ["spielbereich", "erlebniswelt"]:
			if rounds.has(m) and main.view_cam != null and main.mehr != null and main.mehr.dev != null:
				var w = main.mehr.dev.to_world(main.view_cam.global_position)
				if w != null:
					_pos_add(rounds[m], w)


func _on_found(id: String) -> void:
	if not on:
		return
	for m in ["spielbereich", "erlebniswelt"]:
		if rounds.has(m):
			if m == "erlebniswelt" and not id.begins_with("see."):
				continue
			_count(rounds[m], "fortschritt", {"was": "entdeckt", "id": id})


func _pos_add(r: Dictionary, w: Vector2) -> void:
	"""a position (world coordinates): the last minute - a long way, but never far from the middle = «im Kreis»"""
	var P: Array = r["_pos"]
	P.append(w)
	var keep := 30 if not _lite() else 15
	while P.size() > keep:
		P.pop_front()
	r["_wpos"] = w
	if _lite() or P.size() < keep or _now() - float(r["_kreis_t"]) < 90.0:
		return
	var path := 0.0
	var c := Vector2.ZERO
	for i in range(P.size()):
		c += P[i]
		if i > 0:
			path += (P[i] as Vector2).distance_to(P[i - 1])
	c /= float(P.size())
	var rmax := 0.0
	for p in P:
		rmax = maxf(rmax, (p as Vector2).distance_to(c))
	if path >= 60.0 and rmax <= 12.0 and _now() - float(r["_last_prog"]) > 60.0:
		r["_kreis_t"] = _now()
		_count(r, "kreis", {"ort": _nearest(_world(), c), "weg_m": int(path), "radius_m": int(rmax)})


func _world() -> String:
	return str(main.mehr.dev.loaded_world()) if main.mehr != null and main.mehr.dev != null else str(main.scene)


func _nearest(world: String, p: Vector2) -> String:
	if not _places.has(world):
		var L := []
		for e in Dev.alle_orte(main):
			if str(e["world"]) == world and str(e["kind"]) != "szene":
				L.append([str(e["name"]), float(e["x"]), float(e["z"])])
		_places[world] = L
	var best := ""
	var bd := 150.0
	for e in _places[world]:
		var d := p.distance_to(Vector2(float(e[1]), float(e[2])))
		if d < bd:
			bd = d
			best = str(e[0])
	return best if best != "" else Scenes.name_of(str(main.scene))


func _ort_now(r: Dictionary) -> String:
	if str(r.get("ort", "")) != "":
		return str(r["ort"])
	if r.has("_wpos"):
		return _nearest(_world(), r["_wpos"])
	return Scenes.name_of(str(main.scene))


# =============================================================================================================================
# «Wie hat es dir gefallen?» - after every round, 3 drawn smileys + free text, can be skipped
# =============================================================================================================================
func _next_feedback() -> void:
	while not _fb_queue.is_empty():
		var r: Dictionary = _fb_queue.pop_front()
		if DisplayServer.get_name() == "headless" or main == null or main.get("ui_root") == null:
			_finish_feedback(r, 0, "")
			continue
		_fb_round = r
		_show_fb(r)
		return


func _show_fb(r: Dictionary) -> void:
	if _fb == null:
		_build_fb()
	_fb_text.text = ""
	(_fb.get_meta("sub") as Label).text = T.t("%s · %s – %d Min.") % [T.t(str(r["name"])), T.t(str(r["einheit"])), int(round(float(r["aktiv_s"]) / 60.0))]
	_fb.visible = true
	_fb_t = 90.0
	_place_fb()
	set_process(true)


func _build_fb() -> void:
	_ensure_layer()
	_fb = PanelContainer.new()
	_fb.theme = main.ui_root.theme if main.ui_root != null else UI.theme()
	_fb.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.97), UI.ACC, 14, 14, 2))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	_fb.add_child(v)
	var h := Label.new()
	h.text = T.t("Wie hat es dir gefallen?")
	h.add_theme_font_size_override("font_size", 20)
	h.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(h)
	var sub := UI.small("", UI.MUT)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(sub)
	_fb.set_meta("sub", sub)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 18)
	v.add_child(row)
	for s in [3, 2, 1]:
		var b := Button.new()
		b.custom_minimum_size = Vector2(84, 96)
		b.focus_mode = Control.FOCUS_NONE
		b.tooltip_text = T.t(str(SMILEY_WORD[s]))
		var face := Smiley.new()
		face.mood = s
		face.mouse_filter = Control.MOUSE_FILTER_IGNORE
		face.set_anchors_preset(Control.PRESET_FULL_RECT)
		b.add_child(face)
		var sv: int = s
		b.pressed.connect(func(): _answer(sv))
		row.add_child(b)
	var wl := HBoxContainer.new()
	wl.alignment = BoxContainer.ALIGNMENT_CENTER
	wl.add_theme_constant_override("separation", 18)
	v.add_child(wl)
	for s in [3, 2, 1]:
		var l := UI.small(T.t(str(SMILEY_WORD[s])), UI.TXT)
		l.custom_minimum_size = Vector2(84, 0)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		wl.add_child(l)
	_fb_text = LineEdit.new()
	_fb_text.placeholder_text = T.t("Möchtest du noch etwas sagen? (freiwillig)")
	_fb_text.custom_minimum_size = Vector2(320, 34)
	_fb_text.max_length = 300
	v.add_child(_fb_text)
	var bot := HBoxContainer.new()
	bot.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(bot)
	var sk := Button.new()
	sk.text = T.t("Überspringen")
	sk.pressed.connect(func(): _answer(0))
	bot.add_child(sk)
	_fb.visible = false
	_layer.add_child(_fb)


func _place_fb() -> void:
	if _fb == null:
		return
	_fb.reset_size()
	var vs: Vector2 = main.get_viewport().get_visible_rect().size
	_fb.position = ((vs - _fb.size) * 0.5).floor()


func _process(dt: float) -> void:
	if _fb == null or not _fb.visible:
		set_process(false)
		return
	_fb_t -= dt
	if _fb_t <= 0.0:
		_answer(0)                                # nobody answered: skipped


func _answer(smiley: int) -> void:
	var r := _fb_round
	_fb_round = {}
	var txt := _fb_text.text.strip_edges() if _fb_text != null else ""
	if _fb != null:
		_fb.visible = false
	if not r.is_empty():
		_finish_feedback(r, smiley, txt)
	_next_feedback()


func _finish_feedback(r: Dictionary, smiley: int, txt: String) -> void:
	r["bewertung"] = {"smiley": smiley if smiley > 0 else null, "text": txt.left(300), "uebersprungen": smiley <= 0}
	_write(r)
	_push(r)
	if ui != null:
		ui.paint()


func feedback(smiley: int, txt := "") -> Dictionary:
	"""tests: answer the question on the screen (or the next one waiting)"""
	if _fb_round.is_empty() and not _fb_queue.is_empty():
		_fb_round = _fb_queue.pop_front()
	if _fb_round.is_empty():
		return {"ok": false, "error": "no question"}
	if _fb_text != null:
		_fb_text.text = txt
	else:
		var r := _fb_round
		_fb_round = {}
		_finish_feedback(r, smiley, txt)
		return {"ok": true}
	_answer(clampi(smiley, 0, 3))
	return {"ok": true}


func _ensure_layer() -> void:
	if _layer == null:
		_layer = CanvasLayer.new()
		_layer.layer = 72
		add_child(_layer)


class Smiley extends Control:
	var mood := 3                            # 3 good · 2 so-so · 1 not good

	func _draw() -> void:
		var c := size * 0.5
		var r := minf(size.x, size.y) * 0.36
		var col: Color = {3: Color("#3fcf6b"), 2: Color("#f5d04a"), 1: Color("#f59a4a")}.get(mood, Color.WHITE)
		draw_circle(c, r, Color(col, 0.22))
		draw_arc(c, r, 0.0, TAU, 40, col, 3.0, true)
		var e := r * 0.38
		draw_circle(c + Vector2(-e, -e * 0.7), r * 0.1, col)
		draw_circle(c + Vector2(e, -e * 0.7), r * 0.1, col)
		var m := c + Vector2(0, r * 0.32)
		match mood:
			3:
				draw_arc(c + Vector2(0, r * 0.05), r * 0.5, deg_to_rad(25), deg_to_rad(155), 16, col, 3.0, true)
			2:
				draw_line(m + Vector2(-r * 0.4, 0), m + Vector2(r * 0.4, 0), col, 3.0, true)
			_:
				draw_arc(c + Vector2(0, r * 0.75), r * 0.45, deg_to_rad(205), deg_to_rad(335), 16, col, 3.0, true)


# =============================================================================================================================
# the little notepad in the corner (while the assistant runs)
# =============================================================================================================================
class Notepad extends Control:
	var st

	func _draw() -> void:
		var w := size.x
		var h := size.y
		var paper := Color(0.92, 0.94, 0.97, 0.55)
		var ink := Color(0.25, 0.32, 0.42, 0.75)
		draw_rect(Rect2(w * 0.18, h * 0.14, w * 0.64, h * 0.76), paper, true)
		draw_rect(Rect2(w * 0.18, h * 0.14, w * 0.64, h * 0.76), ink, false, 1.0)
		for i in 3:
			draw_circle(Vector2(w * (0.32 + 0.18 * i), h * 0.14), w * 0.05, ink)
		for i in 3:
			var y := h * (0.38 + 0.15 * i)
			draw_line(Vector2(w * 0.28, y), Vector2(w * (0.72 - 0.1 * float(i == 2)), y), ink, 1.2)
		if st != null and not (st.rounds as Dictionary).is_empty():
			draw_circle(Vector2(w * 0.82, h * 0.86), w * 0.09, Color(0.25, 0.81, 0.42, 0.85))   # a round is being noted

	func _gui_input(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT and st != null:
			st.open_window()
			accept_event()


func _paint_icon() -> void:
	if not on:
		if _icon != null:
			_icon.visible = false
		return
	if DisplayServer.get_name() == "headless":
		return
	if _icon == null:
		_ensure_layer()
		_icon = Notepad.new()
		_icon.st = self
		_icon.custom_minimum_size = Vector2(22, 22)
		_icon.size = Vector2(22, 22)
		_icon.mouse_filter = Control.MOUSE_FILTER_STOP
		_icon.tooltip_text = T.t("Spieltest-Assistent läuft (Mehr → Entwickler → Spieltest)")
		_layer.add_child(_icon)
	var vs: Vector2 = main.get_viewport().get_visible_rect().size
	_icon.position = Vector2(6.0, vs.y - 28.0)
	_icon.visible = true
	_icon.queue_redraw()
	if _fb != null and _fb.visible:
		_place_fb()
		set_process(true)


func open_window() -> void:
	if main.mehr != null and main.mehr.dev != null:
		main.mehr.dev.open()
		if main.mehr.dev.extra != null:
			main.mehr.dev.extra.show_tab("spieltest")


# =============================================================================================================================
# push to the phone through MoveEye (world_reply «spieltest», MoveEye 635a)
# =============================================================================================================================
func mw_connected() -> bool:
	return main != null and main.now() - float(main.mw_t) < 3.0


func mw_state() -> Dictionary:
	"""what MoveEye says about its switch «Spieltest-Meldungen» (state «spieltest»): {} = no MoveEye / an older one"""
	if not mw_connected():
		return {}
	var s = main.mw.get("spieltest", null)
	return s if s is Dictionary else {}


func push_text(r: Dictionary) -> String:
	var res: String = {"fertig": T.t("fertig"), "abgebrochen": T.t("abgebrochen"), "verlassen": T.t("verlassen"), "verloren": T.t("verloren")}.get(str(r["ergebnis"]), str(r["ergebnis"]))
	var z: Dictionary = r["zaehler"]
	var t := T.t("Spieltest: %s %s %s, %d Min., %d Tipps") % [T.t(str(KURZ.get(str(r["modus"]), r["name"]))), T.t(str(r["kurz"])), res,
			int(round(float(r["aktiv_s"]) / 60.0)), int(z["tipp"]) + int(z["hilfe"])]
	if int(z["erwischt"]) > 0:
		t += T.t(", %d× erwischt") % int(z["erwischt"])
	var b = r.get("bewertung", null)
	if b is Dictionary and b.get("smiley", null) != null:
		t += ", " + str(SMILEY.get(int(b["smiley"]), ""))
	return t


func _push(r: Dictionary) -> void:
	var id := int(_now() * 1000.0)
	if not push_log.is_empty():
		id = maxi(id, int(push_log[-1]["id"]) + 1)
	var st := "an MoveEye übergeben" if mw_connected() else "kein Push: MoveEye nicht verbunden"
	var it := {"id": id, "t": int(_now()), "text": push_text(r), "status": st, "mw": mw_connected()}
	push_log.append(it)
	while push_log.size() > 10:
		push_log.pop_front()
	r["push"] = {"text": it["text"], "status": st}
	_write(r)


func reply():
	"""world_reply «spieltest»: the messages of the last 10 min (MoveEye 635a pushes them once, only with its switch on)"""
	if push_log.is_empty():
		return null
	var t := _now()
	var out := []
	for it in push_log.slice(-6):
		if t - float(it["t"]) < 600.0:
			out.append({"id": it["id"], "t": it["t"], "text": it["text"]})
	return out if not out.is_empty() else null


func push_line() -> String:
	"""one line for the window: will there be a push?"""
	if not mw_connected():
		return T.t("Kein Push: MoveEye ist nicht verbunden (die Runden werden trotzdem notiert).")
	var s := mw_state()
	if s.is_empty():
		return T.t("Kein Push: dieses MoveEye kennt die Spieltest-Meldungen noch nicht (älter).")
	if not bool(s.get("on", false)):
		return T.t("Kein Push: in MoveEye ist «Spieltest-Meldungen» aus (Einstellungen → Entwickler).")
	var last := ""
	if not push_log.is_empty() and int(s.get("seen", 0)) >= int(push_log[-1]["id"]):
		last = " · " + T.t("letzte Meldung: %s") % _st_word(str(s.get("st", "")))
	return T.t("Push über MoveEye ist an.") + last


static func _st_word(st: String) -> String:
	return {"sent": T.t("gesendet"), "none": T.t("MoveEye hat keinen Push eingerichtet"), "error": T.t("Fehler beim Senden"),
			"off": T.t("Schalter aus"), "net": T.t("kein Netz")}.get(st, st)


func set_mw_push(v: bool) -> bool:
	"""the switch «Spieltest-Meldungen» of MoveEye from here (a request, MoveEye sets it - mw_cmd)"""
	if not mw_connected():
		main.start_info = T.t("MoveEye ist nicht verbunden – der Schalter «Spieltest-Meldungen» ist in MoveEye (Einstellungen → Entwickler).")
		return false
	main.mw_cmd = {"id": maxi(int(_now() * 1000.0), int(main.mw_cmd.get("id", 0)) + 1), "op": "spieltest_push", "on": v}
	return true


# =============================================================================================================================
# the evaluation: fixed, simple rules -> suggestions per mode (with the number of rounds as basis)
# =============================================================================================================================
func load_rounds() -> Array:
	var out := []
	var d := DirAccess.open(RUNDEN)
	if d == null:
		return out
	var files: Array = Array(d.get_files()).filter(func(f): return str(f).ends_with(".json"))
	files.sort()
	for f in files.slice(maxi(0, files.size() - MAX_ROUNDS)):
		var r = JSON.parse_string(FileAccess.get_file_as_string(RUNDEN + "/" + str(f)))
		if r is Dictionary and r.has("modus") and not bool(r.get("laeuft", false)):
			out.append(r)
	return out


static func _pct(a: int, b: int) -> String:
	return "%d von %d" % [a, b]


static func _min(s: float) -> String:
	return str(snappedf(s / 60.0, 0.1)).trim_suffix(".0")


func summary() -> Dictionary:
	"""{modi: [{modus, name, n, vorschlaege: [{text, n, stufe}], runden: [...]}], n, regeln}"""
	var all := load_rounds().filter(func(r): return str(r.get("ergebnis", "")) != "aus")
	var by := {}
	for r in all:
		var m := str(r["modus"])
		if not by.has(m):
			by[m] = []
		by[m].append(r)
	var out := []
	for m in by:
		var R: Array = by[m]
		out.append({"modus": m, "name": str(MODI.get(m, m)), "n": R.size(), "vorschlaege": _rules(str(m), R), "runden": R.slice(-8)})
	out.sort_custom(func(a, b): return int(a["n"]) > int(b["n"]))
	return {"ok": true, "n": all.size(), "modi": out}


func _rules(m: String, R: Array) -> Array:
	var V := []
	var units := {}
	for r in R:
		var u := str(r.get("einheit", ""))
		if not units.has(u):
			units[u] = []
		units[u].append(r)
	# 1. puzzles: tip, wrong answers, long open
	var pz := {}
	for r in R:
		for k in (r.get("raetsel", {}) as Dictionary):
			var x: Dictionary = r["raetsel"][k]
			if not pz.has(k):
				pz[k] = {"n": 0, "tipp": 0, "falsch": 0, "fest": 0}
			pz[k]["n"] += 1
			pz[k]["tipp"] += 1 if bool(x.get("tipp", false)) else 0
			pz[k]["falsch"] += int(x.get("falsch", 0))
			pz[k]["fest"] += 1 if bool(x.get("fest", false)) else 0
	for k in pz:
		var p: Dictionary = pz[k]
		var nu := _rounds_with(R, str(k))
		if int(p["tipp"]) >= 2 and float(p["tipp"]) / float(nu) >= 0.6:
			V.append(_v(T.t("Rätsel «%s»: %s Runden brauchten den Tipp → evtl. zu schwer") % [k, _pct(int(p["tipp"]), nu)], nu, 2))
		if float(p["falsch"]) / float(nu) >= 1.5 and int(p["falsch"]) >= 2:
			V.append(_v(T.t("Rätsel «%s»: im Schnitt %s falsche Antworten → Frage oder Hinweise klarer?") % [k, str(snappedf(float(p["falsch"]) / float(nu), 0.1))], nu, 2))
		if int(p["fest"]) >= 2:
			V.append(_v(T.t("Rätsel «%s»: %s Runden lange ohne Antwort → Hinweis früher zeigen?") % [k, _pct(int(p["fest"]), nu)], nu, 1))
	# 2. duration (only finished rounds): against the plan of the game, otherwise against the other units of the mode
	var avg := {}
	for u in units:
		var fin: Array = (units[u] as Array).filter(func(r): return str(r.get("ergebnis", "")) == "fertig")
		if not fin.is_empty():
			var s := 0.0
			for r in fin:
				s += float(r.get("aktiv_s", 0.0))
			avg[u] = [s / float(fin.size()), fin.size(), float(fin[0].get("plan_min", 0.0))]
	for u in avg:
		var a: float = avg[u][0]
		var nf: int = avg[u][1]
		var plan: float = avg[u][2] * 60.0
		if plan > 0.0:
			if a >= 1.5 * plan:
				V.append(_v(T.t("«%s» dauert im Schnitt %s× so lang wie geplant (Ø %s Min., geplant %s Min.)") % [u, str(snappedf(a / plan, 0.1)), _min(a), _min(plan)], nf, 1))
			elif a <= 0.5 * plan and nf >= 2:
				V.append(_v(T.t("«%s» geht viel schneller als geplant (Ø %s Min., geplant %s Min.) → evtl. zu leicht") % [u, _min(a), _min(plan)], nf, 1))
		else:
			var others := []
			for u2 in avg:
				if u2 != u:
					others.append(float(avg[u2][0]))
			if not others.is_empty():
				others.sort()
				var med: float = others[others.size() / 2]
				if med > 30.0 and a >= 2.0 * med:
					V.append(_v(T.t("«%s» dauert im Schnitt %s× so lang wie die anderen (Ø %s Min., andere %s Min.)") % [u, str(snappedf(a / med, 0.1)), _min(a), _min(med)], nf, 1))
	# 3. caught, per place / region
	var ca := {}
	var ca_n := {}
	for r in R:
		for o in (r.get("orte_erwischt", {}) as Dictionary):
			ca[o] = int(ca.get(o, 0)) + int(r["orte_erwischt"][o])
			ca_n[o] = int(ca_n.get(o, 0)) + 1
	for o in ca:
		if int(ca[o]) >= 5 or (int(ca_n[o]) >= 2 and float(ca[o]) / float(ca_n[o]) >= 3.0):
			V.append(_v(T.t("«%s»: %d× erwischt in %d Runden → Wächter oder Gegner zu schnell / zu streng?") % [o, int(ca[o]), int(ca_n[o])], int(ca_n[o]), 2))
	# 4. per unit: aborted, restarted, tips, detours, rating
	for u in units:
		var U: Array = units[u]
		var n := U.size()
		var ab := 0
		var prog := 0
		var where := {}
		var tips := 0
		var umw := 0
		var neu := 0
		var rate := []
		for r in U:
			var e := str(r.get("ergebnis", ""))
			var z: Dictionary = r.get("zaehler", {})
			if e == "programm_zu":
				prog += 1
			if e in ["abgebrochen", "programm_zu"] or (e == "verlassen" and m != "erlebniswelt"):
				ab += 1
				var a: Array = r.get("abschnitte", [])
				var w := str(r.get("ort", "")) if str(r.get("ort", "")) != "" else (str(a[-1]["name"]) if not a.is_empty() else "")
				if w != "":
					where[w] = int(where.get(w, 0)) + 1
			tips += int(z.get("tipp", 0)) + int(z.get("hilfe", 0))
			umw += int(z.get("umweg", 0))
			neu += int(z.get("neustart", 0))
			var b = r.get("bewertung", null)
			if b is Dictionary and b.get("smiley", null) != null:
				rate.append(int(b["smiley"]))
		if ab >= 2 and float(ab) / float(n) >= 0.5:
			var top := ""
			var tn := 0
			for w in where:
				if int(where[w]) > tn:
					tn = int(where[w])
					top = str(w)
			var txt := T.t("«%s»: %s Runden abgebrochen") % [u, _pct(ab, n)]
			if top != "":
				txt += T.t(", meist bei «%s»") % top
			if prog > 0:
				txt += T.t(" (%d× Programm zu)") % prog
			V.append(_v(txt + T.t(" → Anfang oder diese Stelle anschauen"), n, 2))
		if neu >= 2:
			V.append(_v(T.t("«%s»: %d× neu gestartet → Anfang zu schwer?") % [u, neu], n, 1))
		if n >= 2 and float(tips) / float(n) >= 3.0:
			V.append(_v(T.t("«%s»: im Schnitt %s Tipps pro Runde → evtl. zu schwer") % [u, str(snappedf(float(tips) / float(n), 0.1))], n, 1))
		if n >= 2 and float(umw) / float(n) >= 1.0:
			V.append(_v(T.t("«%s»: im Schnitt %s Umwege pro Runde → Hinweise klarer?") % [u, str(snappedf(float(umw) / float(n), 0.1))], n, 1))
		if rate.size() >= 2:
			var sad := rate.filter(func(x): return int(x) == 1).size()
			var good := rate.filter(func(x): return int(x) == 3).size()
			if float(sad) / float(rate.size()) >= 0.5:
				V.append(_v(T.t("«%s»: %s Bewertungen «nicht so» → anschauen, was nicht gefällt") % [u, _pct(sad, rate.size())], rate.size(), 2))
			elif good == rate.size() and rate.size() >= 3:
				V.append(_v(T.t("«%s» gefällt: %d× «super»") % [u, good], rate.size(), 0))
	# 5. places: long without progress, in circles, judder
	var fe := {}
	var kr := {}
	var ru := {}
	for r in R:
		var seen_f := {}
		var seen_k := {}
		for e in (r.get("ereignisse", []) as Array):
			var o := str(e.get("ort", ""))
			if o == "":
				continue
			if str(e.get("art", "")) == "fest" and str(e.get("raetsel", "")) == "":
				fe[o] = int(fe.get(o, 0)) + 1
				seen_f[o] = true
			elif str(e.get("art", "")) == "kreis":
				kr[o] = int(kr.get(o, 0)) + 1
				seen_k[o] = true
		for o in (r.get("ruckeln", {}) as Dictionary):
			if not ru.has(o):
				ru[o] = {"s": 0, "min": 999.0, "n": 0}
			ru[o]["s"] += int(r["ruckeln"][o].get("s", 0))
			ru[o]["min"] = minf(float(ru[o]["min"]), float(r["ruckeln"][o].get("min", 999.0)))
			ru[o]["n"] += 1
	for o in fe:
		if int(fe[o]) >= 2:
			V.append(_v(T.t("Bei «%s»: %d× lange nichts Neues gefunden → Hinweis früher oder Weg klarer?") % [o, int(fe[o])], R.size(), 1))
	for o in kr:
		if int(kr[o]) >= 2:
			V.append(_v(T.t("Bei «%s»: %d× im Kreis gegangen → Weg oder Ziel unklar?") % [o, int(kr[o])], R.size(), 1))
	for o in ru:
		if int(ru[o]["s"]) >= 5:
			V.append(_v(T.t("Ruckeln bei «%s»: %d s unter %d Bilder/s (tiefste %d, in %d Runden)") % [o, int(ru[o]["s"]), int(FPS_MIN), int(ru[o]["min"]), int(ru[o]["n"])], int(ru[o]["n"]), 2))
	V.sort_custom(func(a, b): return int(a["stufe"]) > int(b["stufe"]))
	return V


static func _rounds_with(R: Array, key: String) -> int:
	var n := 0
	for r in R:
		if (r.get("raetsel", {}) as Dictionary).has(key):
			n += 1
	return maxi(1, n)


static func _v(text: String, n: int, stufe: int) -> Dictionary:
	"""a suggestion: stufe 2 = probably a problem, 1 = look at it, 0 = good news"""
	return {"text": text + " " + (T.t("(Grundlage: %d Runde)") % n if n == 1 else T.t("(Grundlage: %d Runden)") % n), "n": n, "stufe": stufe}


# =============================================================================================================================
# the report (Markdown, German - for Claude) and «ZIP für Claude»
# =============================================================================================================================
const RULES_MD := """## Regeln (fest, damit die Vorschläge nachvollziehbar sind)
- **Tipp**: ein Rätsel / eine Frage braucht in ≥ 60 Prozent der Runden (mind. 2) den Tipp → «evtl. zu schwer».
- **Falsche Antworten**: im Schnitt ≥ 1.5 pro Runde → «Frage oder Hinweise klarer?».
- **Lange ohne Antwort**: Frage ≥ 2 Min. offen, in ≥ 2 Runden. **Lange nichts Neues** (Lauf-Modi): 5 Min. aktiv ohne Fund, ≥ 2× am gleichen Ort.
- **Im Kreis**: in einer Minute ≥ 60 m Weg, aber nie mehr als 12 m von der Mitte, ≥ 2× am gleichen Ort.
- **Dauer**: nur fertige Runden, aktive Zeit (ohne Pause, ohne 3 Min. ohne Eingabe). Gegen die geplante Zeit des Spiels (≥ 1.5× oder ≤ 0.5×), sonst gegen den Median der anderen Einheiten (≥ 2×).
- **Erwischt**: pro Ort / Region ≥ 5× gesamt oder ≥ 3× pro Runde.
- **Abbruch**: ≥ 50 Prozent der Runden einer Einheit (mind. 2) abgebrochen, Spiel verlassen oder Programm zu (Erlebniswelt: Verlassen ist normal).
- **Neustart**: dieselbe Einheit innert 15 Min. nach einem Abbruch wieder gestartet, ≥ 2×.
- **Tipps / Umwege pro Runde**: im Schnitt ≥ 3 Tipps bzw. ≥ 1 Umweg (mind. 2 Runden).
- **Ruckeln**: Bildrate (Stichprobe 1 × pro Sekunde, nur Fenster im Vordergrund) unter {FPS} Bilder/s, ≥ 5 s am gleichen Ort.
- **Bewertung**: ≥ 50 Prozent «nicht so» (mind. 2) bzw. alle «super» (mind. 3).
"""


func report_md() -> String:
	var S := summary()
	var md := "# Spieltest-Bericht MoveEye-Simulator\n\n"
	md += "Erstellt %s · Simulator %s%s · %d Runden · beobachtet seit %s\n\n" % [Time.get_datetime_string_from_system(false, true), str(main.VERSION) if main != null else "?",
			" · Lite" if _lite() else "", int(S["n"]), seit if seit != "" else "-"]
	md += "Nur dieser PC. Keine Passwörter, keine Spielernamen, keine Einstellungen. Zeiten = aktive Zeit.\n\n"
	for g in S["modi"]:
		md += "## %s (%d Runden)\n\n" % [g["name"], int(g["n"])]
		if (g["vorschlaege"] as Array).is_empty():
			md += "- Noch nichts Auffälliges.\n"
		for v in g["vorschlaege"]:
			md += "- %s%s\n" % [["", "", "**"][int(v["stufe"])], str(v["text"]) + ["", "", "**"][int(v["stufe"])]]
		md += "\n| Start | Einheit | Min. | Ergebnis | Tipps | Falsch | Umwege | Erwischt | Fest | Kreis | Ruckeln s | Bewertung |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n"
		for r in g["runden"]:
			var z: Dictionary = r.get("zaehler", {})
			var rs := 0
			for o in (r.get("ruckeln", {}) as Dictionary):
				rs += int(r["ruckeln"][o].get("s", 0))
			var b = r.get("bewertung", null)
			var bt := "-"
			if b is Dictionary:
				bt = (str(SMILEY.get(int(b["smiley"]), "")) if b.get("smiley", null) != null else "übersprungen") + ((" «%s»" % str(b.get("text", "")).replace("|", "/")) if str(b.get("text", "")) != "" else "")
			md += "| %s | %s | %s | %s | %d | %d | %d | %d | %d | %d | %d | %s |\n" % [str(r.get("start", "")).replace("T", " ").left(16), str(r.get("einheit", "")),
					_min(float(r.get("aktiv_s", 0.0))), str(r.get("ergebnis", "")), int(z.get("tipp", 0)) + int(z.get("hilfe", 0)), int(z.get("falsch", 0)),
					int(z.get("umweg", 0)), int(z.get("erwischt", 0)), int(z.get("fest", 0)), int(z.get("kreis", 0)), rs, bt]
		md += "\n"
	if (S["modi"] as Array).is_empty():
		md += "Noch keine Runden notiert.\n\n"
	md += RULES_MD.replace("{FPS}", str(int(FPS_MIN)))
	md += "\nRohdaten: `runden/<id>.json` (eine Datei pro Runde: zaehler, abschnitte mit Sekunden, raetsel, orte_erwischt, ruckeln, ereignisse mit t = aktive Sekunde).\n"
	return md


func export_zip() -> String:
	"""raw data + report as one ZIP (for the chat) - returns the user:// path or ''"""
	DirAccess.make_dir_recursive_absolute(EXPORT_DIR)
	var dt := Time.get_datetime_dict_from_system()
	var path := "%s/MoveEye_Spieltest_%04d-%02d-%02d_%02d%02d.zip" % [EXPORT_DIR, dt.year, dt.month, dt.day, dt.hour, dt.minute]
	var md := report_md()
	var f := FileAccess.open(DIR + "/bericht.md", FileAccess.WRITE)
	if f != null:
		f.store_string(md)
		f.close()
	var entries := [["bericht.md", md.to_utf8_buffer()],
			["LIESMICH.txt", ("Spieltest-Daten aus dem MoveEye-Simulator (Mehr → Entwickler → Spieltest).\nbericht.md = Zusammenfassung mit Vorschlägen, runden/ = Rohdaten (JSON pro Runde).\nVersion %s.\n" % str(main.VERSION)).to_utf8_buffer()]]
	var d := DirAccess.open(RUNDEN)
	if d != null:
		for fn in d.get_files():
			if fn.ends_with(".json"):
				entries.append(["runden/" + fn, FileAccess.get_file_as_bytes(RUNDEN + "/" + fn)])
	return path if preload("res://scripts/devtool_notizen.gd").pack_zip(path, entries) else ""


func clear_all() -> int:
	"""delete every saved round (the setting on / off stays)"""
	var n := 0
	var d := DirAccess.open(RUNDEN)
	if d != null:
		for fn in d.get_files():
			if fn.ends_with(".json") and DirAccess.remove_absolute(RUNDEN + "/" + fn) == OK:
				n += 1
	for m in rounds:
		_write(rounds[m])
	return n


# =============================================================================================================================
# the simulator settings (group «Entwickler», like MoveEye) and /control
# =============================================================================================================================
static func add_controls(m) -> void:
	"""main._register_controls: the two switches in the group «Entwickler» (MoveEye has «Spieltest-Meldungen» in its group
	«Entwickler» too - the same switch: the simulator only asks MoveEye to set it)"""
	m.add_control("toggle", "spieltest_on", "Spieltest-Assistent: beobachtet die Spiele und macht Vorschläge (Mehr → Entwickler → Spieltest)",
			func(): return m.spieltest != null and m.spieltest.on, func(v): _ctl(m, "on", bool(v)), "Entwickler", {"expert": true})
	m.add_control("toggle", "spieltest_push", "Spieltest-Meldungen aufs Handy (Schalter in MoveEye, über dessen Push)",
			func(): return m.spieltest != null and bool(m.spieltest.mw_state().get("on", false)), func(v): _ctl(m, "push", bool(v)), "Entwickler", {"expert": true})
	m.controls[-1]["ro"] = func(): return m.spieltest == null or not m.spieltest.mw_connected()


static func _ctl(m, what: String, v: bool) -> void:
	if m.spieltest == null:
		return
	if what == "on":
		m.spieltest.set_on(v)
	else:
		m.spieltest.set_mw_push(v)


func _devtest() -> bool:
	"""a test progress of «Kapitel-Sprung» (devtool_kapitel.gd) is running - noted in the round"""
	var dv = main.mehr.dev if main.mehr != null else null
	return dv != null and dv.extra != null and dv.extra.kapitel != null and bool(dv.extra.kapitel.test_on)


func info() -> Dictionary:
	var run := []
	for k in rounds:
		var r: Dictionary = rounds[k]
		run.append({"modus": k, "einheit": r["einheit"], "aktiv_s": r["aktiv_s"], "zaehler": r["zaehler"], "abschnitt": (r["abschnitte"] as Array).back() if not (r["abschnitte"] as Array).is_empty() else {},
				"ort": r["ort"], "id": r["id"]})
	return {"ok": true, "on": on, "seit": seit, "laufend": run, "warten": _fb_queue.size() + (0 if _fb_round.is_empty() else 1),
			"frage": _fb != null and _fb.visible, "push": push_log.slice(-3), "push_line": push_line(), "mw": mw_state(), "lite": _lite(),
			"dir": ProjectSettings.globalize_path(DIR)}


func control(d: Dictionary) -> Dictionary:
	match str(d.get("what", "info")):
		"on":
			set_on(str(d.get("value", "true")) in ["true", "1", "on"])
		"summary":
			return summary()
		"report":
			return {"ok": true, "md": report_md()}
		"export":
			var p := export_zip()
			return {"ok": p != "", "path": ProjectSettings.globalize_path(p) if p != "" else ""}
		"end":
			var m := str(d.get("modus", ""))
			for k in rounds.keys():
				if m == "" or k == m:
					_end(str(k), str(d.get("ergebnis", "abgebrochen")))
		"feedback":
			return feedback(int(d.get("smiley", 0)), str(d.get("text", "")))
		"ereignis":
			if on:
				ext(str(d.get("modus", "")), str(d.get("art", "")), d.get("daten", {}) if d.get("daten", {}) is Dictionary else {})
		"clear":
			return {"ok": true, "deleted": clear_all()}
		"mw_push":
			return {"ok": set_mw_push(str(d.get("value", "true")) in ["true", "1", "on"])}
	return info()
