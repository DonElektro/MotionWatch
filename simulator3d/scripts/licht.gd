extends Node
## «Licht & Nacht» (Zweig real-licht, 31.10.2026): Himmel und Lichter wie echt - nachts zählt MoveEye am meisten.
##  Himmel
##   - Sonne: main.sun_pos() (NOAA, Ort der Karte, sonst Schweiz). Dämmerung: bürgerlich (Sonne bis −6°), nautisch (−12°),
##     astronomisch (−18°), danach Nacht - mit Helligkeit in Lux (Tabelle nach Messungen, log-interpoliert).
##   - Mond: Ort (Höhe, Richtung) und Phase aus Datum und Uhrzeit der Simulation (Bahnformeln nach P. Schlyter, ~1°),
##     Licht: Vollmond hoch ~0,25 lx, Halbmond ~0,03 lx, Neumond 0 (dann nur Sterne / Luftleuchten ~0,001 lx).
##     «Mondphase fest» (main.moon_auto aus, Regler «Mond» = beleuchteter Teil): der Mond steht dort, wo er bei dieser
##     Phase stünde (Winkel zur Sonne).
##   - Sterne nur bei Dunkelheit, drehen mit dem Himmel (Sternzeit), weniger bei Dämmerung, hellem Mond, Lichtverschmutzung.
##   - Lichtverschmutzung Land / Dorf / Stadt («auto» nach Szene): Himmel leuchtet orange, tiefe Wolken werfen das
##     Stadtlicht zurück (Stadt + bedeckt heller als Land + klar).
##   - Wolken (main.clouds(), also das Wetter) dämpfen Sonne, Mond und Sterne.
##   - Tiefe Sonne: lange Schatten (das Sonnenlicht bleibt bis kurz vor dem Horizont kräftig, warm), Sonne im Bild einer
##     Kamera -> Dunst und Lens-Flare im Kamerabild (lens.gdshader «glare», nur wenn «Gegenlicht» nicht von Hand an ist).
##  Lichter
##   - Platzlampen (Strassenlampen der Szenen und des Katalogs): an, wenn es dämmert (Sonne unter −2,5°), ein Teil mit
##     Zeitschaltung (aus 0:30–5:00). Einstellung Platzbeleuchtung automatisch / an / aus.
##   - Zeltlaternen: Zelte leuchten abends von innen (jedes Zelt bis zu seiner Schlafenszeit 22–23:40), Wohnwagen- und
##     Hausfenster ebenso (einige bleiben länger an); morgens kurz vor Sonnenaufgang wieder.
##   - Haken: attach_lamp(figur, "head"|"hand") - Stirn- oder Taschenlampe an eine Figur; add_headlights(knoten) -
##     Scheinwerfer an ein Auto / Fahrzeug; set_headlights(knoten, an).
##   - API für Blendung (Kamera-Paket): sources(cam) - alle Lichter mit Ort, Stärke (cd), Farbe, an/aus, Bildpunkt in der
##     Kamera; lux_at(ort) - Beleuchtung an einem Ort; sky - Himmel jetzt (Phase, Lux, Sonne, Mond).
##  Lite: höchstens 4 Platzlampen werfen Licht (die nächsten), keine Lichtquellen in Zelten (nur das Leuchten), keine
##  Schatten kleiner Lichter. Normal: die nächste brennende Platzlampe wirft Schatten.
##  Während Testlauf / Prüfstand schalten Lampen und Fenster wie bisher (nur «dunkel»), damit die Läufe vergleichbar bleiben.
## Einstellungen in user://licht.json. Test: /control {"action": "licht", "do": info | set (key, value) | sources (cam) |
## lux (x, y, z) | attach (i, kind) | at (hour, month)}.

const T = preload("res://scripts/i18n.gd")
const Quality = preload("res://scripts/quality.gd")
const FILE := "user://licht.json"
const SAVE := ["lp_mode", "platz_mode", "home_lights"]

var main
var lp_mode := "auto"            # Lichtverschmutzung: auto | land | dorf | stadt
var platz_mode := "auto"         # Platzbeleuchtung: auto | on | off
var home_lights := true          # Zelte und Fenster nach der Uhrzeit (sonst wie bisher: Fenster immer an, wenn dunkel)

const LP_OPTS := [["auto", "automatisch (nach Szene)"], ["land", "Land (dunkler Himmel)"], ["dorf", "Dorf"], ["stadt", "Stadt"]]
const PLATZ_OPTS := [["auto", "automatisch (Dämmerung, teils Zeitschaltung)"], ["on", "immer an"], ["off", "aus"]]
const LP_AUTO := {"parkplatz": "stadt", "stellplatz": "stadt", "baustelle": "stadt", "garten": "dorf", "zuhause": "dorf",
		"camping_voll": "dorf", "velodieb": "dorf", "schlafzimmer": "dorf"}
const LP_LUX := {"land": 0.0, "dorf": 0.004, "stadt": 0.035}       # Himmelsleuchten bei klarem Himmel (lx)
const LP_GLOW := {"land": 0.0, "dorf": 0.35, "stadt": 1.0}         # orange Kuppel (Stärke wie bisher «Stadt» = 1)
const LP_STARS := {"land": 1.0, "dorf": 0.6, "stadt": 0.22}        # Anteil der sichtbaren Sterne
# Beleuchtung durch Sonne / Dämmerhimmel auf dem Boden bei klarem Himmel: [Sonnenhöhe °, lx]
const TW := [[-18.0, 0.0007], [-15.0, 0.002], [-12.0, 0.008], [-10.0, 0.06], [-8.0, 0.6], [-6.0, 3.4], [-4.0, 15.0],
		[-2.0, 80.0], [0.0, 400.0], [2.0, 1500.0], [5.0, 5000.0], [10.0, 15000.0], [20.0, 40000.0], [40.0, 75000.0],
		[60.0, 95000.0], [90.0, 110000.0]]
const SKY_LUX := 0.0009                 # Sterne + Luftleuchten (Neumond, klar, Land: zusammen ~0,001 lx)
const MOON_LUX := 0.32                  # Vollmond im Zenit ohne Luft (mit Luft ~0,25 lx)
# geschätzte Lichtstärke (Candela) pro Art - für sources() / lux_at() (Kamera-Paket: Blendung)
const CD := {"platz": 1500.0, "lampe": 400.0, "feuer": 250.0, "zelt": 25.0, "fenster": 40.0, "taschenlampe": 600.0,
		"stirnlampe": 300.0, "scheinwerfer": 12000.0, "velo": 400.0, "weisslicht": 2500.0, "ir": 0.0}
const PLATZ_LITE := 4                   # Lite: so viele Platzlampen werfen Licht

var sky := {}                           # der Himmel jetzt (update): phase, lux, sun_el, sun_az, moon_el, moon_az, moon_illum …
var _platz: Array = []                  # [{l: OmniLight3D, glow: [MeshInstance3D], timer: bool}]
var _tents: Array = []                  # [{meshes, mats, light, pos, bed}]
var _wins: Array = []                   # [{mat, pos, bed, early}]
var _extra: Array = []                  # angehängte Lampen / Scheinwerfer: {node, lights: [SpotLight3D], mats, kind, force}
var _shadow_lamp: OmniLight3D = null
var _glare := [0.0, 0.0]
var _t_override := {}                   # nur für Tests: feste Stunde / Monat


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		for k in SAVE:
			if d.has(k):
				set(k, d[k] if typeof(get(k)) != TYPE_BOOL else bool(d[k]))


func save() -> void:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


func add_controls() -> void:
	var m = main
	var sub := {"sub": "Licht & Nacht"}
	m.add_control("select", "licht_lp", "Lichtverschmutzung (Himmel nachts, Sterne)", func(): return lp_mode,
			func(v): lp_mode = str(v); save(); main._update_sky(), "Szene", {"sub": "Licht & Nacht", "options": LP_OPTS})
	m.add_control("select", "licht_platz", "Platzbeleuchtung (Strassen- und Platzlampen)", func(): return platz_mode,
			func(v): platz_mode = str(v); save(); main._update_sky(), "Szene", {"sub": "Licht & Nacht", "options": PLATZ_OPTS})
	m.add_control("toggle", "licht_home", "Zelte und Fenster leuchten abends, bis die Leute schlafen", func(): return home_lights,
			func(v): home_lights = bool(v); save(); main._update_sky(), "Szene", {"sub": "Licht & Nacht", "expert": true})
	m.add_control("button", "licht_info", "Himmel jetzt (Dämmerung, Mond, Helligkeit in Lux)", null,
			func(): main.start_info = summary(), "Szene", sub)


# ---- astronomy ------------------------------------------------------------------------------------------------------
func _place() -> Vector2:
	return Vector2(main.ort_lat if main.ort_lat != 0.0 else 46.8, main.ort_lon if main.ort_lon != 0.0 else 8.2)   # wie main.sun_pos


func _doy() -> int:
	return int(_t_override.get("doy", main.day_of_year()))


func sim_day() -> float:
	"""days since 2000 Jan 0.0 UT of the moment the simulation shows (date like main.day_of_year, Swiss time like sun_pos)"""
	var y: int = int(Time.get_date_dict_from_system()["year"])
	var doy := _doy()
	var tz := 2.0 if doy >= 88 and doy < 300 else 1.0
	var h: float = float(_t_override.get("hour", main.hour()))
	var d0: int = 367 * y - (7 * y) / 4 + 30 - 730530             # 2000 Jan 0 = 0 (Schlyter)
	return float(d0 + doy) + (h - tz) / 24.0


static func _rev(x: float) -> float:
	return fposmod(x, 360.0)


static func ephem(d: float) -> Dictionary:
	"""sun and moon (ecliptic longitude / latitude in degrees, moon distance in earth radii), obliquity and GMST0 - low
	precision (about 1-2 arc minutes for the sun, ~0.5° for the moon), formulas of P. Schlyter «How to compute planetary positions»"""
	var ws := 282.9404 + 4.70935e-5 * d
	var es := 0.016709 - 1.151e-9 * d
	var Ms := _rev(356.0470 + 0.9856002585 * d)
	var Mr := deg_to_rad(Ms)
	var E := Mr + es * sin(Mr) * (1.0 + es * cos(Mr))
	var xv := cos(E) - es
	var yv := sqrt(1.0 - es * es) * sin(E)
	var slon := _rev(rad_to_deg(atan2(yv, xv)) + ws)
	# moon
	var N := deg_to_rad(_rev(125.1228 - 0.0529538083 * d))
	var inc := deg_to_rad(5.1454)
	var wm := _rev(318.0634 + 0.1643573223 * d)
	var a := 60.2666
	var em := 0.0549
	var Mm := _rev(115.3654 + 13.0649929509 * d)
	var M := deg_to_rad(Mm)
	var Em := M + em * sin(M) * (1.0 + em * cos(M))
	for _i in range(4):
		Em = Em - (Em - em * sin(Em) - M) / (1.0 - em * cos(Em))
	var xm := a * (cos(Em) - em)
	var ym := a * sqrt(1.0 - em * em) * sin(Em)
	var v := atan2(ym, xm)
	var r := sqrt(xm * xm + ym * ym)
	var vw := v + deg_to_rad(wm)
	var xh := r * (cos(N) * cos(vw) - sin(N) * sin(vw) * cos(inc))
	var yh := r * (sin(N) * cos(vw) + cos(N) * sin(vw) * cos(inc))
	var zh := r * sin(vw) * sin(inc)
	var mlon := rad_to_deg(atan2(yh, xh))
	var mlat := rad_to_deg(atan2(zh, sqrt(xh * xh + yh * yh)))
	# the biggest disturbances (sun pulls on the moon)
	var Ls := _rev(Ms + ws)
	var Lm := _rev(rad_to_deg(N) + wm + Mm)
	var D := deg_to_rad(Lm - Ls)
	var F := deg_to_rad(Lm - rad_to_deg(N))
	var mm := deg_to_rad(Mm)
	var ms := deg_to_rad(Ms)
	mlon += -1.274 * sin(mm - 2 * D) + 0.658 * sin(2 * D) - 0.186 * sin(ms) - 0.059 * sin(2 * mm - 2 * D) \
			- 0.057 * sin(mm - 2 * D + ms) + 0.053 * sin(mm + 2 * D) + 0.046 * sin(2 * D - ms) + 0.041 * sin(mm - ms) \
			- 0.035 * sin(D) - 0.031 * sin(mm + ms) - 0.015 * sin(2 * F - 2 * D) + 0.011 * sin(mm - 4 * D)
	mlat += -0.173 * sin(F - 2 * D) - 0.055 * sin(mm - F - 2 * D) - 0.046 * sin(mm + F - 2 * D) + 0.033 * sin(F + 2 * D) \
			+ 0.017 * sin(2 * mm + F)
	r += -0.58 * cos(mm - 2 * D) - 0.46 * cos(2 * D)
	return {"slon": slon, "mlon": _rev(mlon), "mlat": mlat, "mr": r, "ecl": 23.4393 - 3.563e-7 * d, "gmst0": _rev(Ls + 180.0)}


static func ecl_to_altaz(lon: float, lat: float, ecl: float, lst: float, phi: float) -> Vector2:
	"""ecliptic (degrees) -> (altitude, azimuth from north) at the local sidereal time lst (degrees) and latitude phi"""
	var lo := deg_to_rad(lon)
	var la := deg_to_rad(lat)
	var e := deg_to_rad(ecl)
	var x := cos(lo) * cos(la)
	var y := sin(lo) * cos(la)
	var z := sin(la)
	var ye := y * cos(e) - z * sin(e)
	var ze := y * sin(e) + z * cos(e)
	var ra := atan2(ye, x)
	var dec := atan2(ze, sqrt(x * x + ye * ye))
	var ha := deg_to_rad(lst) - ra
	var p := deg_to_rad(phi)
	var hx := cos(ha) * cos(dec)
	var hy := sin(ha) * cos(dec)
	var hz := sin(dec)
	var xh := hx * sin(p) - hz * cos(p)
	var zh := hx * cos(p) + hz * sin(p)
	var az := _rev(rad_to_deg(atan2(hy, xh)) + 180.0)
	var alt := rad_to_deg(asin(clampf(zh, -1.0, 1.0)))
	return Vector2(alt, az)


static func tw_lux(el: float) -> float:
	"""ground illuminance from the sun and the twilight sky at this sun elevation, clear sky (lx)"""
	if el <= TW[0][0]:
		return 0.0
	for i in range(1, TW.size()):
		if el <= TW[i][0]:
			var a: Array = TW[i - 1]
			var b: Array = TW[i]
			var t := (el - float(a[0])) / (float(b[0]) - float(a[0]))
			return exp(lerpf(log(float(a[1])), log(float(b[1])), t))
	return float(TW[-1][1])


static func phase_of(el: float) -> String:
	if el > -0.833:
		return "tag"
	if el > -6.0:
		return "buergerlich"
	if el > -12.0:
		return "nautisch"
	if el > -18.0:
		return "astronomisch"
	return "nacht"


const PHASE_DE := {"tag": "Tag", "buergerlich": "Bürgerliche Dämmerung", "nautisch": "Nautische Dämmerung",
		"astronomisch": "Astronomische Dämmerung", "nacht": "Nacht"}


static func airmass(alt: float) -> float:
	return 1.0 / (sin(deg_to_rad(maxf(alt, -0.5))) + 0.50572 * pow(maxf(alt, -0.5) + 6.07995, -1.6364))   # Kasten-Young


func lp_kind() -> String:
	if lp_mode in ["land", "dorf", "stadt"]:
		return lp_mode
	return LP_AUTO.get(main.scene, "land")


func compute() -> Dictionary:
	"""the sky now: sun, twilight, moon, light pollution, clouds -> illuminance (lx) on the ground"""
	var pl := _place()
	var sp: Vector2 = main.sun_pos() if _t_override.is_empty() else _sun_override()
	var el := sp.x
	var d := sim_day()
	var e := ephem(d)
	var h: float = float(_t_override.get("hour", main.hour()))
	var doy := _doy()
	var tz := 2.0 if doy >= 88 and doy < 300 else 1.0
	var lst := _rev(float(e["gmst0"]) + (h - tz) * 15.0 + pl.y)
	var mlon: float = e["mlon"]
	var mlat: float = e["mlat"]
	var mr: float = e["mr"]
	if not main.moon_auto:                                 # «Mondphase fest»: the moon where it would stand at this phase
		var k := clampf(float(main.moon), 0.0, 1.0)
		mlon = _rev(float(e["slon"]) + rad_to_deg(acos(1.0 - 2.0 * k)))
		mlat = 0.0
		mr = 60.3
	var mp := ecl_to_altaz(mlon, mlat, e["ecl"], lst, pl.x)
	mp.x -= rad_to_deg(asin(1.0 / mr)) * cos(deg_to_rad(mp.x))      # parallax: seen from the ground the moon stands lower
	var elong := rad_to_deg(acos(clampf(cos(deg_to_rad(mlon - float(e["slon"]))) * cos(deg_to_rad(mlat)), -1.0, 1.0)))
	var illum := (1.0 - cos(deg_to_rad(elong))) / 2.0
	var age := _rev(mlon - float(e["slon"])) / 360.0       # 0 new, 0.5 full (for the shape in the sky shader)
	var cl: float = main.clouds()
	var trans := 1.0 - 0.78 * pow(cl, 1.3)                 # clouds let this much through (overcast ~25 %)
	var hills: float = main.sun_behind_hills() if _t_override.is_empty() and main.terrain and el > 0.0 else 0.0   # (below the horizon it is 1 anyway)
	var l_sun := tw_lux(el) * trans * (1.0 - 0.6 * hills)      # behind a mountain: no direct sun, the sky still bright
	var l_moon := 0.0
	if mp.x > -1.0:
		var pa := 180.0 - elong                            # phase angle
		var mag := 0.026 * pa + 4e-9 * pow(pa, 4.0)        # brightness of the moon from its phase (Allen), 0 = full
		var ext := pow(10.0, -0.4 * 0.22 * minf(airmass(mp.x), 40.0))
		l_moon = MOON_LUX * pow(10.0, -0.4 * mag) * pow(60.27 / mr, 2.0) * maxf(sin(deg_to_rad(mp.x)), 0.0) * ext
		l_moon *= smoothstep(-1.0, 2.0, mp.x) * trans
	var lk := lp_kind()
	var l_lp: float = float(LP_LUX[lk]) * (1.0 + 3.2 * cl)             # low clouds throw the light of the town back
	var l_bg := SKY_LUX * (1.0 - 0.7 * cl)
	var night_lux := l_moon + l_bg + l_lp
	var dark_k := smoothstep(-3.0, -14.0, el)              # how dark the sky is for the stars
	var moon_up := smoothstep(-1.0, 5.0, mp.x)
	var stars := dark_k * float(LP_STARS[lk]) * (1.0 - 0.45 * illum * moon_up)
	sky = {"phase": phase_of(el), "sun_el": snappedf(el, 0.01), "sun_az": snappedf(sp.y, 0.01),
			"moon_el": snappedf(mp.x, 0.01), "moon_az": snappedf(mp.y, 0.01), "moon_illum": snappedf(illum, 0.001),
			"moon_age": snappedf(age, 0.001), "moon_auto": bool(main.moon_auto), "clouds": snappedf(cl, 0.01),
			"lux": _r(l_sun + night_lux), "lux_sun": _r(l_sun), "lux_moon": _r(l_moon), "lux_sky": _r(l_bg), "lux_lp": _r(l_lp),
			"night_lux": _r(night_lux), "lp": lk, "stars": snappedf(stars, 0.01), "lst": snappedf(lst, 0.1), "trans": snappedf(trans, 0.01)}
	return sky


func _sun_override() -> Vector2:
	"""tests: the sun for a fixed hour / month without moving the clock of the simulation (same formulas as main.sun_pos)"""
	var old_h: float = main.hour0
	var old_c: float = main.clock0
	var old_s: String = main.season
	main.hour0 = float(_t_override.get("hour", main.hour()))
	main.clock0 = main.now()
	if _t_override.has("month"):
		main.season = str(_t_override["month"])
	main._sun_cache = [-1.0, Vector2.ZERO]
	var sp: Vector2 = main.sun_pos()
	main.hour0 = old_h
	main.clock0 = old_c
	main.season = old_s
	main._sun_cache = [-1.0, Vector2.ZERO]
	return sp


static func _r(x: float) -> float:
	"""lux rounded to 3 significant digits (0.00123, 0.25, 412, 15300)"""
	if x <= 0.0:
		return 0.0
	var p := pow(10.0, floor(log(x) / log(10.0)) - 2.0)
	return snappedf(x, p)


static func level_of(lux: float) -> float:
	"""illuminance -> brightness of the simulated night (the pictures of the cameras come from this with their gain):
	full moon 0.25 lx = 0.065 (like before), new moon 0.001 lx ~ 0.007 - a power of 0.4 (the camera adapts a lot)"""
	return 0.065 * pow(maxf(lux, 1e-5) / 0.25, 0.4)


func night_level() -> float:
	"""main.light_level: the part of the light at night (moon, sky, town) - was 0.015 + 0.04 × moon × clear"""
	if sky.is_empty():
		compute()
	return clampf(0.85 * level_of(float(sky["night_lux"])), 0.003, 0.1)


# ---- every 0.5 s: from main._update_sky (after colors.update) ------------------------------------------------------------
func update() -> void:
	if main == null or main.env == null:
		return
	var s := compute()
	var el: float = s["sun_el"]
	var cl: float = s["clouds"]
	var day := clampf((el + 6.0) / 18.0, 0.0, 1.0)
	# sun: strong down to near the horizon (long shadows in the morning and evening); before it faded with sin(elevation)
	var low := 0.26 * smoothstep(-0.6, 2.5, el) * (1.0 - smoothstep(6.0, 15.0, el))
	var e_sun: float = maxf(sin(deg_to_rad(maxf(el, 0.0))), low) * 1.6 * (1.0 - 0.6 * cl) * main.cloud_shade() + (0.02 if el > -4.0 else 0.0)
	main.sun.light_energy = e_sun * (1.0 - main.sun_behind_hills())
	# moon: real place in the sky, shape and light from the phase
	var malt: float = s["moon_el"]
	var maz: float = s["moon_az"]
	var age: float = s["moon_age"]
	main.moon_ph = age
	if main.moon_auto:
		main.moon = snappedf(float(s["moon_illum"]), 0.01)
	main.moonlight.rotation = Vector3(deg_to_rad(-maxf(malt, 3.0)), deg_to_rad(180.0 - maz), 0)
	main.moonlight.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY      # drawn by the sky shader from moon_dir
	var a := deg_to_rad(maz)
	var al := deg_to_rad(malt)
	var mdir := Vector3(sin(a) * cos(al), sin(al), -cos(a) * cos(al))
	var smat: ShaderMaterial = main.sky_mat
	smat.set_shader_parameter("moon_dir", mdir)
	smat.set_shader_parameter("moon_phase", age)
	var sky_dark := clampf(1.0 - day * 3.0, 0.0, 1.0)
	smat.set_shader_parameter("moon_vis", (0.0 if malt < -1.0 else maxf(sky_dark, 0.18 * (1.0 - cl)) * smoothstep(-1.0, 1.0, malt)))
	smat.set_shader_parameter("star_vis", float(s["stars"]) * (1.0 - cl))
	smat.set_shader_parameter("star_lim", clampf(float(s["stars"]), 0.05, 1.0))
	var pl := _place()
	smat.set_shader_parameter("star_rot", Basis(Vector3.UP, deg_to_rad(float(s["lst"]))) * Basis(Vector3.RIGHT, deg_to_rad(90.0 - pl.x)))
	# night brightness: ambient light and moonlight from the lux (was: fixed 0.03 + 0.035 × moon)
	var L: float = s["night_lux"]
	var f := level_of(L)
	var share := clampf(float(s["lux_moon"]) / maxf(L, 1e-6), 0.0, 1.0)
	var amb_night := clampf(f * (1.0 - 0.6 * share), 0.002, 0.15)
	var tw := minf(level_of(tw_lux(el) * float(s["trans"])), 0.15) if el < 0.0 else 0.0      # twilight sky: slowly darker
	amb_night = maxf(amb_night, tw)
	var cur: float = main.env.ambient_light_energy - main._flash_boost      # main.gd + colors.gd (blue hour)
	var amb := maxf(cur - 0.03 + amb_night, amb_night)
	main._amb_base = amb
	main.env.ambient_light_energy = amb + main._flash_boost
	main.moonlight.light_energy = (f * share * 0.6 / maxf(sin(deg_to_rad(maxf(malt, 0.0))), 0.25)) * (1.0 - day) if malt > -1.0 else 0.0
	# twilight: the sky stays the brightest thing for a while after sunset - deep blue above, orange-red at the horizon
	# (before: it got dark with the ground and looked black in the night picture of the cameras)
	var twk := smoothstep(-11.0, -0.5, el) * (1.0 - smoothstep(0.0, 6.0, el))
	if twk > 0.0:
		var hor0: Color = smat.get_shader_parameter("horizon_color")
		var top0: Color = smat.get_shader_parameter("top_color")
		var clear := 1.0 - 0.8 * cl
		smat.set_shader_parameter("top_color", top0.lerp(Color(0.09, 0.15, 0.32), twk * 0.8))
		smat.set_shader_parameter("horizon_color", hor0.lerp(Color(0.62, 0.42, 0.36).lerp(Color(0.85, 0.45, 0.22), smoothstep(-4.0, 1.0, el)) * clear + Color(0.35, 0.36, 0.38) * (1.0 - clear), twk * 0.85))
		main._sky_e_base = maxf(main._sky_e_base, 0.06 + 0.55 * twk * twk)
		smat.set_shader_parameter("energy", main._sky_e_base + main._flash_boost * 0.6)
	# light pollution: the orange glow over the place (main.gd does it only without licht.gd)
	var glow: float = LP_GLOW[s["lp"]]
	if glow > 0.0:
		var k := maxf(0.02, day)
		var hor: Color = smat.get_shader_parameter("horizon_color")
		var top: Color = smat.get_shader_parameter("top_color")
		smat.set_shader_parameter("horizon_color", hor + Color(0.07, 0.045, 0.025) * (1.0 - k) * (0.6 + 0.8 * cl) * glow)
		smat.set_shader_parameter("top_color", top + Color(0.012, 0.009, 0.006) * (1.0 - k) * (0.5 + cl) * glow)
	_lamps()
	_glare_tick()


# ---- lamps, tents, windows ------------------------------------------------------------------------------------------
func on_scene() -> void:
	"""after a scene was built: find its lamps, tents and windows"""
	_platz.clear()
	_tents.clear()
	_wins.clear()
	_shadow_lamp = null
	_extra = _extra.filter(func(x): return is_instance_valid(x["node"]))
	if main.scene_parent == null:
		return
	var meshes: Array = []
	var todo: Array = [main.scene_parent]
	while not todo.is_empty():
		var n = todo.pop_back()
		todo.append_array(n.get_children())
		if n is MeshInstance3D and n.layers == 1:
			meshes.append(n)
	var tent_nodes := {}
	for mi in meshes:
		var mt = mi.material_override
		if mi.mesh is PrismMesh and (mi.mesh as PrismMesh).size.x > 2.4 and (mi.mesh as PrismMesh).size.x < 3.0 \
				and (mi.mesh as PrismMesh).size.y > 1.4 and (mi.mesh as PrismMesh).size.y < 1.7:
			var tn = mi.get_parent()
			if not tent_nodes.has(tn):
				tent_nodes[tn] = []
			tent_nodes[tn].append(mi)
		elif mt is StandardMaterial3D and mt.emission_enabled and (mt as StandardMaterial3D).emission.is_equal_approx(Color(1.0, 0.8, 0.5)):
			if not _wins.any(func(w): return w["mat"] == mt):
				var p: Vector3 = mi.global_position
				_wins.append({"mat": mt, "pos": p, "bed": 22.5 + 1.8 * _hash(p), "early": _hash(p + Vector3(3, 0, 1)) < 0.4})
	for tn in tent_nodes:
		var p: Vector3 = (tn as Node3D).global_position
		var it := {"meshes": tent_nodes[tn], "mats": [], "light": null, "pos": p, "bed": 21.8 + 1.9 * _hash(p),
				"early": _hash(p + Vector3(7, 0, 2)) < 0.35}
		for mi in tent_nodes[tn]:
			var base = mi.material_override
			if base is StandardMaterial3D:
				var m2: StandardMaterial3D = base.duplicate()    # the colour material is shared - each tent its own glow
				m2.emission_enabled = true
				m2.emission = (base as StandardMaterial3D).albedo_color.lerp(Color(1.0, 0.75, 0.4), 0.6)
				m2.emission_energy_multiplier = 0.0
				mi.material_override = m2
				it["mats"].append(m2)
		if not Quality.lite() and main.quality != "simple":
			var ol := OmniLight3D.new()
			ol.position = Vector3(0, 0.7, 1.6)                   # in front of the door: light on the grass
			ol.light_color = Color(1.0, 0.72, 0.4)
			ol.omni_range = 4.0
			ol.light_energy = 0.0
			ol.shadow_enabled = false
			(tn as Node3D).add_child(ol)
			it["light"] = ol
		_tents.append(it)
	_scan_lamps()


func _scan_lamps() -> void:
	"""the lamps of the scene and of the catalogue (main.lamps): street / place lamps get the dusk switch"""
	var known := {}
	for p in _platz:
		known[p["l"]] = true
	for l in main.lamps:
		if not is_instance_valid(l) or known.has(l) or not (l is OmniLight3D):
			continue
		if absf(l.omni_range - 12.0) > 0.5 or not l.light_color.is_equal_approx(Color(1.0, 0.82, 0.55)):
			continue
		var p: Vector3 = l.global_position
		var glows := []
		var par = l.get_parent()
		for c in par.get_children():
			if c is MeshInstance3D and c.material_override in main.lamp_mats and c.global_position.distance_to(p) < 1.2:
				glows.append(c)
				c.visibility_range_end = 5000.0          # Lite: the lamp head stays visible far away (a bright point)
		if glows.is_empty() and par is Node3D:        # catalogue lamp: the glow is deeper in the thing
			var todo: Array = [par]
			while not todo.is_empty():
				var n = todo.pop_back()
				todo.append_array(n.get_children())
				if n is MeshInstance3D and n.material_override in main.lamp_mats:
					glows.append(n)
		_platz.append({"l": l, "glow": glows, "timer": _hash(p) < 0.35})


func _hash(p: Vector3) -> float:
	return fposmod(sin(p.x * 12.9898 + p.z * 78.233 + p.y * 37.719) * 43758.5453, 1.0)


func _testing() -> bool:
	return main.testrun != null and main.testrun.running


func _evening(h: float, bed: float, el: float) -> bool:
	"""people are awake with the light on: from dusk until bed time, and early in the morning while it is still dark"""
	if el > -1.0:
		return false
	var b := bed if bed < 24.0 else bed - 24.0
	if bed < 24.0:
		if h >= 15.0 and h < bed:
			return true
	elif h >= 15.0 or h < b:
		return true
	return h >= 5.6 and h < 7.5


func _lamps() -> void:
	if main.lamps.size() != _platz.size():
		_scan_lamps()
	var h: float = main.hour()
	var el: float = sky["sun_el"]
	var dark: bool = main.is_dark()
	var power: bool = not main.power_off
	var test := _testing()
	var lite := Quality.lite()
	var hp: Vector3 = main.head.global_position if main.head != null else Vector3.ZERO
	# place lamps: dusk switch, some with a timer (off 0:30-5:00)
	var on_list := []
	for p in _platz:
		var l: OmniLight3D = p["l"]
		if not is_instance_valid(l):
			continue
		var on: bool
		if test:
			on = dark and power                         # like before (comparable runs)
		elif platz_mode == "on":
			on = power
		elif platz_mode == "off":
			on = false
		else:
			on = power and el < -2.5 and not (p["timer"] and h >= 0.5 and h < 5.0)
		l.light_energy = 2.2 if on else 0.0
		l.visible = true
		for g in p["glow"]:
			if is_instance_valid(g) and g.material_override is StandardMaterial3D:
				g.material_override.emission_energy_multiplier = 3.0 if on else 0.0
		if on:
			on_list.append([l.global_position.distance_to(hp), l])
	on_list.sort_custom(func(x, y): return x[0] < y[0])
	for i in range(on_list.size()):
		var l: OmniLight3D = on_list[i][1]
		if lite and i >= PLATZ_LITE:
			l.visible = false                          # Lite: far lamps only glow (light_at still counts them)
	# shadows only where cheap: the nearest burning place lamp (Normal / Hoch), never in Lite or «einfach»
	var want: OmniLight3D = null
	if not lite and main.quality != "simple" and not on_list.is_empty() and float(on_list[0][0]) < 30.0:
		want = on_list[0][1]
	if _shadow_lamp != want:
		if is_instance_valid(_shadow_lamp):
			_shadow_lamp.shadow_enabled = false
		if want != null:
			want.shadow_enabled = true
			want.shadow_bias = 0.08
		_shadow_lamp = want
	# tents and windows
	for t in _tents:
		var on: bool = power and home_lights and not test and _evening(h, t["bed"], el) and (h < 7.5 and t["early"] or h >= 7.5)
		for m2 in t["mats"]:
			m2.emission_energy_multiplier = 0.35 if on else 0.0
		if t["light"] != null and is_instance_valid(t["light"]):
			t["light"].light_energy = 0.7 if on else 0.0
	for w in _wins:
		if home_lights and not test:
			var on2: bool = power and _evening(h, w["bed"], el) and (h < 7.5 and w["early"] or h >= 7.5)
			w["mat"].emission_energy_multiplier = 2.5 if on2 else 0.0
		elif w["mat"] != main.window_mat:
			w["mat"].emission_energy_multiplier = 0.0       # like before: only the window of the door sensor (main.gd)
	# attached lamps / headlights
	for x in _extra:
		if not is_instance_valid(x["node"]):
			continue
		var on3: bool = dark if x["force"] == null else bool(x["force"])
		for sl in x["lights"]:
			if is_instance_valid(sl):
				sl.light_energy = float(x["energy"]) if on3 else 0.0
		for m3 in x["mats"]:
			m3.emission_energy_multiplier = float(x["glow"]) if on3 else 0.0


# ---- low sun in a camera: haze and lens flare ---------------------------------------------------------------------------
func _glare_tick() -> void:
	"""the sun in (or just beside) the picture of a camera: lens.gdshader «glare» at its real place - only when the
	condition «Gegenlicht» (fixed place, by hand) is off"""
	if main.cond.get("glare", false):
		return
	var el: float = sky["sun_el"]
	var cl: float = sky["clouds"]
	for i in range(mini(2, main.lens_mats.size())):
		var g := 0.0
		var uvp := Vector2(0.5, 0.2)
		if el > -0.8 and el < 25.0 and i < main.cams.size():
			var cam: Camera3D = main.cams[i]
			var a := deg_to_rad(float(sky["sun_az"]))
			var e := deg_to_rad(el)
			var to_sun := Vector3(sin(a) * cos(e), sin(e), -cos(a) * cos(e))
			var p: Vector3 = cam.global_position + to_sun * 500.0
			if not cam.is_position_behind(p):
				var vs: Vector2 = Vector2(main.vps[i].size)
				var sp: Vector2 = cam.unproject_position(p) / vs
				var off := maxf(maxf(-sp.x, sp.x - 1.0), maxf(-sp.y, sp.y - 1.0))      # > 0: outside the picture
				var inside := 1.0 - smoothstep(0.0, 0.35, off)
				var low := smoothstep(25.0, 6.0, el) * smoothstep(-0.8, 0.5, el)
				g = inside * low * clampf(1.0 - 1.15 * cl, 0.0, 1.0) * float(main.cloud_shade()) * (1.0 - float(main.sun_behind_hills()))
				g *= 0.85 if i == 0 else 0.6
				uvp = sp.clamp(Vector2(-0.2, -0.2), Vector2(1.2, 1.2))
		_glare[i] = snappedf(g, 0.01)
		if g > 0.01:                                       # (_update_lens sets 0 every 0.5 s before)
			main.lens_mats[i].set_shader_parameter("glare", g)
			main.lens_mats[i].set_shader_parameter("glare_pos", uvp)


# ---- hooks for other parts --------------------------------------------------------------------------------------------
func attach_lamp(fig: Node3D, kind := "head", force = null) -> SpotLight3D:
	"""a headlamp («head») or a torch / phone light in the hand («hand») for a figure (actor.gd: on its head / right hand;
	any other Node3D: at 1.6 m / 1.1 m). On at night (or force = true / false). Returns the light."""
	if fig == null:
		return null
	if "lamp" in fig and fig.lamp != null and is_instance_valid(fig.lamp):
		return fig.lamp                                     # actor.gd has one already (lamp_share)
	var sl := SpotLight3D.new()
	sl.spot_range = 10.0 if kind == "head" else 14.0
	sl.spot_angle = 22.0 if kind == "head" else 16.0
	sl.light_color = Color(1.0, 0.97, 0.92) if kind == "head" else Color(1.0, 0.95, 0.85)
	sl.shadow_enabled = false
	var bulb := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.03
	sm.height = 0.06
	bulb.mesh = sm
	var mt := StandardMaterial3D.new()
	mt.albedo_color = Color(1.0, 0.98, 0.9)
	mt.emission_enabled = true
	mt.emission = Color(1.0, 0.98, 0.9)
	mt.emission_energy_multiplier = 0.0
	bulb.material_override = mt
	var par: Node3D = fig
	var pos := Vector3(0, 1.6 if kind == "head" else 1.1, -0.2)
	var rot := Vector3(-0.35 if kind == "head" else -0.6, 0, 0)
	if kind == "head" and "head" in fig and fig.head is Node3D:
		par = fig.head
		pos = Vector3(0, 0.24, -0.16)
	elif kind != "head" and "arms" in fig and fig.arms is Array and fig.arms.size() > 1 and fig.arms[1].size() > 2:
		par = fig.arms[1][2]
		pos = Vector3(0, -0.36, -0.05)
		rot = Vector3(-1.2, 0, 0)
	par.add_child(sl)
	sl.position = pos
	sl.rotation = rot
	par.add_child(bulb)
	bulb.position = pos + Vector3(0, 0, 0.02)
	if "lamp" in fig and force == null:                     # actor.gd switches it with set_night like its own lamps
		fig.lamp = sl
		fig.lamp_mat = mt
		fig.set_night(main.is_dark())
	_extra.append({"node": fig, "lights": [sl], "mats": [mt], "kind": "stirnlampe" if kind == "head" else "taschenlampe",
			"force": force, "energy": 6.0, "glow": 16.0})
	return sl


func detach_lamp(fig: Node3D) -> void:
	for x in _extra.duplicate():
		if x["node"] == fig and str(x["kind"]) in ["stirnlampe", "taschenlampe"]:
			for sl in x["lights"]:
				if is_instance_valid(sl):
					sl.queue_free()
			_extra.erase(x)
	if "lamp" in fig and fig.lamp != null and is_instance_valid(fig.lamp):
		fig.lamp.light_energy = 0.0
		fig.lamp_mat.emission_energy_multiplier = 0.0
		fig.lamp = null


func add_headlights(car: Node3D, front_z := -2.12, half_w := 0.6, y := 0.7, force = null) -> Array:
	"""two headlights (spot 45 m + glowing glass) at the front (−Z) of a car / vehicle; on at night or force"""
	var lights := []
	var mats := []
	for sx in [-1.0, 1.0]:
		var hl := SpotLight3D.new()
		hl.position = Vector3(sx * half_w, y, front_z)
		hl.spot_range = 45.0
		hl.spot_angle = 24.0
		hl.light_color = Color(1.0, 0.95, 0.85)
		hl.light_energy = 0.0
		hl.shadow_enabled = false
		car.add_child(hl)
		lights.append(hl)
		var g := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.28, 0.12, 0.04)
		g.mesh = bm
		var mt := StandardMaterial3D.new()
		mt.albedo_color = Color(1, 1, 0.9)
		mt.emission_enabled = true
		mt.emission = Color(1, 0.97, 0.85)
		mt.emission_energy_multiplier = 0.0
		g.material_override = mt
		g.position = Vector3(sx * half_w, y, front_z + 0.02)
		car.add_child(g)
		mats.append(mt)
	_extra.append({"node": car, "lights": lights, "mats": mats, "kind": "scheinwerfer", "force": force, "energy": 6.0, "glow": 4.0})
	_lamps_extra_now()
	return lights


func set_headlights(car: Node3D, on) -> void:
	"""on = true / false (fixed) or null (automatic: at night)"""
	for x in _extra:
		if x["node"] == car and x["kind"] == "scheinwerfer":
			x["force"] = on
	_lamps_extra_now()


func _lamps_extra_now() -> void:
	var dark: bool = main.is_dark()
	for x in _extra:
		if not is_instance_valid(x["node"]):
			continue
		var on: bool = dark if x["force"] == null else bool(x["force"])
		for sl in x["lights"]:
			if is_instance_valid(sl):
				sl.light_energy = float(x["energy"]) if on else 0.0
		for m3 in x["mats"]:
			m3.emission_energy_multiplier = float(x["glow"]) if on else 0.0


# ---- API: lights for the camera package (glare), lux --------------------------------------------------------------------
func _src(kind: String, n: Node3D, energy: float, col: Color, rng: float, cone := 0.0) -> Dictionary:
	var on := energy > 0.05 and n.is_visible_in_tree()
	var cd: float = float(CD.get(kind, 300.0)) * (clampf(energy / {"platz": 2.2, "zelt": 0.7}.get(kind, 6.0), 0.0, 3.0) if on else 0.0)
	var d := {"kind": kind, "pos": _v(n.global_position), "on": on, "cd": snappedf(cd, 0.1), "color": [snappedf(col.r, 0.01), snappedf(col.g, 0.01), snappedf(col.b, 0.01)],
			"range": snappedf(rng, 0.1)}
	if cone > 0.0:
		d["dir"] = _v(-n.global_transform.basis.z)
		d["cone"] = snappedf(cone, 0.1)
	return d


static func _v(p: Vector3) -> Array:
	return [snappedf(p.x, 0.01), snappedf(p.y, 0.01), snappedf(p.z, 0.01)]


func sources(cam := -1) -> Array:
	"""every light of the world now: {kind, pos [x,y,z], on, cd (estimated candela), color, range, dir + cone (spots)};
	with cam 0/1: also px [x, y] (picture pixels of that camera, if in front), in_view, dist (m), cd_to_cam (what the
	lens sees: a spot pointing away counts 5 %), lux_at_cam (cd_to_cam / dist²)"""
	var out := []
	var plat := {}
	for p in _platz:
		if is_instance_valid(p["l"]):
			plat[p["l"]] = true
			out.append(_src("platz", p["l"], p["l"].light_energy, p["l"].light_color, p["l"].omni_range))
	for l in main.lamps:
		if is_instance_valid(l) and l is Light3D and not plat.has(l):
			var k := "feuer" if l.light_color.g < 0.6 else "lampe"
			out.append(_src(k, l, l.light_energy, l.light_color, l.omni_range if l is OmniLight3D else 10.0))
	for t in _tents:
		if t["light"] != null and is_instance_valid(t["light"]):
			out.append(_src("zelt", t["light"], t["light"].light_energy, t["light"].light_color, 4.0))
		elif not t["mats"].is_empty() and not t["meshes"].is_empty() and is_instance_valid(t["meshes"][0]):
			out.append(_src("zelt", t["meshes"][0], 0.7 if t["mats"][0].emission_energy_multiplier > 0.0 else 0.0, Color(1.0, 0.72, 0.4), 0.0))
	if main.visitors != null:
		for v in main.visitors.get_children():
			if "lamp" in v and v.lamp != null and is_instance_valid(v.lamp) and not _extra.any(func(x): return x["lights"].has(v.lamp)):
				out.append(_src("stirnlampe" if v.lamp.get_parent() == v.get("head") else "taschenlampe", v.lamp, v.lamp.light_energy, v.lamp.light_color, v.lamp.spot_range, v.lamp.spot_angle))
			if "lights" in v:
				for l in v.lights:
					if l is SpotLight3D and is_instance_valid(l):
						out.append(_src("scheinwerfer", l, l.light_energy, l.light_color, l.spot_range, l.spot_angle))
			if "bike_lamp" in v and not v.bike_lamp.is_empty() and is_instance_valid(v.bike_lamp[0]):
				out.append(_src("velo", v.bike_lamp[0], v.bike_lamp[0].light_energy, v.bike_lamp[0].light_color, v.bike_lamp[0].spot_range, v.bike_lamp[0].spot_angle))
	for x in _extra:
		if is_instance_valid(x["node"]):
			for sl in x["lights"]:
				if is_instance_valid(sl):
					out.append(_src(x["kind"], sl, sl.light_energy, sl.light_color, sl.spot_range, sl.spot_angle))
	if main.white_light != null:
		out.append(_src("weisslicht", main.white_light, main.white_light.light_energy, main.white_light.light_color, main.white_light.spot_range, main.white_light.spot_angle))
	if cam >= 0 and cam < mini(2, main.cams.size()):
		var c: Camera3D = main.cams[cam]
		var vs: Vector2 = Vector2(main.vps[cam].size)
		var cp: Vector3 = c.global_position
		for s in out:
			var p := Vector3(s["pos"][0], s["pos"][1], s["pos"][2])
			var dist := maxf(0.3, cp.distance_to(p))
			s["dist"] = snappedf(dist, 0.1)
			var front := not c.is_position_behind(p)
			var px: Vector2 = c.unproject_position(p) if front else Vector2(-1, -1)
			s["in_view"] = front and px.x >= 0.0 and px.y >= 0.0 and px.x < vs.x and px.y < vs.y
			s["px"] = [roundi(px.x), roundi(px.y)] if front else null
			var k := 1.0
			if s.has("dir"):
				var dv := Vector3(s["dir"][0], s["dir"][1], s["dir"][2])
				var cosang := dv.dot((cp - p).normalized())
				k = 1.0 if cosang > cos(deg_to_rad(float(s["cone"]))) else 0.05
			s["cd_to_cam"] = snappedf(float(s["cd"]) * k, 0.1)
			s["lux_at_cam"] = _r(float(s["cd"]) * k / (dist * dist))
	return out


func lux_at(p: Vector3) -> float:
	"""illuminance at a place (lx): sky (sun, twilight, moon, town) + the lamps (cd / d², spots only inside their cone)"""
	if sky.is_empty():
		compute()
	var e: float = float(sky["lux"])
	for s in sources():
		if not s["on"]:
			continue
		var q := Vector3(s["pos"][0], s["pos"][1], s["pos"][2])
		var d := maxf(0.5, q.distance_to(p))
		if float(s["range"]) > 0.0 and d > float(s["range"]) * 1.5:
			continue
		var k := 1.0
		if s.has("dir"):
			var dv := Vector3(s["dir"][0], s["dir"][1], s["dir"][2])
			k = 1.0 if dv.dot((p - q).normalized()) > cos(deg_to_rad(float(s["cone"]))) else 0.02
		e += float(s["cd"]) * k / (d * d)
	return _r(e)


# ---- MoveEye, tests ---------------------------------------------------------------------------------------------------
func reply() -> Dictionary:
	"""world_reply «sky»: the sky in a few numbers (lux at the device, twilight phase, sun, moon) - MoveEye does not read it yet"""
	if sky.is_empty():
		compute()
	var lx: float = lux_at(main.head.global_position + Vector3(0, -1.0, 0)) if main.head != null else float(sky["lux"])
	return {"lux": lx, "sky_lux": sky["lux"], "phase": sky["phase"], "sun_el": snappedf(float(sky["sun_el"]), 0.1),
			"moon_el": snappedf(float(sky["moon_el"]), 0.1), "moon_illum": snappedf(float(sky["moon_illum"]), 0.01), "lp": sky["lp"]}


func summary() -> String:
	if sky.is_empty():
		compute()
	var s := sky
	var moon_txt := T.t("Mond unter dem Horizont") if float(s["moon_el"]) < 0.0 else T.t("Mond %d° hoch, %d %% beleuchtet", [roundi(float(s["moon_el"])), roundi(float(s["moon_illum"]) * 100.0)])
	return T.t("Himmel: %s · Sonne %.1f° · %s · %s lx · Lichtverschmutzung %s", [T.t(PHASE_DE[s["phase"]]), float(s["sun_el"]), moon_txt,
			_lux_txt(float(s["lux"])), T.t({"land": "Land", "dorf": "Dorf", "stadt": "Stadt"}[s["lp"]])])


static func _lux_txt(x: float) -> String:
	if x >= 100.0:
		return "%d" % roundi(x)
	if x >= 1.0:
		return "%.1f" % x
	if x >= 0.01:
		return "%.3f" % x
	return "%.4f" % x


func info() -> Dictionary:
	var d := {"sky": compute().duplicate(), "lp_mode": lp_mode, "platz_mode": platz_mode, "home_lights": home_lights,
			"platz": _platz.size(), "platz_on": _platz.filter(func(p): return is_instance_valid(p["l"]) and p["l"].light_energy > 0.0).size(),
			"platz_visible": _platz.filter(func(p): return is_instance_valid(p["l"]) and p["l"].light_energy > 0.0 and p["l"].visible).size(),
			"tents": _tents.size(), "tents_on": _tents.filter(func(t): return not t["mats"].is_empty() and t["mats"][0].emission_energy_multiplier > 0.0).size(),
			"windows": _wins.size(), "windows_on": _wins.filter(func(w): return w["mat"].emission_energy_multiplier > 0.0).size(),
			"extra": _extra.size(), "shadow_lamp": is_instance_valid(_shadow_lamp), "glare": _glare, "lite": Quality.lite(),
			"night_level": snappedf(night_level(), 0.0001), "ambient": snappedf(main.env.ambient_light_energy, 0.0001),
			"moonlight": snappedf(main.moonlight.light_energy, 0.0001), "sun_energy": snappedf(main.sun.light_energy, 0.001),
			"summary": summary()}
	return d


func control(d: Dictionary) -> Dictionary:
	"""{do: info | set (key, value) | sources (cam) | lux (x, y, z) | attach (i = visitor number, kind) | headlights (i, on) |
	at (hour, month: only the numbers of the sky for that time, the clock keeps running) | at_clear}"""
	var op := str(d.get("do", "info"))
	match op:
		"set":
			var k := str(d.get("key", ""))
			if k in SAVE:
				set(k, bool(d.get("value", true)) if k == "home_lights" else str(d.get("value", "")))
				save()
				main._update_sky()
		"sources":
			return {"ok": true, "sources": sources(int(d.get("cam", -1)))}
		"lux":
			return {"ok": true, "lux": lux_at(Vector3(float(d.get("x", 0)), float(d.get("y", 0)), float(d.get("z", 0))))}
		"attach", "headlights":
			var vs: Array = main.visitors.get_children()
			var i := int(d.get("i", 0))
			if i < 0 or i >= vs.size():
				return {"ok": false, "error": "no visitor %d" % i}
			if op == "attach":
				attach_lamp(vs[i], str(d.get("kind", "head")), d.get("force", null))
			else:
				if not _extra.any(func(x): return x["node"] == vs[i] and x["kind"] == "scheinwerfer"):
					add_headlights(vs[i], -2.12, 0.6, 0.7, d.get("on", null))
				else:
					set_headlights(vs[i], d.get("on", null))
		"at":
			_t_override = {"hour": float(d.get("hour", main.hour()))}
			if d.has("month"):
				var mo := clampi(int(d["month"]), 1, 12)
				_t_override["month"] = mo
				_t_override["doy"] = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349][mo - 1]
			var r := compute().duplicate()
			_t_override = {}
			compute()
			return {"ok": true, "sky": r}
	return {"ok": true, "info": info()}
