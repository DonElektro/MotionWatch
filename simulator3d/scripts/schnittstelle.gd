extends Node
## Schnittstelle zu MoveEye (Aufräumen 2, Daniel 30.10.2026): eine Feldliste für beide Seiten (res://schnittstelle.json).
##   * check(): kurz nach dem Start vergleicht der Simulator seine Antwort an MoveEye (world_reply), /info und die
##     /control-Aktionen mit der Liste und schreibt eine Zeile ins Log: «Schnittstelle: OK …» oder
##     «SCRIPT ERROR: Schnittstelle: …» (damit die Prüfung beim Parse-Schritt auffällt). Ohne Liste (z. B. in der .exe) nichts.
##     MoveEye prüft dieselbe Liste in seinem Selbsttest (Teil 558) - dort auch, wer welches Feld liest.
##   * mw_extra(): was MoveEye schickt und hier sichtbar wird - Schutz an / aus («armed») und die Relais («relays») als
##     Anzeige in der Statuszeile (wie der Python-Simulator sie zeigt).
## Neues Feld: eine Zeile in schnittstelle.json.

var main
const LIST := "res://schnittstelle.json"
var result := ""                     # the last check (one line, also in the log)


func _ready() -> void:
	get_tree().create_timer(2.0).timeout.connect(check)


func load_list() -> Dictionary:
	if not FileAccess.file_exists(LIST):
		return {}
	var d = JSON.parse_string(FileAccess.get_file_as_string(LIST))
	return d if typeof(d) == TYPE_DICTIONARY else {}


func _cmp(sect: String, keys: Array, L: Dictionary, cond: Array) -> Array:
	var out := []
	var lst: Dictionary = L.get(sect, {})
	for k in keys:
		if not lst.has(str(k)):
			out.append("%s: «%s» wird gesendet, steht aber nicht in schnittstelle.json" % [sect, k])
	for k in lst.keys():
		if not keys.has(k) and not cond.has(k):
			out.append("%s: «%s» steht in schnittstelle.json, wird aber nicht gesendet" % [sect, k])
	return out


func check() -> void:
	var L := load_list()
	if L.is_empty():
		return
	var cond: Array = L.get("_bedingt", [])
	var probs := []
	probs += _cmp("world_reply", main.world_reply().keys(), L, cond)
	probs += _cmp("info", main.info().keys(), L, cond)
	# the /control actions MoveEye uses: does main.gd _control know them? (only when the source can be read)
	var src := ""
	if FileAccess.file_exists("res://scripts/main.gd"):
		src = FileAccess.get_file_as_string("res://scripts/main.gd")
	var i := src.find("\nfunc _control(")
	if i >= 0:
		var j := src.find("\nfunc ", i + 10)
		var body := src.substr(i, j - i if j > i else -1)
		for a in (L.get("control", {}) as Dictionary).keys():
			if body.find('a == "%s"' % a) < 0 and body.find('"%s"' % a) < 0:
				probs.append("control: MoveEye braucht «%s», main.gd _control kennt es nicht" % a)
	if probs.is_empty():
		result = "Schnittstelle: OK (%d Antwort-Felder, %d Info-Felder, %d Aktionen wie in schnittstelle.json)" % [
				(L.get("world_reply", {}) as Dictionary).size(), (L.get("info", {}) as Dictionary).size(), (L.get("control", {}) as Dictionary).size()]
		print(result)
	else:
		result = "Schnittstelle: " + " | ".join(probs)
		printerr("SCRIPT ERROR: " + result)


func mw_extra() -> String:
	"""« · Schutz an · Relais Pumpe an, Lampe aus» - only while MoveEye is connected"""
	if main.now() - main.mw_t > 3.0:
		return ""
	var t := ""
	if main.mw.has("armed"):
		t += " · Schutz " + ("an" if bool(main.mw.get("armed", false)) else "aus")
	var rl := []
	for r in main.mw.get("relays", []):
		if typeof(r) == TYPE_DICTIONARY:
			rl.append("%s %s" % [str(r.get("name", "?")).left(16), "AN" if bool(r.get("on", false)) else "aus"])
	if not rl.is_empty():
		t += " · Relais " + ", ".join(rl)
	return t
