extends Node
## Paket «Werksrücksetzung im Simulator» (Daniel 31.10.2026): «⚠ Auf Werkseinstellungen zurücksetzen …» wie in MoveEye
## (quelle/586_guide2.py factory_reset, 516 g2Factory, 585 _g2_tk_factory, Texte 633). Ort: Karte «Mehr» (MoveEye: Mehr →
## System), nur für den Besitzer (devtool.is_owner: nicht im Kinder-Modus - dieselbe Prüfung wie das Entwickler-Fenster).
## Ablauf wie MoveEye: Fenster mit «Zurück auf die Werkseinstellungen / Das bleibt / Das wird gelöscht», zum Bestätigen
## «ZURÜCKSETZEN» (andere Sprachen «RESET») eintippen, «Jetzt zurücksetzen»:
##   1. Kopie: alles, was gelöscht wird (Einstellungen und Spielstände), nach user://werk_kopie/<datum>/ (gleiche Pfade);
##      ohne Kopie: Zwischenspeicher, Protokoll, Aufnahmen / Fotos, Handy-Browser (wie MoveEye: die Aufnahmen ohne Kopie).
##   2. Merker user://werk_reset.json, dann Neustart (wie nach einem Update: restart_args, release_ports, --old-pid).
##   3. Der neue Simulator löscht ganz am Anfang von main._ready (apply_pending), BEVOR ein Teil eine Datei liest - und erst
##      wenn der alte Simulator beendet ist (sonst schreibt er beim Beenden wieder Dateien). Danach startet er wie beim ersten
##      Start (Standardwerte, Rundgang mit Blinki von selbst, Neuigkeiten).
## Was BLEIBT (Daniels Entscheid): KEEP unten - Horror-Passwort (nur Hash/Salz, der Fortschritt der Nacht geht), Sprache, heruntergeladene
## Inhalte (Figuren-Paket, Fotos-Oberflächen/CC0/Texturen, Karten-Zwischenspeicher, MoveEye auf diesem PC), Entwickler-Notizen,
## Kontaktbogen, Spieltest- und Prüfdaten. Alles andere in user:// wird gelöscht. Eine «Kopie wiederherstellen» gibt es nicht
## (MoveEye hat auch keine - dort: Kopie herunterladen); das Fenster zeigt die Kopien und öffnet den Ordner.
## Test: /control {"action": "werk", "do": "info"} · {"do": "open"} · {"do": "reset", "confirm": true} (nur mit confirm).

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const MARK := "user://werk_reset.json"
const COPY_DIR := "user://werk_kopie"
const HORROR := "bergtal_horror.json"                 # (= bergtal_horror.gd FILE)
const HORROR_KEEP := ["hash", "salt", "iter", "v"]     # the password only; progress / strength / restore are the game
const WORDS_S := "ZURÜCKSETZEN_ZURUECKSETZEN_RESET_RÉINITIALISER_REINITIALISER_RIPRISTINA_RESETTAR"   # = MoveEye FACTORY_WORDS (not translated)

# what stays: path relative to user:// ("/" at the end = the whole folder) - why: the comment
const KEEP := [
	"bergtal_horror.json",               # Horror-Passwort (Hash)
	"simulator_sprache.json",            # die gewählte Sprache (i18n.gd CHOICE_FILE) - MoveEye behält die Sprache auch
	"figuren_v1.zip",                    # Figuren-Paket (heruntergeladen, figur_paket.gd PACK)
	"inhalte/",                          # Fotos-Oberflächen, CC0-Texturen, Himmel (heruntergeladen, inhalte.gd)
	"vorlagen/",                         # eigene 3D-Modelle (templates.gd)
	"orte/cache/",                       # Karten-Daten der Orte (heruntergeladen, geo.gd)
	"motionwatch_pc/",                   # MoveEye auf diesem PC (heruntergeladenes Programm, mwpc.gd)
	"autologon/",                        # Autologon-Programm von Microsoft (heruntergeladen, autostart.gd)
	"trainingsbilder/",                  # KI-Trainingsbilder (dataset.gd, kidaten.gd)
	"dev_notizen/",                      # Entwickler-Notizen
	"dev_notizen_export/",               # Entwickler-Notizen (ZIP)
	"kontaktbogen/",                     # Kontaktbogen
	"spieltest/",                        # Spieltest-Daten
	"dev_test/",                         # Kapitel-Tests des Entwickler-Fensters (devtool_kapitel.gd)
	"pruefstand/schluessel.txt",         # Prüfstand: Schlüssel zum Hochladen
	"pruefstand/faelle/",                # Prüfstand: aufgenommene Fälle
	"pruefstand/wege_gesendet.json",     # Prüfstand: schon gesendete Schleichwege
	"testlauf/",                         # Ergebnisse der Testläufe (testrun.gd)
	"einbruch/",                         # Ergebnisse der Einbruch-Abläufe
	"nachttest/",                        # Ergebnisse der Nacht-Testläufe
	"feedback_outbox.json",              # noch nicht gesendete Rückmeldungen
	"feedback_shots/",                   # Bilder der Rückmeldungen
	"logs/godot.log",                    # das laufende Protokoll
	"shader_cache/",                     # Grafik-Zwischenspeicher von Godot
	"vulkan/",                           # Grafik-Zwischenspeicher von Godot
	"werk_kopie/",                       # die Kopien vor dem Zurücksetzen
	"werk_reset.json",                   # (Merker während des Neustarts)
]
# deleted without a copy (caches, log, recordings and photos - MoveEye deletes those too, without a copy)
const NO_COPY := ["logs/", "update.zip", "handy_browser/", "mehr_shots/", "localplay_debug.png", "figur_shot.png", "aufnahmen/",
		"Fotos/", "aufgaben/", "orte/3d_gebaeude_bericht.txt"]

var main
var mehr
var busy := false
var _word: LineEdit
var _go: Button
var _err: Label


func _ready() -> void:
	if Engine.has_meta("werk_done"):                    # the start right after a reset: say so once
		var r: Dictionary = Engine.get_meta("werk_done")
		get_tree().create_timer(3.0).timeout.connect(func():
			if mehr != null:
				mehr.toast(T.t("Zurückgesetzt.") + " " + T.t("Kopie der alten Einstellungen:") + " " + str(r.get("copy", "")))
				if mehr.protokoll != null:
					mehr.protokoll.add("info", "Werkseinstellungen: %d Dateien gelöscht, Kopie %s" % [int(r.get("deleted", 0)), str(r.get("copy", ""))]))


static func is_owner(m) -> bool:
	return preload("res://scripts/devtool.gd").is_owner(m)


# =============================================================================================================================
# which file stays, which goes
# =============================================================================================================================
static func keep_reason(rel: String) -> String:
	"""the rule of KEEP that keeps rel, '' = deleted"""
	for k in KEEP:
		if rel == k or (k.ends_with("/") and rel.begins_with(k)):
			return k
	return ""


static func _no_copy(rel: String) -> bool:
	if rel.ends_with(".part"):
		return true
	for k in NO_COPY:
		if rel == k or (k.ends_with("/") and rel.begins_with(k)):
			return true
	return false


static func _walk(rel: String, out: Array) -> void:
	"""all files below user://<rel> (relative paths, also hidden ones like spiel/<runde>/.gesendet)"""
	var d := DirAccess.open("user://" + rel)
	if d == null:
		return
	d.include_hidden = true
	d.include_navigational = false
	for f in d.get_files():
		out.append(rel + f)
	for s in d.get_directories():
		if d.is_link(s):
			continue                                    # never follow a link out of user://
		_walk(rel + s + "/", out)


static func plan() -> Dictionary:
	"""{keep: [rel], delete: [rel], horror: bool} - what a reset would do now"""
	var all := []
	_walk("", all)
	var keep := []
	var dele := []
	for r in all:
		if keep_reason(r) != "":
			keep.append(r)
		else:
			dele.append(r)
	return {"keep": keep, "delete": dele}


static func _safe_root() -> bool:
	"""only inside the user folder of the simulator (…/MoveEye Sim 3D) - never the home folder or the root"""
	var u := OS.get_user_data_dir().replace("\\", "/").trim_suffix("/")
	var home := (OS.get_environment("USERPROFILE") if OS.get_name() == "Windows" else OS.get_environment("HOME")).replace("\\", "/").trim_suffix("/")
	return u != "" and u.count("/") >= 2 and u != home and u.to_lower().contains("sim")


# =============================================================================================================================
# 1. the copy, 2. the mark and the restart (the running simulator)
# =============================================================================================================================
static func copies() -> Array:
	"""[{name, n}] newest first, at most 10 (like MoveEye factory_backups)"""
	var out := []
	var d := DirAccess.open(COPY_DIR)
	if d == null:
		return out
	var names := Array(d.get_directories())
	names.sort()
	names.reverse()
	for n in names.slice(0, 10):
		var fs := []
		_walk("werk_kopie/" + n + "/", fs)
		out.append({"name": n, "n": fs.size(), "path": ProjectSettings.globalize_path(COPY_DIR + "/" + n)})
	return out


func make_copy() -> Dictionary:
	var stamp := Time.get_datetime_string_from_system(false, false).replace(":", "-").replace("T", "_")
	var base := COPY_DIR + "/" + stamp
	var p := plan()
	var n := 0
	var fails := 0
	for r in p["delete"] + [HORROR]:
		if _no_copy(r) or not FileAccess.file_exists("user://" + r):
			continue
		var to: String = base + "/" + r
		DirAccess.make_dir_recursive_absolute(to.get_base_dir())
		if DirAccess.copy_absolute("user://" + r, to) == OK:
			n += 1
		else:
			fails += 1
	if fails > 0:
		return {"ok": false, "error": T.t("Die Kopie konnte nicht ganz geschrieben werden (%d Dateien fehlen).") % fails, "copy": stamp}
	return {"ok": true, "copy": stamp, "n": n, "path": ProjectSettings.globalize_path(base)}


func start_reset(who := "Fenster") -> Dictionary:
	if not is_owner(main):
		return {"ok": false, "error": T.t("Nur für den Besitzer – nicht im Kinder-Modus.")}
	if busy:
		return {"ok": false, "error": "busy"}
	if not _safe_root():
		return {"ok": false, "error": "unsafe_user_dir", "dir": OS.get_user_data_dir()}
	busy = true
	if main.has_method("_save_settings"):
		main._save_settings()                           # the copy has the settings as they are now
	var c := make_copy()
	if not bool(c["ok"]):
		busy = false
		return c
	var f := FileAccess.open(MARK, FileAccess.WRITE)
	if f == null:
		busy = false
		return {"ok": false, "error": "could not write the mark", "file": MARK}
	f.store_string(JSON.stringify({"copy": c["copy"], "pid": OS.get_process_id(), "who": who, "t": Time.get_unix_time_from_system()}))
	f.close()
	print("factory reset (%s): copy %s (%d files), restarting" % [who, c["copy"], int(c["n"])])
	get_tree().create_timer(1.2).timeout.connect(_restart)
	return {"ok": true, "copy": c["copy"], "copied": c["n"], "path": c["path"], "restart": true,
			"delete": (plan()["delete"] as Array).size()}


func _restart() -> void:
	var a := OS.get_cmdline_args()
	a.append("--")
	var ua: PackedStringArray = main.restart_args() if main.has_method("restart_args") else OS.get_cmdline_user_args()
	var i := 0
	while i < ua.size():                                # like the first start: the default scene
		if ua[i] == "--scene" or ua[i] == "--hour":
			i += 2
			continue
		a.append(ua[i])
		i += 1
	if main.has_method("release_ports"):
		main.release_ports()
	var pid := OS.create_process(OS.get_executable_path(), a)
	if pid <= 0:
		busy = false
		if mehr != null:
			mehr.toast(T.t("Bitte den Simulator neu starten – das Zurücksetzen geschieht beim nächsten Start."))
		return
	get_tree().quit()


# =============================================================================================================================
# 3. the new simulator: delete, right at the start (main._ready, before anything reads a file)
# =============================================================================================================================
static func apply_pending() -> Dictionary:
	if not FileAccess.file_exists(MARK):
		return {}
	var m = JSON.parse_string(FileAccess.get_file_as_string(MARK))
	if typeof(m) != TYPE_DICTIONARY:
		m = {}
	if not _safe_root():
		printerr("factory reset: user folder looks wrong, nothing deleted: ", OS.get_user_data_dir())
		DirAccess.remove_absolute(MARK)
		return {}
	var op := int(m.get("pid", 0))                      # the old simulator first has to be gone (it writes files when closing)
	if op > 0 and op != OS.get_process_id():
		var t0 := Time.get_ticks_msec()
		while OS.is_process_running(op) and Time.get_ticks_msec() - t0 < 10000:
			OS.delay_msec(100)
		if OS.is_process_running(op):
			OS.kill(op)
			OS.delay_msec(500)
	var p := plan()
	var n := 0
	for r in p["delete"]:
		if DirAccess.remove_absolute("user://" + r) == OK:
			n += 1
	_rm_empty_dirs("")
	if FileAccess.file_exists("user://" + HORROR):       # the horror: only the password stays
		var h = JSON.parse_string(FileAccess.get_file_as_string("user://" + HORROR))
		var k := {}
		if typeof(h) == TYPE_DICTIONARY:
			for x in HORROR_KEEP:
				if h.has(x):
					k[x] = h[x]
		if k.has("hash"):
			var f := FileAccess.open("user://" + HORROR, FileAccess.WRITE)
			if f != null:
				f.store_string(JSON.stringify(k))
				f.close()
		else:
			DirAccess.remove_absolute("user://" + HORROR)
	DirAccess.remove_absolute(MARK)
	var res := {"copy": str(m.get("copy", "")), "deleted": n, "left": (p["delete"] as Array).size() - n}
	print("factory reset done: %d files deleted (%d could not), copy werk_kopie/%s" % [n, int(res["left"]), res["copy"]])
	Engine.set_meta("werk_done", res)
	return res


static func _rm_empty_dirs(rel: String) -> bool:
	"""removes empty folders below user://<rel>; true = this one is empty now"""
	var d := DirAccess.open("user://" + rel)
	if d == null:
		return false
	d.include_hidden = true
	var empty := d.get_files().size() == 0
	for s in d.get_directories():
		if d.is_link(s):
			empty = false
			continue
		if _rm_empty_dirs(rel + s + "/") and keep_reason(rel + s + "/") == "" and DirAccess.remove_absolute("user://" + rel + s) == OK:
			continue
		empty = false
	return empty


# =============================================================================================================================
# the window (the look of MoveEye 516 g2Factory: three sections, the word, «Jetzt zurücksetzen» red)
# =============================================================================================================================
func word() -> String:
	var w := WORDS_S.split("_")
	return w[0] if T.lang() == "de" else w[2]


func open() -> void:
	if not is_owner(main):
		if mehr != null:
			mehr.toast(T.t("Nur für den Besitzer – nicht im Kinder-Modus."))
		return
	var b: VBoxContainer = mehr._window("⚠ " + T.t("Auf Werkseinstellungen zurücksetzen"), "trash")
	mehr.win_id = "werk"
	for s in [[T.t("Zurück auf die Werkseinstellungen:"), T.t("alle Einstellungen und Regler, die Fensteranordnung, die Controller-Rollen, der Zuhause-Bausatz, der Echt-Abgleich, die Sprache (wieder wie MoveEye)"), UI.TXT],
			[T.t("Das bleibt:"), T.t("das Horror-Passwort, die Sprache, heruntergeladene Inhalte (Figuren, CC0-Fotos und Texturen, Karten, MoveEye auf diesem PC), eigene 3D-Modelle, Entwickler-Notizen, Kontaktbogen, Spieltest- und Prüfstand-Daten"), UI.GRN],
			[T.t("Das wird gelöscht:"), T.t("alle Spielstände (Abenteuer 1–3, Maggie, Spielbereich, Level, Abzeichen, Entdeckungsbuch), die Ranglisten, Aufnahmen und Fotos und alles Weitere im Benutzerordner"), UI.RED]]:
		var h := Label.new()
		h.text = s[0]
		h.add_theme_font_override("font", UI.heading_font())
		h.add_theme_font_size_override("font_size", 14)
		h.add_theme_color_override("font_color", s[2])
		b.add_child(h)
		var l := UI.small(s[1])
		l.custom_minimum_size = Vector2(480, 0)
		b.add_child(l)
	var c := UI.small(T.t("Zuerst wird eine Kopie der alten Einstellungen und Spielstände gespeichert (Benutzerordner → werk_kopie). Danach startet der Simulator neu wie beim ersten Start."), UI.TXT)
	c.custom_minimum_size = Vector2(480, 0)
	b.add_child(c)
	var wl := UI.small(T.t("Zum Bestätigen {w} eintippen", {"w": "«" + word() + "»"}), UI.TXT)
	b.add_child(wl)
	_word = LineEdit.new()
	_word.placeholder_text = word()
	_word.text_changed.connect(func(_t): _paint())
	_word.text_submitted.connect(func(_t): _do())
	b.add_child(_word)
	_err = UI.small("", UI.RED)
	b.add_child(_err)
	var bt := HBoxContainer.new()
	bt.add_theme_constant_override("separation", 8)
	bt.alignment = BoxContainer.ALIGNMENT_END
	b.add_child(bt)
	var cl := Button.new()
	cl.text = T.t("Schliessen")
	cl.pressed.connect(mehr.close_window)
	bt.add_child(cl)
	_go = Button.new()
	_go.text = T.t("Jetzt zurücksetzen")
	for st in ["normal", "hover", "pressed"]:
		_go.add_theme_stylebox_override(st, UI.box(UI.RED if st != "hover" else UI.RED.lightened(0.1), UI.RED))
	_go.add_theme_stylebox_override("disabled", UI.box(UI.RED.darkened(0.55), UI.RED.darkened(0.55)))
	_go.add_theme_color_override("font_color", Color.WHITE)
	_go.add_theme_color_override("font_disabled_color", Color(1, 1, 1, 0.5))
	_go.pressed.connect(_do)
	bt.add_child(_go)
	var cp := copies()
	if not cp.is_empty():
		b.add_child(UI.small(T.t("Kopien der alten Einstellungen") + ":", UI.TXT))
		var tx := []
		for x in cp.slice(0, 5):
			tx.append("%s  (%d)" % [x["name"], int(x["n"])])
		b.add_child(UI.small("\n".join(tx)))
		var of := Button.new()
		of.text = T.t("Ordner öffnen")
		of.pressed.connect(func(): OS.shell_open(ProjectSettings.globalize_path(COPY_DIR)))
		var oh := HBoxContainer.new()
		oh.add_child(of)
		b.add_child(oh)
	_paint()
	_word.grab_focus.call_deferred()


func word_ok(w: String) -> bool:
	return w.strip_edges().to_upper() in WORDS_S.split("_")


func _paint() -> void:
	if _go != null and is_instance_valid(_go):
		_go.disabled = busy or not word_ok(_word.text)


func _do() -> void:
	if _word == null or not word_ok(_word.text):
		if _err != null:
			_err.text = "⚠ " + T.t("Zum Bestätigen {w} eintippen", {"w": "«" + word() + "»"})
		return
	var r := start_reset("Fenster")
	if not bool(r["ok"]):
		_err.text = "⚠ " + str(r.get("error", ""))
		_paint()
		return
	_go.disabled = true
	_word.editable = false
	_err.add_theme_color_override("font_color", UI.GRN)
	_err.text = "✓ " + T.t("Kopie der alten Einstellungen:") + " werk_kopie/" + str(r["copy"]) + "\n" + T.t("Der Simulator startet neu …")


# =============================================================================================================================
# /control {"action": "werk", "do": info | open | close | reset (confirm: true)}
# =============================================================================================================================
func control(d: Dictionary) -> Dictionary:
	var dd := str(d.get("do", "info"))
	match dd:
		"open":
			open()
			return {"ok": is_owner(main), "open": mehr.win_id == "werk"}
		"close":
			if mehr.win_id == "werk":
				mehr.close_window()
			return {"ok": true}
		"reset":
			if d.get("confirm", false) != true:
				return {"ok": false, "error": "only with \"confirm\": true"}
			return start_reset("control")
		"info":
			var p := plan()
			var keep := {}
			for r in p["keep"]:
				keep[r] = keep_reason(r)
			return {"ok": true, "owner": is_owner(main), "word": word(), "keep": keep, "delete": p["delete"], "copies": copies(),
					"dir": OS.get_user_data_dir(), "safe": _safe_root()}
	return {"ok": false, "error": "do: info | open | close | reset (confirm: true)"}
