extends RefCounted
## «Figuren menschlicher» (01.11.2026): Vielfalt der Menschen - zufällig, aber pro Szene gesteuert. EINE Stelle für alle
## Figuren (einfache Formen actor.gd, Menschen-Paket figur_mensch.gd, Quaternius figur_paket.gd).
##   Alter:      Kind / erwachsen / älter (älter: gebeugter, graue Haare) - kommt aus der Art (child, elderly)
##   Körperbau:  schlank / normal / kräftig
##   Kleidung:   wandern / freizeit / arbeit / regen - Gewichte pro Szene (SZENE), bei Regen meist «regen»
##   Zubehör:    Rucksack, Hut oder Mütze, Wanderstöcke, Stirnlampe oder Laterne (nachts)
## Was menschen.gd (npc_look) oder ein Spieler ausdrücklich wählt, bleibt (actor.gd prüft das).
## Kleidung nach Jahreszeit (lang / kurz / warm) bleibt bei kleidung.gd.

const Worlds = preload("res://scripts/worlds.gd")
const STILE := ["wandern", "freizeit", "arbeit", "regen"]
# Szene -> Gewichte der Kleidung (ohne Regen); fehlt die Szene: DEFAULT
const SZENE := {
	"bergtal": {"wandern": 0.75, "freizeit": 0.15, "arbeit": 0.1},
	"wald": {"wandern": 0.55, "freizeit": 0.3, "arbeit": 0.15},
	"wild": {"wandern": 0.6, "freizeit": 0.3, "arbeit": 0.1},
	"camping": {"freizeit": 0.6, "wandern": 0.3, "arbeit": 0.1},
	"stellplatz": {"freizeit": 0.6, "wandern": 0.3, "arbeit": 0.1},
	"festival": {"freizeit": 0.85, "arbeit": 0.15},
	"garten": {"freizeit": 0.65, "arbeit": 0.3, "wandern": 0.05},
	"parkplatz": {"freizeit": 0.6, "arbeit": 0.25, "wandern": 0.15},
	"ferienpark": {"freizeit": 0.7, "wandern": 0.2, "arbeit": 0.1},
}
const DEFAULT := {"freizeit": 0.6, "wandern": 0.25, "arbeit": 0.15}
# Farben pro Kleidung: Jacke, Hose
const JACKE := {
	"wandern": [Color(0.75, 0.16, 0.12), Color(0.12, 0.36, 0.62), Color(0.2, 0.42, 0.26), Color(0.92, 0.48, 0.1), Color(0.3, 0.32, 0.36), Color(0.5, 0.2, 0.45)],
	"freizeit": [Color(0.24, 0.24, 0.6), Color(0.5, 0.31, 0.16), Color(0.16, 0.43, 0.24), Color(0.6, 0.6, 0.6), Color(0.16, 0.16, 0.16), Color(0.7, 0.62, 0.5), Color(0.55, 0.15, 0.18)],
	"arbeit": [Color(0.95, 0.45, 0.05), Color(0.15, 0.2, 0.35), Color(0.85, 0.85, 0.15), Color(0.3, 0.33, 0.25)],
	"regen": [Color(0.95, 0.8, 0.1), Color(0.8, 0.12, 0.1), Color(0.1, 0.3, 0.65), Color(0.15, 0.45, 0.3), Color(0.12, 0.12, 0.14)],
}
const HOSE := {
	"wandern": [Color(0.22, 0.22, 0.22), Color(0.3, 0.3, 0.26), Color(0.16, 0.18, 0.2), Color(0.38, 0.33, 0.25)],
	"freizeit": [Color(0.18, 0.17, 0.16), Color(0.25, 0.3, 0.45), Color(0.35, 0.3, 0.22), Color(0.12, 0.12, 0.14), Color(0.55, 0.5, 0.4)],
	"arbeit": [Color(0.18, 0.24, 0.4), Color(0.3, 0.3, 0.3), Color(0.32, 0.3, 0.22)],
	"regen": [Color(0.12, 0.12, 0.14), Color(0.2, 0.22, 0.26), Color(0.25, 0.3, 0.45)],
}

static var force := ""                    # tests (/control figuren op stil): "" | wandern | freizeit | arbeit | regen
static var force_bau := ""                # tests: "" | schlank | normal | kraeftig


static func gewichte(main) -> Dictionary:
	var sc := str(main.get("scene"))
	var w: Dictionary = SZENE.get(sc, SZENE.get(Worlds.world_of(sc), DEFAULT))
	return w


static func _zieh(w: Dictionary) -> String:
	var sum := 0.0
	for k in w:
		sum += float(w[k])
	var r := randf() * sum
	for k in w:
		r -= float(w[k])
		if r <= 0.0:
			return str(k)
	return str(w.keys()[0])


static func wahl(main, variant := "", kid := false, old_ := false) -> Dictionary:
	"""{stil, bau, jacke, hose, rucksack, kopf (""|hut|muetze|cap), stoecke, licht (""|stirn|laterne)} für eine neue Figur"""
	var stil := force if force in STILE else ""
	var wet := str(main.get("weather")) == "rain"
	if stil == "":
		stil = "regen" if wet and randf() < 0.75 else _zieh(gewichte(main))
	var bau := force_bau if force_bau in ["schlank", "normal", "kraeftig"] else ""
	if bau == "":
		var r := randf()
		bau = "schlank" if r < 0.35 else ("kraeftig" if r > (0.75 if not old_ else 0.6) else "normal")
	var cold := float(main.get("ambient")) < 8.0 if main.get("ambient") != null else false
	var out := {"stil": stil, "bau": bau, "rucksack": false, "kopf": "", "stoecke": false, "licht": ""}
	var J: Array = JACKE[stil]
	var H: Array = HOSE[stil]
	out["jacke"] = J[randi() % J.size()]
	out["hose"] = H[randi() % H.size()]
	match stil:
		"wandern":
			out["rucksack"] = randf() < (0.75 if not kid else 0.5)
			out["stoecke"] = not kid and randf() < (0.55 if old_ else 0.35)
			out["kopf"] = ["", "", "cap", "hut", "muetze" if cold else "cap"][randi() % 5]
		"arbeit":
			out["kopf"] = ["", "muetze", "cap"][randi() % 3]
			out["rucksack"] = randf() < 0.15
		"regen":
			out["rucksack"] = randf() < 0.3
			out["kopf"] = "hut" if randf() < 0.15 else ""
		_:
			out["rucksack"] = randf() < 0.25
			out["kopf"] = ["", "", "", "cap", "hut"][randi() % 5] if not cold else ["muetze", ""][randi() % 2]
	if bool(main.is_dark()) if main.has_method("is_dark") else false:
		var lr := randf()
		out["licht"] = "stirn" if (stil == "wandern" and lr < 0.55) or lr < 0.2 else ("laterne" if lr < 0.32 else "")
	return out


static func info(main) -> Dictionary:
	return {"force": force, "force_bau": force_bau, "szene": str(main.get("scene")), "gewichte": gewichte(main)}
