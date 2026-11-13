extends SceneTree
## Test Karte «Simulator-PC» (scripts/hp_kiosk.gd: Controller koppeln, Browser, Ausschalten) - ohne Bild, ohne den HP:
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/hp_kiosk_test.gd"   (absoluter Pfad nötig)
## Ein Ersatz-Hilfsprogramm (statt hp_knoepfe.sh) schreibt jeden Aufruf in eine Datei und antwortet auf «info» mit dem, was
## der Test vorgibt. Geprüft: ohne MOVEEYE_HP_KIOSK gibt es die Karte nicht; mit: drei Knöpfe; Ausschalten nie ohne
## Rückfrage, «Abbrechen» schaltet nicht aus, «Test läuft – trotzdem ausschalten?» steht da, wenn ein Test läuft; «ins BIOS»
## nur, wenn der PC es kann (sonst der Hinweis «Esc, dann F10»); Browser öffnet nicht, wenn ein Test läuft, keiner
## installiert ist oder im Kinder-Modus; alle Texte in de / en / fr / it / rm.
## Ende: «HP-Kiosk-Test OK» oder «SCRIPT ERROR: HP-Kiosk-Test: …» (Exit-Code 0 / 1).

const T = preload("res://scripts/i18n.gd")
var errs := []
var dir := ""
var HK


func ok(what: String, cond: bool) -> void:
	if not cond:
		errs.append(what)


func _fake_main() -> Node:
	var s := GDScript.new()
	s.source_code = """extends Node
var kids_on := false
var start_info := ""
var ui_root = null
var fold_bodies := []
var top_cards := []
"""
	s.reload()
	var m := Node.new()
	m.set_script(s)
	return m


func _info(test: bool, aus: bool, bios: bool, browser: String) -> void:
	var f := FileAccess.open(dir + "/info.json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"fassung": 8, "test": test, "aus": aus, "bios": bios, "browser": browser, "koppeln": true}) + "\n")
	f.close()


func _calls() -> String:
	"""was das Ersatz-Hilfsprogramm bisher gerufen wurde (ohne «info»); kurz warten: create_process wartet nicht"""
	OS.delay_msec(400)
	var t := FileAccess.get_file_as_string(dir + "/aufrufe.txt") if FileAccess.file_exists(dir + "/aufrufe.txt") else ""
	var out := PackedStringArray()
	for ln in t.split("\n", false):
		if ln != "info":
			out.append(ln)
	return ",".join(out)


func _clear() -> void:
	DirAccess.remove_absolute(dir + "/aufrufe.txt")


func _texts(n: Node, out: PackedStringArray) -> void:
	if n is Label or n is Button:
		out.append(str(n.get("text")))
	for c in n.get_children():
		_texts(c, out)


func _win_text(h) -> String:
	var out := PackedStringArray()
	if h.win != null:
		_texts(h.win, out)
	return " | ".join(out)


func _press(h, text: String) -> bool:
	"""den Knopf mit diesem Text im offenen Fenster drücken"""
	var stack: Array = [h.win]
	while not stack.is_empty():
		var n = stack.pop_back()
		if n is Button and (n as Button).text == text:
			(n as Button).pressed.emit()
			return true
		for c in n.get_children():
			stack.append(c)
	return false


func _initialize() -> void:
	HK = load("res://scripts/hp_kiosk.gd")
	dir = OS.get_environment("HP_KIOSK_TEST_DIR")
	if dir == "":
		dir = "/tmp/mw_hp_kiosk_test_%d" % OS.get_process_id()
	DirAccess.make_dir_recursive_absolute(dir)
	var helper := dir + "/hp_knoepfe.sh"
	var f := FileAccess.open(helper, FileAccess.WRITE)
	f.store_string("#!/bin/sh\necho \"$*\" >> \"%s/aufrufe.txt\"\n[ \"$1\" = info ] && cat \"%s/info.json\"\nexit 0\n" % [dir, dir])
	f.close()
	OS.execute("chmod", ["755", helper])

	# 1. ohne den Kiosk: nichts
	OS.set_environment("MOVEEYE_HP_KIOSK", "")
	ok("ohne MOVEEYE_HP_KIOSK kein Hilfsprogramm", HK.helper_path() == "")
	OS.set_environment("MOVEEYE_HP_KIOSK", dir + "/fehlt.sh")
	ok("Hilfsprogramm fehlt: keine Karte", HK.helper_path() == "")
	OS.set_environment("MOVEEYE_HP_KIOSK", "hp_knoepfe.sh")
	ok("kein ganzer Pfad: keine Karte", HK.helper_path() == "")
	var m0 := _fake_main()
	root.add_child(m0)
	var h0 = HK.new()
	h0.main = m0
	m0.add_child(h0)
	var box0 := VBoxContainer.new()
	root.add_child(box0)
	h0.build(box0)
	ok("ohne Kiosk: build() baut nichts", box0.get_child_count() == 0 and not h0.active())
	ok("ohne Kiosk: nichts wird gestartet", not h0.run(["aus", "herunterfahren"]))

	# 2. im Kiosk: die Karte mit drei Knöpfen
	OS.set_environment("MOVEEYE_HP_KIOSK", helper)
	ok("im Kiosk: Hilfsprogramm gefunden", HK.helper_path() == helper)
	var m := _fake_main()
	root.add_child(m)
	var h = HK.new()
	h.main = m
	m.add_child(h)
	var box := VBoxContainer.new()
	root.add_child(box)
	h.build(box)
	var names := PackedStringArray()
	_texts(box, names)
	var all := " | ".join(names)
	ok("Karte «Simulator-PC» mit Controller koppeln, Browser, Ausschalten: " + all,
			all.to_upper().contains(T.t("Simulator-PC").to_upper()) and all.contains(T.t("🎮 Controller koppeln")) and all.contains(T.t("🌐 Browser")) and all.contains(T.t("⏻ Ausschalten …")))
	ok("Karte in der Liste der Karten", m.fold_bodies.size() == 1 and m.top_cards.size() == 1)

	# 3. Auskunft: nur bekannte Werte
	_info(true, true, true, "firefox")
	var d: Dictionary = h.info()
	ok("info gelesen", d["ok"] and d["test"] and d["aus"] and d["bios"] and d["browser"] == "firefox")
	var f2 := FileAccess.open(dir + "/info.json", FileAccess.WRITE)
	f2.store_string("{\"test\": \"ja\", \"aus\": 1, \"bios\": null, \"browser\": \"rm -rf /\"}\n")
	f2.close()
	d = h.info()
	ok("info mit falschen Typen: alles aus", d["ok"] and not d["test"] and not d["aus"] and not d["bios"] and d["browser"] == "")
	f2 = FileAccess.open(dir + "/info.json", FileAccess.WRITE)
	f2.store_string("kein JSON\n")
	f2.close()
	ok("info ohne JSON: nicht ok", not h.info()["ok"])

	# 4. Ausschalten: drei Wege, Rückfrage, Abbrechen
	_info(false, true, true, "firefox")
	_clear()
	h.open_aus()
	var w := _win_text(h)
	ok("Ausschalten: Herunterfahren, Neu starten, Neu starten ins BIOS: " + w, w.contains(T.t("Herunterfahren")) and w.contains(T.t("Neu starten"))
			and w.contains(T.t("Neu starten ins BIOS")) and not w.contains("F10") and not w.contains(T.t("Achtung: Am Simulator-PC läuft gerade ein Test.")))
	ok("Auswahl allein schaltet nicht aus", _calls() == "")
	ok("Knopf Herunterfahren", _press(h, T.t("Herunterfahren")))
	w = _win_text(h)
	ok("Rückfrage «Wirklich herunterfahren?»: " + w, h.win_id == "frage:herunterfahren" and w.contains(T.t("Wirklich herunterfahren?")) and w.contains(T.t("Ja, herunterfahren"))
			and not w.contains(T.t("Test läuft – trotzdem ausschalten?")))
	ok("Rückfrage allein schaltet nicht aus", _calls() == "")
	ok("Abbrechen", _press(h, T.t("Abbrechen")))
	ok("Abbrechen: Fenster zu, nichts ausgeschaltet", h.win == null and _calls() == "")
	h.aus("herunterfahren")
	ok("aus() ohne Rückfrage davor: nichts", _calls() == "")
	h.frage("neustart")
	h.aus("herunterfahren")
	ok("aus() mit der Rückfrage für etwas anderes: nichts", _calls() == "")
	h.frage("formatieren")
	h.frage("neustart")
	ok("Ja, neu starten", _press(h, T.t("Ja, neu starten")))
	ok("nach «Ja»: genau ein Wunsch «aus neustart»: " + _calls(), _calls() == "aus neustart" and h.win == null)
	_clear()
	h.open_aus()
	_press(h, T.t("Neu starten ins BIOS"))
	ok("Rückfrage BIOS", h.win_id == "frage:bios" and _win_text(h).contains(T.t("Wirklich neu starten ins BIOS?")))
	_press(h, T.t("Ja, ins BIOS"))
	ok("BIOS: Wunsch «aus bios»: " + _calls(), _calls() == "aus bios")
	_clear()
	h.open_aus()
	_press(h, T.t("Herunterfahren"))
	_press(h, T.t("Ja, herunterfahren"))
	ok("Herunterfahren: Wunsch «aus herunterfahren»: " + _calls(), _calls() == "aus herunterfahren")

	# 5. ein Test läuft: klar gewarnt, aber möglich
	_info(true, true, false, "firefox")
	_clear()
	h.open_aus()
	w = _win_text(h)
	ok("Test läuft: Warnung schon in der Auswahl; ohne BIOS-Start der Hinweis Esc / F10: " + w,
			w.contains(T.t("Achtung: Am Simulator-PC läuft gerade ein Test.")) and not w.contains(T.t("Neu starten ins BIOS")) and w.contains("Esc") and w.contains("F10"))
	_press(h, T.t("Herunterfahren"))
	w = _win_text(h)
	ok("Test läuft: «Test läuft – trotzdem ausschalten?» und was mit dem Test geschieht: " + w,
			w.contains(T.t("Test läuft – trotzdem ausschalten?")) and w.contains(T.t("Der laufende Test wird abgebrochen. Was schon fertig gerechnet ist, bleibt; der Rest wird beim nächsten Lauf nachgeholt.")))
	ok("Test läuft: noch nichts ausgeschaltet", _calls() == "")
	_press(h, T.t("Ja, herunterfahren"))
	ok("Test läuft, trotzdem «Ja»: ausgeschaltet", _calls() == "aus herunterfahren")

	# 6. Ausschalten noch nicht eingerichtet (alte Fassung des Kiosks)
	_info(false, false, false, "firefox")
	_clear()
	h.open_aus()
	w = _win_text(h)
	ok("nicht eingerichtet: Hinweis statt Knöpfe: " + w, not w.contains(T.t("Herunterfahren")) and w.contains(T.t("Schliessen")))
	h.close()

	# 7. Browser
	_info(false, true, true, "firefox")
	_clear()
	h.browser()
	ok("Browser: Wunsch «browser»: " + _calls(), _calls() == "browser" and h.win == null)
	_info(true, true, true, "firefox")
	_clear()
	h.browser()
	ok("Browser, Test läuft: öffnet nicht, sagt es: " + _win_text(h), _calls() == "" and _win_text(h).contains(T.t("Test läuft")))
	h.close()
	_info(false, true, true, "")
	h.browser()
	ok("Browser, keiner installiert: öffnet nicht, sagt es", _calls() == "" and _win_text(h).contains(T.t("Kein Browser installiert")))
	h.close()
	_info(false, true, true, "firefox")
	m.kids_on = true
	h.browser()
	ok("Browser im Kinder-Modus: öffnet nicht", _calls() == "" and h.win == null)
	h.open_aus()
	ok("Kinder-Modus: kein «ins BIOS»", not _win_text(h).contains(T.t("Neu starten ins BIOS")) and _win_text(h).contains(T.t("Herunterfahren")))
	h.close()
	m.kids_on = false
	_clear()
	h.koppeln()
	ok("Controller koppeln: Wunsch «koppeln»", _calls() == "koppeln")

	# 8. alle Texte in allen Sprachen
	var src := FileAccess.get_file_as_string("res://scripts/hp_kiosk.gd")
	var rx := RegEx.new()
	rx.compile("T\\.t\\(\"((?:[^\"\\\\]|\\\\.)*)\"\\)")
	var n := 0
	for mt in rx.search_all(src):
		var de: String = mt.get_string(1)
		n += 1
		for lg in ["en", "fr", "it", "rm"]:
			var tr_: String = T.lookup(de, lg)
			if tr_ == "" or (tr_ == de and not de in ["Browser", "🌐 Browser"]):
				errs.append("Text ohne %s: %s" % [lg, de])
	ok("Texte gefunden (%d)" % n, n >= 30)
	ok("fold_card-Titel übersetzt", T.lookup("Simulator-PC", "en") != "")

	OS.execute("rm", ["-rf", dir])
	if errs.is_empty():
		print("HP-Kiosk-Test OK (%d Texte in 5 Sprachen)" % n)
		quit(0)
	else:
		printerr("SCRIPT ERROR: HP-Kiosk-Test (%d): " % errs.size() + " | ".join(errs.slice(0, 12)))
		quit(1)
