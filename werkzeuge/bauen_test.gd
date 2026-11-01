extends SceneTree
## Test «Bauen» im Simulator (ohne Bild, real-bauen 01.11.2026): die Daten aus werkstatt_daten.gd (erzeugt aus
## hardware/gehaeuse/bau.json, dieselbe Quelle wie MoveEye /build) sind vollständig, das Fenster öffnet alle 10 Reiter in
## derselben Reihenfolge wie ui_gemeinsam.json «more/build/reiter», Varianten blenden Teile ein und aus, «Mein Bau» zählt.
## «Fertig kaufen» (639zj): der Hinweis steht oben, «Fertig bestellen (Anfrage)» öffnet die Rückmeldung mit Art «order» und
## dem Paket, ohne Kontakt geht nichts weg (es wird nie wirklich gesendet).
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/bauen_test.gd"   (absoluter Pfad nötig)
## Ende: «Bauen-Test OK» oder «SCRIPT ERROR: Bauen-Test: …» (Exit-Code 0 / 1).

const FAKE_MAIN := """extends Node
var ui_root = null
var gehaeuse = null
var mw := {}
var mw_t := 0.0
var mw_addr := ""
var feedback_dlg = null
var quality := 1
const VERSION := "test"
func now() -> float:
	return Time.get_ticks_msec() / 1000.0
"""

var errs := []
var W
var F
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
	F = load("res://scripts/feedback.gd").new()
	F.main = main
	main.feedback_dlg = F
	root.add_child.call_deferred(F)


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
	# real-v52-standard (01.11.2026): v5.2 is the standard (bau.json variante_standard), v5.1 stays selectable
	W.set_step(0)                                     # the tab «Montage» above started the assembly
	eq("Standard v5.2", W.v52, true)
	eq("Standard v5.2: Unterteil v5.2", W._shown("tub52"), true)
	eq("Standard v5.2: Unterteil v5.1 aus", W._shown("tub"), false)
	eq("Standard v5.2: Weitwinkel-Kamera", W._shown("wide"), true)
	eq("Standard v5.2: IR-Modul", W._shown("irled"), true)
	W.set_explode(1.0)
	eq("Explosion: Weitwinkel-Kamera", W._shown("wide"), true)
	eq("Explosion: IR-Modul", W._shown("irled"), true)
	W.set_explode(0.0)
	W.set_step(1)
	eq("Schritt 1: Unterteil v5.2 drucken", W._shown("tub52"), true)
	eq("Schritt 1: Unterteil v5.1 nicht", W._shown("tub"), false)
	W.set_step(3)
	eq("Schritt 3: Weitwinkel-Kamera kommt an die Stirnwand", W._shown("wide"), true)
	eq("Schritt 3: Kopf v5.2 noch nicht", W._shown("head52"), false)
	W.set_step(10)
	eq("Schritt 10: Kopf v5.2", W._shown("head52"), true)
	eq("Schritt 10: Kopf v5.1 nicht", W._shown("head"), false)
	W.set_step(0)
	var n1: int = W.all_ids().size()
	W.control({"do": "variant", "group": "gehaeuse", "value": "v51"})
	eq("v5.1 wählbar", W.v52, false)
	eq("v5.1: Unterteil v5.1", W._shown("tub"), true)
	eq("v5.1: keine Weitwinkel-Kamera", W._shown("wide"), false)
	var n0: int = W.all_ids().size()
	if n1 <= n0:
		errs.append("Variante v5.2: nicht mehr Punkte (%d / %d)" % [n0, n1])
	W.control({"do": "variant", "group": "gehaeuse", "value": "v52"})
	eq("v52 zeigt die Teile v5.2", W.v52, true)
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
	# real-einzelteil-vorschau: only this part, as printed, «Wo es hingehört», the print plates (same as MoveEye 639wc)
	W.set_meta("no_shell", true)                        # downloads: only remember the address
	W.control({"do": "variant", "group": "gehaeuse", "value": "v52"})
	W.select("head52")
	eq("Einzelteil: Knopf sichtbar", (W._w["solo_btn"] as Button).visible, true)
	var ei: Dictionary = W.control({"do": "solo", "id": "head52"}).get("einzel", {})
	eq("Einzelteil: Modus", ei.get("mode", ""), "teil")
	eq("Einzelteil: nur dieses Teil", ei.get("visible", []), ["head52"])
	eq("Einzelteil: Wo es hingehört", ei.get("inset", false), true)
	if str(ei.get("where", "")).find("10") < 0:
		errs.append("Einzelteil: Schritt fehlt: " + str(ei.get("where", "")))
	eq("Einzelteil: Daten", ei.get("data", false), true)
	if W.einzel.dims("head52") == "" or W.einzel.print_lines("06_Kamerakopf_v52").size() < 5:
		errs.append("Einzelteil: Grösse / Druck-Infos fehlen")
	ei = W.control({"do": "solo", "id": "tub52", "flat": true}).get("einzel", {})
	eq("Liegend: flach", ei.get("flat", false), true)
	var tb: Transform3D = (W.parts["tub52"]["mi"] as MeshInstance3D).transform
	if tb.basis.is_equal_approx(Basis.IDENTITY) or absf(tb.origin.y) > 0.2:
		errs.append("Liegend: Unterteil nicht gedreht / nicht auf der Platte: " + str(tb))
	eq("Liegend: Platte sichtbar", W.einzel._plate_root.visible, true)
	ei = W.control({"do": "plates", "n": 1}).get("einzel", {})
	eq("Platten: Modus", ei.get("mode", ""), "platten")
	eq("Platten: zwei Platten v5.2", ei.get("plates", 0), 2)
	if (ei.get("visible", []) as Array).size() < 8 or not ("lid" in ei.get("visible", [])):
		errs.append("Platte B: Teile fehlen: " + str(ei.get("visible", [])))
	if int(ei.get("boxes", 0)) < 1:
		errs.append("Platte B: Stopfen als Quader fehlen")
	ei = W.control({"do": "plates", "n": 0}).get("einzel", {})
	# real-einzelteil-2: feet and plugs are real models now (no boxes on plate A), the card is below the picture with symbols
	eq("Platte A: keine Quader mehr", ei.get("boxes", -1), 0)
	for fid in ["feet", "feet2", "feet3", "feet4", "rlplug", "micplug", "dsplug", "llplug"]:
		if not (fid in ei.get("visible", [])):
			errs.append("Platte A: %s fehlt" % fid)
	if W.einzel.lage("feet").get("unsicher", false):
		errs.append("Fuss: Lage noch geschätzt")
	var card: Control = W.einzel._ui["card"]
	if card.get_parent() != (W._w["body3d"] as Control).get_child(0):
		errs.append("Einzelteil-Karte nicht unter dem 3D-Bild")
	eq("Symbol Druckplatten", (W._w["plates_btn"] as Button).get_meta("icon", ""), "printer")
	eq("Symbol Nur dieses Teil", (W._w["solo_btn"] as Button).get_meta("icon", ""), "search")
	var tub_col: Color = (W.parts["tub52"]["mat"] as StandardMaterial3D).albedo_color
	if not tub_col.is_equal_approx(Color("#9a9ea3")):
		errs.append("Farbe Unterteil nicht #9a9ea3: " + str(tub_col))
	ei = W.control({"do": "plate_tap", "id": "rlplug", "datei": "21_Stopfen_Relais"}).get("einzel", {})
	eq("Platte: Stopfen 21 als Einzelteil", [ei.get("mode", ""), ei.get("solo", "")], ["teil", "rlplug"])
	W.control({"do": "plates", "n": 1})
	ei = W.control({"do": "plate_tap", "id": "", "datei": "15_Pupillenring"}).get("einzel", {})
	eq("Platte: Teil ohne Modell nur Infos", ei.get("pdatei", ""), "15_Pupillenring")
	W.einzel.open_url("/build/datei/x", "v5-2/MotionWatch_v5-2_Platte_A_Unterteil.3mf")
	if not str(W.einzel.last_url).ends_with("Druckdateien/v5-2/MotionWatch_v5-2_Platte_A_Unterteil.3mf"):
		errs.append("Download ohne MoveEye: GitHub erwartet, " + str(W.einzel.last_url))
	ei = W.control({"do": "plate_tap", "id": "lid", "datei": "02_Deckel_mit_Laufring"}).get("einzel", {})
	eq("Platte: Teil antippen -> Einzelteil liegend", [ei.get("mode", ""), ei.get("solo", ""), ei.get("flat", false)], ["teil", "lid", true])
	W.control({"do": "where"})
	eq("Wo es hingehört: Montage", [W.tab, W.step, W.einzel.mode], ["montage", 8, ""])
	if not (W.parts["lid"]["mi"] as MeshInstance3D).transform.basis.is_equal_approx(Basis.IDENTITY):
		errs.append("Zurück: Deckel noch gedreht")
	W.control({"do": "whole"})
	eq("Zurück zum ganzen Modell", W.info().get("einzel", {}).get("mode", "?"), "")
	W.control({"do": "step", "n": 4, "done": true})
	# «Fertig kaufen»: the hint at the top, the order goes into the feedback (kind «order», package), no contact = not sent
	var UGf = load("res://scripts/ui_gemeinsam.gd")
	var lg: String = load("res://scripts/i18n.gd").lang()          # the texts follow the language of the simulator
	var fi: Dictionary = W.info().get("fertig", {})
	eq("Fertig: Hinweis sichtbar", fi.get("shown", false), true)
	eq("Fertig: Knopf", fi.get("button", ""), UGf.fertig_text("button", lg))
	eq("Fertig: Text", fi.get("text", ""), UGf.fertig_text("hint", lg))
	eq("Fertig: Standard-Paket", fi.get("pkg", ""), "komplett")
	if (W._w["fertig"] as Control).get_index() > (W._w["tab_uebersicht"] as Control).get_parent().get_parent().get_index():
		errs.append("Fertig: Hinweis nicht über den Reitern")
	var ro: Dictionary = W.control({"do": "order", "pkg": "autark"})
	eq("Fertig: Bestellung", ro.get("ok", false), true)
	eq("Fertig: Bauen zu", W.is_open(), false)
	eq("Fertig: Rückmeldung offen", F.visible, true)
	eq("Fertig: Art", F._kind, "order")
	eq("Fertig: Paket", F._pkg, "autark")
	if F._text.text.find(str(UGf.fertig_paket("autark", lg).get("name", "?"))) < 0:
		errs.append("Fertig: Text nicht vorausgefüllt: " + F._text.text)
	eq("Fertig: Art-Knopf sichtbar", (F._kind_btns["order"] as Button).visible, true)
	eq("Fertig: Paketwahl sichtbar", F._pkg_box.visible, true)
	eq("Fertig: Kontakt-Feld", F._contact.placeholder_text, UGf.fertig_text("contact", lg))
	var waiting: int = F._load().size()
	F.fill_and_send({"kind": "order", "pkg": "basis", "text": F._text.text, "contact": "", "press": true})
	eq("Fertig: ohne Kontakt nicht gesendet", F._load().size(), waiting)
	eq("Fertig: Hinweis Kontakt", F._status.text, UGf.fertig_text("contact_needed", lg))
	if F._body("x").find("Paket: Basis") < 0:
		errs.append("Fertig: Paket fehlt in der Nachricht")
	F.visible = false
	F.open("Mehr")
	eq("Fertig: normale Rückmeldung ohne Bestellung", F._kind, "idea")
	eq("Fertig: Art-Knopf versteckt", (F._kind_btns["order"] as Button).visible, false)
	F.visible = false
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
