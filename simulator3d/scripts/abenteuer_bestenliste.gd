extends RefCounted
## Paket A5 (Bergtal-Abenteuer, Daniel 31.10.2026): die Familien-Bestenliste.
## Zählt pro Person, was sie im Abenteuer gefunden hat (Tagebuchseiten, Tiere, Ausrüstung, Fundstücke), die Etappensiege
## im Wettrennen und behält die besten Wildkamera-Fotos (Bewertung foto_wertung(): Schärfe und Tier).
## Die bestehende Rangliste der Schlafplätze (bergtal.gd ranking(), user://bergtal_rangliste.json) bleibt, wie sie ist,
## und wird hier nur mit angezeigt (kein zweites Format).
## Datei: user://bergtal_abenteuer/familie.json · Fotos: user://bergtal_abenteuer/familie_fotos/
##
## Schnittstellen zu den anderen Paketen (verbunden in 3D-4.74, Paket «Bestenliste verbinden»):
##   hat(id)          Inv.hat() aus abenteuer_inventar.gd (A4)
##   tiere_von(R, P)  A1-Sammlung P["a1_sammlung"] (richtig bestimmte seltene Tiere, A1.TIERE) - A1.sammlung()
##   foto_wertung()   A1.foto_wertung(foto) für Wildkamera-Aufnahmen (Abstand, Grösse, Bewegungsunschärfe, Licht, Seltenheit);
##                    bild_wertung() nur für Fotos ohne A1-Daten (Handy-Begleiter «Foto», take_foto)
##   wildkamera(R)    A1-Aufnahmen der Nacht R["a1"]["fotos"] (am Morgen); die Wildkamera am Tag meldet sich über
##                    add_a1_fotos() selbst (abenteuer_moveeye.gd _tag_done → zweit.on_a1_fotos)
##   Doppelte Fotos: jede A1-Aufnahme (id) kommt nur einmal auf die Liste (Feld "a1_ids").

const FILE := "user://bergtal_abenteuer/familie.json"
const FOTO_DIR := "user://bergtal_abenteuer/familie_fotos"
const PAGES := ["tagebuchseite_1", "tagebuchseite_2", "tagebuchseite_3", "tagebuchseite_4", "tagebuchseite_5",
		"tagebuchseite_6", "tagebuchseite_7", "tagebuchseite_8", "tagebuchseite_9", "tagebuchseite_10"]
const GEAR := ["seil", "stirnlampe", "feldstecher", "kompass", "pickel", "hut", "taschenuhr"]
const MAX_FOTOS := 12
const Inv = preload("res://scripts/abenteuer_inventar.gd")   # A4 (Besitzer, ab 2.98.94 auf main): hat / gib / nimm / anzahl
const A1 = preload("res://scripts/abenteuer_moveeye.gd")      # A1: foto_wertung(foto), TIERE, tier_name()


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
	if not d.get("a1_ids") is Array:
		d["a1_ids"] = []
	return d


static func save_all(d: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://bergtal_abenteuer"))
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d, " "))


# ---- what the run found (A4 inventory, A1 collection and camera trap) -----------------------------------------------------
static func hat(_ab, id: String) -> bool:
	"""das Inventar von A4 (abenteuer_inventar.gd: Inv.hat, kennt die Aliase proviant = essen, feldstecher = fernglas).
	`_ab` bleibt für die Aufrufer."""
	return bool(Inv.hat(id))


static func tiere_von(_R: Dictionary, P: Dictionary) -> Array:
	"""die seltenen Tiere der Sammlung von A1 (P["a1_sammlung"]: auf einer Aufnahme richtig bestimmt), in der Reihe von A1.
	Was erst nach dem Morgen ausgewertet wird, zählt beim nächsten Morgen."""
	var sm = P.get("a1_sammlung", {})
	var out: Array = []
	if sm is Dictionary:
		for t in A1.REIHE:
			if sm.has(t) and int((sm[t] as Dictionary).get("n", 0)) > 0:
				out.append(str(t))
	return out


static func wildkamera(R: Dictionary) -> Array:
	"""die Aufnahmen von MoveEye in dieser Nacht (A1: R["a1"]["fotos"], mit Bild user://…png)"""
	var a1 = R.get("a1", {})
	if not a1 is Dictionary:
		return []
	var fs = (a1 as Dictionary).get("fotos", [])
	return fs if fs is Array else []


static func foto_wertung(foto: Dictionary) -> Dictionary:
	"""= A1.foto_wertung(foto): {"tier", "schaerfe" 0…1, "punkte"}"""
	return A1.foto_wertung(foto)


static func bild_wertung(img: Image, info := {}) -> Dictionary:
	"""für Fotos ohne A1-Daten (Handy-Begleiter): Schärfe 0…1 aus den Kanten des Bildes (mittlere Helligkeitsänderung
	benachbarter Pixel auf 160 × 90, ~0.08 = scharf), Tier aus info["tier"]. Punkte 0 … 100: 60 × Schärfe + 40 mit Tier."""
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
	var w: Dictionary = info["wertung"] if info.get("wertung") is Dictionary else bild_wertung(img, info)
	var d := load_all()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FOTO_DIR))
	var fn := "%s/%d_%d.jpg" % [FOTO_DIR, int(Time.get_unix_time_from_system() * 1000.0), randi() % 1000]
	var small: Image = img.duplicate()
	if small.get_width() > 480:
		small.resize(480, int(480.0 * small.get_height() / small.get_width()), Image.INTERPOLATE_BILINEAR)
	small.save_jpg(fn, 0.8)
	var e := {"file": fn, "wer": wer, "punkte": int(w["punkte"]), "schaerfe": w["schaerfe"], "tier": w["tier"],
			"date": Time.get_datetime_string_from_system().substr(0, 16), "kapitel": int(info.get("kapitel", 0)), "quelle": str(info.get("quelle", ""))}
	var L: Array = d["fotos"]
	if str(info.get("a1_id", "")) != "":
		e["a1_id"] = str(info["a1_id"])
		var ids: Array = d["a1_ids"]
		ids.append(e["a1_id"])
		d["a1_ids"] = ids.slice(maxi(0, ids.size() - 400))
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
	add_a1_fotos(wildkamera(R), str(names[0]) if not names.is_empty() else "")     # A1: the camera-trap pictures of the night
	return load_all()


static func add_a1_fotos(fs: Array, wer: String) -> int:
	"""A1-Aufnahmen auf die Bestenliste: Bild von A1 (user://…png), Punkte von A1.foto_wertung(), jede Aufnahme nur einmal.
	Gibt zurück, wie viele neu dazugekommen sind."""
	var n := 0
	for f in fs:
		if not f is Dictionary:
			continue
		var id := str(f.get("id", ""))
		if id == "" or id in (load_all()["a1_ids"] as Array):
			continue
		var bild := str(f.get("bild", ""))
		if bild == "" or not FileAccess.file_exists(bild):
			continue
		var img := Image.load_from_file(bild)
		if img == null or img.is_empty():
			continue
		var w := foto_wertung(f)
		w["tier"] = A1.tier_name(str(w["tier"]))
		add_foto(img, wer, {"wertung": w, "a1_id": id, "kapitel": int(f.get("kapitel", 0)), "quelle": "wildkamera " + str(f.get("modus", ""))})
		n += 1
	return n


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
	save_all({"names": d["names"], "people": {}, "fotos": [], "a1_ids": []})
