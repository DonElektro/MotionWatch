extends RefCounted
## Gemeinsame Menü-Datei MoveEye ↔ Simulator (P1 «totale Integration», Daniel 31.10.2026): res://ui_gemeinsam.json
## (kommt mit in die .exe, export_presets.cfg). Eine Quelle für Gruppen-IDs, Namen, Symbole, Reihenfolge, die Texte der
## Bedienleiste (Paket P0 «real-layout-leiste» holt sie hier: UG.bar_text("close") -> «Alle zuklappen», dann T.t) und die Liste
## der geteilten Einstellungen. MoveEye bettet dieselbe Datei ein und prüft sich im Selbsttest dagegen (Teil 639p).
##   const UG = preload("res://scripts/ui_gemeinsam.gd")
##   UG.gid("system")        -> "sys"   (alte IDs gelten weiter)
##   UG.check(main)          -> [] oder die Abweichungen von main.gd (GROUPS, GROUP_IDS, GROUP_RENAME, Übersetzungen)
## Beim Start schreibt schnittstelle.gd «Menü-Datei: OK …» bzw. «SCRIPT ERROR: Menü-Datei: …» ins Log; ohne Bild prüft
## werkzeuge/ui_gemeinsam_test.gd dasselbe. Was es nur auf einer Seite gibt, bleibt erlaubt (Gruppen nur mit «mw» oder «sim»).

const FILE := "res://ui_gemeinsam.json"
const FEATURES := ["menu1"]          # also without the file (this build knows the ids sys / extras and «Kinder-Modus»)
static var _d := {}
static var _loaded := false


static func data() -> Dictionary:
	if not _loaded:
		_loaded = true
		if FileAccess.file_exists(FILE):
			var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
			_d = d if typeof(d) == TYPE_DICTIONARY else {}
	return _d


static func features() -> Array:
	"""/info «features»: what this simulator can (MoveEye reads it; older simulators send nothing)"""
	var f: Array = FEATURES.duplicate()
	for x in data().get("features", []):
		if not f.has(str(x)):
			f.append(str(x))
	return f


static func gid(id: String) -> String:
	"""an old group id -> the id of today (system -> sys, sensors -> extras)"""
	return str((data().get("alias", {}) as Dictionary).get(id, id))


static func sim_groups() -> Array:
	"""the groups of the simulator in their order: [{id, key, draw, emoji, old}]"""
	var gs: Array = []
	for g in data().get("groups", []):
		if typeof(g) == TYPE_DICTIONARY and g.has("sim"):
			gs.append(g)
	gs.sort_custom(func(a, b): return float(a.get("order", 0)) < float(b.get("order", 0)))
	var out := []
	for g in gs:
		var s: Dictionary = g["sim"]
		out.append({"id": str(g["id"]), "key": str(s.get("key", "")), "draw": str(s.get("draw", g.get("draw", ""))),
				"emoji": str(s.get("emoji", g.get("emoji", ""))), "old": s.get("old", []), "names": s.get("names", {})})
	return out


static func bar_text(k: String) -> String:
	"""the German text (key of T.t) of a bar element: simple, expert, color, plain, start_groups, close, groups, open"""
	var t = ((data().get("bar", {}) as Dictionary).get("texts", {}) as Dictionary).get(k, {})
	return str(t.get("de", k)) if typeof(t) == TYPE_DICTIONARY else k


static func migrate_fold(mem: Dictionary) -> Dictionary:
	"""saved open / closed state (fold_mem «c:Karte», «s:Karte/Teil») with the old names: take it over once to the new
	names - the old keys stay (only read, not deleted)"""
	var ren := {}                           # old card name -> new
	for g in sim_groups():
		for o in g["old"]:
			ren[str(o)] = g["key"]
	var pren := {}                          # "Karte/old part" -> "Karte/new part"
	for pid in (data().get("parts", {}) as Dictionary).keys():
		var p: Dictionary = data()["parts"][pid]
		var card := ""
		for g in sim_groups():
			if g["id"] == str(pid).get_slice("/", 0):
				card = g["key"]
		for o in p.get("old", []):
			pren[card + "/" + str(o)] = card + "/" + str(p.get("sim", ""))
	var out := mem.duplicate()
	for k in mem.keys():
		var nk := str(k)
		if nk.begins_with("c:") and ren.has(nk.substr(2)):
			nk = "c:" + ren[nk.substr(2)]
		elif nk.begins_with("s:"):
			var rest := nk.substr(2)
			var card := rest.get_slice("/", 0)
			if ren.has(card):
				rest = ren[card] + rest.substr(card.length())
			if pren.has(rest):
				rest = pren[rest]
			nk = "s:" + rest
		if nk != str(k) and not out.has(nk):
			out[nk] = mem[k]
	return out


static func check(main) -> Array:
	"""main.gd (its constants) against the file - [] = the same"""
	var d := data()
	if d.is_empty():
		return []                           # no file (an old export): nothing to compare
	var probs := []
	var T = preload("res://scripts/i18n.gd")
	var want := sim_groups()
	var have: Array = main.GROUPS
	var names_w := want.map(func(g): return g["key"])
	var names_h := have.map(func(g): return str(g[0]))
	if names_w != names_h:
		probs.append("Gruppen/Reihenfolge: main.gd %s statt %s" % [", ".join(names_h), ", ".join(names_w)])
	for g in want:
		var row = null
		for h in have:
			if str(h[0]) == g["key"]:
				row = h
		if row == null:
			continue
		if str(main.GROUP_IDS.get(g["key"], "")) != g["id"]:
			probs.append("%s: gid «%s» statt «%s»" % [g["key"], main.GROUP_IDS.get(g["key"], ""), g["id"]])
		if str(row[1]) != g["draw"]:
			probs.append("%s: Symbol «%s» statt «%s»" % [g["key"], row[1], g["draw"]])
		if str(row[2]) != g["emoji"]:
			probs.append("%s: Emoji «%s» statt «%s»" % [g["key"], row[2], g["emoji"]])
		for o in g["old"]:
			if str(main.GROUP_RENAME.get(str(o), "")) != g["key"]:
				probs.append("GROUP_RENAME: alter Name «%s» -> «%s» fehlt" % [o, g["key"]])
		for l in ["en", "fr", "it", "rm"]:
			var w := str((g["names"] as Dictionary).get(l, ""))
			if w != "" and T.lookup(g["key"], l) != w:
				probs.append("%s (%s): Übersetzung «%s» statt «%s» (i18n/texte.json)" % [g["key"], l, T.lookup(g["key"], l), w])
	# parts with their own rule (sys/kids: «Kinder-Modus», never «Sicherheit …»)
	var parts: Dictionary = d.get("parts", {})
	for pid in parts.keys():
		var p: Dictionary = parts[pid]
		var row = null
		for g in want:
			if g["id"] == str(pid).get_slice("/", 0):
				for h in have:
					if str(h[0]) == g["key"]:
						row = h
		if row == null:
			probs.append("Teil %s: Gruppe fehlt" % pid)
			continue
		if not (row[3] as Array).has(str(p.get("sim", ""))):
			probs.append("Teil %s: «%s» fehlt in %s" % [pid, p.get("sim", ""), row[0]])
		for o in p.get("old", []):
			if (row[3] as Array).has(str(o)) or main.SUB_RENAME.values().has(str(o)) or main.PLACE.values().any(func(v): return str(v[1]) == str(o)):
				probs.append("Teil %s: alter Name «%s» noch in main.gd" % [pid, o])
	# a name that belongs to another group of MoveEye (e.g. «Sicherheit» = password / users) is not used for something else
	for g in d.get("groups", []):
		for r in g.get("reserved", []):
			for h in have:
				for n in [str(h[0])] + (h[3] as Array).map(func(x): return str(x)):
					if n == str(r) or n.begins_with(str(r) + " ") or n.begins_with(str(r) + "/"):
						probs.append("«%s» im Simulator: der Name gehört in MoveEye zu «%s»" % [n, g["id"]])
	# the texts of the bar: German key of the simulator, the same translations as MoveEye
	var tx: Dictionary = (d.get("bar", {}) as Dictionary).get("texts", {})
	for k in tx.keys():
		var e: Dictionary = tx[k]
		for l in ["en", "fr", "it", "rm"]:
			if T.lookup(str(e.get("de", "")), l) != str(e.get(l, "")):
				probs.append("Leiste %s (%s): «%s» statt «%s» (i18n/texte.json)" % [k, l, T.lookup(str(e.get("de", "")), l), e.get(l, "")])
	return probs


static func summary(main) -> String:
	var p := check(main)
	if data().is_empty():
		return ""
	if p.is_empty():
		return "Menü-Datei: OK (%d Gruppen, %d Texte der Leiste wie ui_gemeinsam.json)" % [sim_groups().size(),
				((data().get("bar", {}) as Dictionary).get("texts", {}) as Dictionary).size()]
	return "Menü-Datei: " + " | ".join(p)
