extends RefCounted
## «Bildschirm wechselnd» für zwei Spieler an EINEM Bildschirm – der gemeinsame Teil von abenteuer_zweit.gd («Die Karte des
## Grossvaters» zu zweit) und maggie_zwei.gd («Maggie und der Bergkristall» für zwei Spieler), herausgezogen am 31.10.2026.
##   * zwei Ansichten nebeneinander (schmaler Platz: übereinander); sind beide näher als NEAR_IN beieinander, eine gemeinsame
##     Ansicht (wieder geteilt ab NEAR_OUT – zwei Schwellen, damit es nicht hin und her springt)
##   * jede Ansicht = SubViewportContainer + SubViewport (gleiche Welt) + Camera3D + ein Namensschild oben links
##   * Leistung: zwei Ansichten = die Welt zweimal zeichnen. Normal: volle Auflösung, Sichtweite FAR. Lite: halbe Auflösung
##     (stretch_shrink 2), Sichtweite FAR_LITE, MSAA und Schatten-Atlas aus, im geteilten Bild abwechselnd je eine Ansicht pro
##     Bild (jede mit halber Bildrate).
## Nur statische Helfer (kein eigener Zustand): die beiden Spiel-Dateien behalten ihre Spieler, Kameras und Texte.

const NEAR_IN := 18.0                # m: näher = gemeinsame Ansicht
const NEAR_OUT := 26.0               # m: weiter = wieder geteilt
const FAR := 1500.0                  # m: Sichtweite der Ansichten
const FAR_LITE := 280.0              # m: Sichtweite in Lite


static func zusammen(merged: bool, d: float, near_in := NEAR_IN, near_out := NEAR_OUT) -> bool:
	"""die Schwellen: gemeinsam unter near_in, geteilt über near_out, dazwischen bleibt es, wie es ist"""
	if merged and d > near_out:
		return false
	if not merged and d < near_in:
		return true
	return merged


static func ansicht(parent: Control, col: Color, cull_mask: int, chip_size := 15) -> Dictionary:
	"""eine Ansicht: {box, vp, cam, chip} – zuerst nicht gezeichnet (UPDATE_DISABLED)"""
	var box := SubViewportContainer.new()
	box.stretch = true
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(box)
	var vp := SubViewport.new()
	vp.handle_input_locally = false
	vp.gui_disable_input = true
	vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	vp.msaa_3d = Viewport.MSAA_DISABLED
	vp.positional_shadow_atlas_size = 1024
	box.add_child(vp)
	var cam := Camera3D.new()
	cam.fov = 70.0
	cam.near = 0.1
	cam.cull_mask = cull_mask
	vp.add_child(cam)
	var chip := Label.new()
	chip.add_theme_font_size_override("font_size", chip_size)
	chip.add_theme_color_override("font_color", Color.WHITE)
	chip.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	chip.add_theme_constant_override("outline_size", 6)
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.03, 0.05, 0.08, 0.72)
	sb.border_color = col
	sb.border_width_left = 4
	sb.set_corner_radius_all(8)
	sb.set_content_margin_all(6)
	chip.add_theme_stylebox_override("normal", sb)
	parent.add_child(chip)
	return {"box": box, "vp": vp, "cam": cam, "chip": chip}


static func teilen(a: Rect2, merged: bool) -> Array:
	"""[Rechteck 1, Rechteck 2, nebeneinander?] – gemeinsam: Rechteck 1 = alles"""
	var side := a.size.x / a.size.y >= 1.25
	if merged:
		return [a, Rect2(), side]
	if side:
		return [Rect2(a.position, Vector2(a.size.x / 2.0 - 2.0, a.size.y)),
				Rect2(a.position + Vector2(a.size.x / 2.0 + 2.0, 0), Vector2(a.size.x / 2.0 - 2.0, a.size.y)), side]
	return [Rect2(a.position, Vector2(a.size.x, a.size.y / 2.0 - 2.0)),
			Rect2(a.position + Vector2(0, a.size.y / 2.0 + 2.0), Vector2(a.size.x, a.size.y / 2.0 - 2.0)), side]


static func trennlinie(line: Control, r0: Rect2, a: Rect2, side: bool, merged: bool) -> void:
	line.visible = not merged
	line.position = (r0.position + Vector2(r0.size.x, 0)) if side else (r0.position + Vector2(0, r0.size.y))
	line.size = Vector2(4, a.size.y) if side else Vector2(a.size.x, 4)


static func zeichnen(v0: Dictionary, v1: Dictionary, second_3d: bool, lite: bool, frame: int, msaa: int) -> void:
	"""was gezeichnet wird und wie teuer (Lite und geteilt: jede Ansicht jedes zweite Bild)"""
	var vp0: SubViewport = v0["vp"]
	var vp1: SubViewport = v1["vp"]
	for bx in [v0["box"], v1["box"]]:
		if (bx as SubViewportContainer).stretch_shrink != (2 if lite else 1):
			(bx as SubViewportContainer).stretch_shrink = 2 if lite else 1
	if second_3d and lite:
		vp0.render_target_update_mode = SubViewport.UPDATE_ONCE if frame % 2 == 0 else SubViewport.UPDATE_DISABLED
		vp1.render_target_update_mode = SubViewport.UPDATE_ONCE if frame % 2 == 1 else SubViewport.UPDATE_DISABLED
	else:
		vp0.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		vp1.render_target_update_mode = SubViewport.UPDATE_ALWAYS if second_3d else SubViewport.UPDATE_DISABLED
	for v in [v0, v1]:
		(v["cam"] as Camera3D).far = FAR_LITE if lite else FAR
		(v["vp"] as SubViewport).msaa_3d = Viewport.MSAA_DISABLED if lite else msaa
		(v["vp"] as SubViewport).positional_shadow_atlas_size = 0 if lite else 1024


static func setzen(v: Dictionary, r: Rect2) -> void:
	(v["box"] as Control).position = r.position
	(v["box"] as Control).size = r.size
