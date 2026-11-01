extends SceneTree
## Test «Bauen» im Simulator (ohne Bild, real-bauen 01.11.2026): die Daten aus werkstatt_daten.gd (erzeugt aus
## hardware/gehaeuse/bau.json, dieselbe Quelle wie MoveEye /build) sind vollständig, das Fenster öffnet alle 10 Reiter in
## derselben Reihenfolge wie ui_gemeinsam.json «more/build/reiter», Varianten blenden Teile ein und aus, «Mein Bau» zählt.
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/bauen_test.gd"   (absoluter Pfad nötig)
## Ende: «Bauen-Test OK» oder «SCRIPT ERROR: Bauen-Test: …» (Exit-Code 0 / 1).

const FAKE_MAIN := """extends Node
var ui_root = null
var gehaeuse = null
var mw := {}
var mw_t := 0.0
var mw_addr := ""
func now() -> float:
	return Time.get_ticks_msec() / 1000.0
"""

var errs := []
var W
var _n := 0


func eq(what: String, got, want) -> void:
	if str(got) != str(want):
		errs.append("%s: %s statt %s" % [what, got, want])


func _init() -> void:
	var DATA = load("res://scripts/werkstatt_daten.gd")
	var B: Dictionary = DATA.BAU
	for k in ["varianten", "variante_standard", "haendler", "druck", "werkzeug", "schrauben", "sicherheit", "verkabelung", "software",
			"inbetriebnahme", "fehlersuche", "wartung", "extra_schritte", "bom_extra"]:
		if not B.has(k):
			errs.append("BAU." + k + " fehlt")
	var K: Dictionary = B.get("verkabelung", {}).get("knoten", {})
	for c in B.get("verkabelung", {}).get("verbindungen", []):
		if not K.has(c["von"]) or not K.has(c["nach"]):
			errs.append("Verbindung %s: Modul fehlt" % c["id"])
	for id in DATA.BOM:
		if not B["bom_extra"].has(id) or float(B["bom_extra"][id].get("preis", -1)) < 0:
			errs.append("Einkauf: %s ohne Preis" % id)
	var FH = load("res://scripts/fehler_hilfe.gd")
	for fid in B.get("fehlersuche", []):
		if FH.entry(str(fid)).is_empty():
			errs.append("Fehlersuche: %s nicht im Fehler-Katalog" % fid)
	var UG = load("res://scripts/ui_gemeinsam.gd")
	var build := {}
	for mo in UG.data().get("more", []):
		if str(mo.get("id", "")) == "build":
			build = mo
	var Wk = load("res://scripts/werkstatt.gd")
	var ids := []
	for td in Wk.TABS:
		ids.append(str(td[0]))
	eq("Reiter wie ui_gemeinsam.json", ids, build.get("reiter", []))
	eq("Name im Simulator", (build.get("sim", {}) as Dictionary).get("key", ""), "Bauen")
	var fm := GDScript.new()
	fm.source_code = FAKE_MAIN
	fm.reload()
	var main := Node.new()
	main.set_script(fm)
	root.add_child.call_deferred(main)
	W = Wk.new()
	W.main = main
	root.add_child.call_deferred(W)


func _process(_dt: float) -> bool:
	_n += 1
	if _n < 3:
		return false
	if FileAccess.file_exists(W.MEIN_PFAD):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(W.MEIN_PFAD))
	W.mein = {"var": {}, "done": []}
	W.open()
	eq("offen", W.is_open(), true)
	for td in W.TABS:
		var r: Dictionary = W.control({"do": "tab", "name": str(td[0])})
		eq("Reiter " + str(td[0]), r.get("tab", ""), str(td[0]))
		if str(td[0]) != "uebersicht" and str(td[0]) != "montage" and (W._w["pv"] as VBoxContainer).get_child_count() == 0:
			errs.append("Reiter %s leer" % td[0])
	var n0: int = W.all_ids().size()
	W.control({"do": "variant", "group": "gehaeuse", "value": "v52"})
	eq("v52 zeigt die Teile v5.2", W.v52, true)
	var n1: int = W.all_ids().size()
	if n1 <= n0:
		errs.append("Variante v5.2: nicht mehr Punkte (%d / %d)" % [n0, n1])
	W.control({"do": "variant", "group": "akku", "value": "netz"})
	if "e:ups" in W.all_ids() or not ("e:psu12" in W.all_ids()):
		errs.append("ohne Akku: UPS HAT noch drin oder Netzteil fehlt")
	W.control({"do": "done", "id": "m:3", "on": true})
	eq("Mein Bau", W.info().get("done", 0), 1)
	var csv: String = W._csv()
	if csv.split("\n").size() < 30 or csv.find("Raspberry Pi 5") < 0:
		errs.append("CSV zu kurz")
	W.control({"do": "step", "n": 4, "done": true})
	eq("Montage Schritt", W.info().get("step", 0), 4)
	var np: int = W.parts.size()
	if np < 40:
		errs.append("3D: nur %d Teile geladen" % np)
	W.close()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(W.MEIN_PFAD))
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://MoveEye_Einkauf.csv"))
	if errs.is_empty():
		print("Bauen-Test OK (%d Reiter, %d Punkte in «Mein Bau», %d Teile)" % [W.TABS.size(), n1, np])
		quit(0)
	else:
		push_error("Bauen-Test: " + " | ".join(errs))
		printerr("SCRIPT ERROR: Bauen-Test: " + " | ".join(errs))
		quit(1)
	return true
