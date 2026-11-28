extends SceneTree
## Test «Gang-KI» – der 8er auf Rampe 15° und Kies (gemeinsamer Teil: roboter_ki_gang_basis.gd, dort die ganze Liste). Ohne Bild.
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/roboter_ki_gang_strecken_test.gd"   (absoluter Pfad nötig)
## Ende: «Gang-KI-Strecken-Test OK» oder «SCRIPT ERROR: Gang-KI-Strecken-Test: …» (Exit-Code 0 / 1).

var basis


func _initialize() -> void:
	basis = load((get_script() as Script).resource_path.get_base_dir().path_join("roboter_ki_gang_basis.gd")).new()
	basis.start(self, "strecken", "Gang-KI-Strecken-Test")
