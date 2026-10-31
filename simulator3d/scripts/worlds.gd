extends RefCounted
## Welten (3D-4.x, Daniel 31.10.2026): die alten Szenen leben als **Orte** in wenigen grossen Welten.
##
## Welt «Bergtal» (bergtal.gd): Wald, Wildbeobachtung, Seeufer, Tarnen, Versteckspiel, Parcours, Bauernhof.
## Welt «Ferienpark am See» (ferienpark.gd): Voller Campingplatz, Lustiger Platz, Velodieb, Parkplatz, Stellplatz.
## Welt «Zuhause» (id «daheim», hier gebaut): Garten mit Haus, Schlafzimmer (im Haus), Baustelle nebenan.
## 3D-4.x «Vier kompakte Szenen» (kompakt.gd): Pfadilager (Lichtung im Lärchenwald) und Bergdorf (Taleingang an der
## Passstrasse) sind Orte im Bergtal, der Bauernhof mit Hofladen und Stellplätzen liegt im Ferienpark am See (Ostufer);
## das Festival-Gelände ist eine eigene Welt. Diese Orte haben mehrere MoveEye-Standorte («Standort an diesem Ort»):
## die Welt wird um den Standort gedreht und verschoben (pose()), der Ort selbst mit kompakt.gd auf seiner Fläche gebaut.
## Allein bleiben: Camping-Platz (klein, schnell, Standard), Ort von der Karte, Mein Zuhause (selbst gebaut), Meine Vorlage.
##
## Die alten Kennungen bleiben gültig (Steuerbefehl, MoveEye, Prüfstand, Einstellungen, Spiel-Assistent, Vorlagen, Tests):
## main.scene bleibt die alte Kennung (z. B. «wald»), damit Besucher, Abläufe, Spiele und Testläufe gleich bleiben; gebaut wird
## die Welt um den Ort herum (MoveEye steht im Nullpunkt), der Ort selbst mit dem alten Bauplan von scenes.gd auf einer
## ebenen Fläche (Radius R). Was über R hinausreicht, macht die Welt. «Allein» (main.welt_solo, --solo, Prüfstand) baut den
## Ort wie früher ohne Welt – damit die Messreihen vergleichbar bleiben.

const T = preload("res://scripts/i18n.gd")

# the worlds and the tools in the scene list (in this order)
const SHOWN := ["camping", "bergtal", "ferienpark", "festival", "daheim", "ort", "zuhause", "vorlage"]
const WORLDS := ["bergtal", "ferienpark", "daheim"]
# the default place of a world without its own build (daheim = the garden)
const DEFAULT := {"daheim": "garten"}
# old id -> [world, name of the place, x, z (world coordinates: valley / park / home), looking (degrees, 0 = -z), radius of
# the flat area (m)]. Bergtal: x/z like bergtal.gd (0 = north / down the valley). Ferienpark: like ferienpark.gd.
const PLACES := {
	"wald": ["bergtal", "Schattwald (Wald mit Feuerstelle)", 40.0, -720.0, 0.0, 55.0],
	"wild": ["bergtal", "Wildbeobachtung (Hochsitz, Futterkrippe)", 700.0, -160.0, 0.0, 50.0],
	"seeufer": ["bergtal", "Gumpisee-Ufer mit Steg", -140.0, -491.0, 180.0, 34.0],
	"tarnen": ["bergtal", "Tarnwiese (Tarnen und Kriechen)", 720.0, 0.0, 0.0, 50.0],
	"verstecken": ["bergtal", "Versteckspiel beim Murmelboden", -500.0, 400.0, 63.0, 52.0],
	"parcours": ["bergtal", "Verfolgungs-Parcours (Hochebene)", 840.0, -400.0, 0.0, 55.0],
	"bauernhof": ["bergtal", "Hinterstafel (Bauernhof der Alp)", 40.0, 230.0, 0.0, 50.0],
	"pfadilager": ["bergtal", "Pfadilager auf der Waldlichtung", -150.0, -800.0, 0.0, 60.0],      # 3D-4.x kompakt_pfadi.gd (CLEARING)
	"bergdorf": ["bergtal", "Bergdorf am Taleingang (mit Stellplatz)", 195.0, -930.0, 0.0, 62.0],  # 3D-4.x kompakt_dorf.gd (at the pass road)
	"hofladen": ["ferienpark", "Bauernhof mit Hofladen am Ostufer (Stellplätze)", 268.0, -128.0, 0.0, 42.0],   # 3D-4.x kompakt_hof.gd
	"camping_voll": ["ferienpark", "Zeltwiese in der Hochsaison (voller Platz)", -100.0, -68.0, 0.0, 42.0],
	"lustig": ["ferienpark", "Spielwiese am Strand (lustiger Platz)", -145.0, -105.0, 0.0, 38.0],
	"velodieb": ["ferienpark", "Velo am Parkrand (Velodieb)", 265.0, 50.0, 0.0, 38.0],
	"parkplatz": ["ferienpark", "Grosser Parkplatz beim Eingang", -238.0, -78.0, 0.0, 40.0],
	"stellplatz": ["ferienpark", "Wohnmobil-Stellplatz (Ost)", 265.0, -40.0, 0.0, 42.0],
	"garten": ["daheim", "Garten und Haus", 0.0, 0.0, 0.0, 40.0],
	"schlafzimmer": ["daheim", "Schlafzimmer im Haus (Wecker)", 0.0, 0.0, 0.0, 5.0],     # x/z/looking: _home_xf (in the house)
	"baustelle": ["daheim", "Baustelle nebenan", 52.0, 5.0, 0.0, 40.0]}
const ORDER := {"bergtal": ["wald", "wild", "seeufer", "tarnen", "verstecken", "parcours", "bauernhof", "pfadilager", "bergdorf"],
		"ferienpark": ["camping_voll", "lustig", "velodieb", "parkplatz", "stellplatz", "hofladen"],
		"daheim": ["garten", "schlafzimmer", "baustelle"]}
const OWN := {"bergtal": "– Schlafplatz im Bergtal (oben wählen) –", "ferienpark": "– Standort im Ferienpark (oben wählen) –"}


static func world_of(id: String) -> String:
	"""the world an id belongs to (an old scene id -> its world; a world or a tool -> itself)"""
	if PLACES.has(id):
		return str(PLACES[id][0])
	return id


static func is_place(id: String) -> bool:
	return PLACES.has(id)


static func default_place(id: String) -> String:
	"""a world without its own build -> its first place (daheim -> garten); everything else stays"""
	return str(DEFAULT.get(id, id))


static func place_name(id: String) -> String:
	return str(PLACES[id][1]) if PLACES.has(id) else ""


const SHORT := {"bergtal": "Bergtal", "ferienpark": "Ferienpark am See", "daheim": "Zuhause"}
const Kompakt = preload("res://scripts/kompakt.gd")     # 3D-4.x: places with several MoveEye spots (Pfadilager, Bergdorf, Hofladen)


static func pose(main, id: String) -> Array:
	"""where MoveEye stands for a place: [x, z, looking] in world coordinates. A compact place (kompakt.gd): its centre plus
	the chosen spot (spot coordinates relative to the centre, axes like the world: x = east, z = south)"""
	var p: Array = PLACES[id]
	if Kompakt.is_kompakt(id):
		var sps: Dictionary = Kompakt.spots_of(id)
		var k := str(main.scene_spot(id)) if main != null and main.has_method("scene_spot") else ""
		if not sps.has(k):
			k = str(Kompakt.spot_options(id)[0][0])
		var sp: Array = sps[k]
		return [float(p[2]) + float(sp[1]), float(p[3]) + float(sp[2]), float(sp[3])]
	return [float(p[2]), float(p[3]), float(p[4])]


static func full_name(id: String) -> String:
	"""«Bergtal · Schattwald (Wald mit Feuerstelle)» for a place ("" for anything else)"""
	if not PLACES.has(id):
		return ""
	return "%s · %s" % [T.t(str(SHORT[world_of(id)])), T.t(place_name(id))]


static func place_options(world: String) -> Array:
	"""«Ort in dieser Welt»: [id, name] – the world itself first (if it has its own build)"""
	var out := []
	if OWN.has(world):
		out.append(["", OWN[world]])
	for k in ORDER.get(world, []):
		out.append([k, place_name(k)])
	return out


static func places_of(world: String) -> Array:
	"""[[id, name, x, z, looking, radius], …] of a world"""
	var out := []
	for k in ORDER.get(world, []):
		var p: Array = PLACES[k]
		out.append([k, p[1], p[2], p[3], p[4], p[5]])
	return out


static func active(main, world: String) -> String:
	"""the place of this world that is loaded now ("" = none: the world itself) - not in «allein»"""
	if main == null or main.get("scene") == null:
		return ""
	var sc := str(main.scene)
	if PLACES.has(sc) and str(PLACES[sc][0]) == world and not solo(main, sc):
		return sc
	return ""


static func solo(main, id: String) -> bool:
	"""«allein»: the old scene without its world (main.welt_solo / --solo, or a «scenario» with solo: true)"""
	if main == null:
		return false
	return bool(main.get("welt_solo")) or str(main.get("solo_scene")) == id


# ---- building --------------------------------------------------------------------------------------------------------
static func build(s, id: String) -> void:
	"""scenes.gd: an old scene id inside its world"""
	var w := world_of(id)
	match w:
		"bergtal":
			preload("res://scripts/bergtal.gd").build_scene(s)       # around the place (bergtal.gd reads active())
			_place(s, id, float(PLACES[id][5]))
		"ferienpark":
			preload("res://scripts/ferienpark.gd").build_scene(s)
			_place(s, id, float(PLACES[id][5]))
		"daheim":
			_home(s, id)
		_:
			s.build_legacy(id)


static func _place(s, id: String, r: float) -> void:
	"""the old scene at the origin, clipped to its flat area (the world is around it)"""
	if Kompakt.is_kompakt(id):                                   # 3D-4.x: a compact place (several spots, its own builder)
		Kompakt.build_place(s, id, r)
		s.data["welt"] = {"world": world_of(id), "place": id, "r": r}
		return
	var m = s.m
	var root0: Node3D = s.root
	var n := Node3D.new()
	n.name = "ort_" + id
	root0.add_child(n)
	s.root = n
	s.clip = r
	m.ob_clip = r + 2.0
	s.build_legacy(id)
	s.prune(n, r + 3.0)
	s.clip = 0.0
	m.ob_clip = 0.0
	s.root = root0
	s.data["welt"] = {"world": world_of(id), "place": id, "r": r}


# the home world (flat): the garden at the origin, the bedroom in its house, the building site next door
static func _home_xf(id: String) -> Transform3D:
	"""where a place of the home world is (world coordinates of the home = the garden)"""
	if id == "schlafzimmer":
		# the room (x -3 .. 3.5, z -5 .. 1.5, centre 0.25 / -1.75) in the house of the garden (centre -8 / -17, turned 10°),
		# its door to the front of the house
		var b := Basis(Vector3.UP, deg_to_rad(10.0) + PI)
		return Transform3D(b, Vector3(-8.0, 0, -17.0) - b * Vector3(0.25, 0, -1.75))
	var p: Array = PLACES[id]
	return Transform3D(Basis(Vector3.UP, deg_to_rad(float(p[4]))), Vector3(float(p[2]), 0, float(p[3])))


static func _home(s, id: String) -> void:
	var m = s.m
	var to_active := _home_xf(id).affine_inverse()               # home -> world (MoveEye at the origin of the active place)
	var others: Array = ORDER["daheim"].filter(func(k): return k != id)
	# the neighbours first: only things (no sensors, no data of the scene), in their own frame
	var keep_out := [[Vector2.ZERO, float(PLACES[id][5]) + (1.0 if id == "schlafzimmer" else 2.0)]]
	var excl := []
	for k in others:
		if k == "schlafzimmer":
			continue                                            # inside the house: nothing to see from outside
		var xf: Transform3D = to_active * _home_xf(k)
		_decor(s, k, xf, float(PLACES[k][5]), keep_out, id == "schlafzimmer" and k == "garten")
		excl.append([xf.origin, float(PLACES[k][5]) * 0.8])
	s.excl = excl
	s.build_legacy(id)
	s.excl = []
	s.data["welt"] = {"world": "daheim", "place": id, "r": float(PLACES[id][5])}


static func _decor(s, id: String, xf: Transform3D, r: float, keep_out: Array, road: bool) -> void:
	"""a neighbouring place as scenery: its things in a node at xf, obstacles moved there; what it sets in main (sensors,
	door, test aids, data of the scene) is put back afterwards"""
	var m = s.m
	var save := {"obj": m.obj.duplicate(), "door_node": m.door_node, "door_light": m.door_light, "window_mat": m.window_mat,
			"test_props": m.test_props, "bike_node": m.bike_node, "data": s.data}
	var root0: Node3D = s.root
	var n := Node3D.new()
	n.name = "nachbar_" + id
	n.transform = xf
	root0.add_child(n)
	s.root = n
	s.data = {}
	m.test_props = {}
	s.clip = r
	s.no_road = not road
	s.decor = true
	m.ob_clip = r + 2.0
	m.ob_xf = xf
	m.ob_excl = keep_out
	s.build_legacy(id, false)
	s.prune(n, r + 3.0)
	s.clip = 0.0
	s.no_road = false
	s.decor = false
	m.ob_clip = 0.0
	m.ob_xf = Transform3D.IDENTITY
	m.ob_excl = []
	s.root = root0
	s.data = save["data"]
	m.obj = save["obj"]
	m.door_node = save["door_node"]
	m.door_light = save["door_light"]
	m.window_mat = save["window_mat"]
	m.test_props = save["test_props"]
	m.bike_node = save["bike_node"]


static func info(main) -> Dictionary:
	"""control {"action": "welt"}: the worlds, their places and what is loaded"""
	var ws := {}
	for w in WORLDS:
		ws[w] = place_options(w)
	return {"ok": true, "scene": main.scene, "world": world_of(str(main.scene)), "place": str(main.scene) if PLACES.has(str(main.scene)) else "",
			"solo": solo(main, str(main.scene)), "shown": SHOWN, "worlds": ws}
