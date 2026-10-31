extends SceneTree
## Test «Das Hospiz»: eine Regel für alle Wege (Code-Prüfung H1) und der Knopf «Ohne Passwort starten» (31.10.2026).
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/hospiz_test.gd"   (absoluter Pfad nötig)
## Nur mit einem eigenen Test-HOME laufen lassen: der Test legt in user:// ein Test-Passwort an (nie Daniels user://).
## Ohne Fenster und ohne Welt: ein kleines Ersatz-«main» (kids_on, start_info …); bergtal_horror.gd selbst ist echt.
## Ende: «Hospiz-Test OK» oder «SCRIPT ERROR: Hospiz-Test: …» (Exit-Code 0 / 1).

const PW := "test-hospiz-1234"         # nur im Test-HOME, nie Daniels Passwort

var errs := []


func ok(what: String, cond: bool) -> void:
	if not cond:
		errs.append(what)


func _fake_main() -> Node:
	var s := GDScript.new()
	s.source_code = """extends Node
var kids_on := false
var start_info := ""
var scene := "camping"
var vps := []
var th_preview = null
func set_scene(_s) -> bool:
	scene = _s
	return true
"""
	s.reload()
	var m := Node.new()
	m.set_script(s)
	return m


func _init() -> void:
	var data := OS.get_user_data_dir()
	if not (data.begins_with("/tmp/") or OS.get_environment("HOME").begins_with("/tmp/")):
		push_error("Hospiz-Test: nur mit einem Test-HOME unter /tmp (jetzt: %s)" % data)
		quit(1)
		return
	DirAccess.remove_absolute(data.path_join("bergtal_horror.json"))
	var m := _fake_main()
	root.add_child(m)
	var H = load("res://scripts/bergtal_horror.gd")
	var h = H.new()
	h.main = m
	m.add_child(h)                        # _ready: load user://bergtal_horror.json (missing = no password yet)
	ok("set_password", bool(h.set_password(PW)["ok"]))
	var hash0 := str(h._store.get("hash", ""))
	var salt0 := str(h._store.get("salt", ""))
	# the state after a restart: password set, locked
	h.command({"do": "sperren"})
	ok("gesperrt nach sperren", not h.unlocked and not h.may_play())

	# 1. the old way around the password (H1: «Weiterspielen» -> common start -> neu_beginnen) - now refused
	h.neu_beginnen()
	ok("neu_beginnen ohne Passwort zeigt die Passwort-Abfrage (phase %s)" % h.phase, h.phase == "lock")
	h.weiter()
	ok("weiter ohne Passwort zeigt die Passwort-Abfrage (phase %s)" % h.phase, h.phase == "lock")
	h._show_warn()
	ok("Warnung nicht ohne Passwort (phase %s)" % h.phase, h.phase == "lock")
	h._show_start()
	ok("Startbild nicht ohne Passwort (phase %s)" % h.phase, h.phase == "lock")
	h.begin(1)
	ok("begin ohne Passwort startet nicht", not h.running and h.phase == "lock")
	ok("/control start ohne Passwort", str(h.command({"do": "start", "chapter": 1}).get("error", "")) == "locked")
	ok("nichts gestartet", not h.running and not h._store.has(h._pk()))

	# 2. «ohne Passwort» over /control: only with the mark of net.gd (this PC)
	ok("ohne_passwort ohne _von_lokal", str(h.command({"do": "ohne_passwort"}).get("error", "")) == "nur_lokal" and not h.unlocked)

	# 3. children's mode: never - not the button, not /control from this PC, no start
	m.kids_on = true
	ok("Kinder-Modus: kein Knopf", not h.knopf_erlaubt())
	ok("Kinder-Modus: ohne_passwort", str(h.ohne_passwort().get("error", "")) == "kids" and not h.unlocked)
	ok("Kinder-Modus: /control lokal", str(h.command({"do": "ohne_passwort", "_von_lokal": true}).get("error", "")) == "kids")
	h.phase = ""
	h._clear_card()
	h.open()
	ok("Kinder-Modus: keine Passwort-Abfrage", h.phase == "")
	m.kids_on = false

	# 4. the button (at this PC): unlocked until the restart, password / hash unchanged, warning first, then the dedication
	h.command({"do": "open"})
	ok("Passwort-Dialog", h.phase == "lock")
	h._do_ohne_pw()
	ok("Knopf entsperrt", h.unlocked and h.unlock_via == "knopf" and h.may_play())
	ok("nach dem Knopf kommt die Warnung (phase %s)" % h.phase, h.phase == "warn")
	ok("Hash unverändert", str(h._store.get("hash", "")) == hash0 and str(h._store.get("salt", "")) == salt0 and h.has_password())
	var f := FileAccess.get_file_as_string(data.path_join("bergtal_horror.json"))
	ok("Datei: Hash unverändert", f.find(hash0) >= 0 and f.find(PW) < 0)
	h._show_start()
	ok("Startbild mit Widmung", h.phase == "start" and _has_text(h._card, "Für die Mutigste."))
	m.kids_on = true
	ok("Kinder-Modus sperrt auch nach dem Knopf", not h.may_play() and str(h.command({"do": "start"}).get("error", "")) == "kids")
	m.kids_on = false

	# 5. the password still works as before
	h.command({"do": "sperren"})
	ok("falsches Passwort", not bool(h.unlock("falsch")["ok"]) and not h.unlocked)
	ok("richtiges Passwort", bool(h.unlock(PW)["ok"]) and h.unlock_via == "pw" and h.may_play())

	DirAccess.remove_absolute(data.path_join("bergtal_horror.json"))
	if errs.is_empty():
		print("Hospiz-Test OK")
		quit(0)
	else:
		push_error("Hospiz-Test: " + " · ".join(errs))
		quit(1)


func _has_text(n: Node, t: String) -> bool:
	if n == null:
		return false
	if n is Label and (n as Label).text == t:
		return true
	for c in n.get_children():
		if _has_text(c, t):
			return true
	return false
