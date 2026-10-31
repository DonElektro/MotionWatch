extends RefCounted
## 3D-4.x «Bergtal» (Daniel, 31.10.2026): ein einsames Schweizer Bergtal, rund 2 × 2 km - Haupttal von Norden (unten, Wald,
## Kapelle, Strasse) bis zur Passhöhe im Süden (Hospiz, Parkplatz, Bunker im Fels), dazwischen Bergsee mit Moränenwall, Schlucht
## mit Wasserfall und Holzbrücke, Alphütte mit Stall, Brunnen, Zäunen und Trockenmauern, Blumenwiese, Blockfeld unter der
## Felswand, Geröllhalde; Seitental West mit Moor (Wollgras), Moorsee und Ruine, Grat mit Gipfelkreuz; Seitental Ost mit
## Gletscherzunge (Spalten), Gletschersee und oberer Steinhütte (Materialseilbahn von der Alp). Wanderwege mit gelben Wegweisern
## und Steinmännern, Strommasten entlang der Strasse.
##
## MoveEye bewacht ein Zelt oder einen Schlafplatz unter freiem Himmel (Isomatte + Schlafsack): 12 vorgeschlagene Plätze
## (SPOTS) oder ein frei gewählter («Hier übernachten»). Wie im Ferienpark steht MoveEye immer im Nullpunkt der Welt: das ganze
## Tal wird so gedreht und verschoben, dass der Schlafplatz im Nullpunkt liegt (Tal-Knoten «bergtal», Transform W).
## Tal-Koordinaten: x = Osten, z = Süden (zum Pass), Höhe relativ (ALT0 = 1500 m ü. M. am Nordende).
##
## Gelände: eine Höhenkarte (4 m) für das ganze Tal, einmal berechnet und behalten (Wechsel von Platz und Jahreszeit baut nur
## die Dinge neu). Gezeichnet in 64 Abschnitten à 256 m in zwei Feinheiten (nah 4 m, fern 16 m) - Godot wählt pro Kamera
## (Fenster UND MoveEye-Kameras) nach Entfernung; dahinter ein Ring ferner Berge als Silhouette. Bäume, Felsen, Zäune als
## MultiMesh in 128-m-Gruppen mit Sichtweite (Wald 480 m, Lite 220 m).

const Bib = preload("res://scripts/bib_berg.gd")
const T = preload("res://scripts/i18n.gd")
const Szenen = preload("res://scripts/szenenplus.gd")
const Worlds = preload("res://scripts/worlds.gd")      # 3D-4.x Welten: the old scenes as places in the valley
const Aussicht = preload("res://scripts/bergtal_aussicht.gd")   # «Bergtal · Aussichtspunkte»: what the viewpoints do
const Orte = preload("res://scripts/bergtal_orte.gd")          # Orte zum Erkunden (Innenräume, Wasser, Grat, Geschichte)

const ALT0 := 1500.0                 # metres above sea level at the north end (height 0)
const LO := -1024.0                  # the height map: from LO to -LO in both directions
const STEP := 4.0
const N := 513                       # (2048 / 4) + 1
const CH := 256.0                    # chunk size (m)

# ---- the places (valley coordinates x, z) -------------------------------------------------------------------------------
const LAKE1 := [Vector2(-60, -390), 130.0, 80.0, 0.25]        # Bergsee: centre, half axes, rotation
const LAKE2 := [Vector2(-640, -300), 55.0, 38.0, -0.4]        # Moorsee in the west side valley
const TARN := [Vector2(600, 430), 26.0, 19.0, 0.6]           # Gletschersee in front of the glacier
const LAKE4 := [Vector2(-880, 420), 30.0, 20.0, 0.2]          # the secret lake behind the west ridge (vignette 34)
const LAKES := [LAKE1, LAKE2, TARN, LAKE4]
const HUT := Vector2(60, 0)
const PASS := Vector2(60, 805)
const HOSPICE := Vector2(18, 790)
const CHAPEL := Vector2(210, -700)
const MOOR := Vector2(-470, -265)
const BOULDERS := Vector2(-300, 300)
const GORGE_HEAD := Vector2(42, -92)          # the waterfall
const GORGE_BRIDGE := Vector2(24, -170)
const RUIN := Vector2(-830, -215)
const RIDGE_VIEW := Vector2(-615, 125)
const BIVOUAC := Vector2(-520, 560)
const BUNKER := Vector2(250, 845)
const GLACIER := Vector2(790, 470)
const UPPER_HUT := Vector2(470, 300)
const CLEARING := Vector2(-150, -800)
# viewpoints (Aussichtspunkte, Daniel 31.10.2026): [id, name, kind (gipfel | grat | kanzel | see | gletscher), x, z, furnishing
# (bank_kreuz | fernrohr | tafel | wild), looking (degrees, 0 = north)]. Each is a reserved place and a sleeping spot.
const VIEWPOINTS := [["vp_horn", "Tschingelspitz (Gipfel West)", "gipfel", -790.0, 520.0, "bank_kreuz", 90.0],
		["vp_grat", "Gratspitz über der Rüfi", "grat", -625.0, 125.0, "wild", 60.0],
		["vp_kanzel", "Chanzle über dem Gumpisee", "kanzel", 262.0, -430.0, "fernrohr", -90.0],
		["vp_seeblick", "Seeblick Gumpisee", "see", -250.0, -470.0, "tafel", 70.0],
		["vp_gletscher", "Gletscherblick Wyssgletscher", "gletscher", 690.0, 330.0, "tafel", 120.0],
		["vp_pass", "Passchanzle Furgga", "kanzel", -30.0, 850.0, "fernrohr", 0.0],
		["vp_ostgipfel", "Nüdelistock (Gipfel Ost)", "gipfel", 720.0, -260.0, "wild", -90.0],
		["vp_moorsee", "Ob em Schwarzseeli", "see", -700.0, -380.0, "bank_kreuz", 30.0]]
# the far peaks around the valley (silhouette ring, panorama boards): [name, azimuth from the valley centre (0 = north),
# height above the north end (m), distance (m)]
const PEAKS := [["Piz Vadret", 20.0, 1500.0, 3200.0], ["Schwarzgrat", 65.0, 1350.0, 2900.0], ["Wyssstock", 110.0, 1650.0, 3100.0],
		["Furgghorn", 160.0, 1250.0, 2800.0], ["Chäschessi", 205.0, 1180.0, 2700.0], ["Riedspitz", 250.0, 1300.0, 3000.0],
		["Gipfeli", 300.0, 1450.0, 3300.0], ["Vorder Tschuggen", 340.0, 1100.0, 2900.0]]
const FLOWERS := Vector2(-90, 170)

# the pass road (from the north end up the east side of the valley, hairpins, over the pass to the south)
const ROAD := [Vector2(240, -1060), Vector2(225, -800), Vector2(205, -600), Vector2(190, -400), Vector2(178, -200), Vector2(172, -40),
		Vector2(180, 140), Vector2(175, 300), Vector2(140, 380), Vector2(240, 430), Vector2(100, 490), Vector2(250, 540), Vector2(90, 600),
		Vector2(230, 650), Vector2(80, 710), Vector2(150, 760), Vector2(80, 790), Vector2(60, 830), Vector2(70, 1060)]
# streams: [points, width]
const STREAMS := [[[Vector2(600, 430), Vector2(470, 360), Vector2(330, 290), Vector2(200, 220), Vector2(120, 110), Vector2(80, 30),
			Vector2(48, -60), Vector2(36, -120), Vector2(18, -200), Vector2(-10, -280), Vector2(-30, -310)], 2.6],
		[[Vector2(-55, -472), Vector2(-40, -650), Vector2(-25, -850), Vector2(-10, -1060)], 3.2],
		[[Vector2(-900, -120), Vector2(-760, -250), Vector2(-640, -300), Vector2(-470, -265), Vector2(-300, -300), Vector2(-185, -380)], 1.8]]
const GORGE := [36.0, -60.0, -265.0]       # stream 0: the gorge from z -60 (waterfall at -92) to z -265
# hiking trails (Wanderwege): [name, points, level: 0 = Wanderweg (gelb), 1 = Bergweg (weiss-rot-weiss), 2 = Alpinwanderweg (weiss-blau-weiss)]
const TRAILS := [["Seeweg", [Vector2(178, -40), Vector2(110, -20), Vector2(60, 0), Vector2(20, -60), Vector2(-60, -100), Vector2(-150, -230), Vector2(-200, -330),
			Vector2(-205, -420), Vector2(-120, -490), Vector2(10, -470), Vector2(80, -380), Vector2(110, -250), Vector2(178, -200)], 0],
		["Schluchtweg", [Vector2(60, 0), Vector2(70, -70), Vector2(50, -130), Vector2(GORGE_BRIDGE.x + 10, -170), Vector2(-5, -175), Vector2(-40, -230), Vector2(-60, -300)], 0],
		["Kapellenweg", [Vector2(10, -470), Vector2(40, -600), Vector2(120, -660), Vector2(CHAPEL.x, -690), Vector2(225, -800)], 0],
		["Höhenweg West", [Vector2(60, 0), Vector2(-40, 90), Vector2(-90, 170), Vector2(-200, 250), Vector2(-300, 300), Vector2(-380, 380), Vector2(-450, 470),
			Vector2(-520, 548)], 1],
		["Pfad zum geheimen See", [Vector2(-620, 128), Vector2(-660, 200), Vector2(-720, 290), Vector2(-800, 360), Vector2(-860, 405)], 2],
		["Gratweg", [Vector2(-300, 300), Vector2(-420, 230), Vector2(-500, 170), Vector2(-560, 125), Vector2(-620, 128)], 1],
		["Moorweg", [Vector2(-200, -330), Vector2(-320, -300), Vector2(-470, -240), Vector2(-600, -255), Vector2(-700, -250), Vector2(-830, -205)], 0],
		["Gletscherweg", [Vector2(180, 140), Vector2(260, 200), Vector2(380, 270), Vector2(470, 300), Vector2(560, 380), Vector2(640, 420), Vector2(720, 450)], 2],
		["Passweg", [Vector2(60, 0), Vector2(110, 120), Vector2(120, 260), Vector2(90, 420), Vector2(60, 560), Vector2(40, 700), Vector2(30, 780)], 1]]

# the suggested sleeping spots: id -> [name, x, z, looking (degrees, 0 = north / down the valley, 90 = east), what it is]
const SPOTS := {"seeufer": ["Am Ufer des Gumpisees", -142.0, -332.0, 20.0, "See"],
		"felsnische": ["Felsnische beim Murmelboden", -255.0, 262.0, 150.0, "Fels"],
		"huette": ["Bei der Alp Tschuggen", 30.0, 22.0, -20.0, "Hütte"],
		"pass": ["Auf dem Furggapass (beim Hospiz)", 48.0, 818.0, 0.0, "Pass"],
		"biwak": ["Bei der Biwakschachtel", -512.0, 548.0, 20.0, "Biwak"],
		"moor": ["Am Rand des Riedmoos", -420.0, -230.0, -110.0, "Moor"],
		"waldlichtung": ["Waldlichtung (unten im Tal)", -148.0, -790.0, 180.0, "Wald"],
		"gletschersee": ["Am Gletscherseeli", 632.0, 450.0, -100.0, "Gletscher"],
		"ruine": ["Bei der Ruine Altstafel", -810.0, -230.0, 80.0, "Ruine"],
		"kapelle": ["Bei der Kapelle St. Jodern", 192.0, -688.0, -60.0, "Kapelle"],
		"schlucht": ["Ob dem Tüfelsschlund", 62.0, -112.0, -120.0, "Schlucht"]}
const SPOT_ORDER := ["huette", "seeufer", "felsnische", "pass", "biwak", "moor", "waldlichtung", "gletschersee", "ruine", "kapelle", "schlucht", "frei"]
# named places (quick travel, signs, map)
const PLACES := [["Alp Tschuggen", 60.0, 0.0], ["Gumpisee", -60.0, -390.0], ["Tüfelsschlund (Wasserfall)", 42.0, -92.0], ["Hängebrücke Tüfelsschlund", 24.0, -170.0],
		["Furggapass mit Hospiz", 40.0, 800.0], ["Parkplatz Furgga", 100.0, 775.0], ["Fort Chrüzli (Bunker)", 250.0, 845.0], ["Kapelle St. Jodern", 210.0, -700.0],
		["Riedmoos (Wollgras)", -470.0, -265.0], ["Schwarzseeli", -640.0, -300.0], ["Ruine Altstafel", -830.0, -215.0], ["Steinchaos Murmelboden", -300.0, 300.0],
		["Rüfi (Geröllhalde)", -380.0, 120.0], ["Gratspitz", -625.0, 125.0], ["Biwak Chüebodehorn", -520.0, 560.0], ["Wyssgletscher", 790.0, 470.0],
		["Gletscherseeli", 600.0, 430.0], ["Obri Stafelhütte (Seilbahn)", 470.0, 300.0], ["Bluemenmatte", -90.0, 170.0], ["Lärchenlichtung", -150.0, -800.0],
		["Schattwald", -60.0, -650.0], ["Furggakehren", 160.0, 560.0], ["Klettersteig Gratspitz", -276.0, 200.0], ["Alte Sennerei Chäsgaden", -700.0, -130.0],
		["Steimandli-Wald", -650.0, 430.0], ["Fondueplätzli", -175.0, -300.0]]
# reserved places for the funny / hidden things (later package): [nr, id, name, x, z, free radius]. 1–16 approved by Daniel
# (31.10.2026); 17+ = the varied zones (suggested, waiting for Daniel's choice).
const VIGNETTES := [[1, "murmeltier_zu_spaet", "Murmeltier kommt zu spät zum Bau", -80.0, 215.0, 4.0],
		[2, "kuh_socke", "Kuh leckt am Zelt / klaut eine Socke", 0.0, 0.0, 0.0],
		[3, "dohlen_sandwich", "Alpendohlen streiten um ein Sandwich", 66.0, 812.0, 4.0],
		[4, "steinbock_kante", "Steinbock auf der steilen Kante", -360.0, 210.0, 3.0],
		[5, "schafstau_pass", "Schafstau auf der Passstrasse", 240.0, 540.0, 6.0],
		[6, "wanderer_kreis", "Wanderer läuft im Kreis um den Wegweiser", -300.0, 300.0, 5.0],
		[7, "gipfelbuch", "Gipfelbuch beim Kreuz (Tschingelspitz)", -790.0, 520.0, 3.0],
		[8, "fondue_fuchs", "Vergessenes Fondue-Caquelon + Fuchs mit Käse", -175.0, -300.0, 3.0],
		[9, "echo_schlucht", "Echo-Platz in der Schlucht", 24.0, -175.0, 3.0],
		[10, "kristallhoehle", "Kristallhöhle hinter dem Wasserfall (nur bei wenig Wasser)", 40.0, -98.0, 3.0],
		[11, "bunker_buero", "Bunkertür geht nur nachts auf (Murmeltier-Büro)", 250.0, 845.0, 4.0],
		[12, "yeti_spuren", "Yeti-Spuren bis zum Schneemann mit Wanderschuhen (Winter)", 700.0, 380.0, 6.0],
		[13, "bartgeier_knochen", "Bartgeier lässt Knochen fallen (bei einem Wanderer)", -400.0, 420.0, 5.0],
		[14, "alphorn", "Alphornbläser bei Sonnenaufgang, Kühe kommen gerannt", 95.0, 60.0, 4.0],
		[15, "sternschnuppen", "Sternschnuppen-Platz auf dem Grat (klare Nächte)", -640.0, 80.0, 4.0],
		[16, "flaschenpost_laterne", "Flaschenpost im See → alte Laterne in der Gletscherspalte", -20.0, -335.0, 3.0],
		[17, "lichtung", "Lärchenwald mit Lichtung", -150.0, -800.0, 8.0],
		[18, "blumenwiese", "Blumenwiese", -90.0, 170.0, 8.0],
		[19, "labyrinth", "Blockfeld-Labyrinth", -300.0, 320.0, 6.0],
		[20, "wollgras", "Moor mit Wollgras", -500.0, -275.0, 6.0],
		[21, "spalten", "Gletscherzunge mit Spalten", 760.0, 460.0, 8.0],
		[22, "ruine", "Ruine des alten Unterstands", -830.0, -215.0, 6.0],
		[23, "haarnadel", "Passstrasse mit Haarnadelkurven", 100.0, 490.0, 5.0],
		[24, "kapelle", "Kapelle auf dem Hügel", 210.0, -700.0, 6.0],
		[25, "seilbahn", "Materialseilbahn (Talstation)", 98.0, 22.0, 4.0],
		[26, "strommast", "Strommast an der Strasse", 232.0, -880.0, 4.0],
		[27, "moorsee", "Moorsee (zweiter kleiner See)", -600.0, -285.0, 5.0],
		[28, "gletschersee", "Gletschersee", 600.0, 405.0, 5.0],
		[29, "murmeltier_fussball", "Murmeltier-Fussball (Tennisball)", -60.0, 232.0, 5.0],
		[30, "schneehase_herbst", "Weisser Schneehase im braunen Herbst", -420.0, 385.0, 4.0],
		[31, "hermelin_mauer", "Hermelin schaut aus jedem Mauerloch", 104.0, -34.0, 3.0],
		[32, "salamander_prozession", "Salamander-Prozession nach Regen (einer falsch rum)", 66.0, -40.0, 3.0],
		[33, "kuhglocken_nebel", "Nur Kuhglocken im Nebel, plötzlich eine Kuh", 20.0, 70.0, 5.0],
		[34, "gemse_hospizdach", "Gämse auf dem Hospiz-Dach", 18.0, 790.0, 0.0],
		[35, "selfie_kante", "Selfie-Wanderer an der Schluchtkante, Kuh stupst", 64.0, -140.0, 3.0],
		[36, "trailrunner", "Trailrunner fragt den Wegweiser", -200.0, -330.0, 3.0],
		[37, "huettenwart", "Hüttenwart fegt, der Wind weht zurück", 48.0, 8.0, 3.0],
		[38, "picknick", "Picknick: Korkenzieher auf dem Hut", -10.0, -296.0, 4.0],
		[39, "gleitschirm", "Gleitschirm landet auf der Kuhweide", 135.0, 85.0, 10.0],
		[40, "postauto", "Postauto mit Dreiklang-Horn (Passstrasse)", 175.0, 300.0, 0.0],
		[41, "schmuggler", "Schmugglerroute (Markierungen nur im Abendlicht)", 360.0, 720.0, 4.0],
		[42, "steinmann_wald", "Steinmann-Wald, einer hat Augen", -650.0, 430.0, 22.0],
		[43, "sennerei", "Verlassene Sennerei mit uraltem Käselaib", -700.0, -130.0, 6.0],
		[44, "holzski", "Holzski schmilzt aus dem Gletscher (Sommer)", 830.0, 485.0, 3.0],
		[45, "nordlicht", "Nordlicht-Platz (seltene klare Winternächte)", 60.0, 850.0, 4.0],
		[46, "geheimer_see", "Geheimer Bergsee hinter dem Grat (schmaler Pfad)", -880.0, 420.0, 6.0]]
# Daniel's numbers 1–34 -> our list: 1–16 = 1–16, 17–34 = 29–46 (17–28 are the varied zones of the coordinator's list)

static var _hm := PackedFloat32Array()       # the height map (valley coordinates), kept between rebuilds
static var _col := PackedColorArray()        # ground colour per point (+ alpha: rock may show on steep ground)
static var _chunks := {}                     # "i,j" -> [near mesh, far mesh]
static var _gen_ms := 0
static var _noise: FastNoiseLite
static var _noise2: FastNoiseLite

var s                       # scenes.gd
var m                       # main.gd
var bib
var tal: Node3D
var spot := "huette"
var bed := "tent"
var season := "sommer"
var h0 := 0.0
var inv := Transform3D()
var rng := RandomNumberGenerator.new()
var lite := false
var info := {}
var spot_xz := Vector2.ZERO
var place := ""                              # 3D-4.x Welten: the old scene that is the place now ("" = a sleeping spot)
var place_r := 0.0
var spot_yaw := 0.0
var rating := {}                             # the evaluation of the sleeping spot
var night_log: Array = []                    # what happened at the spot this night (morning rating)
var _was_dark := false
var _ev_next := 0.0
var _fog_k := 0.0                            # 0 … 1: the fog that rolls in (event)
var _fog_target := 0.0
var _storm_until := 0.0
var _bed_node: Node3D
var _food_node: Node3D
var _pack_node: Node3D
var _residents: Array = []                   # cows, sheep, marmots, chamois near the spot (Actor)
var _birds: Array = []
var _stones: Array = []                      # rolling stones (rockfall)
var _burrows: Array = []                     # world positions of marmot burrows near the spot
var _gm: ShaderMaterial
var aussicht                                   # bergtal_aussicht.gd (Fernrohr, Panorama, Stimmungen, Karte, Abzeichen …)


static func _lite() -> bool:
	"""the central question «Lite?» (Quality.lite() via Bib.lite(), set by main.lite_update)"""
	return Bib.lite()


static var _vp_pos := {}                     # viewpoint id -> where it really is (summits: the top)


static func vp_xz(vp: Array) -> Vector2:
	return _vp_pos.get(vp[0], Vector2(vp[3], vp[4]))


static func spot_data(k: String):
	"""[name, x, z, looking, kind] of a suggested spot (also the viewpoints), or null"""
	if SPOTS.has(k):
		return SPOTS[k]
	for vp in VIEWPOINTS:
		if vp[0] == k:
			var c := vp_xz(vp)
			return [vp[1], c.x + 3.0, c.y + 3.0, vp[6], "Aussicht"]
	return null


static func spot_options() -> Array:
	var out := []
	for k in SPOT_ORDER:
		if k != "frei":
			out.append([k, SPOTS[k][0]])
	for vp in VIEWPOINTS:
		out.append([vp[0], "Aussicht: " + str(vp[1])])
	out.append(["frei", "Eigener Platz («Hier übernachten»)"])
	return out


static func place_options() -> Array:
	var out := [["", "– Ort wählen –"]]
	for k in SPOT_ORDER:
		if SPOTS.has(k):
			out.append(["s:" + k, "Schlafplatz: " + str(SPOTS[k][0])])
	for vp in VIEWPOINTS:
		out.append(["p:" + str(vp[1]), "Aussicht: " + str(vp[1])])
	for p in PLACES:
		out.append(["p:" + str(p[0]), str(p[0])])
	out.append_array(Orte.place_options())
	return out


static func season_of(main) -> String:
	"""the season of the valley: chosen, or from the month (Jahreszeit (Sonnenbahn); today = the real date)"""
	var v := str(main.get("bt_season")) if main.get("bt_season") != null else "auto"
	if v in ["fruehling", "sommer", "herbst", "winter"]:
		return v
	var mo := 0
	if str(main.season) == "today":
		mo = int(Time.get_date_dict_from_system()["month"])
	else:
		mo = int(main.season)
	if mo in [12, 1, 2, 3]:
		return "winter"
	if mo in [4, 5, 6]:
		return "fruehling"
	if mo in [7, 8]:
		return "sommer"
	return "herbst"


# =======================================================================================================================
# the ground (valley coordinates)
# =======================================================================================================================
static func cx(z: float) -> float:
	"""the axis of the main valley"""
	return 40.0 * sin(z / 380.0 + 0.4) + 18.0 * sin(z / 150.0) + 20.0


static var _floor_tab := PackedFloat32Array()


static func _floor(z: float) -> float:
	"""height of the valley floor along the main valley (a table every 2 m)"""
	if _floor_tab.is_empty():
		for k in range(1201):
			_floor_tab.append(_floor_calc(-1200.0 + k * 2.0))
	var f := clampf((z + 1200.0) / 2.0, 0.0, 1199.999)
	var i := int(f)
	return lerpf(_floor_tab[i], _floor_tab[i + 1], f - i)


static func _floor_calc(z: float) -> float:
	var pts := [[-1100.0, -5.0], [-1024.0, 0.0], [-700.0, 30.0], [-470.0, 62.0], [-300.0, 72.0], [-250.0, 92.0], [-100.0, 128.0], [0.0, 150.0],
			[300.0, 215.0], [550.0, 305.0], [805.0, 432.0], [1024.0, 385.0], [1100.0, 370.0]]
	for i in range(pts.size() - 1):
		if z <= float(pts[i + 1][0]):
			var t := smoothstep(float(pts[i][0]), float(pts[i + 1][0]), z)
			return lerpf(float(pts[i][1]), float(pts[i + 1][1]), t)
	return float(pts[-1][1])


static func _smin(a: float, b: float, k: float) -> float:
	var hh := clampf(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
	return lerpf(b, a, hh) - k * hh * (1.0 - hh)


static func _seg_t(p: Vector2, a: Vector2, b: Vector2) -> Vector2:
	"""(t along a-b 0..1, distance)"""
	var ab := b - a
	var t := clampf((p - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
	return Vector2(t, p.distance_to(a + ab * t))


const SE0X := 110.0          # ≈ cx(220) + 60
const SE0H := 203.0          # ≈ _floor(220) + 8


static func _base(x: float, z: float) -> float:
	"""the big shape: main valley (U-shaped, rising to the pass), two side valleys, cliffs, ridges"""
	var f := _floor(z)
	var d := x - cx(z)
	var side := 0.0
	if d < 0.0:
		var w := -d
		if w > 700.0:
			w = 700.0 - (w - 700.0) * 0.6                     # the west ridge: behind it the ground falls again
		side = 1050.0 * pow(smoothstep(55.0, 950.0, w), 1.35)
		side += 85.0 * smoothstep(338.0, 356.0, w) * smoothstep(-80.0, 0.0, z) * (1.0 - smoothstep(620.0, 700.0, z))   # the west cliff
	else:
		var de := d if d < 720.0 else 720.0 - (d - 720.0) * 0.6   # the east ridge
		side = 1000.0 * pow(smoothstep(65.0, 900.0, de), 1.3)
		side += 70.0 * smoothstep(232.0, 248.0, d) * smoothstep(-760.0, -700.0, z) * (1.0 - smoothstep(-200.0, -140.0, z))   # east cliff
	var h := f + side
	var n: float = _noise.get_noise_2d(x, z)
	var r: float = 1.0 - absf(_noise2.get_noise_2d(x * 0.7, z * 0.7))
	h += n * (14.0 + side * 0.09) + r * r * side * 0.12
	# west side valley (moor, Moorsee, ruin): a trough from the main valley to the west, rising
	var sw := _seg_t(Vector2(x, z), Vector2(cx(-250.0), -250.0), Vector2(-1100.0, -260.0))
	var swf := lerpf(98.0, 300.0, pow(sw.x, 1.4))
	var swh := swf + 560.0 * pow(smoothstep(60.0, 620.0, sw.y), 1.4) + n * (8.0 + sw.y * 0.05)
	h = _smin(h, swh, 45.0)
	# east side valley (glacier cirque, tarn): higher and steeper
	var se := _seg_t(Vector2(x, z), Vector2(SE0X, 220.0), Vector2(1100.0, 520.0))
	var sef := lerpf(SE0H, 640.0, pow(se.x, 1.15))
	var seh := sef + 520.0 * pow(smoothstep(50.0, 520.0, se.y), 1.35) + n * (6.0 + se.y * 0.06)
	h = _smin(h, seh, 40.0)
	# the chapel knoll
	h += 24.0 * exp(-(pow(x - CHAPEL.x, 2.0) + pow(z - CHAPEL.y, 2.0)) / 2600.0)
	return h


static func generate() -> void:
	"""the height map and the colours - once (about 1 s), then kept"""
	if not _hm.is_empty():
		return
	var t0 := Time.get_ticks_msec()
	_noise = FastNoiseLite.new()
	_noise.seed = 4811
	_noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	_noise.frequency = 1.0 / 420.0
	_noise.fractal_type = FastNoiseLite.FRACTAL_FBM
	_noise.fractal_octaves = 4
	_noise2 = FastNoiseLite.new()
	_noise2.seed = 977
	_noise2.frequency = 1.0 / 260.0
	_noise2.fractal_octaves = 3
	var fine := FastNoiseLite.new()
	fine.seed = 31
	fine.frequency = 1.0 / 38.0
	fine.fractal_octaves = 2
	# 1) the big shape every 8 m, 2) bilinear to 4 m + fine bumps
	var n8 := 257
	var coarse := PackedFloat32Array()
	coarse.resize(n8 * n8)
	for j in range(n8):
		var z := LO + j * 8.0
		for i in range(n8):
			coarse[j * n8 + i] = _base(LO + i * 8.0, z)
	_hm.resize(N * N)
	for j in range(N):
		var j0 := mini(j / 2, n8 - 2)
		var fj := (j - j0 * 2) * 0.5
		for i in range(N):
			var i0 := mini(i / 2, n8 - 2)
			var fi := (i - i0 * 2) * 0.5
			var a := lerpf(coarse[j0 * n8 + i0], coarse[j0 * n8 + i0 + 1], fi)
			var b := lerpf(coarse[(j0 + 1) * n8 + i0], coarse[(j0 + 1) * n8 + i0 + 1], fi)
			_hm[j * N + i] = lerpf(a, b, fj) + fine.get_noise_2d(LO + i * STEP, LO + j * STEP) * 1.6
	# 3) the features: lakes, moor, flat places, streams and the gorge, the road
	for lk in LAKES:
		_carve_lake(lk)
	_flatten(MOOR, 95.0, 0.85)
	_flatten(HUT, 50.0, 0.8)
	_flatten(HOSPICE + Vector2(30, 0), 45.0, 0.9)
	_flatten(UPPER_HUT, 14.0, 0.9)
	_flatten(CHAPEL, 16.0, 0.9)
	_flatten(RUIN, 14.0, 0.8)
	_flatten(BIVOUAC, 8.0, 0.8)
	_flatten(Vector2(-700, -130), 12.0, 0.8)               # the old dairy
	_flatten(Vector2(-650, 430), 30.0, 0.7)                # the cairn plateau
	for i in range(STREAMS.size()):
		_carve_stream(STREAMS[i][0], float(STREAMS[i][1]), i == 0)
	_road_flatten()
	for pl in Worlds.places_of("bergtal"):                 # 3D-4.x Welten: the flat areas of the old scenes (worlds.gd)
		_pad(Vector2(pl[2], pl[3]), float(pl[5]), pl[0] == "seeufer")
	for sp in SPOTS.values():                              # the suggested spots: flat enough for a tent
		_flatten(Vector2(sp[1], sp[2]), 7.0, 1.0)
	for vp in VIEWPOINTS:
		var c := Vector2(vp[3], vp[4])
		if vp[2] in ["gipfel", "grat"]:                      # on the top: the highest point nearby
			var best := c
			for r in range(8, 100, 8):
				for k in range(16):
					var q := c + Vector2(cos(TAU * k / 16.0), sin(TAU * k / 16.0)) * r
					if H(q.x, q.y) > H(best.x, best.y):
						best = q
			c = best
		_vp_pos[vp[0]] = c
		_flatten(c, 6.0, 1.0)
		_flatten(c + Vector2(3.0, 3.0), 4.0, 1.0)
	_hm = Orte.sculpt(_hm, N, LO, STEP)                      # the narrow ridge «Schafgrat» (bergtal_orte.gd)
	_colours()
	_gen_ms = Time.get_ticks_msec() - t0


static func _idx(x: float, z: float) -> Vector2i:
	return Vector2i(clampi(int(round((x - LO) / STEP)), 0, N - 1), clampi(int(round((z - LO) / STEP)), 0, N - 1))


static func H(x: float, z: float) -> float:
	"""height of the ground (valley coordinates, bilinear in the height map; outside: the edge rises)"""
	var fx := (x - LO) / STEP
	var fz := (z - LO) / STEP
	var out := 0.0
	if fx < 0.0 or fz < 0.0 or fx > N - 1 or fz > N - 1:
		out = maxf(maxf(-fx, fx - (N - 1)), maxf(-fz, fz - (N - 1))) * STEP * 0.35
		fx = clampf(fx, 0.0, N - 1.001)
		fz = clampf(fz, 0.0, N - 1.001)
	var i := mini(int(fx), N - 2)
	var j := mini(int(fz), N - 2)
	var u := fx - i
	var v := fz - j
	var k := j * N + i
	return lerpf(lerpf(_hm[k], _hm[k + 1], u), lerpf(_hm[k + N], _hm[k + N + 1], u), v) + out


static func slope_deg(x: float, z: float, r := 1.5) -> float:
	var gx := (H(x + r, z) - H(x - r, z)) / (2.0 * r)
	var gz := (H(x, z + r) - H(x, z - r)) / (2.0 * r)
	return rad_to_deg(atan(Vector2(gx, gz).length()))


static func grad(x: float, z: float) -> Vector2:
	return Vector2(H(x + 2.0, z) - H(x - 2.0, z), H(x, z + 2.0) - H(x, z - 2.0)) / 4.0


static func _ell(p: Vector2, lk: Array) -> float:
	"""0 in the centre, 1 on the shore of the lake"""
	var q: Vector2 = (p - (lk[0] as Vector2)).rotated(-float(lk[3]))
	return sqrt(pow(q.x / float(lk[1]), 2.0) + pow(q.y / float(lk[2]), 2.0))


static var _wl := {}                        # lake -> water level


static func level_of(lk: Array) -> float:
	return float(_wl.get(str(lk[0]), 0.0))


static func _carve_lake(lk: Array) -> void:
	var c: Vector2 = lk[0]
	var a := float(lk[1])
	var b := float(lk[2])
	var R := maxf(a, b) * 1.6
	var wl := H(c.x, c.y) - 1.0
	_wl[str(c)] = wl
	var i0 := _idx(c.x - R, c.y - R)
	var i1 := _idx(c.x + R, c.y + R)
	for j in range(i0.y, i1.y + 1):
		for i in range(i0.x, i1.x + 1):
			var p := Vector2(LO + i * STEP, LO + j * STEP)
			var e := _ell(p, lk)
			var k := j * N + i
			var h := _hm[k]
			if e < 1.0:                                          # the bed (deeper in the middle)
				h = minf(h, wl - 0.6 - (minf(a, b) * 0.16) * (1.0 - e * e))
			elif e < 1.45:                                       # the shore: a flat beach, a moraine where the ground is low
				var sh := wl + 0.35 + 2.4 * smoothstep(1.0, 1.45, e)
				var k2 := smoothstep(1.0, 1.45, e)
				h = lerpf(maxf(minf(h, sh), wl + 0.3), h if h > sh else sh, k2 * k2)
				if e < 1.06:
					h = minf(h, wl + 0.25)
			_hm[k] = h


static func _flatten(c: Vector2, r: float, k: float) -> void:
	var target := H(c.x, c.y)
	var i0 := _idx(c.x - r * 1.6, c.y - r * 1.6)
	var i1 := _idx(c.x + r * 1.6, c.y + r * 1.6)
	for j in range(i0.y, i1.y + 1):
		for i in range(i0.x, i1.x + 1):
			var d := Vector2(LO + i * STEP, LO + j * STEP).distance_to(c)
			var w := k * (1.0 - smoothstep(r, r * 1.6, d))
			if w > 0.0:
				_hm[j * N + i] = lerpf(_hm[j * N + i], target, w)


static func _pad(c: Vector2, r: float, shore := false) -> void:
	"""3D-4.x Welten: a flat area for an old scene (radius r, edge to 1.5 r); the lakes stay (shore: just above the water)"""
	var target := H(c.x, c.y)
	if shore:
		target = level_of(LAKE1) + 0.45
	var i0 := _idx(c.x - r * 1.5, c.y - r * 1.5)
	var i1 := _idx(c.x + r * 1.5, c.y + r * 1.5)
	for j in range(i0.y, i1.y + 1):
		for i in range(i0.x, i1.x + 1):
			var q := Vector2(LO + i * STEP, LO + j * STEP)
			var lake := false
			for lk in LAKES:
				if _ell(q, lk) < 1.04:
					lake = true
			if lake:
				continue
			var w := 1.0 - smoothstep(r, r * 1.5, q.distance_to(c))
			if w > 0.0:
				_hm[j * N + i] = lerpf(_hm[j * N + i], target, w)


static func _carve_stream(pts: Array, w: float, gorge: bool) -> void:
	"""a channel along the stream; the gorge: deep with steep walls, the waterfall at its head"""
	for s_ in range(pts.size() - 1):
		var a: Vector2 = pts[s_]
		var b: Vector2 = pts[s_ + 1]
		var L := a.distance_to(b)
		var k := 0.0
		while k <= L:
			var p := a.lerp(b, k / L)
			var depth := 1.3
			var half := w * 0.5 + 2.0
			if gorge and p.y < GORGE[1] and p.y > GORGE[2]:
				depth = 3.0 + 16.0 * smoothstep(GORGE[1], GORGE[1] - 30.0, p.y) * (1.0 - smoothstep(GORGE[2] + 50.0, GORGE[2], p.y))
				half = 7.0
			var i0 := _idx(p.x - half - 6.0, p.y - half - 6.0)
			var i1 := _idx(p.x + half + 6.0, p.y + half + 6.0)
			var bed := H(p.x, p.y)
			for j in range(i0.y, i1.y + 1):
				for i in range(i0.x, i1.x + 1):
					var q := Vector2(LO + i * STEP, LO + j * STEP)
					var d := _seg_t(q, a, b).y
					var cut := depth * (1.0 - smoothstep(half * 0.5, half + (1.5 if depth > 4.0 else 5.0), d))
					if cut > 0.0:
						_hm[j * N + i] = minf(_hm[j * N + i], bed - cut + (0.0 if d < half * 0.5 else 0.0))
			k += STEP


static var _map_tex: ImageTexture


static func map_texture() -> ImageTexture:
	"""the map in the style of the Swiss national map (Landeskarte): pale ground, green forest, blue water and glacier, grey
	rock, brown contour lines every 20 m (thicker every 100 m), red road, black dashed trails - 512 × 512 (4 m per pixel), once"""
	if _map_tex != null:
		return _map_tex
	var n := 512
	var img := Image.create(n, n, false, Image.FORMAT_RGB8)
	var paper := Color(0.97, 0.96, 0.92)
	var wood := Color(0.8, 0.9, 0.72)
	for j in range(n):
		for i in range(n):
			var k := j * N + i
			var h := _hm[k]
			var c := paper
			var cc: Color = col_at(i, j)
			if absf(cc.r - C_FOREST.r) < 0.05 and absf(cc.g - C_FOREST.g) < 0.05:
				c = wood
			var hr := _hm[k + 1]
			var hd := _hm[k + N]
			var sl := maxf(absf(hr - h), absf(hd - h)) / STEP
			if sl > 0.9:
				c = Color(0.78, 0.77, 0.75) if (i + j) % 3 != 0 else Color(0.55, 0.54, 0.52)     # rock (hatched)
			if cc.a < 0.01 and cc.b > cc.g:
				c = Color(0.62, 0.8, 0.95)                    # (lake bed colour has a = 0)
			if cc.r > 0.7 and cc.b > 0.85:
				c = Color(0.86, 0.93, 1.0)                    # glacier
			var a := floori(h / 20.0)
			if floori(hr / 20.0) != a or floori(hd / 20.0) != a:
				var idx := maxi(a, floori(hr / 20.0))
				var brown := Color(0.62, 0.42, 0.22) if c.b < 0.95 else Color(0.35, 0.55, 0.85)
				c = c.lerp(brown, 0.85 if idx % 5 == 0 else 0.45)
			img.set_pixel(i, j, c)
	for lk in LAKES:                                          # the lakes in blue
		var c0: Vector2 = lk[0]
		var R := maxf(float(lk[1]), float(lk[2]))
		for j in range(int((c0.y - R - LO) / 4.0), int((c0.y + R - LO) / 4.0) + 1):
			for i in range(int((c0.x - R - LO) / 4.0), int((c0.x + R - LO) / 4.0) + 1):
				if i >= 0 and j >= 0 and i < n and j < n and _ell(Vector2(LO + i * 4.0, LO + j * 4.0), lk) < 1.0:
					img.set_pixel(i, j, Color(0.55, 0.76, 0.93))
	for st in STREAMS:
		for q in dense(st[0], 2.0):
			_px(img, q, Color(0.3, 0.55, 0.9))
	var k2 := 0
	for q in road_pts:
		_px(img, q, Color(0.85, 0.2, 0.15))
	for tr in TRAILS:
		k2 = 0
		for q in dense(tr[1], 2.0):
			k2 += 1
			if k2 % 4 < 2:
				_px(img, q, Color(0.1, 0.1, 0.1) if int(tr[2]) < 2 else Color(0.15, 0.3, 0.8))
	_map_tex = ImageTexture.create_from_image(img)
	return _map_tex


static func _px(img: Image, q: Vector2, c: Color) -> void:
	var i := int((q.x - LO) / 4.0)
	var j := int((q.y - LO) / 4.0)
	if i >= 0 and j >= 0 and i < img.get_width() and j < img.get_height():
		img.set_pixel(i, j, c)


static var road_h := PackedFloat32Array()        # the height of the road along ROAD every 4 m (smooth)
static var road_pts := PackedVector2Array()


static func _road_flatten() -> void:
	road_pts.clear()
	for s_ in range(ROAD.size() - 1):
		var a: Vector2 = ROAD[s_]
		var b: Vector2 = ROAD[s_ + 1]
		var L := a.distance_to(b)
		var k := 0.0
		while k < L:
			road_pts.append(a.lerp(b, k / L))
			k += STEP
	road_pts.append(ROAD[-1])
	_round_hairpins()
	var raw := PackedFloat32Array()
	for p in road_pts:
		raw.append(H(p.x, p.y))
	road_h = raw
	for it in range(3):                                      # smooth along the road (no bumps)
		var nh := road_h.duplicate()
		for i in range(road_h.size()):
			var sum := 0.0
			var n := 0
			for o in range(-8, 9):
				var ii := clampi(i + o, 0, road_h.size() - 1)
				sum += road_h[ii]
				n += 1
			nh[i] = sum / n
		road_h = nh
	var wbuf := PackedFloat32Array()
	wbuf.resize(N * N)
	var tbuf := PackedFloat32Array()
	tbuf.resize(N * N)
	for r in range(road_pts.size()):
		var p: Vector2 = road_pts[r]
		var i0 := _idx(p.x - 12.0, p.y - 12.0)
		var i1 := _idx(p.x + 12.0, p.y + 12.0)
		for j in range(i0.y, i1.y + 1):
			for i in range(i0.x, i1.x + 1):
				var d := Vector2(LO + i * STEP, LO + j * STEP).distance_to(p)
				var w := 1.0 - smoothstep(4.5, 11.0, d)
				if w > wbuf[j * N + i]:
					wbuf[j * N + i] = w
					tbuf[j * N + i] = road_h[r] - 0.05
	for k in range(N * N):
		if wbuf[k] > 0.0:
			_hm[k] = lerpf(_hm[k], tbuf[k], wbuf[k])


static func _round_hairpins() -> void:
	"""the corners of the road a little rounder (Chaikin, twice)"""
	for it in range(2):
		var out := PackedVector2Array([road_pts[0]])
		for i in range(road_pts.size() - 1):
			out.append(road_pts[i].lerp(road_pts[i + 1], 0.25))
			out.append(road_pts[i].lerp(road_pts[i + 1], 0.75))
		out.append(road_pts[-1])
		road_pts = out
	var even := PackedVector2Array([road_pts[0]])            # again every 4 m
	var acc := 0.0
	for i in range(1, road_pts.size()):
		acc += road_pts[i].distance_to(road_pts[i - 1])
		if acc >= STEP:
			even.append(road_pts[i])
			acc = 0.0
	road_pts = even


# ---- colours of the ground (per point of the height map; the shader adds rock, snow, the season) -------------------------
const C_MEADOW := Color(0.36, 0.46, 0.2)
const C_ALP := Color(0.46, 0.5, 0.25)          # alpine meadow (higher, drier, yellowish)
const C_FOREST := Color(0.24, 0.24, 0.13)
const C_MOOR := Color(0.42, 0.4, 0.2)
const C_SCREE := Color(0.58, 0.56, 0.52)
const C_GLACIER := Color(0.82, 0.88, 0.94)
const C_SHORE := Color(0.55, 0.52, 0.45)
const C_BED := Color(0.25, 0.27, 0.22)
const C_PASTURE := Color(0.32, 0.44, 0.17)


static func forest_k(x: float, z: float, h: float) -> float:
	"""0 … 1: how much forest (larch / stone pine / spruce lower down) - below the tree line, not on steep or wet ground"""
	var tl := 470.0 + 40.0 * _noise.get_noise_2d(x * 3.0, z * 3.0)     # the tree line (≈ 1970 m)
	var k := 1.0 - smoothstep(tl - 60.0, tl, h)
	k *= 0.55 + 0.9 * _noise2.get_noise_2d(x * 2.5 + 300.0, z * 2.5)
	if Vector2(x, z).distance_to(HUT) < 170.0 or Vector2(x, z).distance_to(CLEARING) < 42.0 or Vector2(x, z).distance_to(MOOR) < 120.0 \
			or Vector2(x, z).distance_to(FLOWERS) < 70.0 or Vector2(x, z).distance_to(CHAPEL) < 45.0:
		k = 0.0
	return clampf(k, 0.0, 1.0)


static func zone(x: float, z: float) -> String:
	"""the kind of ground (for plants, rocks, the spot evaluation)"""
	var p := Vector2(x, z)
	for lk in LAKES:
		var e := _ell(p, lk)
		if e < 1.0:
			return "lake"
		if e < 1.18:
			return "shore"
	if p.distance_to(MOOR) < 95.0 + 15.0 * _noise.get_noise_2d(x * 4.0, z * 4.0):
		return "moor"
	if _glacier_k(x, z) > 0.5:
		return "glacier"
	var w := cx(z) - x
	if w > 230.0 and w < 345.0 and z > -60.0 and z < 660.0:
		return "scree"
	if p.distance_to(BOULDERS) < 75.0:
		return "boulders"
	if p.distance_to(FLOWERS) < 65.0:
		return "flowers"
	if p.distance_to(HUT) < 160.0:
		return "pasture"
	return "meadow"


static func _glacier_k(x: float, z: float) -> float:
	"""the glacier tongue in the east side valley"""
	var se := _seg_t(Vector2(x, z), Vector2(680.0, 445.0), Vector2(1100.0, 540.0))
	var wid := lerpf(40.0, 150.0, se.x)
	return 1.0 - smoothstep(wid * 0.8, wid, se.y + 12.0 * _noise.get_noise_2d(x * 5.0, z * 5.0))


const NC := 257              # the colours every 8 m


static func _colours() -> void:
	_col.resize(NC * NC)
	var rock := FastNoiseLite.new()
	rock.seed = 5
	rock.frequency = 1.0 / 160.0
	for j in range(NC):
		var z := LO + j * 8.0
		for i in range(NC):
			var x := LO + i * 8.0
			var h := _hm[(j * 2) * N + i * 2]
			var zn := zone(x, z)
			var c := C_MEADOW
			var rk := 1.0
			var v: float = rock.get_noise_2d(x, z)
			match zn:
				"lake":
					c = C_BED
					rk = 0.0
				"shore":
					c = C_SHORE
					rk = 0.3
				"moor":
					c = C_MOOR.lerp(Color(0.2, 0.22, 0.16), clampf(0.5 + v * 2.0, 0.0, 1.0) * 0.5)
					rk = 0.0
				"glacier":
					c = C_GLACIER.lerp(Color(0.6, 0.7, 0.78), clampf(0.4 + v, 0.0, 1.0) * 0.4)
					rk = 0.15
				"scree":
					c = C_SCREE.lerp(Color(0.5, 0.48, 0.44), clampf(0.5 + v * 1.5, 0.0, 1.0))
					rk = 0.4
				"boulders":
					c = C_SCREE.lerp(C_ALP, 0.35)
				"flowers":
					c = Color(0.4, 0.5, 0.22)
				"pasture":
					c = C_PASTURE
				_:
					var fk := forest_k(x, z, h)
					c = C_MEADOW.lerp(C_ALP, smoothstep(250.0, 560.0, h + v * 60.0))
					c = c.lerp(C_SCREE.darkened(0.1), smoothstep(560.0, 760.0, h + v * 80.0))      # high up: more stones
					c = c.lerp(C_FOREST, smoothstep(0.25, 0.6, fk))
			# rock tint for the shader (cliffs): stored in alpha × rock-type in the low bits is too much - alpha only
			c.a = rk
			_col[j * NC + i] = c
	# the road and the paths are separate ribbons (crisp); under them: no rock
	for p in road_pts:
		var q := Vector2i(clampi(int(round((p.x - LO) / 8.0)), 0, NC - 1), clampi(int(round((p.y - LO) / 8.0)), 0, NC - 1))
		var cc: Color = _col[q.y * NC + q.x]
		_col[q.y * NC + q.x] = Color(cc.r, cc.g, cc.b, 0.0)


static func col_at(i: int, j: int) -> Color:
	"""the colour at point (i, j) of the 4-m height map (bilinear in the 8-m colours)"""
	var a := mini(i / 2, NC - 2)
	var b := mini(j / 2, NC - 2)
	var u := (i - a * 2) * 0.5
	var v := (j - b * 2) * 0.5
	var k := b * NC + a
	return _col[k].lerp(_col[k + 1], u).lerp(_col[k + NC].lerp(_col[k + NC + 1], u), v)


# ---- meshes of the ground: 8 × 8 chunks, near (4 m) and far (16 m) ---------------------------------------------------------
static func chunk_mesh(ci: int, cj: int, step_i: int) -> ArrayMesh:
	var key := "%d,%d,%d" % [ci, cj, step_i]
	if _chunks.has(key):
		return _chunks[key]
	var per := int(CH / STEP)                          # 64 cells of the height map per chunk
	var n := per / step_i + 1
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var cols := PackedColorArray()
	verts.resize(n * n)
	norms.resize(n * n)
	cols.resize(n * n)
	for b in range(n):
		for a in range(n):
			var i := mini(ci * per + a * step_i, N - 1)
			var j := mini(cj * per + b * step_i, N - 1)
			var k := j * N + i
			var hx := _hm[j * N + mini(i + 1, N - 1)] - _hm[j * N + maxi(i - 1, 0)]
			var hz := _hm[mini(j + 1, N - 1) * N + i] - _hm[maxi(j - 1, 0) * N + i]
			var skirt := 0.0
			if step_i > 1 and (a == 0 or b == 0 or a == n - 1 or b == n - 1):
				skirt = 1.5                                 # far: a little lower at the edge (no gaps to the near chunks)
			verts[b * n + a] = Vector3(LO + i * STEP, _hm[k] - skirt, LO + j * STEP)
			norms[b * n + a] = Vector3(-hx, 2.0 * STEP, -hz).normalized()
			cols[b * n + a] = col_at(i, j)
	var idx := PackedInt32Array()
	for b in range(n - 1):
		for a in range(n - 1):
			var q := b * n + a
			idx.append_array([q, q + 1, q + n, q + 1, q + n + 1, q + n])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_COLOR] = cols
	arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	_chunks[key] = am
	return am


# =======================================================================================================================
# building the scene
# =======================================================================================================================
static func build_scene(sc) -> void:
	var bt = new()
	sc.data["bergtal"] = bt                          # keeps it (and main.ground_fn) alive while the scene is there
	bt._build(sc)


func _notification(what: int) -> void:
	if what == NOTIFICATION_PREDELETE and m != null and is_instance_valid(m) and m.env != null:
		m.env.fog_height_density = 0.0               # the valley fog of the autumn goes with the scene
		if aussicht != null:
			aussicht.cleanup()


func P(x: float, z: float, dy := 0.0) -> Vector3:
	"""a point on the ground (valley coordinates)"""
	return Vector3(x, H(x, z) + dy, z)


func W(p: Vector3) -> Vector3:
	"""valley -> world"""
	return tal.transform * p


func WG(x: float, z: float, dy := 0.0) -> Vector3:
	return tal.transform * P(x, z, dy)


func V(wp: Vector3) -> Vector3:
	"""world -> valley"""
	return inv * wp


func wrot(r: float) -> float:
	return r + tal.rotation.y


var decks: Array = []                        # bridges: [centre (valley), half size, rot, deck height] - people walk over them


func gy(x: float, z: float) -> float:
	"""height of the ground in WORLD coordinates (main.ground_fn) - on a bridge: the deck"""
	var p := inv * Vector3(x, 0, z)
	for d in decks:
		var q: Vector2 = (Vector2(p.x, p.z) - (d[0] as Vector2)).rotated(-float(d[2]))
		if absf(q.x) < (d[1] as Vector2).x and absf(q.y) < (d[1] as Vector2).y:
			return float(d[3]) - h0
	for ic in ice:                                           # winter: on the frozen lake
		var e := _ell(Vector2(p.x, p.z), ic[0])
		if e < 1.0 and e >= float(ic[1]):
			return maxf(H(p.x, p.z), float(ic[2]) + 0.06) - h0
	return H(p.x, p.z) - h0


var ice: Array = []                          # [lake, ice from (ellipse radius), water level] - walkable in winter
var orte = null                              # bergtal_orte.gd: the places to explore (buildings with their inside …)


func _build(sc) -> void:
	var t0 := Time.get_ticks_msec()
	s = sc
	m = sc.m
	lite = _lite() or str(m.quality) == "simple"
	rng.seed = 2026
	var first := _hm.is_empty()
	generate()
	var t1 := Time.get_ticks_msec()
	season = season_of(m)
	bed = str(m.get("bt_bed")) if m.get("bt_bed") != null else "tent"
	spot = str(m.get("bt_spot")) if m.get("bt_spot") != null else "huette"
	var fr: Array = m.get("bt_free") if m.get("bt_free") is Array else []
	place = Worlds.active(m, "bergtal")
	if place != "":                                      # 3D-4.x Welten: an old scene is the place (worlds.gd builds it)
		var pl: Array = Worlds.PLACES[place]
		spot = place
		spot_xz = Vector2(float(pl[2]), float(pl[3]))
		spot_yaw = float(pl[4])
		place_r = float(pl[5])
	elif spot == "frei" and fr.size() >= 3:
		spot_xz = Vector2(float(fr[0]), float(fr[1]))
		spot_yaw = float(fr[2])
	else:
		if spot_data(spot) == null:
			spot = "huette"
		var sp: Array = spot_data(spot)
		spot_xz = Vector2(sp[1], sp[2])
		spot_yaw = float(sp[3])
	h0 = H(spot_xz.x, spot_xz.y)
	tal = Node3D.new()
	tal.name = "bergtal"
	var b := Basis(Vector3.UP, deg_to_rad(spot_yaw))
	tal.transform = Transform3D(b, b * -Vector3(spot_xz.x, h0, spot_xz.y))
	s.root.add_child(tal)
	inv = tal.transform.affine_inverse()
	m.terrain = true
	m.ground_fn = Callable(self, "gy")
	bib = Bib.new(m, s, tal, tal.transform)
	if place != "":
		bib.clear = [[spot_xz, place_r + 8.0]]          # nothing of the valley on the flat area of the place
	orte = Orte.new(self)
	_ground()
	_apron()
	_far_mountains()
	var t2 := Time.get_ticks_msec()
	_water()
	_roads_and_trails()
	_vegetation()
	var t3 := Time.get_ticks_msec()
	_hut_area()
	_lake_gorge()
	_pass_area()
	_lower_valley()
	_side_valleys()
	_viewpoints()
	aussicht = Aussicht.new(self)
	aussicht.pieces()                                # (the things only seen through the telescope)
	_vignette_pieces()
	_signs_and_cairns()
	orte.build()
	if place == "":
		_own_spot()
	bib.finish()
	_lights_and_fx()
	_labels()
	_erleben()
	if season != "winter":
		s.meadow(160 if lite else 420, 3.0, 35.0, func(p: Vector3):
			var q := inv * p
			var z := zone(q.x, q.z)
			return z in ["lake", "shore", "scree", "glacier"] or slope_deg(q.x, q.z) > 30.0 or (place != "" and p.length() < place_r))
	rating = evaluate(spot_xz.x, spot_xz.y)
	_publish()
	aussicht.start()
	s.data["bergtal_erleben_b"] = preload("res://scripts/bergtal_erleben_b.gd").new()   # vignettes 18–34 (Daniel's numbers)
	s.data["bergtal_erleben_b"].setup(self)
	_need_residents = true                                # (at the start of the program the visitors node is not there yet)
	m.anims.append(Callable(self, "_tick"))
	_ev_next = m.now() + randf_range(40.0, 90.0)
	_was_dark = m.is_dark()
	info.merge({"ms": Time.get_ticks_msec() - t0, "terrain_ms": t1 - t0, "terrain_cached": not first, "ground_ms": t2 - t1, "plants_ms": t3 - t2,
			"gen_ms": _gen_ms, "spot": spot, "season": season, "bed": bed, "lite": lite, "lib": bib.stats.duplicate(), "lamps": bib.lamps.size(),
			"mem_static_mb": snappedf(float(OS.get_static_memory_usage()) / 1048576.0, 0.1)}, true)
	print("Bergtal: %s, %s, %d ms (Gelände %d ms%s), %s" % [spot, season, info["ms"], t1 - t0, " aus dem Speicher" if not first else "", str(bib.stats)])


# ---- lustige / versteckte Ereignisse (bergtal_erleben_a.gd: 1–17) ---------------------------------------------------------
func _erleben() -> void:
	var t0 := Time.get_ticks_msec()
	var ea = preload("res://scripts/bergtal_erleben_a.gd").new()
	ea.setup(self)
	s.data["bt_erleben_a"] = ea
	info["erleben_a_ms"] = Time.get_ticks_msec() - t0


# ---- ground ------------------------------------------------------------------------------------------------------------
func _season_params(mt: ShaderMaterial) -> void:
	match season:
		"winter":
			mt.set_shader_parameter("snow_cover", 1.0)
			mt.set_shader_parameter("snow_line", -100.0)
			mt.set_shader_parameter("grass_tint", Vector3(0.8, 0.75, 0.6))
		"fruehling":
			mt.set_shader_parameter("snow_cover", 0.0)
			mt.set_shader_parameter("snow_line", 430.0)      # ≈ 1930 m: late snow on the shady side
			mt.set_shader_parameter("grass_tint", Vector3(1.05, 1.18, 0.85))
		"herbst":
			mt.set_shader_parameter("snow_cover", 0.0)
			mt.set_shader_parameter("snow_line", 820.0)
			mt.set_shader_parameter("grass_tint", Vector3(1.45, 1.05, 0.55))   # brown-yellow alpine grass
		_:
			mt.set_shader_parameter("snow_cover", 0.0)
			mt.set_shader_parameter("snow_line", 980.0)      # ≈ 2480 m (+ the glacier)
			mt.set_shader_parameter("grass_tint", Vector3(1.0, 1.0, 1.0))


func _ground() -> void:
	_gm = ShaderMaterial.new()
	_gm.shader = load("res://shaders/bergtal_boden.gdshader")
	_gm.set_shader_parameter("noise_tex", m.noise_tex)
	_gm.set_shader_parameter("detail", 0.0 if lite else 1.0)
	_season_params(_gm)
	m.ground_mats = [_gm]
	var near_end := 380.0 if lite else 720.0
	for cj in range(8):
		for ci in range(8):
			for lod in [1, 4]:
				var mi: MeshInstance3D = m.add_mesh(tal, chunk_mesh(ci, cj, lod), Vector3.ZERO, _gm, "x")
				var th: MeshInstance3D = tal.get_child(tal.get_child_count() - 1)
				th.material_override = m.tmats["ground"]
				for g in [mi, th]:
					if lod == 1:
						g.visibility_range_end = near_end
						g.visibility_range_end_margin = 20.0
					else:
						g.visibility_range_begin = near_end - 20.0
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if lod == 1 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	info["chunks"] = 64


static var _apron_mesh: ArrayMesh


func _apron() -> void:
	"""the land around the 2 × 2 km (to 3 km): the same big shape, coarse (64 m), no thermal twin needed far away"""
	if _apron_mesh == null:
		var lo := -3008.0
		var st := 64.0
		var n := 95
		var verts := PackedVector3Array()
		var cols := PackedColorArray()
		verts.resize(n * n)
		cols.resize(n * n)
		for j in range(n):
			for i in range(n):
				var x := lo + i * st
				var z := lo + j * st
				var h := _base(x, z)
				var inner := maxf(absf(x), absf(z)) < -LO + 40.0
				if inner:
					h = H(x, z) - 4.0                       # under the near ground at the seam
				verts[j * n + i] = Vector3(x, h, z)
				var c := C_MEADOW.lerp(C_FOREST, 0.6 * (1.0 - smoothstep(300.0, 450.0, h)))
				c = c.lerp(Color(0.42, 0.41, 0.39), smoothstep(450.0, 700.0, h))
				c = c.lerp(Color(0.85, 0.87, 0.9), smoothstep(900.0, 1100.0, h))
				c.a = 1.0
				cols[j * n + i] = c
		var idx := PackedInt32Array()
		for j in range(n - 1):
			for i in range(n - 1):
				var x0 := lo + i * st
				var z0 := lo + j * st
				if x0 >= LO and x0 + st <= -LO and z0 >= LO and z0 + st <= -LO:
					continue
				var a := j * n + i
				idx.append_array([a, a + 1, a + n, a + 1, a + n + 1, a + n])
		var norms := PackedVector3Array()
		norms.resize(n * n)
		for j in range(n):
			for i in range(n):
				var hx := verts[j * n + mini(i + 1, n - 1)].y - verts[j * n + maxi(i - 1, 0)].y
				var hz := verts[mini(j + 1, n - 1) * n + i].y - verts[maxi(j - 1, 0) * n + i].y
				norms[j * n + i] = Vector3(-hx, 4.0 * st, -hz).normalized()
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = verts
		arr[Mesh.ARRAY_NORMAL] = norms
		arr[Mesh.ARRAY_COLOR] = cols
		arr[Mesh.ARRAY_INDEX] = idx
		_apron_mesh = ArrayMesh.new()
		_apron_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mi: MeshInstance3D = m.add_mesh(tal, _apron_mesh, Vector3.ZERO, _gm, "x")
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var th: MeshInstance3D = tal.get_child(tal.get_child_count() - 1)
	th.material_override = m.tmats["ground"]


func _far_mountains() -> void:
	"""a ring of far mountains round the valley (cheap: one mesh, vertex colours, no shadow, not in the thermal picture)"""
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 120 if lite else 240
	var prof := PackedFloat32Array()
	for i in range(n + 1):
		var az := 360.0 * i / n
		var hh := 650.0 + 220.0 * sin(deg_to_rad(az * 3.0)) + 140.0 * sin(deg_to_rad(az * 7.0 + 40.0)) + 90.0 * sin(deg_to_rad(az * 17.0))
		for pk in PEAKS:
			var da := absf(wrapf(az - float(pk[1]), -180.0, 180.0))
			hh = maxf(hh, float(pk[2]) - da * 55.0)
		prof.append(hh)
	var r0 := 3000.0
	for i in range(n):
		var a0 := deg_to_rad(360.0 * i / n)
		var a1 := deg_to_rad(360.0 * (i + 1) / n)
		var d0 := Vector3(sin(a0), 0, -cos(a0))
		var d1 := Vector3(sin(a1), 0, -cos(a1))
		var hA := prof[i]
		var hB := prof[i + 1]
		var lowA := d0 * r0 + Vector3(0, 0, 0)
		var lowB := d1 * r0
		var midA := d0 * (r0 + 500.0) + Vector3(0, hA * 0.72, 0)
		var midB := d1 * (r0 + 500.0) + Vector3(0, hB * 0.72, 0)
		var topA := d0 * (r0 + 900.0) + Vector3(0, hA, 0)
		var topB := d1 * (r0 + 900.0) + Vector3(0, hB, 0)
		var rock := Color(0.32, 0.33, 0.36)
		var snw := Color(0.86, 0.88, 0.92) if season != "sommer" or hA > 1250.0 else rock.lightened(0.15)
		for tri in [[lowA, lowB, midA, Color(0.2, 0.24, 0.18), Color(0.2, 0.24, 0.18), rock], [lowB, midB, midA, Color(0.2, 0.24, 0.18), rock, rock],
				[midA, midB, topA, rock, rock, snw], [midB, topB, topA, rock, snw, snw]]:
			var nrm: Vector3 = ((tri[1] as Vector3) - (tri[0] as Vector3)).cross((tri[2] as Vector3) - (tri[0] as Vector3)).normalized()
			if nrm.dot(-d0) < 0.0:
				nrm = -nrm
			for k in range(3):
				st.set_color(tri[3 + k])
				st.set_normal(nrm)
				st.add_vertex(tri[k])
	var mt := StandardMaterial3D.new()
	mt.vertex_color_use_as_albedo = true
	mt.vertex_color_is_srgb = true
	mt.roughness = 1.0
	mt.cull_mode = BaseMaterial3D.CULL_DISABLED
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mt
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.layers = 1
	mi.position = Vector3(0, -40.0, 0)
	tal.add_child(mi)


# ---- water -------------------------------------------------------------------------------------------------------------
func _water_mat(ice: bool) -> StandardMaterial3D:
	var wm := StandardMaterial3D.new()
	if ice:
		wm.albedo_color = Color(0.78, 0.84, 0.88)
		wm.roughness = 0.35
		wm.metallic = 0.05
	else:
		wm.albedo_color = Color(0.06, 0.2, 0.24) if season != "fruehling" else Color(0.08, 0.24, 0.26)
		wm.metallic = 0.35
		wm.roughness = 0.05
	return wm


func _lake_mesh(lk: Array, e0: float, e1: float, y: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var c: Vector2 = lk[0]
	var nseg := 48
	for i in range(nseg):
		var a0 := TAU * i / nseg
		var a1 := TAU * (i + 1) / nseg
		var pts := []
		for pr in [[a0, e0], [a1, e0], [a1, e1], [a0, e1]]:
			var q := Vector2(cos(pr[0]) * float(lk[1]) * pr[1], sin(pr[0]) * float(lk[2]) * pr[1]).rotated(float(lk[3])) + c
			pts.append(Vector3(q.x, y, q.y))
		for k in [0, 2, 1, 0, 3, 2]:
			st.set_normal(Vector3.UP)
			st.add_vertex(pts[k])
	return st.commit()


func _water() -> void:
	var lakes_info := []
	for lk in LAKES:
		var wl := level_of(lk)
		var high: bool = (lk[0] as Vector2) != (LAKE1[0] as Vector2)
		var ice_e := 1.2                                     # from this «radius» outwards: ice (1.2 = none)
		if season == "winter":
			ice_e = 0.0 if high else 0.72                   # the big lake: an open patch in the middle, ice at the shore
		elif season == "fruehling" and wl > 380.0:
			ice_e = 0.45                                     # high lakes thaw late
		elif season == "herbst" and wl > 600.0:
			ice_e = 0.9
		if ice_e > 0.0:
			m.add_mesh(tal, _lake_mesh(lk, 0.0, minf(ice_e, 1.06), wl), Vector3.ZERO, _water_mat(false), "pond")
		if ice_e < 1.06:
			m.add_mesh(tal, _lake_mesh(lk, ice_e, 1.06, wl + 0.03), Vector3.ZERO, _water_mat(true), "stone")
		lakes_info.append({"x": (lk[0] as Vector2).x, "z": (lk[0] as Vector2).y, "level_m": snappedf(wl + ALT0, 1.0), "ice_from": ice_e})
		if season == "winter" and ice_e < 1.0:
			ice.append([lk, ice_e, wl])                         # thick enough to walk on (Daniel: «begehbar, knackt»)
		# people and animals do not walk into the lake (only where it is near the spot)
		if (lk[0] as Vector2).distance_to(spot_xz) < 700.0:
			var c: Vector2 = lk[0]
			var r := 9.0
			var x := -float(lk[1])
			while x <= float(lk[1]):
				var z := -float(lk[2])
				while z <= float(lk[2]):
					var q := Vector2(x, z).rotated(float(lk[3])) + c
					var eq := _ell(q, lk)
					if eq < 0.9 and (season != "winter" or eq < ice_e - 0.12):
						m.add_obstacle(W(Vector3(q.x, 0, q.y)), r)
						m.set_obstacle_height(0.1)
					z += 12.0
				x += 12.0
	info["lakes"] = lakes_info
	# the streams: ribbons along the bed (in winter mostly under the snow and ice: thin and white-grey)
	var cm := StandardMaterial3D.new()
	cm.albedo_color = Color(0.32, 0.42, 0.44) if season != "winter" else Color(0.7, 0.75, 0.78)
	cm.metallic = 0.2
	cm.roughness = 0.12 if season != "winter" else 0.5
	cm.cull_mode = BaseMaterial3D.CULL_DISABLED
	for si in range(STREAMS.size()):
		var pts: Array = STREAMS[si][0]
		var w := float(STREAMS[si][1]) * (0.5 if season == "winter" else (1.3 if season == "fruehling" else 1.0))
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var prev := []
		var cnt := 0
		for k in range(pts.size() - 1):
			var a: Vector2 = pts[k]
			var b2: Vector2 = pts[k + 1]
			var L := a.distance_to(b2)
			var dd := (b2 - a) / L
			var nn := Vector2(-dd.y, dd.x)
			var t := 0.0
			while t < L:
				var p := a + dd * t
				var y := INF
				for o in [-0.5, 0.0, 0.5]:
					y = minf(y, H(p.x + nn.x * w * o, p.y + nn.y * w * o))
				var inl := false
				for lk in LAKES:
					if _ell(p, lk) < 1.0:
						inl = true
				var l := Vector3(p.x - nn.x * w * 0.5, y + 0.12, p.y - nn.y * w * 0.5)
				var r := Vector3(p.x + nn.x * w * 0.5, y + 0.12, p.y + nn.y * w * 0.5)
				if not prev.is_empty() and not inl:
					for v in [prev[0], prev[1], l, prev[1], r, l]:
						st.set_normal(Vector3.UP)
						st.add_vertex(v)
					cnt += 1
				prev = [l, r] if not inl else []
				t += 3.0
		if cnt > 0:
			var mi: MeshInstance3D = m.add_mesh(tal, st.commit(), Vector3.ZERO, cm, "pond")
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# the waterfall at the head of the gorge: a curtain of white water, spray and its noise
	var top := _bed_at(0, GORGE_HEAD.y + 16.0)
	var bot := _bed_at(0, GORGE_HEAD.y - 16.0)
	var fall := maxf(4.0, top - bot)
	var wm := StandardMaterial3D.new()
	wm.albedo_color = Color(0.88, 0.92, 0.95, 0.75) if season != "winter" else Color(0.85, 0.92, 0.98, 1.0)   # winter: an ice fall
	wm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if season != "winter" else BaseMaterial3D.TRANSPARENCY_DISABLED
	wm.cull_mode = BaseMaterial3D.CULL_DISABLED
	wm.roughness = 0.3
	var wf := QuadMesh.new()
	wf.size = Vector2(3.2 if season == "fruehling" else 2.2, fall)
	var wp := Vector3(GORGE_HEAD.x, bot + fall * 0.5, GORGE_HEAD.y)
	m.add_mesh(tal, wf, wp, wm, "pond", Vector3(0, deg_to_rad(10.0), 0))
	if not lite and season != "winter" and W(wp).length() < 400.0:
		var sp := CPUParticles3D.new()
		sp.amount = 40
		sp.lifetime = 1.6
		sp.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
		sp.emission_box_extents = Vector3(2.0, 0.3, 1.0)
		sp.direction = Vector3(0, 1, 0)
		sp.spread = 60.0
		sp.initial_velocity_min = 1.0
		sp.initial_velocity_max = 2.5
		sp.gravity = Vector3(0, -1.0, 0)
		sp.scale_amount_min = 0.6
		sp.scale_amount_max = 1.4
		var qm := QuadMesh.new()
		qm.size = Vector2(0.6, 0.6)
		var pm := StandardMaterial3D.new()
		pm.albedo_color = Color(1, 1, 1, 0.25)
		pm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		pm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		pm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		qm.material = pm
		sp.mesh = qm
		sp.position = Vector3(wp.x, bot + 0.5, wp.z)
		tal.add_child(sp)
	if W(wp).length() < 500.0 and season != "winter":
		m.add_sound(-6.0, W(wp), 1.0e7)                     # the noise of the waterfall (≈ 85 dB at a few metres)
	info["waterfall_m"] = snappedf(fall, 0.1)


func _bed_at(si: int, z: float) -> float:
	"""the height of the stream bed of stream si where it crosses z (lowest point across)"""
	var pts: Array = STREAMS[si][0]
	for k in range(pts.size() - 1):
		var a: Vector2 = pts[k]
		var b: Vector2 = pts[k + 1]
		if (z - a.y) * (z - b.y) <= 0.0 and a.y != b.y:
			var p := a.lerp(b, (z - a.y) / (b.y - a.y))
			var lo := INF
			for o in range(-6, 7):
				lo = minf(lo, H(p.x + o, p.y))
			return lo
	return H(GORGE_HEAD.x, z)


# ---- road and trails (ribbons on the ground, in pieces so the far ones are not drawn) ------------------------------------
func _ribbon(pts: PackedVector2Array, hs: PackedFloat32Array, w: float, col: Color, lift: float, vis: float, tk := "road") -> void:
	var mt := StandardMaterial3D.new()
	mt.albedo_color = col
	mt.roughness = 0.95
	var pieces := {}
	for i in range(pts.size() - 1):
		var a := pts[i]
		var b2 := pts[i + 1]
		var key := "%d,%d" % [int(floor(a.x / 200.0)), int(floor(a.y / 200.0))]
		if not pieces.has(key):
			var st0 := SurfaceTool.new()
			st0.begin(Mesh.PRIMITIVE_TRIANGLES)
			pieces[key] = st0
		var st: SurfaceTool = pieces[key]
		var dd := (b2 - a).normalized()
		var nn := Vector2(-dd.y, dd.x) * w * 0.5
		var ya := (hs[i] if not hs.is_empty() else H(a.x, a.y)) + lift
		var yb := (hs[i + 1] if not hs.is_empty() else H(b2.x, b2.y)) + lift
		var q := [Vector3(a.x - nn.x, ya, a.y - nn.y), Vector3(a.x + nn.x, ya, a.y + nn.y), Vector3(b2.x + nn.x, yb, b2.y + nn.y), Vector3(b2.x - nn.x, yb, b2.y - nn.y)]
		if hs.is_empty():                                    # a path: every corner on the ground
			for k in range(4):
				q[k].y = H(q[k].x, q[k].z) + lift
		for k in [0, 2, 1, 0, 3, 2]:
			st.set_normal(Vector3.UP)
			st.add_vertex(q[k])
	for key in pieces:
		var mi: MeshInstance3D = m.add_mesh(tal, (pieces[key] as SurfaceTool).commit(), Vector3.ZERO, mt, tk)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.visibility_range_end = vis
		var th: MeshInstance3D = tal.get_child(tal.get_child_count() - 1)
		th.visibility_range_end = vis


static func dense(pts: Array, step: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in range(pts.size() - 1):
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var L := a.distance_to(b)
		var k := 0.0
		while k < L:
			out.append(a.lerp(b, k / L))
			k += step
	out.append(pts[-1])
	return out


func _roads_and_trails() -> void:
	var rc := Color(0.27, 0.27, 0.28) if season != "winter" else Color(0.55, 0.56, 0.58)    # winter: snow-packed
	var rh := PackedFloat32Array()
	for i in range(road_pts.size()):
		rh.append(road_h[mini(i, road_h.size() - 1)] - 0.05)
	_ribbon(road_pts, rh, 5.6, rc, 0.07, 380.0 if lite else 900.0)
	if season != "winter":
		for side in [-1.0, 1.0]:                             # the white edge lines
			var lp := PackedVector2Array()
			for i in range(road_pts.size()):
				var a := road_pts[i]
				var b2 := road_pts[mini(i + 1, road_pts.size() - 1)] if i + 1 < road_pts.size() else road_pts[i] + (road_pts[i] - road_pts[i - 1])
				var dd := (b2 - a).normalized()
				lp.append(a + Vector2(-dd.y, dd.x) * side * 2.5)
			_ribbon(lp, rh, 0.14, Color(0.85, 0.85, 0.82), 0.09, 140.0 if lite else 260.0)
	var tc := Color(0.42, 0.34, 0.24) if season != "winter" else Color(0.8, 0.82, 0.86)
	for tr in TRAILS:
		_ribbon(dense(tr[1], 3.0), PackedFloat32Array(), [1.3, 0.9, 0.6][int(tr[2])], tc, 0.08, 160.0 if lite else 330.0, "road")
	# parking at the pass and at the alp
	for pk in [[Vector2(100, 775), 30.0, 16.0, 0.3], [Vector2(150, 20), 18.0, 10.0, -1.2]]:
		var c: Vector2 = pk[0]
		var pm := PlaneMesh.new()
		pm.size = Vector2(pk[1], pk[2])
		var mt := StandardMaterial3D.new()
		mt.albedo_color = Color(0.3, 0.3, 0.31) if season != "winter" else Color(0.6, 0.62, 0.64)
		m.add_mesh(tal, pm, Vector3(c.x, H(c.x, c.y) + 0.08, c.y), mt, "road", Vector3(0, float(pk[3]), 0))


# ---- plants and rocks --------------------------------------------------------------------------------------------------
var _busy_pts: Array = []                     # [Vector2, radius] where no tree / rock may stand


func _busy(x: float, z: float) -> bool:
	for b2 in _busy_pts:
		if Vector2(x, z).distance_to(b2[0]) < float(b2[1]):
			return true
	return false


func _near_way(x: float, z: float, w: float) -> bool:
	"""near the road or a trail (checked against a coarse grid made once)"""
	var k := Vector2i(int(floor((x - LO) / 8.0)), int(floor((z - LO) / 8.0)))
	if _waygrid.is_empty():
		_make_waygrid()
	for dj in range(-1, 2):
		for di in range(-1, 2):
			var kk := "%d,%d" % [k.x + di, k.y + dj]
			if _waygrid.has(kk):
				for p in _waygrid[kk]:
					if Vector2(x, z).distance_to(p) < w:
						return true
	return false


static var _waygrid := {}


static func _make_waygrid() -> void:
	var all := PackedVector2Array()
	all.append_array(road_pts)
	for tr in TRAILS:
		all.append_array(dense(tr[1], 3.0))
	for p in all:
		var kk := "%d,%d" % [int(floor((p.x - LO) / 8.0)), int(floor((p.y - LO) / 8.0))]
		if not _waygrid.has(kk):
			_waygrid[kk] = []
		_waygrid[kk].append(p)


func way_dist(x: float, z: float, maxd := 80.0) -> float:
	"""distance to the nearest trail or road (up to maxd)"""
	if _waygrid.is_empty():
		_make_waygrid()
	var best := maxd
	var r := int(ceil(maxd / 8.0))
	var k := Vector2i(int(floor((x - LO) / 8.0)), int(floor((z - LO) / 8.0)))
	for dj in range(-r, r + 1):
		for di in range(-r, r + 1):
			var kk := "%d,%d" % [k.x + di, k.y + dj]
			if _waygrid.has(kk):
				for p in _waygrid[kk]:
					best = minf(best, Vector2(x, z).distance_to(p))
	return best


func _vegetation() -> void:
	_busy_pts = [[HUT, 30.0], [UPPER_HUT, 12.0], [HOSPICE, 30.0], [Vector2(100, 775), 22.0], [CHAPEL, 18.0], [RUIN, 10.0], [BIVOUAC, 8.0],
			[BUNKER, 10.0], [spot_xz, maxf(9.0, place_r + 6.0)], [GORGE_BRIDGE, 14.0], [Vector2(-700, -130), 10.0], [Vector2(-650, 430), 32.0]]
	for v in VIGNETTES:
		_busy_pts.append([Vector2(v[3], v[4]), float(v[5]) + 2.0])
	for vp in VIEWPOINTS:
		_busy_pts.append([vp_xz(vp), 9.0])
	for k in SPOTS:
		_busy_pts.append([Vector2(SPOTS[k][1], SPOTS[k][2]), 7.0])
	var ck := str(lite)
	if not _veg_cache.has(ck):
		_veg_cache[ck] = _veg_lists()
	var raw: Dictionary = _veg_cache[ck]
	var trees := {"larch": [], "arve": [], "spruce": [], "pine_shrub": []}
	var trees_far := {"larch": [], "arve": [], "spruce": [], "pine_shrub": []}
	var rocks := {}
	var near_r := 220.0                                 # obstacles (people, animals, rover) only near the spot
	for e in raw["trees"]:                                 # [kind, x, z, rot, scale]
		var q := Vector2(e[1], e[2])
		if q.distance_to(spot_xz) < maxf(9.0, place_r + 4.0):
			continue
		var it := [P(q.x, q.y, -0.15), e[3], e[4]]
		if q.distance_to(spot_xz) < near_r:
			trees[e[0]].append(it)
		else:
			trees_far[e[0]].append(it)
	for e in raw["rocks"]:                                 # [type|variant, x, z, rot, scale]
		var q := Vector2(e[1], e[2])
		if q.distance_to(spot_xz) < maxf(9.0, place_r + 4.0):
			continue
		var key := "%s|%s" % [e[0], "n" if q.distance_to(spot_xz) < near_r else "f"]
		if not rocks.has(key):
			rocks[key] = []
		rocks[key].append([P(q.x, q.y, -0.2 * float(e[4])), e[3], e[4]])
	_veg_rest(trees, trees_far, rocks)


static var _veg_cache := {}


func _veg_lists() -> Dictionary:
	"""where the trees and rocks stand (valley coordinates) - the same for every spot, made once per season"""
	var r_trees := []
	var r_rocks := []
	var sp := 9.5 if lite else 7.0
	var vr := RandomNumberGenerator.new()
	vr.seed = 77
	var busy0 := _busy_pts.duplicate()
	_busy_pts = busy0.filter(func(b): return (b[0] as Vector2) != spot_xz)
	var z := LO + 4.0
	while z < -LO - 4.0:
		var x := LO + 4.0
		while x < -LO - 4.0:
			var px := x + vr.randf_range(-sp * 0.45, sp * 0.45)
			var pz := z + vr.randf_range(-sp * 0.45, sp * 0.45)
			x += sp
			var h := H(px, pz)
			var zn := zone(px, pz)
			if zn in ["lake", "glacier"]:
				continue
			var sl := slope_deg(px, pz, 2.0)
			var r := vr.randf()
			# rocks: on scree, in the boulder field, below cliffs, high up
			var rock_p := 0.0
			match zn:
				"scree":
					rock_p = 0.18
				"boulders":
					rock_p = 0.55
				"shore":
					rock_p = 0.06
				_:
					rock_p = 0.012 + 0.05 * smoothstep(420.0, 700.0, h) + 0.08 * smoothstep(32.0, 45.0, sl)
			if sl > 50.0:
				rock_p *= 0.2
			if r < rock_p:
				if _busy(px, pz) or _near_way(px, pz, 2.5):
					continue
				var rt := "gneis"
				if px > 300.0:
					rt = "serpentin" if pz < 300.0 else "rost"
				elif px < -350.0 and pz > 0.0:
					rt = "kalk"
				var v := vr.randi() % 3
				var sc := vr.randf_range(0.3, 1.2)
				if zn == "boulders":
					sc = vr.randf_range(1.2, 3.6)
				elif zn == "scree":
					sc = vr.randf_range(0.25, 1.5) * (1.0 + smoothstep(0.0, 1.0, vr.randf()) * 0.8)
				r_rocks.append(["%s|%d" % [rt, v], px, pz, vr.randf() * TAU, sc])
				continue
			if zn in ["moor", "scree", "boulders", "shore", "pasture", "flowers"] or sl > 38.0:
				continue
			var fk := forest_k(px, pz, h)
			var kind := ""
			if r < fk * 0.62:
				if h < 160.0:
					kind = "spruce" if vr.randf() < 0.45 else "larch"
				elif h < 380.0:
					kind = "larch" if vr.randf() < 0.6 else "arve"
				else:
					kind = "arve" if vr.randf() < 0.7 else "larch"
			elif h > 380.0 and h < 640.0 and sl > 12.0 and r < 0.05:
				kind = "pine_shrub"
			if kind == "" or _busy(px, pz) or _near_way(px, pz, 3.5):
				continue
			r_trees.append([kind, px, pz, vr.randf() * TAU, vr.randf_range(0.75, 1.3) * (0.7 if h > 420.0 else 1.0)])
		z += sp
	_busy_pts = busy0
	return {"trees": r_trees, "rocks": r_rocks}


func _veg_rest(trees: Dictionary, trees_far: Dictionary, rocks: Dictionary) -> void:
	var snowy := season == "winter"
	var nt := 0
	for k in trees:
		bib.many(k, trees[k], {"season": season, "snow": snowy})
		bib.many(k, trees_far[k], {"season": season, "snow": snowy, "noob": true})
		nt += trees[k].size() + trees_far[k].size()
	var nr := 0
	for key in rocks:
		var parts: PackedStringArray = key.split("|")
		bib.many("boulder", rocks[key], {"rock": parts[0], "v": int(parts[1]), "snow": snowy, "noob": parts[2] == "f"})
		nr += rocks[key].size()
	info["trees"] = nt
	info["rocks"] = nr
	# flowers and cotton grass (spring / summer), the alp meadow and the moor
	if season in ["fruehling", "sommer"]:
		var fl := []
		for i in range(260 if lite else 700):
			var a := rng.randf() * TAU
			var d := sqrt(rng.randf()) * 65.0
			var q := FLOWERS + Vector2(cos(a), sin(a)) * d
			if not _near_way(q.x, q.y, 1.2):
				fl.append([P(q.x, q.y), rng.randf() * TAU, rng.randf_range(0.8, 1.4)])
		for v in range(3):
			bib.many("flowers", fl.slice(v * fl.size() / 3, (v + 1) * fl.size() / 3), {"v": v})
		var cg := []
		for i in range(220 if lite else 600):
			var a := rng.randf() * TAU
			var d := sqrt(rng.randf()) * 90.0
			var q := MOOR + Vector2(cos(a), sin(a)) * d
			if zone(q.x, q.y) == "moor" and not _near_way(q.x, q.y, 1.0):
				cg.append([P(q.x, q.y), rng.randf() * TAU, rng.randf_range(0.8, 1.3)])
		bib.many("cottongrass", cg, {"season": season})
		info["flowers"] = fl.size()
		info["cottongrass"] = cg.size()
	# spring: avalanche cones at the foot of steep gullies, crocuses on the meadows near the spot
	if season == "fruehling":
		var cones := 0
		for zz in range(-900, 760, 90):
			for sd in [-1.0, 1.0]:
				var x0: float = cx(float(zz)) + sd * 175.0
				for k in range(12):
					var x: float = x0 + sd * k * 8.0
					if slope_deg(x + sd * 12.0, float(zz), 4.0) > 33.0 and slope_deg(x, float(zz), 4.0) < 22.0:
						if rng.randf() < 0.5 and zone(x, float(zz)) != "lake" and not _near_way(x, float(zz), 6.0):
							bib.add("snow_cone", P(x, float(zz), -1.0), rng.randf() * TAU, {"r": rng.randf_range(6.0, 12.0)})
							cones += 1
						break
		info["avalanche_cones"] = cones
		var cr := []
		for i in range(150 if lite else 400):
			var a := rng.randf() * TAU
			var q := spot_xz + Vector2(cos(a), sin(a)) * rng.randf_range(4.0, 160.0)
			if zone(q.x, q.y) in ["meadow", "pasture", "flowers"] and not _near_way(q.x, q.y, 1.0):
				cr.append([P(q.x, q.y), rng.randf() * TAU, rng.randf_range(0.5, 0.9)])
		bib.many("flowers", cr, {"v": 4})                    # (variant 4: violet and white first = crocuses)
	if season == "winter":                                    # the avalanche slope: a sign at the foot (snow caves, ski tourers: next package)
		bib.add("info_board", P(cx(380.0) - 215.0, 380.0), PI / 2.0, {"text": "Achtung Lawinengefahr"})
	# dark pools in the moor
	var pm := StandardMaterial3D.new()
	pm.albedo_color = Color(0.05, 0.07, 0.06) if season != "winter" else Color(0.75, 0.8, 0.84)
	pm.roughness = 0.05 if season != "winter" else 0.4
	pm.metallic = 0.3
	for i in range(9):
		var a := i * 2.4
		var q := MOOR + Vector2(cos(a), sin(a)) * (20.0 + i * 7.0)
		var cyl := CylinderMesh.new()
		cyl.top_radius = rng.randf_range(1.5, 4.0)
		cyl.bottom_radius = cyl.top_radius
		cyl.height = 0.02
		cyl.radial_segments = 14
		m.add_mesh(tal, cyl, P(q.x, q.y, 0.05), pm, "pond", Vector3.ZERO, Vector3(1.0, 1.0, rng.randf_range(0.6, 1.0)))


# ---- places --------------------------------------------------------------------------------------------------------------
func _fence(a: Vector2, b: Vector2, kind: String, seg: float, q := {}) -> void:
	"""a fence / wall from a to b on the ground, with gaps where a trail or the road crosses"""
	var L := a.distance_to(b)
	var n := maxi(1, int(round(L / seg)))
	var rot := atan2(b.x - a.x, b.y - a.y) - PI / 2.0
	var list := []
	for i in range(n):
		var p := a.lerp(b, (i + 0.5) / n)
		if _near_way(p.x, p.y, 2.5) or zone(p.x, p.y) == "lake":
			continue
		list.append([P(p.x, p.y), rot])
	var q2: Dictionary = q.duplicate()
	q2["len"] = L / n
	bib.many(kind, list, q2)


var lift := {}                                # the goods cable car: bottom, top (valley coordinates, cable height)


func _hut_area() -> void:
	# the self-catering hut (nobody there - Daniel: «Selbstversorger»): wood stove, a notice at the door, wood in the shed
	if not orte.replaces("alp_hut"):                       # (bergtal_orte.gd builds the hut with its inside)
		bib.add("alp_hut", P(HUT.x, HUT.y), PI, {"text": "Selbstversorgerhütte Alp Tschuggen", "warm": false})
		var nt := P(HUT.x + 3.6, HUT.y - 3.84, 1.55)
		bib.add("notice", nt, PI, {"text": "Selbstversorgerhütte\nHolz im Schopf, Ofen löschen\nKasse: 15 Fr. pro Nacht\nDanke und gute Tour!"})
	bib.add("woodpile", P(HUT.x - 6.0, HUT.y + 1.0), PI / 2.0, {"len": 3.0})
	bib.add("trough", P(HUT.x + 9.0, HUT.y - 9.0), 0.2, {"len": 3.2, "ice": season == "winter"})
	bib.add("cowshed", P(HUT.x + 30.0, HUT.y + 8.0), PI, {"w": 16.0})
	bib.add("bench", P(HUT.x - 4.0, HUT.y - 9.0), PI)
	# the pasture: wooden fences, old dry stone walls
	var pas := [Vector2(-70, -70), Vector2(150, -70), Vector2(160, 150), Vector2(-60, 150)]
	for i in range(4):
		_fence(HUT + pas[i], HUT + pas[(i + 1) % 4], "fence", 2.5, {"style": "wood", "h": 1.1})
	for w in [[Vector2(-40, -110), Vector2(-5, -150)], [Vector2(-130, 40), Vector2(-90, 110)], [Vector2(170, -30), Vector2(200, 60)], [Vector2(-20, 170), Vector2(60, 200)]]:
		_fence(HUT + w[0], HUT + w[1], "dry_wall", 3.0, {"h": 0.9})
	bib.add("wall_holes", P(104.0, -34.0), 0.6, {"len": 6.0})                     # vignette 31 (stoat)
	# the goods cable car (Materialseilbahn) from the alp up to the upper stone hut; you can ride it (control «bergtal» ride)
	var bot := Vector2(98, 22)
	var top := UPPER_HUT + Vector2(-8, -4)
	var ang := atan2(top.x - bot.x, top.y - bot.y)
	if not orte.replaces("lift_station"):
		bib.add("lift_station", P(bot.x, bot.y), ang + PI)
		bib.add("lift_station", P(top.x, top.y), ang, {"top": true})
	bib.add("stone_hut", P(UPPER_HUT.x, UPPER_HUT.y), PI * 0.8, {"w": 5.0, "d": 4.0})
	bib._part(Bib.B(0.6, 0.5, 0.06, 0.0, 1.4, 2.04, "%ffd9a0", 0, 0, 0, "window"), Transform3D(Basis(Vector3.UP, PI * 0.8), P(UPPER_HUT.x, UPPER_HUT.y)) * Transform3D(Basis(), Vector3(1.2, 0, 0)),
			"window", "far", bib._cell_key(P(UPPER_HUT.x, UPPER_HUT.y)))          # somebody is up there: a light far away at night
	var a3 := P(bot.x, bot.y, 3.6) + Vector3(-sin(ang), 0, -cos(ang)) * 1.6
	var b3 := P(top.x, top.y, 3.6) + Vector3(sin(ang), 0, cos(ang)) * 1.6
	lift = {"a": a3, "b": b3, "len": a3.distance_to(b3)}
	var nseg := 10
	var prev := a3
	for k in range(1, nseg + 1):                           # the cable sags a little
		var t := float(k) / nseg
		var p := a3.lerp(b3, t) - Vector3(0, 0.06 * lift["len"] * 4.0 * t * (1.0 - t) * 0.25, 0)
		for sd in [-0.4, 0.4]:
			var o: Vector3 = Vector3(cos(ang), 0, -sin(ang)) * sd
			bib._part(Bib.ROD(prev + o, p + o, 0.025, "2a2a2a"), Transform3D.IDENTITY, "metal", "far", bib._cell_key(p))
		prev = p
	for t in [0.33, 0.66]:                                 # two masts
		var p2 := a3.lerp(b3, t)
		var g := H(p2.x, p2.z)
		bib._part(Bib.B(0.35, p2.y - g, 0.35, p2.x, g + (p2.y - g) / 2.0, p2.z, "6a6a6a", 0, 0, 0, "metal"), Transform3D.IDENTITY, "metal", "far", bib._cell_key(p2))
	# stepping stones where the Passweg crosses the stream (Bachsteine)
	var sa: Vector2 = STREAMS[0][0][4]
	var sb: Vector2 = STREAMS[0][0][5]
	var tt := _seg_t(Vector2(100, 72), sa, sb)
	var c := sa.lerp(sb, tt.x)
	var dd := (sb - sa).normalized()
	var nn := Vector2(dd.y, -dd.x)
	for k in range(-3, 4):
		var q := c + nn * k * 0.85
		bib.add("stepping_stone", P(q.x, q.y, -0.05), k * 0.7, {"r": 0.32 + 0.05 * (k % 2)})


func _waterfall(top: Vector2, bot: Vector2, w: float) -> void:
	var ht := H(top.x, top.y)
	var hb := H(bot.x, bot.y)
	var fall := ht - hb
	if fall < 5.0:
		return
	var wm := StandardMaterial3D.new()
	wm.albedo_color = Color(0.9, 0.93, 0.96, 0.7) if season != "winter" else Color(0.86, 0.92, 0.97, 1.0)
	wm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if season != "winter" else BaseMaterial3D.TRANSPARENCY_DISABLED
	wm.cull_mode = BaseMaterial3D.CULL_DISABLED
	var qm := QuadMesh.new()
	qm.size = Vector2(w * (1.4 if season == "fruehling" else 1.0) * (0.5 if season == "herbst" else 1.0), fall)
	var mid := top.lerp(bot, 0.55)
	var d := (bot - top).normalized()
	var pos := Vector3(mid.x, hb + fall * 0.5 + 0.5, mid.y)
	var mi: MeshInstance3D = m.add_mesh(tal, qm, pos, wm, "pond", Vector3(-atan2(fall, top.distance_to(bot)) + PI / 2.0, atan2(d.x, d.y), 0))
	mi.visibility_range_end = 1500.0
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if W(pos).length() < 400.0 and season != "winter":
		m.add_sound(-8.0, W(pos), 1.0e7)


func _lake_gorge() -> void:
	var lv := snappedf(level_of(LAKE1) + ALT0, 1.0)
	bib.add("info_board", P(-170.0, -322.0), PI * 0.8, {"text": "Gumpisee %d m ü. M." % int(lv)})
	bib.add("bench", P(-120.0, -322.0), PI * 0.9)
	bib.add("bench", P(30.0, -322.0), PI * 1.15)
	# the suspension bridge over the gorge (people walk over it: «decks»)
	var bx := GORGE_BRIDGE
	var rim := minf(H(bx.x - 13.0, bx.y), H(bx.x + 13.0, bx.y))
	bib.add("rope_bridge", Vector3(bx.x, rim - 1.0, bx.y), PI / 2.0, {"len": 26.0, "sag": 1.4, "w": 1.1})
	decks.append([bx, Vector2(13.0, 0.7), 0.0, rim - 0.6])
	for sd in [-1.0, 1.0]:
		bib.add("hiking_sign", P(bx.x + sd * 15.0, bx.y + 1.5), PI if sd > 0 else 0.0, {"arms": [["Hängebrücke · max. 10 Personen", "", 0]]})
	# more waterfalls: from the east cliff above the lake and from the west cliff (and the one at the head of the gorge)
	var ce := cx(-330.0)
	_waterfall(Vector2(ce + 252.0, -330.0), Vector2(ce + 226.0, -330.0), 2.5)
	var cw := cx(420.0)
	_waterfall(Vector2(cw - 360.0, 420.0), Vector2(cw - 334.0, 420.0), 1.8)
	# echo place and crystal cave (vignettes 9, 10): only the places are kept free; the gorge rim has a warning sign
	bib.add("info_board", P(GORGE_HEAD.x + 18.0, GORGE_HEAD.y - 14.0), PI * 0.6, {"text": "Achtung Absturzgefahr"})


func _pass_area() -> void:
	if not orte.replaces("hospice"):
		bib.add("hospice", P(HOSPICE.x, HOSPICE.y), PI / 2.0, {"text": "Hospiz %d m" % int(H(HOSPICE.x, HOSPICE.y) + ALT0)})
	bib.add("parking_lines", P(100.0, 778.0), 0.3, {"n": 9, "spacing": 2.8, "len": 5.0})
	var cols := ["2b5fa8", "d8d8d8", "a01818", "1a1a1a"]
	for i in range(4):
		if i == 2:
			continue
		bib.add("car", P(100.0 - 11.2 + i * 2.8 * 2.0 * cos(0.3), 778.0 - i * 5.6 * sin(0.3)), 0.3 + PI, {"col": cols[i], "style": ["sedan", "suv", "van", "sedan"][i]})
	var k := _road_index_near(Vector2(62, 790))
	var dirv := (road_pts[mini(k + 3, road_pts.size() - 1)] - road_pts[k]).normalized()
	var nrm := Vector2(-dirv.y, dirv.x)
	var bp := road_pts[k] + nrm * 4.6
	bib.add("postauto", P(bp.x, bp.y), atan2(dirv.x, dirv.y) - PI / 2.0)          # vignette 40 (Daniel 28): the horn is a hook
	postauto_pos = W(P(bp.x, bp.y, 2.0))
	bib.add("hiking_sign", P(bp.x + nrm.x * 3.0, bp.y + nrm.y * 3.0), atan2(dirv.x, dirv.y), {"here": "Furggapass (Postauto)", "arms": [["Alp Tschuggen", _walk_time(PASS, HUT), 1]]})
	bib.add("info_board", P(70.0, 815.0), PI, {"text": "Furggapass %d m ü. M." % int(H(PASS.x, PASS.y) + ALT0)})
	bib.add("bunker", P(BUNKER.x, BUNKER.y), -PI / 2.0, {"rock": "serpentin"})
	# snow poles and guard rails along the road above the alp (hairpins)
	var poles := []
	var rails := []
	for i in range(0, road_pts.size() - 1, 6):
		var p := road_pts[i]
		if p.y < 260.0 or p.y > 900.0:
			continue
		var d2 := (road_pts[mini(i + 1, road_pts.size() - 1)] - p).normalized()
		var n2 := Vector2(-d2.y, d2.x)
		var down := 1.0 if H(p.x + n2.x * 8.0, p.y + n2.y * 8.0) < H(p.x - n2.x * 8.0, p.y - n2.y * 8.0) else -1.0
		var rp := p + n2 * down * 3.5
		var rot := atan2(d2.x, d2.y) - PI / 2.0
		rails.append([Vector3(rp.x, road_h[mini(i, road_h.size() - 1)] - 0.05, rp.y), rot])
		if i % 12 == 0:
			var sp2 := p - n2 * down * 3.4
			poles.append([P(sp2.x, sp2.y), 0.0])
	bib.many("guardrail", rails, {"len": 24.0 * 1.0})
	bib.many("snow_pole", poles, {})
	info["guardrails"] = rails.size()


var postauto_pos := Vector3.ZERO


func postauto_horn() -> Dictionary:
	"""HOOK (vignette 40): the three-tone horn of the Postauto (C♯–E–A, «Tü-ta-to»; the sound itself: a later package) -
	loud for the microphone of MoveEye (≈ 105 dB at 1 m, reaches far in the valley)"""
	m.add_sound(-1.0, postauto_pos, 2.4)
	return {"ok": true, "at": postauto_pos, "dist": snappedf(postauto_pos.length(), 0.1)}


func _road_index_near(p: Vector2) -> int:
	var best := 0
	var bd := INF
	for i in range(road_pts.size()):
		var d := road_pts[i].distance_squared_to(p)
		if d < bd:
			bd = d
			best = i
	return best


func _lower_valley() -> void:
	if not orte.replaces("chapel"):
		bib.add("chapel", P(CHAPEL.x, CHAPEL.y), PI)
	bib.add("bench", P(CHAPEL.x - 4.0, CHAPEL.y - 6.0), PI)
	bib.add("summit_cross", P(CHAPEL.x + 8.0, CHAPEL.y - 3.0), PI, {"h": 2.6})
	# the power line along the road (north part): masts every 160 m, three wires
	var prev = null
	var i := 0
	var masts := []
	while i < road_pts.size():
		var p := road_pts[i]
		if p.y > -120.0:
			break
		var d2 := (road_pts[mini(i + 1, road_pts.size() - 1)] - p).normalized()
		var mp := p + Vector2(d2.y, -d2.x) * -24.0
		var rot := atan2(d2.x, d2.y)
		masts.append([P(mp.x, mp.y), rot])
		var hb := H(mp.x, mp.y)
		var tips := []
		for off in [Vector3(-4.5, 18.7, 0), Vector3(4.5, 18.7, 0), Vector3(0, 24.2, 0)]:
			tips.append(Vector3(mp.x, hb, mp.y) + Basis(Vector3.UP, rot + PI / 2.0) * off)
		if prev != null:
			for w in range(3):
				var a: Vector3 = prev[w]
				var b2: Vector3 = tips[w]
				var mid := (a + b2) * 0.5 - Vector3(0, 3.5, 0)
				bib._part(Bib.ROD(a, mid, 0.03, "2a2a2a"), Transform3D.IDENTITY, "metal", "far", bib._cell_key(mid))
				bib._part(Bib.ROD(mid, b2, 0.03, "2a2a2a"), Transform3D.IDENTITY, "metal", "far", bib._cell_key(mid))
		prev = tips
		i += 40                                            # 40 × 4 m
	bib.many("pylon", masts, {"h": 24.0})
	info["pylons"] = masts.size()
	# the clearing in the larch forest
	bib.add("woodpile", P(CLEARING.x + 12.0, CLEARING.y + 10.0), 0.7, {"len": 4.0})
	bib.add("bench", P(CLEARING.x - 10.0, CLEARING.y + 6.0), 2.4)


func _side_valleys() -> void:
	bib.add("ruin", P(RUIN.x, RUIN.y), 0.4)
	bib.add("bench", P(LAKE2[0].x + 40.0, LAKE2[0].y + 40.0), PI * 1.2)
	# the old dairy (Sennerei, vignette 43 / Daniel 31) with a very old cheese
	if not orte.replaces("dairy"):                          # (bergtal_orte.gd: the dairy with its inside, the cheese on the shelf)
		bib.add("stone_hut", P(-700.0, -130.0), 0.3, {"w": 7.0, "d": 5.0})
		bib.add("cheese_wheel", P(-698.5, -127.0, 0.02), 0.0)
	if not orte.replaces("bivouac"):
		bib.add("bivouac", P(BIVOUAC.x, BIVOUAC.y), PI * 0.9, {"text": "Biwak Chüebodehorn"})
	for o in [Vector2(-5, 6), Vector2(4, 7), Vector2(0, 9)]:
		bib.add("boulder", P(BIVOUAC.x + o.x, BIVOUAC.y + o.y, -0.6), rng.randf() * TAU, {"r": 2.4, "rock": "kalk", "v": 2, "snow": season == "winter"})
	# the glacier: crevasses (dark ribbons across the tongue)
	var ax := (Vector2(1100.0, 540.0) - Vector2(680.0, 445.0)).normalized()
	var nx := Vector2(-ax.y, ax.x)
	for k in range(16):
		var c := Vector2(700.0, 450.0) + ax * (20.0 + k * 22.0) + nx * rng.randf_range(-25.0, 25.0)
		var L := rng.randf_range(14.0, 46.0)
		var bend := rng.randf_range(-0.25, 0.25)
		var pts := PackedVector2Array()
		for t in range(7):
			var u := (t / 6.0 - 0.5) * L
			pts.append(c + nx * u + ax * bend * u * u / L)
		if _glacier_k(c.x, c.y) > 0.5:
			_ribbon(pts, PackedFloat32Array(), rng.randf_range(0.6, 1.4), Color(0.06, 0.12, 0.2), 0.05, 700.0, "stone")
	# the cairn plateau («Steinmann-Wald», vignette 42): many small cairns
	var cl := []
	for k in range(80 if lite else 210):
		var a := rng.randf() * TAU
		var q := Vector2(-650.0, 430.0) + Vector2(cos(a), sin(a)) * sqrt(rng.randf()) * 30.0
		cl.append([P(q.x, q.y), rng.randf() * TAU, rng.randf_range(0.5, 1.4)])
	bib.many("cairn", cl, {})
	# the via ferrata (Klettersteig) up the west cliff: steel cable, iron rungs, a ladder at the steepest part
	var zf := 200.0
	var cwf := cx(zf)
	var a0 := Vector2(cwf - 334.0, zf)
	var a1 := Vector2(cwf - 362.0, zf + 4.0)
	var prevp := Vector3.ZERO
	for k in range(41):
		var t := k / 40.0
		var q := a0.lerp(a1, t)
		var p := P(q.x, q.y, 1.1)
		var face := Vector3(1, 0, 0) * 0.35
		if k > 0:
			bib._part(Bib.ROD(prevp + face, p + face, 0.02, "9a9a9a"), Transform3D.IDENTITY, "metal", "mid", bib._cell_key(p))
		if k % 2 == 0:
			bib._part(Bib.B(0.04, 0.04, 0.45, p.x + 0.25, p.y - 0.8, p.z, "6a6a6a", 0, 0, 0, "metal"), Transform3D.IDENTITY, "metal", "small", bib._cell_key(p))
		prevp = p
	var l0 := P(a0.lerp(a1, 0.45).x, a0.lerp(a1, 0.45).y)
	var l1 := P(a0.lerp(a1, 0.62).x, a0.lerp(a1, 0.62).y)
	for sd in [-0.25, 0.25]:
		bib._part(Bib.ROD(l0 + Vector3(0.4, 0, sd), l1 + Vector3(0.4, 0, sd), 0.03, "8a8a8a"), Transform3D.IDENTITY, "metal", "mid", bib._cell_key(l0))
	for k in range(int(l0.distance_to(l1) / 0.35)):
		var p := l0.lerp(l1, k * 0.35 / l0.distance_to(l1)) + Vector3(0.4, 0, 0)
		bib._part(Bib.B(0.03, 0.03, 0.5, p.x, p.y, p.z, "8a8a8a", 0, 0, 0, "metal"), Transform3D.IDENTITY, "metal", "small", bib._cell_key(p))
	bib.add("hiking_sign", P(a0.x + 4.0, a0.y - 2.0), PI / 2.0, {"here": "Klettersteig Gratspitz (K3)", "arms": [["Gratspitz", "1 h 30 min", 2]]})
	via_ferrata = [a0, a1]


var via_ferrata := []


func _viewpoints() -> void:
	var vps := []
	for vp in VIEWPOINTS:
		var c := vp_xz(vp)
		var yaw := deg_to_rad(float(vp[6]))
		var fwd := Vector2(sin(yaw), -cos(yaw))
		var back := c - fwd * 2.5
		match str(vp[5]):
			"bank_kreuz":
				bib.add("summit_cross", P(c.x + fwd.x * 1.5, c.y + fwd.y * 1.5), PI - yaw, {"h": 4.0})
				bib.add("summit_box", P(c.x + fwd.x * 1.5, c.y + fwd.y * 1.5), PI - yaw)
				bib.add("bench", P(back.x, back.y), PI - yaw)
			"fernrohr":
				bib.add("coin_telescope", P(c.x, c.y), PI - yaw)
				bib.add("bench", P(back.x - fwd.y * 2.0, back.y + fwd.x * 2.0), PI - yaw)
			"tafel":
				bib.add("panorama_board", P(c.x, c.y), -yaw, {"peaks": _peaks_seen(c, float(vp[6]))})
				bib.add("bench", P(back.x, back.y), PI - yaw)
			_:
				bib.add("cairn", P(c.x + fwd.x, c.y + fwd.y), 0.0, {"h": 1.4})
				bib.add("boulder", P(c.x - fwd.y * 3.0, c.y + fwd.x * 3.0, -0.4), 0.7, {"r": 1.1, "v": 1, "snow": season == "winter"})
		var wp := WG(c.x, c.y)
		vps.append({"id": vp[0], "name": vp[1], "kind": vp[2], "furnishing": vp[5], "x": snappedf(wp.x, 0.1), "z": snappedf(wp.z, 0.1), "y": snappedf(wp.y, 0.1),
				"alt_m": int(H(c.x, c.y) + ALT0), "look_deg": vp[6], "peaks": _peaks_seen(c, float(vp[6]))})
	s.data["bt_viewpoints"] = vps


func _peaks_seen(c: Vector2, look: float) -> Array:
	"""the far peaks within ± 75° of the view, left to right: [[name, m ü. M.]]"""
	var out := []
	for pk in PEAKS:
		var az := deg_to_rad(float(pk[1]))
		var pp := Vector2(sin(az), -cos(az)) * float(pk[3])
		var a2 := rad_to_deg(atan2((pp - c).x, -(pp - c).y))
		var da := wrapf(a2 - look, -180.0, 180.0)
		if absf(da) < 75.0:
			out.append([da, str(pk[0]), int(float(pk[2]) + ALT0 + 300.0)])
	out.sort_custom(func(a, b): return a[0] < b[0])
	return out.map(func(e): return [e[1], e[2]])


func _vignette_pieces() -> void:
	"""the static pieces of some approved vignettes (the animations come in the next package)"""
	bib.add("tennis_ball", P(-58.0, 230.0, 0.0), 0.0)                              # 29 Murmeltier-Fussball (Daniel 17)
	bib.add("picnic_set", P(-10.0, -296.0), 0.4)                                   # 38 Picknick (26)
	bib.add("fondue_pot", P(-175.0, -300.0), 1.0)                                  # 8 Fondue-Caquelon
	if season in ["sommer", "herbst"]:
		bib.add("wood_ski", P(830.0, 485.0, -0.25), 0.8)                           # 44 Holzski (32) - melts out in summer
	bib.add("lantern_old", P(760.0, 460.0, -0.35), 0.2)                            # 16 the lantern in the crevasse
	for bp in [Vector2(-80, 222), Vector2(-62, 240), Vector2(-40, 215), Vector2(-100, 198)]:
		bib.add("burrow", P(bp.x, bp.y), rng.randf() * TAU)                         # 1 / 29 marmot burrows
	# burrows near the spot (the marmots of the spot disappear into them)
	_burrows.clear()
	if H(spot_xz.x, spot_xz.y) < 650.0 and season != "winter":
		for k in range(3):
			for tries in range(12):
				var a := rng.randf() * TAU
				var q := spot_xz + Vector2(cos(a), sin(a)) * rng.randf_range(25.0, 70.0)
				if zone(q.x, q.y) in ["meadow", "pasture", "flowers", "boulders"] and slope_deg(q.x, q.y) < 28.0 and not _near_way(q.x, q.y, 3.0):
					bib.add("burrow", P(q.x, q.y), rng.randf() * TAU)
					_burrows.append(WG(q.x, q.y))
					break


func _walk_time(a: Vector2, b: Vector2) -> String:
	"""the walking time like on the signposts (Schweizer Wanderwege: 4.2 km/h, + 1 h per 300 m up / 500 m down, the bigger
	part + half the smaller - simplified); the way is ≈ 1.3 × the straight line"""
	var dist := a.distance_to(b) * 1.3 / 1000.0
	var dh := H(b.x, b.y) - H(a.x, a.y)
	var t1 := dist / 4.2
	var t2 := (dh / 300.0) if dh > 0.0 else (-dh / 500.0)
	var t := maxf(t1, t2) + minf(t1, t2) / 2.0
	var mins := int(round(t * 60.0 / 5.0) * 5.0)
	if mins < 60:
		return "%d min" % maxi(5, mins)
	return "%d h %02d min" % [mins / 60, mins % 60] if mins % 60 != 0 else "%d h" % (mins / 60)


func _signs_and_cairns() -> void:
	var junctions := [["Alp Tschuggen %d m", HUT + Vector2(-10, -14), [["Gumpisee", LAKE1[0], 0], ["Furggapass", PASS, 1], ["Biwak Chüebodehorn", BIVOUAC, 1]]],
			["Gumpisee %d m", Vector2(-200, -326), [["Alp Tschuggen", HUT, 0], ["Schwarzseeli", LAKE2[0], 0], ["Kapelle St. Jodern", CHAPEL, 0]]],
			["Tschuggen Strasse", Vector2(174, -46), [["Alp Tschuggen", HUT, 0], ["Gumpisee", LAKE1[0], 0]]],
			["Murmelboden %d m", Vector2(-296, 294), [["Gratspitz", RIDGE_VIEW, 1], ["Biwak Chüebodehorn", BIVOUAC, 1], ["Alp Tschuggen", HUT, 1]]],
			["Gratspitz %d m", RIDGE_VIEW + Vector2(6, 8), [["Murmelboden", BOULDERS, 1], ["Alp Tschuggen", HUT, 1]]],
			["Furggapass %d m", Vector2(34, 776), [["Alp Tschuggen", HUT, 1], ["Gumpisee", LAKE1[0], 1]]],
			["Abzweigung Wyssgletscher", Vector2(186, 136), [["Gletscherseeli", TARN[0], 2], ["Obri Stafel", UPPER_HUT, 2], ["Alp Tschuggen", HUT, 0]]],
			["St. Jodern %d m", CHAPEL + Vector2(14, 12), [["Gumpisee", LAKE1[0], 0], ["Tschuggen Strasse", Vector2(174, -46), 0]]],
			["Riedmoos %d m", Vector2(-470, -236), [["Altstafel", RUIN, 0], ["Gumpisee", LAKE1[0], 0]]],
			["Tüfelsschlund", Vector2(GORGE_BRIDGE.x + 18, -168), [["Alp Tschuggen", HUT, 0], ["Gumpisee", LAKE1[0], 0]]]]
	var signs := []
	for jn in junctions:
		var pos: Vector2 = jn[1]
		var arms := []
		for a in jn[2]:
			arms.append([a[0], _walk_time(pos, a[1]), a[2]])
		var here := str(jn[0])
		if here.contains("%d"):
			here = here % int(H(pos.x, pos.y) + ALT0)
		bib.add("hiking_sign", P(pos.x, pos.y), rng.randf() * TAU, {"here": here, "arms": arms})
		signs.append({"here": here, "x": pos.x, "z": pos.y})
	info["signposts"] = signs.size()
	# marks on stones along the trails (yellow / white-red-white / white-blue-white) and cairns high up
	var marks := [[], [], []]
	var cairns := []
	for tr in TRAILS:
		var lvl := int(tr[2])
		var pts := dense(tr[1], 4.0)
		for i in range(6, pts.size(), 10 if not lite else 20):
			var p := pts[i]
			var d2 := (pts[mini(i + 1, pts.size() - 1)] - pts[i - 1]).normalized()
			var side := Vector2(-d2.y, d2.x) * (1.4 if i % 20 < 10 else -1.4)
			var q := p + side
			marks[lvl].append([P(q.x, q.y, -0.1), atan2(-side.x, -side.y)])
			if lvl > 0 and H(p.x, p.y) > 420.0 and i % 30 == 6:
				var q2 := p - side * 1.3
				cairns.append([P(q2.x, q2.y), rng.randf() * TAU, rng.randf_range(0.8, 1.3)])
	for lvl in range(3):
		bib.many("trail_mark", marks[lvl], {"level": lvl})
	bib.many("cairn", cairns, {})
	info["cairns"] = cairns.size()


# ---- your sleeping place ---------------------------------------------------------------------------------------------------
const BED_AT := Vector3(2.4, 0, 2.2)          # world: the bed beside and behind MoveEye (it looks out over the place)
const PACK_AT := Vector3(-1.4, 0, -2.3)       # the backpack and the food in front of the camera (stranger, fox, choughs)
const FOOD_AT := Vector3(1.6, 0, -3.3)


func _own_node(kind: String, wp: Vector3, rot: float, q := {}) -> Node3D:
	var d: Dictionary = bib.make(kind, q)
	var vp := V(wp)
	var xf := Transform3D(Basis(Vector3.UP, rot - tal.rotation.y), Vector3(vp.x, H(vp.x, vp.z), vp.z))
	var n: Node3D = bib._node_thing(d, xf, kind)
	bib.stats["animals"] -= 1
	bib._extras(d, xf, rot - tal.rotation.y)
	for c in n.get_children():
		if c is GeometryInstance3D:
			(c as GeometryInstance3D).visibility_range_end = 0.0
	return n


const BEDS := [["tent", "Kuppelzelt"], ["tent1", "Einmannzelt"], ["tarp", "Tarp mit Isomatte"], ["bivy", "Biwaksack + Isomatte"], ["mat", "Isomatte + Schlafsack (offen)"]]
# MoveEye's mount at the spot (Daniel): height of the camera head and what it stands on
const MOUNTS := {"stativ": ["Auf dem Stativ (Höhe frei, 1,5 m)", 1.5], "rucksack": ["Auf dem Rucksack (tief, nah)", 0.62], "stein": ["Auf einem Stein (erhöht)", 1.15],
		"zelt": ["Am Zelt (beim Eingang)", 1.0], "baum": ["An einem Baum / Pfosten befestigt", 2.4]}


func _own_spot() -> void:
	var tent := bed in ["tent", "tent1"]
	var mount := str(m.get("bt_mount")) if m.get("bt_mount") != null else "stativ"
	if not MOUNTS.has(mount):
		mount = "stativ"
	var bed_at := BED_AT
	var pack_at := PACK_AT
	match mount:
		"zelt":
			bed_at = Vector3(0.0, 0, 1.7)                     # MoveEye at the entrance of the tent
		"rucksack":
			pack_at = Vector3.ZERO                             # MoveEye sits on the backpack
	var kind: String = {"tent": "bed_tent", "tent1": "bed_tent1", "tarp": "bed_tarp", "bivy": "bed_bivy"}.get(bed, "bed_mat")
	_bed_node = _own_node(kind, bed_at, PI if mount == "zelt" else (0.5 if tent else 0.3), {"col": "e86a1a" if bed == "tent" else ("3a7a3a" if bed == "tent1" else "2a5ab0")})
	_pack_node = _own_node("backpack", pack_at, 0.4)
	_food_node = _own_node("food_bag", FOOD_AT, 0.0)
	var hr: float = m.hour()
	if bool(m.get("bt_stove")):                               # the stove: hot in the evening and in the morning (cooking)
		_own_node("stove", bed_at + Vector3(-1.1, 0, -0.6), 0.0, {"hot": (hr > 18.5 and hr < 20.5) or (hr > 6.5 and hr < 7.5)})
	match mount:
		"stein":
			var n := _own_node("boulder", Vector3.ZERO, 0.4, {"r": 0.75, "v": 2, "noob": true})
			n.position.y -= 0.25
		"stativ":
			_own_node("tripod", Vector3.ZERO, 0.0, {"h": 1.3})
		"baum":
			var tr := _own_node("arve" if H(spot_xz.x, spot_xz.y) > 300.0 else "larch", Vector3(0.45, 0, 0.35), 0.0, {"season": season, "noob": true})
			tr.scale = Vector3.ONE * 0.8
	m.set_mast(float(MOUNTS[mount][1]))
	info["mount"] = mount
	if bool(m.get("bt_wall")):                                # a wind wall of stones on the side of the main wind (W / SW)
		var wa := deg_to_rad(235.0) + tal.rotation.y
		for k in range(9):
			var a := wa + (k - 4) * 0.28
			var wp := bed_at + Vector3(sin(a), 0, -cos(a)) * 2.1
			var vq := V(wp)
			bib.add("dry_wall", P(vq.x, vq.z), a - tal.rotation.y, {"len": 0.75, "h": 0.8})
	var bw: Vector3 = _bed_node.global_position if _bed_node.is_inside_tree() else W(V(bed_at))
	m.obj["pir"] = bw
	m.test_props["Zelt" if tent else "Schlafplatz"] = _bed_node
	m.test_props["Rucksack"] = _pack_node
	m.test_props["Proviant"] = _food_node
	# the door: the zip of the tent (door sensor) / the foot of the sleeping bag
	m.door_node = Node3D.new()
	_bed_node.add_child(m.door_node)
	m.door_node.position = Vector3(0, 0, 1.05) if tent else Vector3(0, 0, 1.0)
	var flap := MeshInstance3D.new()
	flap.mesh = m.box(0.6, 0.6, 0.02)
	flap.position = Vector3(0.3, 0.32, 0)
	flap.material_override = m.mat(Color(0.2, 0.2, 0.2))
	m.door_node.add_child(flap)
	s.door_light_at(_bed_node, Vector3(0, 0.9 if tent else 0.5, 1.6))      # light from the tent when the zip opens (headlamp)
	var lamp := MeshInstance3D.new()                       # the small lamp at the bed (main.window_mat: glows at night)
	lamp.mesh = m.box(0.08, 0.12, 0.08)
	lamp.position = Vector3(0.35, 0.06, 0.7)
	lamp.material_override = s.window_mat()
	_bed_node.add_child(lamp)
	m.obj["door"] = bw + (_bed_node.global_transform.basis * Vector3(0, 0, 1.8) if _bed_node.is_inside_tree() else Vector3(0, 0, 1.8))
	m.obj["bike"] = pack_at                               # the thief tests take the backpack (there is no bike up here)
	m.bike_node = null
	s.data["platz"] = [bw, 6.0]
	s.data["nachbarn"] = []


# ---- lights, smoke, flags, labels -------------------------------------------------------------------------------------------
func _lights_and_fx() -> void:
	var near := []
	for l in bib.lamps:
		var wp := W(l[0])
		if wp.length() < 350.0:
			near.append([wp.length(), l])
	near.sort_custom(func(a, b): return a[0] < b[0])
	var nmax := 3 if lite else 6
	for i in range(mini(nmax, near.size())):
		var l: Array = near[i][1]
		var ol := OmniLight3D.new()
		ol.position = l[0]
		ol.light_color = l[1]
		ol.omni_range = 10.0
		ol.light_energy = 0.0
		tal.add_child(ol)
		m.lamps.append(ol)
	info["lights"] = mini(nmax, near.size())
	var smokes := 0
	var flags := 0
	for f in bib.fx:
		var wp := W(f[1])
		match str(f[0]):
			"smoke":
				if wp.length() < 400.0 and smokes < (1 if lite else 2):
					s.smoke(wp)
					smokes += 1
			"flag":
				if wp.length() < 300.0 and flags < 2:
					s.flag(wp, Bib.cc(f[2] if f[2] != null else "c8102e"))
					flags += 1


func _labels() -> void:
	"""names of the places and the suggested sleeping spots - only in the window (helper layer), not for MoveEye's cameras"""
	var items := []
	for pl in PLACES + Orte.PLACES:
		items.append([str(pl[0]), Vector2(pl[1], pl[2]), Color(0.98, 0.96, 0.9), 5.0])
	for k in SPOT_ORDER:
		if SPOTS.has(k) and k != spot:
			items.append(["Schlafplatz: " + str(SPOTS[k][0]), Vector2(SPOTS[k][1], SPOTS[k][2]), Color(1.0, 0.85, 0.4), 3.0])
	for vp in VIEWPOINTS:
		items.append(["Aussicht: " + str(vp[1]), vp_xz(vp), Color(0.7, 0.9, 1.0), 4.0])
	for it in items:
		var p := P((it[1] as Vector2).x, (it[1] as Vector2).y)
		if W(p).length() > 700.0 or W(p).length() < 30.0:
			continue
		var l := Label3D.new()
		l.text = T.t(str(it[0]))
		l.position = p + Vector3(0, float(it[3]), 0)
		l.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
		l.font_size = 72
		l.pixel_size = 0.014
		l.modulate = it[2]
		l.outline_size = 10
		l.outline_modulate = Color(0.1, 0.12, 0.1)
		l.visibility_range_end = 450.0
		l.layers = m.HELPER_LAYER
		tal.add_child(l)


# =======================================================================================================================
# the evaluation of a sleeping place (wind, rockfall, animals, strangers, view, stars, quiet)
# =======================================================================================================================
static func flat_limit(kind: String) -> float:
	"""steepest ground for sleeping: a tent ≈ 8° (more: you slide, the floor is not tight), tarp / mat ≈ 10°, bivy bag 12°"""
	return {"tent": 8.0, "tent1": 8.0, "tarp": 10.0, "bivy": 12.0}.get(kind, 10.0)


func ground_slope(x: float, z: float) -> float:
	"""the slope under a bed of 2.5 m (the steepest of five points)"""
	var mx := slope_deg(x, z, 1.25)
	for o in [Vector2(1.2, 0), Vector2(-1.2, 0), Vector2(0, 1.2), Vector2(0, -1.2)]:
		mx = maxf(mx, slope_deg(x + o.x, z + o.y, 1.25))
	return mx


func evaluate(x: float, z: float) -> Dictionary:
	var h := H(x, z)
	var p0 := Vector2(x, z)
	# wind: how much higher than the surroundings (TPI), how sheltered (horizon in the first 60 m), the main wind from W / SW / S
	var sum := 0.0
	var n := 0
	for r in [40.0, 120.0, 300.0]:
		for k in range(12):
			var a := TAU * k / 12.0
			sum += H(x + cos(a) * r, z + sin(a) * r)
			n += 1
	var tpi := h - sum / n
	var shelter := 0.0
	var hor := []
	var depr := []
	for k in range(24):
		var az := TAU * k / 24.0
		var d := Vector2(sin(az), -cos(az))
		var near_max := -90.0
		var r := 6.0
		while r <= 60.0:
			near_max = maxf(near_max, rad_to_deg(atan2(H(x + d.x * r, z + d.y * r) - h - 1.0, r)))
			r += 6.0
		var wdir := absf(wrapf(rad_to_deg(az) - 235.0, -180.0, 180.0)) < 70.0     # W / SW (and south: Föhn)
		shelter += (1.0 if near_max > 12.0 else (0.5 if near_max > 5.0 else 0.0)) * (2.0 if wdir else 1.0)
		var far_max := near_max
		var low := 90.0
		r = 60.0
		while r < 1500.0:
			var ang := rad_to_deg(atan2(H(x + d.x * r, z + d.y * r) - h - 1.5, r))
			far_max = maxf(far_max, ang)
			if r < 700.0:
				low = minf(low, ang)
			r += 25.0 if r < 300.0 else 80.0
		hor.append(far_max)
		depr.append(low)
	shelter /= 32.0
	var wind_k := clampf(0.45 + tpi / 45.0 - shelter * 0.6 + smoothstep(350.0, 800.0, h) * 0.2, 0.0, 1.0)
	# rockfall (Fahrböschung: stones reach places from where the source is seen steeper than ≈ 30–33°;
	# Heim 1932, Onofri & Candian 1979 - simplified): a steep cliff (> 40°) above, seen steeper than 30°
	var rock := 0.0
	for k in range(24):
		var a := TAU * k / 24.0
		var r := 15.0
		while r < 260.0:
			var q := Vector2(x + cos(a) * r, z + sin(a) * r)
			var dh := H(q.x, q.y) - h
			if dh > 12.0:
				var ang := rad_to_deg(atan2(dh, r))
				var g := grad(q.x, q.y)
				var fall := -g.normalized() if g.length() > 0.01 else Vector2.ZERO
				var to_spot := (p0 - q).normalized()
				if ang > 30.0 and slope_deg(q.x, q.y, 3.0) > 40.0 and fall.dot(to_spot) > 0.6:    # the fall line points at the spot
					rock = maxf(rock, smoothstep(30.0, 38.0, ang) * (1.0 - r / 300.0) * smoothstep(0.6, 0.9, fall.dot(to_spot)))
			r += 10.0
	var zn := zone(x, z)
	if zn == "scree":
		rock = maxf(rock, 0.5)
	# animals at the lake (they come to drink), strangers on the trails and the road
	var lake_k := 0.0
	for lk in LAKES:
		lake_k = maxf(lake_k, 1.0 - smoothstep(1.0, 1.7, _ell(p0, lk)))
	var wd := way_dist(x, z, 150.0)
	var road_d := INF
	for i in range(0, road_pts.size(), 3):
		road_d = minf(road_d, road_pts[i].distance_to(p0))
	var strangers := maxf(1.0 - smoothstep(8.0, 120.0, wd), 0.8 * (1.0 - smoothstep(20.0, 250.0, road_d)))
	strangers = maxf(strangers, 0.6 * (1.0 - smoothstep(60.0, 220.0, p0.distance_to(HOSPICE))))
	# view and stars
	var hsum := 0.0
	var dsum := 0.0
	for k in range(hor.size()):
		hsum += maxf(0.0, float(hor[k]))
		dsum += maxf(0.0, -float(depr[k]))
	hsum /= hor.size()
	dsum /= depr.size()
	var view_k := clampf(dsum / 10.0, 0.0, 1.0) * 0.65 + clampf((22.0 - hsum) / 22.0, 0.0, 1.0) * 0.35
	var light := 1.0 - smoothstep(80.0, 400.0, p0.distance_to(HOSPICE))
	var stars_k := clampf(1.0 - hsum / 40.0, 0.0, 1.0) * (1.0 - 0.5 * light)
	# quiet: water, cows, people, wind
	var water := 0.0
	for st in STREAMS:
		for q in dense(st[0], 12.0):
			water = maxf(water, 0.45 * (1.0 - smoothstep(10.0, 60.0, q.distance_to(p0))))
	water = maxf(water, 0.75 * (1.0 - smoothstep(30.0, 250.0, p0.distance_to(GORGE_HEAD))))
	var cows := 0.5 * (1.0 - smoothstep(120.0, 320.0, p0.distance_to(HUT))) if season in ["sommer", "herbst"] else 0.0
	var quiet := 1.0 - clampf(maxf(maxf(water, cows), maxf(strangers * 0.7, wind_k * 0.5)), 0.0, 1.0)
	var lightning := clampf(smoothstep(10.0, 40.0, tpi) * smoothstep(380.0, 650.0, h), 0.0, 1.0)
	var danger := maxf(maxf(rock, strangers * 0.55), maxf(lake_k * 0.35, lightning * 0.6))
	var cold := -2.0 - 6.0 * wind_k + clampf(tpi / 8.0, -4.0, 0.0)      # °C: wind chill and the cold air lake in hollows
	var notes := []
	if rock > 0.4:
		notes.append("Steinschlag-Gefahr: Felswand oberhalb")
	if lake_k > 0.4:
		notes.append("Am Wasser: Tiere kommen trinken, nachts feucht und kalt")
	if strangers > 0.5:
		notes.append("Nahe am Weg: es kommen Leute vorbei")
	if wind_k > 0.65:
		notes.append("Ausgesetzt: viel Wind, bei Gewitter gefährlich" if lightning > 0.4 else "Ausgesetzt: viel Wind")
	elif shelter > 0.45:
		notes.append("Gut geschützt vor Wind")
	if view_k > 0.6:
		notes.append("Schöne Aussicht")
	if stars_k > 0.75:
		notes.append("Weiter Himmel: viele Sterne")
	if water > 0.5:
		notes.append("Rauschendes Wasser (laut)")
	return {"x": snappedf(x, 0.1), "z": snappedf(z, 0.1), "alt_m": int(h + ALT0), "zone": zn, "slope_deg": snappedf(ground_slope(x, z), 0.1),
			"wind": snappedf(wind_k, 0.01), "shelter": snappedf(shelter, 0.01), "tpi_m": snappedf(tpi, 0.1), "rockfall": snappedf(rock, 0.01),
			"animals": snappedf(maxf(lake_k, 0.3 if zn in ["meadow", "pasture", "flowers"] else 0.1), 0.01), "strangers": snappedf(strangers, 0.01),
			"lightning": snappedf(lightning, 0.01), "view": snappedf(view_k, 0.01), "stars": snappedf(stars_k, 0.01), "quiet": snappedf(quiet, 0.01),
			"cold_c": snappedf(cold, 0.1), "sicherheit": clampi(int(round(5.0 - 4.0 * danger)), 1, 5), "aussicht": clampi(int(round(1.0 + 4.0 * view_k)), 1, 5),
			"ruhe": clampi(int(round(1.0 + 4.0 * quiet)), 1, 5), "notes": notes}


func _shelter_k() -> float:
	"""what the bed and the wind wall protect from wind and rain (0 = nothing, 1 = fully)"""
	var k: float = {"tent": 0.5, "tent1": 0.5, "tarp": 0.3, "bivy": 0.2}.get(bed, 0.0)
	if bool(m.get("bt_wall")):
		k += 0.25
	return clampf(k, 0.0, 0.8)


func exposure() -> Dictionary:
	"""HOOK for weather / battery / camera (Daniel: «ungeschützt = mehr Wind, Regen, Kälte»): factors of the sleeping spot.
	wind_k 0 … 1 (× wind at the device), rain_k (× rain on the lens), cold_c (°C added to the air temperature at night),
	lightning (ridge / summit), rockfall, animals, strangers. Also as Engine-free meta: main.get_meta("platz_exposure")."""
	var r := rating
	var wall := 0.35 if bool(m.get("bt_wall")) else 0.0
	return {"spot": spot, "bed": bed, "bed_shelter": _shelter_k(), "wind_wall": bool(m.get("bt_wall")), "bag": str(m.get("bt_bag")),
			"wind_k": snappedf(float(r.get("wind", 0.5)) * (1.0 - wall), 0.01), "rain_k": snappedf(clampf(0.4 + 0.6 * float(r.get("wind", 0.5)) - 0.3 * float(r.get("shelter", 0.0)), 0.0, 1.0), 0.01),
			"cold_c": r.get("cold_c", 0.0), "lightning": r.get("lightning", 0.0), "rockfall": r.get("rockfall", 0.0), "animals": r.get("animals", 0.0),
			"strangers": r.get("strangers", 0.0), "alt_m": r.get("alt_m", 0)}


func _publish() -> void:
	var ex := exposure()
	s.data["exposure"] = ex
	m.set_meta("platz_exposure", ex)
	var orte := []
	for pl in PLACES:
		var wp := WG(pl[1], pl[2])
		orte.append([str(pl[0]), snappedf(wp.x, 0.1), snappedf(wp.z, 0.1), snappedf(Vector2(wp.x, wp.z).length(), 0.1)])
	s.data["orte"] = orte
	# the map (minimap.gd): suggested spots (yellow), viewpoints (blue), places (white); click = fly there
	var marks := []
	for k in SPOT_ORDER:
		if SPOTS.has(k):
			marks.append([WG(SPOTS[k][1], SPOTS[k][2]), str(SPOTS[k][0]), Color(1.0, 0.8, 0.25), k == spot])
	for vp in VIEWPOINTS:
		marks.append([WG(vp_xz(vp).x, vp_xz(vp).y), str(vp[1]), Color(0.5, 0.8, 1.0), vp[0] == spot])
	for pl in PLACES:
		marks.append([WG(pl[1], pl[2]), str(pl[0]), Color(0.95, 0.95, 0.9), false])
	for pl in Worlds.places_of("bergtal"):               # 3D-4.x Welten: the old scenes (green)
		marks.append([WG(pl[2], pl[3]), str(pl[1]), Color(0.45, 0.9, 0.5), pl[0] == spot])
	for mk in (m.get("bt_marks") if m.get("bt_marks") is Array else []):
		marks.append([WG(float(mk[1]), float(mk[2])), str(mk[0]), Color(0.95, 0.35, 0.85), false])
	s.data["map_marks"] = marks
	s.data["orientation"] = str(m.get("bt_orient")) if m.get("bt_orient") != null else "leicht"
	var tex := map_texture()
	var px := func(u: float, v: float): return W(Vector3(LO + u * 4.0, 0, LO + v * 4.0))
	s.data["map_img"] = [tex, px.call(0.0, 0.0), px.call(512.0, 0.0), px.call(0.0, 512.0), 512.0]
	var lines := []
	var rl := PackedVector2Array()
	for i in range(0, road_pts.size(), 2):
		var wp := WG(road_pts[i].x, road_pts[i].y)
		rl.append(Vector2(wp.x, wp.z))
	lines.append([rl, Color(0.55, 0.55, 0.55), 3.0])
	for tr in TRAILS:
		var tl := PackedVector2Array()
		for q in dense(tr[1], 12.0):
			var wp := WG(q.x, q.y)
			tl.append(Vector2(wp.x, wp.z))
		lines.append([tl, [Color(0.95, 0.8, 0.1), Color(0.9, 0.25, 0.2), Color(0.3, 0.55, 1.0)][int(tr[2])], 1.5])
	for lk in LAKES:
		var ll := PackedVector2Array()
		for k in range(25):
			var a := TAU * k / 24.0
			var q := Vector2(cos(a) * float(lk[1]), sin(a) * float(lk[2])).rotated(float(lk[3])) + (lk[0] as Vector2)
			var wp := WG(q.x, q.y)
			ll.append(Vector2(wp.x, wp.z))
		lines.append([ll, Color(0.3, 0.55, 0.85), 2.0])
	s.data["map_lines"] = lines
	s.data["road_line"] = rl
	s.data["road_z"] = 900.0                                # (cars without a road near: far away, not over the meadow)
	var er := []
	for v in VIGNETTES:
		var wp := WG(v[3], v[4])
		er.append({"nr": v[0], "id": v[1], "name": v[2], "x": snappedf(wp.x, 0.1), "z": snappedf(wp.z, 0.1), "y": snappedf(wp.y, 0.01), "tal_x": v[3], "tal_z": v[4]})
	s.data["erlebnis"] = er
	if self.orte != null:                                   # (a local «orte» above: the list for MoveEye)
		self.orte.publish()


# =======================================================================================================================
# animals, people, events
# =======================================================================================================================
const BT_KINDS := ["berg_auto", "berg_hiker", "berg_marmot", "berg_chamois", "berg_ibex", "berg_cows", "berg_sheep", "berg_fox_food",
		"berg_choughs", "berg_eagle", "berg_vulture", "berg_snowhare", "berg_salamander", "berg_stoat", "berg_ptarmigan", "berg_stranger",
		"berg_rockfall", "berg_storm", "berg_fog", "berg_fogsea", "berg_deer"]


func is_kind(k: String) -> bool:
	return k in BT_KINDS


func _recolor(v: Node3D, col: Color, temp = null) -> void:
	"""another fur colour (and surface temperature) for an animal of actor.gd"""
	for mi in v.find_children("*", "MeshInstance3D", true, false):
		var g := mi as MeshInstance3D
		if g.layers == 1:
			var old: Color = (g.material_override as StandardMaterial3D).albedo_color if g.material_override is StandardMaterial3D else Color.WHITE
			var lum := (old.r + old.g + old.b) / 3.0
			if lum > 0.04:                                      # (eyes, nose stay)
				g.material_override = m.mat(col * clampf(0.6 + lum, 0.6, 1.4))
		elif g.layers == 2 and temp != null:
			g.material_override = m.tmat_fixed(float(temp))


func _ground_pt(dmin: float, dmax: float, steep := -1.0, az := 999.0) -> Vector3:
	"""a world point dmin … dmax from MoveEye (in front by default), steep > 0: on steep rock"""
	var best := Vector3.ZERO
	for i in range(24):
		var a := az if az != 999.0 else randf_range(-80.0, 80.0)
		var p: Vector3 = m.pos_of(a + randf_range(-25.0, 25.0), randf_range(dmin, dmax))
		var q := V(p)
		var zn := zone(q.x, q.z)
		if zn == "lake":
			continue
		best = p
		if steep < 0.0 or slope_deg(q.x, q.z, 2.0) > steep:
			break
	best.y = gy(best.x, best.z)
	return best


func spawn_kind(kind: String, from = null, to = null):
	var dark: bool = m.is_dark()
	match kind:
		"berg_auto":
			return _auto()
		"berg_hiker":
			return _hiker()
		"berg_marmot":
			return _marmot(_burrows[randi() % _burrows.size()] if not _burrows.is_empty() else _ground_pt(25.0, 50.0))
		"berg_chamois", "berg_ibex":
			var k := "chamois" if kind == "berg_chamois" else "ibex"
			var a := _ground_pt(14.0, 32.0) if dark else _ground_pt(60.0, 160.0, 30.0)      # at night they come close
			var b := _ground_pt(14.0, 40.0) if dark else _ground_pt(60.0, 160.0, 30.0)
			var v = m.spawn(k, a, b)
			v.speed *= 0.5
			if randf() < 0.6:
				var c = m.spawn(k, a + Vector3(2, 0, 1.5), b + Vector3(2, 0, 1.5))
				c.leader = v
				c.follow_off = Vector3(1.5, 0, 2.0)
			return v
		"berg_cows":
			return _herd("cow", randi_range(3, 5))
		"berg_sheep":
			return _herd("sheep", randi_range(6, 10))
		"berg_fox_food":
			return _at_food("fox" if dark else "choughs")
		"berg_choughs":
			return _at_food("choughs")
		"berg_eagle", "berg_vulture":
			return _big_bird(kind == "berg_vulture")
		"berg_snowhare":
			var v2 = m.spawn("hare", from if from != null else _ground_pt(8.0, 25.0), to if to != null else _ground_pt(8.0, 25.0))
			_recolor(v2, Color(0.95, 0.95, 0.93) if season == "winter" else Color(0.5, 0.45, 0.38))
			v2.set_meta("berg_kind", "snowhare")
			return v2
		"berg_stoat":
			var v3 = m.spawn("marten", from if from != null else _ground_pt(5.0, 15.0), to if to != null else _ground_pt(5.0, 15.0))
			v3.body_root.scale *= 0.62                       # Hermelin: 22–30 cm body (Mustela erminea)
			_recolor(v3, Color(0.96, 0.95, 0.9) if season == "winter" else Color(0.5, 0.32, 0.16))
			v3.set_meta("berg_kind", "stoat")
			return v3
		"berg_salamander":
			return _salamander()
		"berg_ptarmigan":
			return _ptarmigan()
		"berg_stranger":
			return stranger()
		"berg_rockfall":
			rockfall()
			return null
		"berg_storm":
			storm()
			return null
		"berg_fog":
			fog_roll()
			return null
		"berg_fogsea":
			fogsea()
			return null
		"berg_deer":
			var dv = m.spawn("deer", _ground_pt(20.0, 50.0), _ground_pt(20.0, 50.0))
			if season == "herbst" and dark:
				m.add_sound(-6.0, dv.global_position if dv != null else Vector3.ZERO, 3.0)     # Hirschbrunft: the roar (≈ 100 dB at 1 m)
			return dv
	return null


func _auto():
	"""who comes now: lonely valley - few people (hikers by day), many animals, by season and time"""
	var h: float = m.hour()
	var dark: bool = m.is_dark()
	var w := {}
	var sumr: bool = season in ["sommer", "herbst"]
	w["berg_hiker"] = 0.0 if dark else (0.5 if season != "winter" else 0.12) * (0.5 + float(rating.get("strangers", 0.3)))
	w["berg_marmot"] = 0.0 if season == "winter" or dark or _burrows.is_empty() else 1.2
	w["berg_chamois"] = 0.9 if dark else 0.5
	w["berg_ibex"] = 0.6 if dark else 0.35
	w["berg_cows"] = 0.6 if sumr and spot_xz.distance_to(HUT) < 300.0 and _count("cow") == 0 else 0.0
	w["berg_sheep"] = 0.4 if sumr and spot_xz.distance_to(Vector2(200, 560)) < 500.0 and _count("sheep") == 0 else 0.0
	w["berg_fox_food"] = 0.7 if dark else (0.4 if season != "winter" else 0.2)
	w["berg_eagle"] = 0.0 if dark else 0.3
	w["berg_vulture"] = 0.0 if dark else 0.2
	w["berg_snowhare"] = 0.6 if (dark or h < 8.0 or h > 18.0) else 0.15
	w["berg_stoat"] = 0.35
	w["berg_ptarmigan"] = 0.3 if float(rating.get("alt_m", 0)) > 1950.0 and not dark else 0.0
	w["berg_salamander"] = 0.8 if season in ["fruehling", "sommer"] and m.weather == "rain" else 0.0
	w["berg_deer"] = (0.9 if season == "herbst" else 0.3) if dark and h0 < 320.0 else 0.0          # red deer lower down; rut in autumn
	var tot := 0.0
	for k in w:
		tot += float(w[k])
	var r := randf() * tot
	for k in w:
		r -= float(w[k])
		if r <= 0.0:
			return spawn_kind(k)
	return null


func _count(kind: String) -> int:
	var n := 0
	for v in m.visitors.get_children():
		if v.get("kind") == kind and not v.done:
			n += 1
	return n


func _hiker():
	"""a hiker on the nearest trail (passes by, sometimes rests); in winter with snowshoes - slower"""
	var best := []
	var bd := INF
	for tr in TRAILS:
		var pts := dense(tr[1], 6.0)
		for i in range(pts.size()):
			var d := pts[i].distance_to(spot_xz)
			if d < bd:
				bd = d
				best = [pts, i]
	var route := []
	if best.is_empty() or bd > 220.0:                          # no trail near: across the slope
		route = [_ground_pt(40.0, 70.0, -1.0, -70.0), _ground_pt(25.0, 40.0, -1.0, 0.0), _ground_pt(40.0, 70.0, -1.0, 70.0)]
	else:
		var pts: PackedVector2Array = best[0]
		var i0: int = best[1]
		var dirn := 1 if randf() < 0.5 else -1
		for k in range(-22, 23, 2):
			var j := clampi(i0 + k * dirn, 0, pts.size() - 1)
			var wp := WG(pts[j].x, pts[j].y)
			if route.is_empty() or (route[-1] as Vector3).distance_to(wp) > 1.0:
				route.append(wp)
	var v = m.spawn("backpacker" if randf() < 0.7 else "person", route[0], route[1] if route.size() > 1 else route[0] + Vector3(5, 0, 0))
	if v == null:
		return null
	v.speed = randf_range(0.9, 1.2) * (0.7 if season == "winter" else 1.0)
	for k in range(2, route.size()):
		v.route.append(route[k])
	if randf() < 0.3 and route.size() > 6:
		v.route.insert(2, [route[route.size() / 2], randf_range(15.0, 40.0), 0.0])    # a rest
	v.set_meta("berg_kind", "hiker")
	return v


func _marmot(burrow: Vector3):
	var out := burrow + Vector3(randf_range(-10, 10), 0, randf_range(-10, 10))
	var v = m.spawn("badger", burrow, out)
	if v == null:
		return null
	v.body_root.scale *= 0.85                               # Murmeltier: 50–60 cm, 3–7 kg (Marmota marmota)
	_recolor(v, Color(0.56, 0.44, 0.3), 31.0)
	v.speed = 0.6
	v.route = [[out, randf_range(20.0, 60.0), 0.0], out + Vector3(randf_range(-4, 4), 0, randf_range(-4, 4)), [burrow, 0.5, 0.0]]
	v.set_meta("berg_kind", "marmot")
	v.set_meta("burrow", burrow)
	_residents.append(v)
	return v


func _herd(kind: String, n: int):
	var c := V(Vector3.ZERO)
	var centre := HUT + Vector2(20, 60) if kind == "cow" else Vector2(200, 560)
	if Vector2(c.x, c.z).distance_to(centre) < 300.0:
		centre = Vector2(c.x, c.z).lerp(centre, 0.3)
	var lead = null
	for i in range(n):
		var q := centre + Vector2(randf_range(-20, 20), randf_range(-20, 20))
		var t := centre + Vector2(randf_range(-40, 40), randf_range(-40, 40))
		var v = m.spawn(kind, WG(q.x, q.y), WG(t.x, t.y))
		if v == null:
			continue
		v.speed *= 0.5
		v.set_meta("berg_kind", kind)
		v.set_meta("bell", kind == "cow" or i % 3 == 0)
		v.set_meta("home", centre)
		_residents.append(v)
		if lead == null:
			lead = v
	return lead


func _at_food(who: String):
	"""a fox (night) or alpine choughs (day) come to the food bag and take it"""
	if _food_node == null or not is_instance_valid(_food_node) or not _food_node.visible:
		return null
	var fp := _food_node.global_position
	if who == "choughs":
		return _choughs(fp)
	var a := _ground_pt(25.0, 45.0)
	var v = m.spawn("fox", a, fp + Vector3(0.5, 0, 0.3))
	if v == null:
		return null
	v.speed = 1.0
	v.route = [[fp + Vector3(0.5, 0, 0.3), 5.0, 0.0], a + Vector3(10, 0, -10)]
	v.set_meta("berg_kind", "fox_food")
	_thieves.append([v, "fox"])
	return v


var _thieves: Array = []                       # [actor or bird list, kind]


func _bird_node(span: float, col: Color, temp: float) -> Node3D:
	"""a simple bird: body and two wings that flap (warm in the thermal picture)"""
	var b := Node3D.new()
	var body: MeshInstance3D = s.put(b, s.sph(span * 0.08, span * 0.35), Vector3.ZERO, col, temp, Vector3(PI / 2, 0, 0))
	body.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	s.put(b, s.sph(span * 0.055), Vector3(0, span * 0.02, -span * 0.17), col.darkened(0.1), temp + 3.0)
	for sd in [-1.0, 1.0]:
		var piv := Node3D.new()
		piv.name = "wing_l" if sd < 0 else "wing_r"
		b.add_child(piv)
		s.put(piv, m.box(span * 0.48, 0.02, span * 0.16), Vector3(sd * span * 0.25, 0, 0), col, temp - 6.0)
	return b


func _choughs(fp: Vector3):
	# Alpendohle (Pyrrhocorax graculus): schwarz, gelber Schnabel, Spannweite 75–85 cm, in Schwärmen bei Rastplätzen
	var list := []
	for i in range(randi_range(4, 7)):
		var b := _bird_node(0.8, Color(0.06, 0.06, 0.07), 38.0)
		s.root.add_child(b)
		var st := fp + Vector3(randf_range(-40, 40), randf_range(25, 45), randf_range(-60, -30))
		b.position = st
		list.append({"n": b, "from": st, "to": fp + Vector3(randf_range(-2.5, 2.5), 0.0, randf_range(-2.5, 2.5)), "t0": m.now() + i * 0.6, "state": "in"})
	_thieves.append([list, "choughs"])
	return null


func _big_bird(vulture: bool):
	# Bartgeier (Gypaetus barbatus): Spannweite 2,6–2,9 m · Steinadler (Aquila chrysaetos): 1,9–2,3 m - kreisen über Grat und Hang
	var span := 2.8 if vulture else 2.1
	var b := _bird_node(span, Color(0.55, 0.42, 0.3) if vulture else Color(0.3, 0.22, 0.14), 34.0)
	s.root.add_child(b)
	var c := _ground_pt(80.0, 220.0)
	var r := randf_range(40.0, 90.0)
	var hgt := randf_range(50.0, 140.0)
	var t0: float = m.now()
	var dur := randf_range(90.0, 180.0)
	var wr: WeakRef = weakref(b)
	m.anims.append(func(_dt, t):
		var bn = wr.get_ref()
		if bn == null:
			return true
		var k: float = m.now() - t0
		if k > dur:
			bn.queue_free()
			return true
		var a := k * 0.12
		var drift := Vector3(k * 0.6, 0, 0)
		bn.position = c + drift + Vector3(cos(a) * r, hgt + 6.0 * sin(k * 0.3), sin(a) * r)
		bn.rotation = Vector3(0, -a, 0.35)
		return false)
	return null


func _salamander():
	# Alpensalamander (Salamandra atra): ganz schwarz, 11–15 cm, kommt nach Regen heraus; wechselwarm = fast so kalt wie die Luft
	var v = m.spawn("marten", _ground_pt(3.0, 8.0), _ground_pt(3.0, 8.0))
	if v == null:
		return null
	v.body_root.scale *= 0.28
	v.speed = 0.08
	_recolor(v, Color(0.04, 0.04, 0.04), float(m.ambient) + 0.5)
	v.set_meta("berg_kind", "salamander")
	return v


func _ptarmigan():
	# Alpenschneehuhn (Lagopus muta): im Winter weiss, im Sommer gesprenkelt braun-grau; läuft, fliegt spät auf
	var b := _bird_node(0.6, Color(0.95, 0.95, 0.93) if season == "winter" else Color(0.48, 0.42, 0.34), 39.0)
	s.root.add_child(b)
	var a := _ground_pt(6.0, 18.0)
	var c := _ground_pt(6.0, 18.0)
	b.position = a
	var t0: float = m.now()
	var wr: WeakRef = weakref(b)
	m.anims.append(func(_dt, _t):
		var bn = wr.get_ref()
		if bn == null:
			return true
		var k: float = (m.now() - t0) / 25.0
		if k > 1.4:
			bn.queue_free()
			return true
		var p := a.lerp(c, minf(k, 1.0))
		p.y = gy(p.x, p.z) + 0.15 + (maxf(0.0, k - 1.0) * 40.0)          # walks, then flies away
		bn.position = p
		return false)
	return null


func stranger():
	"""a stranger at night: comes from the trail with a torch to the backpack, kneels, goes away (Daniel: Dieb / Fremder)"""
	if _pack_node == null or not is_instance_valid(_pack_node):
		return null
	var pp := _pack_node.global_position
	var a := _ground_pt(35.0, 60.0, -1.0, randf_range(-60.0, 60.0))
	var v = m.spawn("person", a, pp + Vector3(0.6, 0, -0.5))
	if v == null:
		return null
	v.speed = 0.85
	v.add_torch()
	if m.is_dark():
		v.torch.light_energy = 3.0
	var away := _ground_pt(40.0, 70.0, -1.0, randf_range(-90.0, 90.0))
	v.route = [[pp + Vector3(0.6, 0, -0.5), 7.0, 1.0], away]
	v.set_meta("berg_kind", "stranger")
	night_log.append({"k": "stranger", "t": m.hour(), "text": "Fremder am Rucksack"})
	return v


func rockfall(near := false) -> Dictionary:
	"""stones come down a steep slope (more likely below cliffs); they roll along the slope and stop on flat ground"""
	var cands := []
	for k in range(36):
		var a := TAU * k / 36.0
		var r := 30.0
		while r < 320.0:
			var q := spot_xz + Vector2(cos(a), sin(a)) * r
			if slope_deg(q.x, q.y, 3.0) > 40.0 and H(q.x, q.y) > h0 + 15.0:
				cands.append([q, r])
				break
			r += 12.0
	if cands.is_empty():
		for zz in range(40):                                    # nothing near: the nearest scree slope
			var q := Vector2(cx(spot_xz.y) - 330.0 + randf_range(-20, 20), clampf(spot_xz.y, -40.0, 640.0) + randf_range(-40, 40))
			cands.append([q, q.distance_to(spot_xz)])
	cands.sort_custom(func(a, b): return a[1] < b[1])
	var src: Vector2 = cands[randi() % mini(4 if near else cands.size(), cands.size())][0]
	var n := randi_range(4, 9)
	for i in range(n):
		var r := randf_range(0.12, 0.55)
		var st := Node3D.new()
		s.root.add_child(st)
		s.put(st, s.sph(r, r * 1.6), Vector3.ZERO, Color(0.45, 0.44, 0.41), float(m.ambient) + 2.0)   # stones: a little warmer from the friction
		var q := src + Vector2(randf_range(-4, 4), randf_range(-4, 4))
		st.position = WG(q.x, q.y, r)
		_stones.append({"n": st, "v": Vector3.ZERO, "r": r, "t0": m.now() + i * randf_range(0.2, 0.9), "rest": 0.0})
	var wsrc := WG(src.x, src.y)
	m.add_sound(-3.0, wsrc, 6.0)                               # rumble and clatter (≈ 100 dB at 1 m)
	night_log.append({"k": "rockfall", "t": m.hour(), "text": "Steinschlag", "dist": snappedf(wsrc.length(), 1.0)})
	return {"ok": true, "source": wsrc, "dist": snappedf(wsrc.length(), 0.1), "stones": n}


func storm() -> Dictionary:
	"""thunderstorm comes (weather hooks of main.gd: rain, thunder, wind); on an exposed spot: stronger and a warning"""
	m.weather = "rain"
	m.thunder = true
	m.wind = maxf(m.wind, 35.0 + 40.0 * float(rating.get("wind", 0.5)))
	m.storm_t = m.now()
	_storm_until = m.now() + randf_range(180.0, 360.0)
	var warn := "Gewitter! Ausgesetzter Platz – runter vom Grat, Schutz suchen (Hütte, Biwak)" if float(rating.get("lightning", 0.0)) > 0.4 else "Gewitter zieht auf"
	m.start_info = T.t(warn)
	night_log.append({"k": "storm", "t": m.hour(), "text": "Gewitter"})
	return {"ok": true, "wind": m.wind, "warn": warn}


var _fogsea_until := 0.0


func fogsea(secs := 600.0) -> Dictionary:
	"""Nebelmeer (inversion): the valley below ≈ 1560 m in thick fog, the high places in the sun above it"""
	_fogsea_until = m.now() + secs
	night_log.append({"k": "fogsea", "t": m.hour(), "text": "Nebelmeer"})
	return {"ok": true, "secs": secs, "above": h0 > 60.0}


func fog_roll() -> Dictionary:
	"""fog comes up the valley fast (≈ 40 s from clear to thick)"""
	m.weather = "fog"
	_fog_k = 0.0
	night_log.append({"k": "fog", "t": m.hour(), "text": "Nebel"})
	return {"ok": true}


# ---- every frame ----------------------------------------------------------------------------------------------------------
var _t_slow := 0.0
var _need_residents := false
var _bell_t := 0.0
var _edge_t := 0.0
var _headlamp: SpotLight3D
var _ride := {}


func _tick(dt: float, _t: float) -> bool:
	if tal == null or not is_instance_valid(tal):
		return true
	# the air: clear and far in the mountains, fog that rolls in, valley fog in autumn mornings
	var target := 1.0 if m.weather == "fog" else 0.0
	_fog_k = move_toward(_fog_k, target, dt / 40.0)
	var base: float = {"clear": 0.00012, "cloudy": 0.0004, "rain": 0.0028, "snow": 0.007, "fog": 0.0008}.get(m.weather, 0.0004)
	m.env.fog_density = lerpf(base, 0.045, _fog_k)
	var hr: float = m.hour()
	if m.now() < _fogsea_until or (season == "herbst" and (hr < 10.0 or hr > 20.0) and m.weather in ["clear", "cloudy"]):
		m.env.fog_height = W(Vector3(0, 60.0, 0)).y                  # «Nebelmeer»: the valley in fog, the high places above it
		m.env.fog_height_density = 0.03
	else:
		m.env.fog_height_density = 0.0
	if aussicht != null:
		aussicht.frame(dt)                               # moods (sun colour, Milky Way), the weather coming from far, the telescope
	_t_slow -= dt
	if _t_slow > 0.0:
		_tick_stones(dt)
		_tick_ride(dt)
		return false
	_t_slow = 0.25
	if _need_residents and m.visitors != null:
		_need_residents = false
		_residents_spawn()
	_tick_stones(dt)
	_tick_ride(dt)
	_tick_residents()
	_tick_thieves()
	_tick_headlamp()
	_tick_edges()
	_tick_ice()
	_tick_visited()
	if aussicht != null:
		aussicht.slow()                                  # (before the morning: alpenglow counts for this morning)
	if _storm_until > 0.0 and m.now() > _storm_until:
		_storm_until = 0.0
		m.thunder = false
		m.weather = "cloudy"
	var dark: bool = m.is_dark()
	if _was_dark and not dark and hr > 4.0 and hr < 11.0:
		morning()
	if dark and not _was_dark:
		night_log.clear()
	if dark and m.weather == "clear" and float(rating.get("stars", 0.0)) > 0.7 and not night_log.any(func(e): return e["k"] == "stars"):
		night_log.append({"k": "stars", "t": hr, "text": "Sternennacht"})
		_discover("berg.sterne." + spot, "Sternennacht am Schlafplatz", "Klare Nacht, weiter Himmel – die Milchstrasse über dem Bergtal.")
	_was_dark = dark
	if bool(m.get("bt_events")) and m.now() > _ev_next and m.busy_with() in ["", "Testlauf"]:
		_ev_next = m.now() + randf_range(60.0, 160.0) / maxf(0.2, float(m.visit_rate))
		_random_event(dark)
	return false


func _random_event(dark: bool) -> void:
	var r := randf()
	var rk := float(rating.get("rockfall", 0.0))
	if r < 0.04 + 0.25 * rk:
		rockfall()
	elif dark and r < 0.40 and randf() < 0.25 + 0.5 * float(rating.get("strangers", 0.0)):
		stranger()
	elif r < 0.6:
		spawn_kind("berg_fox_food")
	elif r < 0.66 and m.weather == "clear":
		if aussicht != null:
			aussicht.plan_weather("storm" if randf() < 0.5 else "fog")     # first seen far away (viewpoints: early warning)
		else:
			storm() if randf() < 0.5 else fog_roll()


func _tick_stones(dt: float) -> void:
	for i in range(_stones.size() - 1, -1, -1):
		var st: Dictionary = _stones[i]
		var n = st["n"]
		if not is_instance_valid(n):
			_stones.remove_at(i)
			continue
		if m.now() < float(st["t0"]):
			continue
		if float(st["rest"]) > 0.0:
			if m.now() - float(st["rest"]) > 90.0:
				n.queue_free()
				_stones.remove_at(i)
			continue
		var q: Vector3 = V(n.global_position)
		var g := grad(q.x, q.z)                                 # along the slope: g = 9.81 · sin(slope), rolling friction
		var sl := atan(g.length())
		var down := -Vector3(g.x, 0, g.y).normalized() if g.length() > 0.001 else Vector3.ZERO
		var acc := down * 9.81 * sin(sl) - (st["v"] as Vector3).normalized() * 9.81 * cos(sl) * 0.45
		var v: Vector3 = st["v"] + acc * dt
		v.y = 0.0
		if v.length() > 25.0:
			v = v.normalized() * 25.0
		var wdir := tal.transform.basis * v
		n.global_position += wdir * dt
		var wp: Vector3 = n.global_position
		wp.y = gy(wp.x, wp.z) + float(st["r"]) + absf(sin(m.now() * 7.0 + i)) * minf(1.2, v.length() * 0.05)   # bouncing
		n.global_position = wp
		n.rotate_x(v.length() * dt / float(st["r"]))
		st["v"] = v
		if v.length() < 0.25 and rad_to_deg(sl) < 25.0 and m.now() - float(st["t0"]) > 2.0:
			st["rest"] = m.now()
			if wp.length() < 25.0:
				night_log.append({"k": "stone_near", "t": m.hour(), "text": "Stein bis %d m an den Platz" % int(wp.length())})


func _tick_residents() -> void:
	var now: float = m.now()
	_bell_t -= 0.25
	for i in range(_residents.size() - 1, -1, -1):
		var v = _residents[i]
		if not is_instance_valid(v) or v.done:
			_residents.remove_at(i)
			continue
		var bk := str(v.get_meta("berg_kind", ""))
		if bk == "marmot":
			# whistles and runs into the burrow when somebody comes near or the white light goes on
			var burrow: Vector3 = v.get_meta("burrow")
			var threat := false
			for o in m.visitors.get_children():
				if o != v and not o.done and o.get("kind") in ["person", "fox", "dog"] and o.position.distance_to(v.position) < 22.0:
					threat = true
			if bool(m.mw.get("lights", {}).get("white", false)):
				threat = true
			if threat and not v.has_meta("fled"):
				v.set_meta("fled", true)
				m.add_sound(-10.0, v.global_position, 0.5)           # Murmeltier-Pfiff (≈ 90 dB at 1 m, carries far)
				v.route.clear()
				v.target = burrow
				v.speed = 2.6
				v.wait_until = 0.0
				v.idle_until = 0.0
			if v.position.distance_to(burrow) < 0.8 and (v.has_meta("fled") or v.route.is_empty()):
				v.done = true                                         # into the burrow
				v.queue_free()
		elif bk in ["cow", "sheep"]:
			if bool(v.get_meta("bell", false)) and _bell_t <= 0.0 and v.cur_speed > 0.1 or (bool(v.get_meta("bell", false)) and randf() < 0.05):
				m.add_sound(-16.0 if bk == "cow" else -24.0, v.global_position, 0.6)    # cow bell ≈ 80 dB at 1 m
			if v.route.is_empty() and v.position.distance_to(v.target) < 1.0:
				var home: Vector2 = v.get_meta("home")
				var near_tent: bool = _bed_node != null and is_instance_valid(_bed_node) and randf() < 0.12 and v.global_position.distance_to(_bed_node.global_position) < 80.0
				if near_tent:                                      # curious: comes to the tent and stands there
					v.route = [[_bed_node.global_position + Vector3(randf_range(-1.5, 1.5), 0, 2.2), randf_range(15.0, 40.0), 0.0]]
					night_log.append({"k": "cow", "t": m.hour(), "text": "Kuh am Zelt" if bed == "tent" else "Kuh am Schlafplatz"})
				else:
					var q := home + Vector2(randf_range(-45, 45), randf_range(-45, 45))
					v.target = WG(q.x, q.y)
	if _bell_t <= 0.0:
		_bell_t = 2.0


func _tick_thieves() -> void:
	for i in range(_thieves.size() - 1, -1, -1):
		var th: Array = _thieves[i]
		if th[1] == "fox":
			var v = th[0]
			if not is_instance_valid(v) or v.done:
				_thieves.remove_at(i)
				continue
			if _food_node != null and is_instance_valid(_food_node) and _food_node.visible and v.global_position.distance_to(_food_node.global_position) < 1.2 and v.cur_speed < 0.1:
				_food_node.visible = false                             # the fox takes the food
				night_log.append({"k": "food", "t": m.hour(), "text": "Fuchs hat den Proviant geholt"})
				_thieves.remove_at(i)
		else:
			var list: Array = th[0]
			var all_gone := true
			for b in list:
				var n = b["n"]
				if not is_instance_valid(n):
					continue
				all_gone = false
				var k: float = (m.now() - float(b["t0"])) / 8.0
				if k < 0.0:
					continue
				var t := clampf(k, 0.0, 1.0)
				var p: Vector3 = (b["from"] as Vector3).lerp(b["to"], t)
				if b["state"] == "in":
					p.y = lerpf((b["from"] as Vector3).y, gy(p.x, p.z) + 0.2, t * t)
					if t >= 1.0:
						b["state"] = "hop"
						b["t1"] = m.now()
				elif b["state"] == "hop":
					var k2: float = m.now() - float(b["t1"])
					p = (b["to"] as Vector3) + Vector3(sin(k2 * 1.3) * 0.8, 0, cos(k2 * 0.9) * 0.8)
					p.y = gy(p.x, p.z) + 0.2 + absf(sin(k2 * 6.0)) * 0.15
					if k2 > 12.0:
						if _food_node != null and is_instance_valid(_food_node) and _food_node.visible:
							_food_node.visible = false
							night_log.append({"k": "food", "t": m.hour(), "text": "Alpendohlen haben den Proviant geholt"})
						b["state"] = "out"
						b["t2"] = m.now()
				else:
					var k3: float = m.now() - float(b["t2"])
					p = (b["to"] as Vector3) + Vector3(k3 * 6.0, k3 * 4.0, -k3 * 5.0)
					if k3 > 15.0:
						n.queue_free()
				n.position = p
				for w in n.get_children():
					if w.name.begins_with("wing"):
						w.rotation.z = sin(m.now() * 14.0) * 0.6 * (1.0 if w.name == "wing_r" else -1.0) * (0.15 if b["state"] == "hop" else 1.0)
			if all_gone:
				_thieves.remove_at(i)


func _tick_headlamp() -> void:
	"""the headlamp of the player at night (exploring): own light cone (Daniel: «Stirnlampe nachts»)"""
	var on: bool = m.is_dark() and m.explore != null and m.explore.on
	if on and _headlamp == null:
		_headlamp = SpotLight3D.new()
		_headlamp.spot_range = 25.0
		_headlamp.spot_angle = 22.0
		_headlamp.light_energy = 2.5
		_headlamp.light_color = Color(1.0, 0.96, 0.9)
		_headlamp.shadow_enabled = not lite
		m.view_cam.add_child(_headlamp)
	if _headlamp != null:
		_headlamp.visible = on
	for v in m.visitors.get_children():                        # players of the game too
		if v.get("controlled") and v.get("torch") == null and m.is_dark():
			v.add_torch()
			v.torch.light_energy = 3.0


func _tick_edges() -> void:
	"""cliff edges near the player / the rover: a warning (you do not fall: an invisible guard - the rover stops there)"""
	var who: Vector3 = m.rig.global_position if m.mover_on or (m.explore != null and m.explore.on) else m.view_cam.global_position
	var q := V(who)
	if q.y - H(q.x, q.z) > 4.0:
		return
	for k in range(8):
		var a := TAU * k / 8.0
		var p := Vector2(q.x + cos(a) * 4.0, q.z + sin(a) * 4.0)
		if H(q.x, q.z) - H(p.x, p.y) > 4.0 and slope_deg(p.x, p.y, 2.0) > 50.0:
			if m.now() - _edge_t > 6.0:
				_edge_t = m.now()
				m.start_info = T.t("Achtung, Absturzkante! Hier geht es senkrecht hinunter.")
			break


var _vis_t := 0.0


static func all_places() -> Array:
	var out: Array = PLACES.duplicate()
	for pl in Worlds.places_of("bergtal"):               # 3D-4.x Welten: the old scenes (map, quick travel, visited)
		out.append([pl[1], pl[2], pl[3]])
	for vp in VIEWPOINTS:
		out.append([vp[1], vp_xz(vp).x, vp_xz(vp).y])
	out.append_array(Orte.all_places())
	return out


func _tick_visited() -> void:
	"""places you have been to (camera or rover within 70 m): only these can be reached by quick travel (Daniel)"""
	_vis_t -= 0.25
	if _vis_t > 0.0:
		return
	_vis_t = 2.0
	var vis: Array = m.bt_visited
	var who := [V(m.view_cam.global_position), V(m.rig.global_position)]
	for pl in all_places():
		if str(pl[0]) in vis:
			continue
		for q in who:
			if Vector2(q.x, q.z).distance_to(Vector2(pl[1], pl[2])) < 70.0 and q.y - H(q.x, q.z) < 120.0:
				vis.append(str(pl[0]))
				m._settings_dirty = true
				m.start_info = "%s %s" % [T.t("Neuer Ort entdeckt:"), T.t(str(pl[0]))]
				break


var _crack_t := 0.0


func _tick_ice() -> void:
	"""HOOK: the ice cracks under the rover / a person (a sound for the microphone; the audible crack: a later package)"""
	if ice.is_empty() or m.now() - _crack_t < 4.0:
		return
	var who := [m.rig.global_position]
	for v in m.visitors.get_children():
		if v.get("kind") == "person" and not v.done:
			who.append(v.global_position)
	for wp in who:
		var q := V(wp)
		for ic in ice:
			var e := _ell(Vector2(q.x, q.z), ic[0])
			if e < 1.0 and e >= float(ic[1]) and randf() < 0.35:
				_crack_t = m.now()
				m.add_sound(-12.0, wp, 0.4)
				return


func edge_guard() -> int:
	"""invisible guards at the cliff edges near the spot (obstacles: people, animals and the rover stop there)"""
	var n := 0
	var r := 0.0
	var step := 8.0
	var z := spot_xz.y - 220.0
	while z < spot_xz.y + 220.0:
		var x := spot_xz.x - 220.0
		while x < spot_xz.x + 220.0:
			var hh := H(x, z)
			for o in [Vector2(step, 0), Vector2(0, step)]:
				var dh := hh - H(x + o.x, z + o.y)
				if absf(dh) > step * 1.4:                     # > 55° between two points
					var top: Vector2 = Vector2(x, z) if dh > 0.0 else Vector2(x, z) + o
					m.add_obstacle(WG(top.x, top.y), 1.6)
					m.set_obstacle_height(1.2)
					n += 1
			x += step
		z += step
		if n > 500:
			break
	return n


# ---- the goods cable car: ride along (the view camera in the box) ------------------------------------------------------------
func ride(up := true) -> Dictionary:
	if lift.is_empty():
		return {"ok": false}
	var a: Vector3 = lift["a"] if up else lift["b"]
	var b: Vector3 = lift["b"] if up else lift["a"]
	var cab: Dictionary = bib.make("lift_cabin", {})
	var n: Node3D = bib._node_thing(cab, Transform3D(Basis(), a), "lift_cabin")
	bib.stats["animals"] -= 1
	_ride = {"n": n, "a": a, "b": b, "t0": m.now(), "dur": float(lift["len"]) / 2.5}      # ≈ 2.5 m/s like small goods lifts
	m._to_free_view()
	return {"ok": true, "secs": snappedf(float(_ride["dur"]), 0.1)}


func _tick_ride(_dt: float) -> void:
	if _ride.is_empty():
		return
	var n = _ride["n"]
	if not is_instance_valid(n):
		_ride = {}
		return
	var k := clampf((m.now() - float(_ride["t0"])) / float(_ride["dur"]), 0.0, 1.0)
	var p: Vector3 = (_ride["a"] as Vector3).lerp(_ride["b"], k)
	p.y -= 0.06 * float(lift["len"]) * k * (1.0 - k) * 0.25 * 4.0
	n.position = p
	var wp := W(p) + Vector3(0, -0.4, 0)
	var dirv := (W(_ride["b"]) - W(_ride["a"])).normalized()
	m.view_cam.global_position = wp - dirv * 0.4 + Vector3(0, 0.3, 0)
	m.view_cam.look_at(wp + dirv * 20.0 + Vector3(0, -6.0, 0), Vector3.UP)
	if k >= 1.0:
		n.queue_free()
		_ride = {}


# ---- the morning: «Wie gut war dein Platz?» ---------------------------------------------------------------------------------
func morning() -> Dictionary:
	var sich := int(rating.get("sicherheit", 3))
	var aus := int(rating.get("aussicht", 3))
	var ruhe := int(rating.get("ruhe", 3))
	var lines := []
	for e in night_log:
		lines.append(str(e["text"]))
		match str(e["k"]):
			"stranger", "stone_near":
				sich -= 1
				ruhe -= 1
			"food", "cow", "storm":
				ruhe -= 1
			"stars":
				aus += 1
	if aussicht != null:                                      # viewpoint, moods seen, wind and cold on a summit
		var adj: Array = aussicht.morning_adjust()
		sich += int(adj[0])
		aus += int(adj[1])
		ruhe += int(adj[2])
		lines.append_array(adj[3])
	sich = clampi(sich, 1, 5)
	aus = clampi(aus, 1, 5)
	ruhe = clampi(ruhe, 1, 5)
	var st := func(n: int): return "★".repeat(n) + "☆".repeat(5 - n)
	var txt := "%s  %s %s · %s %s · %s %s" % [T.t("Wie gut war dein Platz?"), T.t("Sicherheit"), st.call(sich), T.t("Aussicht"), st.call(aus), T.t("Ruhe"), st.call(ruhe)]
	var total := snappedf((sich + aus + ruhe) / 3.0, 0.1)                 # Daniel: all three equal
	txt += "  = %.1f" % total
	var res := {"sicherheit": sich, "aussicht": aus, "ruhe": ruhe, "total": total, "night": lines, "text": txt, "spot": spot, "notes": rating.get("notes", [])}
	res["ranking"] = _rank_add(res)
	info["morning"] = res
	m.start_info = txt
	m._say("%d · %d · %d ★" % [sich, aus, ruhe], m.head.global_position + Vector3(0, 1.4, 0), Color("#ffd166"), m.HELPER_LAYER)
	night_log.clear()
	return res


const RANK_FILE := "user://bergtal_rangliste.json"


static func ranking() -> Array:
	"""the best sleeping places so far (morning ratings), best first"""
	if not FileAccess.file_exists(RANK_FILE):
		return []
	var f := FileAccess.open(RANK_FILE, FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text()) if f != null else null
	return d if d is Array else []


func _rank_add(res: Dictionary) -> Array:
	var lst := ranking()
	var nm := "Eigener Platz %d / %d" % [int(spot_xz.x), int(spot_xz.y)]
	if spot != "frei":
		var sd: Array = spot_data(spot)
		nm = str(sd[0])
	lst.append({"name": nm, "spot": spot, "x": snappedf(spot_xz.x, 0.1), "z": snappedf(spot_xz.y, 0.1), "total": res["total"], "sicherheit": res["sicherheit"],
			"aussicht": res["aussicht"], "ruhe": res["ruhe"], "season": season, "bed": bed, "date": Time.get_datetime_string_from_system().substr(0, 16)})
	lst.sort_custom(func(a, b): return float(a["total"]) > float(b["total"]))
	lst = lst.slice(0, 20)
	var f := FileAccess.open(RANK_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(lst, " "))
	return lst


func _discover(id: String, title: String, text: String) -> void:
	"""counts as a discovery (branch «entdecken»: main.entdecken.register) - only if it is there"""
	var ed = m.get("entdecken")
	if ed == null or not ed.has_method("register"):
		return
	ed.register(id, {"scene": "bergtal", "title": T.t(title), "short_text": T.t(text), "hint": "", "icon": "*", "position": Vector3(0, 2, 0),
			"size": Vector3(2, 2, 2), "radius": 8.0, "kind": "ort"})


# ---- the residents near the spot ------------------------------------------------------------------------------------------
func _residents_spawn() -> void:
	_residents.clear()
	if season in ["sommer", "herbst"] and spot_xz.distance_to(HUT) < 260.0:
		_herd("cow", 3 if lite else 4)
	if season != "winter" and not m.is_dark():
		for b2 in _burrows.slice(0, 2):
			_marmot(b2)
	info["edge_guards"] = edge_guard()
	for pl in all_places():                                   # what you see from the spot counts as visited
		if Vector2(pl[1], pl[2]).distance_to(spot_xz) < 300.0 and not str(pl[0]) in m.bt_visited:
			m.bt_visited.append(str(pl[0]))


# =======================================================================================================================
# «Hier übernachten»: the place in the middle of the view (or where the rover is), checked
# =======================================================================================================================
func pick_here() -> Dictionary:
	var wp := Vector3.ZERO
	var from := "view"
	if (m.mover_on or (m.explore != null and m.explore.on)) and m.rig.global_position.length() > 2.0:
		wp = m.rig.global_position
		from = "rover"
	else:
		var cam: Camera3D = m.view_cam
		var o := cam.global_position
		var d := -cam.global_transform.basis.z
		var t := 1.0
		var hit := false
		while t < 2200.0:
			var p := o + d * t
			if p.y <= gy(p.x, p.z):
				wp = p
				hit = true
				break
			t += 1.0 if t < 60.0 else 4.0
		if not hit:
			return {"ok": false, "error": "Kein Boden in der Bildmitte – schau auf den Platz und versuche es nochmals."}
	var q := V(wp)
	var yaw_world: float = m.view_cam.global_rotation.y
	var yaw := rad_to_deg(-(yaw_world - tal.rotation.y))       # looking like the window camera
	return check_place(q.x, q.z, wp, yaw, from)


func check_place(x: float, z: float, wp: Vector3, yaw: float, from := "") -> Dictionary:
	if absf(x) > -LO - 20.0 or absf(z) > -LO - 20.0:
		return {"ok": false, "error": "Ausserhalb des Tals."}
	if zone(x, z) == "lake" and not (season == "winter"):
		return {"ok": false, "error": "Im Wasser kann man nicht übernachten."}
	var lim := flat_limit(bed)
	var sl := ground_slope(x, z)
	if sl > lim:
		# the nearest flat place within 15 m
		for r in [3.0, 6.0, 9.0, 12.0, 15.0]:
			for k in range(12):
				var a := TAU * k / 12.0
				var q := Vector2(x + cos(a) * r, z + sin(a) * r)
				if ground_slope(q.x, q.y) <= lim and zone(q.x, q.y) != "lake":
					return {"ok": true, "x": q.x, "z": q.y, "yaw": yaw, "slope": snappedf(ground_slope(q.x, q.y), 0.1), "moved_m": r, "from": from,
							"note": "Zu steil (%d°) – %d m daneben ist es flach genug." % [int(sl), int(r)]}
		return {"ok": false, "slope": snappedf(sl, 0.1), "limit": lim, "error": "Boden zu steil (%d°, höchstens %d° für %s)." % [int(sl), int(lim), "ein Zelt" if bed == "tent" else "die Isomatte"]}
	return {"ok": true, "x": x, "z": z, "yaw": yaw, "slope": snappedf(sl, 0.1), "moved_m": 0, "from": from, "note": "Boden flach genug (%d°)." % int(sl)}


# =======================================================================================================================
# control {"action": "bergtal", "do": info | spot | here | bed | season | event | goto | ride | morning | rate | perf | lite_test}
# =======================================================================================================================
static func control(main, d: Dictionary) -> Dictionary:
	var what := str(d.get("do", "info"))
	var bt = main.scenes.data.get("bergtal", null) if main.scenes != null else null
	match what:
		"spot":
			var v := str(d.get("value", ""))
			if v != "frei" and spot_data(v) == null:
				return {"ok": false, "error": "unknown spot", "spots": spot_options()}
			main.set_bt("bt_spot", v)
			return {"ok": true, "spot": v}
		"bed":
			main.set_bt("bt_bed", str(d.get("value", "tent")))
			return {"ok": true, "bed": main.bt_bed}
		"season":
			main.set_bt("bt_season", str(d.get("value", "auto")))
			return {"ok": true, "season": main.bt_season}
		"lite_test":
			preload("res://scripts/quality.gd").set_lite(bool(d.get("value", true)))
			if main.scene == "bergtal":
				main.set_scene("bergtal")
			return {"ok": true, "lite": Bib.lite()}
		"perf":
			return {"ok": true, "fps": Engine.get_frames_per_second(), "draw": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
					"objects": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME), "prims": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
					"scene": main.scene, "lite": Bib.lite(), "quality": main.quality, "nodes": main.get_tree().get_node_count(),
					"mem_static_mb": snappedf(float(OS.get_static_memory_usage()) / 1048576.0, 0.1),
					"video_mb": snappedf(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0, 0.1)}
	if bt == null:
		return {"ok": true, "scene": main.scene, "bergtal": false, "spots": spot_options()}
	match what:
		"here":
			if d.has("x") and d.has("z"):                    # valley coordinates given (tests)
				var r0: Dictionary = bt.check_place(float(d["x"]), float(d["z"]), Vector3.ZERO, float(d.get("yaw", 0.0)), "api")
				return main.bt_take(r0) if bool(d.get("take", true)) else r0
			return main.bt_here()
		"event":
			var k := str(d.get("value", ""))
			if not ("berg_" + k) in BT_KINDS:
				return {"ok": false, "error": "event: rockfall | storm | fog | stranger | fox_food | choughs | hiker | marmot | chamois | ibex | cows | sheep | eagle | vulture | snowhare | stoat | salamander | ptarmigan"}
			var v = bt.spawn_kind("berg_" + k)
			return {"ok": true, "kind": k, "spawned": v != null}
		"goto":
			return main.bt_goto(str(d.get("value", "")))
		"ride":
			return bt.ride(bool(d.get("up", true)))
		"morning":
			return bt.morning()
		"rate":
			if d.has("x"):
				return {"ok": true, "rating": bt.evaluate(float(d["x"]), float(d["z"]))}
			return {"ok": true, "rating": bt.rating, "exposure": bt.exposure()}
		"horn":
			return bt.postauto_horn()
		"erleben":                                       # Ereignisse 1–17: {what: info | where (id) | state (id, state, t, hold)}
			var ea = main.scenes.data.get("bt_erleben_a", null)
			if ea == null or not is_instance_valid(ea):
				return {"ok": false, "error": "no vignettes"}
			return ea.control(d)
		"aussicht":
			return bt.aussicht.control(d) if bt.aussicht != null else {"ok": false}
		"erleben_b":                                         # vignettes 18–34 (bergtal_erleben_b.gd)
			var eb = main.scenes.data.get("bergtal_erleben_b", null)
			return eb.control(d) if eb != null else {"ok": false, "error": "no erleben_b"}
		"orte":
			return bt.orte.control(d) if bt.orte != null else {"ok": false}
	return {"ok": true, "scene": main.scene, "bergtal": true, "spot": bt.spot, "season": bt.season, "bed": bt.bed, "spot_xz": [bt.spot_xz.x, bt.spot_xz.y],
			"alt_m": int(bt.h0 + ALT0), "rating": bt.rating, "exposure": bt.exposure(), "info": bt.info, "spots": spot_options(),
			"viewpoints": main.scenes.data.get("bt_viewpoints", []), "places": main.scenes.data.get("orte", []), "erlebnis": main.scenes.data.get("erlebnis", []),
			"night": bt.night_log, "aussicht": bt.aussicht.info_dict() if bt.aussicht != null else {}, "ground_at_0": bt.gy(0.0, 0.0), "pir": main.obj.get("pir"), "door": main.obj.get("door")}
