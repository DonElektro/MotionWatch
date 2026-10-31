extends RefCounted
## Abenteuer-Inventar (Paket A4 «Rucksack», Besitzer dieser Datei; Daniel 31.10.2026).
## Gemeinsame Schnittstelle für alle Abenteuer-Pakete (A1–A5): Gegenstände abfragen, geben und nehmen.
##
##   const Inv = preload("res://scripts/abenteuer_inventar.gd")
##   Inv.hat("seil")            -> bool
##   Inv.anzahl("proviant")     -> int
##   Inv.gib("kaese", 1)        -> int   (neue Anzahl)
##   Inv.nimm("proviant", 1)    -> bool  (false = nicht genug da, dann wird nichts genommen)
##   Inv.gewicht("seil")        -> float (kg pro Stück)
##
## Gegenstands-IDs (fest, aus dem Abenteuer-Brief): seil, stirnlampe, feldstecher, kompass, pickel, hut, taschenuhr,
## proviant, kaese, batterien, brief, ersatzteil, tagebuchseite_1 … tagebuchseite_10.
## Dazu gehen alle Packliste-IDs aus bergtal_abenteuer_daten.gd ITEMS (isomatte, kocher, wasser …).
##
## Wo die Gegenstände liegen (verbunden mit dem bestehenden Rucksack in bergtal_abenteuer.gd):
## - VERBRAUCH (proviant, kaese, batterien, brief, ersatzteil und alle Packliste-Dinge) gehören zum Rucksack dieser Tour:
##   R["items"] während eines Laufs, sonst die Packliste W["items"]. Sie zählen ins Rucksack-Gewicht (pack_kg).
## - BLEIBEND (gefundene Ausrüstung seil / stirnlampe / feldstecher / kompass, Grossvater-Dinge pickel / hut / taschenuhr,
##   Tagebuchseiten) bleiben über alle Kapitel im Fortschritt P["a4_inventar"] und zählen ebenfalls ins Gewicht (extra_kg).
## - Zwei alte IDs heissen in der Packliste anders: proviant = "essen", feldstecher = "fernglas" (ALIAS).
## Ohne verbundenes Abenteuer (Tests, Headless) liegt alles in einem eigenen Speicher (_lose), damit nichts abstürzt.

const D = preload("res://scripts/bergtal_abenteuer_daten.gd")

const IDS := ["seil", "stirnlampe", "feldstecher", "kompass", "pickel", "hut", "taschenuhr", "proviant", "kaese", "batterien",
		"brief", "ersatzteil", "tagebuchseite_1", "tagebuchseite_2", "tagebuchseite_3", "tagebuchseite_4", "tagebuchseite_5",
		"tagebuchseite_6", "tagebuchseite_7", "tagebuchseite_8", "tagebuchseite_9", "tagebuchseite_10"]
# neue ID -> ID in der bestehenden Packliste (D.ITEMS)
const ALIAS := {"proviant": "essen", "feldstecher": "fernglas"}
# bleibt über alle Kapitel (Fundstücke / Belohnungen); Tagebuchseiten zusätzlich über das Präfix
const BLEIBEND := ["seil", "kompass", "pickel", "hut", "taschenuhr"]
# kg pro Stück für IDs, die nicht in D.ITEMS stehen (gerundete Katalogwerte):
# Hilfsseil/Reepschnur 20 m 0,8–1,2 kg; Kartenkompass 30–60 g; Eispickel 0,4–0,6 kg; Filzhut 0,15 kg; Taschenuhr 0,1 kg;
# Alpkäse-Stück 0,3 kg; 4 AA-Batterien 0,1 kg; Brief 20 g; Ersatzteil (Pumpenventil, Kette …) 0,5 kg; Tagebuchseite 10 g.
const KG := {"seil": 1.0, "kompass": 0.05, "pickel": 0.5, "hut": 0.15, "taschenuhr": 0.1, "kaese": 0.3, "batterien": 0.1,
		"brief": 0.02, "ersatzteil": 0.5, "tagebuchseite": 0.01}
# Anzeigename (deutsch; T.t() übersetzt in der Anzeige)
const NAMEN := {"seil": "Seil", "stirnlampe": "Stirnlampe", "feldstecher": "Feldstecher", "kompass": "Kompass", "pickel": "Pickel des Grossvaters",
		"hut": "Hut des Grossvaters", "taschenuhr": "Taschenuhr des Grossvaters", "proviant": "Proviant", "kaese": "Alpkäse",
		"batterien": "Batterien", "brief": "Brief", "ersatzteil": "Ersatzteil", "tagebuchseite": "Tagebuchseite"}

static var ab = null                 # bergtal_abenteuer.gd (verbinde() in dessen _ready)
static var _lose := {}               # Speicher ohne Abenteuer


static func verbinde(node) -> void:
	ab = node


static func _id(id: String) -> String:
	return str(ALIAS.get(id, id))


static func bleibend(id: String) -> bool:
	return id in BLEIBEND or id.begins_with("tagebuchseite_")


static func _box(id: String) -> Dictionary:
	"""das Dictionary, in dem dieser Gegenstand liegt"""
	if ab == null or not is_instance_valid(ab):
		return _lose
	if bleibend(id):
		if not ab.P.has("a4_inventar") or not (ab.P["a4_inventar"] is Dictionary):
			ab.P["a4_inventar"] = {}
		return ab.P["a4_inventar"]
	if not ab.R.is_empty() and ab.R.has("items"):
		return ab.R["items"]
	return ab.W["items"]


static func anzahl(id: String) -> int:
	var k := _id(id)
	var n := int(_box(id).get(k, 0))
	# eine gefundene Stirnlampe / ein gefundener Feldstecher bleiben auch, wenn sie nicht eingepackt sind
	if not bleibend(id) and ab != null and is_instance_valid(ab) and ab.P.has("a4_inventar"):
		n += int((ab.P["a4_inventar"] as Dictionary).get("fund_" + k, 0))
	return n


static func hat(id: String) -> bool:
	return anzahl(id) > 0


static func gib(id: String, n := 1) -> int:
	var k := _id(id)
	var b := _box(id)
	b[k] = int(b.get(k, 0)) + n
	_geaendert(id)
	return anzahl(id)


static func nimm(id: String, n := 1) -> bool:
	if anzahl(id) < n:
		return false
	var k := _id(id)
	var b := _box(id)
	var rest := n
	var here := int(b.get(k, 0))
	var take := mini(here, rest)
	b[k] = here - take
	rest -= take
	if rest > 0 and ab != null and is_instance_valid(ab) and ab.P.has("a4_inventar"):
		var inv: Dictionary = ab.P["a4_inventar"]
		inv["fund_" + k] = maxi(0, int(inv.get("fund_" + k, 0)) - rest)
	if int(b.get(k, 0)) <= 0:
		b.erase(k)
	_geaendert(id)
	return true


static func finde(id: String) -> void:
	"""Ausrüstung unterwegs gefunden: bleibt für alle weiteren Kapitel (auch stirnlampe / feldstecher)"""
	if bleibend(id):
		gib(id, 1)
		return
	if ab == null or not is_instance_valid(ab):
		gib(id, 1)
		return
	if not ab.P.has("a4_inventar"):
		ab.P["a4_inventar"] = {}
	var inv: Dictionary = ab.P["a4_inventar"]
	inv["fund_" + _id(id)] = 1
	_geaendert(id)


static func gewicht(id: String) -> float:
	var k := _id(id)
	if D.ITEMS.has(k):
		return float(D.ITEMS[k][1])
	if id.begins_with("tagebuchseite_"):
		return float(KG["tagebuchseite"])
	return float(KG.get(id, 0.1))


static func name_of(id: String) -> String:
	if id.begins_with("tagebuchseite_"):
		return "%s %s" % [NAMEN["tagebuchseite"], id.trim_prefix("tagebuchseite_")]
	if NAMEN.has(id):
		return str(NAMEN[id])
	if D.ITEMS.has(id):
		return str(D.ITEMS[id][0])
	return id


static func extra_kg() -> float:
	"""Gewicht, das zusätzlich zur Packliste im Rucksack liegt: bleibende Dinge und neue Verbrauchs-IDs (kaese, brief …)"""
	var kg := 0.0
	if ab != null and is_instance_valid(ab) and ab.P.has("a4_inventar"):
		var inv: Dictionary = ab.P["a4_inventar"]
		for k in inv:
			var kk := str(k)
			if kk.begins_with("fund_"):
				kk = kk.trim_prefix("fund_")
				for a in ALIAS:
					if ALIAS[a] == kk:
						kk = a
			kg += gewicht(kk) * int(inv[k])
	return snappedf(kg, 0.01)


static func liste() -> Array:
	"""alles, was man hat: [[id, Anzahl, kg pro Stück], …] (für die Rucksack-Anzeige und den Tausch)"""
	var out := []
	var seen := {}
	for id in IDS:
		var n := anzahl(id)
		if n > 0:
			out.append([id, n, gewicht(id)])
			seen[_id(id)] = true
	if ab != null and is_instance_valid(ab):
		var b: Dictionary = ab.R["items"] if not ab.R.is_empty() and ab.R.has("items") else ab.W["items"]
		for k in b:
			if not seen.has(str(k)) and int(b[k]) > 0:
				out.append([str(k), int(b[k]), gewicht(str(k))])
	return out


static func _geaendert(id: String) -> void:
	if ab == null or not is_instance_valid(ab):
		return
	if bleibend(id) or id in ["stirnlampe", "feldstecher"]:
		ab._save()
	ab._changed()
