extends SceneTree
## Test Fehler-QR im Simulator (ohne Bild): res://fehler_katalog.json (20–40 Fehler, real-bauen: + Hardware, 5 Sprachen, Aktionen), die Zuordnung zur
## Selbstdiagnose, die Adresse im QR-Code (nur <MoveEye>/hilfe/fehler/<ID>), der eigene QR-Encoder (fehler_hilfe.gd) Bit für
## Bit gleich wie qr_matrix von MoveEye (Teil 110, Referenz unten) und der Notfall-Start (--grafik lite).
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/fehler_qr_test.gd"   (absoluter Pfad nötig)
## FEHLER_QR_PNG=<datei>: schreibt den QR-Code als PNG (zum Lesen mit OpenCV / pyzbar).
## Ende: «Fehler-QR-Test OK» oder «SCRIPT ERROR: Fehler-QR-Test: …» (Exit-Code 0 / 1). MoveEye prüft den Katalog im Selbsttest (639u).

const REF_URL := "http://192.0.2.56:5000/hilfe/fehler/SIM_SLOW"
const REF := "111111100100110011010011101111111,100000100101011111000010101000001,101110101100010011100001001011101,101110101111101010001111101011101,101110101100100100100100101011101,100000101110011110101000001000001,111111101010101010101010101111111,000000001001100100100101000000000,101111100011011101101000101111100,110011001001100000110101111101101,011000101101100110100100111010110,000111011000101110000110110011100,001011101111000100100100010101011,000011000101001111001010010001111,000011101001000001010010000001110,000110000011101010011101010111100,111001111000101001011001000111001,101011000000101011110011111101101,011000101011111101001010111010110,101000011001011011101001011011100,111101100110011110001111110101001,101101001011111101100100010000101,101000111101010110101110101010010,101101001111111100100110010100100,100000101101011101001001111110011,000000001001001010110110100010101,111111100001100100100101101010110,100000101011100110010110100010110,101110101001001000110100111111010,101110101010110111001110000111001,101110101001001000110010111101000,100000100101010010011100100111100,111111101110001001011001111111110"

var errs := []


func eq(what: String, got, want) -> void:
	if str(got) != str(want):
		errs.append("%s: %s statt %s" % [what, got, want])


func _init() -> void:
	var FH = load("res://scripts/fehler_hilfe.gd")
	var es: Array = FH.entries()
	if es.size() < 20 or es.size() > 40:
		errs.append("%d Fehler (20–40)" % es.size())
	var acts: Dictionary = FH.katalog().get("aktionen", {})
	for e in es:
		for k in ["titel", "text", "schritte"]:
			for lg in ["de", "en", "fr", "it", "rm"]:
				if not (e.get(k, {}) as Dictionary).has(lg):
					errs.append("%s.%s: %s fehlt" % [e["id"], k, lg])
		if str(e.get("aktion", "")) != "" and not acts.has(str(e["aktion"])):
			errs.append("%s: Aktion %s unbekannt" % [e["id"], e["aktion"]])
	eq("Zuordnung gfx", FH.for_diag({"id": "gfx", "level": "bad"}).get("id", ""), "SIM_SLOW")
	eq("Zuordnung mw", FH.for_diag({"id": "mw", "level": "warn"}).get("id", ""), "SIM_NO_MW")
	eq("Zuordnung ok", FH.for_diag({"id": "gfx", "level": "ok"}).is_empty(), true)
	eq("Text fr", FH.tx(FH.entry("SIM_SLOW")["titel"], "fr"), "Simulateur trop lent")
	eq("Text rm", FH.ui("fix_now", "rm"), "Reparar ussa")
	eq("Adresse", FH.url(null, "SIM_SLOW", "http://192.0.2.56:5000/"), REF_URL)
	eq("ohne Verbindung kein QR", FH.url(null, "SIM_SLOW"), "")
	var M: Array = FH.matrix(REF_URL)
	var rows := PackedStringArray()
	for r in M:
		var s := ""
		for c in r:
			s += "1" if c else "0"
		rows.append(s)
	eq("QR gleich wie MoveEye (qr_matrix)", ",".join(rows) == REF, true)
	var ua: PackedStringArray = FH.restart_user_args(RefCounted.new(), true)
	eq("Notfall-Start", " ".join(ua).ends_with("--grafik lite"), true)
	eq("Neustart ohne Notfall", " ".join(FH.restart_user_args(RefCounted.new(), false)).find("--grafik lite") < 0, true)
	var png := OS.get_environment("FEHLER_QR_PNG")
	if png != "":
		var im: Image = FH.image(REF_URL, 8)
		if im.save_png(png) != OK:
			errs.append("PNG nicht geschrieben: " + png)
	var ep := FileAccess.get_file_as_string("res://export_presets.cfg")
	if ep != "":
		for line in ep.split("\n"):
			if line.begins_with("include_filter=") and line.find("fehler_katalog.json") < 0:
				errs.append("export_presets.cfg: fehler_katalog.json fehlt in %s" % line)
	if errs.is_empty():
		print("Fehler-QR-Test OK (%d Fehler, QR %d×%d wie MoveEye)" % [es.size(), M.size(), M.size()])
		quit(0)
	else:
		printerr("SCRIPT ERROR: Fehler-QR-Test: " + " | ".join(errs))
		quit(1)
