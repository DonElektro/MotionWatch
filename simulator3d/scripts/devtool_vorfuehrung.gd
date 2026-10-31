extends Node
## Entwicklertool · Vorführung (Daniel 31.10.2026): der Teil «Vorführung» im Fenster «Mehr → Entwickler» (nur der Besitzer,
## devtool.gd). Startet den Vorführmodus «Maggie und der Bergkristall» (maggie_vorfuehrung.gd): Kurzfassung oder ganz,
## Erzählerstimme ein / aus, Kapitel wählen; zeigt den Stand und das Ergebnis des letzten Durchlaufs (ob der Autopilot
## überall weiterkam – BLOCKIERT steht hier und im Protokoll). Lite: nichts Eigenes (neu gezeichnet alle 2 s, wenn offen).

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Vf = preload("res://scripts/maggie_vorfuehrung.gd")

var x                                    # devtool_extra.gd
var dev
var main
var _open := false
var _t := 0.0
var _state: Label
var _stimme: CheckButton
var _kap: OptionButton
var _stop: Button


func build(v: VBoxContainer) -> void:
	var intro := UI.small(T.t("«Maggie und der Bergkristall» als Film: ein Autopilot spielt die Geschichte, du schaust zu (eigener Vorführ-Spielstand, deine Spielstände bleiben unberührt). Im Vollbild: Esc = beenden, Leertaste = Pause, ← → = Kapitel. Im Browser: MoveEye → Simulator → Entwickler → «Vorführung ansehen»."), UI.MUT)
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	intro.custom_minimum_size = Vector2(598, 0)
	v.add_child(intro)
	var r1 := HBoxContainer.new()
	r1.add_theme_constant_override("separation", 8)
	v.add_child(r1)
	var bk := Button.new()
	bk.text = T.t("Kurzfassung ansehen (15–20 Min.)")
	UI.primary(bk)
	bk.tooltip_text = T.t("Je Jahreszeit die Höhepunkte: eine Station mit Maggie, das Schutzding und das böse Tier, das Tor – dazwischen Schnitte. Dann das Finale.")
	bk.pressed.connect(func(): _start("kurz"))
	r1.add_child(bk)
	var bg := Button.new()
	bg.text = T.t("Ganze Geschichte ansehen")
	bg.tooltip_text = T.t("Alle vier Jahreszeiten mit allen Stationen und das Finale – so wie ein Spieler (lang).")
	bg.pressed.connect(func(): _start("ganz"))
	r1.add_child(bg)
	var r2 := HBoxContainer.new()
	r2.add_theme_constant_override("separation", 8)
	v.add_child(r2)
	_stimme = CheckButton.new()
	_stimme.text = T.t("Erzählerstimme")
	_stimme.tooltip_text = T.t("Liest die Texte der Geschichte vor (Sprachausgabe von Windows). Ohne Stimme: nur Untertitel.")
	_stimme.toggled.connect(func(b):
		var vf = Vf.inst(main)
		if vf != null:
			vf.set_stimme(b))
	r2.add_child(_stimme)
	r2.add_child(UI.small(T.t("Beginnen bei:"), UI.MUT))
	_kap = OptionButton.new()
	_kap.focus_mode = Control.FOCUS_NONE
	r2.add_child(_kap)
	_stop = Button.new()
	_stop.text = T.t("Vorführung beenden")
	_stop.pressed.connect(func(): Vf.control(main, {"do": "stop"}))
	r2.add_child(_stop)
	_state = UI.small("", UI.TXT)
	_state.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_state.custom_minimum_size = Vector2(598, 0)
	v.add_child(_state)


func _start(ln: String) -> void:
	var vf = Vf.inst(main)
	if vf == null:
		return
	if _kap.item_count == 0:
		_fill()
	Vf.control(main, {"do": "start", "len": ln, "vollbild": true, "kapitel": maxi(0, _kap.selected)})


func _fill() -> void:
	var vf = Vf.inst(main)
	_kap.clear()
	var nm: Array = vf.kapitel_namen() if vf != null else []
	for i in range(nm.size()):
		_kap.add_item("%d · %s" % [i, nm[i]], i)
	_kap.select(0)


func on_show(tab: String) -> void:
	_open = tab == "vorfuehrung"
	if _open:
		if _kap.item_count == 0:
			_fill()
		paint()


func _process(dt: float) -> void:
	if not _open or dev == null or not dev.shown:
		return
	_t -= dt
	if _t <= 0.0:
		_t = 2.0
		paint()


func paint() -> void:
	var vf = Vf.inst(main)
	if vf == null or _state == null:
		return
	var d: Dictionary = vf.info()
	_stimme.set_pressed_no_signal(bool(d.get("stimme", true)))
	_stimme.disabled = not bool(d.get("stimme_moeglich", false))
	if _stimme.disabled:
		_stimme.tooltip_text = T.t("Auf diesem PC gibt es keine Sprachausgabe – nur Untertitel.")
	_stop.disabled = not bool(d.get("laeuft", false))
	if bool(d.get("laeuft", false)):
		_state.text = T.t("Läuft: %s · %s · %s", [T.t("Kurzfassung") if str(d["laenge"]) == "kurz" else T.t("ganze Geschichte"), str(d.get("kapitel_name", "")), str(d.get("zeit", ""))]) \
				+ ("\n" + T.t("BLOCKIERT: %d Mal – siehe Protokoll.", [int(d["blockiert"])]) if int(d.get("blockiert", 0)) > 0 else "")
	elif str(d.get("ergebnis", "")) != "":
		_state.text = T.t("Letzter Durchlauf: %s", [str(d["ergebnis"])]) + "\n" + str(d.get("text", "")) + "\n" + T.t("Protokoll: %s", [str(d.get("datei", ""))])
	else:
		_state.text = T.t("Bereit.")
	_state.add_theme_color_override("font_color", UI.ORG if int(d.get("blockiert", 0)) > 0 else UI.TXT)
