extends SceneTree
## Test der gemeinsamen Menü-Datei im Simulator (P1, ohne Bild): res://ui_gemeinsam.json gegen main.gd (Gruppen, IDs,
## Reihenfolge, Symbole, alte Namen, Teil «Kinder-Modus»), die Übersetzungen (i18n/texte.json) und die Texte der Leiste;
## dazu Alias, Übernahme des gespeicherten Klappzustands, /info «features» und der Export (export_presets.cfg).
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/ui_gemeinsam_test.gd"   (absoluter Pfad nötig)
## Ende: «Menütest OK» oder «SCRIPT ERROR: Menütest: …» (Exit-Code 0 / 1). MoveEye prüft dieselbe Datei im Selbsttest (639p).

var errs := []


func eq(what: String, got, want) -> void:
	if str(got) != str(want):
		errs.append("%s: %s statt %s" % [what, got, want])


func _init() -> void:
	var UG = load("res://scripts/ui_gemeinsam.gd")
	var M = load("res://scripts/main.gd")
	var d: Dictionary = UG.data()
	if d.is_empty():
		errs.append("res://ui_gemeinsam.json fehlt oder ist kein JSON")
	else:
		eq("Version der Datei", d.get("v"), 1)
		errs += UG.check(M)                                  # the same check as at the start (schnittstelle.gd)
		# the shared groups of both sides in the order of MoveEye (camera, mover, lightsound, extras, sys, dev)
		var both := []
		for g in d.get("groups", []):
			if g.has("mw") and g.has("sim"):
				both.append(g)
		both.sort_custom(func(a, b): return float(a["order"]) < float(b["order"]))
		eq("gemeinsame Gruppen", ",".join(both.map(func(g): return g["id"])), "camera,mover,lightsound,extras,sys,dev")
		var sim_names: Array = M.GROUPS.map(func(g): return str(g[0]))
		eq("Zusatzgeräte nach Licht & Ton", sim_names.find("Zusatzgeräte") - sim_names.find("Licht & Ton"), 1)
		eq("Sensoren weg", sim_names.has("Sensoren"), false)
		eq("gid Zusatzgeräte", M.GROUP_IDS.get("Zusatzgeräte"), "extras")
		eq("gid System", M.GROUP_IDS.get("System"), "sys")
		eq("Teil Kinder-Modus", M.PLACE["kids_ask"][1], "Kinder-Modus")
		# alias (older simulators / saved values)
		eq("alias system", UG.gid("system"), "sys")
		eq("alias sensors", UG.gid("sensors"), "extras")
		eq("alias sonst", UG.gid("scene"), "scene")
		# saved open / closed state with the old names is taken over (the old keys stay)
		var m: Dictionary = UG.migrate_fold({"c:Sensoren": true, "s:Sensoren/Strom": true, "s:System/Sicherheit / Benutzer": true, "c:Szene": false})
		eq("Klappzustand Karte", m.get("c:Zusatzgeräte"), true)
		eq("Klappzustand Teil", m.get("s:Zusatzgeräte/Strom"), true)
		eq("Klappzustand Kinder-Modus", m.get("s:System/Kinder-Modus"), true)
		eq("alter Schlüssel bleibt", m.get("c:Sensoren"), true)
		eq("Szene unverändert", m.get("c:Szene"), false)
		# /info features (MoveEye: menu1 = gids sys / extras)
		eq("features", "menu1" in UG.features(), true)
		# texts of the bar (P0 takes them from here)
		eq("Leiste zuklappen", UG.bar_text("close"), "Alle zuklappen")
		eq("Leiste Gruppen", UG.bar_text("groups"), "Nur Gruppen")
		eq("Leiste aufklappen", UG.bar_text("open"), "Alle aufklappen")
		eq("Leiste Einfach", UG.bar_text("simple"), "Einfach")
		# 639t: the one header - the list of buttons, their order, texts in 5 languages and kopf.gd reads them from here
		var K = load("res://scripts/kopf.gd")
		var ks: Array = K.knoepfe().map(func(b): return str(b.get("id")))
		eq("Kopf: Reihenfolge", ",".join(ks), "help,sound,reload,lang,menu,fs,fold,dev")
		eq("Kopf: schmal ab", str((d.get("kopf", {}) as Dictionary).get("schmal_ab")), "lang")
		for b in K.knoepfe():
			for L in ["de", "en", "fr", "it", "rm"]:
				if str((b.get("texts", {}) as Dictionary).get(L, "")) == "":
					errs.append("Kopf: Text %s fehlt für %s" % [L, b.get("id")])
			if str(b.get("draw", "")) == "" or str(b.get("tk", "")) == "":
				errs.append("Kopf: Symbol (draw / tk) fehlt für %s" % b.get("id"))
		var TT = load("res://scripts/i18n.gd")                # the texts in the language of the simulator (saved choice of this PC)
		eq("Kopf: Text Hilfe", K.text("help"), {"de": "Hilfe", "en": "Help", "fr": "Aide", "it": "Aiuto", "rm": "Agid"}.get(TT.lang(), "Hilfe"))
		eq("Kopf: Text Einklappen", K.text("fold"), str(((K.knoepfe()[6] as Dictionary).get("texts", {}) as Dictionary).get(TT.lang(), "Kopf einklappen")))
		for g in ["head", "page", "general"]:
			if K.menu_text(g) == g:
				errs.append("Kopf: Menü-Abschnitt %s ohne Text" % g)
		var kl: Array = (d.get("kopf", {}) as Dictionary).get("listen", [])
		eq("Kopf: Listen-Gruppen", ",".join(kl.map(func(x): return str(x.get("id")))), "protect,camera,power,env,net,other")
		# the file goes into the .exe
		var ep := FileAccess.get_file_as_string("res://export_presets.cfg")
		if ep != "":
			for line in ep.split("\n"):
				if line.begins_with("include_filter=") and line.find("ui_gemeinsam.json") < 0:
					errs.append("export_presets.cfg: ui_gemeinsam.json fehlt in %s" % line)
		# real-gehaeuse: «more» – entries of the page «Mehr» in both programs (row in mehr.gd, names in texte.json)
		var Mehr = load("res://scripts/mehr.gd")
		var tx = JSON.parse_string(FileAccess.get_file_as_string("res://i18n/texte.json"))
		for mo in UG.data().get("more", []):
			var sm: Dictionary = mo.get("sim", {})
			var row = null
			for it in Mehr.ITEMS:
				if str(it[0]) == str(sm.get("row", "")):
					row = it
			if row == null:
				errs.append("Mehr: Zeile %s fehlt in mehr.gd" % sm.get("row", ""))
				continue
			eq("Mehr %s Name" % mo.get("id", ""), row[2], sm.get("key", ""))
			eq("Mehr %s Symbol" % mo.get("id", ""), row[1], mo.get("draw", ""))
			for lg in ["en", "fr", "it", "rm"]:
				eq("Mehr %s (%s)" % [mo.get("id", ""), lg], ((tx as Dictionary).get(sm.get("key", ""), {}) as Dictionary).get(lg, ""), (sm.get("names", {}) as Dictionary).get(lg, ""))
	if errs.is_empty():
		print("Menütest OK (%d Gruppen im Simulator, %d gemeinsam mit MoveEye)" % [UG.sim_groups().size(), 6])
		quit(0)
	else:
		printerr("SCRIPT ERROR: Menütest: " + " | ".join(errs))
		quit(1)
