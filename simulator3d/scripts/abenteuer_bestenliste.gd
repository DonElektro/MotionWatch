extends RefCounted
## Paket A5 (Bergtal-Abenteuer, Daniel 31.10.2026): die Familien-Bestenliste.
## Zählt pro Person, was sie im Abenteuer gefunden hat (Tagebuchseiten, Tiere, Ausrüstung, Fundstücke), die Etappensiege
## im Wettrennen und behält die besten Wildkamera-Fotos (Bewertung foto_wertung(): Schärfe und Tier).
## Die bestehende Rangliste der Schlafplätze (bergtal.gd ranking(), user://bergtal_rangliste.json) bleibt, wie sie ist,
## und wird hier nur mit angezeigt (kein zweites Format).
## Datei: user://bergtal_abenteuer/familie.json · Fotos: user://bergtal_abenteuer/familie_fotos/
##
## Schnittstellen zu den anderen Paketen (Stand: noch nicht auf main - darum Stubs):
##   hat(id)          Inv.hat() aus abenteuer_inventar.gd (A4), sobald die Datei da ist; sonst Rucksack + Fundstücke
##   tiere_von(R, P)  TODO verbinden mit A1 (seltene Tiere, Feld "a1_tiere" im Spielstand)
##   foto_wertung()   TODO verbinden mit A1 foto_wertung(); bis dahin ein Stub: Schärfe aus dem Bild selbst, Tier aus info
##   wildkamera(R)    TODO verbinden mit A1 (Feld "a1_wildkamera": [{"file" | "jpg_b64", "tier"}])

const FILE := "user://bergtal_abenteuer/familie.json"
const FOTO_DIR := "user://bergtal_abenteuer/familie_fotos"
const PAGES := ["tagebuchseite_1", "tagebuchseite_2", "tagebuchseite_3", "tagebuchseite_4", "tagebuchseite_5",
		"tagebuchseite_6", "tagebuchseite_7", "tagebuchseite_8", "tagebuchseite_9", "tagebuchseite_10"]
const GEAR := ["seil", "stirnlampe", "feldstecher", "kompass", "pickel", "hut", "taschenuhr"]
const MAX_FOTOS := 12
const INV := "res://scripts/abenteuer_inventar.gd"     # A4 (Besitzer), gemeinsame Schnittstelle hat / gib / nimm / anzahl


static func load_all() -> Dictionary:
	var d = null
	if FileAccess.file_exists(FILE):
		var f := FileAccess.open(FILE, FileAccess.READ)
		if f != null:
			d = JSON.parse_string(f.get_as_text())
	if not d is Dictionary:
		d = {}
	if not d.get("names") is Array or (d["names"] as Array).size() < 2:
		d["names"] = ["Spieler 1", "Spieler 2"]
	if not d.get("people") is Dictionary:
		d["people"] = {}
	if not d.get("fotos") is Array:
		d["fotos"] = []
	return d


static func save_all(d: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://bergtal_abenteuer"))
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d, " "))


# ---- what the run found (stubs until A1 / A4 are there) --------------------------------------------------------------
static func hat(ab, id: String) -> bool:
	"""das Inventar von A4 (abenteuer_inventar.gd: Inv.hat, kennt die Aliase proviant = essen, feldstecher = fernglas).
	Die Datei ist noch nicht auf main: darum hier zur Laufzeit geladen (preload ginge ohne Datei nicht durch den Parser).
	TODO beim Zusammenführen (2.98.94): const Inv = preload("res://scripts/abenteuer_inventar.gd") und nur Inv.hat(id)."""
	if ResourceLoader.exists(INV):
		var Inv = load(INV)
		if Inv != null:
			return bool(Inv.hat(id))
	if ab == null:                                          # Ersatz ohne A4: Rucksack (Packliste-Namen) + Fundstücke
		return false
	var pid: String = {"proviant": "essen", "feldstecher": "fernglas"}.get(id, id)
	if ab.has(pid):
		return true
	return id in (ab.R.get("found", []) as Array)


static func tiere_von(R: Dictionary, P: Dictionary) -> Array:
	"""TODO verbinden mit A1: die seltenen Tiere des Laufs (Murmeltier, Schneehase, Steinbock, Gämse, Luchs, Bartgeier, Steinadler)"""
	var out: Array = []
	for src in [R.get("a1_tiere", null), P.get("a1_tiere", null)]:
		if src is Dictionary:
			for k in src:
				if not str(k) in out:
					out.append(str(k))
		elif src is Array:
			for k in src:
				var id := str(k.get("id", "")) if k is Dictionary else str(k)
				if id != "" and not id in out:
					out.append(id)
	return out


static func wildkamera(R: Dictionary) -> Array:
	"""TODO verbinden mit A1: die Wildkamera-Aufnahmen des Laufs (Bild + was MoveEye erkannt hat)"""
	var a = R.get("a1_wildkamera", [])
	return a if a is Array else []


static func foto_wertung(img: Image, info := {}) -> Dictionary:
	"""Stub bis A1 foto_wertung() liefert (gleicher Name, gleiche Rückgabe): Schärfe 0…1 aus den Kanten des Bildes
	(mittlere Helligkeitsänderung benachbarter Pixel auf 160 × 90, ~0.08 = scharf), Tier aus info["tier"] (A1: MoveEyes
	Erkennung). Punkte 0 … 100: 60 × Schärfe + 40 mit Tier."""
	var sch := 0.0
	if img != null and not img.is_empty():
		var s: Image = img.duplicate()
		if s.is_compressed():
			s.decompress()
		s.convert(Image.FORMAT_L8)
		s.resize(160, 90, Image.INTERPOLATE_BILINEAR)
		var acc := 0.0
		var n := 0
		for y in range(0, 89, 2):
			for x in range(0, 159, 2):
				var c := s.get_pixel(x, y).r
				acc += absf(c - s.get_pixel(x + 1, y).r) + absf(c - s.get_pixel(x, y + 1).r)
				n += 2
		sch = clampf((acc / maxf(1.0, n)) / 0.08, 0.0, 1.0)
	var tier := str(info.get("tier", ""))
	var pk := int(round(60.0 * sch + (40.0 if tier != "" else 0.0)))
	return {"punkte": pk, "schaerfe": snappedf(sch, 0.01), "tier": tier}


# ---- writing ------------------------------------------------------------------------------------------------------------
static func add_foto(img: Image, wer: String, info := {}) -> Dictionary:
	"""a picture for the board: rated, saved as JPEG, only the best MAX_FOTOS are kept"""
	if img == null or img.is_empty():
		return {}
	var w := foto_wertung(img, info)
	var d := load_all()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FOTO_DIR))
	var fn := "%s/%d.jpg" % [FOTO_DIR, int(Time.get_unix_time_from_system() * 1000.0)]
	var small: Image = img.duplicate()
	if small.get_width() > 480:
		small.resize(480, int(480.0 * small.get_height() / small.get_width()), Image.INTERPOLATE_BILINEAR)
	small.save_jpg(fn, 0.8)
	var e := {"file": fn, "wer": wer, "punkte": int(w["punkte"]), "schaerfe": w["schaerfe"], "tier": w["tier"],
			"date": Time.get_datetime_string_from_system().substr(0, 16), "kapitel": int(info.get("kapitel", 0)), "quelle": str(info.get("quelle", ""))}
	var L: Array = d["fotos"]
	L.append(e)
	L.sort_custom(func(a, b): return int(a["punkte"]) > int(b["punkte"]))
	for old in L.slice(MAX_FOTOS):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(str(old.get("file", ""))))
	d["fotos"] = L.slice(0, MAX_FOTOS)
	save_all(d)
	return e


static func record_run(names: Array, ab, wins: Dictionary) -> Dictionary:
	"""after a chapter (morning): everybody of the party gets what the party found; the race wins per person"""
	var d := load_all()
	var R: Dictionary = ab.R
	var P: Dictionary = ab.P
	var pages: Array = []
	for id in PAGES:
		if hat(ab, id):
			pages.append(id)
	var gear: Array = []
	for id in GEAR:
		if hat(ab, id):
			gear.append(id)
	var finds: Array = (R.get("found", []) as Array).duplicate()
	var animals := tiere_von(R, P)
	for i in range(names.size()):
		var nm := str(names[i]).strip_edges().left(20)
		if nm == "":
			continue
		var pe: Dictionary = d["people"].get(nm, {"tagebuch": [], "tiere": [], "ausruestung": [], "funde": [], "etappen": 0, "kapitel": 0, "laeufe": 0})
		for pair in [["tagebuch", pages], ["tiere", animals], ["ausruestung", gear], ["funde", finds]]:
			var have: Array = pe.get(pair[0], [])
			for x in pair[1]:
				if not str(x) in have:
					have.append(str(x))
			pe[pair[0]] = have
		pe["etappen"] = int(pe.get("etappen", 0)) + int(wins.get(str(i + 1), 0))
		pe["laeufe"] = int(pe.get("laeufe", 0)) + 1
		if bool(R.get("arrived", false)):
			pe["kapitel"] = maxi(int(pe.get("kapitel", 0)), int(R.get("chapter", 1)))
		pe["zuletzt"] = Time.get_datetime_string_from_system().substr(0, 16)
		d["people"][nm] = pe
	save_all(d)
	for wk in wildkamera(R):                                # A1: the camera-trap pictures of the night
		var img: Image = null
		if wk is Dictionary and str(wk.get("file", "")) != "" and FileAccess.file_exists(str(wk["file"])):
			img = Image.load_from_file(str(wk["file"]))
		elif wk is Dictionary and str(wk.get("jpg_b64", "")) != "":
			img = Image.new()
			img.load_jpg_from_buffer(Marshalls.base64_to_raw(str(wk["jpg_b64"])))
		if img != null:
			add_foto(img, str(names[0]) if not names.is_empty() else "", {"tier": wk.get("tier", ""), "kapitel": R.get("chapter", 0), "quelle": "wildkamera"})
	return load_all()


static func score(pe: Dictionary) -> int:
	"""one number for the order: every find counts, a diary page and a rare animal twice"""
	return (pe.get("tagebuch", []) as Array).size() * 2 + (pe.get("tiere", []) as Array).size() * 2 + (pe.get("ausruestung", []) as Array).size() \
			+ (pe.get("funde", []) as Array).size() + int(pe.get("etappen", 0))


static func people_sorted(d: Dictionary) -> Array:
	var L: Array = []
	for nm in d["people"]:
		L.append([str(nm), d["people"][nm]])
	L.sort_custom(func(a, b): return score(a[1]) > score(b[1]))
	return L


static func reset() -> void:
	var d := load_all()
	for e in d["fotos"]:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(str(e.get("file", ""))))
	save_all({"names": d["names"], "people": {}, "fotos": []})
