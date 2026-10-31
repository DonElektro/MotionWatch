extends Node
## 3D-3.97 (wish of Daniel: «mit Farben könnte man noch viel machen»): the colours and surfaces of the world like in a real
## camera picture.
##  - natural colours: every plain colour a little less saturated and never paper-white or toy-bright (natural())
##  - materials: metal (caravan, car), glass, cloth, stone/wood by the kind of surface; wet in the rain (shinier, darker)
##  - light by the time of day: blue hour after sunset, haze in the distance (aerial perspective)
##  - seasons: spring green, summer, autumn leaves, winter (grass and leaves), from the month of «Jahreszeit» / the date
## The camera colours (white balance under lamps, colour grain in the dark, colours fading at dusk) are in realism.gd.

var main
var on := true                         # natural colours + materials
var seasons_on := true
var _wet := -1.0
var _month := -1
var base_alb := {}                     # material -> its own colour (for wet darkening)
var kind_mats := {}                    # "colour|kind" -> StandardMaterial3D
var wetness := 0.0                     # 3D-3.98: the ground gets wet slowly and dries slowly (sun, wind)
var puddle := 0.0                      # puddles in the hollows after long rain
var ground_fog := 0.0                  # fog lying on the meadow (calm, humid nights and mornings)
var _tw := -1.0

# the kind of surface from the thermal key the scenes give to add_mesh
const KIND := {"caravan": [0.32, 0.25, 0.6], "car": [0.22, 0.55, 0.7], "glass": [0.04, 0.0, 0.9], "tent": [0.9, 0.0, 0.3],
		"stone": [0.88, 0.0, 0.4], "wood": [0.8, 0.0, 0.35], "metal": [0.3, 0.75, 0.6]}   # roughness, metallic, specular


static func natural(c: Color) -> Color:
	"""a colour as a real surface shows it: a little less saturated, no pure white, no glowing toy colours"""
	var s := c.s * (0.68 if c.s > 0.6 else 0.82)
	var v := minf(c.v, 0.86) * (0.92 if c.s > 0.6 else 1.0)
	var n := Color.from_hsv(c.h, s, v, c.a)
	return n


func material_for(c: Color, kind: String) -> StandardMaterial3D:
	"""the material of a plain part (add_mesh): natural colour + the surface of its kind"""
	var k := c.to_html() + "|" + kind
	if kind_mats.has(k):
		return kind_mats[k]
	var m: StandardMaterial3D = main.mat(c).duplicate()
	if on:
		m.albedo_color = natural(c)
		var p: Array = KIND.get(kind, [0.85, 0.0, 0.4])
		m.roughness = float(p[0])
		m.metallic = float(p[1])
		m.metallic_specular = float(p[2])
		if kind == "glass":
			m.albedo_color = natural(c).darkened(0.25)
	base_alb[m] = [m.albedo_color, m.roughness]
	kind_mats[k] = m
	return m


func month() -> int:
	var d: int = main.day_of_year()
	var cum := [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 366]
	for i in range(12):
		if d <= cum[i + 1]:
			return i + 1
	return 12


const GRASS := {   # month -> [grass, dry]
	1: [Color(0.42, 0.38, 0.27), Color(0.56, 0.49, 0.35)], 2: [Color(0.4, 0.38, 0.25), Color(0.55, 0.48, 0.33)],
	3: [Color(0.34, 0.4, 0.2), Color(0.5, 0.46, 0.3)], 4: [Color(0.22, 0.48, 0.14), Color(0.4, 0.5, 0.22)],
	5: [Color(0.19, 0.47, 0.12), Color(0.36, 0.48, 0.2)], 6: [Color(0.2, 0.44, 0.13), Color(0.42, 0.47, 0.22)],
	7: [Color(0.24, 0.42, 0.14), Color(0.5, 0.47, 0.24)], 8: [Color(0.3, 0.4, 0.16), Color(0.58, 0.5, 0.27)],
	9: [Color(0.3, 0.39, 0.16), Color(0.55, 0.48, 0.27)], 10: [Color(0.33, 0.37, 0.17), Color(0.56, 0.45, 0.26)],
	11: [Color(0.38, 0.36, 0.22), Color(0.52, 0.44, 0.3)], 12: [Color(0.42, 0.38, 0.27), Color(0.55, 0.48, 0.34)]}
const LEAF := {    # month -> [colour of broad leaves, how much of it] (conifers keep most of their green)
	1: [Color(0.33, 0.27, 0.2), 0.85], 2: [Color(0.33, 0.27, 0.2), 0.85], 3: [Color(0.42, 0.42, 0.22), 0.45],
	4: [Color(0.32, 0.56, 0.16), 0.4], 5: [Color(0.28, 0.52, 0.15), 0.3], 6: [Color(0.2, 0.42, 0.14), 0.0],
	7: [Color(0.2, 0.4, 0.14), 0.05], 8: [Color(0.3, 0.4, 0.14), 0.15], 9: [Color(0.52, 0.46, 0.12), 0.3],
	10: [Color(0.66, 0.34, 0.08), 0.75], 11: [Color(0.45, 0.28, 0.13), 0.8], 12: [Color(0.33, 0.27, 0.2), 0.85]}


func update() -> void:
	"""from main._update_sky: season, wet surfaces, blue hour and haze"""
	var mo := month() if seasons_on else 6
	if mo != _month:
		_month = mo
		var g: Array = GRASS[mo]
		main.grass_mat.set_shader_parameter("grass", g[0])
		main.grass_mat.set_shader_parameter("dry", g[1])
		for fm in main.foliage_mats:
			if not is_instance_valid(fm):
				continue
			if not fm.has_meta("base"):
				fm.set_meta("base", fm.get_shader_parameter("color"))
			var b: Color = fm.get_meta("base")
			var conifer := not bool(fm.get_meta("broad", false))     # spruce, fir, hedges: stay green
			var lf: Array = LEAF[mo]
			var amt: float = float(lf[1]) * (0.15 if conifer else 1.0)
			fm.set_shader_parameter("color", b.lerp(lf[0], amt))
	_ground_tick()
	var wet: float = 1.0 if main.weather == "rain" else (0.4 if main.weather == "snow" else 0.0)
	if wet != _wet and on:
		_wet = wet
		for m in base_alb.keys():
			if not is_instance_valid(m):
				continue
			var b: Array = base_alb[m]
			m.roughness = lerpf(float(b[1]), 0.22, wet * 0.75)              # wet = shinier
			m.albedo_color = (b[0] as Color).darkened(0.18 * wet)          # and darker
	# blue hour (sun 0 .. 8° below the horizon) and the haze of the distance
	var el: float = main.sun_el()
	var blue: float = clampf(1.0 - absf(el + 4.0) / 4.5, 0.0, 1.0)
	if blue > 0.0:
		main.env.ambient_light_color = main.env.ambient_light_color.lerp(Color(0.42, 0.52, 0.85), blue * 0.7)
		main.env.ambient_light_energy = maxf(main.env.ambient_light_energy, 0.08 * blue)
	var day: float = clampf((el + 6.0) / 18.0, 0.0, 1.0)
	if main.weather in ["clear", "cloudy"]:                  # blue haze in the distance (rain, fog, snow keep their grey)
		main.env.fog_light_color = main.env.fog_light_color.lerp(Color(0.62, 0.7, 0.84) * (0.05 + 0.95 * day), 0.6).lerp(Color(0.3, 0.38, 0.62), blue * 0.5)
	main.env.fog_aerial_perspective = 0.35


func _ground_tick() -> void:
	"""3D-3.98: wet ground and puddles follow the rain slowly; ground fog on calm humid nights (time runs with «x-fach»)"""
	var t: float = main.now()
	var dt: float = 0.0 if _tw < 0.0 else clampf(t - _tw, 0.0, 5.0) * float(main.speed)
	_tw = t
	var el: float = main.sun_el()
	var day: float = clampf((el + 6.0) / 18.0, 0.0, 1.0)
	if main.weather == "rain":
		wetness = minf(1.0, wetness + dt / 90.0)
		puddle = minf(1.0, puddle + dt / 900.0)
	else:
		var dry: float = (1.0 + 2.0 * day + float(main.wind) / 15.0) / 2400.0
		wetness = maxf(0.0, wetness - dt * dry)
		puddle = maxf(0.0, puddle - dt * dry * 0.4)
	if dt == 0.0 and main.weather == "rain":           # the first time (start, scene) in the rain: already wet
		wetness = 1.0
	var mats: Array = [main.grass_mat] + main.ground_mats
	for gm in mats:
		if gm != null:
			gm.set_shader_parameter("wet", wetness)
			gm.set_shader_parameter("puddle", puddle)
	var h: float = main.hour()
	var calm: bool = float(main.wind) < 12.0 and main.weather in ["clear", "cloudy"]
	var want: float = 0.0
	if calm and float(main.humidity) >= 80.0 and (h >= 21.0 or h < 9.5) and el < 12.0:
		want = clampf((float(main.humidity) - 80.0) / 15.0, 0.25, 1.0)
	if main.jahreszeiten != null:                      # «Jahreszeiten»: fog on calm autumn mornings (jahreszeiten.gd fog_want)
		want = maxf(want, main.jahreszeiten.fog_want(h, el, calm))
	ground_fog = move_toward(ground_fog, want, dt / 600.0 if dt > 0.0 else 1.0)
	main.env.fog_height = 0.6
	main.env.fog_height_density = 0.04 * ground_fog         # 3D-4.1: was 0.35 - the whole picture turned white under infrared
