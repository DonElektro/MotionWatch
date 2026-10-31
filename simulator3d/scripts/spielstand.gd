extends RefCounted
## Spielstand (Paket A6, Daniel 31.10.2026): drei Spielstand-Plätze für die Familie, ein Level für alles, automatisches
## Speichern des laufenden Abenteuers an Hütte und Lager, Einstellungen Erzählerstimme / Zwischenszenen.
##   * Platz 1 = der bisherige Spielstand (die alten Dateien werden einfach weiter benutzt - nichts wird verschoben):
##       Abenteuer   user://bergtal_abenteuer/fortschritt.json
##       Spielbereich user://spiel/spielbereich.json
##       Entdecken   user://entdecken.json (nur «gefunden»; was es gibt («known») und die Hinweis-Einstellungen gelten für alle)
##     Platz 2 und 3: dieselben Dateien unter user://spielstand/<n>/.
##   * Ein Level für alles (pro Spielstand): Spielbereich (Entdeckungen, Abzeichen, Abenteuer geschafft / begonnen) +
##     Erfahrung aus dem Bergtal-Abenteuer, eine Kurve (spielbereich.gd need(): 2 = 100, 3 = 300, 4 = 600 …).
##   * Der laufende Lauf (Tour bis Nachtlager) wird an Hütten und am Lager in user://spielstand/<n>/lauf.txt gemerkt
##     (var_to_str, ohne Objekte) - «Weiterspielen» im ersten Schritt des Abenteuers.
## Alles statisch (wie abenteuer_inventar.gd), die Datei user://spielstand.json hält: aktiver Platz, Namen, letzte Stufe
## je Platz (für die Anzeige der anderen Plätze) und die Einstellungen «stimme» / «szenen».

const FILE := "user://spielstand.json"
const N := 3
const AB_1 := "user://bergtal_abenteuer/fortschritt.json"     # (= bergtal_abenteuer.gd SAVE_FILE)
const SB_1 := "user://spiel/spielbereich.json"                 # (= spielbereich.gd SAVE)
const ENT_1 := "user://entdecken.json"                         # (= entdecken.gd SAVE)

static var _d := {}
static var _loaded := false


static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	_d = {"slot": 1, "names": ["", "", ""], "lv": [0, 0, 0], "stimme": true, "szenen": true}
	if FileAccess.file_exists(FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if d is Dictionary:
			for k in d:
				_d[k] = d[k]
	_d["slot"] = clampi(int(_d.get("slot", 1)), 1, N)
	for k in ["names", "lv"]:
		var a: Array = _d[k] if _d.get(k) is Array else []
		while a.size() < N:
			a.append("" if k == "names" else 0)
		_d[k] = a


static func save() -> void:
	_load()
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(_d, " "))


static func slot() -> int:
	_load()
	return int(_d["slot"])


static func name_of(n: int) -> String:
	_load()
	var s := str(_d["names"][clampi(n, 1, N) - 1]).strip_edges()
	return s


static func set_name(n: int, s: String) -> void:
	_load()
	_d["names"][clampi(n, 1, N) - 1] = s.strip_edges().left(24)
	save()


static func setting(k: String, def = true):
	_load()
	return _d.get(k, def)


static func set_setting(k: String, v) -> void:
	_load()
	_d[k] = v
	save()


static func remember_lv(lv: int) -> void:
	_load()
	if int(_d["lv"][slot() - 1]) != lv:
		_d["lv"][slot() - 1] = lv
		save()


static func lv_of(n: int) -> int:
	_load()
	return int(_d["lv"][clampi(n, 1, N) - 1])


# ---- the files of a place --------------------------------------------------------------------------------------------------
static func dir_of(n: int) -> String:
	return "user://spielstand/%d" % clampi(n, 1, N)


static func path_ab(n := -1) -> String:
	n = slot() if n < 1 else n
	return AB_1 if n == 1 else dir_of(n) + "/bergtal_abenteuer.json"


static func path_sb(n := -1) -> String:
	n = slot() if n < 1 else n
	return SB_1 if n == 1 else dir_of(n) + "/spielbereich.json"


static func path_ent(n := -1) -> String:
	n = slot() if n < 1 else n
	return ENT_1 if n == 1 else dir_of(n) + "/entdecken.json"


static func path_lauf(n := -1) -> String:
	n = slot() if n < 1 else n
	return dir_of(n) + "/lauf.txt"


static func info(n: int) -> Dictionary:
	"""what the place holds (also for the places not active now): chapter, stars, a saved run"""
	var out := {"n": n, "name": name_of(n), "active": n == slot(), "lv": lv_of(n), "chapter": 1, "stars": 0, "xp": 0, "used": false,
			"lauf": ""}
	var p := path_ab(n)
	if FileAccess.file_exists(p):
		var d = JSON.parse_string(FileAccess.get_file_as_string(p))
		if d is Dictionary:
			out["used"] = true
			out["chapter"] = int(d.get("chapter", 1))
			out["xp"] = int(d.get("xp", 0))
			var st = d.get("stars", {})
			if st is Dictionary:
				for k in st:
					out["stars"] = int(out["stars"]) + int(st[k])
	var l := lauf_head(n)
	if not l.is_empty():
		out["lauf"] = "%s · %s" % [str(l.get("where_txt", "")), str(l.get("date", ""))]
	return out


# ---- the running tour (auto-save at the hut / the camp) ------------------------------------------------------------------
static func _clean(v):
	"""a copy without objects (textures, nodes) - only data goes to the file"""
	match typeof(v):
		TYPE_OBJECT, TYPE_CALLABLE, TYPE_SIGNAL, TYPE_RID:
			return null
		TYPE_DICTIONARY:
			var o := {}
			for k in v:
				o[k] = _clean(v[k])
			return o
		TYPE_ARRAY:
			var a := []
			for x in v:
				a.append(_clean(x))
			return a
	return v


static func lauf_save(d: Dictionary) -> bool:
	DirAccess.make_dir_recursive_absolute(dir_of(slot()))
	var f := FileAccess.open(path_lauf(), FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(var_to_str(_clean(d)))
	return true


static func lauf_load(n := -1) -> Dictionary:
	var p := path_lauf(n)
	if not FileAccess.file_exists(p):
		return {}
	var s := FileAccess.get_file_as_string(p)
	if s.contains("Object(") or s.contains("Resource("):         # never build objects from the file
		return {}
	var d = str_to_var(s)
	return d if d is Dictionary and d.has("R") and d.has("W") else {}


static func lauf_head(n := -1) -> Dictionary:
	var d := lauf_load(n)
	return {} if d.is_empty() else {"where": d.get("where", ""), "where_txt": d.get("where_txt", ""), "date": d.get("date", ""),
			"chapter": int((d["R"] as Dictionary).get("chapter", 1))}


static func lauf_delete(n := -1) -> void:
	var p := path_lauf(n)
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)


# ---- switch the place ----------------------------------------------------------------------------------------------------
static func switch(main, n: int) -> Dictionary:
	"""all three parts read the files of place n (the current state is saved first)"""
	_load()
	n = clampi(n, 1, N)
	var ab = main.abenteuer
	var sb = main.spielbereich
	var en = main.entdecken
	if ab != null and ab.save_file != path_ab():
		return {"ok": false, "error": "test"}                  # Entwicklertool «Kapitel-Sprung» runs on its own test file
	if ab != null and not ab.R.is_empty() and int(ab.step) in [4, 5, 6]:
		return {"ok": false, "error": "tour"}
	if n == slot():
		return {"ok": true, "slot": n}
	if ab != null:
		ab._save()
	if sb != null:
		sb.save()
	if en != null:
		en.save()
	_d["slot"] = n
	save()
	DirAccess.make_dir_recursive_absolute(dir_of(n))
	if sb != null:
		sb.save_path = path_sb(n)
		sb.data = {"visited": [], "seen_lv": 1, "greeted": false, "done_seen": []}
		sb._load()
	if en != null and en.has_method("use_file"):
		en.use_file(path_ent(n))
	if ab != null:
		ab.save_file = path_ab(n)
		ab.R = {}
		ab.leg = {}
		ab._load()
		ab.W["items"] = ab.blinki_suggest()
		ab.step = 0
		ab._changed()
	return {"ok": true, "slot": n}


static func level(main) -> Dictionary:
	"""the one level of this place: {lv, xp, from, to, parts} (spielbereich.gd level() counts the adventure too)"""
	if main != null and main.spielbereich != null:
		var l: Dictionary = main.spielbereich.level()
		remember_lv(int(l["lv"]))
		return l
	var SB = preload("res://scripts/spielbereich.gd")
	var xp: int = int(main.abenteuer.P.get("xp", 0)) if main != null and main.abenteuer != null else 0
	var lv: int = SB.level_of(xp)
	return {"lv": lv, "xp": xp, "from": SB.need(lv), "to": SB.need(lv + 1), "parts": [["Bergtal-Abenteuer", xp]]}
