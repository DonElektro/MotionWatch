extends RefCounted
## «Frei erkunden mit eigener Figur», Etappe 2 (Besitzer 21.11.2026): wie die eigene Figur aussieht. Nur Daten - gebaut wird
## sie von actor.gd (_build_person mit look «figur»), gewählt im Fenster erkunden_gestalten.gd, gespeichert in main.ex_figur
## (Einstellungen, bleibt). Farben als Hex-Text (JSON).
##   * Person: Geschlecht, Alter (Kind / Jugendlich / Erwachsen), Grösse, Statur
##   * Kopf: Frisur, Haarfarbe, Hautfarbe, Bart (nur Erwachsene, Mann)
##   * Kleider: Jacke, Hose (Farben), Kopfbedeckung, Rucksack
##   * Ausrüstung: Stirnlampe (leuchtet nachts), Wanderstöcke, Feldstecher (um den Hals; benutzen: Etappe 3)

const FELDER := ["sex", "alter", "groesse", "bau", "haar", "haarfarbe", "haut", "bart", "jacke", "hose", "hut", "rucksack",
		"stirnlampe", "stoecke", "feldstecher"]
const OPT := {
	"sex": [["f", "Frau"], ["m", "Mann"]],
	"alter": [["kind", "Kind"], ["teen", "Jugendlich"], ["erw", "Erwachsen"]],
	"groesse": [["s", "Klein"], ["", "Mittel"], ["l", "Gross"]],
	"bau": [["schlank", "Schlank"], ["kraeftig", "Kräftig"]],
	"haar": [["kurz", "Kurz"], ["kurz2", "Kurz, wuschelig"], ["lang", "Lang"], ["dutt", "Dutt"]],
	"hut": [["", "Ohne"], ["muetze", "Mütze"], ["hut", "Hut"], ["cap", "Cap"], ["kapuze", "Kapuze"]]}
const HAARFARBEN := ["262019", "73522e", "bf9959", "999999", "59260f", "d9c08c"]
const HAUTFARBEN := ["ebbf9e", "d9a88c", "a67859", "73523d", "4d3626"]
const JACKEN := ["b8231f", "e6731a", "1f2961", "54592e", "6b4729", "1f1f21", "808085", "e0e0db", "2e8c4d", "6b3a8c"]
const HOSEN := ["1f1f24", "2e3d59", "4d4733", "6b5a40", "808085"]
const SCHALTER := ["bart", "rucksack", "stirnlampe", "stoecke", "feldstecher"]
const DEFAULT := {"sex": "f", "alter": "erw", "groesse": "", "bau": "schlank", "haar": "lang", "haarfarbe": "73522e",
		"haut": "d9a88c", "bart": false, "jacke": "b8231f", "hose": "1f1f24", "hut": "", "rucksack": true,
		"stirnlampe": false, "stoecke": false, "feldstecher": false}
const TALL := {"s": 0.93, "": 1.0, "l": 1.07}
const TEEN := 0.9                    # a teenager: a little smaller than a grown-up


static func _werte(feld: String) -> Array:
	if OPT.has(feld):
		return (OPT[feld] as Array).map(func(e): return str(e[0]))
	match feld:
		"haarfarbe":
			return HAARFARBEN
		"haut":
			return HAUTFARBEN
		"jacke":
			return JACKEN
		"hose":
			return HOSEN
	return []


static func norm(d) -> Dictionary:
	"""a complete, valid choice (unknown or missing fields from DEFAULT)"""
	var out := DEFAULT.duplicate()
	if not (d is Dictionary):
		return out
	for f in FELDER:
		if not d.has(f):
			continue
		if f in SCHALTER:
			out[f] = bool(d[f])
		elif str(d[f]) in _werte(f):
			out[f] = str(d[f])
	if str(out["sex"]) != "m" or str(out["alter"]) != "erw":
		out["bart"] = false                                  # a beard: grown-up men only
	return out


static func setzen(d: Dictionary, feld: String, wert) -> Dictionary:
	var o := d.duplicate()
	o[feld] = wert
	return norm(o)


static func zufall() -> Dictionary:
	var o := {}
	for f in FELDER:
		if f in SCHALTER:
			o[f] = randf() < (0.6 if f == "rucksack" else 0.3)
		else:
			var w: Array = _werte(f)
			o[f] = w[randi() % w.size()]
	return norm(o)


static func art(d: Dictionary) -> String:
	"""actor.setup kind: a child is the variant «child» (its own body and size)"""
	return "child" if str(d.get("alter", "erw")) == "kind" else "person"


static func look(d: Dictionary) -> Dictionary:
	"""the look dict for actor.gd (controlled): the choice + what the older keys say"""
	var n := norm(d)
	var hat := ""
	match str(n["hut"]):
		"kapuze":
			hat = "hood"
		"cap":
			hat = "cap"
	return {"figur": n, "pack": bool(n["rucksack"]), "hat": hat, "col": "", "size": str(n["groesse"]), "build": ""}


static func farbe(hex: String) -> Color:
	return Color.html(hex)


static func hoehe_faktor(d: Dictionary) -> float:
	"""× body_root scale (the child size 0.62 comes from actor.gd)"""
	var n := norm(d)
	return float(TALL.get(str(n["groesse"]), 1.0)) * (TEEN if str(n["alter"]) == "teen" else 1.0)
