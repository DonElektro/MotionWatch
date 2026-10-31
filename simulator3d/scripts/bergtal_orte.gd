extends RefCounted
## 3D-4.x «Bergtal · Orte zum Erkunden» (Daniel, 31.10.2026, alles gewählt): begehbare Gebäude mit gestaltetem Innenraum und
## besondere Orte im Bergtal (bergtal.gd). Eigene Datei, von bergtal.gd aufgerufen (Orte.new(self) · build() · publish()).
##
##   Gebäude (innen gestaltet, Türen offen, Wände sind Hindernisse mit Lücke an der Tür, Boden als «deck» begehbar):
##     Selbstversorgerhütte Alp Tschuggen (Stube mit Holzofen, Hüttenbuch, Matratzenlager oben) · Biwakschachtel Chüebodehorn
##     (Pritschen, Biwakbuch, Notfallkiste) · Kapelle St. Jodern (Bänke, Altar, brennende Kerzen) · Infanteriewerk Gufer (Bunker:
##     Gang, Kampfstand mit Scharte, Filterraum, Mannschaftsraum) · verlassene Sennerei Chäsgaden (Kessi am Turner, Käsepresse,
##     eingefallenes Dach) · altes Hospiz am Furggapass (Eingangshalle mit Treppe, Gaststube mit Kachelofen und stehender Uhr,
##     Küche mit Falltür, Schlafsaal mit Tüchern über den Betten, Hauskapelle - für die spätere Horror-Geschichte: Türen als
##     eigene Knoten (hospiz_door), Raumlichter aus (hospiz_light), Räume in s.data["bt_orte"]["hospiz"]) · Militärbaracke Gufer
##     mit Stacheldraht-Resten · Tal- und Bergstation der Materialseilbahn (Seilwinde, Motor, Schaltkasten).
##   Wasser: Gumpifall mit Höhle dahinter (Wasservorhang, Gumpe davor) · drei Gumpen im Tschuggenbach · Gletschertor am
##     Wyssgletscher mit Schmelzbach (Gletschermilch) ins Gletscherseeli · Holzsteg und Wollgras am Moorsee Schwarzseeli.
##   Höhe: Gipfeltafel auf dem Tschingelspitz (Kreuz und Gipfelbuch hat er schon) · Felsturm Gumpizahn (30 m, nur über den
##     Klettersteig) · Schafgrat: ein schmaler Grat in der Höhenkarte (sculpt, genau auf einer Gitterlinie: die Gratlinie bleibt
##     glatt) mit Gratweg, Ketten, Warnung «Schmaler Grat» und unsichtbarer Sperre links und rechts.
##   Geschichte: alter gepflasterter Säumerweg südlich vom Hospiz · verlassene Alp Altstafel (eingefallene Hütten, Mauerreste,
##     Alpenampfer) · Militärbaracke mit Stacheldraht · Materialseilbahn (Stationen innen).
## Jeder Ort meldet sich im Entdeckungsbuch (main.entdecken.register, ids «berg.ort.*», Art «ort») und steht in der Orts- und
## Schnellreise-Liste (all_places / place_options; «… (innen)» fliegt die Ansicht in den Raum).
## Lite (Raspberry Pi): einfachere Innenräume (weniger Möbel und Kleinteile), keine Kerzen-/Raumlichter, weniger Wollgras und
## Pflastersteine. Zentrale Frage wie bib_berg.gd: Bib.lite() (Engine-Meta «lite»; der Koordinator verbindet es mit Quality.lite()).
## Steuerung: {"action": "bergtal", "do": "orte", "what": "info | where | goto (place) | door (name, deg) | light (name, on)"}.

const Bib = preload("res://scripts/bib_berg.gd")
const T = preload("res://scripts/i18n.gd")

# the buildings: [x, z, rot] in valley coordinates (x = east, z = south); the front with the door is local +z
const B_HUT := [51.0, 3.0, PI]                    # (8 m west of the old place: the east half stood over the gorge edge)
const B_BIV := [-520.0, 560.0, PI * 0.9]
const B_CHAPEL := [210.0, -700.0, PI]
const B_HOSPICE := [18.0, 790.0, PI / 2.0]
const B_DAIRY := [-700.0, -130.0, 0.3]
const B_BUNKER := [-171.0, 800.0, PI / 2.0]       # in the slope west of the pass, the corridor goes into the hill
const B_BARRACK := [-125.0, 836.0, 0.15]
const B_CAVE := [214.0, -330.0, -PI / 2.0]        # at the foot of the east waterfall over the Gumpisee, into the cliff
const B_GATE := [648.0, 445.0, -PI / 2.0]         # the snout of the Wyssgletscher, looking at the Gletscherseeli
const B_LIFT := [98.0, 22.0, 0.0]                 # (the turn comes from the cable)
const TOWER := Vector2(110, -420)                 # Gumpizahn: on the east shore meadow of the Gumpisee
const TOWER_H := 30.0
# the narrow ridge «Schafgrat»: straight along the grid column x = 568 (= LO + 398 × 4 m), so its crest line stays smooth
const RIDGE_X := 568.0
const RIDGE_Z0 := -600.0
const RIDGE_Z1 := -300.0
const RIDGE_A := 22.0                             # m above the plateau edge (flanks 55–70°)
const RIDGE_W := 14.0
# the old paved mule track (Säumerweg) from the hospice to the south
const SAUM := [Vector2(14, 806), Vector2(8, 850), Vector2(0, 900), Vector2(-12, 945), Vector2(-22, 985), Vector2(-30, 1015)]
# the pools (Gumpen) in the Tschuggenbach below the glacier stream: [centre, radius] on stream 0 between (200, 220) and (330, 290)
const POOLS := [[Vector2(230.0, 236.0), 2.4], [Vector2(262.4, 253.6), 2.9], [Vector2(297.5, 272.5), 2.2]]
# the abandoned alp around the old ruin: [x, z, rot, w, d]
const ALP_RUINS := [[-852.0, -192.0, 0.5, 5.0, 4.0], [-806.0, -246.0, -0.3, 6.0, 4.5], [-862.0, -238.0, 1.2, 4.0, 3.5]]

# the new named places (map, labels, quick travel)
const PLACES := [["Gumpizahn (Felsturm)", 110.0, -420.0], ["Schafgrat (Gratweg)", 568.0, -450.0], ["Alter Säumerweg", 0.0, 900.0],
		["Gumpifall mit Höhle", 214.0, -330.0], ["Gumpen im Tschuggenbach", 262.0, 254.0], ["Gletschertor Wyssgletscher", 646.0, 445.0],
		["Militärbaracke Gufer", -125.0, 836.0], ["Infanteriewerk Gufer (Bunker)", -171.0, 800.0], ["Holzsteg am Schwarzseeli", -612.0, -262.0]]
# quick travel into a room: [name, building, camera (local x, y, z), looks at (local x, y, z)]
const INSIDE := [["Alp Tschuggen – Hüttenstube (innen)", "huette", -2.6, 1.6, 2.4, 2.0, 0.9, -2.0],
		["Alp Tschuggen – Matratzenlager (innen)", "huette", 3.6, 3.9, 2.6, -2.5, 3.0, -2.0],
		["Biwak Chüebodehorn (innen)", "biwak", 0.5, 1.5, 1.0, -0.3, 1.0, -1.2],
		["Kapelle St. Jodern (innen)", "kapelle", 0.0, 1.7, 2.6, 0.0, 1.4, -3.0],
		["Hospiz – Eingangshalle (innen)", "hospiz", 0.0, 1.7, 4.8, 0.0, 1.5, -4.0],
		["Hospiz – Gaststube (innen)", "hospiz", -2.4, 1.7, 4.6, -8.0, 1.0, 0.5],
		["Hospiz – Küche (innen)", "hospiz", -2.4, 1.7, -1.4, -8.0, 0.9, -4.6],
		["Hospiz – Schlafsaal (innen)", "hospiz", 2.4, 1.7, 4.6, 8.4, 0.8, 0.0],
		["Hospiz – Hauskapelle (innen)", "hospiz", 2.4, 1.6, -1.8, 6.0, 1.3, -5.0],
		["Infanteriewerk Gufer (innen)", "bunker", -1.2, 1.5, -1.0, -1.2, 1.2, -10.0],
		["Alte Sennerei Chäsgaden (innen)", "sennerei", -2.6, 1.6, 1.8, 1.2, 0.8, -1.2],
		["Militärbaracke Gufer (innen)", "baracke", -5.0, 1.6, 2.0, 4.0, 0.9, -1.2],
		["Gumpifall-Höhle (innen)", "hoehle", 0.0, 1.5, -1.0, 0.0, 1.0, -9.0],
		["Talstation Materialseilbahn (innen)", "seilbahn", 0.0, 1.6, 1.0, 0.0, 1.0, -1.2]]
# the discovery book: [id, title, short text, hint, icon, size (m), radius (m), when]
const ENT := [["berg.ort.huette", "Die Selbstversorgerhütte", "Holzofen, Pritschen unter dem Dach und ein Hüttenbuch voller Grüsse. Holz nachfüllen nicht vergessen!",
			"Die Tür der Alp Tschuggen ist nicht abgeschlossen …", "🛖", Vector3(7, 2.2, 6), 5.0, "any"],
		["berg.ort.biwak", "In der Biwakschachtel", "Pritschen, Wolldecken und ein Biwakbuch – eng, aber sicher bei Sturm.",
			"Die rote Schachtel unter dem Chüebodehorn hat eine Tür.", "⛺", Vector3(2, 1.6, 2.4), 3.0, "any"],
		["berg.ort.kapelle", "Kerzen in St. Jodern", "In der kleinen Kapelle brennen immer ein paar Kerzen – wer zündet sie wohl an?",
			"Schau in die Kapelle auf dem Hügel.", "🕯", Vector3(4, 3, 6), 5.0, "any"],
		["berg.ort.bunker", "Das Infanteriewerk Gufer", "Ein alter Bunker im Hang: Gang, Kampfstand mit Scharte, Filterraum und Mannschaftsraum. Kalt und still.",
			"Westlich vom Furggapass steht eine Stahltür im Hang offen.", "🪖", Vector3(4, 2.2, 3.5), 4.0, "any"],
		["berg.ort.sennerei", "Die verlassene Sennerei", "Das Kessi hängt noch über der Feuerstelle, daneben die Käsepresse – seit Jahrzehnten hat hier niemand mehr gekäst.",
			"Im Seitental West steht eine Steinhütte mit eingefallenem Dach.", "🧀", Vector3(5, 2.2, 3.5), 4.5, "any"],
		["berg.ort.hospiz", "Im alten Hospiz", "Gaststube, Küche, Schlafsaal und eine Hauskapelle – alles still, die Uhr steht. Seit Jahren wohnt hier niemand mehr.",
			"Die Tür des Hospizes auf dem Furggapass ist nur angelehnt.", "🏚", Vector3(6, 2.6, 5), 5.0, "any"],
		["berg.ort.wasserfallhoehle", "Die Höhle hinter dem Gumpifall", "Hinter dem Wasservorhang führt eine Höhle in den Fels – drinnen tropft es.",
			"Am Ostufer des Gumpisees fällt ein Wasserfall über die Wand. Was ist wohl dahinter?", "💧", Vector3(3, 2.4, 6), 4.0, "any"],
		["berg.ort.gumpen", "Die Gumpen im Tschuggenbach", "Der Bach fällt über Stufen in drei tiefe, grüne Becken. Das Wasser ist eiskalt.",
			"Folge dem Bach von der Alp Richtung Gletscher.", "🌊", Vector3(8, 1, 8), 9.0, "any"],
		["berg.ort.gletschertor", "Das Gletschertor", "Aus einem blauen Eistor am Ende des Wyssgletschers schiesst der milchige Schmelzbach.",
			"Wo kommt das Wasser des Gletscherseelis her?", "🧊", Vector3(5, 4, 3), 10.0, "any"],
		["berg.ort.moorsee", "Wollgras am Schwarzseeli", "Ein Holzsteg führt über das Moor zum dunklen See – ringsum weisse Wollgras-Büschel.",
			"Im Seitental West liegt ein dunkler See im Moor.", "🌾", Vector3(3, 1, 3), 8.0, "any"],
		["berg.ort.gipfel", "Auf dem Tschingelspitz", "Gipfelkreuz, Gipfelbuch und Rundumsicht – der höchste Punkt im Westen des Tals.",
			"Der Tschingelspitz trägt ein Kreuz.", "⛰", Vector3(3, 4, 3), 8.0, "any"],
		["berg.ort.felsturm", "Der Gumpizahn", "Ein freistehender Felsturm am Gumpisee – hinauf geht es nur über den Klettersteig.",
			"Am Ostufer des Gumpisees ragt ein Zahn aus der Wiese.", "🧗", Vector3(8, 30, 8), 25.0, "any"],
		["berg.ort.grat", "Tiefblick vom Schafgrat", "Ein schmaler Gratweg, links und rechts geht es steil hinunter – tief unten der Gumpisee.",
			"Hoch über dem Gumpisee zieht ein schmaler Grat nach Süden.", "🏔", Vector3(2, 2, 6), 6.0, "any"],
		["berg.ort.saeumerweg", "Der alte Säumerweg", "Gepflasterte Steine, ausgetreten von Maultieren und Säumern, führen vom Hospiz nach Süden.",
			"Südlich vom Hospiz beginnt ein Weg aus alten Steinen.", "🫏", Vector3(2, 1, 6), 6.0, "any"],
		["berg.ort.alp_ruinen", "Die verlassene Alp Altstafel", "Eingefallene Hütten, Mauerreste und Alpenampfer – hier wurde früher gealpt.",
			"Ganz hinten im Seitental West stehen Mauern ohne Dach.", "🧱", Vector3(6, 2, 6), 10.0, "any"],
		["berg.ort.baracke", "Die Militärbaracke", "Eine alte Holzbaracke, rundherum rostige Stacheldraht-Reste aus dem Aktivdienst.",
			"Westlich vom Pass steht eine graue Baracke.", "🪵", Vector3(10, 2.4, 5), 6.0, "any"],
		["berg.ort.seilbahn", "Die Talstation der Materialseilbahn", "Seilwinde, Motor und Schaltkasten – von hier fährt die Kiste hinauf zur Obri Stafelhütte.",
			"Bei der Alp Tschuggen führt ein Seil den Hang hinauf.", "🚡", Vector3(2.6, 2, 2.2), 4.0, "any"]]

var bt                            # bergtal.gd
var m                             # main.gd
var s                             # scenes.gd
var bib
var lite := false
var full := true                  # not Lite: the full interiors
var season := "sommer"
var info := {}
var ent_pos := {}                 # discovery id -> valley position
var _xf := {}                     # building -> its transform (valley)
var hospiz := {"rooms": {}, "doors": {}, "lights": {}}
var _flames: Array = []           # [OmniLight3D, energy, valley position]
var _slow := 0.0
var _warn_t := -100.0
var _clock := 0.0

const REPLACES := ["alp_hut", "notice", "hospice", "chapel", "bivouac", "dairy", "lift_station"]


static func _lite() -> bool:
	return Bib.lite()


func _init(bt_) -> void:
	bt = bt_
	m = bt.m
	s = bt.s
	bib = bt.bib
	season = str(bt.season)
	lite = bool(bt.lite) or _lite()
	full = not lite


func replaces(kind: String) -> bool:
	"""bergtal.gd leaves these out: built here with their inside"""
	return kind in REPLACES


static func building(key: String) -> Array:
	match key:
		"huette":
			return B_HUT
		"biwak":
			return B_BIV
		"kapelle":
			return B_CHAPEL
		"hospiz":
			return B_HOSPICE
		"sennerei":
			return B_DAIRY
		"bunker":
			return B_BUNKER
		"baracke":
			return B_BARRACK
		"hoehle":
			return B_CAVE
		"tor":
			return B_GATE
		"seilbahn":
			return B_LIFT
	return [0.0, 0.0, 0.0]


static func all_places() -> Array:
	"""the new places + the rooms (for quick travel and «visited»): [name, x, z]"""
	var out: Array = PLACES.duplicate()
	for e in INSIDE:
		var b := building(str(e[1]))
		var q := Vector2(b[0], b[1]) + Vector2(float(e[2]), float(e[4])).rotated(-float(b[2]))
		out.append([str(e[0]), q.x, q.y])
	return out


static func place_options() -> Array:
	var out := []
	for p in PLACES:
		out.append(["p:" + str(p[0]), str(p[0])])
	for e in INSIDE:
		out.append(["p:" + str(e[0]), str(e[0])])
	return out


# =============================================================================================================================
# the ridge in the height map (called from bergtal.generate(), before the colours)
# =============================================================================================================================
static func sculpt(hm: PackedFloat32Array, n: int, lo: float, step: float) -> PackedFloat32Array:
	"""the «Schafgrat»: a narrow crest on the edge of the east plateau, high over the Gumpisee. The profile (1 - d/w)^1.5 gives
	flanks of 55–70°; the crest is exactly on a grid column, so the path along it has no steps."""
	var i0 := maxi(0, int(round((RIDGE_X - RIDGE_W - lo) / step)))
	var i1 := mini(n - 1, int(round((RIDGE_X + RIDGE_W - lo) / step)))
	var j0 := maxi(0, int(round((RIDGE_Z0 - lo) / step)))
	var j1 := mini(n - 1, int(round((RIDGE_Z1 - lo) / step)))
	for j in range(j0, j1 + 1):
		var z := lo + j * step
		var u := (z - RIDGE_Z0) / (RIDGE_Z1 - RIDGE_Z0)
		var a := RIDGE_A * smoothstep(0.0, 0.16, u) * (1.0 - smoothstep(0.84, 1.0, u)) * (0.88 + 0.12 * sin(u * 31.0))
		for i in range(i0, i1 + 1):
			var d := absf(lo + i * step - RIDGE_X)
			if d < RIDGE_W:
				hm[j * n + i] += a * pow(1.0 - d / RIDGE_W, 1.5)
	return hm


# =============================================================================================================================
# building helpers (a building = transform in the valley + its parts; the parts go into the library nets)
# =============================================================================================================================
func _bld(c: Vector2, rot: float, foot := Vector2(4, 4), key := "") -> Dictionary:
	"""a building on the highest ground of its footprint (the floor never has ground poking through); the plinth goes down"""
	var hi := -INF
	var lo := INF
	for fx in [-0.5, 0.0, 0.5]:
		for fz in [-0.5, 0.0, 0.5]:
			var q := c + Vector2(foot.x * fx, foot.y * fz).rotated(-rot)
			var h: float = bt.H(q.x, q.y)
			hi = maxf(hi, h)
			lo = minf(lo, h)
	var b := {"xf": Transform3D(Basis(Vector3.UP, rot), Vector3(c.x, hi, c.y)), "rot": rot, "c": c, "y": hi, "drop": hi - lo, "p": [], "subs": []}
	if key != "":
		_xf[key] = b["xf"]
	return b


func _bk(key: String, foot: Vector2) -> Dictionary:
	var d := building(key)
	return _bld(Vector2(d[0], d[1]), float(d[2]), foot, key)


func _sub(b: Dictionary, x: float, y: float, z: float, ry := 0.0) -> Dictionary:
	"""a piece of furniture turned on its own (parts in its own frame)"""
	var sb := {"xf": (b["xf"] as Transform3D) * Transform3D(Basis(Vector3.UP, ry), Vector3(x, y, z)), "rot": float(b["rot"]) + ry, "p": [], "subs": []}
	(b["subs"] as Array).append(sb)
	return sb


func _bx(b: Dictionary, sx: float, sy: float, sz: float, x: float, y: float, z: float, col, tk = "stone", lod := "small", ry := 0.0, rx := 0.0, rz := 0.0) -> void:
	(b["p"] as Array).append([Bib.B(sx, sy, sz, x, y, z, col, rx, ry, rz, tk), lod])


func _pt(b: Dictionary, part: Array, lod := "small") -> void:
	(b["p"] as Array).append([part, lod])


func _flush(b: Dictionary) -> void:
	var ck: String = bib._cell_key((b["xf"] as Transform3D).origin)
	for pr in b["p"]:
		bib._part(pr[0], b["xf"], "stone", str(pr[1]), ck)
	b["p"] = []
	for sb in b["subs"]:
		_flush(sb)
	b["subs"] = []


func _obst(b: Dictionary, mid: Vector2, sx: float, sz: float, ang: float, h: float) -> void:
	var c: Vector3 = bt.W((b["xf"] as Transform3D) * Vector3(mid.x, 0, mid.y))
	m.add_obstacle_box(c, sx, sz, bt.wrot(float(b["rot"]) + ang))
	m.set_obstacle_height(h)


func _wall(b: Dictionary, a: Vector2, e: Vector2, y0: float, y1: float, t: float, col, tk = "stone", holes := [], ob := true, lod := "far") -> void:
	"""a wall from a to e (local x, z) from height y0 to y1, thickness t; holes: [[distance from a to the middle, width, bottom,
	top]]. Pieces that stand on the floor are obstacles (people, animals and the rover go only through the doors)."""
	var L := a.distance_to(e)
	if L < 0.01:
		return
	var d := (e - a) / L
	var ang := atan2(-d.y, d.x)
	var hs: Array = holes.duplicate()
	hs.sort_custom(func(p, q): return float(p[0]) < float(q[0]))
	var pos := 0.0
	var pieces := []
	for h in hs:
		var h0 := float(h[0]) - float(h[1]) / 2.0
		var h1 := float(h[0]) + float(h[1]) / 2.0
		if h0 > pos:
			pieces.append([pos, h0, y0, y1])
		if float(h[2]) > y0 + 0.01:
			pieces.append([h0, h1, y0, float(h[2])])
		if float(h[3]) < y1 - 0.01:
			pieces.append([h0, h1, float(h[3]), y1])
		pos = h1
	if pos < L:
		pieces.append([pos, L, y0, y1])
	for pc in pieces:
		var ln := float(pc[1]) - float(pc[0])
		if ln < 0.01:
			continue
		var mid := a + d * (float(pc[0]) + ln / 2.0)
		var hh := float(pc[3]) - float(pc[2])
		_pt(b, Bib.B(ln, hh, t, mid.x, float(pc[2]) + hh / 2.0, mid.y, col, 0, rad_to_deg(ang), 0, tk), lod)
		if ob and float(pc[2]) < y0 + 0.3 and hh > 0.5:
			_obst(b, mid, ln, t + 0.1, ang, float(pc[3]))


func _frame(b: Dictionary, a: Vector2, e: Vector2, at: float, w: float, y0: float, y1: float, t: float, col, cross := true, shutters := "") -> void:
	"""the frame of a window (with cross) or a door in the wall a-e at distance «at»"""
	var d := (e - a).normalized()
	var deg := rad_to_deg(atan2(-d.y, d.x))
	var c := a + d * at
	var n := Vector2(-d.y, d.x)
	var hh := y1 - y0
	for sd in [-1.0, 1.0]:
		var q = c + d * sd * (w / 2.0 - 0.03)
		_pt(b, Bib.B(0.07, hh, t + 0.04, q.x, y0 + hh / 2.0, q.y, col, 0, deg, 0, "tree"))
	_pt(b, Bib.B(w, 0.07, t + 0.04, c.x, y1 - 0.03, c.y, col, 0, deg, 0, "tree"))
	if cross:
		_pt(b, Bib.B(w, 0.08, t + 0.06, c.x, y0 + 0.02, c.y, "8a8478", 0, deg, 0, "stone"))      # the sill
		_pt(b, Bib.B(0.04, hh, 0.04, c.x, y0 + hh / 2.0, c.y, col, 0, deg, 0, "tree"))
		_pt(b, Bib.B(w, 0.04, 0.04, c.x, y0 + hh * 0.62, c.y, col, 0, deg, 0, "tree"))
	if shutters != "":                                             # opened shutters on the outside (red-white: the Swiss alp hut)
		for sd in [-1.0, 1.0]:
			var q = c + d * sd * (w * 0.75 + 0.02) + n * (t / 2.0 + 0.04)
			_pt(b, Bib.B(w / 2.0, hh + 0.06, 0.04, q.x, y0 + hh / 2.0, q.y, shutters, 0, deg, 0, "tree"))
			_pt(b, Bib.B(w / 2.0 - 0.1, 0.06, 0.045, q.x, y0 + hh * 0.5, q.y, "f2f2f2", 0, deg, 0, "tree"))


func _leaf(b: Dictionary, a: Vector2, e: Vector2, at: float, w: float, h: float, open_deg: float, col, inward := 1.0, y0 := 0.0) -> void:
	"""a door leaf, opened by open_deg (fixed part)"""
	var d := (e - a).normalized()
	var ang := atan2(-d.y, d.x) + deg_to_rad(open_deg) * inward
	var hinge := a + d * (at - w / 2.0)
	var dir := Vector2(cos(ang), -sin(ang))
	var c := hinge + dir * (w / 2.0)
	_pt(b, Bib.B(w, h, 0.05, c.x, y0 + h / 2.0, c.y, col, 0, rad_to_deg(ang), 0, "tree"), "mid")
	_pt(b, Bib.B(0.04, 0.04, 0.12, c.x + dir.x * w * 0.38, y0 + 1.0, c.y + dir.y * w * 0.38, "2a2a2a", 0, rad_to_deg(ang), 0, "metal"))


func _deck(b: Dictionary, lc: Vector2, half: Vector2, y := 0.0) -> void:
	"""the floor as a walkable «deck» of bergtal.gd (people, animals and the rover stand on it, also under the ground)"""
	var c: Vector2 = (b["c"] as Vector2) + lc.rotated(-float(b["rot"]))
	bt.decks.append([c, half, -float(b["rot"]), float(b["y"]) + y])


func _plinth(b: Dictionary, w: float, d: float, col := "8a847a") -> void:
	var dr := float(b["drop"]) + 0.6
	_bx(b, w + 0.12, dr, d + 0.12, 0, -dr / 2.0 + 0.04, 0, col, "stone", "far")


func _steps(b: Dictionary, x: float, z: float, w: float, dz := 1.0) -> void:
	"""steps down in front of a door (the building stands on the highest ground of its footprint)"""
	var q := _lx(b, x, z + dz * 0.6)
	var drop := float(b["y"]) - float(bt.H(q.x, q.y))
	var n := mini(8, int(ceil(drop / 0.18)))
	var bottom := -drop - 0.25
	for k in range(n):
		var top := -0.18 * (k + 1)
		if top - bottom < 0.05:
			break
		_bx(b, w, top - bottom, 0.3, x, (top + bottom) / 2.0, z + dz * (0.15 + 0.3 * k), "8a847a", "stone", "mid")


func _lx(b: Dictionary, x: float, z: float) -> Vector2:
	"""local -> valley (x, z)"""
	return (b["c"] as Vector2) + Vector2(x, z).rotated(-float(b["rot"]))


func _V(b: Dictionary, x: float, y: float, z: float) -> Vector3:
	"""local -> valley"""
	return (b["xf"] as Transform3D) * Vector3(x, y, z)


func _label(b: Dictionary, text: String, lp: Vector3, ry := 0.0, flat := false, size := 26, px := 0.004, col := Color(0.1, 0.09, 0.08), rng := 22.0) -> Label3D:
	var l := Label3D.new()
	l.text = T.t(text)
	var bs := Basis(Vector3.UP, ry)
	if flat:
		bs = bs * Basis(Vector3.RIGHT, -PI / 2.0)
	l.transform = (b["xf"] as Transform3D) * Transform3D(bs, lp)
	l.font_size = size
	l.pixel_size = px
	l.modulate = col
	l.outline_size = 0
	l.layers = 1
	l.visibility_range_end = rng
	l.autowrap_mode = TextServer.AUTOWRAP_OFF
	bt.tal.add_child(l)
	return l


func _flame(b: Dictionary, lp: Vector3, energy := 0.5, rng := 4.5) -> void:
	"""a real light of candles (not Lite): only on when the view is near (cheap), flickers"""
	if lite:
		return
	var ol := OmniLight3D.new()
	ol.transform = (b["xf"] as Transform3D) * Transform3D(Basis(), lp)
	ol.light_color = Color(1.0, 0.72, 0.4)
	ol.omni_range = rng
	ol.light_energy = energy
	ol.shadow_enabled = false
	ol.visible = false
	bt.tal.add_child(ol)
	_flames.append([ol, energy, ol.position])


# ---- furniture ---------------------------------------------------------------------------------------------------------------
func _bunk(b: Dictionary, x: float, z: float, ry: float, levels := 2, L := 1.95, W := 0.85, frame := "6a4a2c", made := true, metal := false) -> void:
	var f := _sub(b, x, 0, z, ry)
	var tk := "metal" if metal else "tree"
	var hgt := 0.35 + 0.85 * levels
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			_bx(f, 0.06, hgt, 0.06, sx * (L / 2.0 - 0.03), hgt / 2.0, sz * (W / 2.0 - 0.03), frame, tk)
	for k in range(levels):
		var y := 0.35 + 0.85 * k
		_bx(f, L, 0.05, W, 0, y, 0, frame, tk)
		if made:
			_bx(f, L - 0.1, 0.1, W - 0.08, 0, y + 0.08, 0, ["5a6a8a", "8a3a2a", "6a6a5a"][k % 3], "tent")       # mattress / blanket
			if full:
				_bx(f, 0.32, 0.1, W - 0.25, L / 2.0 - 0.25, y + 0.17, 0, "e8e2d4", "tent")                       # pillow
				_bx(f, 0.36, 0.14, W - 0.3, -L / 2.0 + 0.3, y + 0.19, 0, "8a2a22", "tent")                        # folded blanket


func _table(b: Dictionary, x: float, z: float, ry: float, L := 1.6, W := 0.8, col := "7a5434") -> void:
	var f := _sub(b, x, 0, z, ry)
	_bx(f, L, 0.05, W, 0, 0.75, 0, col, "tree", "mid")
	for sx in [-1.0, 1.0]:
		_bx(f, 0.07, 0.72, W - 0.2, sx * (L / 2.0 - 0.15), 0.37, 0, col, "tree")


func _bench(b: Dictionary, x: float, z: float, ry: float, L := 1.6, col := "6a4a2c") -> void:
	var f := _sub(b, x, 0, z, ry)
	_bx(f, L, 0.05, 0.32, 0, 0.45, 0, col, "tree")
	for sx in [-1.0, 1.0]:
		_bx(f, 0.06, 0.43, 0.28, sx * (L / 2.0 - 0.12), 0.22, 0, col, "tree")


func _chair(b: Dictionary, x: float, z: float, ry: float, col := "6a4a2c", sheet := false) -> void:
	var f := _sub(b, x, 0, z, ry)
	if sheet:                                                         # a dust sheet over the chair
		_bx(f, 0.5, 0.95, 0.5, 0, 0.47, 0, "d8d4c8", "tent")
		return
	_bx(f, 0.42, 0.04, 0.42, 0, 0.46, 0, col, "tree")
	_bx(f, 0.42, 0.5, 0.04, 0, 0.72, -0.19, col, "tree")
	if full:
		for sx in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				_bx(f, 0.04, 0.45, 0.04, sx * 0.18, 0.22, sz * 0.18, col, "tree")


func _shelf(b: Dictionary, x: float, z: float, ry: float, L := 1.4, H := 1.6, n := 4, col := "6a4a2c", things := true) -> void:
	var f := _sub(b, x, 0, z, ry)
	for sx in [-1.0, 1.0]:
		_bx(f, 0.04, H, 0.32, sx * L / 2.0, H / 2.0, 0, col, "tree")
	for k in range(n):
		var y := 0.15 + (H - 0.2) * k / maxf(1.0, n - 1.0)
		_bx(f, L, 0.03, 0.32, 0, y, 0, col, "tree")
		if things and full and k > 0:
			for i in range(3):
				var px := -L * 0.35 + i * L * 0.33
				match (k + i) % 3:
					0:
						_pt(f, Bib.C(0.08, 0.16, px, y + 0.09, 0, "c8c0b0", 0, 0, 0, 0, "stone"))            # a jar
					1:
						_bx(f, 0.24, 0.02, 0.24, px, y + 0.03, 0, "e8e2d4", "stone")                     # plates
					_:
						_pt(f, Bib.C(0.1, 0.14, px, y + 0.08, 0, "4a4a4e", 0, 0, 0, 0, "metal"))            # a pot


func _woodstove(b: Dictionary, x: float, z: float, ry: float, pipe := 2.3, warm := false) -> void:
	"""Holzherd / Sparherd aus Gusseisen (Selbstversorger: kalt, der Hinweis sagt «Ofen löschen»)"""
	var f := _sub(b, x, 0, z, ry)
	var tk = 35.0 if warm else "metal"
	_bx(f, 0.9, 0.78, 0.6, 0, 0.39, 0, "2a2a2c", tk, "mid")
	_bx(f, 0.92, 0.04, 0.62, 0, 0.8, 0, "4a4a4e", tk)
	_bx(f, 0.3, 0.22, 0.03, -0.2, 0.45, 0.31, "1a1a1a", tk)                    # the fire door
	_bx(f, 0.06, 0.03, 0.04, -0.2, 0.6, 0.33, "b8a070", "metal")
	_pt(f, Bib.C(0.07, pipe - 0.8, 0.3, 0.8 + (pipe - 0.8) / 2.0, -0.15, "2a2a2c", 0, 0, 0, 0, "metal"))
	if full:
		_pt(f, Bib.C(0.11, 0.16, -0.15, 0.9, 0.05, "6a6a6e", 0, 0, 0, 0, "metal"))           # the kettle
		_pt(f, Bib.C(0.2, 0.42, 0.75, 0.21, 0.1, "6a4a2c", 0, 0, 0, 0, "tree"))              # the wood basket
		for i in range(4):
			_pt(f, Bib.C(0.05, 0.4, 0.68 + 0.05 * (i % 2), 0.48, 0.05 + 0.06 * i, "8a6a4a", 0, 0, 0, 90, "tree"))


func _book(b: Dictionary, x: float, y: float, z: float, ry: float, title: String, left: String, right: String) -> void:
	"""an open book (hut book, bivouac book, guest book): pages with handwriting, the title on the cover"""
	var f := _sub(b, x, y, z, ry)
	_bx(f, 0.44, 0.02, 0.3, 0, 0.01, 0, "6a2a1a", "tent")
	_bx(f, 0.21, 0.015, 0.28, -0.108, 0.025, 0, "f2ecdc", "tent")
	_bx(f, 0.21, 0.015, 0.28, 0.108, 0.025, 0, "f2ecdc", "tent")
	_pt(f, Bib.C(0.004, 0.16, 0.16, 0.035, 0.1, "c8a030", 0, 0, 0, 90, "tree"))             # the pencil
	var fx: Transform3D = f["xf"]
	for side in [[-0.108, left], [0.108, right]]:
		var l := Label3D.new()
		l.text = str(side[1])
		l.transform = fx * Transform3D(Basis(Vector3.RIGHT, -PI / 2.0), Vector3(float(side[0]), 0.036, 0))
		l.font_size = 22
		l.pixel_size = 0.0009
		l.width = 200.0
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.modulate = Color(0.12, 0.12, 0.3)
		l.outline_size = 0
		l.visibility_range_end = 8.0
		bt.tal.add_child(l)
	var lt := Label3D.new()
	lt.text = T.t(title)
	lt.transform = fx * Transform3D(Basis(Vector3.RIGHT, -PI / 2.0), Vector3(0, 0.04, 0.17))
	lt.font_size = 22
	lt.pixel_size = 0.0012
	lt.modulate = Color(0.25, 0.1, 0.05)
	lt.outline_size = 0
	lt.visibility_range_end = 10.0
	bt.tal.add_child(lt)


func _candles(b: Dictionary, x: float, y: float, z: float, n: int, lit := true, r := 0.18) -> void:
	for i in range(n):
		var a := i * 2.39
		var q := Vector2(cos(a), sin(a)) * r * sqrt((i + 0.5) / n)
		var hh := 0.08 + 0.05 * ((i * 7) % 3)
		_pt(b, Bib.C(0.018, hh, x + q.x, y + hh / 2.0, z + q.y, "f2ead0", 0, 0, 0, 0, 30.0 if lit else "tent"))
		if lit:
			_pt(b, Bib.S(0.012, 0.035, x + q.x, y + hh + 0.02, z + q.y, "*ffc860", 60.0))


func _sign(b: Dictionary, text: String, lp: Vector3, ry := 0.0, w := 0.9, col := "e8e0cc", tcol := Color(0.1, 0.08, 0.06), size := 30) -> void:
	"""a small board on the wall with text"""
	var f := _sub(b, lp.x, lp.y, lp.z, ry)
	_bx(f, w, 0.32, 0.03, 0, 0, 0, col, "tree")
	_label(b, text, lp + Basis(Vector3.UP, ry) * Vector3(0, 0, 0.025), ry, false, size, 0.0035, tcol, 14.0)


# =============================================================================================================================
# building all
# =============================================================================================================================
func build() -> void:
	var t0 := Time.get_ticks_msec()
	var n0: int = m.obstacles.size()
	_hut()
	_bivouac()
	_chapel()
	_hospice()
	_dairy()
	_bunker()
	_barrack()
	_lift_stations()
	_cave()
	_pools()
	_glacier_gate()
	_moor_lake()
	_summit()
	_tower()
	_ridge()
	_saeumerweg()
	_alp_ruins()
	_register()
	m.anims.append(Callable(self, "_tick"))
	info = {"ms": Time.get_ticks_msec() - t0, "lite": lite, "obstacles": m.obstacles.size() - n0, "decks": bt.decks.size(),
			"lights": _flames.size(), "places": PLACES.size(), "inside": INSIDE.size(), "discoveries": ENT.size()}


# ---- Selbstversorgerhütte Alp Tschuggen ---------------------------------------------------------------------------------------------
func _hut() -> void:
	var w := 9.0
	var d := 7.5
	var b := _bk("huette", Vector2(w, d))
	_plinth(b, w, d, "a49c90")
	var stone := "a49c90"
	var wood := "5a3a22"
	var t := 0.5
	var fz := d / 2.0 - t / 2.0
	var bz := -d / 2.0 + t / 2.0
	var sx := w / 2.0 - t / 2.0
	var door_x := -w * 0.25
	# ground floor (stone): Stube with stove, table, hut book; the door at the front
	_wall(b, Vector2(-w / 2.0, fz), Vector2(w / 2.0, fz), 0, 2.4, t, stone, "stone", [[door_x + w / 2.0, 1.0, 0.0, 2.0], [0.6 + w / 2.0, 0.6, 1.0, 1.6], [2.8 + w / 2.0, 0.6, 1.0, 1.6]])
	_wall(b, Vector2(-w / 2.0, bz), Vector2(w / 2.0, bz), 0, 2.4, t, stone, "stone", [[w / 2.0 - 1.5, 0.5, 1.2, 1.6]])
	_wall(b, Vector2(-sx, bz + t / 2.0), Vector2(-sx, fz - t / 2.0), 0, 2.4, t, stone, "stone", [[d / 2.0 - t, 0.6, 1.0, 1.6]])
	_wall(b, Vector2(sx, bz + t / 2.0), Vector2(sx, fz - t / 2.0), 0, 2.4, t, stone)
	for xx in [0.6, 2.8]:
		_frame(b, Vector2(-w / 2.0, fz), Vector2(w / 2.0, fz), xx + w / 2.0, 0.6, 1.0, 1.6, t, "5a3a22")
	_frame(b, Vector2(-w / 2.0, fz), Vector2(w / 2.0, fz), door_x + w / 2.0, 1.0, 0.0, 2.0, t, "4a3220", false)
	_leaf(b, Vector2(-w / 2.0, fz - t / 2.0), Vector2(w / 2.0, fz - t / 2.0), door_x + w / 2.0, 0.95, 1.95, 75.0, "4a3220", 1.0)
	_bx(b, w - 0.4, 0.06, d - 0.4, 0, 0.03, 0, "6a5a48", "tree", "mid")                         # the floor (boards)
	# the upper floor (wood): Matratzenlager under the roof; floor with the hatch for the ladder
	_bx(b, w - 0.2, 0.1, d - 3.2, 0, 2.4, -1.4, "6a4a2c", "tree", "mid")
	_bx(b, w - 1.6, 0.1, 3.0, -0.7, 2.4, d / 2.0 - 1.6, "6a4a2c", "tree", "mid")
	var tw := 0.14
	var fz2 := d / 2.0 - tw / 2.0
	var u_holes := [[-w * 0.3 + w / 2.0, 0.55, 3.3, 3.9], [0.05 + w / 2.0, 0.55, 3.3, 3.9], [w * 0.3 + w / 2.0, 0.55, 3.3, 3.9]]
	_wall(b, Vector2(-w / 2.0, fz2), Vector2(w / 2.0, fz2), 2.4, 4.7, tw, wood, "tree", u_holes, false)
	_wall(b, Vector2(-w / 2.0, -fz2), Vector2(w / 2.0, -fz2), 2.4, 4.7, tw, wood, "tree", [], false)
	for sd in [-1.0, 1.0]:
		_wall(b, Vector2(sd * (w / 2.0 - tw / 2.0), -fz2), Vector2(sd * (w / 2.0 - tw / 2.0), fz2), 2.4, 4.7, tw, wood, "tree", [[d / 2.0, 0.55, 3.3, 3.9]], false)
		_frame(b, Vector2(sd * (w / 2.0 - tw / 2.0), -fz2), Vector2(sd * (w / 2.0 - tw / 2.0), fz2), d / 2.0, 0.55, 3.3, 3.9, tw, "f2f2f2", true, "b8241c")
	for hh in u_holes:
		_frame(b, Vector2(-w / 2.0, fz2), Vector2(w / 2.0, fz2), float(hh[0]), 0.55, 3.3, 3.9, tw, "f2f2f2", true, "b8241c")
	_pt(b, Bib.P(d + 1.0, 1.6, w + 1.2, 0, 5.5, 0, "7a7670", 0, 90, 0), "far")                    # stone slab roof
	_bx(b, 0.7, 1.8, 0.7, w * 0.3, 6.2, 0, "8a8378", "stone", "far")                               # the chimney
	_bx(b, 2.0, 0.08, 0.45, w * 0.18, 0.45, d / 2.0 + 0.6, "8a5a32", "tree", "mid")              # the bench in front
	_bx(b, 1.6, 0.3, 0.06, door_x, 2.15, d / 2.0 + 0.04, "e8dcc0", "tree", "mid")                 # the name board
	_label(b, "Selbstversorgerhütte Alp Tschuggen", Vector3(door_x, 2.15, d / 2.0 + 0.08), 0.0, false, 30, 0.01, Color(0.16, 0.1, 0.06), 60.0)
	_sign(b, "Selbstversorgerhütte\nHolz im Schopf, Ofen löschen\nKasse: 15 Fr. pro Nacht\nDanke und gute Tour!", Vector3(door_x + 1.0, 1.55, d / 2.0 + 0.04), 0.0, 0.62, "f4f0e4", Color(0.1, 0.1, 0.12), 18)
	_steps(b, door_x, d / 2.0, 1.1)
	# inside: stove (cold - «Ofen löschen»), table with the hut book, benches, shelves, ladder
	_woodstove(b, 3.0, -2.6, 0.0, 2.35)
	_table(b, 2.3, 1.8, 0.0, 1.8, 0.85)
	_bench(b, 2.3, 2.7, 0.0, 1.8)
	_bench(b, 2.3, 0.95, 0.0, 1.8)
	_bench(b, 0.7, 1.8, PI / 2.0, 1.4)
	_book(b, 2.0, 0.78, 1.8, 0.2, "Hüttenbuch Alp Tschuggen",
			"12.8. Nebel, aber der Ofen hat gezogen. Danke! – Familie Brunner\n\n15.8. Les vaches nous ont réveillés à 5 h. Magnifique! – Claire",
			"21.8. Holz nachgefüllt, 15 Fr. in die Kasse. – Ruedi & Vreni\n\n2.9. Sternenhimmel wie noch nie. Grazie! – Luca")
	_shelf(b, -1.2, -3.0, 0.0, 1.6, 1.7, 4)
	_shelf(b, 1.0, -3.0, 0.0, 1.2, 1.4, 3)
	_bx(b, 0.3, 0.22, 0.12, door_x + 1.0, 1.25, -d / 2.0 + t + 0.06, "4a5a3a", "metal")                # the cash box
	_sign(b, "Hüttenordnung\n1. Holz nur aus dem Schopf\n2. Abfall wieder mitnehmen\n3. Tür gut schliessen (Kühe!)", Vector3(door_x - 1.3, 1.5, -d / 2.0 + t + 0.02), 0.0, 0.7, "f4f0e4", Color(0.1, 0.1, 0.12), 16)
	_bx(b, 1.6, 0.06, 0.5, -3.3, 0.9, 1.6, "8a8a86", "stone")                                          # the stone sink
	if full:
		_pt(b, Bib.C(0.13, 0.3, -3.9, 0.15, 0.6, "6a4a2c", 0, 0, 0, 0, "tree"))                         # water bucket
		_pt(b, Bib.C(0.07, 0.22, 2.3, 0.89, 2.2, "2a3a2a", 0, 0, 0, 0, "glass"))                        # candle in a bottle
		_candles(b, 2.3, 1.0, 2.2, 1, false, 0.0)
		_pt(b, Bib.C(0.08, 0.25, -w / 2.0 + t + 0.15, 1.9, -0.5, "3a3a3a", 0, 0, 0, 0, "metal"))       # storm lantern on a hook
		_bx(b, 0.5, 0.6, 0.3, -3.6, 0.3, -2.5, "6a4a2c", "tree")                                         # wood box
		for k in range(5):
			_bx(b, 0.12, 0.012, 0.012, -3.2 + k * 0.1, 1.15, d / 2.0 - t - 0.04, "6a6a6a", "metal")      # hooks for clothes
	# the ladder up through the hatch
	var lad := _sub(b, 3.6, 0, -0.2, 0.0)
	for sd in [-0.22, 0.22]:
		_pt(lad, Bib.B(0.05, 2.7, 0.05, sd, 1.3, -0.15, "7a5434", 0, 0, 12.0 * 0.0, "tree"))
	for k in range(8):
		_bx(lad, 0.44, 0.04, 0.04, 0, 0.25 + k * 0.3, -0.15, "7a5434", "tree")
	# upstairs: Pritschen (two levels along the back, one along the front)
	var plat := _sub(b, 0, 2.45, 0, 0.0)
	_bx(plat, w - 0.6, 0.06, 2.0, 0, 0.4, -d / 2.0 + 1.25, "7a5434", "tree", "mid")
	_bx(plat, w - 0.6, 0.06, 2.0, 0, 1.25, -d / 2.0 + 1.25, "7a5434", "tree", "mid")
	_bx(plat, w - 2.4, 0.06, 1.8, -0.9, 0.4, d / 2.0 - 1.15, "7a5434", "tree", "mid")
	for k in range(6 if full else 3):
		var px := -w / 2.0 + 0.9 + k * (w - 1.6) / 5.0
		for lvl in [0.4, 1.25]:
			_bx(plat, 0.72, 0.08, 1.85, px, lvl + 0.07, -d / 2.0 + 1.25, ["5a6a8a", "6a6a5a", "8a3a2a"][k % 3], "tent")
			if full:
				_bx(plat, 0.5, 0.12, 0.3, px, lvl + 0.15, -d / 2.0 + 0.45, "8a2a22" if k % 2 == 0 else "4a5a7a", "tent")    # folded blankets
		if k < 4:
			_bx(plat, 0.72, 0.08, 1.7, px, 0.47, d / 2.0 - 1.15, "6a6a5a", "tent")
	for px2 in [-w / 2.0 + 0.4, 0.0, w / 2.0 - 0.4]:
		_bx(plat, 0.08, 1.4, 0.08, px2, 0.7, -d / 2.0 + 2.2, "6a4a2c", "tree")
	_flush(b)
	_deck(b, Vector2.ZERO, Vector2(w / 2.0 - t, d / 2.0 - t), 0.06)
	ent_pos["berg.ort.huette"] = _V(b, 0.8, 1.2, 0.0)
	# the building's obstacle for the line of sight from outside: the walls carry it (height 4.7 for the upper floor)


# ---- Biwakschachtel Chüebodehorn ---------------------------------------------------------------------------------------------------
func _bivouac() -> void:
	var b := _bk("biwak", Vector2(2.8, 3.2))
	var col := "c8402a"
	var t := 0.08
	var W := 2.5
	var D := 3.0
	_bx(b, W + 0.3, 0.4 + float(b["drop"]), D + 0.3, 0, 0.2 - float(b["drop"]) / 2.0, 0, "8a857d", "stone", "far")   # foundation
	var y0 := 0.4
	var fz := D / 2.0 - t / 2.0
	_wall(b, Vector2(-W / 2.0, fz), Vector2(W / 2.0, fz), y0, y0 + 1.6, t, col, "metal", [[W / 2.0 + 0.45, 0.7, y0, y0 + 1.55], [W / 2.0 - 0.6, 0.4, y0 + 1.0, y0 + 1.35]])
	_wall(b, Vector2(-W / 2.0, -fz), Vector2(W / 2.0, -fz), y0, y0 + 1.6, t, col, "metal")
	for sd in [-1.0, 1.0]:
		_wall(b, Vector2(sd * (W / 2.0 - t / 2.0), -fz), Vector2(sd * (W / 2.0 - t / 2.0), fz), y0, y0 + 1.6, t, col, "metal")
	# the round roof (four plates on an arc) and the round gable ends
	var R := 1.25
	for k in range(4):
		var a := deg_to_rad(22.5 + 45.0 * k)
		var rr := R * cos(deg_to_rad(22.5))
		_pt(b, Bib.B(2.0 * R * sin(deg_to_rad(22.5)) + 0.05, t, D, cos(a) * rr, y0 + 1.6 + sin(a) * rr, 0, col, 0, 0, rad_to_deg(a) + 90.0, "metal"), "far")
		_pt(b, Bib.B(2.0 * R * sin(deg_to_rad(22.5)), 0.03, D - 0.1, cos(a) * (rr - 0.08), y0 + 1.6 + sin(a) * (rr - 0.08), 0, "b89a6a", 0, 0, rad_to_deg(a) + 90.0, "tree"))
	for sd in [-1.0, 1.0]:
		_bx(b, 1.8, 0.7, t, 0, y0 + 1.95, sd * fz, col, "metal", "far")
		_bx(b, 1.0, 0.35, t, 0, y0 + 2.45, sd * fz, col, "metal", "far")
	for xx in [-1.0, 1.0]:
		_pt(b, Bib.ROD(Vector3(xx * 1.1, y0 + 2.4, 0), Vector3(xx * 2.6, 0.0, -0.6), 0.03, "8a8a8a"), "mid")         # guy wires (storms)
	_frame(b, Vector2(-W / 2.0, fz), Vector2(W / 2.0, fz), W / 2.0 - 0.6, 0.4, y0 + 1.0, y0 + 1.35, t, "d8d8d8")
	_leaf(b, Vector2(-W / 2.0, fz + 0.05), Vector2(W / 2.0, fz + 0.05), W / 2.0 + 0.45, 0.68, 1.5, -100.0, "6a2a1a", 1.0, y0)
	_label(b, "Biwak Chüebodehorn", Vector3(-0.3, y0 + 1.75, D / 2.0 + 0.05), 0.0, false, 28, 0.008, Color(0.95, 0.95, 0.95), 50.0)
	# inside: wooden lining, floor, bunks across the back, a shelf with the book and the emergency box
	var inn := _sub(b, 0, y0, 0, 0.0)
	_bx(inn, W - 0.2, 0.05, D - 0.2, 0, 0.03, 0, "a8885a", "tree", "mid")
	_bx(inn, W - 0.2, 1.5, 0.03, 0, 0.8, -fz + 0.07, "b89a6a", "tree")
	for sd in [-1.0, 1.0]:
		_bx(inn, 0.03, 1.5, D - 0.2, sd * (W / 2.0 - 0.09), 0.8, 0, "b89a6a", "tree")
	for lvl in [0.45, 1.3]:
		_bx(inn, W - 0.2, 0.05, 1.3, 0, lvl, -D / 2.0 + 0.75, "8a6a40", "tree", "mid")
		for k in range(3):
			_bx(inn, 0.66, 0.08, 1.2, -0.75 + k * 0.75, lvl + 0.07, -D / 2.0 + 0.75, ["5a6a8a", "6a6a5a", "8a3a2a"][(k + int(lvl)) % 3], "tent")
			if full:
				_bx(inn, 0.5, 0.14, 0.3, -0.75 + k * 0.75, lvl + 0.18, -D / 2.0 + 0.3, "6a5a4a", "tent")
	_bx(inn, 0.9, 0.04, 0.4, -0.65, 0.72, 0.9, "8a6a40", "tree")                    # folding table
	_bx(inn, 0.04, 0.7, 0.04, -0.65, 0.36, 1.05, "6a6a6a", "metal")
	_book(b, -0.65, y0 + 0.74, 0.88, 0.0, "Biwakbuch",
			"3.8. Gewitter am Grat, hier Unterschlupf gefunden. Danke an alle, die das Biwak pflegen! – M. & S.",
			"19.8. Zu dritt, eng aber warm. Decken wieder gefaltet. – SAC Sektion Bern")
	_bx(inn, 0.5, 0.32, 0.32, 0.8, 0.2, 1.1, "e86a1a", "tent")                         # the emergency box
	_bx(inn, 0.22, 0.06, 0.01, 0.8, 0.28, 1.265, "f2f2f2", "tent")
	_bx(inn, 0.06, 0.22, 0.01, 0.8, 0.28, 1.266, "f2f2f2", "tent")
	_sign(b, "Notruf 112 · Rega 1414\nBitte Biwak sauber verlassen", Vector3(0.6, y0 + 1.25, fz - 0.06), PI, 0.55, "f4f0e4", Color(0.6, 0.05, 0.05), 16)
	if full:
		_candles(b, -0.4, y0 + 0.74, 1.0, 1, false, 0.0)
		_pt(inn, Bib.C(0.05, 0.11, -0.95, 0.8, 0.95, "3a5ab0", 0, 0, 0, 0, "metal"))        # gas cartridge
	_flush(b)
	_deck(b, Vector2.ZERO, Vector2(W / 2.0 - 0.1, D / 2.0 - 0.1), y0 + 0.05)
	ent_pos["berg.ort.biwak"] = _V(b, 0.0, y0 + 1.0, 0.0)


# ---- Kapelle St. Jodern -------------------------------------------------------------------------------------------------------------
func _chapel() -> void:
	var w := 5.0
	var L := 7.0
	var b := _bk("kapelle", Vector2(w, L))
	_plinth(b, w, L)
	var white := "f2eee4"
	var t := 0.5
	var fz := L / 2.0 - t / 2.0
	var sx := w / 2.0 - t / 2.0
	_wall(b, Vector2(-w / 2.0, fz), Vector2(w / 2.0, fz), 0, 3.6, t, white, "stone", [[w / 2.0, 1.2, 0.0, 2.3]])
	_wall(b, Vector2(-w / 2.0, -fz), Vector2(w / 2.0, -fz), 0, 3.6, t, white)
	for sd in [-1.0, 1.0]:
		_wall(b, Vector2(sd * sx, -fz + t / 2.0), Vector2(sd * sx, fz - t / 2.0), 0, 3.6, t, white, "stone", [[L / 2.0 - t - L * 0.2, 0.6, 1.55, 2.85], [L / 2.0 - t + L * 0.2, 0.6, 1.55, 2.85]])
		for zz in [-L * 0.2, L * 0.2]:
			_bx(b, 0.04, 1.3, 0.6, sd * sx, 2.2, zz, "%e8c890", "window", "mid")                          # coloured glass
	_frame(b, Vector2(-w / 2.0, fz), Vector2(w / 2.0, fz), w / 2.0, 1.2, 0.0, 2.3, t, "5a3820", false)
	_leaf(b, Vector2(-w / 2.0, fz + t / 2.0), Vector2(w / 2.0, fz + t / 2.0), w / 2.0, 1.15, 2.25, -80.0, "5a3820", 1.0)
	_pt(b, Bib.P(w + 0.8, 2.4, L + 0.6, 0, 4.8, 0, "5a5652"), "far")
	_bx(b, 1.2, 1.4, 1.2, 0, 6.3, -L / 2.0 + 0.6, white, "stone", "far")
	_pt(b, Bib.K(0.95, 2.0, 0, 8.0, -L / 2.0 + 0.6, "4a4a4e"), "far")
	_bx(b, 0.08, 0.9, 0.08, 0, 9.4, -L / 2.0 + 0.6, "c8a43a", "metal", "far")
	_bx(b, 0.5, 0.08, 0.08, 0, 9.6, -L / 2.0 + 0.6, "c8a43a", "metal", "far")
	_pt(b, Bib.C(0.5, 0.05, 0, 4.4, L / 2.0 + 0.05, "%ffe0a0", 0, 90, 0, 0, "window"), "mid")
	_steps(b, 0.0, L / 2.0, 1.6)
	# inside: stone floor, ceiling, pews, altar, candle stand with burning candles, offering box, holy water
	_bx(b, w - 0.9, 0.05, L - 0.9, 0, 0.03, 0, "9a948a", "stone", "mid")
	_bx(b, w - 0.9, 0.08, L - 0.9, 0, 3.55, 0, "e8e2d4", "stone", "mid")
	var alt := _sub(b, 0, 0, -L / 2.0 + t + 0.5, 0.0)
	_bx(alt, 1.6, 0.25, 1.0, 0, 0.12, 0.1, "9a948a", "stone", "mid")          # the step
	_bx(alt, 1.3, 0.85, 0.6, 0, 0.67, 0, "d8d0c0", "stone", "mid")           # altar
	_bx(alt, 1.36, 0.03, 0.66, 0, 1.11, 0, "f4f2ea", "tent")                 # altar cloth
	_bx(alt, 0.05, 0.6, 0.05, 0, 1.42, -0.15, "c8a43a", "metal")             # cross
	_bx(alt, 0.32, 0.05, 0.05, 0, 1.55, -0.15, "c8a43a", "metal")
	_bx(alt, 1.1, 1.3, 0.05, 0, 2.3, -0.27, "3a4a7a", "tree")                # the picture (Madonna, blue)
	_bx(alt, 1.18, 1.38, 0.04, 0, 2.3, -0.29, "c8a43a", "tree")
	_bx(alt, 0.4, 0.6, 0.06, 0, 2.35, -0.23, "e8d8b0", "tree")
	_candles(b, -0.45, 1.12, -L / 2.0 + t + 0.5, 1, true, 0.0)
	_candles(b, 0.45, 1.12, -L / 2.0 + t + 0.5, 1, true, 0.0)
	for row in range(4 if full else 2):
		for sd in [-1.0, 1.0]:
			var pw := _sub(b, sd * 0.95, 0, -0.6 + row * 1.0, 0.0)
			_bx(pw, 1.5, 0.05, 0.36, 0, 0.45, 0, "6a4a2c", "tree", "mid")
			_bx(pw, 1.5, 0.45, 0.04, 0, 0.8, 0.2, "6a4a2c", "tree")
			_bx(pw, 0.05, 0.9, 0.4, -0.72, 0.45, 0, "5a3a22", "tree")
			_bx(pw, 0.05, 0.9, 0.4, 0.72, 0.45, 0, "5a3a22", "tree")
	# the candle stand (front left): a tray of sand with burning votive candles, the offering box beside
	var cs := Vector3(-w / 2.0 + t + 0.45, 0, L / 2.0 - t - 1.1)
	_bx(b, 0.05, 0.9, 0.05, cs.x, 0.45, cs.z, "3a3a3a", "metal")
	_bx(b, 0.6, 0.06, 0.45, cs.x, 0.92, cs.z, "2a2a2a", "metal")
	_bx(b, 0.56, 0.03, 0.41, cs.x, 0.96, cs.z, "c8b890", "stone")
	_candles(b, cs.x, 0.97, cs.z, 8 if full else 4, true, 0.2)
	_bx(b, 0.3, 0.35, 0.25, cs.x, 0.6, cs.z + 0.7, "4a3a2a", "tree")
	_sign(b, "Kerzen 2 Fr.", Vector3(-w / 2.0 + t + 0.02, 1.25, cs.z + 0.7), PI / 2.0, 0.4, "f4f0e4", Color(0.1, 0.1, 0.1), 18)
	_flame(b, Vector3(cs.x, 1.15, cs.z), 0.55, 4.5)
	_flame(b, Vector3(0, 1.35, -L / 2.0 + t + 0.6), 0.3, 3.5)
	_pt(b, Bib.C(0.13, 0.12, w / 2.0 - t - 0.15, 1.1, L / 2.0 - t - 0.3, "c8c0b0", 0, 0, 0, 0, "stone"))   # holy water
	if full:
		for k in range(5):                                                             # ex-votos (small thank-you pictures)
			_bx(b, 0.02, 0.22, 0.17, w / 2.0 - t - 0.01, 1.7 + 0.3 * (k % 2), -0.8 + k * 0.4, ["c8a43a", "8a3a2a", "3a5a8a"][k % 3], "tree")
	_flush(b)
	_deck(b, Vector2.ZERO, Vector2(w / 2.0 - t, L / 2.0 - t), 0.05)
	ent_pos["berg.ort.kapelle"] = _V(b, 0.0, 1.2, 0.5)


# ---- das alte Hospiz am Furggapass (mehrere Räume; Bühne der späteren Horror-Geschichte) --------------------------------------------
func _hospice() -> void:
	var w := 20.0
	var d := 12.0
	var b := _bk("hospiz", Vector2(w, d))
	_plinth(b, w, d)
	var plaster := "e2dccc"
	var t := 0.7
	var fz := d / 2.0 - t / 2.0
	var sx := w / 2.0 - t / 2.0
	var xs := []
	for i in range(7):
		xs.append(-w * 0.46 + w * 0.92 * (i + 0.5) / 7.0)
	var zs := []
	for i in range(4):
		zs.append(-d * 0.425 + d * 0.85 * (i + 0.5) / 4.0)
	var front_h := []
	var back_h := []
	var side_h := []
	for fl in range(3):
		var y0 := 1.2 + fl * 3.0
		for i in range(7):
			if fl == 0 and i == 3:
				front_h.append([float(xs[i]) + w / 2.0, 1.6, 0.0, 2.5])                 # the main door
			else:
				front_h.append([float(xs[i]) + w / 2.0, 0.9, y0, y0 + 1.2])
		for i in [1, 5]:
			back_h.append([float(xs[i]) + w / 2.0, 0.8, y0 + 0.2, y0 + 1.2])
		for i in range(4):
			side_h.append([float(zs[i]) + d / 2.0 - t, 0.9, y0, y0 + 1.2])
	_wall(b, Vector2(-w / 2.0, fz), Vector2(w / 2.0, fz), 0, 10.0, t, plaster, "stone", front_h)
	_wall(b, Vector2(-w / 2.0, -fz), Vector2(w / 2.0, -fz), 0, 10.0, t, plaster, "stone", back_h)
	for sd in [-1.0, 1.0]:
		_wall(b, Vector2(sd * sx, -fz + t / 2.0), Vector2(sd * sx, fz - t / 2.0), 0, 10.0, t, plaster, "stone", side_h)
	for hh in front_h:
		if float(hh[2]) > 0.5:
			_frame(b, Vector2(-w / 2.0, fz), Vector2(w / 2.0, fz), float(hh[0]), 0.9, float(hh[2]), float(hh[3]), t, "4a4038")
	if full:
		for hh in side_h:
			for sd in [-1.0, 1.0]:
				_frame(b, Vector2(sd * sx, -fz + t / 2.0), Vector2(sd * sx, fz - t / 2.0), float(hh[0]), 0.9, float(hh[2]), float(hh[3]), t, "4a4038")
		for hh in back_h:
			_frame(b, Vector2(-w / 2.0, -fz), Vector2(w / 2.0, -fz), float(hh[0]), 0.8, float(hh[2]), float(hh[3]), t, "4a4038")
	for sd in [-1.0, 1.0]:                                # grey stone band at the bottom of the front
		_bx(b, w / 2.0 - 0.9, 1.0, 0.06, sd * (w / 4.0 + 0.45), 0.5, d / 2.0 + 0.02, "8a8478", "stone", "far")
	_pt(b, Bib.P(w + 1.0, 3.5, d + 1.2, 0, 11.75, 0, "5a5a5e"), "far")
	_bx(b, 0.8, 2.0, 0.8, w * 0.35, 13.0, 0, "d8d2c4", "stone", "far")
	_bx(b, 5.0, 0.12, 2.0, 0, 2.9, d / 2.0 + 1.0, "5a5a5e", "metal", "far")              # the porch roof
	_bx(b, 4.0, 0.7, 0.08, 0, 4.0, d / 2.0 + 0.06, "f2f2f2", "stone", "far")
	_label(b, "Hospiz %d m" % int(float(b["y"]) + 1500.0), Vector3(0, 4.0, d / 2.0 + 0.12), 0.0, false, 60, 0.01, Color(0.42, 0.1, 0.06), 110.0)
	_sign(b, "Hospiz geschlossen\nKein Verkauf · Keine Übernachtung", Vector3(1.4, 1.5, d / 2.0 + 0.04), 0.0, 0.8, "e8e0cc", Color(0.4, 0.05, 0.05), 18)
	# floors and ceilings (the upper floors: empty rooms behind the windows)
	var ix := w / 2.0 - t
	var iz := d / 2.0 - t
	_bx(b, 2 * ix, 0.06, 2 * iz, 0, 0.03, 0, "7a6a58", "tree", "mid")
	_bx(b, 2 * ix, 0.25, 2 * iz - 2.8, 0, 3.0, 1.4, "d8d0c0", "stone", "mid")                    # ceiling with the stair opening at the back
	_bx(b, ix - 1.6, 0.25, 2.8, -(ix + 1.6) / 2.0, 3.0, -iz + 1.4, "d8d0c0", "stone", "mid")
	_bx(b, ix - 1.6, 0.25, 2.8, (ix + 1.6) / 2.0, 3.0, -iz + 1.4, "d8d0c0", "stone", "mid")
	_bx(b, 2 * ix, 0.25, 2 * iz, 0, 6.0, 0, "8a7a68", "stone", "mid")
	_bx(b, 2 * ix, 0.25, 2 * iz, 0, 9.0, 0, "8a7a68", "stone", "mid")
	# the rooms on the ground floor: hall (middle, stairs at the back), Gaststube (front left), kitchen (back left),
	# dormitory (front right), house chapel (back right)
	var it := 0.3
	var ih := 3.0
	var dk := "c8bca8"
	_wall(b, Vector2(-1.6, -iz), Vector2(-1.6, iz), 0, ih, it, dk, "stone", [[iz + 2.5, 0.9, 0.0, 2.1], [iz - 3.2, 0.9, 0.0, 2.1]])
	_wall(b, Vector2(1.6, -iz), Vector2(1.6, iz), 0, ih, it, dk, "stone", [[iz + 2.5, 0.9, 0.0, 2.1], [iz - 3.2, 0.9, 0.0, 2.1]])
	_wall(b, Vector2(-ix, -0.5), Vector2(-1.6, -0.5), 0, ih, it, dk, "stone", [[ix - 7.5, 0.8, 0.0, 2.0]])
	_wall(b, Vector2(1.6, -1.0), Vector2(ix, -1.0), 0, ih, it, dk, "stone")
	var dc := "5a3820"
	hospiz["doors"]["eingang"] = _door_node(b, Vector2(-0.8, d / 2.0 - t + 0.03), 1.6, 2.45, 0.0, 78.0, dc)
	hospiz["doors"]["gaststube"] = _door_node(b, Vector2(-1.6 - it / 2.0, 2.5 - 0.45), 0.9, 2.05, -PI / 2.0, -70.0, dc)
	hospiz["doors"]["kueche"] = _door_node(b, Vector2(-1.6 - it / 2.0, -3.2 - 0.45), 0.9, 2.05, -PI / 2.0, -14.0, dc)
	hospiz["doors"]["schlafsaal"] = _door_node(b, Vector2(1.6 + it / 2.0, 2.5 - 0.45), 0.9, 2.05, -PI / 2.0, 40.0, dc)
	hospiz["doors"]["kapelle"] = _door_node(b, Vector2(1.6 + it / 2.0, -3.2 - 0.45), 0.9, 2.05, -PI / 2.0, 55.0, dc)
	var rooms := {"halle": Vector3(0, 1.5, 1.0), "gaststube": Vector3(-5.6, 1.5, 2.6), "kueche": Vector3(-5.6, 1.5, -2.9),
			"schlafsaal": Vector3(5.6, 1.5, 2.4), "kapelle": Vector3(5.6, 1.5, -3.1), "oben": Vector3(-5.0, 4.6, 3.5)}
	for k in rooms:
		hospiz["rooms"][k] = _V(b, rooms[k].x, rooms[k].y, rooms[k].z)
		var ol := OmniLight3D.new()                         # HOOK (Horror): a light per room, off («Licht im Fenster»)
		ol.transform = (b["xf"] as Transform3D) * Transform3D(Basis(), rooms[k] + Vector3(0, 1.0, 0))
		ol.light_color = Color(1.0, 0.78, 0.5)
		ol.omni_range = 7.0
		ol.light_energy = 0.0
		ol.visible = false
		ol.shadow_enabled = false
		bt.tal.add_child(ol)
		hospiz["lights"][k] = ol
	# hall: stairs up at the back, coat hooks, a bench, the old stand with walking sticks
	var st := _sub(b, 0, 0, -iz + 0.3, 0.0)
	for k in range(15):
		_bx(st, 2.6, 0.2 * (k + 1), 0.28, 0, 0.1 * (k + 1), 0.28 * (14 - k) + 0.14, "6a5040", "tree", "mid")
	_bx(st, 0.05, 0.05, 4.9, 1.25, 2.4, 2.1, "4a3828", "tree", "mid", 0, 37.6)          # the hand rail
	_bench(b, -1.2, 3.8, PI / 2.0, 1.4)
	_sign(b, "Gaststube", Vector3(-1.6 + it / 2.0 + 0.02, 2.4, 2.5), PI / 2.0, 0.6)
	_sign(b, "Küche", Vector3(-1.6 + it / 2.0 + 0.02, 2.4, -3.2), PI / 2.0, 0.5)
	_sign(b, "Schlafsaal", Vector3(1.6 - it / 2.0 - 0.02, 2.4, 2.5), -PI / 2.0, 0.6)
	_sign(b, "Kapelle", Vector3(1.6 - it / 2.0 - 0.02, 2.4, -3.2), -PI / 2.0, 0.5)
	if full:
		for k in range(4):
			_bx(b, 0.04, 0.04, 0.14, -1.6 + it / 2.0 + 0.07, 1.8, 4.4 + k * 0.3, "3a3a3a", "metal")
		_pt(b, Bib.C(0.13, 0.6, 1.2, 0.3, 4.6, "4a3a2a", 0, 0, 0, 0, "tree"))
		for k in range(3):
			_pt(b, Bib.C(0.015, 0.9, 1.18 + 0.03 * k, 0.75, 4.6, "6a5040", 0, 0, 4 * k, 0, "tree"))
	# Gaststube: tables and chairs, tiled stove with bench, corner with the crucifix, buffet, the stopped clock, guest book
	var tables: Array = [Vector2(-7.2, 3.6), Vector2(-4.0, 3.6), Vector2(-7.2, 1.2)] if full else [Vector2(-5.5, 3.2)]
	for tp in tables:
		_table(b, tp.x, tp.y, 0.0, 1.5, 0.8, "6a4a2c")
		for c in [Vector2(-0.45, 0.6), Vector2(0.45, 0.6), Vector2(-0.45, -0.6), Vector2(0.45, -0.6)]:
			_chair(b, tp.x + c.x, tp.y + c.y, 0.0 if c.y < 0 else PI, "5a3a22")
	var ko := _sub(b, -ix + 0.8, 0, -0.5 + it / 2.0 + 0.7, 0.0)                         # Kachelofen (green tiles)
	_bx(ko, 1.4, 1.5, 1.2, 0, 0.75, 0, "4a6a50", "stone", "mid")
	_bx(ko, 1.5, 0.08, 1.3, 0, 1.54, 0, "3a5040", "stone")
	_bx(ko, 1.0, 0.5, 0.9, 0, 1.83, 0, "4a6a50", "stone")
	_bx(ko, 0.4, 0.06, 1.25, 0.95, 0.45, 0, "6a4a2c", "tree")                             # the bench at the stove
	var hw := _sub(b, -ix + 0.3, 0, iz - 0.3, -PI / 4.0)                                  # Herrgottswinkel
	_bx(hw, 0.04, 0.4, 0.04, 0, 2.2, 0, "4a3020", "tree")
	_bx(hw, 0.24, 0.04, 0.04, 0, 2.3, 0, "4a3020", "tree")
	_bx(hw, 0.4, 0.04, 0.25, 0, 1.92, 0.04, "6a4a2c", "tree")
	_bx(b, 3.0, 1.0, 0.6, -4.6, 0.5, -0.5 + it / 2.0 + 0.32, "5a3a22", "tree", "mid")             # the buffet
	_bx(b, 3.0, 0.9, 0.35, -4.6, 1.9, -0.5 + it / 2.0 + 0.2, "5a3a22", "tree", "mid")
	_book(b, -4.0, 1.0, -0.5 + it / 2.0 + 0.35, 0.0, "Gästebuch Hospiz Furgga",
			"14. Okt. 1961\nBei Schneetreiben über den Pass – warme Suppe, gutes Bett.",
			"18. Okt. 1961\nDie Wirtsleute haben uns bis zum Postauto begleitet.")
	var clk := _sub(b, -6.6, 2.2, -0.5 + it / 2.0 + 0.03, 0.0)                         # the clock on the wall - it stands still
	_pt(clk, Bib.C(0.22, 0.05, 0, 0, 0, "e8e2d0", 90, 0, 0, 0, "tree"))
	_pt(clk, Bib.TO(0.2, 0.24, 0, 0, 0, "4a3020", 90, 0, 0, "tree"))
	_bx(clk, 0.015, 0.15, 0.01, 0.04, 0.05, 0.03, "1a1a1a", "metal", "small", 0, 0, -38.0)
	_bx(clk, 0.015, 0.1, 0.01, -0.03, -0.02, 0.03, "1a1a1a", "metal", "small", 0, 0, 112.0)
	if full:
		for k in range(3):                                                               # old photos (dark frames)
			_bx(b, 0.4, 0.3, 0.03, -8.0 + k * 1.1, 1.9, iz - 0.02, "3a3028", "tree")
			_bx(b, 0.32, 0.22, 0.03, -8.0 + k * 1.1, 1.9, iz - 0.04, "8a8070", "tree")
		_bx(b, 0.04, 1.2, 1.6, -ix + 0.02, 1.5, 2.6, "b8b0a0", "stone")                    # a patch of peeling paint
	# kitchen: wood range along the back wall, pots, the stone sink, a table, shelves, the trap door to the cellar
	_woodstove(b, -6.0, -iz + 0.45, 0.0, 2.9)
	_bx(b, 1.6, 0.85, 0.6, -4.4, 0.42, -iz + 0.32, "6a6458", "stone", "mid")
	_bx(b, 1.0, 0.1, 0.5, -8.4, 0.9, -iz + 0.3, "8a8a86", "stone")
	_table(b, -5.4, -2.6, 0.0, 1.8, 0.9, "7a5a3a")
	_shelf(b, -ix + 0.2, -2.6, PI / 2.0, 1.8, 1.9, 5)
	_bx(b, 1.0, 0.04, 0.8, -3.0, 0.07, -3.3, "5a4030", "tree")                              # Falltür (cellar)
	_pt(b, Bib.TO(0.03, 0.05, -2.7, 0.1, -3.3, "3a3a3a", 0, 0, 0, "metal"))
	hospiz["rooms"]["falltuer"] = _V(b, -3.0, 0.1, -3.3)
	if full:
		for k in range(4):
			_pt(b, Bib.C(0.12 - 0.015 * k, 0.12, -8.8 + k * 0.32, 2.0, -iz + 0.1, "5a5a5e", 0, 0, 0, 0, "metal"))   # pots on hooks
	# dormitory: iron beds with dust sheets, washstand
	for k in range(4 if full else 2):
		for row in [0, 1]:
			var bx := 2.8 + k * 1.6
			var bz := 4.3 if row == 0 else 0.4
			var bed := _sub(b, bx, 0, bz, 0.0)
			_bx(bed, 0.9, 0.04, 1.9, 0, 0.45, 0, "3a3a3a", "metal")
			_bx(bed, 0.04, 1.0, 0.04, -0.43, 0.5, -0.93, "3a3a3a", "metal")
			_bx(bed, 0.04, 1.0, 0.04, 0.43, 0.5, -0.93, "3a3a3a", "metal")
			_bx(bed, 0.9, 0.04, 0.04, 0, 0.98, -0.93, "3a3a3a", "metal")
			_bx(bed, 0.98, 0.3, 2.0, 0, 0.6, 0.0, "d8d4c8", "tent")                                       # the dust sheet
	_bx(b, 0.8, 0.85, 0.45, ix - 0.3, 0.42, -0.2, "6a4a2c", "tree")
	_pt(b, Bib.C(0.2, 0.08, ix - 0.3, 0.9, -0.2, "e8e8e0", 0, 0, 0, 0, "stone"))
	# house chapel: small altar, a kneeler, two pews, candle stubs (not lit), a statue
	var ka := _sub(b, 5.6, 0, -iz + 0.4, 0.0)
	_bx(ka, 1.2, 0.9, 0.5, 0, 0.45, 0, "d8d0c0", "stone", "mid")
	_bx(ka, 1.26, 0.03, 0.56, 0, 0.91, 0, "e8e2d4", "tent")
	_pt(ka, Bib.C(0.1, 0.5, 0, 1.17, 0, "7a8aa8", 0, 0, 0, 0, "stone"))
	_pt(ka, Bib.S(0.08, 0.16, 0, 1.5, 0, "d8c8b0", "stone"))
	_candles(b, 5.2, 0.92, -iz + 0.4, 2, false, 0.05)
	_candles(b, 6.0, 0.92, -iz + 0.4, 2, false, 0.05)
	for row in range(2):
		var pw := _sub(b, 5.6, 0, -2.6 + row * 0.9, 0.0)
		_bx(pw, 2.0, 0.05, 0.35, 0, 0.45, 0, "5a3a22", "tree", "mid")
		_bx(pw, 2.0, 0.4, 0.04, 0, 0.78, 0.18, "5a3a22", "tree")
		_bx(pw, 0.05, 0.85, 0.38, -0.95, 0.42, 0, "4a3020", "tree")
		_bx(pw, 0.05, 0.85, 0.38, 0.95, 0.42, 0, "4a3020", "tree")
	_flush(b)
	_deck(b, Vector2.ZERO, Vector2(ix, iz), 0.06)
	ent_pos["berg.ort.hospiz"] = _V(b, -5.0, 1.3, 2.0)


func _door_node(b: Dictionary, hinge: Vector2, w: float, h: float, wall_rot: float, open_deg: float, col: String) -> Node3D:
	"""a door that can move (HOOK for the horror story: «Türen gehen von selbst auf») - hinge at «hinge» (local), the closed door
	lies along local +x turned by wall_rot; open_deg turns it"""
	var n := Node3D.new()
	n.name = "hospiz_tuer"
	n.transform = (b["xf"] as Transform3D) * Transform3D(Basis(Vector3.UP, wall_rot), Vector3(hinge.x, 0.0, hinge.y))
	var piv := Node3D.new()
	piv.rotation.y = deg_to_rad(open_deg)
	n.add_child(piv)
	bt.tal.add_child(n)
	var mt := StandardMaterial3D.new()
	mt.albedo_color = Bib.cc(col)
	mt.roughness = 0.85
	var mi: MeshInstance3D = m.add_mesh(piv, m.box(w, h, 0.05), Vector3(w / 2.0, h / 2.0, 0), mt, "tree")
	mi.visibility_range_end = 90.0
	(piv.get_child(piv.get_child_count() - 1) as MeshInstance3D).visibility_range_end = 90.0
	var km: MeshInstance3D = m.add_mesh(piv, m.box(0.12, 0.04, 0.1), Vector3(w - 0.12, 1.0, 0), mt, "metal")
	km.visibility_range_end = 30.0
	piv.set_meta("closed", 0.0)
	piv.set_meta("open", open_deg)
	return piv


func hospiz_door(nm: String, deg: float, secs := 2.5) -> Dictionary:
	"""HOOK (Horror): turn a door of the hospice (0 = closed) slowly, e.g. it opens by itself"""
	var piv = hospiz["doors"].get(nm, null)
	if piv == null or not is_instance_valid(piv):
		return {"ok": false, "doors": hospiz["doors"].keys()}
	var tw: Tween = m.create_tween()
	tw.tween_property(piv, "rotation:y", deg_to_rad(deg), maxf(0.05, secs)).set_trans(Tween.TRANS_SINE)
	return {"ok": true, "door": nm, "deg": deg}


func hospiz_light(nm: String, on: bool, energy := 0.8) -> Dictionary:
	"""HOOK (Horror): a warm light in a room of the hospice (seen through the windows at night: «Licht im Fenster»)"""
	var ol = hospiz["lights"].get(nm, null)
	if ol == null:
		return {"ok": false, "rooms": hospiz["lights"].keys()}
	(ol as OmniLight3D).visible = on
	(ol as OmniLight3D).light_energy = energy if on else 0.0
	return {"ok": true, "room": nm, "on": on}


# ---- verlassene Sennerei Chäsgaden ----------------------------------------------------------------------------------------------------
func _dairy() -> void:
	var w := 7.0
	var d := 5.0
	var b := _bk("sennerei", Vector2(w, d))
	_plinth(b, w, d)
	var c1 := "8e887c"
	var t := 0.5
	var fz := d / 2.0 - t / 2.0
	var sx := w / 2.0 - t / 2.0
	_wall(b, Vector2(-w / 2.0, fz), Vector2(w / 2.0, fz), 0, 2.4, t, c1, "stone", [[w / 2.0 - 1.2, 1.0, 0.0, 1.85], [w / 2.0 + 1.6, 0.5, 1.1, 1.5]])
	_wall(b, Vector2(-w / 2.0, -fz), Vector2(w / 2.0 - 2.2, -fz), 0, 2.4, t, c1)
	_wall(b, Vector2(w / 2.0 - 2.2, -fz), Vector2(w / 2.0, -fz), 0, 1.3, t, c1)                    # the collapsed corner
	_wall(b, Vector2(-sx, -fz + t / 2.0), Vector2(-sx, fz - t / 2.0), 0, 2.4, t, c1, "stone", [[1.2, 0.4, 1.2, 1.5]])
	_wall(b, Vector2(sx, -fz + t / 2.0), Vector2(sx, 0.4), 0, 1.6, t, c1)
	_wall(b, Vector2(sx, 0.4), Vector2(sx, fz - t / 2.0), 0, 2.4, t, c1)
	_pt(b, Bib.P(d, 1.2, t, -sx, 3.0, 0, c1, 0, 90, 0), "far")                                     # the west gable (the east one fell)
	_pt(b, Bib.ROD(Vector3(-w / 2.0, 3.55, 0), Vector3(w / 2.0 - 1.0, 3.5, 0), 0.12, "3a2a1a", "tree"), "far")    # ridge beam
	for k in range(6):                                                                             # rafters; on the east half some broken
		var x := -w / 2.0 + 0.4 + k * (w - 0.8) / 5.0
		for sd in [-1.0, 1.0]:
			if x > 1.0 and sd > 0 and k % 2 == 1:
				_pt(b, Bib.ROD(Vector3(x, 3.5, 0), Vector3(x + 0.1, 3.0, sd * 1.1), 0.07, "3a2a1a", "tree"), "mid")
				continue
			_pt(b, Bib.ROD(Vector3(x, 3.5, 0), Vector3(x, 2.4, sd * (fz + 0.2)), 0.07, "3a2a1a", "tree"), "mid")
	for sd in [-1.0, 1.0]:                                                                         # stone slabs: the west part still there
		var ang = rad_to_deg(atan2(1.1, d / 2.0)) * sd
		_pt(b, Bib.B(w * 0.55, 0.1, d / 2.0 + 0.4, -w * 0.22, 2.98, sd * (d / 4.0 + 0.1), "6e6a64", ang, 0, 0, "stone"), "far")
	_pt(b, Bib.B(w * 0.2, 0.1, d / 2.0 + 0.4, w * 0.4, 2.98, -(d / 4.0 + 0.1), "6e6a64", -rad_to_deg(atan2(1.1, d / 2.0)), 0, 0, "stone"), "far")
	_bx(b, 1.3, 0.12, 0.9, 1.6, 0.2, 0.6, "6e6a64", "stone", "mid", 20.0, 8.0, 14.0)             # fallen slabs on the floor
	_bx(b, 1.0, 0.1, 0.8, 2.3, 0.12, -0.4, "6e6a64", "stone", "mid", -40.0, -5.0, 3.0)
	_bx(b, 0.95, 1.8, 0.06, w / 2.0 - 1.4, 0.06, fz + 0.6, "4a3220", "tree", "mid", 10.0, 90.0, 0.0)   # the door, fallen out
	_bx(b, w - 0.9, 0.05, d - 0.9, 0, 0.03, 0, "6a6458", "stone", "mid")
	# inside: fire place with the swing crane and the copper kettle (Kessi), cheese press, shelves with a very old cheese
	var fp := Vector3(-1.9, 0, -0.6)
	for k in range(8):
		var a := TAU * k / 8.0
		_pt(b, Bib.S(0.18, 0.2, fp.x + cos(a) * 0.65, 0.08, fp.z + sin(a) * 0.65, "4a4844", "stone"))
	_bx(b, 1.0, 0.03, 1.0, fp.x, 0.05, fp.z, "1a1816", "stone")                                     # soot and ash
	_bx(b, 1.4, 1.6, 0.04, fp.x, 1.6, -d / 2.0 + t + 0.02, "2a2622", "stone")                      # black soot on the wall
	_bx(b, 0.14, 2.3, 0.14, fp.x - 0.9, 1.15, fp.z - 0.6, "4a3424", "tree", "mid")                  # the Turner (swing crane)
	_bx(b, 1.15, 0.12, 0.12, fp.x - 0.35, 2.1, fp.z - 0.6, "4a3424", "tree", "mid", 30.0)
	_pt(b, Bib.ROD(Vector3(fp.x - 0.9, 1.4, fp.z - 0.6), Vector3(fp.x - 0.1, 2.08, fp.z - 0.25), 0.05, "4a3424", "tree"))
	_pt(b, Bib.C(0.55, 0.6, fp.x, 0.95, fp.z, "a8643a", 0.45, 0, 0, 0, "metal"), "mid")               # the copper Kessi
	_pt(b, Bib.TO(0.52, 0.58, fp.x, 1.25, fp.z, "8a4a2a", 0, 0, 0, "metal"))
	_pt(b, Bib.ROD(Vector3(fp.x - 0.5, 1.28, fp.z), Vector3(fp.x - 0.1, 2.05, fp.z - 0.25), 0.012, "3a3a3a", "metal"))
	_pt(b, Bib.ROD(Vector3(fp.x + 0.5, 1.28, fp.z), Vector3(fp.x - 0.1, 2.05, fp.z - 0.25), 0.012, "3a3a3a", "metal"))
	var pr := _sub(b, 1.4, 0, -1.4, 0.0)                                                            # the cheese press
	_bx(pr, 1.4, 0.08, 0.7, 0, 0.75, 0, "6a4a2c", "tree", "mid")
	for sxx in [-0.6, 0.6]:
		_bx(pr, 0.08, 0.75, 0.6, sxx, 0.37, 0, "5a3a22", "tree")
	_pt(pr, Bib.C(0.3, 0.12, -0.2, 0.86, 0, "b8a878", 0, 0, 0, 0, "tree"))                          # the form (Järb)
	_bx(pr, 0.12, 1.5, 0.12, 0.45, 1.5, 0, "5a3a22", "tree")
	_bx(pr, 1.3, 0.1, 0.12, -0.1, 1.2, 0, "5a3a22", "tree", "small", 0, 0, -8.0)                     # the lever
	_pt(pr, Bib.S(0.24, 0.32, -0.7, 1.32, 0, "8a8478", "stone"))                                     # the stone weight
	_shelf(b, -w / 2.0 + t + 0.2, 1.2, PI / 2.0, 1.6, 1.6, 4, "4a3424", false)
	var sh := _sub(b, -w / 2.0 + t + 0.2, 0, 1.2, PI / 2.0)
	_pt(sh, Bib.C(0.21, 0.1, -0.4, 0.66, 0, "b8a050", 0, 0, 0, 0, "tree"))                            # a very old cheese
	if full:
		_pt(sh, Bib.C(0.2, 0.09, 0.3, 1.13, 0, "8a7a40", 0, 0, 0, 0, "tree"))
		_pt(b, Bib.C(0.16, 0.3, 0.2, 0.15, 1.6, "6a5032", 0.13, 0, 0, 0, "tree"))                       # milk bucket
		_pt(b, Bib.C(0.15, 0.95, -0.6, 0.48, 1.7, "6a5032", 0.18, 0, 0, 0, "tree"))                     # butter churn
		_pt(b, Bib.C(0.02, 0.4, -0.6, 1.1, 1.7, "6a5032", 0, 0, 0, 0, "tree"))
		_bx(b, 1.6, 0.35, 0.5, 2.3, 0.18, 1.6, "5a4030", "tree")                                         # wooden trough
	_flush(b)
	_deck(b, Vector2.ZERO, Vector2(w / 2.0 - t, d / 2.0 - t), 0.05)
	ent_pos["berg.ort.sennerei"] = _V(b, -0.6, 1.2, -0.2)


# ---- Infanteriewerk Gufer (Bunker im Hang) --------------------------------------------------------------------------------------------
func _bunker() -> void:
	var b := _bk("bunker", Vector2(2, 1))
	var con := "8a8a82"
	var dk := "5e5e58"
	var t := 0.35
	var hh := 2.4
	# the front: concrete with camouflage paint, steel door open, the embrasure (Scharte) of the firing position
	_wall(b, Vector2(-3.2, 0.0), Vector2(3.2, 0.0), -0.3, 3.4, 0.7, "7a7a6a", "stone", [[2.0, 1.0, 0.0, 2.0], [4.8, 0.55, 1.1, 1.38]], true, "far")
	for k in range(5):
		_bx(b, 0.9 + 0.3 * (k % 2), 0.7, 0.04, -2.6 + k * 1.25, 0.6 + 0.6 * ((k * 3) % 4), 0.36, ["5a6a4a", "6e6a52", "4e5a40"][k % 3], "stone", "far")
	_frame(b, Vector2(-3.2, 0.0), Vector2(3.2, 0.0), 2.0, 1.0, 0.0, 2.0, 0.7, "4a4a3a", false)
	_leaf(b, Vector2(-3.2, 0.36), Vector2(3.2, 0.36), 2.0, 0.98, 1.98, -95.0, "4a4a3a", 1.0)
	_bx(b, 0.75, 0.08, 0.6, 1.6, 1.08, 0.1, "4a4a44", "stone")                           # the embrasure sill
	_sign(b, "Infanteriewerk Gufer\nZutritt auf eigene Gefahr", Vector3(-0.2, 2.5, 0.37), 0.0, 1.1, "d8d0b0", Color(0.2, 0.15, 0.05), 20)
	# corridor (x -1.8 … -0.6), Kampfstand (right, behind the embrasure), filter room (left), crew room (at the end)
	var rooms := [[-1.2, -4.15, 1.2, 8.3], [1.1, -1.75, 3.4, 3.0], [-3.0, -5.75, 2.4, 2.5], [-1.5, -10.0, 5.0, 4.0]]
	for r in rooms:
		_bx(b, float(r[2]) + 0.2, 0.06, float(r[3]) + 0.2, float(r[0]), 0.03, float(r[1]), "6a6a64", "stone", "mid")
		_bx(b, float(r[2]) + 0.7, 0.35, float(r[3]) + 0.7, float(r[0]), hh + 0.17, float(r[1]), dk, "stone", "mid")
		_deck(b, Vector2(float(r[0]), float(r[1])), Vector2(float(r[2]) / 2.0, float(r[3]) / 2.0), 0.06)
	# walls (x0, z0, x1, z1, holes)
	var ws := [[-1.8, -0.35, -1.8, -4.5, []], [-1.8, -7.0, -1.8, -8.0, []], [-0.6, -0.35, -0.6, -8.0, [[1.25, 0.9, 0.0, 2.0]]],
			[-0.6, -3.25, 2.8, -3.25, []], [2.8, -0.35, 2.8, -3.25, []],
			[-4.2, -4.5, -1.8, -4.5, []], [-4.2, -7.0, -1.8, -7.0, []], [-4.2, -4.5, -4.2, -7.0, []], [-1.8, -4.5, -1.8, -7.0, [[1.25, 0.9, 0.0, 2.0]]],
			[-4.0, -8.0, 1.0, -8.0, [[2.8, 1.0, 0.0, 2.1]]], [-4.0, -12.0, 1.0, -12.0, []], [-4.0, -8.0, -4.0, -12.0, []], [1.0, -8.0, 1.0, -12.0, []]]
	for wl in ws:
		_wall(b, Vector2(float(wl[0]), float(wl[1])), Vector2(float(wl[2]), float(wl[3])), 0, hh, t, con, "stone", wl[4], true, "mid")
	# the gas-tight door in the corridor (open) and its frame
	_bx(b, 1.2, 0.2, 0.25, -1.2, 2.1, -4.0, "4a4a44", "metal", "mid")
	_bx(b, 0.12, 2.0, 0.85, -1.73, 1.0, -3.55, "4a4a3e", "metal", "mid")
	for k in range(3):
		_bx(b, 0.14, 0.1, 0.1, -1.66, 0.5 + k * 0.6, -3.3, "6a6a5a", "metal")
	# Kampfstand: the pivot of the old gun, ammunition boxes, periscope
	_pt(b, Bib.C(0.2, 0.9, 1.6, 0.45, -0.9, "4a4a3e", 0.28, 0, 0, 0, "metal"), "mid")
	_bx(b, 0.5, 0.1, 0.2, 1.6, 0.98, -0.75, "3a3a32", "metal")
	_bx(b, 0.6, 0.3, 0.3, 2.3, 0.15, -2.6, "4a5a3a", "metal")
	_bx(b, 0.6, 0.3, 0.3, 2.3, 0.45, -2.6, "4a5a3a", "metal")
	_pt(b, Bib.C(0.06, 1.4, 0.2, 1.7, -0.6, "3a3a32", 0, 0, 0, 0, "metal"))
	_sign(b, "Kampfstand", Vector3(1.1, 2.0, -3.25 + t / 2.0 + 0.02), 0.0, 0.7, "c8c0a0", Color(0.1, 0.1, 0.1), 22)
	# filter room: the ventilation unit with the hand crank, pipes
	_bx(b, 1.0, 1.3, 0.8, -3.4, 0.65, -5.7, "5a6a5a", "metal", "mid")
	_pt(b, Bib.TO(0.18, 0.22, -2.85, 0.9, -5.7, "3a3a3a", 0, 0, 90, "metal"))
	_pt(b, Bib.C(0.12, 1.1, -3.4, 1.85, -5.7, "6a6a62", 0, 0, 0, 0, "metal"))
	_pt(b, Bib.C(0.1, 2.2, -2.9, 2.15, -5.1, "6a6a62", 0, 90, 0, 0, "metal"))
	# crew room: steel bunks (three high), table with stools, lockers, the old telephone, a cage lamp
	_bunk(b, -3.2, -10.6, PI / 2.0, 3, 1.9, 0.7, "4a5040", true, true)
	_bunk(b, -2.2, -10.6, PI / 2.0, 3, 1.9, 0.7, "4a5040", full, true)
	_table(b, -0.2, -9.6, 0.0, 1.4, 0.7, "6a6a5a")
	for k in range(3 if full else 1):
		_pt(b, Bib.C(0.17, 0.45, -0.6 + k * 0.45, 0.22, -9.0, "5a5a52", 0, 0, 0, 0, "metal"))
	for k in range(3):
		_bx(b, 0.5, 1.8, 0.45, -1.0 + k * 0.52, 0.9, -11.7, "4e5a4a", "metal", "mid")
	_bx(b, 0.18, 0.25, 0.1, 0.9 - t / 2.0 - 0.05, 1.4, -9.0, "2a2a2a", "metal", "small", PI / 2.0)
	_pt(b, Bib.C(0.1, 0.18, -1.5, hh - 0.12, -10.0, "%c8c0a0", 0, 0, 0, 0, "metal"))
	_sign(b, "Mannschaftsraum · Ruhe", Vector3(-1.2, 2.0, -8.0 - t / 2.0 - 0.02), PI, 1.1, "c8c0a0", Color(0.1, 0.1, 0.1), 22)
	# rock over the parts that are not deep enough in the hill
	for p in [Vector2(0, -1.5), Vector2(2.0, -1.5), Vector2(-1.2, -4.0), Vector2(-3.0, -5.8), Vector2(-1.5, -10.0), Vector2(-3.5, -10), Vector2(0.5, -10)]:
		var q := _lx(b, p.x, p.y)
		var top := float(b["y"]) + hh + 0.6
		if bt.H(q.x, q.y) < top + 0.4:
			_pt(b, Bib.S(2.6, 2.4, p.x, hh + 0.6, p.y, Bib.ROCK_COLS["serpentin"][k_rock(p)], "stone"), "far")
	_flush(b)
	_deck(b, Vector2(-1.2, 0.7), Vector2(0.7, 0.5), 0.0)
	ent_pos["berg.ort.bunker"] = _V(b, -1.5, 1.2, -10.0)


func k_rock(p: Vector2) -> int:
	return int(absf(p.x * 3.0 + p.y * 7.0)) % 3


# ---- Militärbaracke Gufer mit Stacheldraht-Resten -------------------------------------------------------------------------------------
func _barrack() -> void:
	var w := 12.0
	var d := 6.0
	var b := _bk("baracke", Vector2(w, d))
	var y0 := 0.35
	for xx in [-5.5, -2.0, 2.0, 5.5]:
		for zz in [-2.6, 2.6]:
			_bx(b, 0.4, 0.4 + float(b["drop"]), 0.4, xx, y0 / 2.0 - float(b["drop"]) / 2.0, zz, "8a8a82", "stone", "far")   # concrete blocks
	var wood := "7a7468"
	var t := 0.12
	var fz := d / 2.0 - t / 2.0
	var holes := [[w / 2.0 - 3.0, 1.0, y0, y0 + 2.0]]
	for xx in [-5.0, -1.2, 1.5, 4.5]:
		holes.append([xx + w / 2.0, 0.8, y0 + 1.0, y0 + 1.8])
	_wall(b, Vector2(-w / 2.0, fz), Vector2(w / 2.0, fz), y0, y0 + 2.5, t, wood, "tree", holes)
	_wall(b, Vector2(-w / 2.0, -fz), Vector2(w / 2.0, -fz), y0, y0 + 2.5, t, wood, "tree", [[3.0, 0.8, y0 + 1.0, y0 + 1.8], [9.0, 0.8, y0 + 1.0, y0 + 1.8]])
	for sd in [-1.0, 1.0]:
		_wall(b, Vector2(sd * (w / 2.0 - t / 2.0), -fz), Vector2(sd * (w / 2.0 - t / 2.0), fz), y0, y0 + 2.5, t, wood, "tree", [[d / 2.0, 0.7, y0 + 1.0, y0 + 1.7]])
	for sd in [-1.0, 1.0]:                                                      # gable ends (prism along x, so turned)
		_pt(b, Bib.P(d, 1.3, t, sd * (w / 2.0 - t / 2.0), y0 + 3.15, 0, wood, 0, 90, 0, "tree"), "far")
	_pt(b, Bib.P(d + 0.8, 1.35, w + 0.6, 0, y0 + 3.17, 0, "3a3a38", 0, 90, 0, "stone"), "far")                     # tar paper roof
	for hh in holes:
		if float(hh[2]) > y0 + 0.5:
			_frame(b, Vector2(-w / 2.0, fz), Vector2(w / 2.0, fz), float(hh[0]), 0.8, float(hh[2]), float(hh[3]), t, "5a564e")
	_leaf(b, Vector2(-w / 2.0, fz + 0.04), Vector2(w / 2.0, fz + 0.04), w / 2.0 - 3.0, 0.95, 1.95, -35.0, "6a6458", 1.0, y0)
	for k in range(3):                                                           # steps of old planks
		_bx(b, 1.2, 0.08, 0.3, -3.0, y0 - 0.12 - k * 0.12, d / 2.0 + 0.2 + k * 0.3, "6a5a48", "tree", "mid")
	_bx(b, w - 0.3, 0.06, d - 0.3, 0, y0 + 0.03, 0, "6a5e4e", "tree", "mid")
	_bx(b, w - 0.3, 0.05, d - 0.3, 0, y0 + 2.48, 0, "8a8070", "tree", "mid")
	# inside: bunk frames (no mattresses any more), the rusty stove, a long table with benches, lockers
	var inn := _sub(b, 0, y0, 0, 0.0)
	for k in range(4 if full else 2):
		_bunk(inn, -4.6 + k * 1.1, -1.8, PI / 2.0, 2, 1.9, 0.8, "6a5a48", false)
	_woodstove(inn, 1.0, -2.4, 0.0, 2.5)
	_table(inn, 3.2, 0.4, 0.0, 2.6, 0.8, "6a5a48")
	_bench(inn, 3.2, 1.1, 0.0, 2.4)
	_bench(inn, 3.2, -0.3, 0.0, 2.4)
	for k in range(3):
		_bx(inn, 0.5, 1.8, 0.45, 5.4, 0.9, -1.8 + k * 0.55, "5a6050", "metal", "mid")
	_sign(b, "Baracke 3", Vector3(-1.2, y0 + 2.0, fz + 0.07), 0.0, 0.7, "c8c4b4", Color(0.15, 0.15, 0.15), 24)
	_flush(b)
	_deck(b, Vector2.ZERO, Vector2(w / 2.0 - t, d / 2.0 - t), y0 + 0.06)
	ent_pos["berg.ort.baracke"] = _V(b, 2.0, y0 + 1.2, 0.0)
	# barbed wire: old posts around and towards the bunker, rusty strands (some broken), coils in the grass
	var c := Vector2(float(B_BARRACK[0]), float(B_BARRACK[1]))
	var line := [c + Vector2(-12, -9), c + Vector2(12, -9), c + Vector2(13, 10), c + Vector2(-11, 11), c + Vector2(-12, -9), Vector2(-160, 808)]
	var posts := []
	var prev = null
	var k2 := 0
	for i in range(line.size() - 1):
		var a: Vector2 = line[i]
		var e: Vector2 = line[i + 1]
		var n := maxi(1, int(a.distance_to(e) / 3.0))
		for j in range(n):
			var q := a.lerp(e, float(j) / n)
			if bt._near_way(q.x, q.y, 2.0):
				prev = null
				continue
			k2 += 1
			var top = bt.P(q.x, q.y, 1.3)
			posts.append([bt.P(q.x, q.y), bt.rng.randf_range(-0.2, 0.2), 1.0])
			if prev != null and k2 % 5 != 0:
				for hgt in [0.35, 0.75, 1.15]:
					var pa: Vector3 = prev + Vector3(0, hgt - 1.3, 0)
					var pb = top + Vector3(0, hgt - 1.3, 0)
					var mid = (pa + pb) * 0.5 - Vector3(0, 0.12, 0)
					if (k2 + int(hgt * 10.0)) % 7 == 0:                 # a broken strand hangs down
						pb = pa.lerp(pb, 0.4) - Vector3(0, hgt * 0.8, 0)
						mid = (pa + pb) * 0.5
					bib._part(Bib.ROD(pa, mid, 0.008, "5a3420", "metal"), Transform3D.IDENTITY, "metal", "small", bib._cell_key(mid))
					bib._part(Bib.ROD(mid, pb, 0.008, "5a3420", "metal"), Transform3D.IDENTITY, "metal", "small", bib._cell_key(mid))
			prev = top
	bib.many("wire_post", posts, {})
	for q in [c + Vector2(-14, 2), c + Vector2(8, 13), c + Vector2(15, -4)]:
		bib.add("wire_coil", bt.P(q.x, q.y), bt.rng.randf() * TAU)
	info["wire_posts"] = posts.size()


# ---- die Stationen der Materialseilbahn (innen) ----------------------------------------------------------------------------------
func _lift_stations() -> void:
	var bot := Vector2(float(B_LIFT[0]), float(B_LIFT[1]))
	var top: Vector2 = bt.UPPER_HUT + Vector2(-8, -4)
	var ang := atan2(top.x - bot.x, top.y - bot.y)
	for up in [false, true]:
		var c: Vector2 = top if up else bot
		var b := _bld(c, ang if up else ang + PI, Vector2(3.0, 2.6), "seilbahn_oben" if up else "seilbahn")
		var wood := "6a4a2c"
		_plinth(b, 3.0, 2.6, "8a847a")
		# a wooden shed, open towards the cable (local -z): back wall with a door, side walls, roof
		_wall(b, Vector2(-1.5, 1.25), Vector2(1.5, 1.25), 0, 2.4, 0.1, wood, "tree", [[1.0, 0.85, 0.0, 1.95]])
		for sd in [-1.0, 1.0]:
			_wall(b, Vector2(sd * 1.45, -1.3), Vector2(sd * 1.45, 1.25), 0, 2.4, 0.1, wood, "tree", [[1.3, 0.5, 1.2, 1.6]])
		_bx(b, 3.0, 1.0, 0.1, 0, 1.9, -1.25, wood, "tree", "far")                               # above the opening
		_pt(b, Bib.P(3.4, 0.8, 3.0, 0, 2.8, 0, "5a5652"), "far")
		_bx(b, 2.9, 0.05, 2.5, 0, 0.03, 0, "5a4a38", "tree", "mid")
		_leaf(b, Vector2(-1.5, 1.3), Vector2(1.5, 1.3), 1.0, 0.82, 1.9, 70.0, "4a3220", -1.0)
		# the gantry with the cable wheel outside
		for sd in [-1.0, 1.0]:
			_bx(b, 0.2, 3.6, 0.2, sd * 1.2, 1.8, -1.6, "5a5a5e", "metal", "far")
		_bx(b, 2.8, 0.25, 0.25, 0, 3.5, -1.6, "5a5a5e", "metal", "far")
		_pt(b, Bib.C(0.6, 0.12, 0, 3.6, -1.6, "3a3a3e", 0, 90, 0, 0, "metal"), "far")
		if not up:
			# the winch: cable drum, electric motor with belt guard, the switch box with buttons and key
			_pt(b, Bib.C(0.45, 1.2, 0, 0.75, -0.2, "4a4a4e", 0, 0, 0, 90, "metal"), "mid")
			_pt(b, Bib.C(0.47, 0.05, -0.6, 0.75, -0.2, "8a2a1a", 0, 0, 0, 90, "metal"))
			_pt(b, Bib.C(0.47, 0.05, 0.6, 0.75, -0.2, "8a2a1a", 0, 0, 0, 90, "metal"))
			for k in range(6):
				_pt(b, Bib.TO(0.44, 0.47, -0.5 + k * 0.2, 0.75, -0.2, "2a2a2a", 0, 0, 90, "metal"))           # the cable on the drum
			_bx(b, 0.5, 0.4, 0.4, 0.95, 0.35, 0.5, "3a5a8a", 30.0, "mid")                                    # motor (a little warm)
			_bx(b, 0.12, 0.5, 0.75, 0.68, 0.55, 0.15, "c8a020", "metal")                                     # belt guard
			_bx(b, 1.6, 0.25, 0.9, 0, 0.12, -0.2, "5a5a5a", "metal")                                         # the base frame
			var sw := _sub(b, -1.38, 1.3, 0.5, PI / 2.0)
			_bx(sw, 0.45, 0.6, 0.18, 0, 0, 0, "8a8a8a", "metal")
			_pt(sw, Bib.C(0.035, 0.03, -0.1, 0.12, 0.1, "2aa040", 0, 90, 0, 0, "metal"))
			_pt(sw, Bib.C(0.035, 0.03, 0.1, 0.12, 0.1, "c82020", 0, 90, 0, 0, "metal"))
			_pt(sw, Bib.C(0.05, 0.03, 0.0, -0.12, 0.1, "c8c820", 0, 90, 0, 0, "metal"))                     # emergency stop
			_bx(sw, 0.04, 0.04, 0.05, 0.0, 0.0, 0.11, "c0c0c0", "metal")                                     # the key
			_sign(b, "Materialseilbahn Alp Tschuggen – Obri Stafel\nNutzlast 300 kg", Vector3(0.2, 1.75, 1.2), PI, 1.3, "e8e0cc", Color(0.1, 0.1, 0.1), 18)
			if full:
				_pt(b, Bib.C(0.08, 0.22, 1.1, 0.11, 0.9, "c82020", 0, 0, 0, 0, "metal"))                     # oil can
				_bx(b, 1.2, 0.7, 1.0, 0, 0.35, -2.8, "8a8a86", "metal", "mid")                               # the load box at the platform
			ent_pos["berg.ort.seilbahn"] = _V(b, 0.0, 1.0, 0.0)
		else:
			_pt(b, Bib.C(0.55, 0.15, 0, 0.9, -0.3, "4a4a4e", 0, 0, 0, 0, "metal"), "mid")                 # the return wheel
			_bx(b, 0.3, 0.8, 0.3, 0, 0.4, -0.3, "5a5a5e", "metal")
			_bx(b, 1.0, 0.04, 0.6, 0.8, 0.8, 0.8, "6a4a2c", "tree")
		_flush(b)
		_deck(b, Vector2.ZERO, Vector2(1.4, 1.2), 0.05)


# ---- Gumpifall mit Höhle dahinter -------------------------------------------------------------------------------------------------
func _cave() -> void:
	var b := _bk("hoehle", Vector2(1, 1))
	var cols: Array = ["4a4844", "3e3c38", "56534c"]
	var D := 10.0
	var winter := season == "winter"
	for k in range(5):
		var z0 := -k * 2.5 - 1.25
		var wl := 1.5 + 0.3 * sin(k * 1.7)
		var wr := 1.5 + 0.3 * cos(k * 2.3)
		var hc := 2.5 - 0.3 * k / 4.0 + 0.2 * sin(k * 2.9)
		_bx(b, wl + wr + 0.8, 0.4, 2.7, (wr - wl) / 2.0, -0.18, z0, cols[1], "stone", "mid")
		_bx(b, 0.9, hc + 0.6, 2.7, -wl - 0.4, hc / 2.0, z0, cols[k % 3], "stone", "far", 4.0 * sin(k * 3.1))
		_bx(b, 0.9, hc + 0.6, 2.7, wr + 0.4, hc / 2.0, z0, cols[(k + 1) % 3], "stone", "far", -4.0 * cos(k * 2.2))
		_bx(b, wl + wr + 1.6, 0.9, 2.7, (wr - wl) / 2.0, hc + 0.4, z0, cols[(k + 2) % 3], "stone", "far", 0.0, 3.0 * sin(k), 3.0 * cos(k))
		if full:
			_pt(b, Bib.S(0.5, 0.6, -wl + 0.1, hc - 0.2, z0 + 0.6, cols[0], "stone"))
			_pt(b, Bib.S(0.4, 0.5, wr - 0.1, 0.25, z0 - 0.5, cols[2], "stone"))
		_deck(b, Vector2((wr - wl) / 2.0, z0), Vector2(minf(wl, wr), 1.25), 0.02)
	_bx(b, 4.6, 3.4, 0.8, 0, 1.5, -D - 0.5, cols[0], "stone", "mid")                          # the back wall
	for p in [Vector3(-2.2, 2.9, 0.2), Vector3(2.0, 3.0, 0.0), Vector3(0.0, 3.4, 0.4), Vector3(-1.0, 3.6, -1.2)]:
		_pt(b, Bib.S(1.4, 1.5, p.x, p.y, p.z, cols[int(absf(p.x)) % 3], "stone"), "far")        # rock around the mouth
	_bx(b, 1.4, 0.03, 1.0, 0.4, 0.04, -6.5, "1a2a34", "pond", "mid")                           # a puddle
	if full:
		for i in range(5):
			_pt(b, Bib.S(0.25 + 0.05 * (i % 2), 0.3, -0.8 + i * 0.4, 0.1, -3.0 - i * 1.2, cols[i % 3], "stone"))
		_pt(b, Bib.C(0.015, 0.06, 0.6, 2.3, -4.0, "8ab0c0", 0, 0, 0, 0, "pond"))                   # a drop under the ceiling
	_flush(b)
	# the curtain of water in front of the mouth (winter: ice) and the pool (Gumpe) below
	var wm := StandardMaterial3D.new()
	wm.albedo_color = Color(0.88, 0.92, 0.96, 0.62) if not winter else Color(0.82, 0.9, 0.97, 1.0)
	wm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if not winter else BaseMaterial3D.TRANSPARENCY_DISABLED
	wm.cull_mode = BaseMaterial3D.CULL_DISABLED
	wm.roughness = 0.25
	var qm := QuadMesh.new()
	qm.size = Vector2(3.4 if season != "herbst" else 2.2, 6.0)
	var cp := _V(b, 0.0, 3.0, 0.9)
	var mi: MeshInstance3D = m.add_mesh(bt.tal, qm, cp, wm, "pond", Vector3(0, float(b["rot"]), 0))
	mi.visibility_range_end = 900.0
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var pq := _lx(b, 0.0, 3.2)
	_pool(pq, 2.3, minf(float(b["y"]) - 0.25, float(bt.H(pq.x, pq.y)) + 0.25), 0.0)
	if bt.W(cp).length() < 400.0 and not winter:
		m.add_sound(-9.0, bt.W(cp), 1.0e7)
	ent_pos["berg.ort.wasserfallhoehle"] = _V(b, 0.0, 1.2, -5.0)


func _pool(c: Vector2, r: float, y: float, rot: float, stretch := 1.0) -> void:
	"""a pool (Gumpe): deep green water, stones around"""
	var winter := season == "winter"
	var mt := StandardMaterial3D.new()
	mt.albedo_color = Color(0.12, 0.3, 0.3) if not winter else Color(0.8, 0.86, 0.9)
	mt.roughness = 0.08 if not winter else 0.5
	mt.metallic = 0.25
	var cm := CylinderMesh.new()
	cm.top_radius = r
	cm.bottom_radius = r * 0.8
	cm.height = 0.3
	cm.radial_segments = 14 if not lite else 8
	cm.rings = 1
	var mi: MeshInstance3D = m.add_mesh(bt.tal, cm, Vector3(c.x, y, c.y), mt, "pond" if not winter else "stone", Vector3(0, rot, 0), Vector3(1, 1, stretch))
	mi.visibility_range_end = 500.0
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var n := 7 if full else 4
	for k in range(n):
		var a := TAU * (k + 0.3) / n
		var q := c + Vector2(cos(a) * (r + 0.35), sin(a) * (r + 0.35) * stretch).rotated(-rot)
		bib.add("boulder", Vector3(q.x, maxf(y - 0.2, bt.H(q.x, q.y) - 0.3), q.y), a, {"r": 0.35 + 0.15 * (k % 3), "v": k % 3, "rock": "gneis", "noob": true, "snow": winter})


# ---- Gumpen im Tschuggenbach ---------------------------------------------------------------------------------------------------
func _pools() -> void:
	var a: Vector2 = Vector2(200, 220)
	var e: Vector2 = Vector2(330, 290)
	var d := (e - a).normalized()
	var rot := atan2(d.x, d.y)
	var prev := Vector3.ZERO
	var i := 0
	var order: Array = POOLS.duplicate()
	order.reverse()                                               # from the top (near the glacier) down
	for pl in order:
		var c: Vector2 = pl[0]
		var r := float(pl[1])
		var bed := INF
		for o in range(-5, 6):
			bed = minf(bed, bt.H(c.x - d.y * o, c.y + d.x * o))
		var y := bed + 0.22
		_pool(c, r, y, rot, 1.35)
		if i == order.size() - 1:
			var sq := c + Vector2(-d.y, d.x) * (r + 1.3)
			bib.add("boulder", Vector3(sq.x, bt.H(sq.x, sq.y) - 0.3, sq.y), rot, {"r": 0.9, "v": 1, "noob": true})   # a flat slab to sit
		if i > 0 and full and season != "winter":                  # the little fall from the pool above into this one
			var top := prev
			var bot := Vector3(c.x, y, c.y) + Vector3(d.x, 0, d.y) * r * 1.2
			var fall := top.y - bot.y
			var hd := Vector2(bot.x - top.x, bot.z - top.z)
			if fall > 0.6 and hd.length() > 0.1:
				var wm := StandardMaterial3D.new()
				wm.albedo_color = Color(0.92, 0.95, 0.97, 0.7)
				wm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
				wm.cull_mode = BaseMaterial3D.CULL_DISABLED
				var qm := QuadMesh.new()
				qm.size = Vector2(1.0, top.distance_to(bot))
				var dn := hd.normalized()
				var mi: MeshInstance3D = m.add_mesh(bt.tal, qm, (top + bot) * 0.5, wm, "pond", Vector3(-atan2(fall, hd.length()) + PI / 2.0, atan2(dn.x, dn.y), 0))
				mi.visibility_range_end = 300.0
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		prev = Vector3(c.x, y, c.y) - Vector3(d.x, 0, d.y) * r * 1.2       # the lower lip of this pool
		i += 1
	var mc: Vector2 = POOLS[1][0]
	if bt.WG(mc.x, mc.y).length() < 400.0 and season != "winter":
		m.add_sound(-14.0, bt.WG(mc.x, mc.y), 1.0e7)
	ent_pos["berg.ort.gumpen"] = bt.P(mc.x, mc.y, 0.8)


# ---- Gletschertor mit Schmelzbach -----------------------------------------------------------------------------------------------------
func _glacier_gate() -> void:
	var b := _bk("tor", Vector2(1, 1))
	var winter := season == "winter"
	var ice := ["a8d0e8", "c0e0f2", "8cbcd8"]
	var dark := "2a4a6a"
	# the arch: two pillars and a vault of ice blocks, ice above that goes into the glacier
	for sd in [-1.0, 1.0]:
		_bx(b, 1.4, 3.4, 2.4, sd * 2.6, 1.6, -0.2, ice[0], "stone", "far", 0.0, 0.0, sd * 4.0)
	for k in range(6):
		var a := PI * (k + 0.5) / 6.0
		_bx(b, 1.5, 0.9, 2.4, cos(a) * 2.5, 2.6 + sin(a) * 2.2, -0.2, ice[k % 3], "stone", "far", 0.0, 0.0, rad_to_deg(a) - 90.0)
	for p in [Vector3(-3.4, 4.4, -2.0), Vector3(3.2, 4.6, -1.6), Vector3(0.0, 5.6, -2.5), Vector3(-1.8, 5.2, -4.0), Vector3(2.0, 5.0, -4.5)]:
		_pt(b, Bib.S(2.6, 2.4, p.x, p.y, p.z, ice[int(absf(p.x)) % 3] if not winter else "eef2f6", "stone"), "far")
	# the tunnel: dark blue walls, the ceiling, the end
	for k in range(3):
		var z0 := -1.6 - k * 2.0
		for sd in [-1.0, 1.0]:
			_bx(b, 0.6, 3.6, 2.1, sd * 2.0, 1.6, z0, dark, "stone", "mid", sd * 6.0)
		_bx(b, 4.4, 0.6, 2.1, 0, 3.6 - k * 0.35, z0, "3a5a7a", "stone", "mid")
		_deck(b, Vector2(0, z0), Vector2(1.6, 1.0), 0.02)
	_bx(b, 4.0, 3.4, 0.6, 0, 1.6, -7.4, "1a3048", "stone", "mid")
	_bx(b, 3.6, 0.05, 6.0, 0, 0.03, -4.0, "6a6a66", "stone", "mid")                             # wet gravel
	if full:
		for i in range(6):
			_pt(b, Bib.S(0.3 + 0.08 * (i % 3), 0.35, -1.2 + (i % 3) * 1.1, 0.12, 1.5 + i * 0.9, "7c7a74", "stone"))
	_flush(b)
	# the meltwater stream (milky «Gletschermilch») from the gate into the Gletscherseeli
	var tarn: Vector2 = bt.TARN[0]
	var g0 := _lx(b, 0.3, 0.5)
	var pts := PackedVector2Array()
	var hs := PackedFloat32Array()
	var tgt: Vector2 = tarn + (g0 - tarn).normalized() * (float(bt.TARN[1]) - 3.0)
	var n := int(g0.distance_to(tgt) / 1.5)
	for k in range(n + 1):
		var q := g0.lerp(tgt, float(k) / n) + Vector2(0, 0.8 * sin(k * 0.9))
		pts.append(q)
		hs.append(maxf(bt.H(q.x, q.y), bt.level_of(bt.TARN) if k > n - 3 else -INF) + 0.08)
	hs[0] = float(b["y"]) + 0.08
	if not winter:
		bt._ribbon(pts, hs, 1.4 if season != "fruehling" else 2.0, Color(0.55, 0.64, 0.64), 0.0, 600.0, "pond")
		if bt.W(_V(b, 0, 0, 0)).length() < 400.0:
			m.add_sound(-10.0, bt.W(_V(b, 0, 0.5, 1.0)), 1.0e7)
	else:
		bt._ribbon(pts, hs, 0.6, Color(0.85, 0.9, 0.93), 0.0, 400.0, "stone")
	var sp := _lx(b, -4.0, 6.0)
	bib.add("info_board", bt.P(sp.x, sp.y), float(b["rot"]), {"text": "Gletschertor\nEishöhle nicht betreten – Einsturzgefahr!"})
	ent_pos["berg.ort.gletschertor"] = _V(b, 0.0, 1.8, 0.5)


# ---- Moorsee Schwarzseeli: Holzsteg und Wollgras ----------------------------------------------------------------------------------------
func _moor_lake() -> void:
	var lk: Array = bt.LAKE2
	var c: Vector2 = lk[0]
	var from := Vector2(-600, -255)                                       # on the Moorweg
	var dir := (from - c).normalized()
	var shore := c
	for k in range(200):                                                   # the shore in the direction of the path
		var q := c + dir * (k * 0.5)
		if bt._ell(q, lk) >= 1.0:
			shore = q
			break
	var end := shore - dir * 3.0                                           # 3 m over the water
	var L := from.distance_to(end)
	var d := (end - from) / L
	var rot := atan2(d.x, d.y)
	var wl: float = bt.level_of(lk)
	var planks := int(L / 0.3)
	for k in range(planks):
		var q := from + d * (k * 0.3 + 0.15)
		var y := maxf(bt.H(q.x, q.y), wl) + 0.32
		bib._part(Bib.B(1.1, 0.05, 0.26, 0, 0, 0, "7a5a3a" if k % 9 != 4 else "5a4a32", 0, 0, 0, "tree"), Transform3D(Basis(Vector3.UP, rot), Vector3(q.x, y, q.y)), "tree", "mid", bib._cell_key(Vector3(q.x, y, q.y)))
		if k % 6 == 0:
			for sd in [-0.5, 0.5]:
				var pq = q + Vector2(d.y, -d.x) * sd
				bib._part(Bib.C(0.05, 1.0, 0, 0, 0, "4a3a28", 0, 0, 0, 0, "tree"), Transform3D(Basis(), Vector3(pq.x, y - 0.5, pq.y)), "tree", "small", bib._cell_key(Vector3(pq.x, y, pq.y)))
	var pc := end
	bib._part(Bib.B(2.2, 0.06, 2.2, 0, 0, 0, "7a5a3a", 0, 0, 0, "tree"), Transform3D(Basis(Vector3.UP, rot), Vector3(pc.x, wl + 0.32, pc.y)), "tree", "mid", bib._cell_key(Vector3(pc.x, wl, pc.y)))
	bib.add("bench", Vector3(pc.x, wl + 0.35, pc.y) + Vector3(d.x, 0, d.y) * 0.6, rot + PI)
	var mid := (from + end) * 0.5
	bt.decks.append([mid, Vector2(0.55, L / 2.0), -rot, maxf(bt.H(mid.x, mid.y), wl) + 0.35])
	bt.decks.append([pc, Vector2(1.1, 1.1), -rot, wl + 0.35])
	bib.add("info_board", bt.P(from.x - d.y * 2.0, from.y + d.x * 2.0), rot + PI, {"text": "Hochmoor Schwarzseeli\nBitte auf dem Steg bleiben"})
	# cotton grass around the shore (white tufts in early summer, brown in autumn, gone under the snow)
	if season != "winter":
		var list := []
		var n := 260 if full else 80
		for k in range(n * 3):
			if list.size() >= n:
				break
			var a = bt.rng.randf() * TAU
			var e = bt.rng.randf_range(1.02, 1.3)
			var q := Vector2(cos(a) * float(lk[1]) * e, sin(a) * float(lk[2]) * e).rotated(float(lk[3])) + c
			if bt.zone(q.x, q.y) == "lake" or bt.slope_deg(q.x, q.y) > 14.0:
				continue
			list.append([bt.P(q.x, q.y), bt.rng.randf() * TAU, bt.rng.randf_range(0.8, 1.3)])
		bib.many("cottongrass", list, {"season": season})
		info["cottongrass"] = list.size()
	ent_pos["berg.ort.moorsee"] = Vector3(pc.x, wl + 1.0, pc.y)


# ---- Tschingelspitz: Gipfeltafel (Kreuz und Gipfelbuch stehen schon) -------------------------------------------------------------------
func _summit() -> void:
	var vp: Array = bt.VIEWPOINTS[0]
	var c: Vector2 = bt.vp_xz(vp)
	var yaw := deg_to_rad(float(vp[6]))
	var fwd := Vector2(sin(yaw), -cos(yaw))
	var side := Vector2(-fwd.y, fwd.x)
	var q := c - fwd * 1.0 - side * 1.6
	var b := _bld(q, PI - yaw, Vector2(0.5, 0.5))
	_bx(b, 0.5, 1.0, 0.4, 0, 0.5, 0, "7c7a74", "stone", "mid")
	_bx(b, 0.42, 0.3, 0.02, 0, 0.8, 0.21, "c8a43a", "metal", "mid")
	_label(b, T.t("Tschingelspitz\n%d m ü. M.") % int(bt.H(c.x, c.y) + bt.ALT0), Vector3(0, 0.8, 0.225), 0.0, false, 26, 0.004, Color(0.2, 0.12, 0.02), 20.0)
	_flush(b)
	ent_pos["berg.ort.gipfel"] = bt.P(c.x, c.y, 1.5)


# ---- Felsturm Gumpizahn mit Klettersteig ------------------------------------------------------------------------------------------------
func _tower() -> void:
	var c := TOWER
	var g := INF
	for o in [Vector2(-4, -4), Vector2(4, -4), Vector2(-4, 4), Vector2(4, 4), Vector2.ZERO]:
		g = minf(g, bt.H(c.x + o.x, c.y + o.y))
	var b := _bld(c, 0.35, Vector2(1, 1))
	b["xf"] = Transform3D((b["xf"] as Transform3D).basis, Vector3(c.x, g, c.y))
	b["y"] = g
	var cols: Array = Bib.ROCK_COLS["gneis"]
	var layers := 7
	var faces := []                                         # the west face x of each layer (for the via ferrata)
	for k in range(layers):
		var f := float(k) / (layers - 1)
		var sx := lerpf(9.0, 3.2, f) + 0.6 * sin(k * 2.1)
		var sz := lerpf(8.0, 3.0, f) + 0.5 * cos(k * 1.7)
		var hk := TOWER_H / layers
		var ox := 0.4 * sin(k * 1.3)
		var oz := 0.4 * cos(k * 2.7)
		_bx(b, sx, hk + 0.3, sz, ox, hk * (k + 0.5) - 0.2 * (1 if k == 0 else 0), oz, cols[k % 3], "stone", "far", 6.0 * sin(k * 2.0), 2.0 * sin(k * 3.3), 2.0 * cos(k * 2.6))
		if full or k % 2 == 0:
			_pt(b, Bib.B(sx * 0.6, hk * 0.8, sz * 0.5, ox + sx * 0.3, hk * (k + 0.45), oz - sz * 0.35, cols[(k + 1) % 3], 4, 20 + k * 9, -5, "stone"), "far")
			_pt(b, Bib.S(sx * 0.35, hk * 0.9, ox - sx * 0.25, hk * (k + 0.5), oz + sz * 0.42, cols[(k + 2) % 3], "stone"), "far")
		faces.append([ox - sx / 2.0, hk * k, hk * (k + 1)])
	var top_y := TOWER_H
	_bx(b, 2.6, 0.4, 2.4, 0.2, top_y, 0.0, cols[1], "stone", "far")
	bib._part(Bib.B(0.12, 1.8, 0.12, 0, 0.9, 0, "6a4a2e", 0, 0, 0, "tree"), (b["xf"] as Transform3D) * Transform3D(Basis(), Vector3(0.6, top_y + 0.2, 0.2)), "tree", "far", bib._cell_key(c3(c)))
	bib._part(Bib.B(0.9, 0.1, 0.12, 0, 1.35, 0, "6a4a2e", 0, 0, 0, "tree"), (b["xf"] as Transform3D) * Transform3D(Basis(), Vector3(0.6, top_y + 0.2, 0.2)), "tree", "far", bib._cell_key(c3(c)))
	# the via ferrata on the west face: steel cable in zigzag, iron rungs, a ladder at the overhang (layers 4–5)
	var prev := Vector3.ZERO
	var zz := -0.6
	for k in range(layers):
		var fx := float(faces[k][0]) - 0.25
		var y0 := float(faces[k][1])
		var y1 := float(faces[k][2])
		var pa := Vector3(fx, y0 + 0.9, zz)
		zz = -zz * 0.8 + 0.3 * sin(k)
		var pb := Vector3(fx, y1 + 0.9, zz)
		if k > 0:
			_pt(b, Bib.ROD(prev, pa, 0.015, "a0a0a0", "metal"), "mid")
		_pt(b, Bib.ROD(pa, pb, 0.015, "a0a0a0", "metal"), "mid")
		prev = pb
		if k == 4:
			for sd in [-0.25, 0.25]:
				_pt(b, Bib.ROD(Vector3(fx - 0.35, y0, zz + sd), Vector3(fx - 0.35, y1 + 0.3, zz + sd), 0.025, "8a8a8a", "metal"), "mid")
			for j in range(int((y1 - y0) / 0.3)):
				_bx(b, 0.05, 0.03, 0.5, fx - 0.35, y0 + 0.15 + j * 0.3, zz, "8a8a8a", "metal", "mid")
		else:
			for j in range(int((y1 - y0) / 0.45)):
				var t := float(j) / maxf(1.0, (y1 - y0) / 0.45)
				_bx(b, 0.25, 0.03, 0.32, fx + 0.05, y0 + 0.2 + j * 0.45, lerpf(pa.z, pb.z, t), "6a6a6a", "metal", "mid")
	_flush(b)
	m.add_obstacle(bt.WG(c.x, c.y), 4.6)
	m.set_obstacle_height(TOWER_H)
	bt.decks.append([c + Vector2(0.2, 0.0).rotated(-0.35), Vector2(1.2, 1.1), -0.35, g + top_y + 0.2])
	var wf := c + Vector2(-6.5, 0.0).rotated(-0.35)
	bib.add("info_board", bt.P(wf.x, wf.y), -PI / 2.0 + 0.35, {"text": "Klettersteig Gumpizahn (K4)\nNur mit Klettersteigset und Helm"})
	ent_pos["berg.ort.felsturm"] = Vector3(c.x, g + top_y + 1.0, c.y)


func c3(c: Vector2) -> Vector3:
	return Vector3(c.x, 0, c.y)


# ---- Schafgrat: der schmale Gratweg ---------------------------------------------------------------------------------------------
func _ridge() -> void:
	var pts := PackedVector2Array()
	var hs := PackedFloat32Array()
	var z := RIDGE_Z0 + 8.0
	while z <= RIDGE_Z1 - 8.0:
		pts.append(Vector2(RIDGE_X, z))
		hs.append(bt.H(RIDGE_X, z) + 0.03)
		z += 4.0
	bt._ribbon(pts, hs, 0.55, Color(0.52, 0.48, 0.42), 0.0, 600.0, "stone")
	var marks := []
	var chains_at := []
	var guards := 0
	for i in range(pts.size()):
		var p := pts[i]
		if i % 8 == 3:
			var sd := 0.55 if i % 16 == 3 else -0.55
			marks.append([bt.P(p.x + sd, p.y, -0.08), PI / 2.0 if sd < 0 else -PI / 2.0])
		var steep := absf(bt.H(p.x, p.y + 4.0) - bt.H(p.x, p.y - 4.0)) / 8.0
		if steep > 0.28:
			chains_at.append(p)
		if i % 1 == 0:                                       # the guard left and right (you do not fall: the rover stops)
			for sd2 in [-1.0, 1.0]:
				m.add_obstacle(bt.WG(p.x + sd2 * 2.3, p.y), 1.25)
				m.set_obstacle_height(1.2)
				guards += 1
	bib.many("trail_mark", marks, {"level": 2})
	# chains on posts where the path is steep (fixed rope like on real alpine trails)
	var prev = null
	for p in chains_at:
		var post = bt.P(p.x + 0.45, p.y, 0.0)
		bib._part(Bib.B(0.04, 0.9, 0.04, 0, 0.45, 0, "5a5a5e", 0, 0, 0, "metal"), Transform3D(Basis(), post), "metal", "small", bib._cell_key(post))
		var top = post + Vector3(0, 0.85, 0)
		if prev != null and (prev as Vector3).distance_to(top) < 6.0:
			var mid = ((prev as Vector3) + top) * 0.5 - Vector3(0, 0.15, 0)
			bib._part(Bib.ROD(prev, mid, 0.012, "7a7a7e", "metal"), Transform3D.IDENTITY, "metal", "small", bib._cell_key(mid))
			bib._part(Bib.ROD(mid, top, 0.012, "7a7a7e", "metal"), Transform3D.IDENTITY, "metal", "small", bib._cell_key(mid))
		prev = top
	for e in [[RIDGE_Z0 + 4.0, PI], [RIDGE_Z1 - 4.0, 0.0]]:
		bib.add("hiking_sign", bt.P(RIDGE_X + 1.4, float(e[0])), float(e[1]), {"here": T.t("Schafgrat %d m") % int(bt.H(RIDGE_X, float(e[0])) + bt.ALT0),
				"arms": [["Schafgrat (ausgesetzt)", "40 min", 2]]})
	var zm := -450.0
	ent_pos["berg.ort.grat"] = bt.P(RIDGE_X, zm, 1.2)
	info["ridge"] = {"path_pts": pts.size(), "chains": chains_at.size(), "guards": guards, "top_m": int(bt.H(RIDGE_X, zm) + bt.ALT0),
			"flank_drop_8m": snappedf(bt.H(RIDGE_X, zm) - bt.H(RIDGE_X - 8.0, zm), 0.1), "flank_drop_8m_east": snappedf(bt.H(RIDGE_X, zm) - bt.H(RIDGE_X + 8.0, zm), 0.1)}


# ---- alter Säumerweg -------------------------------------------------------------------------------------------------------------
func _saeumerweg() -> void:
	var pts: PackedVector2Array = bt.dense(SAUM, 0.55 if full else 1.1)
	var hs := PackedFloat32Array()
	for p in pts:
		hs.append(bt.H(p.x, p.y) + 0.02)
	bt._ribbon(pts, hs, 1.9, Color(0.42, 0.4, 0.36), 0.0, 400.0, "stone")
	var stones := []
	var border := []
	for i in range(pts.size()):
		var p := pts[i]
		var d := (pts[mini(i + 1, pts.size() - 1)] - pts[maxi(i - 1, 0)]).normalized()
		var n := Vector2(-d.y, d.x)
		var rot := atan2(d.x, d.y)
		for k in ([-0.55, 0.0, 0.55] if full else [-0.3, 0.3]):
			var q = p + n * (k + bt.rng.randf_range(-0.06, 0.06))
			stones.append([bt.P(q.x, q.y, -0.02), rot + bt.rng.randf_range(-0.2, 0.2), bt.rng.randf_range(0.9, 1.15)])
		if i % (4 if full else 2) == 0:
			for sd in [-1.0, 1.0]:
				var q2 = p + n * sd * 0.98
				border.append([bt.P(q2.x, q2.y, -0.02), rot + PI / 2.0, 1.35])
	bib.many("pave_stone", stones, {"v": 0})
	bib.many("pave_stone", border, {"v": 2})
	var s0: Vector2 = SAUM[0]
	bib.add("info_board", bt.P(s0.x + 3.0, s0.y + 2.0), PI * 0.9, {"text": "Alter Säumerweg\nHier trugen Maultiere Salz, Wein und Käse über den Pass."})
	var sm: Vector2 = SAUM[3]
	bib.add("summit_cross", bt.P(sm.x + 1.8, sm.y), PI / 2.0, {"h": 2.0})          # a wayside cross
	info["pave_stones"] = stones.size() + border.size()
	ent_pos["berg.ort.saeumerweg"] = bt.P(float(SAUM[2].x), float(SAUM[2].y), 0.6)


# ---- verlassene Alp Altstafel (zur Ruine dazu) ----------------------------------------------------------------------------------------
func _alp_ruins() -> void:
	var col := "8a8478"
	for r in ALP_RUINS:
		var b := _bld(Vector2(float(r[0]), float(r[1])), float(r[2]), Vector2(float(r[3]), float(r[4])))
		var w := float(r[3])
		var d := float(r[4])
		var hs := [1.4, 0.6, 1.0, 0.35]
		var corners := [Vector2(-w / 2.0, -d / 2.0), Vector2(w / 2.0, -d / 2.0), Vector2(w / 2.0, d / 2.0), Vector2(-w / 2.0, d / 2.0)]
		for k in range(4):
			var h := float(hs[(k + int(w)) % 4]) + 0.2 * sin(k * 3.0 + w)
			var holes := [[corners[k].distance_to(corners[(k + 1) % 4]) * 0.5, 1.0, 0.0, 2.0]] if k == 2 else []
			_wall(b, corners[k], corners[(k + 1) % 4], -0.2, h, 0.55, col, "stone", holes, true, "mid")
		for i in range(8 if full else 4):                                  # stones fallen out of the walls
			var a := i * 2.1 + w
			_pt(b, Bib.S(0.22 + 0.06 * (i % 3), 0.26, cos(a) * w * 0.45, 0.08, sin(a) * d * 0.45, "7c7a74", "stone"))
		_pt(b, Bib.ROD(Vector3(-w * 0.3, 0.1, 0.4), Vector3(w * 0.25, 0.5, -0.3), 0.08, "4a3a2a", "tree"))                   # a fallen beam
		_flush(b)
	# the old enclosure (Pferch) and the overgrown trough
	var rc: Vector2 = bt.RUIN
	bt._fence(rc + Vector2(-40, 18), rc + Vector2(10, 32), "dry_wall", 3.0, {"h": 0.6})
	bt._fence(rc + Vector2(10, 32), rc + Vector2(30, -10), "dry_wall", 3.0, {"h": 0.5})
	var tq := rc + Vector2(-14, -24)
	bib._part(Bib.B(2.2, 0.5, 0.7, 0, 0.2, 0, "7c7a74", 0, 0, 0, "stone"), Transform3D(Basis(Vector3.UP, 0.4), bt.P(tq.x, tq.y)), "stone", "mid", bib._cell_key(bt.P(tq.x, tq.y)))
	bib._part(Bib.B(1.9, 0.05, 0.45, 0, 0.38, 0, "3a4a30", 0, 0, 0, "pond"), Transform3D(Basis(Vector3.UP, 0.4), bt.P(tq.x, tq.y)), "pond", "mid", bib._cell_key(bt.P(tq.x, tq.y)))
	# Alpenampfer («Blacken») where the cattle used to lie: the sign of an old alp
	if season != "winter":
		var list := []
		for k in range(70 if full else 25):
			var a = bt.rng.randf() * TAU
			var q = rc + Vector2(-15, -5) + Vector2(cos(a), sin(a)) * bt.rng.randf_range(4.0, 34.0)
			if bt.slope_deg(q.x, q.y) < 25.0:
				list.append([bt.P(q.x, q.y), bt.rng.randf() * TAU, bt.rng.randf_range(0.7, 1.3)])
		bib.many("laeger_plant", list, {})
	ent_pos["berg.ort.alp_ruinen"] = bt.P(-830.0, -222.0, 1.0)


# =============================================================================================================================
# discovery book, places, map
# =============================================================================================================================
func _register() -> void:
	var ed = m.get("entdecken")
	var out := []
	for e in ENT:
		var id := str(e[0])
		if not ent_pos.has(id):
			continue
		var wp: Vector3 = bt.W(ent_pos[id])
		out.append({"id": id, "x": snappedf(wp.x, 0.1), "y": snappedf(wp.y, 0.1), "z": snappedf(wp.z, 0.1)})
		if ed == null or not ed.has_method("register"):
			continue
		ed.register(id, {"scene": "bergtal", "title": T.t(str(e[1])), "short_text": T.t(str(e[2])), "hint": T.t(str(e[3])), "icon": str(e[4]),
				"position": wp, "size": e[5], "radius": float(e[6]), "when": str(e[7]), "kind": "ort"})
	info["registered"] = ed != null and ed.has_method("register")
	s.data["bt_orte_disc"] = out


func publish() -> void:
	"""after bergtal._publish: the places on the map, the ridge and the mule track as lines, the list for MoveEye"""
	var marks: Array = s.data.get("map_marks", [])
	var orte: Array = s.data.get("orte", [])
	for pl in PLACES:
		var wp: Vector3 = bt.WG(float(pl[1]), float(pl[2]))
		marks.append([wp, str(pl[0]), Color(0.95, 0.95, 0.9), false])
		orte.append([str(pl[0]), snappedf(wp.x, 0.1), snappedf(wp.z, 0.1), snappedf(Vector2(wp.x, wp.z).length(), 0.1)])
	var lines: Array = s.data.get("map_lines", [])
	var rl := PackedVector2Array()
	for z in [RIDGE_Z0 + 8.0, RIDGE_Z1 - 8.0]:
		var wp: Vector3 = bt.WG(RIDGE_X, z)
		rl.append(Vector2(wp.x, wp.z))
	lines.append([rl, Color(0.3, 0.55, 1.0), 1.5])
	var sl := PackedVector2Array()
	for q in SAUM:
		var wp: Vector3 = bt.WG(q.x, q.y)
		sl.append(Vector2(wp.x, wp.z))
	lines.append([sl, Color(0.6, 0.45, 0.3), 2.0])
	var rooms := {}
	for k in hospiz["rooms"]:
		var wp: Vector3 = bt.W(hospiz["rooms"][k])
		rooms[k] = [snappedf(wp.x, 0.1), snappedf(wp.y, 0.1), snappedf(wp.z, 0.1)]
	s.data["bt_orte"] = {"places": PLACES.map(func(p): return p[0]), "inside": INSIDE.map(func(e): return e[0]), "discoveries": s.data.get("bt_orte_disc", []),
			"hospiz": {"rooms": rooms, "doors": hospiz["doors"].keys(), "lights": hospiz["lights"].keys()}}


func fly(nm: String) -> bool:
	"""quick travel into a room: the view flies through the door and looks into the room"""
	for e in INSIDE:
		if str(e[0]) != nm or not _xf.has(str(e[1])):
			continue
		var xf: Transform3D = _xf[str(e[1])]
		var p: Vector3 = bt.W(xf * Vector3(float(e[2]), float(e[3]), float(e[4])))
		var t: Vector3 = bt.W(xf * Vector3(float(e[5]), float(e[6]), float(e[7])))
		m._to_free_view()
		if m.fly_tw != null:
			m.fly_tw.kill()
		var start: Transform3D = m.view_cam.global_transform
		var end := Transform3D(Basis(), p).looking_at(t, Vector3.UP)
		var cam: Camera3D = m.view_cam
		m.fly_tw = m.create_tween()
		m.fly_tw.tween_method(func(f: float): cam.global_transform = start.interpolate_with(end, f), 0.0, 1.0, 1.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		return true
	return false


func _tick(dt: float, _t: float) -> bool:
	if bt.tal == null or not is_instance_valid(bt.tal):
		return true
	_clock += dt
	var cam: Vector3 = bt.V(m.view_cam.global_position)
	for f in _flames:                                                        # candles: on only near the view, they flicker
		var ol: OmniLight3D = f[0]
		if not is_instance_valid(ol):
			continue
		if ol.visible:
			ol.light_energy = float(f[1]) * (0.85 + 0.1 * sin(_clock * 13.0 + ol.position.x) + 0.06 * sin(_clock * 31.0))
	_slow -= dt
	if _slow > 0.0:
		return false
	_slow = 0.4
	for f in _flames:
		var ol: OmniLight3D = f[0]
		if is_instance_valid(ol):
			ol.visible = cam.distance_to(f[2]) < 45.0
	# the narrow ridge: a warning when you walk on it (view near the ground or the rover)
	var who: Vector3 = m.rig.global_position if m.mover_on or (m.explore != null and m.explore.on) else m.view_cam.global_position
	var q: Vector3 = bt.V(who)
	if absf(q.x - RIDGE_X) < 3.0 and q.z > RIDGE_Z0 and q.z < RIDGE_Z1 and q.y - bt.H(q.x, q.z) < 4.0 and m.now() - _warn_t > 9.0:
		_warn_t = m.now()
		m.start_info = T.t("Schmaler Grat: links und rechts geht es steil hinunter. Langsam gehen – bei Gewitter sofort weg vom Grat!")
	return false


func control(d: Dictionary) -> Dictionary:
	match str(d.get("what", "info")):
		"goto":
			var nm := str(d.get("place", d.get("value", "")))
			for pl in PLACES:
				if str(pl[0]) == nm:
					m.fly_to(bt.WG(float(pl[1]), float(pl[2])) + Vector3(0, 2, 0), 40.0)
					return {"ok": true, "place": nm}
			return {"ok": fly(nm), "place": nm}
		"door":
			return hospiz_door(str(d.get("name", "eingang")), float(d.get("deg", 0.0)), float(d.get("secs", 2.5)))
		"light":
			return hospiz_light(str(d.get("name", "gaststube")), bool(d.get("on", true)), float(d.get("energy", 0.8)))
		"where":
			var poses := {}
			for e in INSIDE:
				if _xf.has(str(e[1])):
					var p: Vector3 = bt.W((_xf[str(e[1])] as Transform3D) * Vector3(float(e[2]), float(e[3]), float(e[4])))
					poses[str(e[0])] = [snappedf(p.x, 0.1), snappedf(p.y, 0.1), snappedf(p.z, 0.1)]
			return {"ok": true, "inside": poses, "discoveries": s.data.get("bt_orte_disc", []), "hospiz": s.data.get("bt_orte", {}).get("hospiz", {})}
	return {"ok": true, "info": info, "places": PLACES.size(), "inside": INSIDE.size(), "ridge": info.get("ridge", {})}
