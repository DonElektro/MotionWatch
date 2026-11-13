extends Node
## Karte «Simulator-PC» (Besitzer 12.11.2026): die Knöpfe, die es nur am Simulator-PC des Projekts gibt (HP im Kiosk):
##   «🎮 Controller koppeln» · «🌐 Browser» · «⏻ Ausschalten …» (Herunterfahren, Neu starten, Neu starten ins BIOS).
## Die Karte gibt es nur, wenn der Kiosk es sagt: kiosk_sitzung.sh setzt MOVEEYE_HP_KIOSK auf das Hilfsprogramm
## hp_knoepfe.sh (beilagen_linux). Auf jedem anderen PC (Windows, Linux ohne Kiosk, Raspberry Pi) ist nichts davon zu sehen.
## Der Simulator selbst hat dafür keine Rechte und führt nichts anderes aus als dieses eine Programm mit festen Wörtern:
##   info                               -> eine Zeile JSON {"test", "aus", "bios", "browser", "koppeln"}
##   aus herunterfahren|neustart|bios   -> leere Wunsch-Datei, der Dienst moveeye-aus (root) schaltet aus (hp_aus.sh)
##   browser                            -> Browser über dem Kiosk; der Simulator wird solange angehalten (SIGSTOP) und läuft
##                                         danach weiter; zählt als «Spielen» (hp_wache.py). Läuft ein Test: öffnet nicht.
##   koppeln                            -> Fenster «Controller koppeln» (controller_fenster.py)
## Jedes Ausschalten fragt hier im Simulator nach («Wirklich …?»); läuft ein Test, steht das gross dabei.
## Browser und «ins BIOS» nicht im Kinder-Modus. Test: werkzeuge/hp_kiosk_test.gd (Ersatz-Hilfsprogramm).

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const ENV := "MOVEEYE_HP_KIOSK"
const WAS := ["herunterfahren", "neustart", "bios"]

var main
var helper := ""
var card: Control = null
var layer: CanvasLayer
var win: PanelContainer = null
var win_id := ""                       # "" | aus | frage:<was> | hinweis
var last := {}                         # die letzte Auskunft von «info»
var note: Label
var _browser_btn: Button
var _toast_t := 0.0


static func helper_path() -> String:
	"""das Hilfsprogramm des Kiosks, '' = dieser PC ist kein Simulator-PC im Kiosk"""
	var p := OS.get_environment(ENV)
	if p == "" or OS.get_name() != "Linux" or not p.is_absolute_path() or not FileAccess.file_exists(p):
		return ""
	return p


func _init() -> void:
	helper = helper_path()
	layer = CanvasLayer.new()                               # the small windows: above the panel and the windows of «Mehr»
	layer.layer = 62
	add_child(layer)
	set_process(false)


func active() -> bool:
	return helper != ""


func kids() -> bool:
	return main != null and bool(main.get("kids_on"))


# ---- das Hilfsprogramm ------------------------------------------------------------------------------------------------------
func info() -> Dictionary:
	"""fragt das Hilfsprogramm (kurz, wartet darauf): {"test": bool, "aus": bool, "bios": bool, "browser": "firefox" | "", "koppeln": bool}"""
	var d := {"test": false, "aus": false, "bios": false, "browser": "", "koppeln": false, "ok": false}
	if helper == "":
		return d
	var out := []
	if OS.execute(helper, ["info"], out, false) != 0 or out.is_empty():
		last = d
		return d
	var js := JSON.new()                                    # (parse(): no error line in the log when the answer is not JSON)
	var j = js.data if js.parse(str(out[0]).strip_edges()) == OK else null
	if typeof(j) == TYPE_DICTIONARY:
		for k in ["test", "aus", "bios", "koppeln"]:
			var x = j.get(k, false)
			d[k] = typeof(x) == TYPE_BOOL and x
		var b := str(j.get("browser", ""))
		d["browser"] = b if b in ["firefox", "firefox-esr", "chromium", "chromium-browser"] else ""
		d["ok"] = true
	last = d
	return d


func run(args: Array) -> bool:
	"""startet das Hilfsprogramm mit festen Wörtern, ohne zu warten"""
	if helper == "":
		return false
	return OS.create_process(helper, PackedStringArray(args)) > 0


# ---- die Karte --------------------------------------------------------------------------------------------------------------
func build(box_: VBoxContainer) -> void:
	if not active():
		return
	var body := UI.fold_card(box_, "Simulator-PC", false, "")
	card = body.get_meta("card")
	if main != null:
		main.fold_bodies.append(body)
		main.top_cards.append(card)
	_knopf(body, T.t("🎮 Controller koppeln"), T.t("PS5-Controller per Bluetooth koppeln, Liste mit Akku, Trennen, Vergessen"), koppeln)
	_browser_btn = _knopf(body, T.t("🌐 Browser"), T.t("Öffnet den Browser über dem Simulator. Der Simulator hält solange an. Zurück: Leiste oben oder Ctrl+Alt+Z"), browser)
	_knopf(body, T.t("⏻ Ausschalten …"), T.t("Herunterfahren, neu starten oder neu starten ins BIOS – mit Rückfrage"), open_aus)
	note = UI.small(T.t("Nur an diesem Simulator-PC."))
	body.add_child(note)


func _knopf(parent: Control, text: String, tip: String, f: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.tooltip_text = tip
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.focus_mode = Control.FOCUS_ALL
	b.custom_minimum_size = Vector2(0, 34)
	b.pressed.connect(f)
	parent.add_child(b)
	return b


func say(t: String) -> void:
	"""eine Zeile auf der Karte (und in der Statuszeile des Simulators)"""
	if note != null:
		note.text = t
	if main != null:
		main.set("start_info", t)
	_toast_t = 8.0
	set_process(true)


func _process(dt: float) -> void:
	_toast_t -= dt
	if _toast_t <= 0.0:
		set_process(false)
		if note != null:
			note.text = T.t("Nur an diesem Simulator-PC.")


# ---- Controller koppeln, Browser ------------------------------------------------------------------------------------------------
func koppeln() -> void:
	if not run(["koppeln"]):
		say(T.t("Das geht an diesem PC nicht."))


func browser() -> void:
	if kids():
		say(T.t("Der Browser ist im Kinder-Modus aus."))
		return
	var d := info()
	if not d["ok"]:
		say(T.t("Das geht an diesem PC nicht."))
	elif d["test"]:
		_hinweis(T.t("Test läuft"), T.t("Am Simulator-PC läuft gerade ein Test. Der Browser öffnet jetzt nicht – sonst wird das Ergebnis verfälscht. Bitte später noch einmal."))
	elif d["browser"] == "":
		_hinweis(T.t("Kein Browser installiert"), T.t("Auf diesem PC ist kein Browser installiert (Firefox oder Chromium). Einmal im normalen Desktop (Ctrl+Alt+D) installieren: sudo apt install firefox"))
	else:
		say(T.t("Der Browser öffnet … Zurück: Leiste oben oder Ctrl+Alt+Z"))
		run(["browser"])


# ---- Ausschalten ------------------------------------------------------------------------------------------------------------
func open_aus() -> void:
	var d := info()
	var v := _fenster("aus", T.t("Ausschalten"))
	if not d["ok"] or not d["aus"]:
		_text(v, T.t("Ausschalten aus dem Simulator ist an diesem PC noch nicht eingerichtet (kommt mit dem nächsten Update des Simulator-PCs). Bis dahin: den Einschaltknopf am Gehäuse kurz drücken."), UI.ORG)
		_reihe(v, [[T.t("Schliessen"), close, false]])
		return
	if d["test"]:
		_text(v, T.t("Achtung: Am Simulator-PC läuft gerade ein Test."), UI.ORG)
	_gross(v, T.t("Herunterfahren"), func(): frage("herunterfahren"))
	_gross(v, T.t("Neu starten"), func(): frage("neustart"))
	if d["bios"] and not kids():
		_gross(v, T.t("Neu starten ins BIOS"), func(): frage("bios"))
	else:
		_text(v, T.t("Ins BIOS: beim Einschalten Esc, dann F10."), UI.MUT)
	_reihe(v, [[T.t("Abbrechen"), close, false]])


func frage(was: String) -> void:
	"""die Rückfrage vor dem Ausschalten; läuft ein Test, steht es gross dabei"""
	if not was in WAS:
		return
	var d := info()
	var titel: String = {"herunterfahren": T.t("Wirklich herunterfahren?"), "neustart": T.t("Wirklich neu starten?"),
			"bios": T.t("Wirklich neu starten ins BIOS?")}[was]
	var v := _fenster("frage:" + was, titel)
	if d["test"]:
		_text(v, T.t("Test läuft – trotzdem ausschalten?"), UI.ORG, 16)
		_text(v, T.t("Der laufende Test wird abgebrochen. Was schon fertig gerechnet ist, bleibt; der Rest wird beim nächsten Lauf nachgeholt."), UI.TXT)
	if was == "bios":
		_text(v, T.t("Der PC startet neu und zeigt die Einstellungen der Hauptplatine (BIOS). Dort «Exit» wählen, um normal zu starten."), UI.TXT)
	else:
		_text(v, T.t("Der Simulator wird beendet. Nicht gespeicherte Spielstände gehen verloren."), UI.TXT)
	var ja: String = {"herunterfahren": T.t("Ja, herunterfahren"), "neustart": T.t("Ja, neu starten"), "bios": T.t("Ja, ins BIOS")}[was]
	_reihe(v, [[T.t("Abbrechen"), close, false], [ja, func(): aus(was), true]])


func aus(was: String) -> void:
	"""nach der Rückfrage: den Wunsch abgeben (das Hilfsprogramm legt die leere Wunsch-Datei an)"""
	if not was in WAS or win_id != "frage:" + was:
		return                                             # nie ohne die Rückfrage davor
	close()
	if run(["aus", was]):
		say({"herunterfahren": T.t("Der PC fährt herunter …"), "neustart": T.t("Der PC startet neu …"), "bios": T.t("Der PC startet neu ins BIOS …")}[was])
	else:
		say(T.t("Das geht an diesem PC nicht."))


# ---- das kleine Fenster -----------------------------------------------------------------------------------------------------
func _hinweis(titel: String, text: String) -> void:
	var v := _fenster("hinweis", titel)
	_text(v, text, UI.TXT)
	_reihe(v, [[T.t("Schliessen"), close, false]])


func close() -> void:
	if win != null and is_instance_valid(win):
		win.get_parent().queue_free()
	win = null
	win_id = ""


func _fenster(id: String, titel: String) -> VBoxContainer:
	close()
	var dim := ColorRect.new()                             # dunkelt den Simulator ab und fängt Klicks daneben ab
	dim.color = Color(0, 0, 0, 0.55)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	layer.add_child(dim)
	var mitte := CenterContainer.new()
	mitte.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.add_child(mitte)
	win = PanelContainer.new()
	win.theme = main.ui_root.theme if main != null and main.get("ui_root") != null else UI.theme()
	win.add_theme_stylebox_override("panel", UI.box(UI.PANEL, UI.ORG, 14, 18, 2))
	win.custom_minimum_size = Vector2(440, 0)
	mitte.add_child(win)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	win.add_child(v)
	var h := Label.new()
	h.text = titel
	h.add_theme_font_override("font", UI.heading_font())
	h.add_theme_font_size_override("font_size", 18)
	v.add_child(h)
	win_id = id
	return v


func _text(v: VBoxContainer, t: String, col: Color, size := 13) -> void:
	var l := Label.new()
	l.text = t
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(420, 0)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	v.add_child(l)


func _gross(v: VBoxContainer, t: String, f: Callable) -> void:
	var b := Button.new()
	b.text = t
	b.custom_minimum_size = Vector2(0, 44)
	b.focus_mode = Control.FOCUS_ALL
	b.pressed.connect(f)
	v.add_child(b)


func _reihe(v: VBoxContainer, knoepfe: Array) -> void:
	var r := HBoxContainer.new()
	r.alignment = BoxContainer.ALIGNMENT_END
	r.add_theme_constant_override("separation", 8)
	v.add_child(r)
	var erster: Button = null
	for k in knoepfe:
		var b := Button.new()
		b.text = k[0]
		b.custom_minimum_size = Vector2(120, 36)
		b.focus_mode = Control.FOCUS_ALL
		if k[2]:                                             # der Knopf, der wirklich ausschaltet: rot
			for st in ["normal", "hover", "pressed"]:
				b.add_theme_stylebox_override(st, UI.box(UI.RED if st != "hover" else UI.RED.lightened(0.1), UI.RED))
			b.add_theme_color_override("font_color", Color.WHITE)
		b.pressed.connect(k[1])
		r.add_child(b)
		if erster == null:
			erster = b
	if erster != null and erster.is_inside_tree():
		erster.grab_focus()                                  # Fokus auf «Abbrechen» / «Schliessen»: Enter schaltet nie aus Versehen aus


func _unhandled_key_input(e: InputEvent) -> void:
	if win != null and e is InputEventKey and e.pressed and (e as InputEventKey).keycode == KEY_ESCAPE:
		close()
		get_viewport().set_input_as_handled()
