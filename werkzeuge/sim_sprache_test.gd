extends SceneTree
## Test der Simulator-Sprachen (i18n.gd): Übersetzungen, Fallbacks, Platzhalter, Wahl / MoveEye-Sprache.
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/sim_sprache_test.gd"   (absoluter Pfad nötig)
## Ende: «Sprachtest OK» oder «SCRIPT ERROR: Sprachtest: …» (Exit-Code 0 / 1).

var errs := []


func eq(what: String, got, want) -> void:
	if str(got) != str(want):
		errs.append("%s: %s statt %s" % [what, got, want])


func _init() -> void:
	var T = load("res://scripts/i18n.gd")
	var keep_choice: String = T.choice()
	# 1. the real texte.json: a fully translated text comes back in every language
	var st: Dictionary = T.stats()
	if int(st.get("texts", 0)) < 1000:
		errs.append("texte.json: nur %d Texte" % int(st.get("texts", 0)))
	eq("de Wetter", T.lookup("Wetter", "de"), "Wetter")
	for l in ["en", "fr", "it", "rm"]:
		var x: String = T.lookup("Wetter", l)
		if x == "" or x == "Wetter" and l != "rm":
			errs.append("Wetter in %s: «%s»" % [l, x])
	# 2. fallbacks with a made-up table
	T._tx = {"Nur Englisch": {"en": "English only", "fr": "", "it": "", "rm": ""},
			"Ohne": {"en": "", "fr": "", "it": "", "rm": ""},
			"Alle %d Bilder": {"en": "All %d pictures", "fr": "Toutes les %d images", "it": "Tutte le %d immagini", "rm": "Tut ils %d maletgs"},
			"Wir folgen {name}": {"en": "Following {name}", "fr": "Nous suivons {name}", "it": "Seguiamo {name}", "rm": "Nus suandain {name}"}}
	T._loaded = true
	T._cache = {}
	eq("fr -> en", T.lookup("Nur Englisch", "fr"), "English only")
	eq("it -> en", T.lookup("Nur Englisch", "it"), "English only")
	eq("rm -> de", T.lookup("Nur Englisch", "rm"), "Nur Englisch")
	eq("fr -> en -> de", T.lookup("Ohne", "fr"), "Ohne")
	eq("en -> de", T.lookup("Ohne", "en"), "Ohne")
	eq("unbekannt", T.lookup("Gibt es nicht", "fr"), "Gibt es nicht")
	# 3. the choice in the simulator + placeholders
	T.set_lang("fr")
	eq("Wahl fr", T.lang(), "fr")
	eq("%d", T.t("Alle %d Bilder", [7]), "Toutes les 7 images")
	eq("{name}", T.t("Wir folgen {name}", {"name": "Anna"}), "Nous suivons Anna")
	T.set_lang("rm")
	eq("rm %d", T.t("Alle %d Bilder", 3), "Tut ils 3 maletgs")
	eq("rm Fallback", T.t("Nur Englisch"), "Nur Englisch")
	eq("falscher Code", T.set_lang("xx"), false)
	# 4. without a choice: the language MoveEye sent, else German
	T.set_lang("auto")
	T._mw_lang = ""
	T._changed()
	eq("auto ohne MoveEye", T.lang(), "de")
	T.set_moveeye_lang("it")
	eq("auto mit MoveEye it", T.lang(), "it")
	eq("it {name}", T.t("Wir folgen {name}", {"name": "Bo"}), "Seguiamo Bo")
	T.set_lang("en")
	eq("Wahl schlägt MoveEye", T.lang(), "en")
	T.set_lang(keep_choice)
	if errs.is_empty():
		print("Sprachtest OK (%d Texte, en %d, fr %d, it %d, rm %d)" % [st.texts, st.en, st.fr, st.it, st.rm])
		quit(0)
	else:
		printerr("SCRIPT ERROR: Sprachtest: " + " | ".join(errs))
		quit(1)
