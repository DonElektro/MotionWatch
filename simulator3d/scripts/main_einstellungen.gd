extends Object
## Teil von main.gd (Vorschlag 24 «main.gd zerlegen»): die Einstellungen (Controls): add_control, die Liste aller Regler und Schalter, Reihenfolge, Laden und Speichern.
## main.gd lädt diesen Teil erst beim ersten Aufruf (_mod) und leitet seine Funktionen weiter: main.xyz bleibt gleich.
## Hier steht «main.» vor allem, was zu main.gd gehört.

var main                              # main.gd
const Kompakt := preload("res://scripts/kompakt.gd")
const Quality := preload("res://scripts/quality.gd")
const Stimme = preload("res://scripts/abenteuer_stimme.gd")
const T := preload("res://scripts/i18n.gd")
const Versionen = preload("res://scripts/versionen.gd")
const Worlds := preload("res://scripts/worlds.gd")


func add_control(type: String, id: String, label: String, getter, setter, group: String, extra) -> void:
	var st = setter
	if setter != null and type != "button":
		st = func(v):                                 # a changed setting is saved (a few seconds later)
			setter.call(v)
			main._settings_dirty = true
	main.controls.append({"type": type, "id": id, "label": label, "group": group, "get": getter, "set": st, "extra": extra})


func _simple_ok(c: Dictionary) -> bool:
	"""what «Einfach» shows (Menüs A: the list SIMPLE_IDS, about 60); everything else is «Experte»"""
	if c.group == "Spiel":
		return c.id in main.GAME_MAIN or c.id in main.DISC_SIMPLE
	return c.id in main.SIMPLE_IDS or str(c.id).begins_with("welt_ort_")


func _order_controls() -> void:
	"""every setting into its group and part, sorted like GROUPS (the window and the page of MoveEye show this order)"""
	var gi := {}
	for i in range(main.GROUPS.size()):
		gi[main.GROUPS[i][0]] = i
	var keyed := []
	for i in range(main.controls.size()):
		var c: Dictionary = main.controls[i]
		c.extra = c.extra.duplicate()                     # several controls share one dictionary ({"expert": true})
		var pl = main.PLACE.get(c.id, null)
		if pl == null and str(c.id).begins_with("spawn_"):
			pl = ["Besuch", "Menschen einzeln" if str(c.id).trim_prefix("spawn_") in main.PEOPLE_KINDS else "Wildtiere"]
		if main.VISIT_SUB.has(c.id):
			pl = ["Besuch", main.VISIT_SUB[c.id]]              # Menüs A: people out of «Tiere schicken», long lists split
		elif pl == null and str(c.extra.get("sub", "")) in ["Menschen schicken", "Tiere schicken"]:
			pl = [c.group, "Menschen einzeln" if str(c.extra["sub"]) == "Menschen schicken" else "Wildtiere"]   # a new button of another part
		if main.VISIT_EMOJI.has(str(c.id).trim_prefix("spawn_")):
			c.extra["emoji"] = main.VISIT_EMOJI[str(c.id).trim_prefix("spawn_")]      # a picture on the button of the page (3D-3.38)
		if pl != null:
			c.group = pl[0]
			c.extra["sub"] = pl[1]
		if main.ALIAS_IDS.has(c.id):                           # Menüs A: the old id of a merged control - only /control, tests, settings
			c.extra["alias"] = main.ALIAS_IDS[c.id]
			c.extra["wiz"] = true                          # «wiz»: not in the panel, not on the page of MoveEye (also older MoveEye)
			c.extra.erase("devwin")                        # pruef_open: no second «Prüfstand» in the developer window
		if c.id in main.PHOTO_IDS and main.zwilling != null and not c.has("ro"):
			c["ro"] = func(): return main.zwilling.cur().is_empty()   # Menüs A: without a photo of the place these do nothing - greyed out
			c.extra["ro_tip"] = "Zuerst ein Foto des Platzes laden (Gegenstände → Foto des Platzes)"   # tooltip on the page of MoveEye
		c.group = main.GROUP_RENAME.get(c.group, c.group)       # 3D-4.21: names like MoveEye
		if main.SUB_RENAME.has(str(c.extra.get("sub", ""))):
			c.extra["sub"] = main.SUB_RENAME[str(c.extra.get("sub", ""))]
		if c.id in main.DEV_IDS:
			c.extra["sub"] = "Updates" if c.id == "dev_updates" else ""
		if c.group == "Spiel":                            # 3D-4.7: only open / start / stop on the card, the rest in the assistant
			if c.id in main.DISC_IDS:
				c.extra["sub"] = "Entdecken"           # Erlebniswelt 20–23: its own part on the card
			elif c.id in main.GAME_MAIN:
				c.extra["sub"] = ""                    # straight on the card (no part «Runde» any more)
			else:
				c.extra["wiz"] = true
				c.extra["sub"] = "Assistent"
		c.extra["gid"] = main.GROUP_IDS.get(c.group, str(c.group).to_lower())
		if not main._simple_ok(c):
			c.extra["expert"] = true                      # 3D-3.90: «Einfach» = about 60 settings (the page of MoveEye has the same switch, stored in MoveEye «sim»)
		var g: int = gi.get(c.group, main.GROUPS.size())
		var sub := str(c.extra.get("sub", ""))
		c.extra["icon"] = main.GROUPS[g][2] if g < main.GROUPS.size() else ""
		c.extra["iconk"] = main.GROUPS[g][1] if g < main.GROUPS.size() else ""          # the drawn symbol (page of MoveEye from 2.93.16)
		var si: int = (main.GROUPS[g][3] as Array).find(sub) if g < main.GROUPS.size() else 0
		keyed.append([g * 10000 + max(si, 0) * 100, i, c])   # Menüs A: Besuch has 13 parts now (1000 was too small)
	keyed.sort_custom(func(a, b): return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1]))
	main.controls = keyed.map(func(k): return k[2])
	# 3D-4.21 (Menü 2, like MoveEye): «Einfach» = the main switch of every group - a group without one gets its first switch
	var has_main := {}
	for c in main.controls:
		if not c.extra.get("expert", false) and not c.extra.get("hide", false) and not c.extra.get("wiz", false):
			has_main[c.group] = true
	for c in main.controls:
		if has_main.has(c.group) or c.group in ["Entwickler", "Spiel"] or c.extra.get("hide", false) or c.extra.get("wiz", false):
			continue
		if c.type in ["toggle", "select", "button"]:
			c.extra.erase("expert")
			has_main[c.group] = true


func _register_controls() -> void:
	"""every setting of the simulator - for the window and for the web page of MoveEye (CONTROL protocol).
	extra "expert": true = only shown with «Experte» - in the window and on the page of MoveEye (its switch Einfach / Experte
	is stored in the settings of MoveEye, page «sim», like on its main page)."""
	var sc := []
	for s in Worlds.SHOWN:                        # 3D-4.x Welten: only the worlds and the tools (the old scenes are places in them)
		sc.append([s, main.Scenes.name_of(s)])
	var ex := {"expert": true}
	main.add_control("select", "scene", "Szene", func(): return Worlds.world_of(main.scene), func(v): main.set_scene(v), "Szene", {"options": sc})
	for w in Worlds.WORLDS:                       # «Ort in dieser Welt»: the old scenes of this world (one select per world)
		main.add_control("select", "welt_ort_" + w, "Ort in dieser Welt", func(): return main.scene if Worlds.is_place(main.scene) else "",
				func(v): main.set_scene(str(v) if str(v) != "" else w), "Szene", {"options": Worlds.place_options(w)})
		main.controls[-1]["only"] = func(): return Worlds.world_of(main.scene) == w
	main.add_control("toggle", "welt_solo", "Alte Szenen allein laden (ohne Welt drumherum – für Prüfstand-Vergleiche)", func(): return main.welt_solo,
			func(v): main.welt_solo = bool(v); main.set_scene(main.scene), "Szene", {"expert": true})
	main.add_control("button", "home_edit", "Mein Zuhause bauen (Baukasten mit der Maus)", null, func(): main.home_editor.open(true), "Szene")
	main.add_control("select", "fp_spot", "Standort im Ferienpark am See", func(): return main.fp_spot, func(v): main.set_fp_spot(str(v)), "Szene",
			{"options": preload("res://scripts/ferienpark.gd").spot_options()})
	main.controls[-1]["only"] = func(): return main.scene == "ferienpark"   # 3D-4.28: only shown in its scene (window and MoveEye; not in a place of the park)
	var Bt = preload("res://scripts/bergtal.gd")
	main.add_control("select", "bt_spot", "Schlafplatz im Bergtal", func(): return main.bt_spot, func(v): main.set_bt("bt_spot", str(v)), "Szene", {"options": Bt.spot_options()})
	main.add_control("select", "bt_bed", "Übernachten im Bergtal", func(): return main.bt_bed, func(v): main.set_bt("bt_bed", str(v)), "Szene", {"options": Bt.BEDS})
	var mo := []
	for k in Bt.MOUNTS:
		mo.append([k, Bt.MOUNTS[k][0]])
	main.add_control("select", "bt_mount", "MoveEye-Halterung am Schlafplatz (Bergtal)", func(): return main.bt_mount, func(v): main.set_bt("bt_mount", str(v)), "Szene", {"options": mo})
	main.add_control("select", "bt_bag", "Schlafsack (Bergtal)", func(): return main.bt_bag, func(v): main.set_bt("bt_bag", str(v)), "Szene", {"options": [["sommer", "Sommerschlafsack"], ["winter", "Winterschlafsack"]], "expert": true})
	main.add_control("toggle", "bt_stove", "Kocher am Schlafplatz (Bergtal)", func(): return main.bt_stove, func(v): main.set_bt("bt_stove", bool(v)), "Szene", {"expert": true})
	main.add_control("toggle", "bt_wall", "Windschutzmauer aus Steinen bauen (Bergtal)", func(): return main.bt_wall, func(v): main.set_bt("bt_wall", bool(v)), "Szene")
	main.add_control("select", "bt_orient", "Orientierung im Bergtal", func(): return main.bt_orient, func(v): main.set_bt("bt_orient", str(v)), "Szene",
			{"options": [["leicht", "leicht (Karte, Kompass, eigener Standort)"], ["mittel", "mittel (Karte und Kompass)"], ["schwer", "schwer (nur Wegweiser)"]], "expert": true})
	main.add_control("text", "bt_mark", "Eigene Markierung auf der Karte (Name; wird in der Bildmitte gesetzt)", func(): return "", func(v): main.bt_mark(str(v)), "Szene", {"expert": true})
	main.add_control("button", "bt_here", "Hier übernachten (Bergtal: der Platz in der Bildmitte oder beim Mover)", null, func(): main.bt_here(), "Szene")
	main.add_control("select", "bt_goto", "Schnellreise im Bergtal (Ort wählen)", func(): return "", func(v): main.bt_goto(str(v)), "Szene", {"options": Bt.place_options()})
	main.add_control("select", "bt_season", "Jahreszeit im Bergtal", func(): return main.bt_season, func(v): main.set_bt("bt_season", str(v)), "Szene",
			{"options": [["auto", "nach dem Monat (Jahreszeit)"], ["fruehling", "Frühling"], ["sommer", "Sommer"], ["herbst", "Herbst (Lärchen gelb, Nebel)"], ["winter", "Winter (Schnee, Eis)"]]})
	main.add_control("button", "bt_ride", "Mit der Materialseilbahn fahren (Bergtal)", null, func(): main._bt_do("ride"), "Szene", {"expert": true})
	main.add_control("button", "bt_morning", "Wie gut war dein Platz? (Bergtal: Bewertung jetzt)", null, func(): main._bt_do("morning"), "Szene", {"expert": true})
	# 3D-4.40: Horror-Modus «Das Hospiz» opens from the 5th mood of the Bergtal adventure (bergtal_abenteuer.gd), no button here
	main.add_control("toggle", "bt_events", "Bergtal: Ereignisse von selbst (Steinschlag, Fremder, Tier am Proviant, Wetterumschwung)", func(): return main.bt_events, func(v): main.bt_events = bool(v), "Besuch", {"sub": "Von selbst"})
	main.add_control("button", "bt_ev_rockfall", "Steinschlag (Bergtal)", null, func(): main._bt_do("rockfall"), "Besuch", {"sub": "Abläufe"})
	main.add_control("button", "bt_ev_stranger", "Fremder am Rucksack (Bergtal)", null, func(): main._bt_do("stranger"), "Besuch", {"sub": "Abläufe"})
	main.add_control("button", "bt_ev_food", "Tier am Proviant (Bergtal)", null, func(): main._bt_do("fox_food"), "Besuch", {"sub": "Abläufe"})
	main.add_control("button", "bt_ev_storm", "Gewitter zieht auf (Bergtal)", null, func(): main._bt_do("storm"), "Wetter", {"sub": "Mehr Wetter"})
	main.add_control("button", "bt_ev_fog", "Nebel kommt schnell (Bergtal)", null, func(): main._bt_do("fog"), "Wetter", {"sub": "Mehr Wetter"})
	main.add_control("button", "bt_ev_fogsea", "Nebelmeer (Bergtal: das Tal im Nebel, oben Sonne)", null, func(): main._bt_do("fogsea"), "Wetter", {"sub": "Mehr Wetter"})
	preload("res://scripts/bergtal_aussicht.gd").add_controls(main)     # «Bergtal · Aussichtspunkte»: Fernrohr, Panorama, Reichweite …
	for _c in main.controls:   # Bergtal-only controls: only shown in its scene (like fp_spot); season, quick travel, events also in its places
		if str(_c.id).begins_with("bt_"):
			if str(_c.id) in ["bt_season", "bt_goto", "bt_events", "bt_orient", "bt_mark"] or str(_c.id).begins_with("bt_ev_"):
				_c["only"] = func(): return Worlds.world_of(main.scene) == "bergtal"
			else:
				_c["only"] = func(): return main.scene == "bergtal"
			if _c.group == "Szene":
				_c.extra = _c.extra.duplicate()
				_c.extra["sub"] = "Bergtal"            # 3D-4.36 (Daniel): own part «Bergtal» on the card Szene, only in the Bergtal
	main.add_control("select", "szene_spot", "Standort an diesem Ort (Pfadilager, Hofladen, Bergdorf, Festival)", func(): return main.scene_spot(main.scene),
			func(v): main.set_scene_spot(str(v)), "Szene", {"options": main._spot_options()})     # 3D-4.x: where MoveEye stands in a compact place (kompakt.gd)
	main.controls[-1]["only"] = func(): return Kompakt.is_kompakt(main.scene)
	main.add_control("map", "ort_map", "Ort auf der Karte wählen (Schweiz)", func(): return "%.6f, %.6f" % [main.ort_lat, main.ort_lon] if main.ort_lat != 0.0 else "",
			func(v): main.set_place_text(str(v)), "Ort von der Karte")
	main.add_control("text", "ort", "Ort (Name oder Koordinaten, z. B. «Zermatt» oder «46.0207, 7.7491»)", func(): return main.place_label(), func(v): main.set_place_text(str(v)), "Ort von der Karte")
	main.add_control("slider", "hour", "Uhrzeit", func(): return snappedf(main.hour(), 0.01), func(v): main.set_hour(v), "Szene", {"min": 0, "max": 23.75, "step": 0.25, "unit": "h"})
	main.add_control("select", "season", "Jahreszeit (Sonnenbahn)", func(): return main.season, func(v): main.season = str(v); main._sun_cache = [-1.0, Vector2.ZERO]; main._update_sky(), "Szene",
			{"options": [["today", "wie heute (echtes Datum)"], ["1", "Januar"], ["2", "Februar"], ["3", "März"], ["4", "April"], ["5", "Mai"], ["6", "Juni"],
			["7", "Juli"], ["8", "August"], ["9", "September"], ["10", "Oktober"], ["11", "November"], ["12", "Dezember"]]})
	main.add_control("slider", "speed", "Zeit läuft x-fach", func(): return main.speed, func(v): main._set_speed(v), "Szene", {"min": 1, "max": 120, "step": 1, "unit": "×", "expert": true})
	main.add_control("toggle", "moon_auto", "Mondphase automatisch (Ort, Form und Licht des Monds nach Datum und Uhrzeit)", func(): return main.moon_auto, func(v): main.moon_auto = v, "Szene", {"expert": true})
	main.add_control("slider", "moon", "Mondphase fest: beleuchteter Teil (0 = Neumond, 1 = Vollmond)", func(): return main.moon, func(v):
		main.moon = v
		main.moon_auto = false, "Szene", {"min": 0, "max": 1, "step": 0.1, "expert": true})
	main.add_control("slider", "cam1_yaw", "Weitwinkel am Mast: Richtung", func(): return main.cam1_yaw, func(v): main.cam1_yaw = v, "Szene", {"min": -90, "max": 90, "step": 1, "unit": "°", "expert": true})
	main.add_control("select", "weather", "Wetter", func(): return main.weather, func(v): main.weather = v, "Wetter",
			{"options": [["clear", "klar"], ["cloudy", "bewölkt"], ["rain", "Regen"], ["fog", "Nebel"], ["snow", "Schnee"]]})
	main.add_control("toggle", "world_cloth", "Fahnen und Wäsche im Wind", func(): return main.world_cloth, func(v): main.set_cloth(v), "Wetter", ex)
	main.add_control("toggle", "world_smoke", "Rauch aus Kaminen", func(): return main.world_smoke, func(v): main.set_smoke(v), "Wetter", ex)
	main.add_control("toggle", "world_fireflies", "Glühwürmchen in warmen Nächten", func(): return main.world_fireflies, func(v): main.world_fireflies = v, "Wetter", ex)
	main.add_control("toggle", "fauna_on", "Vögel am Tag (fliegen vorbei, Krähen, Elstern und Möwen am Boden), Fledermäuse in der Nacht (warm im Wärmebild, typische Fehlalarm-Ursache)", func(): return main.fauna_on, func(v): main.fauna_on = bool(v); main.fauna.on = main.fauna_on, "Wetter", {"sub": "Natur und Wind"})
	main.add_control("toggle", "gusts", "Wind in Böen", func(): return main.gusts, func(v): main.gusts = v, "Wetter", ex)
	main.add_control("toggle", "cloud_shadows", "Wolkenschatten (die Helligkeit wechselt)", func(): return main.cloud_shadows, func(v): main.cloud_shadows = v, "Wetter", ex)
	main.add_control("slider", "lamp_share", "Nachts mit Stirnlampe oder Handylicht", func(): return main.lamp_share, func(v): main.lamp_share = v, "Besuch", {"min": 0, "max": 1, "step": 0.05, "expert": true})
	main.add_control("toggle", "look_at_light", "Menschen schauen zum Licht, wenn es angeht", func(): return main.look_at_light, func(v): main.look_at_light = v, "Besuch", ex)
	main.add_control("slider", "wind", "Wind", func(): return main.wind, func(v): main.wind = v, "Wetter", {"min": 0, "max": 120, "step": 1, "unit": "km/h"})
	main.add_control("toggle", "real_weather", "Echtes Wetter vom Ort (alle 10 Minuten, braucht Internet)", func(): return main.real_weather, func(v): main.real_weather = v; main.life._wx_t = -10000.0, "Wetter")
	main.add_control("toggle", "surprise_on", "Überraschungsnacht: nachts ab und zu Stromausfall, Nebelbank, Ablenkung, Scheinwerfer, ein Tier steht still – am Morgen die Bewertung von MoveEye", func(): return main.surprise_on, func(v): main.surprise.set_on(bool(v)), "Wetter")
	main.add_control("toggle", "night_weather", "Wetterverlauf über die Nacht (Dämmerung, Regenschauer, Tau auf der Linse, Morgennebel)", func(): return main.night_weather, func(v): main.night_weather = v; main._nw["day"] = -1, "Wetter")
	main.add_control("toggle", "real_time", "Echte Uhrzeit (die Uhr des PCs)", func(): return main.real_time, func(v): main.real_time = v, "Szene")
	main.add_control("slider", "ambient", "Temperatur", func(): return main.ambient, func(v): main.ambient = v, "Wetter", {"min": -15, "max": 40, "step": 0.5, "unit": "°C"})
	main.add_control("slider", "humidity", "Luftfeuchtigkeit", func(): return main.humidity, func(v): main.humidity = v, "Wetter", {"min": 10, "max": 100, "step": 1, "unit": "%", "expert": true})
	main.add_control("slider", "pressure", "Luftdruck", func(): return main.pressure, func(v): main.pressure = v, "Wetter", {"min": 960, "max": 1040, "step": 0.5, "unit": "hPa", "expert": true})
	main.add_control("button", "storm", "Sturm zieht auf", null, func(): main.storm_t = main.now(), "Wetter", ex)
	main.add_control("toggle", "thunder", "Gewitter mit Blitzen (bei Regen; die Blitze sind auch eine typische Fehlalarm-Ursache)", func(): return main.thunder, func(v): main.thunder = v, "Wetter")
	# visitors: one button each (the window has the pictures to drag, the web page these buttons)
	for k in main.VISITOR_LIST:
		main.add_control("button", "spawn_" + k[0], k[1], null, func(): main.visit(k[0]), "Besuch")
	main.add_control("button", "car", "Auto", null, func(): main.car(), "Besuch")
	main.add_control("button", "thief", "Dieb (Velo, Tür)", null, func(): main.thief(), "Besuch")
	main.add_control("button", "dogwalk", "Spaziergang mit Hund", null, func(): main.visit("dogwalk"), "Besuch")
	main.add_control("button", "herd", "Rehrudel", null, func(): main.visit("herd"), "Besuch")
	# 3D-3.39: more visitors (single people and animals are in VISITOR_LIST; these come in groups or do something)
	main.add_control("button", "couple", "Paar (zu zweit)", null, func(): main.visit("couple"), "Besuch")
	main.add_control("button", "horse_walk", "Mit dem Pferd unterwegs", null, func(): main.visit("horse_walk"), "Besuch")
	main.add_control("button", "cows", "Kühe auf der Weide", null, func(): main.visit("cows"), "Besuch")
	main.add_control("button", "sheep_flock", "Schafherde", null, func(): main.visit("sheep_flock"), "Besuch")
	main.add_control("button", "bats", "Fledermäuse am Licht (nachts)", null, func(): main.visit("bats"), "Besuch")
	main.add_control("button", "owl", "Eule fliegt vorbei", null, func(): main.visit("owl"), "Besuch")
	main.add_control("button", "burglar", "Einbruchsversuch (schleicht, prüft die Tür – flieht vor Licht und Sirene)", null, func(): main.visit("burglar"), "Besuch")
	main.add_control("button", "sneaker", "Vorsichtiger Schleicher (von Deckung zu Deckung, kriecht, erstarrt bei Licht, Lampe aus)", null, func(): main.visit("sneaker"), "Besuch")
	main.add_control("button", "bbq", "Grillabend (Grill, Rauch, Freunde kommen)", null, func(): main.visit("bbq"), "Besuch")
	main.add_control("button", "homecoming", "Spät heimkommen (Auto hält, Tür auf und zu)", null, func(): main.visit("homecoming"), "Besuch")
	main.add_control("button", "parcel", "Paket wird gebracht", null, func(): main.visit("parcel"), "Besuch")
	main.add_control("button", "fox_trash", "Fuchs am Abfalleimer", null, func(): main.visit("fox_trash"), "Besuch")
	main.add_control("button", "boar_group", "Wildschweine mit Jungen", null, func(): main.visit("boar_group"), "Besuch")
	main.add_control("button", "kids_tag", "Kinder spielen Fangen", null, func(): main.visit("kids_tag"), "Besuch")
	main.add_control("button", "mowing", "Bauer mäht mit dem Traktor", null, func(): main.visit("mowing"), "Besuch")
	main.add_control("button", "night_lapse", "Ganze Nacht im Zeitraffer (20 → 6 Uhr, 60-fach, etwa 10 Minuten)", null, func(): main.stories.night_lapse(), "Besuch")
	main.add_control("toggle", "calendar", "Kalender: am Wochenende mehr Leute, im Winter weniger", func(): return main.calendar_on, func(v): main.calendar_on = v, "Besuch")
	main.add_control("button", "tractor", "Traktor", null, func(): main.visit("tractor"), "Besuch")
	main.add_control("button", "moto", "Töff", null, func(): main.visit("moto"), "Besuch")
	main.add_control("button", "van", "Lieferwagen", null, func(): main.visit("van"), "Besuch")
	main.add_control("button", "car_park", "Auto kommt an und parkiert (Leute steigen aus)", null, func(): main.visit("car_park"), "Besuch", ex)
	main.add_control("button", "bench", "Besuch setzt sich auf die Bank (Lustiger Platz)", null, func(): main.visit("bench"), "Besuch", ex)
	main.add_control("button", "feed", "Reh kommt zur Futterstelle (Wildbeobachtung)", null, func(): main.visit("feed_deer"), "Besuch", ex)
	main.add_control("button", "garden_person", "Besuch kommt durchs Gartentor (Garten)", null, func(): main.visit("garden_person"), "Besuch", ex)
	var pre_opts := [["", "– Vorlage wählen –"]]
	for vp in main.VISIT_PRESETS:
		pre_opts.append([vp[0], vp[1]])
	main.add_control("select", "visit_preset", "Vorlage für den Besuch (stellt «Von selbst» passend ein)", func(): return main.visit_preset, func(v): main.apply_visit_preset(str(v)), "Besuch",
			{"options": pre_opts})
	main.add_control("button", "clear", "Alle Besucher weg", null, func(): main.clear_visitors(), "Besuch")
	main.add_control("toggle", "auto", "ab und zu Besuch von selbst", func(): return main.auto_visitors, func(v): main.auto_visitors = v, "Besuch")
	main.add_control("toggle", "daily_life", "Tagesablauf: jeder kommt zu seiner Zeit (Fuchs nachts, Reh in der Dämmerung, Briefträger um 10 Uhr …)", func(): return main.daily_life, func(v): main.daily_life = v, "Besuch")
	main.add_control("select", "mix", "Wer kommt", func(): return main.mix, func(v): main.mix = v, "Besuch",
			{"options": [["mixed", "Tiere und Menschen"], ["more_animals", "mehr Tiere"], ["more_people", "mehr Menschen"], ["animals", "nur Tiere"], ["people", "nur Menschen"]]})
	main.add_control("slider", "visit_rate", "Wie oft Besuch kommt", func(): return main.visit_rate, func(v): main.visit_rate = v, "Besuch", {"min": 0.25, "max": 4.0, "step": 0.25, "unit": "×"})
	main.add_control("slider", "max_visitors", "Höchstens gleichzeitig", func(): return main.max_visitors, func(v): main.max_visitors = int(v); main._perf_orig.erase("max_visitors"), "Besuch", {"min": 1, "max": 30, "step": 1, "expert": true})
	main.add_control("slider", "visitor_speed", "Tempo der Besucher", func(): return main.visitor_speed, func(v): main.visitor_speed = v, "Besuch", {"min": 0.25, "max": 2.5, "step": 0.05, "unit": "×", "expert": true})
	main.add_control("toggle", "flee_light", "Tiere flüchten nachts vor dem weissen Licht", func(): return main.flee_light, func(v): main.flee_light = v, "Besuch", ex)
	main.add_control("toggle", "flee_sound", "Tiere flüchten vor der Sirene", func(): return main.flee_sound, func(v): main.flee_sound = v, "Besuch", ex)
	main.add_control("toggle", "avoid_on", "Um Bäume, Häuser und Fahrzeuge herumgehen", func(): return main.avoid_on, func(v): main.avoid_on = v, "Besuch", ex)
	# 3D-4.x P1: the noise slider is also the one of «Kamera wie echt» (camphys.gd: noise from the gain of the sensor) - no second one
	main.add_control("slider", "lens_noise", "Rauschen (wie der Sensor: mehr Verstärkung = mehr Rauschen, am Tag sauber)", func(): return main.lens_noise, func(v): main.lens_noise = v, "Kamerabild", {"sub": "Wie echt", "min": 0, "max": 1, "step": 0.05, "expert": true})
	main.add_control("slider", "night_gain", "Nachtverstärkung der Kameras (höchstens)", func(): return main.night_gain, func(v): main.night_gain = v, "Kamerabild", {"min": 1, "max": 8, "step": 0.5, "unit": "×"})
	main.add_control("slider", "ir_range", "Reichweite des Infrarot-Lichts", func(): return main.ir_range, func(v): main.ir_range = v, "Kamerabild", {"min": 4, "max": 30, "step": 1, "unit": "m"})
	main.add_control("slider", "lens_vignette", "Dunkle Bildecken", func(): return main.lens_vignette, func(v): main.lens_vignette = v, "Kamerabild", {"min": 0, "max": 1, "step": 0.05, "expert": true})
	# 3D-3.94: the camera like a real one - and like the real one of MoveEye
	main.add_control("toggle", "real_fx", "Kamera wie echt (Camera Module 3 NoIR): Belichtung und Verstärkung mit echten Grenzen, Rauschen bei wenig Licht, Bewegungsunschärfe, NoIR-Farben, Blendung nachts", func(): return main.realism.fx_on, func(v): main.realism.fx_on = bool(v); main.realism.save(), "Kamerabild", {"sub": "Wie echt"})
	main.add_control("toggle", "real_look", "Echt-Abgleich: Helligkeit, Farbe, Schärfe und Rauschen an die echten Bilder von MoveEye angleichen", func(): return main.realism.real_on, func(v): main.realism.real_on = bool(v); main.realism.save(), "Kamerabild", {"sub": "Wie echt"})
	main.add_control("toggle", "real_servo", "Servos wie echt: MG90S-Tempo nach Spannung, Getriebespiel, Nachschwingen, Anlaufstrom", func(): return main.realism.servo_real, func(v): main.realism.servo_real = bool(v); main.realism.save(), "Kamerabild", {"sub": "Wie echt"})
	if main.servo != null:
		main.servo.add_controls()                           # «Servo-Mechanik»: head weight, gear play; Störung «Schwaches Servosignal»
	main.add_control("button", "real_reset", "Echt-Abgleich zurücksetzen", null, func(): main.realism.reset(), "Kamerabild", {"sub": "Wie echt", "expert": true})
	main.camphys.add_controls()                                 # 3D-4.x P1: «Bewegungsunschärfe», «NoIR-Farben»
	main.add_control("toggle", "colors_on", "Natürliche Farben und Materialien (Metall, Glas, Stoff, nass bei Regen) – wirkt nach dem Szenenwechsel", func(): return main.colors_on, func(v): main.colors_on = v; main.colors.on = v; main._settings_dirty = true, "Kamerabild", {"sub": "Wie echt"})
	main.add_control("toggle", "seasons_on", "Jahreszeiten: Gras und Laub nach dem Monat (Frühling, Sommer, Herbst, Winter)", func(): return main.seasons_on, func(v): main.seasons_on = v; main.colors.seasons_on = v; main.colors._month = -1; main._update_sky(); main._settings_dirty = true, "Szene", {"sub": "Zeit"})
	main.add_control("toggle", "show_laser", "Blickrichtung: roter Strahl aus dem Kopf und Bildränder am Boden (nur für dich sichtbar)", func(): return main.show_laser, func(v): main.show_laser = v; main._settings_dirty = true, "Kamerabild")
	main.add_control("toggle", "show_zones3d", "Zonen von MoveEye in der 3D-Ansicht (nur für dich sichtbar)", func(): return main.show_zones3d, func(v): main.show_zones3d = v; main._settings_dirty = true, "Kamerabild")
	main.add_control("toggle", "show_det3d", "Erkennung live in 3D: Rahmen von MoveEye über den Figuren (grün erkannt, rot Fehlalarm, orange übersehen)", func(): return main.show_det3d, func(v): main.show_det3d = v; main._settings_dirty = true, "Kamerabild")
	main.add_control("toggle", "lens_drops", "Regentropfen auf der Linse", func(): return main.lens_drops, func(v): main.lens_drops = v, "Kamerabild")
	main.add_control("toggle", "sound_on", "Geräusche der Welt ans Mikrofon von MoveEye", func(): return main.sound_on, func(v): main.sound_on = v, "Kamerabild", ex)
	main.add_control("toggle", "insects", "Insekten am Licht (nachts, lösen wie echt Bewegung aus)", func(): return main.insects_on, func(v): main.insects_on = v, "Kamerabild")
	for cd in [["glare", "Gegenlicht (tiefe Sonne in der Linse, Äste lassen sie flackern)"], ["drops", "Tropfen auf der Linse (auch ohne Regen)"],
			["web", "Spinnennetz vor der Kopfkamera (nachts im Licht hell)"], ["headlights", "Scheinwerfer: nachts fahren immer wieder Autos vorbei"],
			["shadows", "Wolkenschatten: schnelle, tiefe Schatten"], ["ir", "Infrarot-Licht immer an (auch ohne MoveEye)"],
			["fogged", "Beschlagene Linse (Tau am Morgen, milchiger Schleier)"], ["dirt", "Schmutz und Pollen auf der Linse"],
			["shake", "Kamera wackelt im Wind (Mast, Stange)"], ["net", "Schlechtes WLAN: das Bild ruckelt und bleibt hängen"]]:
		var key: String = cd[0]
		main.add_control("toggle", "cond_" + key, cd[1], func(): return main.cond[key], func(v): main.cond[key] = bool(v), "Kamerabild")
	main.simreal.add_controls()                                 # 3D-4.4: closer to the real device
	main.objplus.add_controls()                                 # 3D-4.x «Gegenstände»: lures
	main.inhalte.add_controls()                                 # F2: System → Grafik «Echte Oberflächen und Himmel»
	main.sicherung.add_controls()                               # System → Sicherung (sicherung.gd)
	main.umgebung.add_controls()                                # 3D-4.x: surroundings like real
	main.statisten.add_controls()                               # Paket «Statisten»: Besuch → Von selbst (wie viele, pro Spielmodus)
	main.menschen.add_controls()                                # P10: people like real (Besuch → Verhalten / Von selbst / Menschen schicken)
	main.tiere.add_controls()                                   # Paket «Tiere»: free dog, birds on the ground
	main.fahrzeuge.add_controls()                               # Paket «Fahrzeuge»
	main.licht.add_controls()                                   # «Licht & Nacht»: light pollution, place lamps, tents / windows
	main.jahreszeiten.add_controls()                            # «Jahreszeiten & Tageslauf»: season, snow, fog, leaves, campsite occupancy
	main.gelaende.add_controls()                                # 3D-4.x: hills and more plants (Szene)
	main.wetter.add_controls()                                  # real-wetter: rain strength, visibility, ground fog, snow, lens, lightning
	main.wind_fx.add_controls()                                 # F6: wind in the plants and tents (Wetter → Natur und Wind)
	preload("res://scripts/figur_paket.gd").add_controls(main)   # F5: figures from the pack (System → Grafik)
	main.szenen.add_controls()                                  # 3D-4.x: the visitors of the new scenes (szenenplus.gd)
	if main.statusled != null:
		main.statusled.add_controls()                           # Licht & Ton → Status-LED & Tasten (Fenster «Gerät»)
	if main.smalltv != null:
		main.smalltv.add_controls()                             # 3D-4.19: Sensoren → Zusatz-Bildschirm (virtueller SmallTV)
	main.weit.add_controls()                                    # 3D-4.17: the wide camera (card «Kamerabild», part «Weitwinkel-Kamera»)
	main.parcours.add_controls()                                # 3D-4.18: card «Testlauf», part «Verfolgungs-Parcours»
	main.einbruch.add_controls()                                # card «Testen», part «Einbruch-Abläufe» (einbruch.gd)
	main.zwilling.add_controls()
	main.add_control("toggle", "dev2_on", "Zweites MoveEye-Gerät in der Welt (eigene Adresse: Port des Simulators + 20, meist 8785)", func(): return main.dev2.on, func(v): main.dev2.set_on(v), "Mover")
	main.add_control("select", "dev2_place", "Platz des zweiten Geräts", func(): return main.dev2.place, func(v): main.dev2.set_place(str(v)), "Mover",
			{"options": [["opposite", "gegenüber (30 m)"], ["left", "links"], ["right", "rechts"], ["door", "bewacht Zelt / Tür"], ["bike", "bewacht das Velo"], ["car", "bewacht das Auto (Strasse)"]]})
	main.add_control("toggle", "mover_on", "Mover (Kettenfahrzeug) simulieren – fahren mit dem grünen Stick unten rechts, den Pfeiltasten oder dem zweiten Stick in MoveEye", func(): return main.mover_on, func(v): main.set_mover(v), "Mover")
	# 3D-3.61: «Patrouille»
	main.add_control("toggle", "patrol_on", "Patrouille: der Mover fährt MoveEye die Route ab", func(): return main.patrol != null and main.patrol.active, func(v): if main.patrol != null: main.patrol.set_active(bool(v)), "Mover")
	main.add_control("select", "patrol_mode", "Route", func(): return main.patrol.mode if main.patrol != null else "points", func(v): if main.patrol != null: main.patrol.mode = str(v); main.patrol._dirty = true, "Mover",
			{"options": [["points", "feste Punkte (mit der Maus gesetzt)"], ["area", "zufällig im Bereich"]]})
	main.add_control("button", "patrol_points", "Punkte setzen: in die Welt klicken (Rechtsklick = Punkt weg)", null, func(): main.patrol.edit = "points"; main.patrol.mode = "points", "Mover")
	main.add_control("button", "patrol_area", "Bereich aufziehen (mit gedrückter Maustaste)", null, func(): main.patrol.edit = "area", "Mover")
	main.add_control("button", "patrol_random", "Zufällige Route rund um MoveEye", null, func(): main.patrol.random_route(), "Mover")
	main.add_control("button", "patrol_clear", "Route löschen", null, func(): main.patrol.clear_route(), "Mover")
	main.add_control("slider", "patrol_speed", "Tempo der Patrouille", func(): return main.patrol.speed if main.patrol != null else 0.9, func(v): if main.patrol != null: main.patrol.speed = float(v), "Mover", {"min": 0.3, "max": 3.0, "step": 0.1, "unit": "m/s"})
	main.add_control("slider", "patrol_dwell", "An jedem Punkt umschauen", func(): return main.patrol.dwell if main.patrol != null else 5.0, func(v): if main.patrol != null: main.patrol.dwell = float(v), "Mover", {"min": 1.0, "max": 20.0, "step": 1.0, "unit": "s"})
	main.add_control("slider", "patrol_sweep", "Kopf schwenkt beim Fahren", func(): return main.patrol.sweep if main.patrol != null else 70.0, func(v): if main.patrol != null: main.patrol.sweep = float(v), "Mover", {"min": 0.0, "max": 160.0, "step": 10.0, "unit": "°"})
	main.add_control("toggle", "patrol_follow", "Kopf dreht zu Verdächtigem, der Mover fährt dann langsamer", func(): return main.patrol.follow if main.patrol != null else true, func(v): if main.patrol != null: main.patrol.follow = bool(v), "Mover")
	main.add_control("select", "patrol_judge", "Spiel «Patrouille»: wer erwischt", func(): return main.patrol_judge, func(v): main.patrol_judge = str(v), "Mover",
			{"options": [["mw", "die echte Erkennung von MoveEye"], ["sim", "der Wächter des Simulators (geht ohne Pi)"]]})
	main.add_control("button", "rover_place", "📍 Mover versetzen – danach in die Welt klicken (beim Erkunden: Strg + Klick)", null, func(): main.place_kind = "rover", "Mover")
	main.add_control("slider", "mast_h", "Höhe der Kamera (Stange; beim Erkunden Bild auf / ab oder Steuerkreuz)", func(): return main.mast_h, func(v): main.set_mast(float(v)), "Mover", {"min": main.MAST_MIN, "max": main.MAST_MAX, "step": 0.05, "unit": "m", "live": true})
	main.add_control("button", "pad_roles", "🎮 Controller zuteilen (mehrere Controller: Wächter, Schleicher, Mover)", null, func(): main.padmap.open_roles(), "Mover", {"sub": "Controller"})
	main.add_control("button", "pad_test", "🎮 Controller testen (zeigt Stick roh und nach der Drift-Korrektur)", null, func(): main._pad_test(), "Mover", {"sub": "Controller"})
	main.add_control("toggle", "pad_auto", "Stick-Drift selbst lernen (ein Stick, der 3 s genau gleich steht, gilt als Ruhelage)", func(): return main.pad_auto, func(v): main.pad_auto = v; main._settings_dirty = true, "Mover", {"sub": "Controller"})
	main.add_control("button", "pad_cal", "🎮 Controller kalibrieren (gegen Stick-Drift: Sticks 2 s nicht berühren)", null, func(): main.start_info = main.explore.calibrate() if main.explore != null else "", "Mover", {"sub": "Controller"})
	main.add_control("slider", "pad_dead", "Totzone der Sticks (höher = weniger Drift, aber träger)", func(): return main.pad_dead, func(v): main.pad_dead = v; main._settings_dirty = true, "Mover", {"min": 0.02, "max": 0.5, "step": 0.01, "sub": "Controller"})
	main.add_control("slider", "pad_sens", "Empfindlichkeit von Kopf und Ansicht (Stick)", func(): return main.pad_sens, func(v): main.pad_sens = float(v), "Mover", {"min": 0.3, "max": 2.5, "step": 0.1, "sub": "Controller"})
	main.add_control("toggle", "pad_inv_y", "Y umkehren (Stick hoch = Kopf / Blick runter)", func(): return main.pad_inv_y, func(v): main.pad_inv_y = bool(v), "Mover", {"sub": "Controller"})
	main.add_control("toggle", "pad_swap", "Sticks tauschen (links Mover / gehen, rechts Kopf / schauen)", func(): return main.pad_swap, func(v): main.pad_swap = bool(v), "Mover", {"sub": "Controller"})
	main.add_control("toggle", "pad_rumble", "Vibration (erwischt, Treffer, Alarm, die Kamera sieht dich)", func(): return main.pad_rumble, func(v): main.pad_rumble = bool(v), "Mover", {"sub": "Controller"})
	main.add_control("slider", "explore_speed", "Tempo beim Erkunden (Shift / A = schneller)", func(): return main.explore.speed if main.explore != null else 1.6, func(v): if main.explore != null: main.explore.speed = v, "Mover", {"min": 0.5, "max": 6.0, "step": 0.1, "unit": "m/s"})
	main.add_control("slider", "mover_max", "Höchstgeschwindigkeit des Movers", func(): return main.mover_max, func(v): main.mover_max = v, "Mover", {"min": 0.2, "max": 2.0, "step": 0.1, "unit": "m/s"})
	main.add_control("button", "mover_home", "Mover zurück an den Startplatz", null, func(): main.mover_home(), "Mover")
	main.add_control("toggle", "door", "Wohnwagentür offen", func(): return main.door_open, func(v): main.set_door(v), "Sensoren")
	main.add_control("toggle", "gas", "Gas / Rauch", func(): return main.gas_on, func(v): main.set_gas(v), "Sensoren")
	main.add_control("button", "pir", "PIR Zelt auslösen", null, func(): main.add_event("PIR Zelt", "pir"), "Sensoren")
	main.add_control("button", "bike", "Velo-Sensor auslösen (jemand rüttelt am Velo)", null, func(): main.add_event("Velo", "tag"), "Sensoren")
	main.simint.add_controls()                              # 30.10.2026: Lautsprecher, Störungen, Wärmebild (simint.gd)
	# 3.23 (Daniel 01.11.2026): ONE switch for the voice (narrator, demo, trailer) - like MoveEye (Licht & Ton → Lautsprecher)
	main.add_control("select", "stimme_modus", "Stimme (Erzähler, Vorführung, Trailer)", func(): return Stimme.modus(), func(v): Stimme.set_modus(str(v)),
			"Licht & Ton", {"sub": "Lautsprecher", "options": [["an", "an"], ["aus", "aus"], ["untertitel", "nur Untertitel"]]})
	# 3.23: «Bewegung reduzieren» and tour / Blinki in ONE place - like MoveEye (System → Gerät & Hilfe)
	main.add_control("select", "reduce_motion", "Bewegung reduzieren (Logo, Blinki, Wippen, Trailer sanfter)", func(): return main.reduce_motion,
			func(v): main.reduce_motion = str(v) if str(v) in ["auto", "an", "aus"] else "auto"; main.UI.motion_still = main.motion_reduced(), "System",
			{"sub": "Gerät & Hilfe", "options": [["auto", "wie das Betriebssystem"], ["an", "an: ruhige Bilder"], ["aus", "aus: alles bewegt sich"]]})
	main.add_control("toggle", "tour_auto", "Rundgang mit Blinki beim ersten Start von selbst", func(): return main.tour_auto, func(v): main.tour_auto = bool(v), "System", {"sub": "Gerät & Hilfe"})
	main.add_control("toggle", "blinki_on", "Blinki zeigen (die kleine Figur im Rundgang)", func(): return main.blinki_on, func(v): main.blinki_on = bool(v), "System", {"sub": "Gerät & Hilfe"})
	main.thermsensor.add_controls()                         # 3D-4.26: Kamerabild → Wärmebild (palette, sensor, tent, warm car)
	main.pir.add_controls()                                 # real-pir-ton: Sensoren → Bewegungsmelder (PIR)
	main.mikro.add_controls()                               # real-pir-ton: Licht & Ton → Mikrofon, Umgebungsgeräusche
	if main.klang != null:
		main.klang.add_controls()                           # Spielton: Licht & Ton → Spiel-Ton (Musik an/aus, vier Regler)
	main.simwerte.add_controls()                            # Simulator-Werte: Akku und Strom, Netz-Ausfall testen (power.gd)
	main.add_control("toggle", "rifle", "Gewehr (unblutig, nur Tiere)", func(): return main.rifle_on, func(v): main.rifle_on = v, "Wildbeobachtung")
	main.add_control("button", "shoot_head", "Schuss aus der Kopfkamera", null, func(): main.shoot_head(), "Wildbeobachtung")
	main.add_control("button", "score0", "Punkte auf 0", null, func(): main.reset_score(), "Wildbeobachtung")
	main.zimmertiere.add_controls()                         # Erlebniswelt «mehr Tiere drinnen»: Wildtier → Hamster, Vogel, Spinne
	main.add_control("toggle", "news_popup", "Nach einem Update kurz zeigen, was neu ist (und was als Nächstes kommt)", func(): return main.news_popup, func(v): main.news_popup = v; main._settings_dirty = true, "Updates")
	main.add_control("button", "news_show", "Was ist neu?", null, func(): main.news.show_news(), "Updates")
	# «Links zu Neuerungen» (wie MoveEye, nur im Entwickler-Bereich): auto = Projektschalter projekt_veroeffentlicht (ui_gemeinsam.json)
	main.add_control("select", "news_links", "Links zu Neuerungen", func(): return main.news_links,
			func(v): main.news_links = str(v) if str(v) in ["auto", "on", "off"] else "auto"; main._settings_dirty = true, "Entwickler",
			{"expert": true, "devwin": true, "options": [["auto", "Standard (an, bis das Projekt veröffentlicht ist)"], ["on", "an"], ["off", "aus"]]})
	# 3D-3.90: one choice instead of two switches (the old ids stay for MoveEye, hidden in the window)
	main.add_control("select", "update_mode", "Neue Versionen", func(): return "dev" if main.dev_updates else ("auto" if main.auto_update else "off"),
			func(v): main.dev_updates = str(v) == "dev"; main.set_auto_update(str(v) != "off"), "Updates",
			{"options": [["off", "nur von Hand (Knopf oben)"], ["auto", "automatisch installieren"], ["dev", "Entwicklungsphase: jede Minute, sofort"]]})
	# 3D-4.21: group «Entwickler» (like MoveEye, only «Experte»): test bench and faults - the same buttons as in «Testen»
	# Paket «Entwickler zusammenlegen»: in the panel only «Entwickler-Fenster öffnen»; the rest («devwin») in the window, tab «Schalter»
	main.add_control("button", "dev_open", "Entwickler-Fenster öffnen", null, func(): main.dev_window("schalter"), "Entwickler", {"expert": true})
	main.add_control("button", "pruef_open", "Prüfstand öffnen", null, func(): main.pruef.open(not main.pruef.visible), "Entwickler", {"expert": true, "devwin": true})
	main.add_control("button", "simint_open", "Störungen testen", null, func(): main._open_stoer(), "Entwickler", {"expert": true, "devwin": true})
	preload("res://scripts/spieltest.gd").add_controls(main)   # Spieltest-Assistent + «Spieltest-Meldungen» (wie MoveEye Entwickler)
	preload("res://scripts/maggie_vorfuehrung.gd").add_controls(main)   # Vorführmodus «Maggie» (Entwickler, Reiter «Vorführung»)
	preload("res://scripts/trailer.gd").add_controls(main)   # Trailer der Geschichten (Entwickler; dazu oben im Entwickler-Fenster)
	main.add_control("toggle", "dev_updates", "Entwicklungsphase: jede Minute nach neuen Versionen schauen und sofort installieren", func(): return main.dev_updates, func(v): main.dev_updates = v; main._settings_dirty = true, "Updates", {"expert": true, "hide": true})
	main.add_control("toggle", "auto_update", "Neue Versionen automatisch installieren", func(): return main.auto_update, func(v): main.set_auto_update(v), "Updates", {"expert": true, "hide": true})
	main.add_control("button", "update_now", "Jetzt nach Updates suchen und installieren", null, func(): main.run_update(true, false), "Updates", {"expert": true, "hide": true})
	main.add_control("select", "testrun_plan", "Welcher Testlauf", func(): return main.testrun.plan, func(v): main.testrun.plan = v, "Testlauf",
			{"options": main.testrun.plan_options()})
	main.add_control("button", "testrun_start", "Testlauf starten (MoveEye muss verbunden sein)", null, func(): main.testrun.start(), "Testlauf")
	main.add_control("button", "testrun_stop", "Testlauf abbrechen", null, func(): main.testrun.stop(false), "Testlauf")
	main.add_control("button", "rec_start", "● Aufnahme starten (wer wo geht, Zeit, Wetter – höchstens 5 Minuten)", null, func(): main.recorder.start_rec(), "Testlauf")
	main.add_control("button", "rec_stop", "■ Aufnahme beenden und speichern", null, func(): main.recorder.stop_rec(), "Testlauf")
	main.add_control("select", "rec_pick", "Aufnahme", func(): return main.recorder.pick, func(v): main.recorder.pick = str(v), "Testlauf", {"options": main.recorder.options()})
	main.add_control("button", "rec_play", "▶ Aufnahme abspielen (genau gleich wie aufgenommen)", null, func(): main.recorder.play(), "Testlauf")
	main.add_control("toggle", "rec_loop", "Immer wieder abspielen", func(): return main.recorder.loop, func(v): main.recorder.loop = v, "Testlauf")
	main.add_control("button", "rec_stopplay", "Wiedergabe beenden", null, func(): main.recorder.stop_play(), "Testlauf")
	main.add_control("button", "testrun_open", "Letzten Bericht öffnen", null, func(): main.testrun.open_report(), "Testlauf")
	main.add_control("button", "tv_mode", "📺 TV-Modus für den Spielabend (Taste T, ganzer Bildschirm)", null, func(): main.tv.set_on(not main.tv.on), "Spiel")
	main.add_control("button", "game_wizard", "🎮 Assistent öffnen: Spiel einrichten und starten", null, func(): main.gamewiz.open_wiz(), "Spiel")
	# 3D-4.39: the Bergtal adventure starts from the game wizard (quick start card «Bergtal-Abenteuer», gamewiz.gd)
	main.add_control("toggle", "game_open", "Spiel öffnen (Handys können mitspielen)", func(): return main.game.open, func(v): main.game.set_open(v), "Spiel")
	main.add_control("button", "game_start", "▶ Start", null, func(): main._game_card_start(), "Spiel")
	main.add_control("button", "game_stop", "⏹ Stopp", null, func(): main._game_card_stop(), "Spiel")
	main.entdecken.register_controls()                       # Erlebniswelt 20–23: Spiel → Entdecken (Buch, Foto, Blinki-Hinweise)
	main.add_control("button", "disc_seek", "🙈 Verstecken mit MoveEye", null, func(): main._fp_seek(), "Spiel")   # Erlebniswelt 12
	main.controls[-1]["only"] = func(): return main.scene == "ferienpark"   # 3D-4.30: only in the Ferienpark (like «Standort im Ferienpark»)
	preload("res://scripts/ferienpark_leben.gd").add_controls(main)   # Ferienpark-Leben: 3 tasks (Spiel → Entdecken) + «Leben nach Uhrzeit» (Besuch → Von selbst)
	main.add_control("slider", "game_minutes", "Dauer einer Runde", func(): return main.game_minutes, func(v): main.game_minutes = v, "Spiel", {"min": 1, "max": 15, "step": 1, "unit": "min"})
	main.add_control("select", "game_mode", "Spielart", func(): return main.game_mode, func(v): main.game_mode = v, "Spiel",
			{"options": [["mw", "Gegen MoveEye (echte Erkennung)"], ["guard", "Wächter (ein Spieler oder der Bot-Wächter)"], ["seek", "Verstecken mit dem Mover (Fänger sieht nur die Kamera)"], ["free", "Zonen-Check – ohne Erwischen (zum Testen der Erkennung)"], ["jaeger", "Fehlalarm-Jäger – Tiere und Dinge täuschen MoveEye (nur mit MoveEye)"], ["camera", "ältere: Alle gegen die Kamera"], ["mwhand", "ältere: Team gegen MoveEye (Wächter steuern MoveEye)"], ["patrol", "ältere: Patrouille mit dem Mover"]]})
	# Balance 30.10.2026: two levels, ONE text (gamerules.gd LEVEL_TXT / GLEVEL_TXT - the same as in the wizard)
	main.add_control("select", "game_level", "Schleicher-Stufe (wie schnell die Kamera / MoveEye dich bemerkt)", func(): return main.game_level, func(v): main.game_level = v, "Spiel",
			{"options": preload("res://scripts/gamerules.gd").level_options()})
	main.add_control("select", "game_glevel", "Wächter-Stufe (Treffer-Kreis und Energie)", func(): return main.game.rules.guard_level, func(v): main.game.rules.cfg_set({"game_glevel": str(v)}), "Spiel",
			{"options": preload("res://scripts/gamerules.gd").glevel_options()})
	main.add_control("toggle", "game_real", preload("res://scripts/gamerules.gd").REAL_TXT, func(): return main.game.rules.real_hw, func(v): main.game.rules.cfg_set({"game_real": bool(v)}), "Spiel")
	main.add_control("select", "game_lives", "Leben", func(): return str(main.game_lives), func(v): main.game_lives = int(v), "Spiel",
			{"options": [["0", "unbegrenzt"], ["3", "3 Leben"], ["1", "1 Leben"]]})
	main.add_control("slider", "game_items", "Kristalle zum Sammeln", func(): return main.game_items, func(v): main.game_items = int(v), "Spiel", {"min": 0, "max": 6, "step": 1})
	# 3D-4.x (Aufräumen): no toggle «Zwei Teams» any more - teams only with the goal «Fahne erobern» (game.sync_teams)
	main.add_control("toggle", "game_rescue", "Befreien: Erwischte kommen in die Zelle, ein Teamkollege befreit sie", func(): return main.game_rescue, func(v): main.game_rescue = v, "Spiel")
	main.add_control("toggle", "game_teamgoal", "Team-Ziel: das Ziel öffnet erst, wenn alle Kristalle gefunden sind", func(): return main.game_teamgoal, func(v): main.game_teamgoal = v, "Spiel", ex)
	main.add_control("select", "game_goal", "Spielziel", func(): return main.game_goal, func(v): main.game_goal = v, "Spiel",
			{"options": [["reach", "Zum Ziel schleichen"], ["return", "Beute holen und zurückbringen"], ["flag", "Fahne erobern (zwei Teams)"], ["sprint", "Sprint: 90 s, fester Parcours"], ["theft", "Diebstahl: Velo oder Kühlbox zum Ausgang tragen"],
				["mission", "Mission mit Gegenständen (Portemonnaie, Früchte, Paket)"], ["sweat", "Bring MoveEye ins Schwitzen"]]})
	main.add_control("toggle", "game_stones", "Steine werfen zum Ablenken", func(): return main.game_stones, func(v): main.game_stones = v, "Spiel")
	main.add_control("toggle", "game_powers", "Power-ups: Unsichtbar-Trank (lila) und Turbo (gelb)", func(): return main.game_powers, func(v): main.game_powers = v, "Spiel")
	main.add_control("toggle", "game_photos", "Erwischt-Fotos (Bild der Kamera beim Erwischen, Galerie am Schluss)", func(): return main.game_photos, func(v): main.game_photos = v, "Spiel")
	# 3D-3.52: the hit sequence (each on its own) and what the game teaches MoveEye
	main.add_control("toggle", "game_fx_laser", "Treffer: roter Laser vom Kamerakopf (Handy: Fadenkreuz)", func(): return main.game_fx_laser, func(v): main.game_fx_laser = v, "Spiel")
	main.add_control("toggle", "game_fx_paint", "Treffer: Farbklecks (Handy: Klecks auf dem Bildschirm)", func(): return main.game_fx_paint, func(v): main.game_fx_paint = v, "Spiel")
	main.add_control("toggle", "game_fx_flash", "Treffer: Blitz wie ein Radarfoto (Handy: weisser Blitz)", func(): return main.game_fx_flash, func(v): main.game_fx_flash = v, "Spiel")
	main.add_control("toggle", "game_tap", "Jäger an MoveEye zielt durch Antippen im Livebild", func(): return main.game_tap, func(v): main.game_tap = v, "Spiel")
	main.add_control("toggle", "game_learn_miss", "Erkennung lernen: Bilder von Spielern, die MoveEye nicht gemeldet hat", func(): return main.game_learn_miss, func(v): main.game_learn_miss = v, "Spiel")
	main.add_control("toggle", "game_learn_report", "Erkennung lernen: Spielbericht (wie schnell gemeldet, Abstand, Haltung, Licht)", func(): return main.game_learn_report, func(v): main.game_learn_report = v, "Spiel")
	main.add_control("toggle", "game_learn_paths", "Erkennung lernen: unerkannte Schleichwege als Testlauf speichern", func(): return main.game_learn_paths, func(v): main.game_learn_paths = v, "Spiel")
	main.add_control("toggle", "game_blind_bonus", "Bonus für blinde Flecken (+20 Punkte pro Sekunde sichtbar, aber nicht gemeldet)", func(): return main.game_blind_bonus, func(v): main.game_blind_bonus = v, "Spiel")
	main.add_control("button", "game_report_send", "📊 Spielberichte senden (GitHub-Schlüssel vom Prüfstand, sonst Schreibtisch)", null, func(): main._game_report_send(), "Spiel")
	main.add_control("slider", "game_hides", "Verstecke (Büsche: 8 s unsichtbar)", func(): return main.game_hides, func(v): main.game_hides = int(v), "Spiel", {"min": 0, "max": 6, "step": 1})
	main.add_control("toggle", "game_decoy", "Lockvogel erlaubt (lockt die Kamera weg, Teampunkte)", func(): return main.game_decoy, func(v): main.game_decoy = v, "Spiel")
	main.add_control("toggle", "game_night", "Nacht-Runde mit Taschenlampen", func(): return main.game_night, func(v): main.game_night = v, "Spiel")
	main.add_control("toggle", "game_events", "Zufallsereignisse (Gewitter, Hund, Auto)", func(): return main.game_events, func(v): main.game_events = v, "Spiel")
	main.add_control("slider", "game_checkpoints", "Checkpoints (+150 Punkte)", func(): return main.game_checkpoints, func(v): main.game_checkpoints = int(v), "Spiel", {"min": 0, "max": 3, "step": 1})
	main.add_control("select", "game_bots", "Computer-Spieler (Bots), die mitschleichen", func(): return str(main.game_bots), func(v): main.game_bots = int(v); main.game.set_bots(main.game_bots), "Spiel",
			{"options": [["0", "keine"], ["1", "1 Bot"], ["2", "2 Bots"], ["3", "3 Bots"]]})
	main.add_control("toggle", "game_tutorial", "Übungsrunde: Schritt für Schritt erklärt, niemand wird erwischt", func(): return main.game_tutorial, func(v): main.game_tutorial = v, "Spiel")
	main.add_control("toggle", "game_daily", "Tagesaufgabe: heute für alle dieselbe Szene, dasselbe Ziel und dieselben Startpunkte", func(): return main.game_daily, func(v): main.game_daily = v, "Spiel")
	main.add_control("toggle", "game_ghost", "Geisterläufer: der eigene beste Weg läuft als Geist mit (nur die Spieler sehen ihn)", func(): return main.game_ghost, func(v): main.game_ghost = v, "Spiel")
	main.add_control("toggle", "game_heart", "Herzschlag, wenn die Kamera dich gleich sieht (Handy vibriert)", func(): return main.game_heart, func(v): main.game_heart = v, "Spiel")
	main.add_control("toggle", "game_botguard", "Bot-Wächter, wenn niemand Wächter sein will (Spielart «Wächter»)", func(): return main.game_botguard, func(v): main.game_botguard = v, "Spiel")
	main.add_control("toggle", "game_kiguard", "🤖 MoveEye als KI-Wächter (Runden mit Wächter: MoveEye bewacht selbst – echte Erkennung, Kopf folgt, Auslöser-Autopilot; braucht MoveEye)",
			func(): return main.game_kiguard, func(v): main.game_kiguard = bool(v), "Spiel")
	main.add_control("button", "game_kig_reset", "Liste «gegen die KI» zurücksetzen", null, func(): if main.game != null: main.game.kig.command({"op": "reset"}), "Spiel")
	main.add_control("button", "game_local", "Hier am PC mitspielen (Tastatur, Maus oder Controller)", null, func(): main.localplay.start("runner"), "Spiel")
	main.add_control("button", "game_local_guard", "Hier am PC Wächter sein (Kopf drehen, «Erwischt!»)", null, func(): main.localplay.start("guard"), "Spiel")
	main.add_control("toggle", "game_tasks", "Aufgabe für jede Runde (z. B. nur kriechend ins Ziel, Bonus)", func(): return main.game_tasks, func(v): main.game_tasks = v, "Spiel")
	main.add_control("toggle", "game_autohandicap", "Handicap für den Ersten der Rangliste", func(): return main.game_autohandicap, func(v): main.game_autohandicap = v, "Spiel")
	main.add_control("button", "game_board_reset", "Rangliste des Abends zurücksetzen", null, func(): main.game.board_reset(), "Spiel")
	main.add_control("toggle", "game_spectate", "Zuschauer-Kamera: fliegt bei Spielstart selbst übers Spielfeld", func(): return main.game_spectate, func(v): main.game_spectate = v, "Spiel")
	main.add_control("toggle", "spectate_now", "Zuschauer-Kamera jetzt", func(): return main.spectate, func(v): main.spectate_start() if v else main.spectate_stop(), "Spiel")
	main.add_control("toggle", "game_noise", "Mikrofon hört laute Schritte", func(): return main.game_noise, func(v): main.game_noise = v, "Spiel", ex)
	main.add_control("toggle", "game_cones", "Sichtfeld der Kameras zeigen (für Anfänger)", func(): return main.game_cones, func(v): main.game_cones = v, "Spiel")
	main.add_control("toggle", "game_random", "Start und Ziel zufällig", func(): return main.game_random, func(v): main.game_random = v, "Spiel", ex)
	main.add_control("select", "game_quality", "Bild auf dem Handy", func(): return main.game_quality, func(v): main.game_quality = v, "Spiel",
			{"options": [["small", "klein (schnell)"], ["mid", "mittel"], ["big", "gross (braucht mehr Leistung)"]], "expert": true})
	main.add_control("slider", "game_max", "Läufer höchstens (mehr Spieler schauen zu)", func(): return main.game_max, func(v): main.game_max = int(v), "Spiel",
			{"min": 2, "max": 12, "step": 1, "tip": "Jeder Läufer ist ein eigenes 3D-Bild auf dem PC und ein eigenes Video übers Netz. Laptop: etwa 4, PC mit Grafikkarte: 6–8. Ab 5 Läufern werden die Bilder automatisch kleiner."})
	main.add_control("toggle", "game_guard", "Ohne MoveEye bewacht der Kopf selbst", func(): return main.game_guard, func(v): main.game_guard = v, "Spiel", ex)
	for tl in [["light", "💡 Licht"], ["siren", "📢 Sirene"], ["scan", "📡 Scan"], ["zoom", "🔍 Zoom"]]:   # 3D-4.x: tools of the guards at MoveEye (gametools.gd, part 543)
		var tid: String = tl[0]
		main.add_control("button", "game_tool_" + tid, "Wächter an MoveEye: " + tl[1], null, func(): main.game.tools.use(null, tid, "MoveEye"), "Spiel")
	main.add_control("toggle", "autostart", "Mit dem PC starten (sendet gleich an MoveEye)", func(): return main.autostart_on, func(v): main.set_autostart(v), "Start mit dem PC")
	main.add_control("toggle", "autostart_min", "Dabei klein (nur das Kästchen in der Ecke)", func(): return main.autostart_min, func(v): main.autostart_min = v, "Start mit dem PC")
	main.add_control("toggle", "autostart_mwpc", "Dabei auch MoveEye auf diesem PC starten (ohne Pi)", func(): return main.autostart_mwpc, func(v): main.autostart_mwpc = v, "Start mit dem PC")
	if OS.get_name() == "Windows":
		main.add_control("toggle", "autostart_lock", "Danach den Bildschirm sperren", func(): return main.autostart_lock, func(v): main.autostart_lock = v, "Start mit dem PC")
		main.add_control("button", "autologon", "Ohne Anmelden: automatische Anmeldung von Windows einrichten …", null, func(): main.setup_autologon(), "Start mit dem PC", {"expert": true})
	# 3D-3.69: what the «Kinder» mode shows (only the adults can change it - in the Kinder mode these settings are hidden)
	main.add_control("toggle", "kids_scary", "Kinder-Modus: Wildschwein, Wolf und Luchs", func(): return main.kids_scary, func(v): main.kids_scary = v, "Kinder-Modus")
	main.add_control("toggle", "kids_thief", "Kinder-Modus: Schleicher (Dieb) und Einbrecher", func(): return main.kids_thief, func(v): main.kids_thief = v, "Kinder-Modus")
	main.add_control("toggle", "kids_laser", "Kinder-Modus: Laser-Treffer im Spiel", func(): return main.kids_laser, func(v): main.kids_laser = v, "Kinder-Modus")
	main.add_control("toggle", "kids_sound", "Kinder-Modus: Töne bei den Knöpfen", func(): return main.kids_sound, func(v): main.kids_sound = v, "Kinder-Modus")
	main.add_control("toggle", "kids_ask", "Kinder-Modus: zum Verlassen eine Rechenaufgabe stellen (aus = ein Klick auf «Erwachsene» genügt)", func(): return main.kids_ask, func(v): main.kids_ask = bool(v), "Kinder-Modus")
	# F1 (Konzept-Wunsch): EINE Wahl «Grafik-Modus» Automatisch / Lite / Normal / Hoch; die Feinheiten (Grafik-Details,
	# «Automatisch leichter», Tiefenschärfe) nur unter «Experte»
	main.add_control("select", "grafik_mode", "Grafik-Modus", func(): return main.grafik_mode, func(v): main.set_grafik_mode(str(v)), "Grafik",
			{"options": Quality.MODES, "tip": "Hoch: Licht prallt von Flächen ab, Dunst, weiche Schatten, Spiegelungen auf Wasser und nassen Flächen, bessere Oberflächen. Braucht eine gute Grafikkarte (Vulkan); der Simulator startet dafür einmal neu."})
	main.add_control("select", "quality", "Grafik-Details (Schatten, Leuchten, Wolken)", func(): return main.quality, func(v): main._set_quality(v), "Grafik",
			{"expert": true, "options": [["simple", "einfach (schnell)"], ["medium", "mittel"], ["nice", "schön (Schatten, Leuchten, Wolken)"],
						 ["ultra", "ultra (für starke Grafikkarten; mit Vulkan noch mehr Effekte)"]]})
	main.add_control("toggle", "grafik_dof", "Hoch: Tiefenschärfe in der freien Ansicht (die Kamerabilder für MoveEye bleiben scharf)", func(): return main.hoch.dof_free, func(v): main.hoch.set_dof(bool(v)), "Grafik", ex)
	main.add_control("toggle", "cam_wippen", "Ansicht wippt beim Gehen (Spielfigur)", func(): return main.cam_wippen, func(v): main.cam_wippen = bool(v), "Grafik",
			{"expert": true, "tip": "Die Ansicht hinter der Spielfigur geht mit den Schritten leicht auf und ab. Aus, wenn dir davon schwindlig wird. Nur bei Grafik «schön» oder «ultra»."})
	main.add_control("toggle", "foto_tex", "Foto-Texturen im Bergtal", func(): return main.foto_tex, func(v): main.set_foto_tex(bool(v)), "Grafik",
			{"expert": true, "tip": "Wiese, Fels, Geröll, Alpenrosen, Wege und Seegrund aus echten Fotos (Daniel Bärschi). Aus = die gezeichneten Farben wie früher. In Lite immer aus."})
	main.add_control("slider", "view_scale", "Schärfe der Ansicht im Fenster (weniger = schneller; die Bilder für MoveEye bleiben scharf)", func(): return main.view_scale, func(v): main.set_view_scale(float(v)), "Grafik", {"min": 0.4, "max": 1.0, "step": 0.05, "unit": "×"})
	main.add_control("select", "win_fps", "Bilder pro Sekunde im Fenster", func(): return str(main.win_fps), func(v): main.win_fps = int(v); main._perf_orig.erase("win_fps"); main._settings_dirty = true, "Grafik",
			{"options": [["0", "so viele wie möglich"], ["60", "60"], ["30", "30 (spart Strom)"], ["20", "20 (schwacher PC)"]]})
	main.add_control("toggle", "auto_perf", "Automatisch leichter, wenn der PC zu langsam ist", func(): return main.auto_perf, func(v): main.auto_perf = v; main._slow_n = 0, "Grafik", ex)
	main.add_control("toggle", "eco_idle", "Simulator ruht, wenn niemand zuschaut (rechnet nur, wenn das Fenster offen oder MoveEye verbunden ist)", func(): return main.eco_idle, func(v): main.eco_idle = v, "Grafik", ex)
	main.add_control("toggle", "meadow", "Gras und Blumen auf der Wiese", func(): return main.meadow_on, func(v): main.set_meadow(v), "Grafik", ex)
	main.add_control("toggle", "map_on", "Übersichtskarte oben links (M)", func(): return main.map_on, func(v): main.set_map(v), "Grafik")
	main.add_control("toggle", "live_on", "Livebild unter der Karte (L)", func(): return main.live_on, func(v): main.set_live(v), "Grafik")
	main.add_control("select", "live_cam", "Livebild: welche Kamera", func(): return str(main.live_cam), func(v): main.set_live(main.live_on, int(v)), "Grafik",
			{"options": [["0", "Kamera 1 (Kopf)"], ["1", "Kamera 2"], ["2", "Wärmebild"]]})
	main.add_control("slider", "live_size", "Livebild: Breite", func(): return main.live_size, func(v): main.set_live(main.live_on, -1, float(v)), "Grafik",
			{"min": 160, "max": 520, "step": 20, "unit": "px"})
	# Menüs A, Punkt 5: was in «Testen → Mehr: Aufstellen, Erkunden, Handy-Simulator» - now where it belongs (planner = tile
	# «Aufstellen», Erkunden = bar, feedback = «Mehr»); the phone view as a normal control next to map and live picture
	main.add_control("button", "phone_sim", "Handy- / Tablet-Simulator (P)", null, func(): main._toggle_phone(), "Grafik", {"expert": true})
	main._menu_merge()


func _cget(id: String):
	for c in main.controls:
		if c.id == id and c["get"] != null:
			return c["get"].call()
	return null


func _cset(id: String, v) -> void:
	for c in main.controls:
		if c.id == id and c["set"] != null:
			c["set"].call(v)
			return


func _menu_merge() -> void:
	"""Menüs A, Punkt 4 (Daniel 31.10.2026): one control instead of 2–4 with the same name. It only reads and sets the old
	controls (ALIAS_IDS: they stay for /control, the test runs, the Prüfstand and the saved settings)"""
	main.add_control("select", "linse_tropfen", "Tropfen auf der Linse",
			func():
				if bool(main._cget("cond_drops")):
					return "immer"
				if not bool(main._cget("lens_drops")):
					return "aus"
				return "echt" if bool(main._cget("w_lens")) else "regen",
			func(v):
				main._cset("cond_drops", str(v) == "immer")
				main._cset("lens_drops", str(v) != "aus")
				if str(v) in ["regen", "echt"]:
					main._cset("w_lens", str(v) == "echt"),
			"Kamerabild", {"options": [["aus", "aus"], ["regen", "bei Regen (einfach)"],
					["echt", "bei Regen wie echt (Tropfen haften und rinnen, Linse beschlägt)"], ["immer", "immer, auch ohne Regen"]]})
	main.add_control("select", "scheinwerfer", "Scheinwerfer in der Nacht",
			func():
				var a = bool(main._cget("cond_headlights"))
				var b = bool(main._cget("fa_sweep"))
				return "beides" if a and b else ("autos" if a else ("kegel" if b else "aus")),
			func(v):
				main._cset("cond_headlights", str(v) in ["autos", "beides"])
				main._cset("fa_sweep", str(v) in ["kegel", "beides"]),
			"Kamerabild", {"options": [["aus", "aus"], ["kegel", "ab und zu streift ein Lichtkegel über Wände und Zelt"],
					["autos", "immer wieder fahren Autos vorbei"], ["beides", "beides"]]})
	var months := [["today", "wie heute (echtes Datum)"]]
	var mn := ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
	var sn := ["Winter", "Winter", "Frühling", "Frühling", "Frühling", "Sommer", "Sommer", "Sommer", "Herbst", "Herbst", "Herbst", "Winter"]
	for i in range(12):
		months.append([str(i + 1), "%s (%s)" % [mn[i], sn[i]]])
	months.append(["ohne", "ohne Jahreszeit (Pflanzen immer wie im Sommer, Sonne wie heute)"])
	main.add_control("select", "jahreszeit", "Jahreszeit (Sonne, Tageslänge, Pflanzen, Belegung)",
			func(): return "ohne" if not main.seasons_on else str(main.season),
			func(v):
				if str(v) == "ohne":
					main._cset("season", "today")
					main._cset("seasons_on", false)
					return
				if not main.seasons_on:
					main._cset("seasons_on", true)
				if main.jahreszeiten != null:
					main.jahreszeiten.mode = "auto"                 # the month decides (jz_mode would set the month again at the start)
					main.jahreszeiten.save()
				main._cset("season", str(v)),
			"Szene", {"options": months})
	main.add_control("select", "tagesablauf", "Tagesablauf (wer wann kommt)",
			func():
				var a = bool(main._cget("daily_life"))
				var b = bool(main._cget("m_plan"))
				return "beides" if a and b else ("zeit" if a else ("platz" if b else "aus")),
			func(v):
				main._cset("daily_life", str(v) in ["zeit", "beides"])
				main._cset("m_plan", str(v) in ["platz", "beides"]),
			"Besuch", {"options": [["aus", "aus (Besuch kommt zufällig)"], ["zeit", "jeder kommt zu seiner Zeit (Fuchs nachts, Reh in der Dämmerung, Briefträger um 10 Uhr)"],
					["beides", "dazu der Alltag auf dem Campingplatz (morgens WC und Dusche, abends draussen sitzen)"],
					["platz", "nur der Alltag auf dem Campingplatz"]]})


func control_set(id: String, v) -> Dictionary:
	"""one setting by its id (the game wizard; like the CONTROL action «set»)"""
	for c in main.controls:
		if c.id == id and c["set"] != null:
			match c.type:
				"slider":
					v = clamp(float(v), float(c.extra.get("min", -1e9)), float(c.extra.get("max", 1e9)))
				"toggle":
					v = bool(v)
				"button":
					c["set"].call()
					return {"ok": true}
				_:
					v = str(v)
			c["set"].call(v)
			main._settings_dirty = true
			main._sync_ui()
			return {"ok": true}
	return {"ok": false}


func _load_settings() -> void:
	"""the settings of the last time (simulator_settings.json in the user folder)"""
	if not FileAccess.file_exists(main.SETTINGS_FILE):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(main.SETTINGS_FILE))
	if typeof(d) != TYPE_DICTIONARY:
		return
	main.quality_set = d.has("quality")
	for k in main.KEEP:
		if d.has(k):
			var v = d[k]
			var old = main.get(k)
			if typeof(old) == TYPE_INT:
				v = int(v)
			elif typeof(old) == TYPE_BOOL:
				v = bool(v)
			elif typeof(old) == TYPE_FLOAT:
				v = float(v)
			else:
				v = str(v)
			main.set(k, v)
	if not bool(d.get("ui_icons_pick", false)) and str(d.get("ui_icons", "")) != "color":
		main.ui_icons = "color"                                # 3.23: files up to 3.22 saved the old standard «schlicht» - now «farbig»
	if typeof(d.get("fold_mem")) == TYPE_DICTIONARY:      # nurgruppen: the own open / closed state of the cards and parts
		main.fold_mem = preload("res://scripts/ui_gemeinsam.gd").migrate_fold(d["fold_mem"])   # P1: «Sensoren» -> «Zusatzgeräte» …
	main.grafik_mode = Quality.mode_id(main.grafik_mode)            # 3D-4.25: unknown / older names -> «Automatisch»
	if main.game_mode == "teamguard":                          # Balance 30.10.2026: «Team gegen Team» is gone
		main.game_mode = "guard"
	if d.has("hour_now") and not "--hour" in OS.get_cmdline_user_args() and not "--hour" in OS.get_cmdline_args() and not main.real_time:
		# 3D-3.76: the time as it was set; a short break (update, restart) - the clock went on meanwhile, like outside
		main.speed = clampf(float(d.get("speed_now", 1.0)), 1.0, 120.0)
		var gap: float = Time.get_unix_time_from_system() - float(d.get("hour_at", 0))
		main.set_hour(float(d["hour_now"]) + (gap * main.speed / 3600.0 if gap >= 0.0 and gap < 1800.0 else 0.0))


func _save_settings() -> void:
	var d := {}
	for k in main.KEEP:
		d[k] = main.get(k)
	for k in main._perf_orig:                                   # 3D-3.88: «automatisch leichter» is not saved
		d[k] = main._perf_orig[k]
	if main._grafik_keep != "":
		d["grafik_mode"] = main._grafik_keep
	d["hour_now"] = snappedf(main.hour(), 0.001)               # 3D-3.76: the time of the scene stays after a restart
	d["hour_at"] = int(Time.get_unix_time_from_system())
	d["speed_now"] = main.speed
	d["fold_mem"] = main.fold_mem                              # nurgruppen
	if main.mehr != null:
		d.merge(main.mehr.keep(), true)                        # 3D-4.2x: look (Hell / Rotlicht / Dunkel) and the tour
	main._hour_saved_t = main.now()
	var f = FileAccess.open(main.SETTINGS_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d, " "))
	main._settings_dirty = false


func _ui_control(parent: Control, c: Dictionary) -> void:
	match c.type:
		"button":
			var b := Button.new()
			b.text = main.UI.short(main.no_emoji(c.label))[0]     # 3D-3.98: the window has no emoji font (the page of MoveEye keeps them); 3D-4.21: short, the rest in the tooltip
			b.pressed.connect(func(): c["set"].call())
			var tk: String = {"dogwalk": "dog", "herd": "deer", "feed": "deer", "garden_person": "person", "bench": "person", "thief": "person"}.get(
					str(c.id), str(c.id).trim_prefix("spawn_"))
			if not tk in main.VISITOR_KINDS_ALL and main.Sym.lead(c.label)[0] != "":
				b.icon = main.Sym.tex(main.Sym.lead(c.label)[0])      # 3D-4.22: the drawn symbol instead of the emoji
			if tk in main.VISITOR_KINDS_ALL:                    # the small picture of the visitor on its button (3D-3.38)
				b.add_theme_constant_override("icon_max_width", 26)
				b.alignment = HORIZONTAL_ALIGNMENT_LEFT
				main.thumb_btns.append([b, tk])
				if main.thumbs.has(tk):
					b.icon = main.thumbs[tk]
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			var flow: HFlowContainer = null                # buttons side by side, wrapping (like the tiles on the page)
			if parent.get_child_count() > 0 and parent.get_child(parent.get_child_count() - 1) is HFlowContainer:
				flow = parent.get_child(parent.get_child_count() - 1)
			else:
				flow = HFlowContainer.new()
				flow.add_theme_constant_override("h_separation", 6)
				flow.add_theme_constant_override("v_separation", 6)
				parent.add_child(flow)
			b.custom_minimum_size = Vector2(150 if b.text.length() < 22 else 300, 0)
			b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART   # long texts on two lines (never wider than the panel)
			b.tooltip_text = c.label
			flow.add_child(b)
			if c.has("ro"):
				main.ui_rows[c.id] = b                          # Menüs A: greyed out by _sync_ui
			main.ui_items.append([b, c.label, c.extra.get("expert", false), parent])
		"toggle":
			var row := HBoxContainer.new()                   # text (wraps) + switch on the right, like on the page of MoveEye
			var tl := Label.new()
			var sh: Array = main.UI.short(main.no_emoji(c.label))          # 3D-4.21: at most ~40 characters, the rest in the tooltip
			if main.Sym.lead(c.label)[0] != "":
				row.add_child(main.Sym.icon_rect(main.Sym.lead(c.label)[0]))   # 3D-4.22: the drawn symbol in front
			tl.text = sh[0]
			tl.tooltip_text = sh[1]
			tl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			tl.custom_minimum_size = Vector2(60, 0)
			tl.mouse_filter = Control.MOUSE_FILTER_STOP
			row.add_child(tl)
			var cb := CheckButton.new()
			cb.toggled.connect(func(on): c["set"].call(on))
			cb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			row.add_child(cb)
			tl.gui_input.connect(func(ev):
				if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
					cb.button_pressed = not cb.button_pressed)
			parent.add_child(row)
			main.ui_rows[c.id] = cb
			main.ui_items.append([row, c.label, c.extra.get("expert", false), parent])
		"select":
			var hb := VBoxContainer.new()                    # label above the choice: long choices never widen the panel
			hb.add_theme_constant_override("separation", 2)
			var l := Label.new()
			var shs: Array = main.UI.short(main.no_emoji(c.label))
			l.text = shs[0]
			l.tooltip_text = shs[1]
			l.mouse_filter = Control.MOUSE_FILTER_PASS
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			hb.add_child(l)
			var ob := OptionButton.new()
			ob.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			ob.fit_to_longest_item = false
			ob.clip_text = true
			ob.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
			for o in c.extra.options:
				ob.add_item(o[1])
				ob.set_item_metadata(ob.item_count - 1, o[0])
			ob.item_selected.connect(func(idx): c["set"].call(ob.get_item_metadata(idx)))
			hb.add_child(ob)
			parent.add_child(hb)
			main.ui_rows[c.id] = ob
			main.ui_items.append([hb, c.label, c.extra.get("expert", false), parent])
		"map":                                            # in the window: a button that opens the map (karte.gd)
			var mb := Button.new()
			mb.text = "Karte öffnen: " + c.label + " (K)"
			mb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			mb.pressed.connect(main.open_map)
			parent.add_child(mb)
			main.ui_items.append([mb, c.label, c.extra.get("expert", false), parent])
		"text":
			var tb := VBoxContainer.new()
			tb.add_theme_constant_override("separation", 2)
			var tl2 := Label.new()
			var sht: Array = main.UI.short(main.no_emoji(c.label))
			tl2.text = sht[0]
			tl2.tooltip_text = sht[1]
			tl2.mouse_filter = Control.MOUSE_FILTER_PASS
			tl2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			tb.add_child(tl2)
			var le := LineEdit.new()
			le.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			le.text_submitted.connect(func(t): c["set"].call(t))
			tb.add_child(le)
			parent.add_child(tb)
			main.ui_rows[c.id] = le
			main.ui_items.append([tb, c.label, c.extra.get("expert", false), parent])
		"slider":
			var vb := VBoxContainer.new()
			var hb2 := HBoxContainer.new()
			var l2 := Label.new()
			var shl: Array = main.UI.short(main.no_emoji(c.label))
			if main.Sym.lead(c.label)[0] != "":
				hb2.add_child(main.Sym.icon_rect(main.Sym.lead(c.label)[0]))   # 3D-4.22: the drawn symbol in front
			l2.text = shl[0]
			l2.tooltip_text = shl[1]
			l2.mouse_filter = Control.MOUSE_FILTER_PASS
			l2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			l2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			var val := Label.new()
			hb2.add_child(l2)
			hb2.add_child(val)
			vb.add_child(hb2)
			var hs := HSlider.new()
			hs.min_value = c.extra["min"]
			hs.max_value = c.extra["max"]
			hs.step = c.extra.get("step", 1)
			hs.value_changed.connect(func(v):
				val.text = "%s %s" % [str(snappedf(v, 0.01)), c.extra.get("unit", "")]
				if not main._syncing:
					c["set"].call(v))
			vb.add_child(hs)
			if c.extra.has("tip"):                       # 3D-3.95: explanation when the mouse is over it
				vb.tooltip_text = str(c.extra["tip"])
				hs.tooltip_text = str(c.extra["tip"])
			parent.add_child(vb)
			main.ui_rows[c.id] = hs
			main.ui_items.append([vb, c.label, c.extra.get("expert", false), parent])
