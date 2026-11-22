extends RefCounted
## «Frei erkunden mit eigener Figur», Etappe 3 (Besitzer 21.11.2026): der Rucksack - packen wie im Abenteuer (30 / 50 / 70 L,
## Gewicht; dieselben Sachen und Gewichte wie bergtal_abenteuer_daten.gd PACKS / ITEMS) und dazu, was es beim Erkunden gibt:
## Feldstecher, Kompass, Taschenuhr, Seil, Pickel, Hut. Gespeichert in main.ex_rucksack {"pack": "50", "n": {id: Anzahl}}.
## Was die Sachen tun: erkunden_sachen.gd. Nur Daten und Rechnen hier.

const AbD = preload("res://scripts/bergtal_abenteuer_daten.gd")

# id -> [Name, kg, Liter, Gruppe, Text, höchstens Anzahl] (nur beim Erkunden; die anderen kommen aus AbD.ITEMS)
const EXTRA := {"feldstecher": ["Feldstecher", 0.6, 1.0, "sehen", "Zoom 2–10×, Tiere und Menschen mit Name und Distanz, Foto, Nachtsicht (B).", 1],
		"kompass": ["Kompass", 0.1, 0.2, "sehen", "Richtung und eine Nadel zum gemerkten Ort (O).", 1],
		"taschenuhr": ["Taschenuhr", 0.1, 0.1, "sehen", "Zeigt die Zeit; vor- und zurückspulen (, und .).", 1],
		"seil": ["Seil", 1.8, 4.0, "sicher", "An steilen Stellen abseilen (E an der Kante).", 1],
		"pickel": ["Pickel", 0.5, 1.0, "sicher", "Auf Schnee und Eis sicher und schneller; höhere Kanten hoch.", 1],
		"hut": ["Hut", 0.1, 0.0, "kleider", "Sieht gut aus.", 1]}
const ORDER := ["isomatte", "einmannzelt", "kuppelzelt", "tarp", "biwaksack", "sommerschlafsack", "winterschlafsack", "kocher", "essen",
		"wasser", "stirnlampe", "feldstecher", "kompass", "taschenuhr", "seil", "pickel", "stoecke", "jacke", "apotheke", "ministativ",
		"powerbank", "hut", "karabiner"]
const DACH := ["einmannzelt", "kuppelzelt", "tarp", "biwaksack"]
const SCHLAF := ["sommerschlafsack", "winterschlafsack"]
const DEFAULT := {"pack": "50", "n": {"stirnlampe": 1, "kompass": 1, "taschenuhr": 1, "feldstecher": 1, "essen": 2, "wasser": 1, "jacke": 1}}


static func item(id: String) -> Array:
	"""[Name, kg, Liter, Gruppe, Text, höchstens] - [] = unknown"""
	if EXTRA.has(id):
		return EXTRA[id]
	if AbD.ITEMS.has(id):
		var e: Array = AbD.ITEMS[id]
		return [e[0], e[1], e[2], e[3], e[4], e[5]]
	return []


static func norm(d) -> Dictionary:
	var out := {"pack": "50", "n": {}}
	if not (d is Dictionary):
		d = DEFAULT
	if AbD.PACKS.has(str(d.get("pack", ""))):
		out["pack"] = str(d["pack"])
	var n = d.get("n", {})
	if n is Dictionary:
		for id in ORDER:
			if n.has(id) and not item(id).is_empty():
				var k := clampi(int(n[id]), 0, int(item(id)[5]))
				if k > 0:
					out["n"][id] = k
	return out


static func anzahl(d: Dictionary, id: String) -> int:
	return int((d.get("n", {}) as Dictionary).get(id, 0))


static func hat(d: Dictionary, id: String) -> bool:
	return anzahl(d, id) > 0


static func hat_eins(d: Dictionary, ids: Array) -> bool:
	for id in ids:
		if hat(d, str(id)):
			return true
	return false


static func gewicht(d: Dictionary) -> float:
	"""kg: the pack itself + everything in it"""
	var kg := float(AbD.PACKS[str(d["pack"])][2])
	for id in d.get("n", {}):
		kg += float(item(str(id))[1]) * float(d["n"][id])
	return kg


static func volumen(d: Dictionary) -> float:
	var l := 0.0
	for id in d.get("n", {}):
		l += float(item(str(id))[2]) * float(d["n"][id])
	return l


static func platz(d: Dictionary) -> float:
	return float(AbD.PACKS[str(d["pack"])][1])


static func bequem(d: Dictionary) -> float:
	"""kg that are comfortable for this pack (more makes tired faster with «Echt»)"""
	return float(AbD.PACKS[str(d["pack"])][3])


static func dazu(d: Dictionary, id: String, k: int) -> Dictionary:
	"""k = +1 / -1; refuses when it does not fit (volume) or more than allowed: {ok, d, grund}"""
	var o := norm(d)
	var e := item(id)
	if e.is_empty():
		return {"ok": false, "d": o, "grund": "?"}
	var n := anzahl(o, id) + k
	if n < 0 or n > int(e[5]):
		return {"ok": false, "d": o, "grund": "Nicht mehr davon"}
	if k > 0 and volumen(o) + float(e[2]) > platz(o) + 0.01:
		return {"ok": false, "d": o, "grund": "Passt nicht mehr in den Rucksack"}
	if n == 0:
		o["n"].erase(id)
	else:
		o["n"][id] = n
	return {"ok": true, "d": o, "grund": ""}


static func pack_setzen(d: Dictionary, pack: String) -> Dictionary:
	"""a smaller pack: what does not fit any more comes out (from the end of the list)"""
	var o := norm(d)
	if not AbD.PACKS.has(pack):
		return o
	o["pack"] = pack
	var ids := ORDER.duplicate()
	ids.reverse()
	for id in ids:
		while volumen(o) > platz(o) + 0.01 and anzahl(o, id) > 0:
			o = dazu(o, id, -1)["d"]
	return o
