extends SceneTree
## Test «Spielton» (klang.gd) ohne Bild, mit der echten Welt (main.tscn):
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/spielton_test.gd" -- --no-update --no-tour --port 9449
## Prüft: alle Skripte laden (Parse), die Dateien klang/sp_*.ogg (Länge, Schleifen), die Busse Musik / Effekte / Umgebung /
## UI (→ Master) und den Begrenzer auf Master, die Regler (Lautstärke 0 / Musik aus / «Ton am PC» aus = stumm), dass im
## Überwachungsmodus (Start, kein Spiel) und bei einem Testlauf nichts erklingt (keine Momente, keine Musik, keine Klicks,
## Umgebung wie bisher auf Master) und dass im Spiel (Entdecken) die Auslöser wirken: Fund, Fanfare (auch über den Haken
## spieltest.gd), Kapitel, Tusch, Erwischt, Donner, Spannung (Puls / Wirbel), Musik ein und bei Spannung leiser, Klicks.
## Ende: «Spielton-Test OK» oder «SCRIPT ERROR: Spielton-Test: …» (Exit-Code 0 / 1).

var errs := []
var m = null
var K = null


func _init() -> void:
	_start.call_deferred()


func _warte(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func _f(t: String) -> void:
	errs.append(t)


func _hat(art: String, seit: float) -> bool:
	for e in K.log_:
		if float(e[0]) >= seit and str(e[1]) == art:
			return true
	return false


func _start() -> void:
	# 1. parse: every script of the simulator loads
	var n := 0
	for f in DirAccess.get_files_at("res://scripts"):
		if f.ends_with(".gd"):
			var s = load("res://scripts/" + f)
			n += 1
			if s == null or not (s as GDScript).can_instantiate():
				_f("Skript lädt nicht: " + f)
	print("Skripte geladen: %d" % n)
	# 2. the files
	var info = JSON.parse_string(FileAccess.get_file_as_string("res://klang/spielton.json"))
	if not info is Dictionary or (info as Dictionary).size() < 18:
		_f("klang/spielton.json fehlt oder unvollständig")
		info = {}
	for nm in info:
		var p: String = "res://klang/sp_%s.ogg" % nm
		if not FileAccess.file_exists(p):
			_f("Datei fehlt: " + p)
			continue
		var o := AudioStreamOggVorbis.load_from_buffer(FileAccess.get_file_as_bytes(p))
		if o == null or o.get_length() < 0.05:
			_f("Datei leer: " + p)
		if bool(info[nm].get("loop", false)) != (nm.begins_with("musik_") or nm in ["wirbel", "puls", "feuer"]):
			_f("Schleife falsch: " + nm)
	# 3. the world
	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in range(90):
		await process_frame
	await _warte(1.5)
	K = m.klang
	if K == null:
		_f("main.klang fehlt")
		_ende()
		return
	var Kl = load("res://scripts/klang.gd")
	for b in ["Musik", "Effekte", "Umgebung", "UI"]:
		var i := AudioServer.get_bus_index(b)
		if i < 0:
			_f("Bus fehlt: " + b)
		elif AudioServer.get_bus_send(i) != AudioServer.get_bus_name(0):
			_f("Bus %s geht nicht auf Master" % b)
	var lim := false
	for e in range(AudioServer.get_bus_effect_count(0)):
		if AudioServer.get_bus_effect(0, e) is AudioEffectHardLimiter:
			lim = true
	if not lim:
		_f("kein Begrenzer auf Master")
	var ids := []
	for c in m.controls:
		ids.append(str(c["id"]))
	for id in ["st_musik", "st_vol_musik", "st_vol_eff", "st_vol_umg", "st_vol_ui"]:
		if not id in ids:
			_f("Regler fehlt: " + id)
	# 4. surveillance (start, no game): nothing
	await _warte(0.6)
	if K.kontext != "":
		_f("Start: Kontext «%s» statt still" % K.kontext)
	var t0: float = K._t
	for fn in ["fund", "raetsel", "kapitel", "tusch", "erwischt"]:
		if bool(Kl.call(fn)):
			_f("Überwachung: %s spielt" % fn)
	if Kl.donner(900.0):
		_f("Überwachung: Donner spielt")
	Kl.gefahr("test", 1.0, 3.0)
	var b0 := Button.new()
	root.add_child(b0)
	await process_frame
	b0.pressed.emit()
	await _warte(1.2)
	for e in K.log_:
		if float(e[0]) >= t0 and not str(e[1]).begins_with("kontext"):
			_f("Überwachung: Ton «%s»" % str(e[1]))
	if K.spannung() > 0.01 or (K._mus[0] as AudioStreamPlayer).playing or (K._mus[1] as AudioStreamPlayer).playing:
		_f("Überwachung: Spannung / Musik läuft")
	for k in m.mikro._players:
		if str((m.mikro._players[k] as AudioStreamPlayer).bus) != "Master":
			_f("Überwachung: Umgebung %s nicht auf Master" % k)
	if not Kl.echt(m, "wind").is_empty():
		_f("Überwachung: echte Aufnahme statt Synthese")
	# 5. a game: «Entdecken» at the current place
	var t_sp: float = K._t
	m.control({"action": "spielton", "do": "erleben", "id": str(m.scene)})
	await _warte(0.8)
	if K.kontext != "erleben":
		_f("Entdecken: Kontext «%s»" % K.kontext)
	t0 = K._t
	if not Kl.fund():
		_f("Spiel: Fund spielt nicht")
	await _warte(2.0)
	load("res://scripts/spieltest.gd").ereignis("maggie", "fortschritt", {"raetsel": "test"})
	if not _hat("raetsel", t0):
		_f("Spiel: Rätsel über spieltest.gd ohne Fanfare")
	await _warte(2.0)
	if not Kl.kapitel():
		_f("Spiel: Kapitel spielt nicht")
	await _warte(2.0)
	if not Kl.tusch():
		_f("Spiel: Tusch spielt nicht")
	if not Kl.donner(1200.0):
		_f("Spiel: Donner spielt nicht")
	await _warte(4.0)
	var mus: String = K.info()["musik"]
	if not mus.begins_with("musik_") or not _hat("musik:" + mus, t_sp):
		_f("Spiel: keine Begleitmusik (%s)" % mus)
	var g0: float = K._mus_g[K._mus_i]
	Kl.gefahr("test", 1.0, 6.0)
	await _warte(2.5)
	if K.spannung() < 0.5 or not _hat("puls", t0) or not _hat("wirbel", t0):
		_f("Spiel: Spannung wirkt nicht (%.2f)" % K.spannung())
	if K._mus_g[K._mus_i] > g0 * 0.8:
		_f("Spiel: Musik bei Spannung nicht leiser (%.2f → %.2f)" % [g0, K._mus_g[K._mus_i]])
	if not Kl.erwischt() or K.spannung() > 0.01:
		_f("Spiel: Erwischt (Paukenschlag) wirkt nicht")
	var b1 := Button.new()
	root.add_child(b1)
	await process_frame
	b1.pressed.emit()
	if not _hat("ui_klick", t0):
		_f("Spiel: kein Menü-Klick")
	if Kl.echt(m, "wind").is_empty() or str(Kl.echt(m, "wind")[2]) != "Umgebung":
		_f("Spiel: Wind nicht auf «Umgebung»")
	# 6. the controls
	K.setze_vol("Musik", 0.0)
	if not AudioServer.is_bus_mute(AudioServer.get_bus_index("Musik")):
		_f("Regler Musik 0: nicht stumm")
	K.setze_vol("Musik", 35.0)
	K.musik_an = false
	K._pegel()
	if not AudioServer.is_bus_mute(AudioServer.get_bus_index("Musik")):
		_f("Musik aus: nicht stumm")
	K.musik_an = true
	m.mikro.pc_on = false
	K._pegel()
	for b in ["Musik", "Effekte", "Umgebung", "UI"]:
		if not AudioServer.is_bus_mute(AudioServer.get_bus_index(b)):
			_f("Ton am PC aus: %s nicht stumm" % b)
	if Kl.fund():
		_f("Ton am PC aus: Fund spielt")
	m.mikro.pc_on = true
	K._pegel()
	# 7. a task of MoveEye (a drill, a protection test …) or a «solo» scene of the test bench during the game: still again
	for fall in ["MoveEye-Aufgabe", "allein (Prüfstand)"]:
		if fall == "MoveEye-Aufgabe":
			m.mw["simtask_de"] = "Schutz-Test"
			m.mw_t = m.now()
		else:
			m.welt_solo = true
		await _warte(0.6)
		if K.kontext != "":
			_f("%s: Kontext «%s» statt still" % [fall, K.kontext])
		if Kl.fund():
			_f("%s: Fund spielt" % fall)
		for i in range(6):                                  # (the MoveEye task lasts while MoveEye answers: keep it fresh)
			m.mw_t = m.now()
			await _warte(0.5)
		if (K._mus[0] as AudioStreamPlayer).playing or (K._mus[1] as AudioStreamPlayer).playing:
			_f("%s: Musik spielt weiter" % fall)
		m.mw.erase("simtask_de")
		m.welt_solo = false
		await _warte(0.6)
	print("Spielton: %s" % JSON.stringify(K.info()))
	_ende()


func _ende() -> void:
	if errs.is_empty():
		print("Spielton-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Spielton-Test: " + str(e))
		quit(1)
