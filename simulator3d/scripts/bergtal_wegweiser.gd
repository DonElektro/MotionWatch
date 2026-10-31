extends RefCounted
## «Bergtal · Wegweiser» (Daniel 31.10.2026, Paket real-berg-orte): die gelben Wegweiser der Schweizer Wanderwege an den
## Weggabelungen von bergtal.gd. Ersetzt die alte Liste in bergtal._signs_and_cairns (gleiche Standorte, dazu neue Gabelungen).
##   - Zeit aus dem Weg, nicht aus der Luftlinie: ein Netz aus allen Wanderwegen (TRAILS) und der Passstrasse, kürzester Weg
##     (Dijkstra), dann die Formel der Schweizer Wanderwege (4,2 km/h; 1 h pro 300 m auf, 500 m ab; der grössere Teil plus die
##     Hälfte des kleineren), auf 5 min gerundet: «25 min», «1 h 30 min».
##   - Die Pfeile zeigen in die Richtung, in die der Weg die Gabelung verlässt. Ziele in derselben Richtung stehen untereinander
##     auf einer Tafel (wie echt: nah, mittel, fern). Spitze weiss-rot-weiss, wenn der Weg dorthin ein Bergweg ist, weiss-blau-weiss
##     beim Alpinwanderweg. Oben die weisse Standort-Tafel mit Höhe.
##   - Texte über T.t() (Namen und «… %d m»), die Zeit bleibt «h» / «min» wie auf den echten Tafeln.
## Ohne Weg zum Ziel (Netz nicht verbunden): die alte Schätzung (Luftlinie × 1,3).

const T = preload("res://scripts/i18n.gd")

# [Standort (Text, «%d» = Höhe), Ort (Tal x, z), [[Ziel, Ort], …]] - die Ziele sind Orte aus bergtal.gd PLACES / SPOTS
const JUNCTIONS := [
		["Alp Tschuggen %d m", Vector2(50, -14), [["Gumpisee", Vector2(-120, -490)], ["Furggapass", Vector2(30, 780)], ["Biwak Chüebodehorn", Vector2(-520, 548)],
			["Hängebrücke Tüfelsschlund", Vector2(34, -170)]]],
		["Gumpisee %d m", Vector2(-200, -326), [["Alp Tschuggen", Vector2(60, 0)], ["Schwarzseeli", Vector2(-600, -255)], ["Kapelle St. Jodern", Vector2(210, -690)],
			["Tuffwasserfall", Vector2(-188, -584)]]],
		["Tschuggen Strasse", Vector2(174, -46), [["Alp Tschuggen", Vector2(60, 0)], ["Gumpisee", Vector2(-200, -330)]]],
		["Murmelboden %d m", Vector2(-296, 294), [["Gratspitz", Vector2(-620, 128)], ["Biwak Chüebodehorn", Vector2(-520, 548)], ["Alp Tschuggen", Vector2(60, 0)]]],
		["Gratspitz %d m", Vector2(-609, 133), [["Murmelboden", Vector2(-300, 300)], ["Alp Tschuggen", Vector2(60, 0)], ["Geheimer See", Vector2(-860, 405)]]],
		["Furggapass %d m", Vector2(34, 776), [["Alp Tschuggen", Vector2(60, 0)], ["Gumpisee", Vector2(-120, -490)]]],
		["Abzweigung Wyssgletscher", Vector2(186, 136), [["Gletscherseeli", Vector2(640, 420)], ["Obri Stafel", Vector2(470, 300)], ["Chalchstock", Vector2(437, 207)],
			["Alp Tschuggen", Vector2(60, 0)]]],
		["St. Jodern %d m", Vector2(224, -688), [["Gumpisee", Vector2(10, -470)], ["Tschuggen Strasse", Vector2(178, -40)]]],
		["Riedmoos %d m", Vector2(-470, -236), [["Altstafel", Vector2(-830, -205)], ["Gumpisee", Vector2(-200, -330)]]],
		["Tüfelsschlund", Vector2(42, -168), [["Alp Tschuggen", Vector2(60, 0)], ["Gumpisee", Vector2(-60, -300)]]],
		# new (real-berg-orte): the forks of the Tobelweg and the Kapellenweg, the waterfall, Obri Stafel, the summit
		["Schattwald %d m", Vector2(-120, -490), [["Tuffwasserfall", Vector2(-188, -584)], ["Gumpisee", Vector2(-200, -330)], ["Kapelle St. Jodern", Vector2(210, -690)]]],
		["Gumpisee Nordufer %d m", Vector2(10, -470), [["Kapelle St. Jodern", Vector2(210, -690)], ["Alp Tschuggen", Vector2(60, 0)], ["Tuffwasserfall", Vector2(-188, -584)]]],
		["Tuffwasserfall %d m", Vector2(-186, -588), [["Gumpisee", Vector2(-200, -330)], ["Alp Tschuggen", Vector2(60, 0)]]],
		["Obri Stafel %d m", Vector2(479, 293), [["Chalchstock", Vector2(437, 207)], ["Gletscherseeli", Vector2(640, 420)], ["Alp Tschuggen", Vector2(60, 0)]]],
		["Chalchstock %d m", Vector2(441, 210), [["Obri Stafel", Vector2(470, 300)], ["Alp Tschuggen", Vector2(60, 0)]]]]

const MERGE := 8.0            # trail points closer than this are one node (where the trails meet)
const DENSE := 10.0           # m between the nodes along a trail

static var _nodes := PackedVector2Array()
static var _adj: Array = []   # node -> [[other, level], …]
static var _grid := {}
static var _hs := PackedFloat32Array()   # height of every node (once)


static func _key(p: Vector2) -> String:
	return "%d,%d" % [int(floor(p.x / MERGE)), int(floor(p.y / MERGE))]


static func _node(p: Vector2) -> int:
	var k := Vector2i(int(floor(p.x / MERGE)), int(floor(p.y / MERGE)))
	for dj in range(-1, 2):
		for di in range(-1, 2):
			var kk := "%d,%d" % [k.x + di, k.y + dj]
			for i in _grid.get(kk, []):
				if _nodes[i].distance_to(p) < MERGE:
					return i
	_nodes.append(p)
	_adj.append([])
	var ks := _key(p)
	if not _grid.has(ks):
		_grid[ks] = []
	_grid[ks].append(_nodes.size() - 1)
	return _nodes.size() - 1


static func _link(a: int, b: int, lvl: int) -> void:
	if a == b:
		return
	for e in _adj[a]:
		if int(e[0]) == b:
			return
	_adj[a].append([b, lvl])
	_adj[b].append([a, lvl])


static func _line(pts: Array, lvl: int) -> void:
	var dn := PackedVector2Array()
	for i in range(pts.size() - 1):
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var L := a.distance_to(b)
		var n := maxi(1, int(ceil(L / DENSE)))
		for k in range(n):
			dn.append(a.lerp(b, float(k) / n))
	dn.append(pts[-1])
	var prev := -1
	for p in dn:
		var i := _node(p)
		if prev >= 0:
			_link(prev, i, lvl)
		prev = i


static func build_net(trails: Array, road: PackedVector2Array) -> void:
	"""the net of all trails and the road (once; the trails are constants)"""
	if not _nodes.is_empty():
		return
	for tr in trails:
		_line(tr[1], int(tr[2]))
	var rp := []
	for i in range(0, road.size(), 4):
		rp.append(road[i])
	if road.size() > 0:
		rp.append(road[road.size() - 1])
	if rp.size() > 1:
		_line(rp, 0)


static func _nearest(p: Vector2) -> int:
	var best := -1
	var bd := INF
	for i in range(_nodes.size()):
		var d := _nodes[i].distance_squared_to(p)
		if d < bd:
			bd = d
			best = i
	return best


static func swiss_time(km: float, up: float, down: float) -> int:
	"""minutes like on the signs, rounded to 5 min"""
	var t1 := km / 4.2
	var t2 := up / 300.0 + down / 500.0
	var t := maxf(t1, t2) + minf(t1, t2) / 2.0
	return maxi(5, int(round(t * 60.0 / 5.0) * 5.0))


static func fmt(mins: int) -> String:
	if mins < 60:
		return "%d min" % mins
	if mins % 60 == 0:
		return "%d h" % (mins / 60)
	return "%d h %02d min" % [mins / 60, mins % 60]


static func route(hfn: Callable, from: Vector2, to: Vector2) -> Dictionary:
	"""the way along the trails: {ok, km, up, down, mins, level, dir (where the way leaves «from»)}"""
	var s := _nearest(from)
	var g := _nearest(to)
	if s < 0 or g < 0 or _nodes[g].distance_to(to) > 60.0:
		return {"ok": false}
	var n := _nodes.size()
	var dist := PackedFloat32Array()
	dist.resize(n)
	dist.fill(INF)
	var prev := PackedInt32Array()
	prev.resize(n)
	prev.fill(-1)
	if _hs.size() != n:
		_hs.resize(n)
		for i in range(n):
			_hs[i] = hfn.call(_nodes[i].x, _nodes[i].y)
		for it in range(10):                                 # bridges: a node far below both neighbours is on the deck
			for i in range(n):
				if (_adj[i] as Array).size() == 2:
					var ha: float = _hs[int(_adj[i][0][0])]
					var hb: float = _hs[int(_adj[i][1][0])]
					if _hs[i] < minf(ha, hb) - 4.0:
						_hs[i] = (ha + hb) / 2.0
	var hs := _hs
	dist[s] = 0.0
	var open := [s]
	var done := {}
	while not open.is_empty():
		var bi := 0
		for k in range(1, open.size()):
			if dist[open[k]] < dist[open[bi]]:
				bi = k
		var u: int = open[bi]
		open.remove_at(bi)
		if done.has(u):
			continue
		done[u] = true
		if u == g:
			break
		for e in _adj[u]:
			var v := int(e[0])
			if done.has(v):
				continue
			var dh := hs[v] - hs[u]
			var c := _nodes[u].distance_to(_nodes[v]) / 4200.0 + (dh / 300.0 if dh > 0.0 else -dh / 500.0)
			if dist[u] + c < dist[v]:
				dist[v] = dist[u] + c
				prev[v] = u
				open.append(v)
	if dist[g] == INF:
		return {"ok": false}
	var path := [g]
	while path[-1] != s:
		path.append(prev[path[-1]])
	path.reverse()
	var km := 0.0
	var up := 0.0
	var down := 0.0
	var lvl := 0
	for i in range(path.size() - 1):
		var a: int = path[i]
		var b: int = path[i + 1]
		km += _nodes[a].distance_to(_nodes[b]) / 1000.0
		var dh := hs[b] - hs[a]
		if dh > 0.0:
			up += dh
		else:
			down -= dh
		for e in _adj[a]:
			if int(e[0]) == b:
				lvl = maxi(lvl, int(e[1]))
	km += from.distance_to(_nodes[s]) / 1000.0
	var dir := Vector2.ZERO
	var walked := 0.0
	for i in range(1, path.size()):
		walked += _nodes[path[i - 1]].distance_to(_nodes[path[i]])
		dir = _nodes[path[i]] - from
		if walked > 14.0:
			break
	return {"ok": true, "km": km, "up": up, "down": down, "mins": swiss_time(km, up, down), "level": lvl, "dir": dir.normalized() if dir.length() > 0.1 else Vector2(1, 0)}


static func groups_for(hfn: Callable, pos: Vector2, targets: Array) -> Array:
	"""the boards of one sign: [[yaw (valley), level, [[name, time], …]], …] - targets in the same direction share a board"""
	var arms := []
	for t in targets:
		var r := route(hfn, pos, t[1])
		var mins := 0
		var lvl := 0
		var dir: Vector2 = (t[1] as Vector2 - pos).normalized()
		if r.get("ok", false):
			mins = int(r["mins"])
			lvl = int(r["level"])
			dir = r["dir"]
		else:                                                # not on the net: the old estimate (straight line × 1.3)
			var km: float = pos.distance_to(t[1]) * 1.3 / 1000.0
			var dh: float = float(hfn.call(t[1].x, t[1].y)) - float(hfn.call(pos.x, pos.y))
			mins = swiss_time(km, maxf(dh, 0.0), maxf(-dh, 0.0))
		arms.append([str(t[0]), mins, lvl, atan2(-dir.y, dir.x)])
	arms.sort_custom(func(a, b): return int(a[1]) < int(b[1]))
	var groups := []
	for a in arms:
		var put := false
		for g in groups:
			if absf(wrapf(float(a[3]) - float(g[0]), -PI, PI)) < deg_to_rad(28.0) and (g[2] as Array).size() < 3:
				(g[2] as Array).append([T.t(str(a[0])), fmt(int(a[1]))])
				g[1] = maxi(int(g[1]), int(a[2]))
				put = true
				break
		if not put:
			groups.append([float(a[3]), int(a[2]), [[T.t(str(a[0])), fmt(int(a[1]))]]])
	return groups


static func build(bt, trails: Array, road: PackedVector2Array, alt0: float) -> Array:
	"""all signposts into bt.bib; returns [{here, x, z, boards}] for info"""
	build_net(trails, road)
	var hfn := Callable(bt, "H")
	var out := []
	for jn in JUNCTIONS:
		var pos: Vector2 = jn[1]
		var here := str(jn[0])
		if here.contains("%d"):
			here = T.t(here) % int(bt.H(pos.x, pos.y) + alt0)
		else:
			here = T.t(here)
		var groups := groups_for(hfn, pos, jn[2])
		bt.bib.add("hiking_sign", bt.P(pos.x, pos.y), 0.0, {"here": here, "groups": groups, "both": true})
		out.append({"here": here, "x": pos.x, "z": pos.y, "boards": groups.map(func(g): return [snappedf(rad_to_deg(float(g[0])), 1.0), g[1], g[2]])})
	return out
