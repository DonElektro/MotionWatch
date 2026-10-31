extends Node
## «Jahreszeiten & Tageslauf» (Zweig real-jahreszeiten, 31.10.2026): das Jahr wie echt - Pflanzen, Tageslänge, Belegung.
##  Jahreszeit
##   - gemeinsam für alle Szenen: «automatisch» nach dem Datum (Jahreszeit (Sonnenbahn) = Monat oder heute) oder fest
##     Frühling / Sommer / Herbst / Winter. Eine feste Jahreszeit stellt die Sonnenbahn auf ihren Monat (April, Juli,
##     Oktober, Januar) - so passen Tageslänge, Sonnenaufgang und -untergang, Mond (licht.gd) und Farben (colors.gd) dazu.
##   - Haken für andere Teile: main.jahreszeit() -> "fruehling" | "sommer" | "herbst" | "winter" (meteorologisch: März-Mai,
##     Juni-Aug., Sept.-Nov., Dez.-Feb.); main.jahreszeiten.state() - alle Zahlen. Bergtal (bergtal.gd season_of) liest
##     bisher bt_season und main.season - weil eine feste Jahreszeit hier main.season setzt, folgt Bergtal «auto» schon
##     ohne Änderung (Bergtal zählt März noch zum Winter: Berg). Vorschlag für den Koordinator in REAL_JAHRESZEITEN.md.
##  Pflanzen (nur Laubbäume, Nadelbäume bleiben grün; foliage.gdshader «bare» / «blossom»)
##   - Laubaustrieb Mitte April - Anfang Mai, Laubfall Ende Oktober - Mitte November (Buche / Eiche im Mittelland,
##     Phänologie MeteoSchweiz: Blattentfaltung Buche ~20. April, Blattverfärbung ~Mitte Oktober, kahl ~Mitte November).
##     Kahle Bäume im Winter: nur noch Äste (die Krone ist durchsichtig), sie wiegen kaum im Wind - weniger Bewegung
##     im Bild (MoveEye: weniger Fehlalarme durch Laub im Wind, aber auch weniger Deckung).
##   - Blüten: Kirsch- / Apfelblüte Anfang - Ende April (MeteoSchweiz Kirschblüte Liestal im Mittel ~10. April), ein
##     Drittel der Laubbäume blüht weiss-rosa.
##   - Herbst: fallende Blätter (Partikel um die Kamera, mehr bei Wind - bewegte Dinge im Bild wie echt), Bodennebel an
##     ruhigen Herbstmorgen (Mitte Sept. - Nov.: von 2 h vor bis 2,5 h nach Sonnenaufgang, über colors.gd ground_fog).
##   - Winter: Schnee liegt (auch ohne Schneefall), wenn es kalt ist (Aussentemperatur <= 1 °C) - «Schnee im Winter»
##     automatisch / immer / nie.
##  Tageslauf: Sonnenaufgang, -untergang, bürgerliche Dämmerung, Tageslänge für Datum und Ort (Sonne aus licht.gd ephem /
##   ecl_to_altaz, Horizont -0,833° wie üblich: Refraktion + Sonnenradius). Bern 21. Juni ~15 h 59 min, 21. Dez. ~8 h 25 min.
##  Belegung (Campingplätze: camping, camping_voll, ferienpark, stellplatz, seeufer): «Wie oft Besuch kommt» bekommt den
##   Faktor der Saison - Menschen kommen in der Hochsaison (Juli / August, Schulferien) öfter, in der Nebensaison selten,
##   im Winter fast nie; Tiere kommen gleich oft. Während Testlauf / Prüfstand / Nacht-Testlauf: wie bisher.
##  Lite: keine fallenden Blätter (Partikel), sonst gleich (die Shader-Werte kosten nichts).
## Einstellungen in user://jahreszeiten.json. Test: /control {"action": "jahreszeiten", "do": info | set (key, value) |
## sun (doy, lat, lon) | year}.

const T = preload("res://scripts/i18n.gd")
const Quality = preload("res://scripts/quality.gd")
const Licht = preload("res://scripts/licht.gd")
const Worlds = preload("res://scripts/worlds.gd")
const FILE := "user://jahreszeiten.json"
const SAVE := ["mode", "snow_mode", "occupancy_on", "fog_on", "leaves_on"]

var main
var mode := "auto"               # auto | fruehling | sommer | herbst | winter
var snow_mode := "auto"          # auto (kalt) | on | off
var occupancy_on := true         # Campingplatz nach Saison belegt
var fog_on := true               # Herbst: Nebel am Morgen
var leaves_on := true            # Herbst: fallende Blätter

const KEYS := ["fruehling", "sommer", "herbst", "winter"]
const REP_MONTH := {"fruehling": "4", "sommer": "7", "herbst": "10", "winter": "1"}
const NAME_DE := {"fruehling": "Frühling", "sommer": "Sommer", "herbst": "Herbst", "winter": "Winter"}
const MODE_OPTS := [["auto", "automatisch (nach Datum / Monat)"], ["fruehling", "Frühling (frisches Grün, Blüten)"],
		["sommer", "Sommer (lange Tage, Hochsaison)"], ["herbst", "Herbst (bunte Blätter, Nebel am Morgen)"],
		["winter", "Winter (kahle Bäume, kurze Tage)"]]
const SNOW_OPTS := [["auto", "automatisch (wenn kalt, bis 1 °C)"], ["on", "immer im Winter"], ["off", "nie"]]
const CAMP_SCENES := ["camping", "camping_voll", "ferienpark", "stellplatz", "seeufer"]
# Belegung eines Campingplatzes im Mittelland / an einem See pro Monat (1 = voll). Grob nach den Logiernächten der
# Campingplätze (BFS Parahotellerie: Juli / August ~45 % der Jahresnächte, November - März zusammen < 5 %).
const OCC := [0.08, 0.08, 0.12, 0.35, 0.5, 0.7, 1.0, 1.0, 0.55, 0.3, 0.08, 0.12]
const OCC_REF := 0.7              # so belegt waren die Szenen bisher (Juni) - Faktor 1
const SNOW_C := 1.0               # bis zu dieser Aussentemperatur bleibt Schnee liegen (auto)

var _leaves: CPUParticles3D = null
var _leaf_level := -1
var _sun_cache := {}              # "doy|lat|lon" -> sun_times()
var _now := {}                    # state() zuletzt


static func _lite() -> bool:
	return Quality.lite()


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		for k in SAVE:
			if d.has(k):
				set(k, bool(d[k]) if typeof(get(k)) == TYPE_BOOL else str(d[k]))
	if mode != "auto" and main != null:
		main.season = REP_MONTH.get(mode, main.season)


func save() -> void:
	var d := {}
	for k in SAVE:
		d[k] = get(k)
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


func add_controls() -> void:
	var m = main
	m.add_control("select", "jz_mode", "Jahreszeit (Pflanzen, Tageslänge, Belegung)", func(): return cur_mode(),
			func(v): set_mode(str(v)), "Szene", {"sub": "Zeit", "options": MODE_OPTS})
	m.add_control("select", "jz_snow", "Schnee liegt im Winter", func(): return snow_mode,
			func(v): snow_mode = str(v); save(); main._update_sky(), "Szene", {"sub": "Zeit", "options": SNOW_OPTS, "expert": true})
	m.add_control("toggle", "jz_fog", "Herbst: Nebel am Morgen (ruhige Tage)", func(): return fog_on,
			func(v): fog_on = bool(v); save(), "Szene", {"sub": "Zeit", "expert": true})
	m.add_control("toggle", "jz_leaves", "Herbst: fallende Blätter (mehr bei Wind)", func(): return leaves_on,
			func(v): leaves_on = bool(v); save(); _leaf_level = -1; update(), "Szene", {"sub": "Zeit", "expert": true})
	m.add_control("button", "jz_info", "Tageslauf heute (Sonnenaufgang, -untergang, Tageslänge)", null,
			func(): main.start_info = summary(), "Szene", {"sub": "Zeit"})
	m.add_control("toggle", "jz_occ", "Campingplatz nach Saison belegt (Hochsaison voll, Nebensaison leer)", func(): return occupancy_on,
			func(v): occupancy_on = bool(v); save(), "Besuch", {"sub": "Von selbst"})


func cur_mode() -> String:
	"""the chosen season - «auto» again as soon as somebody sets another month under «Jahreszeit (Sonnenbahn)»"""
	if mode in REP_MONTH and str(main.season) == REP_MONTH[mode]:
		return mode
	return "auto"


func set_mode(v: String) -> void:
	mode = v if v in REP_MONTH else "auto"
	if mode != "auto":
		main.season = REP_MONTH[mode]                   # the sun path (day length), the moon and the colours fit it
	else:
		main.season = "today"
	main._sun_cache = [-1.0, Vector2.ZERO]
	main._settings_dirty = true
	save()
	main._update_sky()


# ---- the year ---------------------------------------------------------------------------------------------------------
func doy() -> int:
	return int(main.day_of_year())


static func season_of_doy(d: int) -> String:
	"""meteorological seasons: spring Mar-May, summer Jun-Aug, autumn Sep-Nov, winter Dec-Feb"""
	if d >= 60 and d < 152:
		return "fruehling"
	if d >= 152 and d < 244:
		return "sommer"
	if d >= 244 and d < 335:
		return "herbst"
	return "winter"


func season() -> String:
	return season_of_doy(doy())


static func bare_k(d: float) -> float:
	"""how bare the broad-leaved trees are (1 = only branches): leaf-out 5 Apr - 10 May, leaf fall 17 Oct - 21 Nov"""
	return maxf(1.0 - smoothstep(95.0, 130.0, d), smoothstep(290.0, 325.0, d))


static func blossom_k(d: float) -> float:
	"""cherry / apple blossom: early to late April (peak ~18 April)"""
	return clampf(1.0 - absf(d - 108.0) / 18.0, 0.0, 1.0)


static func fall_k(d: float) -> float:
	"""falling leaves: most at the end of October"""
	return clampf(1.0 - absf(d - 300.0) / 30.0, 0.0, 1.0)


static func fog_k(d: float) -> float:
	"""season of the morning fog in the Mittelland: mid September to the end of November"""
	return smoothstep(255.0, 280.0, d) * (1.0 - smoothstep(330.0, 350.0, d))


func occupancy() -> float:
	return float(OCC[_month_of(doy()) - 1])


static func _month_of(d: int) -> int:
	var cum := [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 366]
	for i in range(12):
		if d <= cum[i + 1]:
			return i + 1
	return 12


func _testing() -> bool:
	return main.busy_with() in ["Testlauf", "Prüfstand", "Nacht-Testlauf"]


func visit_factor() -> float:
	"""people on a campsite: × this (1 = like before); 0 .. 1.43"""
	if not occupancy_on or not (main.scene in CAMP_SCENES) or _testing():
		return 1.0
	return occupancy() / OCC_REF


func accept_visit(kind: String, people: Array) -> bool:
	"""main._life: the interval was already shortened by max(1, f) - people come with f / max(1, f), animals 1 / max(1, f)"""
	var f := visit_factor()
	var hi := maxf(1.0, f)
	if kind in people:
		return randf() < f / hi
	return randf() < 1.0 / hi


# ---- day length -------------------------------------------------------------------------------------------------------
func _place() -> Vector2:
	return Vector2(main.ort_lat if main.ort_lat != 0.0 else 46.8, main.ort_lon if main.ort_lon != 0.0 else 8.2)


static func sun_el_at(d_doy: int, h: float, lat: float, lon: float) -> float:
	"""elevation of the sun (°) on day d_doy at h o'clock Swiss time (summer time like main.sun_pos) - licht.gd ephem"""
	var y: int = int(Time.get_date_dict_from_system()["year"])
	var tz := 2.0 if d_doy >= 88 and d_doy < 300 else 1.0
	var d0: int = 367 * y - (7 * y) / 4 + 30 - 730530
	var d := float(d0 + d_doy) + (h - tz) / 24.0
	var e: Dictionary = Licht.ephem(d)
	var lst := fposmod(float(e["gmst0"]) + (h - tz) * 15.0 + lon, 360.0)
	return Licht.ecl_to_altaz(float(e["slon"]), 0.0, float(e["ecl"]), lst, lat).x


static func _cross(d_doy: int, lat: float, lon: float, lim: float, rising: bool) -> float:
	"""the hour when the sun passes lim (°) - morning (rising) or evening; -1 when it does not (polar day / night)"""
	var a := 0.0 if rising else 12.0
	var step := 0.25
	var prev := sun_el_at(d_doy, a, lat, lon)
	var h := a + step
	while h <= a + 12.0 + 0.001:
		var cur := sun_el_at(d_doy, h, lat, lon)
		if (rising and prev < lim and cur >= lim) or (not rising and prev >= lim and cur < lim):
			var lo := h - step
			var hi := h
			for _i in range(12):
				var mid := (lo + hi) / 2.0
				var em := sun_el_at(d_doy, mid, lat, lon)
				if (em >= lim) == rising:
					hi = mid
				else:
					lo = mid
			return (lo + hi) / 2.0
		prev = cur
		h += step
	return -1.0


func sun_times(d_doy := -1, lat := 999.0, lon := 999.0) -> Dictionary:
	"""sunrise, sunset (sun -0.833°), civil twilight (-6°), day length in hours - for the date and the place of the scene"""
	var pl := _place()
	var la := pl.x if lat == 999.0 else lat
	var lo := pl.y if lon == 999.0 else lon
	var dd := doy() if d_doy < 0 else d_doy
	var key := "%d|%.3f|%.3f" % [dd, la, lo]
	if _sun_cache.has(key):
		return _sun_cache[key]
	var rise := _cross(dd, la, lo, -0.833, true)
	var set_ := _cross(dd, la, lo, -0.833, false)
	var dawn := _cross(dd, la, lo, -6.0, true)
	var dusk := _cross(dd, la, lo, -6.0, false)
	var r := {"doy": dd, "lat": la, "lon": lo, "sunrise": snappedf(rise, 0.001), "sunset": snappedf(set_, 0.001),
			"dawn": snappedf(dawn, 0.001), "dusk": snappedf(dusk, 0.001),
			"day_h": snappedf(set_ - rise, 0.001) if rise >= 0.0 and set_ >= 0.0 else (24.0 if sun_el_at(dd, 12.5, la, lo) > 0.0 else 0.0)}
	if _sun_cache.size() > 64:
		_sun_cache.clear()
	_sun_cache[key] = r
	return r


static func hm(h: float) -> String:
	if h < 0.0:
		return "–"
	var mins := roundi(h * 60.0)
	return "%d:%02d" % [mins / 60, mins % 60]


# ---- every 0.5 s: from main._update_sky (after colors and licht) ---------------------------------------------------------
func update() -> void:
	if main == null or main.env == null:
		return
	var d := doy()
	var on: bool = main.seasons_on
	var bare := bare_k(d) if on else 0.0
	var bl := blossom_k(d) if on else 0.0
	var n_broad := 0
	for fm in main.foliage_mats:
		if not is_instance_valid(fm):
			continue
		var broad := bool(fm.get_meta("broad", false))
		var b := bare if broad else 0.0
		var k := 0.0
		if broad:
			n_broad += 1
			if n_broad % 3 == 1:                       # a third of the broad-leaved trees are fruit trees (blossom)
				k = bl
		var want := [snappedf(b, 0.01), snappedf(k, 0.01)]
		if fm.get_meta("jz", []) != want:
			fm.set_meta("jz", want)
			fm.set_shader_parameter("bare", want[0])
			fm.set_shader_parameter("blossom", want[1])
	var snow := snow_now()
	if snow > 0.0 and main.weather != "snow":
		main.grass_mat.set_shader_parameter("snow_amount", snow)
		for gm in main.ground_mats:
			gm.set_shader_parameter("snow_amount", snow)
	_leaves_tick(d)
	_now = state()


func snow_now() -> float:
	"""snow lying on the ground in winter (not in Bergtal: it has its own snow per season)"""
	if snow_mode == "off" or not main.seasons_on or Worlds.world_of(main.scene) == "bergtal":
		return 0.0
	var s := season()
	if s != "winter":
		return 0.0
	if snow_mode == "on" or float(main.ambient) <= SNOW_C:
		return 0.8
	return 0.0


func fog_want(h: float, el: float, calm: bool) -> float:
	"""colors._ground_tick: how much fog an autumn morning brings (0 .. 0.6) - calm, dry weather, around sunrise"""
	if not fog_on or not main.seasons_on or not calm or _testing():
		return 0.0
	var k := fog_k(float(doy()))
	if k <= 0.0:
		return 0.0
	var st := sun_times()
	var rise := float(st["sunrise"])
	if rise < 0.0:
		return 0.0
	if h < rise - 2.0 or h > rise + 2.5 or el > 15.0:
		return 0.0
	var fade := 1.0 - smoothstep(rise + 1.0, rise + 2.5, h)   # the sun warms the ground - the fog lifts
	return 0.6 * k * fade


func _leaves_tick(d: int) -> void:
	var k := fall_k(float(d))
	var lvl := 0
	if leaves_on and main.seasons_on and not _lite() and k > 0.0 and main.weather != "snow" and not _testing() and _trees_near():
		var w := clampf(float(main.wind) / 30.0, 0.0, 1.0)
		lvl = clampi(roundi(k * (1.0 + 2.0 * w)), 1, 3)
	if lvl == _leaf_level:
		if _leaves != null and lvl > 0:
			_wind_leaves()
		return
	_leaf_level = lvl
	if lvl == 0:
		if _leaves != null:
			_leaves.emitting = false
		return
	if _leaves == null:
		_leaves = _make_leaves()
		main.add_child(_leaves)
	_leaves.amount = [0, 24, 48, 90][lvl]
	_leaves.emitting = true
	_wind_leaves()


func _trees_near() -> bool:
	var n := 0
	for t in main.tree_spots:
		if (t[0] as Vector2).length() < 35.0:
			n += 1
	return n > 0


func _wind_leaves() -> void:
	"""leaves fall at ~1-1.5 m/s and drift with the wind (wind from the west -> to +x)"""
	var w: float = float(main.wind) * float(main.gust()) / 3.6
	_leaves.gravity = Vector3(0.35 * w, -1.1, 0.1 * w)


func _make_leaves() -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = 24
	p.lifetime = 9.0
	p.preprocess = 4.0
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(14, 2, 12)
	p.position = Vector3(0, 7, -10)
	p.direction = Vector3(0, -1, 0)
	p.spread = 40.0
	p.initial_velocity_min = 0.2
	p.initial_velocity_max = 0.6
	p.damping_min = 0.4
	p.damping_max = 1.0
	p.angle_min = 0.0
	p.angle_max = 360.0
	p.angular_velocity_min = -200.0
	p.angular_velocity_max = 200.0
	p.scale_amount_min = 0.7
	p.scale_amount_max = 1.3
	var g := Gradient.new()
	g.set_color(0, Color(0.75, 0.42, 0.1))
	g.set_color(1, Color(0.5, 0.26, 0.1))
	g.add_point(0.5, Color(0.8, 0.62, 0.15))
	p.color_initial_ramp = g
	var qm := QuadMesh.new()
	qm.size = Vector2(0.07, 0.05)
	var mt := StandardMaterial3D.new()
	mt.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mt.vertex_color_use_as_albedo = true
	mt.cull_mode = BaseMaterial3D.CULL_DISABLED
	mt.roughness = 0.9
	qm.material = mt
	p.mesh = qm
	p.emitting = false
	return p


# ---- MoveEye, tests ---------------------------------------------------------------------------------------------------
func state() -> Dictionary:
	var st := sun_times()
	var d := doy()
	return {"season": season(), "mode": cur_mode(), "doy": d, "sunrise": hm(float(st["sunrise"])), "sunset": hm(float(st["sunset"])),
			"day_h": st["day_h"], "bare": snappedf(bare_k(d), 0.01), "blossom": snappedf(blossom_k(d), 0.01),
			"leaves": maxi(_leaf_level, 0), "snow": snow_now() > 0.0, "occupancy": snappedf(occupancy(), 0.01),
			"visit_factor": snappedf(visit_factor(), 0.01)}


func reply() -> Dictionary:
	"""world_reply «season»: season, sunrise / sunset, day length, campsite occupancy - MoveEye does not read it yet"""
	var s := state()
	return {"season": s["season"], "doy": s["doy"], "sunrise": s["sunrise"], "sunset": s["sunset"], "day_h": snappedf(float(s["day_h"]), 0.01),
			"snow": s["snow"], "occupancy": s["occupancy"]}


func summary() -> String:
	var st := sun_times()
	var dh := float(st["day_h"])
	return T.t("%s · Sonnenaufgang %s · Sonnenuntergang %s · Tag %d h %02d min · Dämmerung %s–%s · Campingplatz zu %d %% belegt",
			[T.t(NAME_DE[season()]), hm(float(st["sunrise"])), hm(float(st["sunset"])), int(dh), roundi(fposmod(dh, 1.0) * 60.0) % 60,
			hm(float(st["dawn"])), hm(float(st["dusk"])), roundi(occupancy() * 100.0)])


func control(d: Dictionary) -> Dictionary:
	"""{do: info | set (key, value) | sun (doy, lat, lon) | year (lat, lon: sunrise / sunset on the 15th of every month)}"""
	var op := str(d.get("do", "info"))
	match op:
		"set":
			var k := str(d.get("key", ""))
			if k == "mode":
				set_mode(str(d.get("value", "auto")))
			elif k in SAVE:
				set(k, bool(d.get("value", true)) if typeof(get(k)) == TYPE_BOOL else str(d.get("value", "")))
				save()
				_leaf_level = -1
				main._update_sky()
		"sun":
			return {"ok": true, "sun": sun_times(int(d.get("doy", doy())), float(d.get("lat", 999.0)), float(d.get("lon", 999.0)))}
		"year":
			var out := []
			for mo in range(12):
				var dd: int = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349][mo]
				var st := sun_times(dd, float(d.get("lat", 999.0)), float(d.get("lon", 999.0)))
				out.append([mo + 1, hm(float(st["sunrise"])), hm(float(st["sunset"])), st["day_h"], season_of_doy(dd),
						snappedf(bare_k(dd), 0.01), float(OCC[mo])])
			return {"ok": true, "year": out}
	return {"ok": true, "info": state(), "summary": summary(), "lite": _lite(), "fps": Engine.get_frames_per_second(), "leaves_node": _leaves != null and _leaves.emitting}
