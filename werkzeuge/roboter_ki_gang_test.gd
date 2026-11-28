extends SceneTree
## Test «Gang-KI» – Sehen, Schnittstelle für Stufe 3, 8er an der Stufe 6 cm und an der Lücke 15 cm (gemeinsamer Teil: roboter_ki_gang_basis.gd, dort die ganze Liste). Ohne Bild.
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/roboter_ki_gang_test.gd"   (absoluter Pfad nötig)
## Ende: «Gang-KI-Test OK» oder «SCRIPT ERROR: Gang-KI-Test: …» (Exit-Code 0 / 1).

var basis


func _initialize() -> void:
	basis = load((get_script() as Script).resource_path.get_base_dir().path_join("roboter_ki_gang_basis.gd")).new()
	basis.start(self, "sehen", "Gang-KI-Test")
