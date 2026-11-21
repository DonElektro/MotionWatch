extends SceneTree
## Erreichbarkeit des ganzen Parcours (Grossvater-Neubau, Besitzer 21.11.2026: in Szene 6 kam er nicht zum Brückenkopf - ein
## Test, der so etwas für alle 12 Szenen findet). Mit der echten Welt, ohne Bild:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/kit_weg_test.gd" -- --no-update --no-tour
## 1  Modell: ein Raster (0.25 m) über die Schlucht und über das Lager am Rand mit den Höhen von main.ground_y (Gelände,
##    Planken, Blöcke), den Hindernissen von main.keep_out, Wasser und Spalten. Kanten wie in kit_figur.gd: steigen bis
##    STUFE (und nicht steiler als STEIL), hinunter bis FALL_OK; Sprünge mit SPRUNG_V / GRAV (gehend und rennend, Wand im
##    Flug = nein, über einem Spalt tiefer als 1 m = nein); Kontext-Aktionen als Kanten (Kante hochklettern, Leiter, Seil,
##    Baumstamm, Steine). Für JEDES Ziel jeder Szene (ort / ort_tal / aktion / fund) wird ein Weg vom Start der Szene bzw.
##    vom vorigen Ziel gesucht.
## 2  Bot: wo der Weg nur aus Gehen und Springen besteht, läuft die echte Figur ihn ab - mit der Führung (WEGE) der Szene,
##    so wie ein Spieler, der dem Weg folgt. Sie muss im Zielkreis ankommen (nicht zurück zum Checkpoint, nicht nass).
## 3  «Zum nächsten Abschnitt springen» (nach 90 s ohne Fortschritt im Pausenmenü) bringt zum Ziel.
## Ende: «Weg-Test OK» oder «SCRIPT ERROR: Weg-Test: …» (Exit-Code 0 / 1).

const KF = preload("res://scripts/kit_figur.gd")
const H := 0.25
const V_GEH := 1.5
const V_RENN := 3.45

var errs: Array = []
var m = null
var k = null
var D = null
var R := {}                # the grid: kind, a0, b0, ni, nj, h (heights), f (flags)


func _init() -> void:
	_welt.call_deferred()


func _warte(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func c(d: Dictionary) -> Dictionary:
	d["action"] = "kit"
	return m.control(d)


func info() -> Dictionary:
	return c({"do": "info"}).get("kit", {})


func pruef(ok: bool, was: String) -> void:
	print(("ok   " if ok else "FEHL ") + was)
	if not ok:
		errs.append(was)


func _bis(cond: Callable, secs: float) -> bool:
	var t := 0.0
	while t < secs:
		if cond.call():
			return true
		await _warte(0.1)
		t += 0.1
	return cond.call()


# =======================================================================================================================
# the grid
# =======================================================================================================================
func welt_von(kind: String, a: float, b: float) -> Vector3:
	return k.par.welt(a, b) if kind == "sq" else k.par.W(k.par.G(a, b))


func ab_von(kind: String, w: Vector3) -> Vector2:
	return k.par.sq_von(w) if kind == "sq" else k.par.tal_von(w)


func raster(kind: String, a0: float, a1: float, b0: float, b1: float) -> Dictionary:
	var ni := int((a1 - a0) / H) + 1
	var nj := int((b1 - b0) / H) + 1
	var hh := PackedFloat32Array()
	var ff := PackedByteArray()
	hh.resize(ni * nj)
	ff.resize(ni * nj)
	for i in range(ni):
		for j in range(nj):
			var w := welt_von(kind, a0 + i * H, b0 + j * H)
			var g: float = m.ground_y(w.x, w.z)
			hh[i * nj + j] = g
			var f := 0
			var p2 := Vector2(w.x, w.z)
			if (m.keep_out(p2, 0.3, true) as Vector2).distance_to(p2) > 0.05:
				f |= 1
			var gf: Dictionary = k.par.gefahr_bei(Vector3(w.x, g, w.z))
			if not gf.is_empty():
				f |= 2 if str(gf["art"]) == "wasser" else 4
			ff[i * nj + j] = f
	# 8 = right beside a wall or an edge (higher than STUFE / deeper than FALL_OK within 0.35 m): the figure looks 0.3 m ahead and stops there - the
	# model keeps this clearance, so its straight lines between cells do not cut the corners of walls and blocks
	var n := 2
	for i in range(ni):
		for j in range(nj):
			var h0 := hh[i * nj + j]
			for di in range(-n, n + 1):
				for dj in range(-n, n + 1):
					var i2 := i + di
					var j2 := j + dj
					if (di == 0 and dj == 0) or i2 < 0 or j2 < 0 or i2 >= ni or j2 >= nj or Vector2(di, dj).length() * H > 0.36:
						continue
					var dh2: float = hh[i2 * nj + j2] - h0
					if dh2 > KF.STUFE or -dh2 > KF.FALL_OK:          # a wall - or an edge only a jump goes down
						ff[i * nj + j] |= 8
	return {"kind": kind, "a0": a0, "b0": b0, "ni": ni, "nj": nj, "h": hh, "f": ff}


func zelle(r: Dictionary, a: float, b: float) -> int:
	var i := int(round((a - float(r["a0"])) / H))
	var j := int(round((b - float(r["b0"])) / H))
	if i < 0 or j < 0 or i >= int(r["ni"]) or j >= int(r["nj"]):
		return -1
	return i * int(r["nj"]) + j


func ab(r: Dictionary, idx: int) -> Vector2:
	var nj := int(r["nj"])
	return Vector2(float(r["a0"]) + (idx / nj) * H, float(r["b0"]) + (idx % nj) * H)


func gehen_ok(r: Dictionary, a: int, b: int) -> bool:
	var f: PackedByteArray = r["f"]
	if f[b] & 3 or ((f[b] & 8) and not (f[a] & 8)):
		return false                                      # (from the wall away is fine, towards it not)
	var hh: PackedFloat32Array = r["h"]
	var dh := hh[b] - hh[a]
	if dh > KF.STUFE or (dh > 0.12 and dh / 0.3 > KF.STEIL):
		return false
	if -dh > KF.FALL_OK:
		return false
	return true


func spruenge(r: Dictionary, a: int) -> Array:
	"""landing cells of a jump from a: [cell, kind]"""
	var out := []
	var hh: PackedFloat32Array = r["h"]
	var f: PackedByteArray = r["f"]
	var p0 := ab(r, a)
	var ha := hh[a]
	var seen := {}
	for v in [V_GEH, V_RENN * 0.9]:
		for di in range(16):
			var dir := Vector2.from_angle(TAU * di / 16.0)
			var t := 0.02
			while t < 1.6:
				var y: float = ha + KF.SPRUNG_V * t - 0.5 * KF.GRAV * t * t
				var p: Vector2 = p0 + dir * float(v) * t
				var c2 := zelle(r, p.x, p.y)
				if c2 < 0:
					break
				var g := hh[c2]
				if g > y + 0.05 and g - ha > 0.5:
					break                                     # a wall in the flight
				if (f[c2] & 4) and ha - y > 1.0:
					break                                     # over the gap: grabbing the edge (back)
				if y <= g and t > 0.1:
					if not (f[c2] & 11) and c2 != a and not seen.has(c2) and _flach(r, c2):
						seen[c2] = true
						out.append([c2, "sprung"])
					break
				t += 0.02
	return out


func _flach(r: Dictionary, c2: int) -> bool:
	"""a landing needs room: the cells within 0.35 m at the same height (not the edge of a log or a stone)"""
	var hh: PackedFloat32Array = r["h"]
	var f: PackedByteArray = r["f"]
	var nj := int(r["nj"])
	for d in [[-1, 0], [1, 0], [0, -1], [0, 1]]:
		var c3: int = c2 + int(d[0]) * nj + int(d[1])
		if c3 < 0 or c3 >= hh.size() or absf(hh[c3] - hh[c2]) > 0.15 or (f[c3] & 3):
			return false
	return true


func rand_zelle(r: Dictionary, a: int) -> bool:
	"""a cell where walking stops somewhere around (only there jumps are searched)"""
	var nj := int(r["nj"])
	var ni := int(r["ni"])
	var i := a / nj
	var j := a % nj
	for di in [-1, 0, 1]:
		for dj in [-1, 0, 1]:
			if di == 0 and dj == 0:
				continue
			var i2: int = i + di
			var j2: int = j + dj
			if i2 < 0 or j2 < 0 or i2 >= ni or j2 >= nj:
				continue
			if not gehen_ok(r, a, i2 * nj + j2):
				return true
	return false


func aktions_kanten(r: Dictionary) -> Dictionary:
	"""cell -> [[cell, "aktion:<id>"]] for the actions that move the figure"""
	var out := {}
	var dinge := {}
	for d in D.DINGE:
		dinge[str(d["id"])] = d
	for a in D.AKTIONEN:
		if a.has("tal") != (str(r["kind"]) == "tal"):
			continue
		var art := str(a["art"])
		var ziel = null
		var dd: Dictionary = dinge.get(str(a.get("ding", "")), {})
		match art:
			"kante":
				ziel = Vector2(float(dd["s"]), float(a["q"]))
			"leiter":
				ziel = Vector2(float(a["oben"][0]), float(a["oben"][1]))
			"seil":
				ziel = Vector2(float(dd["nach"][0]), float(dd["nach"][1]))
			"balance":
				ziel = Vector2(float(dd["s"]) + float(dd["ls"]) + 0.4, float(dd["q"]))
			"steine":
				ziel = Vector2(float(a["nach"][0]), float(a["nach"][1]))
		if ziel == null:
			continue
		var zc := zelle(r, ziel.x, ziel.y)
		var starts := []
		if art == "kante" and a.has("ding") and dd.has("von"):
			for vp in dd["von"]:
				starts.append(Vector2(float(vp[0]), float(vp[1])))
		else:
			starts.append(Vector2(float(a["s"]), float(a["q"])))
		for st in starts:
			var rr := minf(float(a["r"]), 1.0)
			var n := int(rr / H)
			for di in range(-n, n + 1):
				for dj in range(-n, n + 1):
					var sc := zelle(r, st.x + di * H, st.y + dj * H)
					if sc < 0 or Vector2(di, dj).length() * H > rr:
						continue
					if not out.has(sc):
						out[sc] = []
					out[sc].append([zc, "aktion:" + str(a["id"])])
	return out


# ---- A* ------------------------------------------------------------------------------------------------------------------
func suchen(r: Dictionary, von: Vector2, ziel: Vector2, rad: float, akt: Dictionary) -> Array:
	"""the cells [[cell, how]] from von into the goal circle (and at the height of the goal, like kit_abenteuer.gd), or []"""
	var s0 := zelle(r, von.x, von.y)
	var zc := zelle(r, ziel.x, ziel.y)
	if s0 < 0 or zc < 0:
		return []
	var hz: float = (r["h"] as PackedFloat32Array)[zc]
	var g := {s0: 0.0}
	var prev := {s0: [-1, ""]}
	var heap := [[ab(r, s0).distance_to(ziel), s0]]
	var nj := int(r["nj"])
	var ni := int(r["ni"])
	var done := {}
	var n := 0
	while not heap.is_empty():
		var top: Array = _pop(heap)
		var a: int = top[1]
		if done.has(a):
			continue
		done[a] = true
		n += 1
		if ab(r, a).distance_to(ziel) < rad and absf((r["h"] as PackedFloat32Array)[a] - hz) < 1.0:
			var path := []
			var cur := a
			while cur >= 0:
				path.push_front([cur, prev[cur][1]])
				cur = prev[cur][0]
			return path
		var nb := []
		var i := a / nj
		var j := a % nj
		for di in [-1, 0, 1]:
			for dj in [-1, 0, 1]:
				if di == 0 and dj == 0:
					continue
				var i2: int = i + di
				var j2: int = j + dj
				if i2 >= 0 and j2 >= 0 and i2 < ni and j2 < nj and gehen_ok(r, a, i2 * nj + j2):
					nb.append([i2 * nj + j2, "gehen"])
		if rand_zelle(r, a):
			nb.append_array(spruenge(r, a))
		nb.append_array(akt.get(a, []))
		for e in nb:
			var b: int = e[0]
			if b < 0 or done.has(b):
				continue
			var cost: float = ab(r, a).distance_to(ab(r, b)) + (4.0 if str(e[1]) == "sprung" else 0.0) + (3.0 if str(e[1]).begins_with("aktion") else 0.0)
			var ng: float = float(g[a]) + cost
			if ng < float(g.get(b, 1.0e18)):
				g[b] = ng
				prev[b] = [a, str(e[1])]
				_push(heap, [ng + ab(r, b).distance_to(ziel), b])
	return []


func _push(h: Array, e: Array) -> void:
	h.append(e)
	var i := h.size() - 1
	while i > 0:
		var p := (i - 1) / 2
		if float(h[p][0]) <= float(h[i][0]):
			break
		var t = h[p]
		h[p] = h[i]
		h[i] = t
		i = p


func _pop(h: Array) -> Array:
	var top: Array = h[0]
	var last: Array = h.pop_back()
	if h.is_empty():
		return top
	h[0] = last
	var i := 0
	while true:
		var l := i * 2 + 1
		var r2 := l + 1
		var s := i
		if l < h.size() and float(h[l][0]) < float(h[s][0]):
			s = l
		if r2 < h.size() and float(h[r2][0]) < float(h[s][0]):
			s = r2
		if s == i:
			break
		var t = h[s]
		h[s] = h[i]
		h[i] = t
		i = s
	return top


# =======================================================================================================================
# the goals of the scenes
# =======================================================================================================================
func ziel_von(bis: String) -> Dictionary:
	"""{kind, p: Vector2 (s,q or tal x,z), r, nach: Vector2 (where the figure is afterwards)} or {} (no walking)"""
	if bis.begins_with("ort:"):
		var p := bis.substr(4).split(",")
		return {"kind": "sq", "p": Vector2(float(p[0]), float(p[1])), "r": float(p[2])}
	if bis.begins_with("ort_tal:"):
		var pt := bis.substr(8).split(",")
		return {"kind": "tal", "p": Vector2(float(pt[0]), float(pt[1])), "r": float(pt[2])}
	var id := ""
	if bis.begins_with("aktion:"):
		id = bis.substr(7)
	elif bis.begins_with("fund:"):
		for a in D.AKTIONEN:
			if str(a.get("ding", "")) == bis.substr(5) and str(a["art"]) == "fund":
				id = str(a["id"])
	for a in D.AKTIONEN:
		if str(a["id"]) == id and float(a["r"]) > 0.0:
			if a.has("tal"):
				return {"kind": "tal", "p": Vector2(float(a["tal"][0]), float(a["tal"][1])), "r": minf(float(a["r"]), 1.2)}
			return {"kind": "sq", "p": Vector2(float(a["s"]), float(a["q"])), "r": minf(float(a["r"]), 1.2)}
	return {}


func start_von(sz: Dictionary) -> Dictionary:
	var st: Array = sz.get("start", [])
	if st.size() >= 2:
		return {"kind": "sq", "p": Vector2(float(st[0]), float(st[1]))}
	var cp: Dictionary = D.CHECKPOINTS["lager"]
	return {"kind": "tal", "p": Vector2(float(cp["tal"][0]), float(cp["tal"][1]))}


# =======================================================================================================================
# the bot: the real figure walks the way
# =======================================================================================================================
func bot(r: Dictionary, path: Array, ziel: Vector2, rad: float, was: String) -> bool:
	var kind := str(r["kind"])
	await _bis(func(): return k.figur.zustand != "zurueck", 3.0)
	await _warte(0.8)                                     # (a pending «back to the checkpoint» of a failed run)
	var p0 := ab(r, int(path[0][0]))
	if kind == "sq":
		c({"do": "setzen", "s": p0.x, "q": p0.y})
	else:
		c({"do": "setzen", "tal": [p0.x, p0.y]})
	await _warte(0.4)
	var cp0 := str(info().get("checkpoint", ""))
	var nass0 := int(k.figur.nass)
	# waypoints: every 4th cell, every jump / action and the end
	var wp := []
	for i in range(1, path.size()):
		var how := str(path[i][1])
		var vor_sprung: bool = i + 1 < path.size() and str(path[i + 1][1]) != "gehen"
		var knick: bool = i + 1 < path.size() and int(path[i + 1][0]) - int(path[i][0]) != int(path[i][0]) - int(path[i - 1][0])
		if how != "gehen" or vor_sprung or knick or i % 2 == 0 or i == path.size() - 1:
			wp.append([ab(r, int(path[i][0])), how])
	for w in wp:
		var pt: Vector2 = w[0]
		var how := str(w[1])
		var wz := welt_von(kind, pt.x, pt.y)
		if how.begins_with("aktion:"):
			if kind == "sq":
				c({"do": "setzen", "s": pt.x, "q": pt.y})
			else:
				c({"do": "setzen", "tal": [pt.x, pt.y]})
			await _warte(0.3)
			continue
		if how == "sprung":
			var fp: Vector3 = k.figur.pos()
			var d := Vector3(wz.x - fp.x, 0, wz.z - fp.z)
			k.figur.a.heading = atan2(-d.x, -d.z)
			k.figur.a.rotation.y = k.figur.a.heading
			var hz: float = m.ground_y(wz.x, wz.z) - k.figur.pos().y      # the speed of the running jump that lands there
			var t_flug := (KF.SPRUNG_V + sqrt(maxf(0.0, KF.SPRUNG_V * KF.SPRUNG_V - 2.0 * KF.GRAV * hz))) / KF.GRAV
			k.figur.a.cur_speed = clampf(d.length() / t_flug * 1.05, 0.3, V_RENN)
			k.figur._springen(Vector2.ZERO)
			await _bis(func(): return k.figur.zustand == "luft", 1.0)
			await _bis(func(): return k.figur.zustand != "luft", 3.0)
			continue
		var t := 0.0
		var limit := 4.0 + ab_von(kind, k.figur.pos()).distance_to(pt) / 0.6
		while t < limit:
			var fp2: Vector3 = k.figur.pos()
			if Vector2(fp2.x, fp2.z).distance_to(Vector2(wz.x, wz.z)) < 0.3:
				break
			if k.figur.zustand == "zurueck" or int(k.figur.nass) != nass0:
				break
			c({"do": "eingabe", "ziel": [wz.x, wz.z], "s": 0.25})
			await _warte(0.2)
			t += 0.2
		if k.figur.zustand == "zurueck" or int(k.figur.nass) != nass0 or k.figur.zustand == "haengen":
			print("     Bot: %s bei %s (%s) - Weg: %s" % [k.figur.zustand, str(ab_von(kind, k.figur.pos())), was, _weg_text(r, path)])
			return false
	c({"do": "eingabe", "mv": [0, 0], "s": 0.1})
	await _warte(0.3)
	var me := ab_von(kind, k.figur.pos())
	var zw := welt_von(kind, ziel.x, ziel.y)
	var ok: bool = me.distance_to(ziel) < rad + 0.3 and k.figur.zustand == "boden" and absf(k.figur.pos().y - float(m.ground_y(zw.x, zw.z))) < 1.0
	if not ok:
		print("     Bot: steht bei %s, Ziel %s r %.1f, %s - Weg: %s" % [str(me), str(ziel), rad, k.figur.zustand, _weg_text(r, path)])
	return ok


func _weg_text(r: Dictionary, path: Array) -> String:
	var o := []
	var hh: PackedFloat32Array = r["h"]
	for e in path:
		var p := ab(r, int(e[0]))
		o.append("%s(%.2f,%.2f h%.2f)" % ["" if str(e[1]) in ["gehen", ""] else str(e[1]) + ">", p.x, p.y, hh[int(e[0])]])
	return " ".join(o)


# =======================================================================================================================
func _welt() -> void:
	D = load("res://scripts/kit_k2_daten.gd")
	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in range(120):
		await process_frame
	await _warte(2.0)
	c({"do": "start", "rolle": "enkelin", "name": "Test", "figur_test": true})
	var ok: bool = await _bis(func(): return str(info().get("phase", "")) == "spiel", 60.0)
	pruef(ok, "Start: Spiel läuft")
	if not ok:
		_ende()
		return
	k = m.kit
	c({"do": "frei", "on": true})
	k.par.tor_auf("tor")                                  # (scene 3: Maggie opens it - here: open for all later goals)
	var t0 := Time.get_ticks_msec()
	var rs := {"sq": raster("sq", -12.0, 64.0, -11.0, 11.0), "tal": raster("tal", -32.0, -2.0, -26.0, 2.0)}
	var akt := {"sq": aktions_kanten(rs["sq"]), "tal": aktions_kanten(rs["tal"])}
	print("Raster: %d + %d Zellen in %d ms" % [int(rs["sq"]["ni"]) * int(rs["sq"]["nj"]), int(rs["tal"]["ni"]) * int(rs["tal"]["nj"]), Time.get_ticks_msec() - t0])

	# ---- 1 + 2: every goal of every scene
	var bots := 0
	for sz in D.SZENEN:
		var sid := str(sz["id"])
		var cur := start_von(sz)
		k.weg = k.par.weg_punkte(D.WEGE.get(sid, []))
		for st in sz["schritte"]:
			if not (st as Dictionary).has("ziel"):
				continue
			var z := ziel_von(str(st.get("bis", "")))
			if z.is_empty():
				print("     %s: «%s» – kein Weg nötig" % [sid, str(st["bis"])])
				continue
			var kind := str(z["kind"])
			if str(cur["kind"]) != kind:
				cur = {"kind": kind, "p": z["p"]}               # (from the gorge to the rim: the scene starts at the camp)
			var r: Dictionary = rs[kind]
			var zp: Vector2 = z["p"]
			var path := suchen(r, cur["p"], zp, float(z["r"]), akt[kind])
			var wie := {}
			for e in path:
				wie[str(e[1])] = true
			pruef(not path.is_empty(), "%s: «%s» erreichbar von %s (%s)" % [sid, str(st["bis"]), str(cur["p"]), ", ".join(wie.keys().filter(func(x): return x != ""))])
			if path.is_empty():
				continue
			var nur_gehen := true
			for e in path:
				if str(e[1]).begins_with("aktion:"):
					nur_gehen = false
			if nur_gehen and path.size() > 2:
				var bok: bool = await bot(r, path, zp, float(z["r"]), sid)
				bots += 1
				pruef(bok, "%s: Bot läuft zu «%s» (%d Felder)" % [sid, str(st["bis"]), path.size()])
			cur = {"kind": kind, "p": ab(r, int(path[path.size() - 1][0]))}
	pruef(bots >= 6, "Bot ist %d Wege gelaufen" % bots)

	# ---- the bridge head: from the start of scene 6 straight at the middle of the bridge = the edge of the cleft;
	# the way over the landing on the right works (the reason for the owner's report)
	var r6: Dictionary = rs["sq"]
	var kopf := zelle(r6, float(D.BRUECKENKOPF[0]), float(D.BRUECKENKOPF[1]))
	pruef(kopf >= 0 and not (r6["f"][kopf] & 3), "Brückenkopf: begehbar")

	# ---- 4: the camera at the start of every scene (21.11.: it went into a boulder at the bridge head): not in a rock detail,
	# above the ground, the head of the figure in view
	k.regie.yaw = 0.0
	for sz in D.SZENEN:
		var st := start_von(sz)
		var stp: Vector2 = st["p"]
		for blick in [0.0, PI * 0.5, PI, -PI * 0.5]:
			if str(st["kind"]) == "sq":
				c({"do": "setzen", "s": stp.x, "q": stp.y})
			else:
				c({"do": "setzen", "tal": [stp.x, stp.y]})
			k.figur.a.heading = blick
			k.regie.hinter_figur()
			await _warte(0.8)
			var cp: Vector3 = m.view_cam.global_position
			var kopf_p: Vector3 = k.figur.pos() + Vector3(0, 1.45, 0)
			var drin := ""
			if k.par.schlucht != null:
				for kg in k.par.schlucht.kugeln_welt(Callable(k.par, "W")):
					if cp.distance_to(kg[0]) < float(kg[1]):
						drin = "in einem Felsbrocken"
			if cp.y < float(m.ground_y(cp.x, cp.z)) + 0.25:
				drin = "im Boden"
			var frei: bool = k.regie._blocker(cp, kopf_p, 16) < 0.0
			pruef(drin == "" and frei, "Kamera %s Blick %.1f: %s" % [str(sz["id"]), blick, "frei" if drin == "" and frei else (drin if drin != "" else "Fels zwischen Kamera und Kopf")])

	# ---- 3: the way out after 90 s
	c({"do": "frei", "on": false})
	c({"do": "szene", "value": "s06_bruecke"})
	await _bis(func(): return str(info().get("phase", "")) == "film", 3.0)
	c({"do": "skip"})
	await _bis(func(): return str(info().get("phase", "")) == "spiel", 3.0)
	await _warte(0.3)
	pruef(str(info().get("ziel", "")).find("Hängebrücke") >= 0, "Szene 6: Ziel Hängebrücke")
	var zw = k.ziel_welt()
	var zsq: Vector2 = k.par.sq_von(zw) if zw is Vector3 else Vector2.ZERO
	pruef(zsq.distance_to(Vector2(51.0, 6.3)) < 0.3, "Szene 6: der Kompass zeigt zuerst zum Plattenweg (%s)" % str(zsq))
	k.schritt["_t0"] = k.uhr - 95.0
	await _warte(0.4)
	pruef(bool(info().get("abschnitt_angebot", false)), "nach 90 s: Angebot «Zum nächsten Abschnitt springen»")
	k.pause(true)
	pruef(k.hud._abschnitt_btn != null and k.hud._abschnitt_btn.visible, "Pausenmenü: Knopf «Zum nächsten Abschnitt springen» sichtbar")
	k.hud._abschnitt_btn.pressed.emit()
	ok = await _bis(func(): return str(info().get("phase", "")) == "film", 4.0)
	pruef(ok, "Abschnitt gesprungen: der Einsturz-Film beginnt")
	_ende()


func _ende() -> void:
	Engine.time_scale = 1.0
	if errs.is_empty():
		print("Weg-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Weg-Test: " + str(e))
		quit(1)
