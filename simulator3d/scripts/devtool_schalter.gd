extends Node
## Entwicklertool · Schalter (Daniel 31.10.2026, Paket «Entwickler zusammenlegen»): der Reiter «Schalter» im Fenster
## «Mehr → Entwickler» (devtool_extra.gd, neben Notizen / Kontaktbogen / Kapitel-Sprung / Spieltest). Hier stehen die Knöpfe
## der früheren Gruppe «Entwickler» des Bedienfelds - es gibt im Simulator nur noch EIN «Entwickler» (dieses Fenster).
##   * die Steuerelemente der Gruppe «Entwickler» mit extra «devwin» (main._register_controls: Prüfstand öffnen,
##     Störungen testen) - dieselben Einträge wie bisher (gleiche ids, gleiche /control-Befehle set / press), nur hier gezeichnet
##   * «Diagnose-Paket (MoveEye)» (main._diag_pack, früher als Knopf in der Gruppe)
##   * die Zeile, ob der «Entwickler-Bereich» von MoveEye an ist (dann zeigt das Bedienfeld die Karte «Entwickler» mit dem
##     Knopf «Entwickler-Fenster öffnen», wie MoveEye seine Gruppe «Entwickler» nur mit dem Entwickler-Bereich zeigt)
##   Spieltest-Assistent und «Meldung aufs Handy» stehen nur im Reiter «Spieltest» (nicht doppelt).
## Lite: nichts Eigenes (nur Knöpfe; die Zeile wird beim Öffnen und alle 2 s neu geschrieben, solange der Reiter offen ist).
## /control {"action": "dev", "do": "tab", "value": "schalter"} öffnet das Fenster auf diesem Reiter.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")

var x                                    # devtool_extra.gd
var dev
var main
var _state: Label
var _open := false
var _t := 0.0
var _say_t := -100.0                     # a message of a button stays a few seconds before the state line comes back


static func ids(m) -> Array:
	"""the controls of the tab: group «Entwickler», marked «devwin», not the Spieltest switches (tab «Spieltest»)"""
	var out := []
	if m == null:
		return out
	for c in m.controls:
		if c.group == "Entwickler" and c.extra.get("devwin", false) and not str(c.id).begins_with("spieltest_"):
			out.append(c)
	return out


func build(v: VBoxContainer) -> void:
	var intro := UI.small(T.t("Prüfstand, Störungen und Diagnose – früher die Gruppe «Entwickler» im Bedienfeld. Spieltest: eigener Reiter."), UI.MUT)
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	intro.custom_minimum_size = Vector2(598, 0)
	v.add_child(intro)
	var fl := HFlowContainer.new()
	fl.add_theme_constant_override("h_separation", 6)
	fl.add_theme_constant_override("v_separation", 6)
	v.add_child(fl)
	for c in ids(main):
		if c.type == "button":
			var b := Button.new()
			b.text = T.t(str(c.label))
			b.custom_minimum_size = Vector2(190, 34)
			var cc: Dictionary = c
			b.pressed.connect(func(): cc["set"].call())
			fl.add_child(b)
		elif c.type == "toggle":
			var t := CheckButton.new()
			t.text = T.t(str(c.label))
			var cc2: Dictionary = c
			t.set_pressed_no_signal(bool(c["get"].call()) if c["get"] != null else false)
			t.toggled.connect(func(on): cc2["set"].call(on))
			t.set_meta("ctl", c)
			fl.add_child(t)
	var dg := Button.new()
	dg.text = T.t("Diagnose-Paket (MoveEye)")
	dg.tooltip_text = T.t("MoveEye packt Protokoll, Einstellungen ohne Passwörter und Systemwerte in ein ZIP (öffnet den Browser). Braucht ein verbundenes MoveEye.")
	dg.custom_minimum_size = Vector2(190, 34)
	dg.pressed.connect(func():
		main._diag_pack()
		_say(str(main.start_info)))
	fl.add_child(dg)
	_state = UI.small("", UI.TXT)
	_state.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_state.custom_minimum_size = Vector2(598, 0)
	v.add_child(_state)
	paint()


func _say(t: String) -> void:
	if _state != null and t != "":
		_state.text = t
		_say_t = Time.get_ticks_msec() / 1000.0


func paint() -> void:
	if _state == null or main == null or Time.get_ticks_msec() / 1000.0 - _say_t < 6.0:
		return
	var con: bool = main.mw_addr != "" and main.now() - main.mw_t <= 10.0
	if not con:
		_state.text = T.t("MoveEye nicht verbunden – Diagnose-Paket und Entwickler-Bereich brauchen ein verbundenes MoveEye.")
	elif main.dev_area:
		_state.text = T.t("Entwickler-Bereich von MoveEye: an – das Bedienfeld zeigt die Karte «Entwickler» (Knopf zu diesem Fenster).")
	else:
		_state.text = T.t("Entwickler-Bereich von MoveEye: aus (MoveEye: Einstellungen → System → Gerät & Hilfe) – nur dieses Fenster.")


func on_show(tab: String) -> void:
	_open = tab == "schalter"
	if _open:
		paint()


func _process(dt: float) -> void:
	if not _open or dev == null or not dev.shown:
		return
	_t -= dt
	if _t <= 0.0:
		_t = 2.0
		paint()


func info() -> Dictionary:
	return {"ok": true, "ids": ids(main).map(func(c): return c.id), "dev_area": main.dev_area if main != null else false}
