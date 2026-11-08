extends Node
## «Flora und Fauna» Paket 2: Licht / Farbstimmung NUR für die freie Ansicht (Normal / Hoch; Lite, MW_FLORA=alt und
## --quality: aus). Eine CanvasLayer (Ebene -50, unter der Bedienung) im Fenster liest das fertige 3D-Bild und stimmt es nach
## der Tageszeit: Mittag klar, goldene Stunde warm, Dämmerung leicht blau, Nacht nur wenig (die Nacht bleibt dunkel).
## Die MoveEye-Kameras (main.vps, eigene SubViewports) und das Wärmebild sehen davon nichts: ihre Bilder bleiben Pixel für
## Pixel gleich (werkzeuge/farbstimmung_pruefen.gd). Angelegt / entfernt von gras.gd (Gras.ground, bei jeder Szene).

var main
var mat: ShaderMaterial
var layers: Array = []               # [CanvasLayer] - one in the window, one per picture tool viewport (attach)
var _t := 0.0


static func ensure(m, want: bool) -> void:
	var n: Node = m.get_node_or_null("flora_licht")
	if not want:
		if n != null:
			n.queue_free()
		return
	if n == null:
		n = load("res://scripts/farbstimmung.gd").new()
		n.name = "flora_licht"
		n.main = m
		m.add_child(n)


func _ready() -> void:
	mat = ShaderMaterial.new()
	mat.shader = load("res://shaders/farbstimmung.gdshader")
	attach(self)
	_update()


func attach(parent: Node) -> CanvasLayer:
	"""eine Farbstimmungs-Ebene in parent (das Fenster: dieser Knoten; ein Bilder-Werkzeug: seine SubViewport)"""
	var cl := CanvasLayer.new()
	cl.layer = -50
	var r := ColorRect.new()
	r.material = mat
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.set_anchors_preset(Control.PRESET_FULL_RECT)
	cl.add_child(r)
	parent.add_child(cl)
	layers.append(cl)
	return cl


func _process(dt: float) -> void:
	_t -= dt
	if _t > 0.0:
		return
	_t = 0.5
	_update()


func _update() -> void:
	if main == null or mat == null:
		return
	var h: float = main.hour() if main.has_method("hour") else 13.0
	# 0 at noon … 1 in the golden hour (sun low: 1.5 h after sunrise / before sunset, roughly), night: 2
	var gold := clampf(1.0 - absf(h - 13.0) / 6.0, 0.0, 1.0)
	gold = 1.0 - gold                                         # far from noon -> golden
	var dark: bool = main.has_method("is_dark") and main.is_dark()
	# owner 08.11.2026: about half the earlier strength - noon nearly neutral, evening only gently warm, night only slightly blue
	var tint := Vector3(1.0, 1.0, 1.0).lerp(Vector3(1.035, 1.0, 0.94), smoothstep(0.55, 0.9, gold))
	var lift := Vector3(0.0, 0.002, 0.006)
	var sat := 1.02
	var con := 0.025
	var vign := 0.08
	if dark:
		tint = Vector3(0.98, 0.99, 1.025)                     # night: a little blue, not brighter
		lift = Vector3(0.0, 0.0, 0.003)
		sat = 0.96
		con = 0.03
	mat.set_shader_parameter("tint", tint)
	mat.set_shader_parameter("lift", lift)
	mat.set_shader_parameter("sat", sat)
	mat.set_shader_parameter("contrast", con)
	mat.set_shader_parameter("vign", vign)
