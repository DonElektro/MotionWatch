extends Node
## Spielton (Besitzer 01.11.2026, Paket «Ton in den Spielen»): echte Geräusche, kurze Musik-Momente, Spannung, Überraschung,
## leise Begleitmusik und Menü-Klicks – NUR in Spielen und Geschichten (Maggie, Grossvater, Spielrunden, Entdecken im
## Ferienpark / Bergtal / …, Fenster «Spielen»). Überwachung, Testläufe, Prüfstand, MoveEye-Aufgaben bleiben wie bisher.
##   * Ein Knoten unter main («klang», main.klang). Aufrufe von überall: const Klang = preload("res://scripts/klang.gd")
##       Klang.fund()      Glockenspiel              Klang.raetsel()   kleine Fanfare        Klang.kapitel()  Streicher
##       Klang.tusch()     Trommelwirbel + Tusch (geheime Funde: Steinmännchen, SEELI-Abzeichen); Klang.tusch(true) auch
##                         ausserhalb einer Geschichte (Easter Egg beim freien Wandern), nie bei Tests
##       Klang.erwischt()  Paukenschlag              Klang.gefahr(quelle, stufe 0…1, dauer s)   Puls / Trommelwirbel
##       Klang.donner(m)   Donner (Abstand in m)     Klang.ereignis(modus, art, daten)   (Haken in spieltest.gd)
##     Alles prüft selbst, ob gerade ein Spiel läuft (kontext() != ""); sonst passiert nichts. Rückgabe true = gespielt.
##   * Wann ist «Spiel»? kontext(): «maggie» (maggie.running), «grossvater» (bergtal_abenteuer R läuft), «horror»
##     (nur Umgebung und Klicks), «spiel» (game.gd Runde), «erleben» (über «Spielen → Entdecken» in eine Szene gereist, bis
##     zum nächsten Szenenwechsel; Ferienpark-Aufgaben), «menue» (Fenster «Spielen» / Geschichten-Start: nur Klicks).
##     Immer still (""), wenn: Testlauf, Prüfstand, Nacht-Testlauf (ausser der Nacht im Grossvater-Abenteuer),
##     Trainingsbilder, Blinde Flecken, Fehlalarm nachstellen, Parcours, Einbruch-Ablauf, Wiedergabe, Trailer, Vorführung,
##     «allein»-Szenen (Prüfstand), eine Aufgabe von MoveEye (main._mw_task).
##   * Busse: «Musik», «Effekte», «Umgebung», «UI» (je ein Regler, Licht & Ton → Spiel-Ton), alle → Master; auf dem
##     Master ein Begrenzer (−1 dBFS, keine Übersteuerung). «Ton am PC» (mikrofon.pc_on, Zweig real-schalter: ein Schalter)
##     schaltet alle vier stumm. Einstellungen: user://spielton.json.
##   * Dateien: res://klang/sp_<name>.ogg (werkzeuge/spielton_bauen.py, Pegel in klang/spielton.json) und die Trailer-
##     Aufnahmen res://klang/<name>.ogg (donner, regen, wind, wasser, pauke; Pegel klang/klaenge.json). Fehlt eine Datei,
##     gilt der alte, erzeugte Klang (trailer_ton.gd get_snd) bzw. bleibt es bei der bisherigen Synthese (mikrofon.gd,
##     maggie_story.gd, maggie_gefahr.gd) – nichts Altes wurde entfernt.
##   * Begleitmusik: je Jahreszeit (Maggie: die Region, Grossvater: die gewählte Jahreszeit, sonst das Datum), Ferienpark
##     eigenes Stück (am See). Sanft ein (4 s) und aus (2.5 s), bei Spannung und während eines Musik-Moments leiser.
##   * Umgebung im Spiel: Wind / Regen / Bach als echte Aufnahmen statt der Synthese (mikrofon.gd fragt echt()), Donner zum
##     Blitz (main.lightning_strike), Feuer knistert an jeder Feuerstelle in der Nähe (Lichter in main.lamps mit Feuerfarbe),
##     Schritte der Spielfigur (Maggie, Spieler 2) auf Gras, Kies oder Schnee (wie anim_spuren.gd).
## Steuerbefehl: {"action": "spielton", "do": "info" | "test" (art) | "erleben" (id)} (main.gd → control()).

const Ton = preload("res://scripts/trailer_ton.gd")
const ORDNER := "res://klang/"
const FILE := "user://spielton.json"
const BUSSE := ["Musik", "Effekte", "Umgebung", "UI"]
const LIMIT_DB := -1.0
const STILL := ["Testlauf", "Prüfstand", "Trainingsbilder", "Blinde Flecken", "Fehlalarm nachstellen", "Verfolgungs-Parcours",
		"Einbruch-Ablauf", "Wiedergabe", "Trailer"]
const JZ := ["fruehling", "sommer", "herbst", "winter"]
# without the new file: the old (generated or recorded) sound of the trailers (trailer_ton.gd get_snd)
const ERSATZ := {"fund": "chime", "fanfare": "chime", "kapitel": "pad_hell", "tusch": "boom", "wirbel": "pulse", "puls": "pulse",
		"musik_fruehling": "pad_hell", "musik_sommer": "pad_hell", "musik_herbst": "pad_ruhig", "musik_winter": "pad_ruhig",
		"musik_see": "pad_hell"}
const PRIO := {"fund": 1, "raetsel": 2, "kapitel": 3, "tusch": 4}
const MOMENT_DB := {"fund": -4.0, "fanfare": -5.0, "kapitel": -4.0, "tusch": -3.0, "pauke": -4.0}
const MUSIK_DB := -4.0                 # the loops are quiet already (−26 LUFS); with the bus at 35 % about −39 LUFS
const ECHT := {"wind": "wind", "rain": "regen", "water": "wasser"}   # mikrofon.gd kinds -> recordings of klang/
const ECHT_DB := -6.0

static var inst = null

var main
var musik_an := true
var vol := {"Musik": 35.0, "Effekte": 70.0, "Umgebung": 65.0, "UI": 45.0}
var kontext := ""
var log_: Array = []                   # the last triggers [t, art] (tests, info)
var _k_t := 0.0
var _info = null
var _info_alt = null
var _cache := {}
var _erleben := ""
var _mus: Array = []                   # two players for the cross fade
var _mus_nm := ["", ""]
var _mus_g := [0.0, 0.0]
var _mus_ziel := [0.0, 0.0]
var _mus_i := 0
var _duck_bis := 0.0
var _spannung := 0.0
var _gefahr := {}                      # quelle -> [stufe, bis]
var _sp := {}                          # "puls" / "wirbel" -> AudioStreamPlayer
var _moment_t := -10.0
var _moment_p := 0
var _fx: Array = []                    # one-shot players (Effekte)
var _ui: AudioStreamPlayer
var _step: Array = []                  # [player, stop at]
var _step_n := {}
var _feuer := {}                       # light id -> AudioStreamPlayer3D
var _feuer_t := 0.0
var _gv_step_t := 0.0
var _t := 0.0
var _dirty := false


# =============================================================================================================================
# static API (from every script; nothing happens outside a game)
# =============================================================================================================================
static func _ok() -> bool:
	return inst != null and is_instance_valid(inst)


static func fund(geheim := false) -> bool:
	return _ok() and (inst._tusch() if geheim else inst._moment("fund"))


static func raetsel() -> bool:
	return _ok() and inst._moment("fanfare", "raetsel")


static func kapitel() -> bool:
	return _ok() and inst._moment("kapitel")


static func tusch(auch_frei := false) -> bool:
	"""Überraschung: Trommelwirbel und Tusch (Easter Egg, geheime Funde). auch_frei = true: auch ausserhalb einer Geschichte
	(z. B. das Easter Egg beim freien Wandern), nur nie bei Tests / MoveEye-Aufgaben"""
	return _ok() and inst._tusch(auch_frei)


static func erwischt() -> bool:
	return _ok() and inst._erwischt()


static func gefahr(quelle: String, stufe: float, dauer := 3.0) -> void:
	if _ok():
		inst._gefahr[quelle] = [clampf(stufe, 0.0, 1.0), inst._t + maxf(0.1, dauer)]


static func donner(dist: float) -> bool:
	return _ok() and inst._donner(dist)


static func ereignis(modus: String, art: String, daten := {}) -> void:
	"""the hook of spieltest.gd (one line in every game): the music moments follow the events of the games"""
	if not _ok():
		return
	match art:
		"erwischt":
			inst._erwischt()
		"fortschritt":
			if (daten as Dictionary).has("raetsel"):
				inst._moment("fanfare", "raetsel")
			elif str((daten as Dictionary).get("zwei", "")) == "fund":
				inst._moment("fund")                            # zwei_bausteine.gd: a find of the team
		"ende":
			if str((daten as Dictionary).get("ergebnis", "")) == "fertig":
				inst._moment("kapitel")


static func ersetze(kind: String) -> bool:
	"""the old generated sounds of the stories (maggie_story._play, maggie_gefahr._ui_play): true = the real one plays (or
	just played), the caller stays quiet; false = the old sound as before"""
	if not _ok():
		return false
	match kind:
		"chime", "pickup":
			return inst._moment("fund")
		"fanfare":
			return inst._moment("kapitel")
	return false


static func echt(main_, kind: String) -> Array:
	"""mikrofon.gd: [stream, dB offset, bus] of the real recording while a game runs ([] = keep the synthesis)"""
	if not _ok() or inst.kontext in ["", "menue"]:
		return []
	if not ECHT.has(kind):
		return [null, 0.0, "Umgebung"]                   # animals: the same sound, only on the bus «Umgebung»
	var e: Array = inst._stream(str(ECHT[kind]), false)
	if e.is_empty():
		return [null, 0.0, "Umgebung"]
	return [e[0], float(e[1]) + ECHT_DB, "Umgebung"]


static func erleben(id: String) -> void:
	"""spielbereich.start_adventure: travelled to a place by «Spielen → Entdecken» - a game until the next change of scene"""
	if _ok():
		inst._erleben = id


# =============================================================================================================================
# start, settings, buses
# =============================================================================================================================
func _ready() -> void:
	name = "klang"
	inst = self
	_laden()
	busse()
	_ui = AudioStreamPlayer.new()
	_ui.bus = "UI"
	add_child(_ui)
	for i in range(2):
		var p := AudioStreamPlayer.new()
		p.bus = "Musik"
		add_child(p)
		_mus.append(p)
	for i in range(2):
		var s := AudioStreamPlayer.new()
		s.bus = "Umgebung"
		add_child(s)
		_step.append([s, 0.0])
	get_tree().node_added.connect(_knoten)
	call_deferred("_spaet")


func _exit_tree() -> void:
	if inst == self:
		inst = null


func _spaet() -> void:
	if main != null and main.get("entdecken") != null and main.entdecken.has_signal("found"):
		if not main.entdecken.found.is_connected(_gefunden):
			main.entdecken.found.connect(_gefunden)


func _gefunden(_a = null, _b = null, _c = null) -> void:
	"""entdecken.found: a find - a little later, so a «Tusch» of the same find (secret badge, Easter Egg) wins"""
	var t0 := _t
	get_tree().create_timer(0.25).timeout.connect(func():
		if not (_moment_p >= 4 and _moment_t >= t0 - 0.5):
			_moment("fund"))


func _laden() -> void:
	if not FileAccess.file_exists(FILE):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
	if d is Dictionary:
		musik_an = bool(d.get("musik", musik_an))
		var v = d.get("vol", {})
		if v is Dictionary:
			for b in BUSSE:
				if v.has(b):
					vol[b] = clampf(float(v[b]), 0.0, 100.0)


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"musik": musik_an, "vol": vol}))


func busse() -> void:
	"""the four buses (→ Master) and the limiter on the Master bus (once)"""
	for b in BUSSE:
		if AudioServer.get_bus_index(b) < 0:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, b)
			AudioServer.set_bus_send(i, AudioServer.get_bus_name(0))
	var hat := false
	for e in range(AudioServer.get_bus_effect_count(0)):
		if AudioServer.get_bus_effect(0, e) is AudioEffectHardLimiter:
			hat = true
	if not hat:
		var lim := AudioEffectHardLimiter.new()
		lim.ceiling_db = LIMIT_DB
		lim.release = 0.1
		AudioServer.add_bus_effect(0, lim)
	_pegel()


func ton_am_pc() -> bool:
	"""the one switch «Ton am PC» (mikrofon.gd pc_on; real-schalter sets it together with the loudspeaker)"""
	var mk = main.get("mikro") if main != null else null
	return mk == null or bool(mk.get("pc_on"))


func _pegel() -> void:
	var an := ton_am_pc()
	for b in BUSSE:
		var i := AudioServer.get_bus_index(b)
		if i < 0:
			continue
		var v: float = float(vol[b])
		AudioServer.set_bus_volume_db(i, linear_to_db(maxf(0.0001, v / 100.0)))
		AudioServer.set_bus_mute(i, not an or v < 0.5 or (b == "Musik" and not musik_an))


func setze_vol(b: String, v: float) -> void:
	vol[b] = clampf(v, 0.0, 100.0)
	_pegel()
	save()


func add_controls() -> void:
	"""Licht & Ton → Spiel-Ton (main.GROUPS): music on / off and the four volumes"""
	var g := "Licht & Ton"
	var S := {"sub": "Spiel-Ton"}
	main.add_control("toggle", "st_musik", "Begleitmusik in Spielen und Geschichten (Tests und Überwachung bleiben still)",
			func(): return musik_an, func(v): musik_an = bool(v); _pegel(); save(), g, S)
	for e in [["st_vol_musik", "Musik", "Lautstärke Musik"], ["st_vol_eff", "Effekte", "Lautstärke Effekte (Fund, Fanfare, Spannung, Tusch)"],
			["st_vol_umg", "Umgebung", "Lautstärke Umgebung im Spiel (Wind, Regen, Bach, Feuer, Schritte, Tiere)"],
			["st_vol_ui", "UI", "Lautstärke Menü-Klicks"]]:
		var b: String = e[1]
		main.add_control("slider", e[0], e[2], func(): return vol[b], func(v): setze_vol(b, float(v)), g,
				{"sub": "Spiel-Ton", "min": 0, "max": 100, "step": 5, "unit": "%"})


# =============================================================================================================================
# when is it a game?
# =============================================================================================================================
func still() -> bool:
	"""tests, measurements, MoveEye's tasks: everything as before (no sound of this file)"""
	var m = main
	if m == null:
		return true
	if bool(Engine.get_meta("vorfuehrung", false)):          # (the spectator camera of a game round is part of the game)
		return true
	if bool(m.get("welt_solo")) or str(m.get("solo_scene")) != "":
		return true
	if m.has_method("measuring") and m.measuring():
		return true
	var b: String = m.busy_with() if m.has_method("busy_with") else ""
	if b in STILL or b.ends_with("(von MoveEye)"):
		return true
	if b == "Nacht-Testlauf" and not _grossvater():
		return true
	if m.has_method("_mw_task") and m._mw_task() != "":
		return true
	if m.get("pruef") != null and bool(m.pruef.get("running")):
		return true
	return false


func _grossvater() -> bool:
	var ab = main.get("abenteuer")
	return ab != null and ab.get("R") is Dictionary and not (ab.R as Dictionary).is_empty()


func kontext_neu() -> String:
	var m = main
	if m == null or still():
		return ""
	if m.get("maggie") != null and bool(m.maggie.get("running")):
		return "maggie"
	if m.get("horror") != null and bool(m.horror.get("running")):
		return "horror"
	if _grossvater():
		return "grossvater"
	if m.get("game") != null and str(m.game.get("round_state")) in ["countdown", "play"]:
		return "spiel"
	if preload("res://scripts/ferienpark_leben.gd").task_busy(m) != "":
		return "erleben"
	if _erleben != "":
		if str(m.scene) == _erleben or preload("res://scripts/worlds.gd").world_of(str(m.scene)) == _erleben:
			return "erleben"
		_erleben = ""                                     # another scene now: no longer the game
	if m.get("mehr") != null and str(m.mehr.get("win_id")) in ["spiel", "gstart"]:
		return "menue"
	return ""


func aktiv() -> bool:
	return kontext != "" and ton_am_pc()


func _spielt() -> bool:
	"""music moments, tension, steps, fire: a real game (not the menu, not the horror with its own sounds)"""
	return aktiv() and not kontext in ["menue", "horror"]


# =============================================================================================================================
# sounds: the new files, the trailer recordings, the old generated sounds
# =============================================================================================================================
func _json(p: String):
	if FileAccess.file_exists(p):
		var j = JSON.parse_string(FileAccess.get_file_as_string(p))
		if j is Dictionary:
			return j
	return {}


func _stream(nm: String, ersatz := true) -> Array:
	"""[stream, dB, loop] – klang/sp_<nm>.ogg, else klang/<nm>.ogg, else the old sound (trailer_ton.gd); [] = none"""
	if _cache.has(nm):
		return _cache[nm]
	if _info == null:
		_info = _json(ORDNER + "spielton.json")
		_info_alt = _json(ORDNER + "klaenge.json")
	var out := []
	for e in [["sp_" + nm, _info.get(nm, null)], [nm, _info_alt.get(nm, null)]]:
		var p: String = ORDNER + str(e[0]) + ".ogg"
		if out.is_empty() and FileAccess.file_exists(p):
			var o := AudioStreamOggVorbis.load_from_buffer(FileAccess.get_file_as_bytes(p))
			if o != null and o.get_length() > 0.0:
				var inf = e[1] if e[1] is Dictionary else {}
				o.loop = bool(inf.get("loop", false))
				out = [o, float(inf.get("db", 0.0)), o.loop]
	if out.is_empty() and ersatz:
		var alt := str(ERSATZ.get(nm, nm))
		var w = Ton.get_snd(alt)
		if w != null:
			var lp := nm.begins_with("musik_") or nm in ["wirbel", "puls"]
			if w is AudioStreamWAV and lp:
				var wv := (w as AudioStreamWAV).duplicate() as AudioStreamWAV
				wv.loop_mode = AudioStreamWAV.LOOP_FORWARD
				wv.loop_begin = 0
				wv.loop_end = wv.data.size() / (2 * (2 if wv.stereo else 1))
				w = wv
			elif w is AudioStreamOggVorbis and lp:
				w = (w as AudioStreamOggVorbis).duplicate()
				w.loop = true
			out = [w, -6.0, lp]
	_cache[nm] = out
	return out


func _merke(art: String) -> void:
	log_.append([snappedf(_t, 0.01), art])
	if log_.size() > 40:
		log_.pop_front()


func _eins(nm: String, db: float, bus := "Effekte", pitch := 1.0) -> AudioStreamPlayer:
	var e := _stream(nm)
	if e.is_empty():
		return null
	var p: AudioStreamPlayer = null
	for q in _fx:
		if not (q as AudioStreamPlayer).playing:
			p = q
			break
	if p == null:
		if _fx.size() >= 6:
			p = _fx[0]
		else:
			p = AudioStreamPlayer.new()
			add_child(p)
			_fx.append(p)
	p.bus = bus
	p.stream = e[0]
	p.volume_db = db + float(e[1])
	p.pitch_scale = pitch
	p.play()
	return p


func _moment(nm: String, art := "") -> bool:
	"""a music moment (fund / fanfare / kapitel): the most important one wins when two come at once"""
	if not _spielt():
		return false
	var a := art if art != "" else nm
	var pr: int = int(PRIO.get(a, 1))
	if _t - _moment_t < 1.8 and pr <= _moment_p:
		return true                                        # the same moment from a second hook: already playing
	var p := _eins(nm, float(MOMENT_DB.get(nm, -4.0)))
	if p == null:
		return false
	_moment_t = _t
	_moment_p = pr
	_duck_bis = _t + p.stream.get_length() * 0.8
	_merke(a)
	return true


func _tusch(frei := false) -> bool:
	if not (_spielt() or (frei and ton_am_pc() and not still())):
		return false
	if _t - _moment_t < 1.0 and _moment_p >= 4:
		return true
	var p := _eins("tusch", float(MOMENT_DB["tusch"]))
	if p == null:
		return false
	_moment_t = _t
	_moment_p = 4
	_duck_bis = _t + 3.5
	_merke("tusch")
	return true


func _erwischt() -> bool:
	if not _spielt():
		return false
	var p := _eins("pauke", float(MOMENT_DB["pauke"]))
	if p == null:
		return false
	_gefahr.clear()
	_spannung = 0.0                                       # the tension is over: the drum ends it
	_duck_bis = _t + 2.5
	_merke("erwischt")
	return true


func _donner(dist: float) -> bool:
	if not aktiv() or kontext == "menue":
		return false
	var d := clampf(dist, 300.0, 6000.0)
	var db := -2.0 - 14.0 * log(d / 800.0) / log(10.0)
	var p := _eins("donner", clampf(db, -26.0, 0.0), "Umgebung", clampf(1.05 - d / 20000.0, 0.8, 1.05))
	if p != null:
		_merke("donner")
	return p != null


# =============================================================================================================================
# every frame: context, music, tension, steps, fire
# =============================================================================================================================
func _process(dt: float) -> void:
	_t += dt
	_k_t -= dt
	if _k_t <= 0.0:
		_k_t = 0.25
		var k := kontext_neu()
		if k != kontext:
			kontext = k
			_merke("kontext:" + k)
		_pegel()
	_musik_tick(dt)
	_spannung_tick(dt)
	_schritte_tick()
	_feuer_t -= dt
	if _feuer_t <= 0.0:
		_feuer_t = 1.5
		_feuer_tick()


func jahreszeit() -> String:
	var jz = main.get("jahreszeiten") if main != null else null
	if jz != null and jz.has_method("season"):
		var s := str(jz.season())
		if s in JZ:
			return s
	return "sommer"


func musik_wahl() -> String:
	match kontext:
		"maggie":
			var r := str(main.maggie.get("region"))
			return "musik_" + (r if r in JZ else jahreszeit())
		"grossvater":
			var s := str((main.abenteuer.R as Dictionary).get("season", ""))
			return "musik_" + (s if s in JZ else jahreszeit())
		"erleben":
			if str(main.scene) == "ferienpark" or preload("res://scripts/worlds.gd").world_of(str(main.scene)) == "ferienpark":
				return "musik_see"
			return "musik_" + jahreszeit()
		"spiel":
			return "musik_" + jahreszeit()
	return ""


func _musik_tick(dt: float) -> void:
	var nm := musik_wahl() if (aktiv() and musik_an) else ""
	if nm != _mus_nm[_mus_i]:
		if _mus_nm[_mus_i] != "":
			_mus_ziel[_mus_i] = 0.0                        # the old one fades out
		if nm != "":
			var e := _stream(nm)
			if not e.is_empty():
				_mus_i = 1 - _mus_i
				var p: AudioStreamPlayer = _mus[_mus_i]
				p.stream = e[0]
				p.set_meta("db", float(e[1]))
				_mus_g[_mus_i] = 0.0
				p.volume_db = -80.0
				p.play(randf() * maxf(0.0, p.stream.get_length() - 1.0))
				_merke("musik:" + nm)
		_mus_nm[_mus_i] = nm
	var duck := 1.0 if _t > _duck_bis else 0.4
	var ziel := duck * (1.0 - 0.7 * _spannung)
	for i in range(2):
		var p: AudioStreamPlayer = _mus[i]
		var z: float = ziel if (i == _mus_i and _mus_nm[i] != "") else 0.0
		var rate := dt / (4.0 if z > _mus_g[i] else 2.5)   # in 4 s, out 2.5 s
		_mus_g[i] = move_toward(_mus_g[i], z, rate)
		if _mus_g[i] <= 0.001:
			if p.playing:
				p.stop()
			if i != _mus_i:
				_mus_nm[i] = ""
			continue
		p.volume_db = MUSIK_DB + float(p.get_meta("db", 0.0)) + linear_to_db(_mus_g[i])


func _spannung_tick(dt: float) -> void:
	var lv := 0.0
	if _spielt():
		if kontext == "maggie":
			var g = main.maggie.get_node_or_null("maggie_gefahr")
			if g != null and g.get("_grusel") != null:
				_gefahr["maggie"] = [float(g._grusel), _t + 0.6]
		for q in _gefahr.keys():
			var e: Array = _gefahr[q]
			if _t > float(e[1]):
				_gefahr.erase(q)
			else:
				lv = maxf(lv, float(e[0]))
	else:
		_gefahr.clear()
	_spannung = move_toward(_spannung, lv, dt * (0.8 if lv > _spannung else 0.3))
	for nm in ["puls", "wirbel"]:
		var g := clampf(_spannung * 2.2, 0.0, 1.0) if nm == "puls" else smoothstep(0.45, 1.0, _spannung)
		var p: AudioStreamPlayer = _sp.get(nm, null)
		if g <= 0.01:
			if p != null and p.playing:
				p.stop()
			continue
		if p == null:
			var e := _stream(nm)
			if e.is_empty():
				continue
			p = AudioStreamPlayer.new()
			p.bus = "Effekte"
			p.stream = e[0]
			p.set_meta("db", float(e[1]))
			add_child(p)
			_sp[nm] = p
		p.volume_db = -3.0 + float(p.get_meta("db", 0.0)) + linear_to_db(g)
		if not p.playing:
			p.play()
			_merke(nm)


func spannung() -> float:
	return _spannung


# ---- steps of the own figure ------------------------------------------------------------------------------------------------
func _figuren() -> Array:
	var out := []
	if kontext == "maggie" and main.maggie.has_method("spieler"):
		var f = main.maggie.spieler()
		if f != null:
			out.append(f)
		var z = main.maggie.get_node_or_null("maggie_zwei")
		if z != null and z.get("fig2") != null and is_instance_valid(z.fig2):
			out.append(z.fig2)
	return out


func boden(p: Vector3) -> String:
	"""gras | kies | schnee under a foot (like anim_spuren.gd: snow of the season / weather, the gravel paths)"""
	if kontext == "maggie" and str(main.maggie.get("region")) == "winter":
		return "schnee"
	var s = preload("res://scripts/anim_spuren.gd")._ich(main)
	if s != null:
		s._boden()
		if bool(s._schnee):
			return "schnee"
		if s._kies(p):
			return "kies"
	return "gras"


func _schritte_tick() -> void:
	for e in _step:
		if float(e[1]) > 0.0 and _t >= float(e[1]):
			(e[0] as AudioStreamPlayer).stop()
			e[1] = 0.0
	if not _spielt():
		return
	if kontext == "grossvater":
		_gv_schritte()
		return
	for f in _figuren():
		var spd := float(f.get("cur_speed"))
		var n := int(floor(float(f.get("phase")) / PI))
		var id: int = f.get_instance_id()
		if int(_step_n.get(id, n)) != n and spd > 0.25:
			_schritt(boden(f.global_position), spd)
		_step_n[id] = n


func _gv_schritte() -> void:
	"""the Grossvater tour has no figure: while a leg is being walked (nothing asked, not paused), steps in the rhythm"""
	var ab = main.abenteuer
	var R_: Dictionary = ab.R
	if int(ab.get("step")) != 4 or not bool(R_.get("walking", false)) or not (R_.get("pending", {}) as Dictionary).is_empty():
		return
	if _t >= _gv_step_t:
		_gv_step_t = _t + 0.55
		var sn := str(R_.get("season", "")) == "winter"
		_schritt("schnee" if sn else ("kies" if randf() < 0.6 else "gras"), 1.1)


func _schritt(art: String, spd: float) -> void:
	var e := _stream("schritt_" + art, false)
	if e.is_empty():
		return
	var slot: Array = _step[0] if not (_step[0][0] as AudioStreamPlayer).playing else _step[1]
	var p: AudioStreamPlayer = slot[0]
	p.stream = e[0]
	p.volume_db = float(e[1]) - 4.0 + clampf((spd - 1.2) * 4.0, -4.0, 4.0) + randf_range(-1.5, 0.5)
	p.pitch_scale = randf_range(0.93, 1.07)
	p.play(0.5 * (randi() % 4))
	slot[1] = _t + 0.46 / p.pitch_scale


# ---- fire places nearby: crackling -------------------------------------------------------------------------------------------
func _feuer_tick() -> void:
	var cam := get_viewport().get_camera_3d() if is_inside_tree() else null
	var want := {}
	if _spielt() and cam != null and main.get("lamps") is Array:
		var cp := cam.global_position
		var n := []
		for l in main.lamps:
			if l is OmniLight3D and is_instance_valid(l) and l.is_inside_tree() and l.visible and l.light_energy > 0.05 \
					and l.light_color.g < 0.6 and l.light_color.r > 0.8:
				var d: float = (l as Node3D).global_position.distance_to(cp)
				if d < 45.0:
					n.append([d, l])
		n.sort_custom(func(a, b): return a[0] < b[0])
		for i in range(mini(3, n.size())):
			want[(n[i][1] as Node).get_instance_id()] = n[i][1]
	for id in _feuer.keys():
		if not want.has(id) or not is_instance_valid(_feuer[id]):
			if is_instance_valid(_feuer[id]):
				(_feuer[id] as Node).queue_free()
			_feuer.erase(id)
	for id in want:
		if _feuer.has(id):
			continue
		var e := _stream("feuer", false)
		if e.is_empty():
			return
		var p := AudioStreamPlayer3D.new()
		p.bus = "Umgebung"
		p.stream = e[0]
		p.unit_size = 3.0
		p.max_distance = 45.0
		p.volume_db = float(e[1]) + 4.0
		(want[id] as Node3D).add_child(p)
		p.play(randf() * 5.0)
		_feuer[id] = p
		_merke("feuer")


# ---- menu clicks (only in games and the window «Spielen») --------------------------------------------------------------------
func _knoten(n: Node) -> void:
	if n is BaseButton and not n.has_meta("klang_klick"):
		n.set_meta("klang_klick", true)
		if (n as BaseButton).toggle_mode:
			(n as BaseButton).toggled.connect(func(on: bool): _klick("ui_auf" if on else "ui_zu"))
		else:
			(n as BaseButton).pressed.connect(func(): _klick("ui_klick"))


func _klick(nm: String) -> void:
	if not aktiv() or _ui == null:
		return
	if main != null and bool(main.get("kids_on")) and bool(main.get("kids_sound")):
		return                                             # the kids mode has its own button sounds (kids.gd)
	var e := _stream(nm, false)
	if e.is_empty():
		return
	_ui.stream = e[0]
	_ui.volume_db = float(e[1]) - 2.0
	_ui.play()
	_merke(nm)


# =============================================================================================================================
# info / control
# =============================================================================================================================
func info() -> Dictionary:
	var busse_ := {}
	for b in BUSSE:
		var i := AudioServer.get_bus_index(b)
		busse_[b] = {"i": i, "db": snappedf(AudioServer.get_bus_volume_db(i), 0.1) if i >= 0 else null,
				"stumm": AudioServer.is_bus_mute(i) if i >= 0 else null, "vol": vol[b]}
	var lim := false
	for e in range(AudioServer.get_bus_effect_count(0)):
		if AudioServer.get_bus_effect(0, e) is AudioEffectHardLimiter:
			lim = true
	return {"ok": true, "kontext": kontext, "ton_am_pc": ton_am_pc(), "musik_an": musik_an, "musik": _mus_nm[_mus_i],
			"musik_g": snappedf(_mus_g[_mus_i], 0.01), "spannung": snappedf(_spannung, 0.01), "busse": busse_, "begrenzer": lim,
			"feuer": _feuer.size(), "log": log_.slice(-12)}


func control(d: Dictionary) -> Dictionary:
	match str(d.get("do", "info")):
		"test":
			var ok := false
			match str(d.get("art", "fund")):
				"raetsel":
					ok = raetsel()
				"kapitel":
					ok = kapitel()
				"tusch":
					ok = tusch()
				"erwischt":
					ok = erwischt()
				_:
					ok = fund()
			return {"ok": ok, "kontext": kontext}
		"erleben":
			erleben(str(d.get("id", main.scene)))
			return {"ok": true}
		"gefahr":
			gefahr(str(d.get("quelle", "test")), float(d.get("stufe", 1.0)), float(d.get("dauer", 5.0)))
			return {"ok": true}
	return info()
