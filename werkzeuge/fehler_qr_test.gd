extends SceneTree
## Test Fehler-QR im Simulator (ohne Bild): res://fehler_katalog.json (20–30 Fehler, 5 Sprachen, Aktionen), die Zuordnung zur
## Selbstdiagnose, die Adresse im QR-Code (nur <MoveEye>/hilfe/fehler/<ID>), der eigene QR-Encoder (fehler_hilfe.gd) Bit für
## Bit gleich wie qr_matrix von MoveEye (Teil 110, Referenz unten) und der Notfall-Start (--grafik lite).
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/fehler_qr_test.gd"   (absoluter Pfad nötig)
## FEHLER_QR_PNG=<datei>: schreibt den QR-Code als PNG (zum Lesen mit OpenCV / pyzbar).
## Ende: «Fehler-QR-Test OK» oder «SCRIPT ERROR: Fehler-QR-Test: …» (Exit-Code 0 / 1). MoveEye prüft den Katalog im Selbsttest (639s).

const REF_URL := "http://192.168.1.56:5000/hilfe/fehler/SIM_SLOW"
const REF := "111111101000101111001111101111111,100000100101100001010110101000001,101110100010010000001100101011101,101110101011001101101101001011101,101110101101111000111110001011101,100000101011010010110000101000001,111111101010101010101010101111111,000000001010101111000111100000000,100010111110101001110101011111001,010110010100111110001001100001110,101010110101100111000001100001010,101011010000001101110101011000010,001000110101111100101000101101001,110000011100000010010100011100000,110000100100101011010001100001010,010101000101000001011110010000000,101101101101000101100100011010010,000000010000110111001111100001110,111111100110110100100001001001010,110110001010000110011010110000001,101110110111000110010011001011001,101111011010011000111000011001010,001111101000001101001111101101010,000011010010011111000100110110001,111001110001101001110101111110000,000000001110110110101000100010110,111111101001111111001110101011010,100000100111001111101101100011011,101110101000001100111000111111000,101110100100010011010110011011110,101110100010100010110001011110000,100000100001001001111110011100000,111111101111001101000101101011001"

var errs := []


func eq(what: String, got, want) -> void:
	if str(got) != str(want):
		errs.append("%s: %s statt %s" % [what, got, want])


func _init() -> void:
	var FH = load("res://scripts/fehler_hilfe.gd")
	var es: Array = FH.entries()
	if es.size() < 20 or es.size() > 30:
		errs.append("%d Fehler (20–30)" % es.size())
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
	eq("Adresse", FH.url(null, "SIM_SLOW", "http://192.168.1.56:5000/"), REF_URL)
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
