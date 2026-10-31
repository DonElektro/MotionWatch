extends RefCounted
## Erzählerstimme (Paket A6, Daniel 31.10.2026): die Tagebuchseiten des Grossvaters werden vorgelesen.
## Godot 4.3 DisplayServer.tts_* (Sprachausgabe des Betriebssystems):
##   Windows = SAPI / OneCore-Stimmen (bei Windows dabei, z. B. «Microsoft Hedda» Deutsch, «Zira» Englisch),
##   Linux = speech-dispatcher (libspeechd.so.2, wird zur Laufzeit geladen; Paket «speech-dispatcher» + z. B. espeak-ng),
##   macOS = AVSpeechSynthesizer. Headless / ohne Stimmen: nichts passiert, das Abenteuer läuft normal weiter.
## Voraussetzung: Projekteinstellung audio/general/text_to_speech = true (project.godot). Ohne sie würde jeder Aufruf
## eine Fehlermeldung schreiben - darum wird sie hier zuerst geprüft.
## Abschaltbar: Abenteuer → «Schwierigkeit & Ziel» → Einstellungen → «Erzählerstimme» (spielstand.gd setting "stimme").
## Sprache: die des Simulators (i18n.gd lang()); für Romanisch gibt es kaum Stimmen - dann eine deutsche.

const T = preload("res://scripts/i18n.gd")
const SS = preload("res://scripts/spielstand.gd")

static var _voice := ""
static var _voice_lang := "?"


static func moeglich() -> bool:
	"""this PC can speak (project setting on, the display server has TTS, at least one voice)"""
	if not bool(ProjectSettings.get_setting("audio/general/text_to_speech", false)):
		return false
	if DisplayServer.get_name() == "headless" or not DisplayServer.has_feature(DisplayServer.FEATURE_TEXT_TO_SPEECH):
		return false
	return _pick() != ""


static func an() -> bool:
	return bool(SS.setting("stimme", true))


static func set_an(v: bool) -> void:
	SS.set_setting("stimme", v)
	if not v:
		stopp()


static func _pick() -> String:
	var lg := T.lang()
	if lg == _voice_lang:
		return _voice
	_voice_lang = lg
	_voice = beste(lg)
	if _voice == "":
		_voice = beste("en")
	if _voice == "":
		var all: Array = DisplayServer.tts_get_voices()
		if not all.is_empty():
			_voice = str(all[0].get("id", ""))
	return _voice


static func beste(lg: String) -> String:
	"""the best voice of a language, same order as the browser (MoveEye 639n): 1. name / id with Premium, Enhanced,
	Erweitert, Natural, Neural, Online or Google, 2. the region (de-CH before de-DE before de-AT), 3. the first one
	(the default of the system); rm: a Romansh voice, else a German one. "" = none"""
	if DisplayServer.get_name() == "headless" or not DisplayServer.has_feature(DisplayServer.FEATURE_TEXT_TO_SPEECH):
		return ""
	var base := lg.substr(0, 2).to_lower()
	var reg: Array = ["de_ch", "de_de", "de_at"] if base in ["de", "rm"] else []
	var good := RegEx.create_from_string("(?i)premium|enhanced|erweitert|natural|neural|online|google")
	var best := ""
	var best_s := -1
	var i := 0
	for v in DisplayServer.tts_get_voices():
		var l := str(v.get("language", "")).to_lower().replace("-", "_")
		var s := 0
		if l.begins_with(base):
			s = 300
		elif base == "rm" and l.begins_with("de"):
			s = 100
		else:
			continue
		if good.search(str(v.get("name", "")) + " " + str(v.get("id", ""))) != null:
			s += 1000
		var ri := reg.find(l.substr(0, 5))
		if ri >= 0:
			s += (3 - ri) * 20
		s -= mini(i, 9)                                # among equals: the earlier (the system's order)
		i += 1
		if s > best_s:
			best_s = s
			best = str(v.get("id", ""))
	return best


static func sprich(text: String) -> bool:
	"""read one text (an older one is stopped); false = not possible or switched off"""
	if not an() or not moeglich():
		return false
	var t := text.replace("«", "").replace("»", "").replace("\n", " ").strip_edges()
	if t == "":
		return false
	DisplayServer.tts_stop()
	# a calm voice: a bit slower and lower than normal (the grandfather's diary)
	DisplayServer.tts_speak(t, _pick(), 80, 0.95, 0.92)
	return true


static func spricht() -> bool:
	if not bool(ProjectSettings.get_setting("audio/general/text_to_speech", false)) or DisplayServer.get_name() == "headless":
		return false
	return DisplayServer.tts_is_speaking()


static func stopp() -> void:
	if bool(ProjectSettings.get_setting("audio/general/text_to_speech", false)) and DisplayServer.get_name() != "headless":
		DisplayServer.tts_stop()


static func state() -> Dictionary:
	var ok := moeglich()
	return {"an": an(), "moeglich": ok, "stimme": _voice if ok else "", "spricht": spricht() if ok else false,
			"display": DisplayServer.get_name()}
