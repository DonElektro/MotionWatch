extends SceneTree
## «Die Karte des Grossvaters»: Kapitel um Kapitel (22.11.2026), mit der echten Welt, ohne Bild:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/kit_kette_test.gd" -- --no-update --no-tour
## * die Adresse der Startseiten-Kachel: ?grossvater=1 (Kapitelwähler), ?grossvater=1&kapitel=N (gleich Kapitel N)
## * ohne gespeicherten Helden zuerst die Heldenwahl, dann der Wähler: «Ganzes Spiel ab Kapitel 1» + nur die fertigen Kapitel
## * die Kette: Ende Kapitel 1 → (5 s) Kapitel 2 → («Weiter») Kapitel 3 → (5 s) Kapitel 4 → «Fortsetzung folgt»; Held,
##   Name und Rucksack bleiben; «Zurück zum Menü»; der Steuerbefehl {"action":"kit","do":"grossvater","kapitel":N}
## Ende: «Kette-Test OK» oder «SCRIPT ERROR: Kette-Test: …».

const KA = preload("res://scripts/kit_abenteuer.gd")
const WEB = preload("res://scripts/web.gd")
const SS = preload("res://scripts/spielstand.gd")

var errs: Array = []
var m = null
var k = null


func _init() -> void:
	_lauf.call_deferred()


func _warte(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func c(d: Dictionary) -> Dictionary:
	d["action"] = "kit"
	return m.control(d)


func info() -> Dictionary:
	return c({"do": "info"}).get("kit", {})


func pruef(ok: bool, was: String) -> void:
	print(("ok   " if ok else "FEHL ") + was)
	if not ok:
		errs.append(was)


func _bis(cond: Callable, secs: float) -> bool:
	var t := 0.0
	while t < secs:
		if cond.call():
			return true
		await _warte(0.1)
		t += 0.1
	return cond.call()


func _laeuft(n: int) -> bool:
	return k.running and k.kapitel == n and k.phase in ["film", "spiel"]


func _zum_ende() -> void:
	"""the chapter's end (its last film key) - the chain starts from the end card"""
	await _bis(func(): return k.phase in ["film", "spiel"], 30.0)
	c({"do": "eintrag", "e": {"k": "ende", "text": str(k.daten.get_script_constant_map().get("ENDE", "Ende"))}})
	await _bis(func(): return k.hud._ende != null, 3.0)


func _knopf(name_: String) -> Button:
	if k.hud._ende == null or not is_instance_valid(k.hud._ende):
		return null
	return k.hud._ende.find_child(name_, true, false) as Button


func _lauf() -> void:
	# 1 the address of the homepage tile and the start options
	pruef(Array(WEB.grossvater_args({"grossvater": "1"})) == ["--grossvater-neu"], "?grossvater=1 → --grossvater-neu (Kapitelwähler)")
	pruef(Array(WEB.grossvater_args({"szene": "wald"})).is_empty(), "ohne ?grossvater nichts")
	pruef(int(KA.autostart_ziel(WEB.grossvater_args({"grossvater": "1"}))["kapitel"]) == 0 and bool(KA.autostart_ziel(WEB.grossvater_args({"grossvater": "1"}))["an"]),
			"?grossvater=1: der Wähler (Kapitel 0)")
	for n in KA.KAPITEL_FERTIG:
		var a := WEB.grossvater_args({"grossvater": "1", "kapitel": str(n)})
		var z: Dictionary = KA.autostart_ziel(a)
		pruef(bool(z["an"]) and int(z["kapitel"]) == int(n), "?grossvater=1&kapitel=%d → %s → Kapitel %d" % [n, " ".join(a), int(z["kapitel"])])
	pruef(int(KA.autostart_ziel(WEB.grossvater_args({"grossvater": "1", "kapitel": "9"}))["kapitel"]) == 0, "?kapitel=9 (noch nicht da): der Wähler")
	pruef(int(KA.autostart_ziel(PackedStringArray(["--grossvater-kapitel=3"]))["kapitel"]) == 3, "Startoption --grossvater-kapitel=3")
	pruef(int(KA.autostart_ziel(WEB.grossvater_args({"grossvater": "k2"}))["kapitel"]) == 2, "die alte Adresse ?grossvater=k2: Kapitel 2")
	pruef(KA.kapitel_liste() == [1, 2, 3, 4] and KA.naechstes_kapitel(1) == 2 and KA.naechstes_kapitel(4) == -1, "fertige Kapitel 1–4, nach 4 «Fortsetzung folgt»")

	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in range(120):
		await process_frame
	await _warte(2.0)
	SS.set_setting("k_held", {})
	SS.set_setting("k_rucksack", ["seil", "lampe", "karte"])
	k = KA.ensure(m)

	# 2 no hero yet: the hero card, then the chooser with the released chapters only
	c({"do": "grossvater"})
	var ok: bool = await _bis(func(): return k._start_karte_offen, 5.0)
	pruef(ok, "ohne gespeicherten Helden: zuerst die Heldenwahl")
	c({"do": "startwahl"})
	ok = await _bis(func(): return k.waehler_offen(), 3.0)
	pruef(ok and str(KA.held().get("name", "")) == "Nina", "dann der Kapitelwähler, der Held ist gespeichert (%s)" % str(KA.held()))
	var kn: Array = c({"do": "waehler"}).get("knoepfe", [])
	pruef(kn == ["ganz", "kapitel1", "kapitel2", "kapitel3", "kapitel4", "held", "zu"], "Wähler: «Ganzes Spiel» + Kapitel 1–4, kein unfertiges (%s)" % str(kn))
	c({"do": "waehler", "wahl": "zu"})
	await _warte(0.3)
	pruef(not k.waehler_offen() and not k.running, "«Schliessen»")
	# the story card in «Spielen»: the same list
	if m.get("spielbereich") != null:
		m.spielbereich.open()
		await _warte(0.5)
		var kw: Node = m.find_child("kapitelwahl", true, false)
		var namen: Array = []
		if kw != null:
			for b in kw.get_children():
				namen.append(str(b.name))
		pruef(kw != null and namen == ["kapitel1", "kapitel2", "kapitel3", "kapitel4"] and m.find_child("kapitelwahl_ganz", true, false) != null,
				"Geschichten-Karte: «Ganzes Spiel ab Kapitel 1» + Kapitel 1–4 (%s)" % str(namen))
		if m.mehr != null and m.mehr.has_method("close_menu"):
			m.mehr.close_menu()

	# 3 the Steuerbefehl like the tile: every chapter directly, with the saved hero
	SS.set_setting("k_held", {"rolle": "sohn", "name": "Luca"})
	for n in KA.KAPITEL_FERTIG:
		c({"do": "grossvater", "kapitel": n})
		ok = await _bis(func(): return _laeuft(int(n)), 60.0)
		pruef(ok and k.rolle == "sohn" and k.name_ == "Luca" and not k._start_karte_offen, "Steuerbefehl grossvater kapitel=%d: Kapitel %d mit Luca (Sohn)" % [n, k.kapitel])
	c({"do": "stop"})
	await _warte(0.5)

	# 4 the chain: chapter 1 → 2 (countdown) → 3 («Weiter») → 4 (countdown) → «Fortsetzung folgt»
	c({"do": "start", "kapitel": 1, "rolle": "tochter", "name": "Mia", "touch": false})
	ok = await _bis(func(): return _laeuft(1), 60.0)
	pruef(ok, "Start Kapitel 1 (Mia, Tochter)")
	await _zum_ende()
	var lab: String = k.hud._kette_lab.text if k.hud._kette_lab != null else ""
	pruef(_knopf("weiter") != null and _knopf("menue") != null and lab.begins_with("Weiter in"),
			"Ende Kapitel 1: «Weiter», «Zurück zum Menü», Countdown «%s»" % lab)
	var titel: String = (k.hud._ende.find_children("*", "Label", true, false)[0] as Label).text
	pruef(titel.begins_with("Kapitel 1 geschafft – weiter mit Kapitel 2"), "Endkarte: «%s»" % titel)
	ok = await _bis(func(): return _laeuft(2), KA.KETTE_SEK + 40.0)
	pruef(ok and k.name_ == "Mia" and k.rolle == "tochter", "nach dem Countdown von selbst: Kapitel 2, weiter mit Mia (Tochter)")
	await _zum_ende()
	var bw := _knopf("weiter")
	pruef(bw != null, "Ende Kapitel 2: «Weiter»")
	if bw != null:
		bw.pressed.emit()
	ok = await _bis(func(): return _laeuft(3), 40.0)
	pruef(ok and k.name_ == "Mia", "«Weiter»: Kapitel 3")
	await _zum_ende()
	ok = await _bis(func(): return _laeuft(4), KA.KETTE_SEK + 40.0)
	pruef(ok and k.name_ == "Mia" and k.rolle == "tochter", "Kapitel 3 → Kapitel 4")
	await _zum_ende()
	await _warte(KA.KETTE_SEK + 1.0)
	var texte: Array = []
	if k.hud._ende != null:
		for l in k.hud._ende.find_children("*", "Label", true, false):
			texte.append((l as Label).text)
	pruef(k.kapitel == 4 and k.phase == "ende" and _knopf("weiter") == null and _knopf("beenden") != null and str(texte[0]).contains("Fortsetzung folgt"),
			"nach dem letzten Kapitel: «%s», keine Kette" % str(texte[0] if texte.size() > 0 else ""))
	pruef(SS.setting("k_rucksack", []) == ["seil", "lampe", "karte"], "der Rucksack (k_rucksack) bleibt über die Kapitel")

	# 5 «Zurück zum Menü» from the chain card
	c({"do": "start", "kapitel": 3, "rolle": "tochter", "name": "Mia", "touch": false})
	ok = await _bis(func(): return _laeuft(3), 60.0)
	await _zum_ende()
	var bm := _knopf("menue")
	if bm != null:
		bm.pressed.emit()
	await _warte(KA.KETTE_SEK + 1.0)
	pruef(bm != null and not k.running and m.spielbereich.is_open(), "«Zurück zum Menü»: das Abenteuer endet, «Spielen» ist offen, keine Kette")
	_ende()


func _ende() -> void:
	if errs.is_empty():
		print("Kette-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Kette-Test: " + str(e))
		quit(1)
