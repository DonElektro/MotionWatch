extends RefCounted
## «Bergtal wie auf den Fotos» (Daniel, 31.10.2026, Vorlage: Fotos vom Stockhorn-Gebiet, Hinter-/Oberstockensee, Grat mit
## Legföhren, Vierwaldstättersee von oben). Nur Aussehen und Verteilung der Landschaft - keine Wege, Orte oder Höhen neu.
##
## Was hier gebaut wird (NUR ausserhalb von Lite, bergtal.gd fragt bt.lite):
##   * Karstweide: viele helle, kantige Kalkblöcke (bib_berg.gd «karst»), halb eingesunken, in Gruppen und einzeln, mit
##     schmalen Trampelpfaden dazwischen (nur Aussehen, kein Wanderweg); Geröll auf den Schuttkegeln unter den Wänden
##   * Felszähne am Grat (bib_berg.gd «rock_tooth»)
##   * Wald: zusätzliche einzelne Fichten und kleine Gruppen am Waldrand und auf den Weiden, dürre Fichten an der
##     Waldgrenze, Legföhren und Zwergsträucher (Alpenrosen, Heidelbeeren) am Grat - in den Listen von bergtal._veg_rest
##     (gleiche MultiMeshes, keine zusätzlichen Zeichenaufrufe ausser den Zwergsträuchern)
##   * Bergsee: Shader bergsee.gdshader (türkis bis smaragdgrün, flaches Ufer hell mit sichtbarem Grund, tief dunkel,
##     Spiegelung von Wald und Fels aus einem Horizont-Profil, ohne zweite Kamera)
##   * Himmel: Quellwolken, Kondensstreifen, leichte Sonnenstrahlen, Abendverlauf Gelb → Blaugrau (sky.gdshader, Werte
##     «cumulus», «contrails», «rays», «dusk_band»; 0 = wie bisher) und Dunst im Gegenlicht (env.fog_sun_scatter)
## In Lite bleibt alles wie bisher (nur Farben: Boden, ferne Berge, Wasser, Fichten - die kosten nichts).
##
## Freihalten: Wanderwege und Strasse (bt._near_way: Blöcke 4,2 m, Bäume 5 m, Felszähne 7 m ab der Mitte - die Strasse ist
## 5,6 m breit), die besetzten Stellen des Tals (bt._busy_pts: Hütten, Orte,
## Vignetten, Aussichtspunkte, Schlafplätze), Bäche, die Wege des Abenteuers (bergtal_abenteuer_daten.gd CHAPTERS), die
## Fundstellen und Wege der Geschichten (STORY_PTS / STORY_LINES unten, aus den Skripten der Geschichten gezogen) und rund
## um den Standort von MoveEye (Blöcke 20 m, Bäume 35 m, Felszähne 50 m: die Sicht der Kameras bleibt frei).

const AD = preload("res://scripts/bergtal_abenteuer_daten.gd")

# Fundstellen, Rastplätze, Tore, Ziele der Geschichten (Grossvater / Abenteuer, Maggie, Geschichten, Horror, Erlebnisse,
# Orte): alle festen Tal-Koordinaten aus den Skripten (Stand 31.10.2026), je 10 m frei. Neue Geschichten-Orte hier ergänzen.
const STORY_PTS := [
		Vector2(-1000, -1000), Vector2(-940, 600), Vector2(-878, 428), Vector2(-870, -170), Vector2(-870, 450), Vector2(-860, -240), Vector2(-832, 512), Vector2(-830, -215),
		Vector2(-830, 380), Vector2(-827, 505), Vector2(-810, -230), Vector2(-800, -130), Vector2(-790, 462), Vector2(-790, 520), Vector2(-780, 0), Vector2(-770, 150),
		Vector2(-760, -180), Vector2(-740, -350), Vector2(-720, 300), Vector2(-720, 495), Vector2(-710, -320), Vector2(-705, 40), Vector2(-700, -250), Vector2(-700, -130),
		Vector2(-700, 450), Vector2(-700, 470), Vector2(-700, 520), Vector2(-688, -114), Vector2(-680, 240), Vector2(-660, 470), Vector2(-650, 430), Vector2(-645, -295),
		Vector2(-640, -330), Vector2(-640, -235), Vector2(-640, -200), Vector2(-640, -300), Vector2(-640, 0), Vector2(-640, 300), Vector2(-625, 125), Vector2(-620, 128),
		Vector2(-615, 125), Vector2(-612, -262), Vector2(-600, -255), Vector2(-598, 450), Vector2(-590, -240), Vector2(-588, 330), Vector2(-578, 330), Vector2(-570, 340),
		Vector2(-540, -200), Vector2(-530, 480), Vector2(-520, 548), Vector2(-520, 560), Vector2(-512, 548), Vector2(-480, 300), Vector2(-470, -265), Vector2(-470, 380),
		Vector2(-470, 560), Vector2(-450, 380), Vector2(-420, -230), Vector2(-420, -220), Vector2(-400, 400), Vector2(-380, 120), Vector2(-360, 140), Vector2(-340, -255),
		Vector2(-320, -300), Vector2(-300, 300), Vector2(-290, 210), Vector2(-280, 320), Vector2(-276, 200), Vector2(-262, -232), Vector2(-260, -250), Vector2(-255, 262),
		Vector2(-250, -470), Vector2(-240, 240), Vector2(-230, 240), Vector2(-205, -480), Vector2(-200, -330), Vector2(-195, -320), Vector2(-185, 90), Vector2(-180, -400),
		Vector2(-175, -300), Vector2(-160, -470), Vector2(-150, -230), Vector2(-150, -800), Vector2(-148, -790), Vector2(-142, -332), Vector2(-140, -340), Vector2(-120, -490),
		Vector2(-110, -330), Vector2(-100, -100), Vector2(-95, -55), Vector2(-90, 170), Vector2(-80, 110), Vector2(-80, 215), Vector2(-60, -100), Vector2(-60, -390),
		Vector2(-60, -650), Vector2(-58, 32), Vector2(-50, -760), Vector2(-48, -150), Vector2(-40, -230), Vector2(-30, -250), Vector2(-30, 850), Vector2(-10, 40),
		Vector2(-5, -175), Vector2(10, -470), Vector2(18, 790), Vector2(20, -60), Vector2(24, -170), Vector2(30, 22), Vector2(34, -170), Vector2(38, 18),
		Vector2(40, 800), Vector2(42, -92), Vector2(48, 818), Vector2(50, -130), Vector2(60, 0), Vector2(60, 100), Vector2(60, 20), Vector2(60, 805),
		Vector2(62, -112), Vector2(70, -70), Vector2(100, 775), Vector2(102, 32), Vector2(110, -20), Vector2(110, 80), Vector2(115, -148), Vector2(120, -40),
		Vector2(160, 28), Vector2(170, 40), Vector2(178, -200), Vector2(178, -40), Vector2(182, -300), Vector2(190, -400), Vector2(190, -500), Vector2(192, -688),
		Vector2(200, -300), Vector2(200, -600), Vector2(205, -690), Vector2(210, -700), Vector2(214, -330), Vector2(250, 845), Vector2(262, -430), Vector2(420, 60),
		Vector2(470, 300), Vector2(470, 310), Vector2(480, 368), Vector2(542, 208), Vector2(590, 360), Vector2(600, 430), Vector2(632, 450), Vector2(688, 328),
		Vector2(690, 330), Vector2(720, -260), Vector2(790, 470)]
# Wege der Rätsel (abenteuer_raetsel.gd LAWINE_PTS, SEIL_PTS)
const STORY_LINES := [[Vector2(-700, -130), Vector2(-705, 40), Vector2(-680, 240), Vector2(-650, 430)],
		[Vector2(-700, 470), Vector2(-790, 462), Vector2(-870, 450)]]
const CELL := 32.0

var bt                              # bergtal.gd
var m
var info := {}
var _sky_t := 0.0
var _sky_on := false

static var _cache := {}            # "lists" -> {karst, teeth, trees, shrubs, paths} (Tal-Koordinaten, für jeden Platz gleich)
static var _free := {}             # Zelle (32 m) -> [[Vector2, Radius]] (Freihalte-Punkte)
static var _knoise: FastNoiseLite  # Karstfelder
static var _gnoise: FastNoiseLite  # Gruppen (Häufchen)


func _init(bt_) -> void:
	bt = bt_
	m = bt.m


# =======================================================================================================================
# freihalten
# =======================================================================================================================
static func _add_free(q: Vector2, r: float) -> void:
	var k := Vector2i(int(floor(q.x / CELL)), int(floor(q.y / CELL)))
	if not _free.has(k):
		_free[k] = []
	_free[k].append([q, r])


static func _collect_lines(v, out: Array) -> void:
	"""all lists of Vector2 (walks, forks, detours) somewhere in the chapters of the adventure"""
	if v is Array:
		var pts := []
		for e in v:
			if e is Vector2:
				pts.append(e)
		if pts.size() >= 2 and pts.size() == (v as Array).size():
			out.append(pts)
			return
		for e in v:
			_collect_lines(e, out)
	elif v is Dictionary:
		for e in (v as Dictionary).values():
			_collect_lines(e, out)


func _make_free() -> void:
	if not _free.is_empty():
		return
	for p in STORY_PTS:
		_add_free(p, 10.0)
	var lines: Array = STORY_LINES.duplicate()
	_collect_lines(AD.CHAPTERS, lines)
	for ln in lines:
		for q in bt.dense(ln, 3.0):
			_add_free(q, 3.5)
	for st in bt.STREAMS:
		for q in bt.dense(st[0], 4.0):
			_add_free(q, 4.0)
	for p in bt.PLACES:
		_add_free(Vector2(p[1], p[2]), 10.0)
	for k in bt.SPOTS:
		_add_free(Vector2(bt.SPOTS[k][1], bt.SPOTS[k][2]), 25.0)
	for vp in bt.VIEWPOINTS:
		_add_free(bt.vp_xz(vp), 22.0)


static func _is_free(q: Vector2, extra := 0.0) -> bool:
	var k := Vector2i(int(floor(q.x / CELL)), int(floor(q.y / CELL)))
	for dj in range(-1, 2):
		for di in range(-1, 2):
			var kk := Vector2i(k.x + di, k.y + dj)
			if _free.has(kk):
				for e in _free[kk]:
					if q.distance_to(e[0]) < float(e[1]) + extra:
						return false
	return true


func _ok(q: Vector2, way: float, extra := 0.0) -> bool:
	return not bt._busy(q.x, q.y) and not bt._near_way(q.x, q.y, way) and _is_free(q, extra)


# =======================================================================================================================
# the lists (once per run of the program; the same for every spot)
# =======================================================================================================================
func _lists() -> Dictionary:
	if _cache.has("lists"):
		return _cache["lists"]
	var t0 := Time.get_ticks_msec()
	_make_free()
	_knoise = FastNoiseLite.new()
	_knoise.seed = 9001
	_knoise.frequency = 1.0 / 170.0
	_knoise.fractal_octaves = 2
	_gnoise = FastNoiseLite.new()
	_gnoise.seed = 4242
	_gnoise.frequency = 1.0 / 22.0
	_gnoise.fractal_octaves = 1
	var rr := RandomNumberGenerator.new()
	rr.seed = 3107
	var busy0: Array = bt._busy_pts.duplicate()             # (like bergtal._veg_lists: not the spot-dependent entries)
	bt._busy_pts = busy0.filter(func(b): return (b[0] as Vector2) != bt.spot_xz and (b[0] as Vector2) != bt.place_c)
	var paths := _paths(rr)
	var karst := _karst(rr)
	var teeth := _teeth(rr)
	var tr := _trees(rr)
	bt._busy_pts = busy0
	var out := {"karst": karst, "teeth": teeth, "trees": tr[0], "shrubs": tr[1], "paths": paths}
	_cache["lists"] = out
	_cache["ms"] = Time.get_ticks_msec() - t0
	return out


func karst_k(x: float, z: float, h: float) -> float:
	"""0 … 1: how much karst pasture (light limestone blocks in the alp grass) - the alp belt, patchy"""
	var n := _knoise.get_noise_2d(x, z)
	return smoothstep(0.0, 0.3, n) * smoothstep(200.0, 290.0, h) * (1.0 - smoothstep(700.0, 790.0, h))


func _ground_ok(q: Vector2, smax: float) -> bool:
	var zn: String = bt.zone(q.x, q.y)
	if zn in ["lake", "shore", "moor", "glacier", "pasture", "flowers"]:
		return false
	return bt.slope_deg(q.x, q.y, 2.0) < smax


func _paths(rr: RandomNumberGenerator) -> Array:
	"""Trampelpfade: narrow paths of cows and hikers through the karst pasture, along the slope (only looks, not a trail)"""
	var out := []
	var cands := []
	for tr in bt.TRAILS:                                     # from a trail into the field …
		for q in bt.dense(tr[1], 15.0):
			cands.append(q)
	var g := 60.0                                            # … or somewhere in the field
	var z: float = bt.LO + g
	while z < -bt.LO - g:
		var x: float = bt.LO + g
		while x < -bt.LO - g:
			cands.append(Vector2(x + rr.randf_range(-20.0, 20.0), z + rr.randf_range(-20.0, 20.0)))
			x += g
		z += g
	var starts := []
	for q in cands:
		var h: float = bt.H(q.x, q.y)
		if karst_k(q.x, q.y, h) < 0.45 or bt.slope_deg(q.x, q.y, 3.0) > 24.0 or not _ground_ok(q, 24.0):
			continue
		var far_ok := true
		for s0 in starts:
			if q.distance_to(s0) < 200.0:
				far_ok = false
		if far_ok:
			starts.append(q)
	for q0 in starts.slice(0, 9):
		var q: Vector2 = q0
		var gr: Vector2 = bt.grad(q.x, q.y)
		var d := (gr.orthogonal().normalized() if gr.length() > 0.01 else Vector2.RIGHT) * (1.0 if rr.randf() < 0.5 else -1.0)
		var line := PackedVector2Array([q])
		for k in range(50):
			var gk: Vector2 = bt.grad(q.x, q.y)
			if gk.length() > 0.01:                               # along the slope (a cow path), with a little wandering
				var c := gk.orthogonal().normalized()
				if c.dot(d) < 0.0:
					c = -c
				d = d.lerp(c, 0.35 * smoothstep(0.15, 0.45, gk.length())).normalized()
			d = d.rotated(rr.randf_range(-0.18, 0.18))
			var n := q + d * 3.0
			var h: float = bt.H(n.x, n.y)
			if not _ground_ok(n, 30.0) or bt.forest_k(n.x, n.y, h) > 0.6 or bt._busy(n.x, n.y) or bt._near_way(n.x, n.y, 2.0) or not _is_free(n):
				break
			q = n
			line.append(q)
		if line.size() >= 14:
			out.append(line)
			for p in line:
				_add_free(p, 1.4)                                   # the blocks keep off the path
	return out


func _karst(rr: RandomNumberGenerator) -> Array:
	"""[[v, x, z, rot, scale, sunk]] - groups and single blocks in the karst pasture, scree on the cones below the walls"""
	var out := []
	var z: float = bt.LO + 6.0
	while z < -bt.LO - 6.0:
		var x: float = bt.LO + 6.0
		while x < -bt.LO - 6.0:
			var px := x + rr.randf_range(-3.0, 3.0)
			var pz := z + rr.randf_range(-3.0, 3.0)
			x += 8.0
			var r := rr.randf()
			var h: float = bt.H(px, pz)
			var kk := karst_k(px, pz, h)
			var cone: float = bt.cone_at(px, pz)
			var single := (0.004 + 0.035 * kk) if (h > 260.0 and h < 760.0) else 0.0      # single blocks, scattered
			var p := kk * (0.02 + 0.9 * smoothstep(0.15, 0.45, _gnoise.get_noise_2d(px, pz))) + single + cone * 0.3   # groups with gaps
			if r > p:
				continue
			var q := Vector2(px, pz)
			if not _ground_ok(q, 38.0) or bt.forest_k(px, pz, h) > 0.7 or not _ok(q, 4.2):
				continue
			var n := 1
			if kk > 0.3 and rr.randf() < 0.65:
				n = rr.randi_range(3, 9)                           # a group
			for i in range(n):
				var o := q + Vector2.from_angle(rr.randf() * TAU) * (0.0 if i == 0 else rr.randf_range(1.2, 6.0))
				if i > 0 and not _ok(o, 4.2):
					continue
				var sc := rr.randf_range(0.3, 0.7) if rr.randf() < 0.55 else rr.randf_range(0.7, 1.5)   # mixed, also big ones
				if cone > 0.3 and kk < 0.3:
					sc *= 0.55                                      # scree: small
				out.append([rr.randi() % 4, o.x, o.y, rr.randf() * TAU, sc, rr.randf_range(0.2, 0.4)])
		z += 8.0
	return out


func _teeth(rr: RandomNumberGenerator) -> Array:
	"""[[v, x, z, rot, scale]] - rock teeth on the ridges (the crest is higher than all round it)"""
	var out := []
	var z: float = bt.LO + 12.0
	while z < -bt.LO - 12.0:
		var x: float = bt.LO + 12.0
		while x < -bt.LO - 12.0:
			var px := x + rr.randf_range(-5.0, 5.0)
			var pz := z + rr.randf_range(-5.0, 5.0)
			x += 14.0
			var r := rr.randf()
			var h: float = bt.H(px, pz)
			if h < 430.0 or r > 0.3:
				continue
			var lower := 0
			for k in range(8):
				var d := Vector2.from_angle(TAU * k / 8.0) * 22.0
				if bt.H(px + d.x, pz + d.y) < h - 2.5:
					lower += 1
			if lower < 6:
				continue
			var q := Vector2(px, pz)
			if bt.zone(px, pz) in ["glacier", "lake"] or not _ok(q, 7.0, 4.0):
				continue
			var n := rr.randi_range(1, 4)
			for i in range(n):
				var o := q + Vector2.from_angle(rr.randf() * TAU) * (0.0 if i == 0 else rr.randf_range(3.0, 8.0))
				if i > 0 and not _ok(o, 7.0, 4.0):
					continue
				out.append([rr.randi() % 3, o.x, o.y, rr.randf() * TAU, rr.randf_range(0.5, 1.3) * (1.0 + 0.4 * smoothstep(550.0, 800.0, h))])
		z += 14.0
	return out


func _trees(rr: RandomNumberGenerator) -> Array:
	"""[[kind, x, z, rot, scale]] trees (single spruces and small groups, dead spruces, mountain pines) and
	[[x, z, rot, scale]] dwarf shrubs (alpine roses, blueberries) on the ridges"""
	var out := []
	var shrubs := []
	var z: float = bt.LO + 6.0
	while z < -bt.LO - 6.0:
		var x: float = bt.LO + 6.0
		while x < -bt.LO - 6.0:
			var px := x + rr.randf_range(-4.0, 4.0)
			var pz := z + rr.randf_range(-4.0, 4.0)
			x += 12.0
			var r := rr.randf()
			var r2 := rr.randf()
			var h: float = bt.H(px, pz)
			if h < 60.0 or h > 640.0:
				continue
			var fk: float = bt.forest_k(px, pz, h)
			var q := Vector2(px, pz)
			var kind := ""
			var n := 1
			if fk > 0.02 and fk < 0.4 and h < 520.0 and r < 0.1:
				kind = "spruce"                                    # at the edge of the forest and on the pastures
				n = 1 if r2 < 0.55 else rr.randi_range(2, 4)
			elif h > 410.0 and h < 560.0 and r < 0.022:
				kind = "spruce_dead"                               # near the tree line, on the ridge
			elif h > 420.0 and r < 0.06 and bt.slope_deg(px, pz, 4.0) > 10.0:
				kind = "pine_shrub"                                # Legföhren on the ridge
				n = rr.randi_range(1, 3)
			if kind == "" and h > 400.0 and r2 < 0.05:
				if _ground_ok(q, 34.0) and _ok(q, 3.6):
					for i in range(rr.randi_range(2, 6)):
						var o := q + Vector2.from_angle(rr.randf() * TAU) * rr.randf_range(0.0, 3.5)
						if _ok(o, 3.6):
							shrubs.append([o.x, o.y, rr.randf() * TAU, rr.randf_range(0.6, 1.3)])
				continue
			if kind == "" or not _ground_ok(q, 36.0) or not _ok(q, 5.0):
				continue
			for i in range(n):
				var o := q + Vector2.from_angle(rr.randf() * TAU) * (0.0 if i == 0 else rr.randf_range(3.0, 7.0))
				if i > 0 and (not _ok(o, 5.0) or not _ground_ok(o, 36.0)):
					continue
				var sc := rr.randf_range(0.7, 1.25) * (0.8 if h > 440.0 else 1.0)
				out.append([kind, o.x, o.y, rr.randf() * TAU, sc])
		z += 12.0
	return [out, shrubs]


# =======================================================================================================================
# building (called by bergtal.gd)
# =======================================================================================================================
func add_trees(trees: Dictionary, trees_far: Dictionary, near_r: float) -> void:
	"""the extra trees into the lists of bergtal._veg_rest (same MultiMeshes)"""
	var L := _lists()
	var n := 0
	for e in L["trees"]:
		var q := Vector2(e[1], e[2])
		if q.distance_to(bt.spot_xz) < 35.0 or q.distance_to(bt.place_c) < maxf(35.0, bt.place_r + 12.0):
			continue
		var k := str(e[0])
		if not trees.has(k):
			trees[k] = []
			trees_far[k] = []
		var it := [bt.P(q.x, q.y, -0.15), e[3], e[4]]
		if q.distance_to(bt.spot_xz) < near_r:
			trees[k].append(it)
		else:
			trees_far[k].append(it)
		n += 1
	info["trees_extra"] = n


func build() -> void:
	"""karst blocks, scree, rock teeth, dwarf shrubs and the narrow paths (not in Lite)"""
	var L := _lists()
	var snowy: bool = bt.season == "winter"
	var bib = bt.bib
	# karst blocks and scree: 4 kinds (one MultiMesh per kind and group of 128 m), obstacles only for the big ones near the spot
	var by_v := [[], [], [], []]
	var nob := 0
	for e in L["karst"]:
		var q := Vector2(e[1], e[2])
		if q.distance_to(bt.spot_xz) < 20.0 or q.distance_to(bt.place_c) < bt.place_r + 10.0:
			continue
		var sc := float(e[4])
		var p: Vector3 = bt.P(q.x, q.y, -float(e[5]) * sc)
		by_v[int(e[0])].append([p, e[3], sc])
		if sc > 0.85 and q.distance_to(bt.spot_xz) < 220.0:
			m.add_obstacle(bt.W(p), 0.6 * sc, true)
			m.set_obstacle_height(0.5 * sc)
			nob += 1
	var nk := 0
	for v in range(4):
		bib.many("karst", by_v[v], {"v": v, "c": v % 2, "snow": snowy})
		nk += by_v[v].size()
	# rock teeth on the ridges (seen from far)
	var th := [[], [], []]
	for e in L["teeth"]:
		var q := Vector2(e[1], e[2])
		if q.distance_to(bt.spot_xz) < 50.0 or q.distance_to(bt.place_c) < bt.place_r + 20.0:
			continue
		th[int(e[0])].append([bt.P(q.x, q.y, -1.0 * float(e[4])), e[3], e[4]])
	var nt := 0
	for v in range(3):
		bib.many("rock_tooth", th[v], {"v": v, "c": 1, "noob": true})
		nt += th[v].size()
	# dwarf shrubs (not in winter: under the snow)
	var sh := []
	if not snowy:
		for e in L["shrubs"]:
			var q := Vector2(e[0], e[1])
			if q.distance_to(bt.spot_xz) < 15.0 or q.distance_to(bt.place_c) < bt.place_r + 6.0:
				continue
			sh.append([bt.P(q.x, q.y, -0.1), e[2], e[3]])
		bib.many("dwarf_shrub", sh, {"season": bt.season})
	# the narrow paths between the blocks
	var pc := Color(0.34, 0.31, 0.22) if not snowy else Color(0.82, 0.84, 0.87)
	for ln in L["paths"]:
		bt._ribbon(ln, PackedFloat32Array(), 0.38, pc, 0.05, 220.0, "road")
	info.merge({"karst": nk, "karst_obstacles": nob, "teeth": nt, "shrubs": sh.size(), "paths": (L["paths"] as Array).size(),
			"lists_ms": int(_cache.get("ms", 0))}, true)


# ---- the lake --------------------------------------------------------------------------------------------------------------
static var _hz := {}                 # lake -> horizon texture (128 × 1: colour of the land, alpha = its height angle)


func _horizon(lk: Array, wl: float) -> ImageTexture:
	var key := str(lk[0])
	if _hz.has(key):
		return _hz[key]
	var c: Vector2 = lk[0]
	var img := Image.create(128, 1, false, Image.FORMAT_RGBA8)
	for i in range(128):
		var az := (i + 0.5) / 128.0 * TAU - PI
		var d := Vector2(sin(az), cos(az))
		var best := 0.0
		var col := Color(0.3, 0.35, 0.3)
		var dist := 10.0
		while dist < 2600.0:
			var q := c + d * dist
			var h: float = bt.H(q.x, q.y)
			var fk: float = bt.forest_k(q.x, q.y, h) if absf(q.x) < 1024.0 and absf(q.y) < 1024.0 else 0.0
			var top := h + 12.0 * smoothstep(0.2, 0.5, fk)
			var a := atan2(top - wl, dist)
			if a > best and bt._ell(q, lk) > 1.05:
				best = a
				if fk > 0.3:
					col = Color(0.11, 0.17, 0.11)                   # spruce forest
				elif bt.slope_deg(q.x, q.y, 4.0) > 36.0:
					col = Color(0.66, 0.65, 0.61)                   # light limestone
				elif h > 900.0:
					col = Color(0.8, 0.82, 0.86)
				else:
					col = Color(0.44, 0.48, 0.24)                   # alp meadow
			dist += 8.0 if dist < 200.0 else 30.0
		col.a = clampf(best / (PI / 2.0), 0.0, 1.0)
		img.set_pixel(i, 0, col)
	var sm := img.duplicate()                                  # a little smoother (no hard stripes in the mirror)
	for i in range(128):
		var acc := Color(0, 0, 0, 0)
		for o in [-2, -1, 0, 1, 2]:
			acc += img.get_pixel(posmod(i + o, 128), 0) * [0.1, 0.2, 0.4, 0.2, 0.1][o + 2]
		sm.set_pixel(i, 0, acc)
	var tex := ImageTexture.create_from_image(sm)
	_hz[key] = tex
	return tex


static var _lake_shader: Shader


func lake_material(lk: Array) -> ShaderMaterial:
	if _lake_shader == null:
		_lake_shader = load("res://shaders/bergsee.gdshader")
	var wl: float = bt.level_of(lk)
	var mt := ShaderMaterial.new()
	mt.shader = _lake_shader
	mt.set_shader_parameter("noise_tex", m.noise_tex)
	mt.set_shader_parameter("horizon", _horizon(lk, wl))
	mt.set_shader_parameter("spring", 1.0 if bt.season == "fruehling" else 0.0)
	return mt


func lake_mesh(lk: Array, e0: float, e1: float, y: float) -> ArrayMesh:
	"""like bergtal._lake_mesh, but with rings (UV.x = how far out: 0 centre … 1 shore) - the shallow water near the shore"""
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var c: Vector2 = lk[0]
	var rings := [0.0, 0.35, 0.6, 0.74, 0.84, 0.91, 0.96, 1.0, 1.06].filter(func(e): return e > e0 and e < e1)
	rings.push_front(e0)
	rings.push_back(e1)
	var nseg := 64
	for ri in range(rings.size() - 1):
		var ea: float = rings[ri]
		var eb: float = rings[ri + 1]
		for i in range(nseg):
			var a0 := TAU * i / nseg
			var a1 := TAU * (i + 1) / nseg
			var pts := []
			var es := []
			for pr in [[a0, ea], [a1, ea], [a1, eb], [a0, eb]]:
				var q := Vector2(cos(pr[0]) * float(lk[1]) * pr[1], sin(pr[0]) * float(lk[2]) * pr[1]).rotated(float(lk[3])) + c
				pts.append(Vector3(q.x, y, q.y))
				es.append(pr[1])
			for k in [0, 2, 1, 0, 3, 2]:
				st.set_normal(Vector3.UP)
				st.set_uv(Vector2(es[k], 0.0))
				st.add_vertex(pts[k])
	return st.commit()


# ---- the sky and the air (every frame cheap, the values 4 × per second) ---------------------------------------------------
const SKY_KEYS := ["cumulus", "contrails", "rays", "dusk_band"]


func tick(dt: float, _t: float) -> bool:
	if bt.tal == null or not is_instance_valid(bt.tal):
		return true
	_sky_t -= dt
	if _sky_t > 0.0:
		return false
	_sky_t = 0.25
	var sm: ShaderMaterial = m.sky_mat
	if sm == null:
		return false
	var lite: bool = bt.lite or bt._lite() or str(m.quality) == "simple"
	if lite:
		if _sky_on:
			cleanup()
		return false
	_sky_on = true
	var el: float = m.sun_el()
	var w := str(m.weather)
	var fair := w in ["clear", "cloudy"]
	var day := clampf((el + 4.0) / 14.0, 0.0, 1.0)
	sm.set_shader_parameter("cumulus", (0.75 if w == "clear" else 0.45) * day if fair else 0.0)
	sm.set_shader_parameter("contrails", 0.8 * day if w == "clear" else 0.0)
	sm.set_shader_parameter("rays", 0.5 * smoothstep(2.0, 12.0, el) if w == "clear" else 0.0)
	# the evening (and a little the morning): yellow at the horizon, blue-grey above (the sun just under or over the horizon)
	var band := smoothstep(10.0, 1.0, el) * smoothstep(-8.0, -1.5, el) * (0.4 + 0.6 * (1.0 if m.hour() > 12.0 else 0.5))
	sm.set_shader_parameter("dusk_band", band if fair else band * 0.3)
	# haze in the back light (the sun low and in front): the fog of the valley takes the colour of the sun
	m.env.fog_sun_scatter = 0.35 if fair else 0.1
	return false


func cleanup() -> void:
	_sky_on = false
	if m != null and is_instance_valid(m) and m.sky_mat != null:
		for k in SKY_KEYS:
			m.sky_mat.set_shader_parameter(k, 0.0)
		if m.env != null:
			m.env.fog_sun_scatter = 0.0
