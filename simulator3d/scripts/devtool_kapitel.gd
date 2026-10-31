extends Node
## Entwicklertool 3 · Kapitel-Sprung (Daniel 31.10.2026): Kapitel bzw. Schritt wählen und dorthin springen - zum Testen,
## ohne alles durchzuspielen.
##   * Geschichte «Die Karte des Grossvaters» (bergtal_abenteuer.gd): Kapitel 1 … 5, Schritt Kapitel … Morgen. Ab «Unterwegs»
##     startet die Tour (fester Seed), «Nachtlager» = am Ziel angekommen, «Nacht» = Lager steht, «Morgen» = schnelle Nacht.
##   * Spielbereich (spielbereich.gd): Kapitel 1 … 4 offen (die davor als besucht) und hinein.
##   * Horror-Modus «Das Hospiz» (bergtal_horror.gd): Nacht 1 … 3 - NUR wenn Horror im laufenden Programm schon mit dem
##     Passwort entsperrt ist (horror.unlocked). Keine Umgehung: ohne Entsperren ist der Knopf aus, /control sagt «locked».
## Test-Spielstand: Abenteuer, Spielbereich und Entdeckungsbuch (Abzeichen) schreiben bis zum Neustart (oder «Test beenden»)
## in eigene Dateien (user://dev_test/…, save_file / save_path / use_file der drei Teile) - Daniels echter Spielstand bleibt
## unberührt; das Level des Tests wird nicht beim Spielstand gemerkt (Engine-Meta «dev_test», spielstand.gd remember_lv).
## Der Horror-Modus hat Passwort und Fortschritt in einer Datei: im Test schreibt er Fortschritt und Rätsel unter eigene
## Schlüssel («progress_test» / «raetsel_test», bergtal_horror.gd test_mode) - die echten Schlüssel aller Spielstände werden
## nie geschrieben; «Test beenden» (und Schliessen) löscht die Test-Schlüssel. Das Passwort wird nie angefasst.
## /control {"action": "dev", "do": "chapters" | "chapter" (area: abenteuer | spielbereich | horror, n, step) | "test_end"}

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")

const TEST_DIR := "user://dev_test"
const AB_TEST := "user://dev_test/bergtal_abenteuer_fortschritt.json"
const SB_TEST := "user://dev_test/spielbereich.json"
const ENT_TEST := "user://dev_test/entdecken.json"
const AREAS := [["abenteuer", "Geschichte «Die Karte des Grossvaters»"], ["spielbereich", "Spielbereich (Kapitel der Szenen)"],
		["horror", "Horror-Modus «Das Hospiz»"]]
const SEED := 4242                       # the same tour every time (like «Situation speichern»)

var x
var dev
var main
var test_on := false
var _scene0 := ""                        # the scene before the test (back there at the end: the play area counts a scene as visited)
var _horror_touched := false
var _horror_mem := {}                    # what the horror keeps in memory (chapter, choices, end, clips) - back at the end
var _area: OptionButton
var _n: OptionButton
var _step: OptionButton
var _go: Button
var _end: Button
var _lab: Label


# =============================================================================================================================
# what there is
# =============================================================================================================================
func _ab_steps() -> Array:
	var ab = main.abenteuer
	return ab.STEPS if ab != null else []


func chapters() -> Dictionary:
	var ab = main.abenteuer
	var sb = main.spielbereich
	var h = main.horror
	var out := {"test": test_on, "areas": []}
	if ab != null:
		var D = ab.D
		var chs := []
		for i in D.CHAPTERS.size():
			chs.append({"n": i + 1, "name": str(D.CHAPTERS[i].get("title", ""))})
		out["areas"].append({"id": "abenteuer", "chapters": chs, "steps": ab.STEPS, "now": {"chapter": ab.W["chapter"], "step": ab.step}})
	if sb != null:
		var chs2 := []
		for i in sb.CHAPTERS.size():
			chs2.append({"n": i + 1, "id": str(sb.CHAPTERS[i][0]), "name": str(sb.CHAPTERS[i][1])})
		out["areas"].append({"id": "spielbereich", "chapters": chs2, "steps": []})
	if h != null:
		out["areas"].append({"id": "horror", "chapters": [{"n": 1}, {"n": 2}, {"n": 3}], "steps": [], "unlocked": bool(h.unlocked),
				"note": "" if bool(h.unlocked) else "locked: first unlock with the password (Abenteuer → Stimmung → Horror)"})
	return out


func horror_ok() -> bool:
	var h = main.horror
	return h != null and bool(h.unlocked) and not bool(main.get("kids_on"))


# =============================================================================================================================
# the test state
# =============================================================================================================================
func _begin_test() -> void:
	if test_on:
		return
	test_on = true
	_scene0 = str(main.scene)
	DirAccess.make_dir_recursive_absolute(TEST_DIR)
	var ab = main.abenteuer
	if ab != null:
		ab.save_file = AB_TEST
	var sb = main.spielbereich
	if sb != null:
		sb.save_path = SB_TEST
	var en = main.entdecken
	if en != null and en.has_method("use_file"):
		en.save()                                                  # the real book as it is now ...
		var real: String = preload("res://scripts/spielstand.gd").path_ent()
		if FileAccess.file_exists(real):
			DirAccess.copy_absolute(real, ENT_TEST)                # ... and the test starts from a copy of it
		elif FileAccess.file_exists(ENT_TEST):
			DirAccess.remove_absolute(ENT_TEST)
		en.use_file(ENT_TEST)
	Engine.set_meta("dev_test", true)


func test_end() -> Dictionary:
	"""everything back to the real progress (the test files stay for the next test)"""
	if not test_on:
		return {"ok": true, "test": false}
	var ab = main.abenteuer
	if ab != null:
		_ab_stop_run()
		ab.save_file = preload("res://scripts/spielstand.gd").path_ab()   # A6: back to the active Spielstand (place 1 = SAVE_FILE)
		ab._load()
		ab.step = 0
		ab._changed()
	_horror_back()
	if _scene0 != "" and str(main.scene) != _scene0:
		main.set_scene(_scene0)          # (before the real file of the play area is used again)
	var sb = main.spielbereich
	if sb != null:
		sb.save_path = preload("res://scripts/spielstand.gd").path_sb()   # A6
		sb.data = {"visited": [], "seen_lv": 1, "greeted": false, "done_seen": []}
		sb._load()
	var en = main.entdecken
	if en != null and en.has_method("use_file"):
		en.save()                                                  # (into the test file)
		en.use_file(preload("res://scripts/spielstand.gd").path_ent())
	if Engine.has_meta("dev_test"):
		Engine.remove_meta("dev_test")
	test_on = false
	_paint()
	dev._say(T.t("Test beendet – wieder dein echter Spielstand."))
	return {"ok": true, "test": false}


func _horror_back() -> void:
	var h = main.horror
	if h == null or not _horror_touched:
		return
	if h.running:
		h.stop()
	h._store.erase("progress_test")                      # only the test keys: the real ones were never written
	h._store.erase("raetsel_test")
	h.test_mode = false
	h._save()
	for k in _horror_mem:
		h.set(k, _horror_mem[k])
	_horror_touched = false
	_horror_mem = {}


func _exit_tree() -> void:
	_horror_back()                       # the simulator closes during a test: the real horror progress back on disk


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		_horror_back()


func _ab_stop_run() -> void:
	var ab = main.abenteuer
	if ab == null or ab.R.is_empty():
		return
	if main.nacht != null and main.nacht.running and str(main.nacht.opts.get("by", "")) == "abenteuer":
		main.nacht.stop(false)
	ab._restore()
	ab.R = {}
	ab.leg = {}
	ab.fast = false
	ab.replaying = false


# =============================================================================================================================
# the jumps
# =============================================================================================================================
func jump(area: String, n: int, s := 0) -> Dictionary:
	if bool(main.get("kids_on")):
		return {"ok": false, "error": "kids"}
	match area:
		"abenteuer":
			return _jump_ab(n, s)
		"spielbereich":
			return _jump_sb(n)
		"horror":
			return _jump_horror(n)
	return {"ok": false, "error": "unknown area", "areas": ["abenteuer", "spielbereich", "horror"]}


func _jump_ab(n: int, s: int) -> Dictionary:
	var ab = main.abenteuer
	if ab == null:
		return {"ok": false, "error": "no adventure"}
	var D = ab.D
	n = clampi(n, 1, D.CHAPTERS.size())
	s = clampi(s, 0, ab.STEPS.size() - 1)
	var b: String = main.busy_with("Die Karte des Grossvaters")
	if b != "" and b != "Nacht-Testlauf":
		return {"ok": false, "error": "busy", "busy": b}
	_begin_test()
	_ab_stop_run()
	# the test progress: this chapter open, the level of this chapter (so its things can be packed), the map pieces before it
	var pieces := []                     # (chapter k has map piece k - 1; arriving also shows the next one)
	for i in range(n):
		pieces.append(i)
	ab.P = {"chapter": n, "xp": int(D.LEVEL_XP[mini(n - 1, D.LEVEL_XP.size() - 1)]), "stars": {}, "finds": [], "finale": false,
			"runs": [], "pieces": pieces, "test": true}
	ab._save()                           # (into the test file)
	ab.open_ab()
	ab.W["chapter"] = n
	ab.W["items"] = ab.blinki_suggest()
	ab.step = mini(s, 3)
	ab._changed()
	var out := {"ok": true, "area": "abenteuer", "chapter": n, "step": s}
	if s >= 4:
		var r: Dictionary = ab.op({"do": "start", "chapter": n, "seed": SEED})
		if ab.R.is_empty():
			return {"ok": false, "error": str(r.get("error", ab.error)), "state": ab.state()}
	if s >= 5:                           # at the goal: no walking, no question open
		ab.leg = {}
		ab.R["walking"] = false
		ab.R["pending"] = {}
		var ch: Dictionary = ab.chapter()
		var cp: Array = ch.get("camp", [])
		if cp.size() >= 3 and str(cp[0]) != "frei":
			ab.R["pos"] = Vector2(float(cp[1]), float(cp[2]))
		ab._arrive(false)
	if s >= 6:
		ab.set_camp("rucksack", false)
	if s >= 7:                           # the morning: a quick night
		ab.fast = true
		var rn: Dictionary = ab.start_night()
		out["night"] = rn
	out["state"] = ab.state()
	_paint()
	dev._say(T.t("Abenteuer: Kapitel %d · %s (Test-Spielstand)") % [n, T.t(str(ab.STEPS[s]))])
	return out


func _jump_sb(n: int) -> Dictionary:
	var sb = main.spielbereich
	if sb == null:
		return {"ok": false, "error": "no play area"}
	n = clampi(n, 1, sb.CHAPTERS.size())
	_begin_test()
	var vis := []
	for i in n:
		vis.append(str(sb.CHAPTERS[i][0]))
	sb.data = {"visited": vis, "seen_lv": int(sb.data.get("seen_lv", 1)), "greeted": true, "done_seen": []}
	sb.save()                            # (into the test file)
	var r: Dictionary = sb.start_adventure(str(sb.CHAPTERS[n - 1][0]))
	_paint()
	dev._say(T.t("Spielbereich: Kapitel %d (Test-Spielstand)") % n)
	return {"ok": bool(r.get("ok", false)), "area": "spielbereich", "chapter": n, "start": r}


func _jump_horror(n: int) -> Dictionary:
	if not horror_ok():
		return {"ok": false, "error": "locked", "msg": T.t("Horror ist gesperrt – zuerst mit dem Passwort entsperren (Abenteuer → Stimmung → Horror).")}
	var h = main.horror
	n = clampi(n, 1, 3)
	_begin_test()
	if not _horror_touched:
		_horror_touched = true
		_horror_mem = {"chapter": h.chapter, "choices": (h.choices as Dictionary).duplicate(true), "end_kind": h.end_kind,
				"clips": (h.clips as Array).duplicate()}
	h.test_mode = true
	var r: Dictionary = h.command({"do": "start", "chapter": n})
	_paint()
	dev._say(T.t("Horror: Nacht %d (Test)") % n)
	return {"ok": bool(r.get("ok", false)), "area": "horror", "chapter": n, "start": r}


# =============================================================================================================================
# the part of the window
# =============================================================================================================================
func build(v: VBoxContainer) -> void:
	var r1 := HBoxContainer.new()
	r1.add_theme_constant_override("separation", 6)
	v.add_child(r1)
	_area = OptionButton.new()
	for a in AREAS:
		_area.add_item(T.t(str(a[1])))
	_area.item_selected.connect(func(_i): _fill_opts())
	r1.add_child(_area)
	_n = OptionButton.new()
	r1.add_child(_n)
	_step = OptionButton.new()
	r1.add_child(_step)
	var r2 := HBoxContainer.new()
	r2.add_theme_constant_override("separation", 6)
	v.add_child(r2)
	_go = Button.new()
	_go.text = T.t("Hinspringen (Test-Spielstand)")
	UI.primary(_go)
	_go.pressed.connect(func():
		var r := jump(str(AREAS[_area.selected][0]), _n.selected + 1, _step.selected if _step.visible else 0)
		if not bool(r.get("ok", false)):
			dev._say(str(r.get("msg", T.t("Ging nicht: %s") % str(r.get("error", "?"))))))
	r2.add_child(_go)
	_end = Button.new()
	_end.text = T.t("Test beenden (echter Spielstand)")
	_end.pressed.connect(test_end)
	r2.add_child(_end)
	_lab = UI.small("", UI.MUT)
	_lab.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_lab.custom_minimum_size = Vector2(598, 0)
	v.add_child(_lab)
	_fill_opts()


func on_show(tab: String) -> void:
	if tab == "kapitel":
		_fill_opts()


func _fill_opts() -> void:
	if _n == null:
		return
	var a := str(AREAS[_area.selected][0])
	_n.clear()
	_step.clear()
	match a:
		"abenteuer":
			var ab = main.abenteuer
			if ab != null:
				for i in ab.D.CHAPTERS.size():
					_n.add_item(T.t(str(ab.D.CHAPTERS[i].get("title", ""))))
				for s in ab.STEPS:
					_step.add_item(T.t(str(s)))
		"spielbereich":
			var sb = main.spielbereich
			if sb != null:
				for i in sb.CHAPTERS.size():
					_n.add_item(T.t("Kapitel %d") % (i + 1) + " · " + T.t(str(sb.CHAPTERS[i][1])))
		"horror":
			for i in 3:
				_n.add_item(T.t("Nacht %d") % (i + 1))
	_step.visible = a == "abenteuer"
	_paint()


func _paint() -> void:
	if _lab == null:
		return
	var a := str(AREAS[_area.selected][0])
	var locked := a == "horror" and not horror_ok()
	_go.disabled = locked
	var t := ""
	if locked:
		t = T.t("Horror ist gesperrt – zuerst mit dem Passwort entsperren (Abenteuer → Stimmung → Horror).")
	elif test_on:
		t = T.t("Test-Spielstand aktiv – dein echter Spielstand bleibt unberührt (bis «Test beenden» oder Neustart).")
	else:
		t = T.t("Springen setzt einen Test-Spielstand (eigene Datei) – dein echter Spielstand bleibt unberührt.")
	_lab.text = t
	_lab.add_theme_color_override("font_color", UI.ORG if test_on or locked else UI.MUT)
	_end.disabled = not test_on


# =============================================================================================================================
# /control
# =============================================================================================================================
func control(d: Dictionary) -> Dictionary:
	match str(d.get("do", "")):
		"chapter":
			return jump(str(d.get("area", "abenteuer")), int(d.get("n", d.get("chapter", 1))), int(d.get("step", 0)))
		"test_end":
			return test_end()
	return chapters()
