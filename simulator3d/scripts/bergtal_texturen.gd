extends RefCounted
## Foto-Texturen im Bergtal (3.30): Texturen aus eigenen Fotos von Elektro, mit seiner Erlaubnis (LIZENZEN.md).
## Dateien: res://texturen/*.jpg (Qualität 85, aus werkzeuge/texturen_bauen.py; Naht in der Mitte geglättet).
## Nicht benutzte Fotos liegen in texturen/unbenutzt/ (mit .gdignore: nicht importiert, nicht im Export).
##
## Wo:   Boden (bergtal_boden.gdshader: Wiese, Alpweide, Geröll, Alpenrosen am Grat, Fels der Wände, Wald von weitem),
##       Seegrund am flachen Ufer (bergsee.gdshader, nur als Grundfarbe), Strasse und Parkplätze (bergtal.gd _ribbon).
## Unscharfe Fotos (aus kleinen Ausschnitten hochskaliert): wald_von_oben_02 nur als grosse Farbflecken von weitem,
## wasser_seegrund_flach_01 nur als Grundfarbe (grobe Mip-Stufe); weg_kies, wiese_ampfer, wasser_see_tuerkis,
## wald_von_oben_01 gar nicht (texturen/unbenutzt/). Wanderwege bleiben gezeichnet.
## Schalter: «Foto-Texturen im Bergtal» (main.foto_tex, System › Grafik, Standard an). Aus = alles wie vor 3.30
## (prozedurale Farben und Rauschen; der alte Code bleibt unverändert der Rückfall).
## Lite (Raspberry Pi): nie - keine Textur wird geladen, die Shader lesen keine (photo = 0), Leistung wie bisher.
## Fehlt eine Datei (z. B. altes Paket), bleibt alles wie vorher.
## Schnee: noch kein Foto (Besitzer liefert später eines) - Schnee bleibt prozedural.

const DIR := "res://texturen/"
# Mittelwert jeder Textur (linear): Foto / Mittelwert gibt die Struktur ohne die Grundfarbe. Gebraucht für den Asphalt
# (StandardMaterial); die Shader nehmen den Mittelwert selbst aus der kleinsten Mip-Stufe (gleicher Farbraum in jedem
# Renderer - mit diesen festen Werten war das Bild in «Kompatibilität» viel zu hell), avg_* bleibt dort nur als Rückfall-Wert
const AVG := {"fels_kalk_grau_01": Color(0.0931, 0.0980, 0.0955), "fels_platte_hell_01": Color(0.4088, 0.3715, 0.3121),
		"geroell_gras_02": Color(0.2457, 0.2328, 0.1391), "wald_von_oben_02": Color(0.1331, 0.1765, 0.0953),
		"wasser_seegrund_flach_01": Color(0.1654, 0.2632, 0.1624), "weg_asphalt_01": Color(0.1112, 0.1213, 0.1272),
"wiese_alp_01": Color(0.1997, 0.2383, 0.1204),
		"wiese_alp_steinig_01": Color(0.2115, 0.2280, 0.1449), "wiese_hellgruen_01": Color(0.1085, 0.1562, 0.0410),
		"zwergstrauch_alpenrose_01": Color(0.1088, 0.1597, 0.0659)}
# Shader-Parameter des Bodens -> Datei
const GROUND := {"wiese": "wiese_alp_01", "wiese2": "wiese_hellgruen_01", "alp": "wiese_alp_steinig_01",
		"geroell": "geroell_gras_02", "rose": "zwergstrauch_alpenrose_01", "fels": "fels_kalk_grau_01",
		"fels2": "fels_platte_hell_01", "wald": "wald_von_oben_02"}

static func on(main) -> bool:
	"""Foto-Texturen jetzt? Schalter an, nicht Lite, Dateien da"""
	if main == null or not bool(main.get("foto_tex")):
		return false
	if Engine.has_meta("lite") and bool(Engine.get_meta("lite")):
		return false
	return ResourceLoader.exists(DIR + "wiese_alp_01.jpg")


static func tex(name: String) -> Texture2D:
	# no own cache (a static Dictionary with textures stays alive until exit): ResourceLoader keeps them while in use
	var p := DIR + name + ".jpg"
	return load(p) if ResourceLoader.exists(p) else null


static func _lin(c: Color) -> Vector3:
	return Vector3(c.r, c.g, c.b)


static func ground(main, mt: ShaderMaterial) -> bool:
	"""der Boden des Bergtals: die Texturen setzen (photo = 1) oder aus lassen"""
	if not on(main):
		mt.set_shader_parameter("photo", 0.0)
		return false
	for k in GROUND:
		var t := tex(GROUND[k])
		if t == null:
			mt.set_shader_parameter("photo", 0.0)
			return false
		mt.set_shader_parameter("t_" + k, t)
		mt.set_shader_parameter("avg_" + k, _lin(AVG[GROUND[k]]))
	mt.set_shader_parameter("photo", 1.0)
	return true


static func lake(main, mt: ShaderMaterial) -> void:
	var t := tex("wasser_seegrund_flach_01") if on(main) else null
	mt.set_shader_parameter("photo", 1.0 if t != null else 0.0)
	if t != null:
		mt.set_shader_parameter("t_grund", t)
		mt.set_shader_parameter("avg_grund", _lin(AVG["wasser_seegrund_flach_01"]))


static func way(main, mt: StandardMaterial3D, kind: String, tile: float) -> void:
	"""Strasse und Parkplätze (kind «asphalt»): das Foto in Weltkoordinaten (von oben), die Farbe des Wegs bleibt
	(Farbe / Mittelwert des Fotos), Kachel tile m"""
	if not on(main):
		return
	if kind != "asphalt":
		return
	var nm := "weg_asphalt_01"
	var t := tex(nm)
	if t == null:
		return
	var a: Color = AVG[nm]
	var c := mt.albedo_color.srgb_to_linear()
	mt.albedo_texture = t
	mt.albedo_color = Color(c.r / a.r, c.g / a.g, c.b / a.b, mt.albedo_color.a).linear_to_srgb()
	mt.uv1_triplanar = true
	mt.uv1_world_triplanar = true
	mt.uv1_scale = Vector3.ONE / tile
	mt.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
