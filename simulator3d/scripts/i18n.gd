extends RefCounted
## Sprachen des Simulators (Phase 1, 30.10.2026): die Sprachen von MoveEye - Deutsch, Français, Italiano, Rumantsch Grischun,
## English. Die Texte im Code bleiben deutsch; T.t("Deutscher Text") gibt sie in der aktuellen Sprache zurück.
##   const T = preload("res://scripts/i18n.gd")
##   T.t("Wetter")                                  -> «Météo» (fr)
##   T.t("%d Bilder", [n])                          -> Vorlage übersetzen, dann einsetzen (%s %d %.1f …)
##   T.t("Wir folgen {name}", {"name": who})        -> {name} einsetzen
## Übersetzungen: res://i18n/texte.json {"Deutsch": {"en", "fr", "it", "rm"}} - gesammelt und nachgeführt mit
## werkzeuge/sim_texte.py. Fehlt eine: Rumantsch -> Deutsch, Französisch / Italienisch -> Englisch -> Deutsch,
## Englisch -> Deutsch (wie in MoveEye, CLAUDE.md «Sprachen»).
## Welche Sprache: die Wahl im Simulator (set_lang, user://simulator_sprache.json); ohne Wahl («auto») die Sprache von
## MoveEye (Feld «lang» im Zustand, den MoveEye schickt - auch nach dem Trennen bleibt die zuletzt gemeldete); sonst Deutsch.
## Zum Testen: /control {"action": "lang", "value": "fr"} (oder "auto"), {"action": "lang", "text": "Wetter"}.
## Phase 2 (später): alle Texte mit T.t() umhüllen, Umschalter ins Bedienfeld («Mehr»), Schrift-Check für Akzente.

const LANGS := [["de", "Deutsch"], ["fr", "Français"], ["it", "Italiano"], ["rm", "Rumantsch Grischun"], ["en", "English"]]
const FALLBACK := {"de": [], "en": ["de"], "fr": ["en", "de"], "it": ["en", "de"], "rm": ["de"]}
const FILE := "res://i18n/texte.json"
const CHOICE_FILE := "user://simulator_sprache.json"

static var _tx := {}                  # German -> {en, fr, it, rm}
static var _loaded := false
static var _cache := {}               # lang -> {German -> result}
static var _choice := ""              # what the user picked in the simulator ("" = auto: like MoveEye)
static var _mw_lang := ""             # the last language MoveEye sent
static var _choice_loaded := false
static var _lang_frame := -1
static var _lang := "de"
static var version := 0               # +1 on every change of the language (the panel can rebuild itself)


static func codes() -> Array:
	var out := []
	for l in LANGS:
		out.append(l[0])
	return out


static func langs() -> Array:
	"""[[code, name], …] for the switch (phase 2: in the panel, «Mehr»)"""
	return LANGS.duplicate(true)


static func _load() -> void:
	_loaded = true
	_tx = {}
	if not FileAccess.file_exists(FILE):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
	if typeof(d) != TYPE_DICTIONARY:
		return
	for k in d:
		if typeof(d[k]) == TYPE_DICTIONARY and not str(k).begins_with("_"):
			_tx[k] = d[k]


static func _load_choice() -> void:
	_choice_loaded = true
	if not FileAccess.file_exists(CHOICE_FILE):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(CHOICE_FILE))
	if typeof(d) == TYPE_DICTIONARY:
		var c := str(d.get("lang", ""))
		_choice = c if c in codes() else ""
		var m := str(d.get("mw_lang", ""))
		_mw_lang = m if m in codes() else ""


static func _save_choice() -> void:
	var f := FileAccess.open(CHOICE_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"lang": _choice, "mw_lang": _mw_lang}))


static func _changed() -> void:
	_cache = {}
	_lang_frame = -1
	version += 1


static func set_lang(code: String) -> bool:
	"""the user picks a language in the simulator; "" or "auto" = like MoveEye again. false = unknown code"""
	if not _choice_loaded:
		_load_choice()
	var c := code.strip_edges().to_lower()
	if c == "auto":
		c = ""
	if c != "" and not c in codes():
		return false
	if c != _choice:
		_choice = c
		_save_choice()
		_changed()
	return true


static func choice() -> String:
	"""the user's choice ("" = auto)"""
	if not _choice_loaded:
		_load_choice()
	return _choice


static func set_moveeye_lang(code) -> void:
	"""MoveEye told its language (state field «lang»); kept for later, also after a restart"""
	if not _choice_loaded:
		_load_choice()
	var c := str(code if code != null else "").strip_edges().to_lower().left(2)
	if c in codes() and c != _mw_lang:
		_mw_lang = c
		_save_choice()
		_changed()


static func _main_node() -> Node:
	var ml = Engine.get_main_loop()
	if ml is SceneTree and (ml as SceneTree).current_scene != null:
		return (ml as SceneTree).current_scene
	return null


static func lang() -> String:
	"""the language shown now: the choice in the simulator, else the one of MoveEye, else German"""
	var fr := Engine.get_process_frames()
	if fr == _lang_frame and fr > 0:
		return _lang
	_lang_frame = fr
	if not _choice_loaded:
		_load_choice()
	var mn := _main_node()
	if mn != null and "mw" in mn and typeof(mn.mw) == TYPE_DICTIONARY and mn.mw.has("lang"):
		set_moveeye_lang(mn.mw.get("lang"))
	var l := _choice if _choice != "" else (_mw_lang if _mw_lang != "" else "de")
	if l != _lang:
		_lang = l
		_cache = {}
	_lang_frame = fr
	return _lang


static func lookup(de: String, code: String) -> String:
	"""the text in that language with the fallbacks (no placeholders filled in)"""
	if code == "de" or de == "":
		return de
	if not _loaded:
		_load()
	var row = _tx.get(de)
	if typeof(row) != TYPE_DICTIONARY:
		return de
	for l in [code] + FALLBACK.get(code, ["de"]):
		if l == "de":
			return de
		var v := str(row.get(l, ""))
		if v != "":
			return v
	return de


static func t(de: String, args = null) -> String:
	"""the German UI text in the current language; args: Array/value for %s %d …, Dictionary for {name}"""
	var code := lang()
	var c: Dictionary = _cache.get(code, {})
	if not _cache.has(code):
		_cache[code] = c
	var s: String
	if c.has(de):
		s = c[de]
	else:
		s = lookup(de, code)
		c[de] = s
	return fill(s, args)


static func tr_de(de: String, args = null) -> String:
	"""same as t() (a name that does not clash with Object.tr)"""
	return t(de, args)


static func fill(s: String, args) -> String:
	if args == null:
		return s
	if typeof(args) == TYPE_DICTIONARY:
		for k in args:
			s = s.replace("{" + str(k) + "}", str(args[k]))
		return s
	if typeof(args) != TYPE_ARRAY:
		args = [args]
	if s.count("%") == 0:
		return s
	return s % args


static func stats() -> Dictionary:
	"""how many texts are translated per language (for tests and the report)"""
	if not _loaded:
		_load()
	var out := {"texts": _tx.size()}
	for l in ["en", "fr", "it", "rm"]:
		var n := 0
		for k in _tx:
			if str(_tx[k].get(l, "")) != "":
				n += 1
		out[l] = n
	return out


static func control(d: Dictionary) -> Dictionary:
	"""/control {"action": "lang", "value": "fr" | "auto"} switches; {"text": "…"} translates a text (tests)"""
	if d.has("value"):
		if not set_lang(str(d["value"])):
			return {"ok": false, "error": "unknown language", "langs": codes()}
	var out := {"ok": true, "lang": lang(), "choice": choice(), "moveeye": _mw_lang, "langs": codes(), "stats": stats()}
	if d.has("text"):
		var lng := str(d.get("in", lang()))
		out["text"] = lookup(str(d["text"]), lng) if lng in codes() else str(d["text"])
	return out
