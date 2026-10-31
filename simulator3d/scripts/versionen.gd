extends RefCounted
## Versionsnummern (Versionierung 3.0.0, Entscheid Daniel 31.10.2026): ab 3.0.0 haben MoveEye und der Simulator immer
## dieselbe Nummer X.Y.Z («MoveEye 3.0.0» / «MoveEye Sim 3.0.0»). Bis dahin hiess der Simulator «3D-A.B» (bis 3D-4.8x).
##
## Brücke für alte Simulatoren: sie lesen in simulator3d/version.json nur «version», nehmen «3D-» weg und vergleichen die
## Zahlen - «3.0.0» wäre für sie älter als «3D-4.82» und sie fänden das Update nie. Darum steht in «version» immer die alte
## Schreibweise «3D-(X+2).Y.Z» (3.0.0 -> «3D-5.0.0», 3.1.0 -> «3D-5.1.0», 4.0.0 -> «3D-6.0.0») und die echte Nummer in «ver».
## Hier gilt dieselbe Abbildung rückwärts: «3D-A.B[.C]» = (A-2).B.C, also 3D-4.82 = 2.82.0 < 3.0.0 = 3D-5.0.0.
## Python-Gegenstück: sim_vkey() in quelle/300_werkzeuge_simulator3d.py und werkzeuge/versionen.py (gleiche Regeln).

const LEGACY_SHIFT := 2


static func is_new(v: String) -> bool:
	"""true for the new schema X.Y.Z (no «3D-» in it)"""
	return v.strip_edges() != "" and v.find("3D-") < 0


static func key(v: String) -> Array:
	"""[X, Y, Z] to compare; «3D-4.82» -> [2, 82, 0], «3D-5.0.0» -> [3, 0, 0], «3.0.0» / «MoveEye Sim 3.0.0» -> [3, 0, 0];
	unreadable -> [0, 0, 0]"""
	var s := v.strip_edges()
	var re := RegEx.new()
	re.compile("3D-(\\d+)\\.(\\d+)(?:\\.(\\d+))?")
	var m := re.search(s)
	if m != null:
		return [int(m.get_string(1)) - LEGACY_SHIFT, int(m.get_string(2)), int(m.get_string(3)) if m.get_string(3) != "" else 0]
	re.compile("(\\d+)\\.(\\d+)(?:\\.(\\d+))?")
	m = re.search(s)
	if m != null:
		return [int(m.get_string(1)), int(m.get_string(2)), int(m.get_string(3)) if m.get_string(3) != "" else 0]
	return [0, 0, 0]


static func newer(a: String, b: String) -> bool:
	"""is version a newer than b? (both schemas, also mixed)"""
	var x := key(a)
	var y := key(b)
	for i in range(3):
		if x[i] != y[i]:
			return x[i] > y[i]
	return false


static func legacy(v: String) -> String:
	"""what old simulators read in version.json «version»: 3.0.0 -> «3D-5.0.0» (an old «3D-…» stays as it is)"""
	if not is_new(v):
		return v.strip_edges()
	var k := key(v)
	return "3D-%d.%d.%d" % [k[0] + LEGACY_SHIFT, k[1], k[2]]


static func plain(v: String) -> String:
	"""the number to show: «3.0.0» (new) or «3D-4.82» (old)"""
	return v.strip_edges().trim_prefix("MoveEye Sim · 3D ").trim_prefix("MoveEye Sim ")


static func label(v: String) -> String:
	"""the name with the number: «MoveEye Sim 3.0.0»; old schema as before «MoveEye Sim · 3D 3D-4.82»"""
	return ("MoveEye Sim %s" if is_new(v) else "MoveEye Sim · 3D %s") % plain(v)


static func of_info(d: Dictionary) -> String:
	"""the newest version in version.json: «ver» (new schema, from 3.0.0), else «version»"""
	var v := str(d.get("ver", "")).strip_edges()
	return v if v != "" else str(d.get("version", "")).strip_edges()
