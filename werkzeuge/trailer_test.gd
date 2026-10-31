extends SceneTree
## Test der Trailer (trailer.gd, trailer_buehne.gd, trailer_ton.gd) ohne Bild und ohne Welt:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/trailer_test.gd"   (absoluter Pfad nötig)
## Prüft: Länge je Trailer (≈ 3 Min.), jede Einstellung hat ihre Methoden, jeder Klang lässt sich erzeugen, alle Texte
## (Tafeln, Erzähler) sind in en / fr / it / rm übersetzt, keine Spoiler-Wörter (Steinmännchen, Seeli, Kapelle am Gipfel …).
## Ende: «Trailer-Test OK» oder «SCRIPT ERROR: Trailer-Test: …» (Exit-Code 0 / 1).

var errs := []
const VERBOTEN := ["Steinm", "Seeli", "Bergkapelle", "Finale", "Karabiner", "Blechdose", "Geheimwort"]


func _init() -> void:
	var T = load("res://scripts/i18n.gd")
	var B = load("res://scripts/trailer_buehne.gd")
	var Ton = load("res://scripts/trailer_ton.gd")
	var R = load("res://scripts/trailer.gd")
	var tx: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://i18n/texte.json"))
	var keep_lang: String = T.choice()
	T.set_lang("de")                                          # the texts are checked in German (the keys of texte.json)
	var b = B.new()
	for id in R.IDS:
		var shots: Array = b.einstellungen(id)
		var d := 0.0
		for sh in shots:
			d = maxf(d, float(sh["t0"]) + float(sh["d"]))
			var auf := str(sh.get("auf", ""))
			if str(sh.get("art", "")) == "welt" and not b.has_method(auf):
				errs.append("%s: Methode %s fehlt" % [id, auf])
			for c in sh.get("ton", []):
				if str(c[1]) in ["loop", "one", "stop"] and not str(c[2]) in R.KLAENGE:
					errs.append("%s: Klang %s nicht in KLAENGE" % [id, c[2]])
			var texte := []
			for s in sh.get("say", []):
				texte.append(str(s[1]))
			for k in ["text", "sub"]:
				if sh.has(k):
					texte.append(str(sh[k]))
			for t in texte:
				for w in VERBOTEN:
					if t.contains(w):
						errs.append("%s: Spoiler-Wort «%s» in «%s»" % [id, w, t])
				for part in t.split("  ·  "):
					if part.contains("Jahren") or part.contains("Kapitel, je") or part.contains("Stunden"):
						continue                                   # (composed from texts that are translated on their own)
					var row = tx.get(part, null)
					if not (row is Dictionary):
						errs.append("%s: Text nicht in texte.json: %s" % [id, part])
						continue
					for l in ["en", "fr", "it", "rm"]:
						if str(row.get(l, "")) == "":
							errs.append("%s: %s fehlt für «%s»" % [id, l, part])
		print("Trailer %s: %d Einstellungen, %.0f s" % [id, shots.size(), d])
		if d < 165.0 or d > 195.0:
			errs.append("%s: Länge %.0f s statt etwa 180 s" % [id, d])
	b.free()
	T.set_lang(keep_lang if keep_lang != "" else "auto")
	var t0 := Time.get_ticks_msec()
	for k in R.KLAENGE:
		var w = Ton.get_snd(k)
		if w == null or w.get_length() <= 0.0:
			errs.append("Klang %s fehlt" % k)
	print("Klänge erzeugt: %d in %d ms" % [R.KLAENGE.size(), Time.get_ticks_msec() - t0])
	if errs.is_empty():
		print("Trailer-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Trailer-Test: " + str(e))
		quit(1)
