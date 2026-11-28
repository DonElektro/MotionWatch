extends RefCounted
## «Figuren matt» (Idee #45, 28.11.2026): ein weicher Kontaktschatten unter den Füssen jeder menschlichen Figur
## (Besucher, Held, Erkunden-Figur; Tiere nicht). Billig für jede Grafikstufe (auch Lite / Pi): eine flache Scheibe mit
## einem runden Verlauf, die den Boden darunter nur abdunkelt (schwarz mit weichem Alpha, ohne Licht, ohne Nebel, wirft
## keinen Schatten, nicht im Wärmebild). Nachts bleibt dunkler Boden dunkel - die Scheibe leuchtet nie.
## (Nicht «multiplizieren» (BLEND_MODE_MUL): im Compatibility-Renderer mit Glow wird daraus ein dunkles Viereck.)
## Auf Hügeln (main.hilly) legt sie sich alle ~0,25 s schräg wie der Boden; liegt die Figur (Kriechen), wird sie länger.
## Texturen und Material sind einmal gemacht und von allen Figuren geteilt.

const MITTE := 0.55                 # so hell bleibt der Boden in der Mitte (1 = gar kein Schatten)
const BREIT := 0.8                  # m quer (Schultern)
const LANG := 0.95                  # m längs (Schritt)
const HOEHE := 0.025                # m über den Füssen (kein Flimmern mit dem Boden)

static var _mat: StandardMaterial3D = null
static var _mesh: PlaneMesh = null


static func _textur() -> Texture2D:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	for y in range(n):
		for x in range(n):
			var dx := (x + 0.5) / n * 2.0 - 1.0
			var dy := (y + 0.5) / n * 2.0 - 1.0
			var r := sqrt(dx * dx + dy * dy)
			var f := 1.0 - smoothstep(0.0, 1.0, r)                   # 1 in der Mitte, 0 am Rand
			var v := lerpf(1.0, MITTE, pow(f, 1.6))                  # so viel Boden bleibt
			img.set_pixel(x, y, Color(0, 0, 0, 1.0 - v))
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


static func material() -> StandardMaterial3D:
	if _mat == null:
		_mat = StandardMaterial3D.new()
		_mat.resource_name = "kontaktschatten"
		_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_mat.albedo_color = Color(0, 0, 0, 1)
		_mat.albedo_texture = _textur()
		_mat.disable_fog = true
		_mat.disable_receive_shadows = true
		_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		_mat.texture_repeat = false
		_mat.render_priority = -1
	return _mat


static func bauen(a) -> MeshInstance3D:
	"""die Scheibe unter der Figur a (actor.gd, Person) - Kind von a, folgt Ort und Richtung"""
	if _mesh == null:
		_mesh = PlaneMesh.new()
		_mesh.size = Vector2(1, 1)
	var mi := MeshInstance3D.new()
	mi.name = "Kontaktschatten"
	mi.set_meta("kontaktschatten", true)            # Boxen / Grössen / Umfärben der Figur (dataset, gamelearn, vielfalt, fotomodus, web_demo) lassen sie aus
	mi.mesh = _mesh
	mi.material_override = material()
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	var k: float = (a.body_root as Node3D).scale.y if a.body_root != null else 1.0
	mi.scale = Vector3(BREIT * k, 1.0, LANG * k)
	mi.position = Vector3(0, HOEHE, 0)
	a.add_child(mi)
	return mi


static func tick(a, mi: MeshInstance3D) -> void:
	"""alle ~0,25 s (actor.gd _process): schräg wie der Boden, länger beim Liegen"""
	mi.visible = a.body_root == null or (a.body_root as Node3D).visible   # unsichtbarer Träger (gamejaeger.gd): kein Schatten
	var k: float = (a.body_root as Node3D).scale.y if a.body_root != null else 1.0
	var lang: float = LANG * k * (1.0 + 1.3 * clampf(float(a.prone), 0.0, 1.0))
	var main = a.main
	var b := Basis.IDENTITY
	if main != null and main.hilly():
		var p: Vector3 = a.global_position
		var e := 0.35
		var hx: float = main.ground_y(p.x + e, p.z) - main.ground_y(p.x - e, p.z)
		var hz: float = main.ground_y(p.x, p.z + e) - main.ground_y(p.x, p.z - e)
		var nrm := Vector3(-hx, 2.0 * e, -hz).normalized()
		if nrm.dot(Vector3.UP) > 0.5:                                    # Wand / Kante: flach lassen
			var q := Quaternion(Vector3.UP, nrm)
			b = (a.global_transform.basis as Basis).orthonormalized().inverse() * Basis(q)
	mi.basis = b * Basis.from_scale(Vector3(BREIT * k, 1.0, lang))
