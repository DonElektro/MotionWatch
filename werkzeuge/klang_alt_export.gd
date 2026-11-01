extends SceneTree
## Die alten, im Code erzeugten Trailer-Klänge (trailer_ton.gd synth) als WAV-Dateien – für werkzeuge/klang_bauen.py
## (die Tierstimmen bleiben die bisherigen und werden dort nur in einen Raum gesetzt) und zum Vergleichen.
##   cd simulator3d && KLANG_OUT=/ordner <godot> --headless --path . -s "$PWD/../werkzeuge/klang_alt_export.gd"


func _init() -> void:
	var R = load("res://scripts/trailer.gd")
	var Ton = load("res://scripts/trailer_ton.gd")
	var out := OS.get_environment("KLANG_OUT")
	if out == "":
		printerr("KLANG_OUT fehlt")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(out)
	for k in R.KLAENGE:
		var w: AudioStreamWAV = Ton.synth(k)
		if w != null:
			w.save_to_wav(out.path_join(k + ".wav"))
	print("Alte Klänge: %d nach %s" % [R.KLAENGE.size(), out])
	quit()
