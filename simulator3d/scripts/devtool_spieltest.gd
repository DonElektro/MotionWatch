extends Node
## Entwicklertool · Spieltest (Daniel 31.10.2026, Paket «Spieltest-Assistent»): der Teil «Spieltest» im Fenster
## «Mehr → Entwickler» (devtool_extra.gd, wie Notizen / Kontaktbogen / Kapitel-Sprung). Der Assistent selbst ist
## spieltest.gd (läuft auch ohne dieses Fenster, ein / aus bleibt über Neustarts). Hier:
##   * Schalter «Spieltest-Assistent» + Stand (läuft seit …, was gerade notiert wird)
##   * Push: Schalter «Spieltest-Meldungen aufs Handy» (= der Schalter in MoveEye, Einstellungen → Entwickler) und die Zeile,
##     ob es einen Push gibt (ohne verbundenes MoveEye: keiner)
##   * Zusammenfassung pro Spielmodus: Vorschläge nach festen Regeln, mit Anzahl Runden als Grundlage; die letzten Runden
##   * «ZIP für Claude» (Rohdaten + Bericht.md, devtool_notizen.pack_zip), «Datei hier: …», «Ordner öffnen», «Daten löschen»
## Lite: nichts Eigenes (neu gezeichnet nur beim Öffnen, nach einer Runde und alle 5 s, solange der Teil offen ist).

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Sym = preload("res://scripts/symbole.gd")

var x                                    # devtool_extra.gd
var dev
var main
var _on: CheckButton
var _state: Label
var _push_chk: CheckButton
var _push_l: Label
var _box: VBoxContainer
var _path: LineEdit
var _del: Button
var _del_armed := false
var _open := false
var _t := 0.0


func st():
	return main.spieltest if main != null else null


func build(v: VBoxContainer) -> void:
	var r1 := HBoxContainer.new()
	r1.add_theme_constant_override("separation", 8)
	v.add_child(r1)
	_on = CheckButton.new()
	_on.text = T.t("Spieltest-Assistent")
	_on.tooltip_text = T.t("Beobachtet Abenteuer, Spielbereich, Horror (nur entsperrt), Ferienpark-Aufgaben, Erlebniswelt und das Spiel – bis du ihn ausschaltest, auch nach einem Neustart.")
	_on.toggled.connect(func(b):
		if st() != null:
			st().set_on(b))
	r1.add_child(_on)
	_state = UI.small("", UI.TXT)
	_state.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_state.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	r1.add_child(_state)
	var r2 := HBoxContainer.new()
	r2.add_theme_constant_override("separation", 8)
	v.add_child(r2)
	_push_chk = CheckButton.new()
	_push_chk.text = T.t("Meldung aufs Handy")
	_push_chk.tooltip_text = T.t("Der Schalter «Spieltest-Meldungen» von MoveEye (Einstellungen → Entwickler): nach jeder Runde eine kurze Push-Nachricht über die Push-Einstellung von MoveEye.")
	_push_chk.toggled.connect(func(b):
		if st() != null and not st().set_mw_push(b):
			_push_chk.set_pressed_no_signal(not b)
		paint())
	r2.add_child(_push_chk)
	_push_l = UI.small("", UI.MUT)
	_push_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_push_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	r2.add_child(_push_l)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(598, 190)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(sc)
	_box = VBoxContainer.new()
	_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_box.add_theme_constant_override("separation", 3)
	sc.add_child(_box)
	var r3 := HBoxContainer.new()
	r3.add_theme_constant_override("separation", 6)
	v.add_child(r3)
	var bz := Button.new()
	bz.text = T.t("ZIP für Claude")
	UI.primary(bz)
	bz.tooltip_text = T.t("Rohdaten (eine JSON-Datei pro Runde) und der Bericht mit den Vorschlägen (Markdown) in einer ZIP-Datei")
	bz.pressed.connect(_export)
	r3.add_child(bz)
	var bo := Button.new()
	bo.text = T.t("Ordner öffnen")
	bo.pressed.connect(func(): x.open_folder(st().EXPORT_DIR if st() != null else "user://spieltest/export"))
	r3.add_child(bo)
	var br := Button.new()
	br.text = T.t("Neu auswerten")
	br.pressed.connect(paint)
	r3.add_child(br)
	_del = Button.new()
	_del.text = T.t("Daten löschen")
	_del.tooltip_text = T.t("Alle notierten Runden löschen (zweimal klicken)")
	_del.pressed.connect(_delete)
	r3.add_child(_del)
	_path = LineEdit.new()
	_path.editable = false
	_path.custom_minimum_size = Vector2(598, 0)
	_path.placeholder_text = T.t("Die ZIP-Datei kannst du im Chat anhängen.")
	v.add_child(_path)


func on_show(tab: String) -> void:
	_open = tab == "spieltest"
	if _open:
		if st() != null:
			st().ui = self
		paint()


func _process(dt: float) -> void:
	if not _open or dev == null or not dev.shown:
		return
	_t -= dt
	if _t <= 0.0:
		_t = 5.0
		_paint_state()


func _paint_state() -> void:
	var s = st()
	if s == null or _on == null:
		return
	_on.set_pressed_no_signal(s.on)
	if not s.on:
		_state.text = T.t("Aus. Einschalten: dann werden alle Runden notiert (nur auf diesem PC).")
	else:
		var t := T.t("Läuft seit %s.") % str(s.seit).replace("T", " ").left(16)
		var run := []
		for m in s.rounds:
			var r: Dictionary = s.rounds[m]
			run.append("%s · %s (%s Min.)" % [T.t(str(s.KURZ.get(m, m))), T.t(str(r["einheit"])), str(int(float(r["aktiv_s"]) / 60.0))])
		_state.text = t + " " + (T.t("Notiert gerade: %s") % ", ".join(PackedStringArray(run)) if not run.is_empty() else T.t("Gerade keine Runde."))
	_push_chk.set_pressed_no_signal(bool(s.mw_state().get("on", false)))
	_push_chk.disabled = not s.mw_connected()
	_push_l.text = s.push_line()
	if not s.push_log.is_empty():
		var it: Dictionary = s.push_log[-1]
		_push_l.text += "\n" + T.t("Letzte: «%s» – %s") % [Sym.clean(str(it["text"])), T.t(str(it["status"]))]
	_push_l.add_theme_color_override("font_color", UI.GRN if s.push_line().begins_with(T.t("Push über MoveEye ist an.")) else UI.ORG)


func paint() -> void:
	if _box == null or st() == null:
		return
	_paint_state()
	for c in _box.get_children():
		c.queue_free()
	var S: Dictionary = st().summary()
	if (S["modi"] as Array).is_empty():
		_box.add_child(UI.small(T.t("Noch keine Runden notiert. Spiel eine Runde (z. B. Spielbereich oder Abenteuer) – danach stehen hier die Vorschläge."), UI.MUT))
		return
	for g in S["modi"]:
		var h := Label.new()
		h.text = "%s · %s" % [T.t(str(g["name"])), (T.t("%d Runde") if int(g["n"]) == 1 else T.t("%d Runden")) % int(g["n"])]
		h.add_theme_font_size_override("font_size", 14)
		_box.add_child(h)
		var V: Array = g["vorschlaege"]
		if V.is_empty():
			_box.add_child(_line("•", T.t("Noch nichts Auffälliges."), UI.MUT))
		for vv in V:
			var col: Color = [UI.GRN, UI.TXT, UI.ORG][int(vv["stufe"])]
			_box.add_child(_line(["+", "•", "!"][int(vv["stufe"])], str(vv["text"]), col))
		var last := []
		for r in (g["runden"] as Array).slice(-3):
			var b = r.get("bewertung", null)
			var sm := ""
			if b is Dictionary and b.get("smiley", null) != null:
				sm = " · " + T.t(str(st().SMILEY_WORD.get(int(b["smiley"]), "")))
			last.append("%s %s %s Min. %s%s" % [str(r.get("start", "")).substr(11, 5), T.t(str(r.get("einheit", ""))),
					str(snappedf(float(r.get("aktiv_s", 0.0)) / 60.0, 0.1)), T.t(str(r.get("ergebnis", ""))), sm])
		_box.add_child(_line(" ", T.t("Zuletzt: %s") % " | ".join(PackedStringArray(last)), UI.MUT))


func _line(mark: String, t: String, col: Color) -> Control:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 6)
	var m := UI.small(mark, col)
	m.custom_minimum_size = Vector2(12, 0)
	h.add_child(m)
	var l := UI.small(t, col)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(l)
	return h


func _export() -> void:
	var p: String = st().export_zip() if st() != null else ""
	if p == "":
		dev._say(T.t("Export ging nicht."))
		return
	_path.text = T.t("Datei hier: %s") % ProjectSettings.globalize_path(p)
	dev._say(T.t("Spieltest-Daten exportiert."))


func _delete() -> void:
	if not _del_armed:
		_del_armed = true
		_del.text = T.t("Wirklich löschen?")
		get_tree().create_timer(4.0).timeout.connect(func():
			_del_armed = false
			if _del != null:
				_del.text = T.t("Daten löschen"))
		return
	_del_armed = false
	_del.text = T.t("Daten löschen")
	var n: int = st().clear_all() if st() != null else 0
	dev._say(T.t("%d Runden gelöscht.") % n)
	paint()
