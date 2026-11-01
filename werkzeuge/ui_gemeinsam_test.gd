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
		# ★5: the shared entries of «Mehr» in the same order as MoveEye (more_order)
		var order: Array = UG.data().get("more_order", [])
		var rows: Array = Mehr.ITEMS.map(func(it): return str(it[0]))
		var seen := []
		for mo_id in order:
			for mo in UG.data().get("more", []):
				if str(mo.get("id")) == str(mo_id):
					seen.append(rows.find(str((mo.get("sim", {}) as Dictionary).get("row", ""))))
		var sorted_ := seen.duplicate()
		sorted_.sort()
		eq("Mehr: Reihenfolge wie MoveEye (%s)" % ",".join(order), seen, sorted_)
		eq("Mehr: alle gemeinsamen Zeilen da", seen.has(-1), false)
		_abgleich()
		_neu_links(d, M)
	if errs.is_empty():
		print("Menütest OK (%d Gruppen im Simulator, %d gemeinsam mit MoveEye)" % [UG.sim_groups().size(), 6])
		quit(0)
	else:
		printerr("SCRIPT ERROR: Menütest: " + " | ".join(errs))
		quit(1)


# ---- P2: the view shared with MoveEye (abgleich.gd) - a value changed on one side appears on the other (no picture) -----
const FAKE := """extends Node
const VERSION := "%s"
var ui_simple := true
var ui_icons := "color"
var reduce_motion := "auto"
var tour_auto := true
var blinki_on := true
var news_popup := true
var news_links := "auto"
var start_groups := false
var _settings_dirty := false
var mw := {}
var mw_t := 0.0
var mw_addr := ""
var kids_on := false
var dev_area := false
var leiste = null
var mehr = null
var ui_root = null
var net = null
var fine_bodies := []
var t := 100.0
func now() -> float:
	return t
func set_simple(on: bool) -> void:
	ui_simple = on
func set_icons(v: String) -> void:
	ui_icons = v
func motion_reduced() -> bool:
	return reduce_motion == "an"
func control(_d):
	return {}
"""


func _abgleich() -> void:
	var UG = load("res://scripts/ui_gemeinsam.gd")
	var M = load("res://scripts/main.gd")
	var gs := GDScript.new()
	gs.source_code = FAKE % str(M.VERSION)
	if gs.reload() != OK:
		errs.append("Abgleich: Test-Hauptskript lädt nicht")
		return
	var fm = gs.new()
	var TT = load("res://scripts/i18n.gd")
	var St = load("res://scripts/abenteuer_stimme.gd")
	var keep_lang: String = TT.choice()
	var keep_voice: String = St.modus()
	TT.set_lang("auto")
	var ab = load("res://scripts/abgleich.gd").new()
	ab.main = fm
	var n = load("res://scripts/net.gd").new()
	n.abgleich = ab
	fm.net = n
	var mwv := {"simple": false, "icons": "plain", "lang": "fr", "motion": "on", "voice": "off", "tours": false, "blinki": false, "news": false, "news_links": "off"}
	var st := func(rev: int, took: int, v: Dictionary, extra := {}) -> Dictionary:
		var d := {"uid": "A", "device": "MoveEye", "mw_version": str(M.VERSION), "ui": {"rev": rev, "took": took, "v": v.duplicate()}}
		d.merge(extra, true)
		fm.mw = d
		fm.mw_t = fm.t
		return d
	# 1. MoveEye -> simulator: the first packet takes everything (MoveEye leads)
	ab.on_state(st.call(5, 0, mwv, {"level": {"id": "watch", "col": "#ff8a1f"}}), true)
	eq("Abgleich MW->Sim Einfach", fm.ui_simple, false)
	eq("Abgleich MW->Sim Symbole", fm.ui_icons, "plain")
	eq("Abgleich MW->Sim Sprache", TT.lang(), "fr")
	eq("Abgleich MW->Sim Bewegung", fm.reduce_motion, "an")
	eq("Abgleich MW->Sim Stimme", St.modus(), "aus")
	eq("Abgleich MW->Sim Rundgang/Blinki/Neu", [fm.tour_auto, fm.blinki_on, fm.news_popup], [false, false, false])
	eq("Abgleich MW->Sim Links zu Neuerungen", fm.news_links, "off")
	eq("Abgleich: nichts zu senden", ab.reply().is_empty(), true)
	eq("Zustand Wachsam", ab.level_text(), str((UG.data()["level"]["watch"]["names"] as Dictionary).get("fr")))
	eq("Versions-Paar gleich", ab.pair()["same"], true)
	# 2. simulator -> MoveEye: an own change goes out until MoveEye confirms it (took)
	fm.t += 0.1
	fm.set_simple(true)
	ab.on_state(st.call(5, 0, mwv), true)
	var r: Dictionary = ab.reply()
	eq("Abgleich Sim->MW gesendet", (r.get("set", {}) as Dictionary).get("simple"), true)
	eq("Abgleich Sim->MW bleibt bis bestätigt", fm.ui_simple, true)
	fm.t += 0.1
	ab.on_state(st.call(5, 0, mwv), true)                # the answer got lost: the change is sent again, not overwritten
	eq("Abgleich Sim->MW nochmals", (ab.reply().get("set", {}) as Dictionary).has("simple"), true)
	mwv["simple"] = true
	fm.t += 0.1
	ab.on_state(st.call(6, int(r.get("n", 0)), mwv), true)
	eq("Abgleich bestätigt", ab.reply().is_empty(), true)
	eq("Abgleich Wert bleibt", fm.ui_simple, true)
	# 3. same packet: MoveEye wins
	fm.t += 0.1
	fm.tour_auto = true
	ab.on_state(st.call(6, int(r.get("n", 0)), mwv), true)
	var r2: Dictionary = ab.reply()
	fm.t += 0.1
	ab.on_state(st.call(7, int(r2.get("n", 0)), mwv), true)   # MoveEye kept «tours: false»
	eq("Gleichstand: MoveEye gewinnt", fm.tour_auto, false)
	# 4. without connection the simulator goes on; after reconnecting MoveEye leads
	fm.blinki_on = true
	fm.t += 10.0
	ab.on_state(st.call(7, int(r2.get("n", 0)), mwv), true)
	eq("Neu verbunden: MoveEye führt", fm.blinki_on, false)
	eq("Neu verbunden: nichts zu senden", ab.reply().is_empty(), true)
	# 5. a MoveEye that only watches changes nothing
	var other := mwv.duplicate()
	other["icons"] = "color"
	ab.on_state(st.call(99, 0, other), false)
	eq("Zuschauer ändert nichts", fm.ui_icons, "plain")
	# 6. operator mode: locked, the PIN goes to MoveEye; the developer window only with the developer area and not locked
	fm.dev_area = true
	var Dev = load("res://scripts/devtool.gd")
	eq("Entwickler mit Bereich", Dev.dev_ok(fm), true)
	fm.t += 0.1
	ab.on_state(st.call(7, int(r2.get("n", 0)), mwv, {"lock": {"on": true, "n": 0}}), true)
	eq("gesperrt", ab.locked(), true)
	eq("Entwickler gesperrt", Dev.dev_ok(fm), false)
	ab.unlock("4321")
	eq("PIN an MoveEye", (ab.reply().get("unlock", {}) as Dictionary).get("pin"), "4321")
	fm.dev_area = false
	fm.t += 0.1
	ab.on_state(st.call(7, int(r2.get("n", 0)), mwv, {"lock": {"on": false, "n": 1, "msg": "ok"}}), true)
	eq("entsperrt", ab.locked(), false)
	eq("PIN vergessen", ab.reply().has("unlock"), false)
	eq("Entwickler ohne Bereich", Dev.dev_ok(fm), false)
	# 7. the push preview and the version pair
	ab.on_state(st.call(7, int(r2.get("n", 0)), mwv, {"push": {"id": "1", "title": "x"}}), true)
	ab.on_state(st.call(7, int(r2.get("n", 0)), mwv, {"push": {"id": "2", "title": "Person erkannt", "hm": "22:14", "status": "test"}}), true)
	eq("Push-Vorschau", ab.push_text().ends_with("Person erkannt · 22:14"), true)
	fm.mw["mw_version"] = "3.0.1"
	eq("Versions-Paar älter", ab.pair()["older"], "mw")
	TT.set_lang(keep_lang if keep_lang != "" else "auto")
	St.set_modus(keep_voice)
	ab.free()
	n.free()
	fm.free()


# ---- Links zu Neuerungen (news.gd, ui_gemeinsam.json «neu_ziele» / «projekt_veroeffentlicht») - no picture -----------------
func _neu_links(d: Dictionary, M) -> void:
	var N = load("res://scripts/news.gd")
	if typeof(d.get("projekt_veroeffentlicht")) != TYPE_BOOL:
		errs.append("Links: «projekt_veroeffentlicht» fehlt (true / false)")
	var zs = d.get("neu_ziele", {})
	if typeof(zs) != TYPE_DICTIONARY or zs.is_empty():
		errs.append("Links: «neu_ziele» fehlt")
		return
	var steu := FileAccess.get_file_as_string("res://scripts/main_steuerung.gd")
	var parts := {}
	for g in M.GROUPS:
		parts[g[0]] = g[3]
	for v in zs:
		var z: Dictionary = zs[v]
		var sm := str(z.get("sim_menue", ""))
		if sm != "":
			var p := sm.split("/")
			if not parts.has(p[0]) or (p.size() > 1 and not (p[1] in parts[p[0]])):
				errs.append("Links %s: Menü «%s» gibt es nicht (main.gd GROUPS)" % [v, sm])
		if typeof(z.get("sim_aktion")) == TYPE_DICTIONARY:
			if not steu.contains('a == "%s"' % str(z["sim_aktion"].get("action", ""))):
				errs.append("Links %s: Aktion «%s» fehlt in main_steuerung.gd" % [v, z["sim_aktion"].get("action", "")])
		var se := str(z.get("sim_einstellung", ""))
		if se != "":
			var found := false
			for f in DirAccess.get_files_at("res://scripts"):
				if f.ends_with(".gd") and FileAccess.get_file_as_string("res://scripts/" + f).contains('"%s"' % se):
					found = true
					break
			if not found:
				errs.append("Links %s: Einstellung «%s» unbekannt" % [v, se])
	var pub: bool = bool(d.get("projekt_veroeffentlicht", false))
	var gs := GDScript.new()
	gs.source_code = "extends RefCounted\nvar news_links := \"auto\"\n"
	gs.reload()
	var m = gs.new()
	eq("Links Standard (Projektschalter)", N.links_on(m), not pub)
	m.news_links = "on"
	eq("Links eigene Wahl an", N.links_on(m), true)
	m.news_links = "off"
	eq("Links eigene Wahl aus", N.links_on(m), false)
	eq("Links MoveEye-Seite", N.mw_href({"einstellung": "dev_area"}), "/settings?setting=dev_area")
	eq("Links MoveEye-Abschnitt", N.mw_href({"anker": "sec:Backup"}), "/settings?open=sec%3ABackup")
	eq("Links MoveEye-Seite fest", N.mw_href({"seite": "/case"}), "/case")
