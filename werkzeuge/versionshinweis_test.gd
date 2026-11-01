extends SceneTree
## Test ohne Bild für den Versionshinweis (abgleich.gd, 3.44.2): Platz unten rechts im 3D-Bild bei 1920×1080 mit offenem
## Seitenmenü - weicht der Leiste unten, dem Mover-Feld und dem Gerät-Fenster aus, bleibt links vom Seitenmenü;
## die kurzen Texte gibt es in allen Sprachen (i18n/texte.json).
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/versionshinweis_test.gd"   (absoluter Pfad nötig)
## Ende: «Versionshinweis-Test OK» oder «SCRIPT ERROR: Versionshinweis-Test: …» (Exit-Code 0 / 1).

var errs := []


func check_spot(A, name: String, sz: Vector2, vs: Vector2, right: float, obs: Array) -> Vector2:
	var p: Vector2 = A.ver_spot(sz, vs, right, obs)
	var r := Rect2(p, sz)
	if r.position.x < 0.0 or r.position.y < 0.0 or r.end.x > right + 0.5 or r.end.y > vs.y + 0.5:
		errs.append("%s: ausserhalb %s (frei bis x=%d)" % [name, r, right])
	for o in obs:
		if (o as Rect2).intersects(r):
			errs.append("%s: %s deckt %s" % [name, r, o])
	if r.position.y < vs.y * 0.5:
		errs.append("%s: nicht unten (%s)" % [name, r])
	return p


func _init() -> void:
	var A = load("res://scripts/abgleich.gd")
	var vs := Vector2(1920, 1080)
	var right := 1920.0 - 555.0                                     # Seitenmenü offen (555 px wie bei Daniel)
	var sz := Vector2(330, 34)
	var bar := Rect2((right - 568.0) / 2.0, vs.y - 66.0, 568.0, 54.0)   # Leiste unten in der Mitte
	var geraet := Rect2(right - 300.0, 8.0, 292.0, 124.0)            # Gerät (LED und Tasten), oben rechts
	var pad := Rect2(right - 176.0, vs.y - 226.0, 164.0, 214.0)      # Mover fahren, unten rechts
	var p0 := check_spot(A, "ohne Mover", sz, vs, right, [bar, geraet])
	if p0.x + sz.x < right - 20.0:
		errs.append("ohne Mover: nicht rechts (%s)" % p0)
	var p1 := check_spot(A, "mit Mover", sz, vs, right, [bar, geraet, pad])
	if p1.x + sz.x > pad.position.x:
		errs.append("mit Mover: nicht links vom Mover-Feld (%s)" % p1)
	check_spot(A, "Seitenmenü zu", sz, vs, 1920.0, [Rect2((1920.0 - 568.0) / 2.0, vs.y - 66.0, 568.0, 54.0)])
	check_spot(A, "kleines Fenster", Vector2(460, 34), Vector2(1280, 720), 1280.0 - 400.0,
			[Rect2((880.0 - 568.0) / 2.0, 720.0 - 66.0, 568.0, 54.0), Rect2(880.0 - 176.0, 720.0 - 226.0, 164.0, 214.0)])
	# the texts in every language, one line (no letter-by-letter wrap: the label has no autowrap)
	var tx = JSON.parse_string(FileAccess.get_file_as_string("res://i18n/texte.json"))
	for k in ["⚠ MoveEye %s älter", "⚠ Simulator %s älter", "Hinweis ausblenden (erscheint wieder, wenn sich eine Version ändert)"]:
		var row = tx.get(k) if typeof(tx) == TYPE_DICTIONARY else null
		if typeof(row) != TYPE_DICTIONARY:
			errs.append("Text fehlt: " + k)
			continue
		for l in ["en", "fr", "it", "rm"]:
			if str(row.get(l, "")) == "":
				errs.append("Übersetzung fehlt (%s): %s" % [l, k])
	var src := FileAccess.get_file_as_string("res://scripts/abgleich.gd")
	if not src.contains("_ver_l.autowrap_mode = TextServer.AUTOWRAP_OFF"):
		errs.append("Versionshinweis ohne AUTOWRAP_OFF (Buchstaben-Umbruch)")
	if A.VER_MIN < 200.0 or A.VER_MAX > 520.0 or A.VER_MIN >= A.VER_MAX:
		errs.append("Breite %s–%s" % [A.VER_MIN, A.VER_MAX])
	if errs.is_empty():
		print("Versionshinweis-Test OK")
		quit(0)
	else:
		push_error("Versionshinweis-Test: " + "; ".join(errs))
		quit(1)
